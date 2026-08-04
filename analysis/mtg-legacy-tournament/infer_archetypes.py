"""
infer_archetypes.py — Infer deck archetypes from mainboard co-occurrence
structure, replacing the hand-authored anchor-card rules in archetype_cluster.py.

Why
───
The rebuild brief (§2.1) treats archetypes as OUTPUTS: stable, winning
clumping patterns of cards that fall out of card-level co-occurrence — not a
hand-authored label list that goes in. The 12 anchor-rule archetypes in
archetype_cluster.py are kept as a *validation benchmark*: run with
--validate to check that the named archetypes are recovered and that the
anchor rules' "Other" share (~51.5%) drops materially.

Method (stdlib only — no ML dependencies)
─────────────────────────────────────────
A deck is represented as its set of mainboard card names. The card vocabulary
is filtered to min_df ≤ document frequency ≤ max_df·N before computing
similarity: format staples (Brainstorm, Force of Will, fetchlands — in >40%
of decks) carry no archetype signal, and sub-min_df cards are noise.

  Pass 1 — discovery: greedy leader clustering over a random subsample
    (default 25,000 decks, seeded). Each deck joins the best existing cluster
    if Jaccard(deck, cluster core) ≥ --threshold, else it founds a new
    cluster. A cluster's "core" is the set of cards present in
    ≥ --core-fraction of its members; cores are refreshed on a doubling
    schedule. An inverted index (card → clusters whose core contains it)
    keeps each lookup near-constant, so noise singletons don't blow up cost.
  Merge — leader clustering is order-sensitive, so clusters whose cores have
    Jaccard ≥ --merge-threshold are unioned. Clusters below
    --min-cluster-size are then dropped (their decks fall through to a
    surviving cluster, or to "Other", in pass 2).
  Pass 2 — assignment: every deck in the full panel is assigned to the best
    surviving core by Jaccard; below --assign-threshold → "Other".

Expected runtime at full scale (~87,600 decks): reading deck JSONs dominates
(~1–2 min on SSD); pass 1 on a 25K sample ≈ 1–3 min; pass 2 over the full
panel ≈ 1–2 min. Whole run ≈ 5 min single-core, < 1 GB RAM.

Within-cluster win log-OR
─────────────────────────
Identical conventions to archetype_cluster.py / analyze pipeline: 0.5 Laplace
smoothing, default n ≥ 20 decks with AND without the card, bracket-ranked
decks only. cluster_card_stats.csv has the same columns as
archetype_card_stats.csv (with cluster IDs in the `archetype` column), so the
downstream within-archetype stats consumers can swap files.

Outputs
────────
  data/deck_clusters.csv       — per-deck assignment: deck_id, cluster_id,
                                 cluster_label, similarity
  data/cluster_summary.csv     — cluster sizes, win rates, top characteristic
                                 cards by lift
  data/cluster_card_stats.csv  — per-cluster per-card win log-OR
                                 (same columns as archetype_card_stats.csv)
  data/cluster_validation.csv  — only with --validate: recovery of the
                                 anchor-rule archetypes (recall/purity)

Usage
─────
    uv run python infer_archetypes.py [--sample N] [--threshold X] [--seed N]
    uv run python infer_archetypes.py --validate
"""

import argparse
import csv
import json
import math
import random
import sys
import types
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


# ---------------------------------------------------------------------------
# Anchor rules (validation benchmark) — imported from archetype_cluster.py
# ---------------------------------------------------------------------------

def load_anchor_rules():
    """Import the anchor-rule table and matcher from archetype_cluster.py.

    archetype_cluster.py imports tqdm at module level; tqdm is not needed for
    the rule table itself, so stub it if absent (keeps --validate usable in
    minimal environments).
    """
    if "tqdm" not in sys.modules:
        try:
            import tqdm  # noqa: F401
        except ImportError:
            stub = types.ModuleType("tqdm")
            stub.tqdm = lambda iterable, **kwargs: iterable
            sys.modules["tqdm"] = stub
    sys.path.insert(0, str(Path(__file__).parent))
    from archetype_cluster import ARCHETYPES, assign_archetype
    return ARCHETYPES, assign_archetype


# ---------------------------------------------------------------------------
# Bracket rank (same logic as build_features.py / archetype_cluster.py)
# ---------------------------------------------------------------------------

def bracket_rank(placement: int) -> int | None:
    if placement == 1:
        return 1
    if placement == 2:
        return 2
    if placement >= 6 and placement % 2 == 0:
        return (placement - 6) // 2 + 3
    return None


# ---------------------------------------------------------------------------
# Step 1: Load decks and event metadata
# ---------------------------------------------------------------------------

def load_decks(raw_dir: Path) -> dict[int, frozenset]:
    """Read all deck_*.json files → deck_id → frozenset of mainboard card names."""
    if not raw_dir.is_dir():
        raise SystemExit(
            f"ERROR: raw data directory not found: {raw_dir}\n"
            "Expected the MTGTop8 scrape cache (deck_*.json, events_*.json) "
            "produced by fetch_data.py. This dataset is gitignored and lives "
            "on the owner's machine only."
        )
    files = sorted(raw_dir.glob("deck_*.json"))
    if not files:
        raise SystemExit(
            f"ERROR: no deck_*.json files in {raw_dir} — run fetch_data.py first."
        )

    decks: dict[int, frozenset] = {}
    for i, path in enumerate(files, 1):
        try:
            deck = json.loads(path.read_text())
            did = deck["deck_id"]
            mainboard = deck.get("mainboard", [])
        except Exception:
            print(f"  WARNING: skipping unreadable/malformed deck file {path.name} "
                  "(expected schema: {deck_id, mainboard: [{card_name, quantity}]})")
            continue
        cards = frozenset(e["card_name"] for e in mainboard if e.get("card_name"))
        if cards:
            decks[did] = cards
        if i % 10000 == 0:
            print(f"    {i:,}/{len(files):,} deck files read")
    if not decks:
        raise SystemExit(f"ERROR: no decks with a non-empty mainboard found in {raw_dir}")
    return decks


def build_deck_meta(raw_dir: Path) -> dict[int, dict]:
    """Read all events_*.json files → deck_id → {placement, event_id}."""
    deck_meta: dict[int, dict] = {}
    for path in sorted(raw_dir.glob("events_*.json")):
        events = json.loads(path.read_text())
        for event in events:
            for d in event.get("decks", []):
                did = d["deck_id"]
                if did not in deck_meta:
                    deck_meta[did] = {
                        "placement": d["placement"],
                        "event_id":  event["event_id"],
                    }
    return deck_meta


# ---------------------------------------------------------------------------
# Step 2: Vocabulary filter — drop format staples and noise cards
# ---------------------------------------------------------------------------

def build_reps(
    decks: dict[int, frozenset],
    min_df: int,
    max_df_frac: float,
) -> tuple[dict[int, frozenset], Counter]:
    """Reduce each deck to its similarity representation.

    Returns (deck_id → filtered card set, card → document frequency).
    Cards in fewer than min_df decks or more than max_df_frac of all decks
    are excluded from the similarity space (but kept everywhere else).
    """
    df: Counter = Counter()
    for cards in decks.values():
        df.update(cards)

    n = len(decks)
    max_df = max_df_frac * n
    vocab = {c for c, k in df.items() if min_df <= k <= max_df}

    reps = {did: frozenset(cards & vocab) for did, cards in decks.items()}
    n_empty = sum(1 for r in reps.values() if not r)
    print(f"  vocabulary: {len(vocab):,} cards kept of {len(df):,} "
          f"(min_df={min_df}, max_df={max_df_frac:.0%}); "
          f"{n_empty:,} decks have an empty representation → Other")
    return reps, df


# ---------------------------------------------------------------------------
# Step 3: Pass 1 — greedy leader clustering on a subsample
# ---------------------------------------------------------------------------

def _jaccard(a: frozenset, b: frozenset) -> float:
    inter = len(a & b)
    if inter == 0:
        return 0.0
    return inter / (len(a) + len(b) - inter)


def _core_of(counts: Counter, size: int, core_fraction: float) -> frozenset:
    cutoff = core_fraction * size
    return frozenset(c for c, k in counts.items() if k >= cutoff)


def discover_clusters(
    reps: dict[int, frozenset],
    sample_size: int,
    threshold: float,
    core_fraction: float,
    seed: int,
) -> list[dict]:
    """Greedy leader clustering. Returns clusters [{counts, size, core}]."""
    ids = [did for did, rep in reps.items() if rep]
    rng = random.Random(seed)
    if len(ids) > sample_size:
        ids = rng.sample(ids, sample_size)
    else:
        rng.shuffle(ids)

    clusters: list[dict] = []
    index: dict[str, set] = defaultdict(set)  # card → cluster idx whose core has it

    def refresh_core(i: int) -> None:
        cl = clusters[i]
        new_core = _core_of(cl["counts"], cl["size"], core_fraction)
        for card in cl["core"] - new_core:
            index[card].discard(i)
        for card in new_core - cl["core"]:
            index[card].add(i)
        cl["core"] = new_core

    for n_done, did in enumerate(ids, 1):
        rep = reps[did]

        candidates: set = set()
        for card in rep:
            candidates |= index.get(card, set())

        best_i, best_sim = -1, 0.0
        for i in candidates:
            sim = _jaccard(rep, clusters[i]["core"])
            if sim > best_sim:
                best_i, best_sim = i, sim

        if best_i >= 0 and best_sim >= threshold:
            cl = clusters[best_i]
            cl["counts"].update(rep)
            cl["size"] += 1
            # Refresh the core on a doubling schedule (plus every 128 adds)
            if cl["size"] & (cl["size"] - 1) == 0 or cl["size"] % 128 == 0:
                refresh_core(best_i)
        else:
            i = len(clusters)
            clusters.append({"counts": Counter(rep), "size": 1, "core": rep})
            for card in rep:
                index[card].add(i)

        if n_done % 5000 == 0:
            print(f"    {n_done:,}/{len(ids):,} sampled decks clustered "
                  f"({len(clusters):,} leaders so far)")

    # Final core refresh on everything
    for i in range(len(clusters)):
        refresh_core(i)
    return clusters


# ---------------------------------------------------------------------------
# Step 4: Merge near-duplicate leaders, drop small clusters
# ---------------------------------------------------------------------------

def merge_clusters(
    clusters: list[dict],
    merge_threshold: float,
    core_fraction: float,
    min_cluster_size: int,
) -> list[dict]:
    """Union clusters with Jaccard-similar cores; drop those below min size.

    Returns surviving clusters sorted by size (desc), cores recomputed.
    """
    parent = list(range(len(clusters)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    index: dict[str, set] = defaultdict(set)
    for i, cl in enumerate(clusters):
        for card in cl["core"]:
            index[card].add(i)

    for i, cl in enumerate(clusters):
        candidates: set = set()
        for card in cl["core"]:
            candidates |= index[card]
        for j in candidates:
            if j <= i:
                continue
            if _jaccard(cl["core"], clusters[j]["core"]) >= merge_threshold:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[rj] = ri

    merged: dict[int, dict] = {}
    for i, cl in enumerate(clusters):
        root = find(i)
        if root not in merged:
            merged[root] = {"counts": Counter(), "size": 0}
        merged[root]["counts"].update(cl["counts"])
        merged[root]["size"] += cl["size"]

    survivors = [m for m in merged.values() if m["size"] >= min_cluster_size]
    survivors.sort(key=lambda m: -m["size"])
    for m in survivors:
        m["core"] = _core_of(m["counts"], m["size"], core_fraction)
    survivors = [m for m in survivors if m["core"]]

    print(f"  {len(clusters):,} leaders → {len(merged):,} merged → "
          f"{len(survivors):,} clusters with ≥ {min_cluster_size} sampled decks")
    if not survivors:
        raise SystemExit(
            "ERROR: no clusters survived merging — thresholds are likely too "
            "strict for this panel. Try lowering --threshold/--min-cluster-size."
        )
    return survivors


# ---------------------------------------------------------------------------
# Step 5: Pass 2 — assign every deck to a surviving cluster
# ---------------------------------------------------------------------------

def assign_decks(
    reps: dict[int, frozenset],
    clusters: list[dict],
    assign_threshold: float,
) -> dict[int, tuple[int | None, float]]:
    """deck_id → (cluster index or None for Other, similarity)."""
    index: dict[str, set] = defaultdict(set)
    for i, cl in enumerate(clusters):
        for card in cl["core"]:
            index[card].add(i)

    assignment: dict[int, tuple[int | None, float]] = {}
    for n_done, (did, rep) in enumerate(sorted(reps.items()), 1):
        best_i, best_sim = None, 0.0
        if rep:
            candidates: set = set()
            for card in rep:
                candidates |= index.get(card, set())
            for i in candidates:
                sim = _jaccard(rep, clusters[i]["core"])
                if sim > best_sim:
                    best_i, best_sim = i, sim
        if best_sim < assign_threshold:
            best_i = None
        assignment[did] = (best_i, round(best_sim, 4))
        if n_done % 20000 == 0:
            print(f"    {n_done:,}/{len(reps):,} decks assigned")
    return assignment


# ---------------------------------------------------------------------------
# Step 6: Labels (top characteristic cards by lift) and output CSVs
# ---------------------------------------------------------------------------

def label_clusters(
    clusters: list[dict],
    assignment: dict[int, tuple[int | None, float]],
    decks: dict[int, frozenset],
    df: Counter,
    min_df: int,
) -> tuple[list[str], list[list[tuple[str, float]]]]:
    """Returns (labels, top_cards) per cluster.

    lift(card | cluster) = P(card | cluster) / P(card | panel), computed on
    full mainboard sets of the decks assigned in pass 2. The label is the top
    3 cards by lift among cards in ≥50% of the cluster's decks.
    """
    n_total = len(decks)
    counts = [Counter() for _ in clusters]
    sizes = [0] * len(clusters)
    for did, (ci, _sim) in assignment.items():
        if ci is not None:
            counts[ci].update(decks[did])
            sizes[ci] += 1

    labels: list[str] = []
    top_cards: list[list[tuple[str, float]]] = []
    for ci in range(len(clusters)):
        size = sizes[ci]
        scored: list[tuple[str, float]] = []
        if size:
            for card, k in counts[ci].items():
                if k / size < 0.5 or df[card] < min_df:
                    continue
                lift = (k / size) / (df[card] / n_total)
                scored.append((card, round(lift, 2)))
            scored.sort(key=lambda t: (-t[1], t[0]))
        top_cards.append(scored[:10])
        labels.append(" / ".join(c for c, _ in scored[:3]) or "(no characteristic cards)")
    return labels, top_cards


def write_deck_clusters(
    out: Path,
    assignment: dict[int, tuple[int | None, float]],
    cluster_ids: list[str],
    labels: list[str],
) -> None:
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["deck_id", "cluster_id", "cluster_label", "similarity"])
        for did in sorted(assignment):
            ci, sim = assignment[did]
            if ci is None:
                w.writerow([did, "Other", "", sim])
            else:
                w.writerow([did, cluster_ids[ci], labels[ci], sim])
    print(f"  deck_clusters.csv: {len(assignment):,} decks")


def write_cluster_summary(
    out: Path,
    cluster_ids: list[str],
    labels: list[str],
    top_cards: list[list[tuple[str, float]]],
    clus_total: dict[str, int],
    clus_wins: dict[str, int],
    n_assigned: dict[str, int],
    n_total: int,
) -> None:
    rows = []
    for key in sorted(n_assigned, key=lambda k: -n_assigned[k]):
        ci = cluster_ids.index(key) if key in cluster_ids else None
        total = clus_total.get(key, 0)
        wins = clus_wins.get(key, 0)
        rows.append({
            "cluster_id":    key,
            "cluster_label": labels[ci] if ci is not None else "",
            "n_decks":       n_assigned[key],
            "pct_of_decks":  round(n_assigned[key] / n_total, 4) if n_total else 0,
            "n_ranked":      total,
            "win_decks":     wins,
            "win_rate":      round(wins / total, 4) if total else 0,
            "top_cards":     "; ".join(f"{c} (lift {l})" for c, l in top_cards[ci]) if ci is not None else "",
        })
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  cluster_summary.csv: {len(rows)} clusters (incl. Other)")


def compute_cluster_stats(
    assignment: dict[int, tuple[int | None, float]],
    cluster_ids: list[str],
    decks: dict[int, frozenset],
    deck_meta: dict[int, dict],
) -> tuple[dict, dict, dict, dict, dict]:
    """Win accumulators over bracket-ranked decks, keyed by cluster id string."""
    clus_total: dict[str, int] = defaultdict(int)
    clus_wins:  dict[str, int] = defaultdict(int)
    clus_card_total: dict[tuple, int] = defaultdict(int)
    clus_card_wins:  dict[tuple, int] = defaultdict(int)
    n_assigned: dict[str, int] = defaultdict(int)

    for did, (ci, _sim) in assignment.items():
        key = cluster_ids[ci] if ci is not None else "Other"
        n_assigned[key] += 1

        rank = bracket_rank(deck_meta.get(did, {}).get("placement", 0))
        if rank is None:
            continue  # skip unranked decks — no win signal
        is_win = rank == 1

        clus_total[key] += 1
        if is_win:
            clus_wins[key] += 1
        for card in decks[did]:
            clus_card_total[(key, card)] += 1
            if is_win:
                clus_card_wins[(key, card)] += 1

    return clus_total, clus_wins, clus_card_total, clus_card_wins, n_assigned


def write_cluster_card_stats(
    out: Path,
    clus_total: dict[str, int],
    clus_wins: dict[str, int],
    clus_card_total: dict[tuple, int],
    clus_card_wins: dict[tuple, int],
    min_with: int,
    min_without: int,
) -> None:
    """Same columns and conventions as archetype_card_stats.csv
    (archetype_cluster.py): 0.5 Laplace smoothing, n ≥ min_with / min_without.
    """
    rows = []
    clus_cards: dict[str, set] = defaultdict(set)
    for (key, card) in clus_card_total:
        clus_cards[key].add(card)

    for key in clus_cards:
        total_clus = clus_total.get(key, 0)
        wins_clus  = clus_wins.get(key, 0)
        clus_win_rate = wins_clus / total_clus if total_clus else 0

        for card in clus_cards[key]:
            with_total = clus_card_total.get((key, card), 0)
            with_wins  = clus_card_wins.get((key, card), 0)
            without_total = total_clus - with_total
            without_wins  = wins_clus  - with_wins
            if with_total < min_with or without_total < min_without:
                continue
            with_odds    = (with_wins + 0.5) / (with_total - with_wins + 0.5)
            without_odds = (without_wins + 0.5) / (without_total - without_wins + 0.5)
            within_log_or = round(math.log(with_odds / without_odds), 3)
            rows.append({
                "archetype":        key,
                "card_name":        card,
                "arch_total":       total_clus,
                "arch_win_rate":    round(clus_win_rate, 4),
                "with_total":       with_total,
                "with_wins":        with_wins,
                "win_rate_with":    round(with_wins / with_total, 4) if with_total else 0,
                "without_total":    without_total,
                "without_wins":     without_wins,
                "win_rate_without": round(without_wins / without_total, 4) if without_total else 0,
                "within_log_or":    within_log_or,
            })

    rows.sort(key=lambda r: (r["archetype"], -r["within_log_or"]))
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "archetype", "card_name", "arch_total", "arch_win_rate",
            "with_total", "with_wins", "win_rate_with",
            "without_total", "without_wins", "win_rate_without", "within_log_or",
        ])
        w.writeheader()
        w.writerows(rows)
    print(f"  cluster_card_stats.csv: {len(rows):,} (cluster, card) pairs")


# ---------------------------------------------------------------------------
# Step 7: Validation against the anchor rules (--validate)
# ---------------------------------------------------------------------------

def validate_against_anchors(
    out: Path,
    assignment: dict[int, tuple[int | None, float]],
    cluster_ids: list[str],
    labels: list[str],
    decks: dict[int, frozenset],
) -> list[dict]:
    """Cross-tabulate inferred clusters vs anchor-rule archetypes.

    Per named archetype: recall = share of its decks in its best single
    cluster; purity = share of that cluster belonging to the archetype;
    clusters_for_90pct = how many clusters it takes to cover 90% of the
    archetype's decks (granularity check — sub-archetype splits are fine).
    Also reports the Other-share drop and the fate of previously-Other decks.
    """
    _, assign_anchor = load_anchor_rules()

    n = len(assignment)
    crosstab: dict[str, Counter] = defaultdict(Counter)  # anchor → cluster key → n
    cluster_size: Counter = Counter()
    for did, (ci, _sim) in assignment.items():
        key = cluster_ids[ci] if ci is not None else "Other"
        anchor = assign_anchor(decks[did])
        crosstab[anchor][key] += 1
        cluster_size[key] += 1

    rows = []
    print("\n  Anchor-archetype recovery:")
    print(f"    {'archetype':<22} {'n':>7}  {'best cluster':<14} {'recall':>7} {'purity':>7}  {'90% needs':>9}")
    for anchor in sorted(crosstab, key=lambda a: -sum(crosstab[a].values())):
        dist = crosstab[anchor]
        n_anchor = sum(dist.values())
        # Best non-Other cluster; fall back to Other only if nothing else exists
        ranked = sorted(dist.items(), key=lambda t: -t[1])
        non_other = [(k, v) for k, v in ranked if k != "Other"]
        best_key, best_n = (non_other[0] if non_other else ranked[0])
        recall = best_n / n_anchor if n_anchor else 0
        purity = best_n / cluster_size[best_key] if cluster_size[best_key] else 0
        cum, needs = 0, 0
        for _k, v in ranked:
            cum += v
            needs += 1
            if cum >= 0.9 * n_anchor:
                break
        best_label = labels[cluster_ids.index(best_key)] if best_key in cluster_ids else ""
        rows.append({
            "archetype":          anchor,
            "n_decks":            n_anchor,
            "best_cluster":       best_key,
            "best_cluster_label": best_label,
            "recall":             round(recall, 4),
            "purity":             round(purity, 4),
            "clusters_for_90pct": needs,
        })
        if anchor != "Other":
            print(f"    {anchor:<22} {n_anchor:>7,}  {best_key:<14} {recall:>6.1%} {purity:>6.1%}  {needs:>9}")

    other_dist = crosstab.get("Other", Counter())
    n_other_anchor = sum(other_dist.values())
    n_other_rescued = n_other_anchor - other_dist.get("Other", 0)
    n_other_inferred = cluster_size.get("Other", 0)
    print(f"\n  'Other' share:  anchor rules {n_other_anchor / n:.1%}  →  "
          f"inferred clusters {n_other_inferred / n:.1%}")
    if n_other_anchor:
        print(f"  Previously-Other decks now in a stable cluster: "
              f"{n_other_rescued:,}/{n_other_anchor:,} ({n_other_rescued / n_other_anchor:.1%})")

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  cluster_validation.csv: {len(rows)} archetypes")
    return rows


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Infer deck archetypes from mainboard co-occurrence structure")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR,
                        help="Data directory containing raw/ (default: ./data)")
    parser.add_argument("--sample", type=int, default=25000,
                        help="Subsample size for pass-1 discovery (default: 25000)")
    parser.add_argument("--threshold", type=float, default=0.35,
                        help="Min Jaccard to join a cluster in pass 1 (default: 0.35)")
    parser.add_argument("--assign-threshold", type=float, default=0.30,
                        help="Min Jaccard for pass-2 assignment; below → Other (default: 0.30)")
    parser.add_argument("--merge-threshold", type=float, default=0.50,
                        help="Min core Jaccard to merge two clusters (default: 0.50)")
    parser.add_argument("--core-fraction", type=float, default=0.50,
                        help="Card must be in this fraction of members to enter the core (default: 0.50)")
    parser.add_argument("--min-df", type=int, default=5,
                        help="Min document frequency for a card to enter the similarity vocab (default: 5)")
    parser.add_argument("--max-df", type=float, default=0.40,
                        help="Max document frequency fraction — format staples above this carry no signal (default: 0.40)")
    parser.add_argument("--min-cluster-size", type=int, default=25,
                        help="Drop discovered clusters smaller than this (default: 25)")
    parser.add_argument("--min-with", type=int, default=20,
                        help="Min decks in cluster WITH the card for log-OR (default: 20)")
    parser.add_argument("--min-without", type=int, default=20,
                        help="Min decks in cluster WITHOUT the card for log-OR (default: 20)")
    parser.add_argument("--seed", type=int, default=17,
                        help="RNG seed for subsampling (default: 17)")
    parser.add_argument("--validate", action="store_true",
                        help="Cross-tabulate inferred clusters against the anchor rules "
                             "in archetype_cluster.py and report archetype recovery")
    args = parser.parse_args(argv)

    raw_dir = args.data_dir / "raw"
    out_dir = args.data_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Step 1/6: Loading decks and event metadata...")
    decks = load_decks(raw_dir)
    deck_meta = build_deck_meta(raw_dir)
    print(f"  {len(decks):,} decks, {len(deck_meta):,} placements indexed")

    print("\nStep 2/6: Building similarity vocabulary...")
    reps, df = build_reps(decks, args.min_df, args.max_df)

    print(f"\nStep 3/6: Pass 1 — leader clustering on ≤{args.sample:,} sampled decks...")
    clusters = discover_clusters(reps, args.sample, args.threshold,
                                 args.core_fraction, args.seed)

    print("\nStep 4/6: Merging near-duplicate clusters...")
    clusters = merge_clusters(clusters, args.merge_threshold,
                              args.core_fraction, args.min_cluster_size)

    print("\nStep 5/6: Pass 2 — assigning all decks...")
    assignment = assign_decks(reps, clusters, args.assign_threshold)
    cluster_ids = [f"C{i + 1:02d}" for i in range(len(clusters))]
    labels, top_cards = label_clusters(clusters, assignment, decks, df, args.min_df)

    n_other = sum(1 for ci, _ in assignment.values() if ci is None)
    print(f"  {len(clusters)} clusters; Other share: {n_other / len(assignment):.1%}")

    print("\nStep 6/6: Writing output CSVs...")
    (clus_total, clus_wins, clus_card_total, clus_card_wins,
     n_assigned) = compute_cluster_stats(assignment, cluster_ids, decks, deck_meta)
    write_deck_clusters(out_dir / "deck_clusters.csv", assignment, cluster_ids, labels)
    write_cluster_summary(out_dir / "cluster_summary.csv", cluster_ids, labels,
                          top_cards, clus_total, clus_wins, n_assigned, len(assignment))
    write_cluster_card_stats(out_dir / "cluster_card_stats.csv",
                             clus_total, clus_wins, clus_card_total, clus_card_wins,
                             args.min_with, args.min_without)

    if args.validate:
        print("\nValidation: cross-tabulating against anchor rules...")
        validate_against_anchors(out_dir / "cluster_validation.csv",
                                 assignment, cluster_ids, labels, decks)

    print(f"\nDone. Outputs in {out_dir}/")


if __name__ == "__main__":
    main()
