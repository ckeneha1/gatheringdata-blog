"""
archetype_cluster.py — Assign decks to archetypes and compute within-archetype
win log-OR for each (archetype, card) pair.

Archetype assignment
────────────────────
Uses anchor-card rules: each archetype requires a set of "must-have" cards
(all required) plus optionally at least one card from a "discriminator" set.
Priority order matters — a deck is assigned to the first matching archetype.
Unmatched decks are labelled "Other".

Within-archetype win log-OR
────────────────────────────
For each (archetype, card) pair where the card appears in ≥ MIN_WITH decks of
that archetype AND is absent from ≥ MIN_WITHOUT decks:

  within_log_or = log(
      (wins_with + 0.5) / (total_with  - wins_with  + 0.5)
    / (wins_without + 0.5) / (total_without - wins_without + 0.5)
  )

Positive → decks in the archetype that run this card win more often than those
that don't. Negative → the card is a drag within the archetype.

This answers a different question than the format-wide win log-OR in
card_stats.csv. Format-wide: is the card correlated with winning across all
decks? Within-archetype: given you're already playing this strategy, does
adding this card help or hurt?

Outputs
────────
  data/archetype_summary.csv      — archetype deck counts and baseline win rates
  data/archetype_card_stats.csv   — per-archetype per-card win log-OR

Usage
─────
    uv run python archetype_cluster.py [--min-with N] [--min-without N]
"""

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from tqdm import tqdm

RAW_DIR = Path(__file__).parent / "data" / "raw"
OUT_DIR = Path(__file__).parent / "data"

YEARS = list(range(2011, 2027))

# ---------------------------------------------------------------------------
# Archetype definitions — (name, required_all, required_any_or_none)
# Checked in order; first match wins.
# ---------------------------------------------------------------------------

ARCHETYPES: list[tuple[str, frozenset, frozenset | None]] = [
    # Most specific first to avoid false positives from shared card overlap
    (
        "Oops All Spells",
        frozenset({"Balustrade Spy", "Undercity Informer"}),
        None,
    ),
    (
        "Elves",
        frozenset({"Heritage Druid", "Nettle Sentinel"}),
        None,
    ),
    (
        "Miracles",
        frozenset({"Counterbalance"}),
        frozenset({"Terminus", "Entreat the Angels", "Sensei's Divining Top"}),
    ),
    (
        "Sneak and Show",
        frozenset({"Show and Tell"}),
        frozenset({"Sneak Attack", "Omniscience"}),
    ),
    (
        "Lands",
        frozenset({"Life from the Loam"}),
        frozenset({"Dark Depths", "Thespian's Stage"}),
    ),
    (
        "Storm",
        frozenset({"Infernal Tutor", "Dark Ritual"}),
        None,
    ),
    (
        "Reanimator",
        frozenset({"Entomb"}),
        frozenset({"Reanimate", "Exhume", "Animate Dead", "Unearth"}),
    ),
    (
        "Red Prison",
        frozenset({"Blood Moon", "Ancient Tomb", "Trinisphere"}),
        None,
    ),
    (
        "Death and Taxes",
        frozenset({"Thalia, Guardian of Thraben", "Aether Vial"}),
        None,
    ),
    (
        "Dredge",
        frozenset({"Narcomoeba"}),
        frozenset({"Ichorid", "Breakthrough", "Putrid Imp"}),
    ),
    (
        "Delver",
        frozenset({"Daze"}),
        frozenset({"Delver of Secrets", "Dragon's Rage Channeler", "Murktide Regent"}),
    ),
    (
        "Burn",
        frozenset({"Eidolon of the Great Revel"}),
        frozenset({"Chain Lightning", "Price of Progress", "Fireblast"}),
    ),
]


def assign_archetype(cards: set[str]) -> str:
    for name, required_all, required_any in ARCHETYPES:
        if required_all.issubset(cards):
            if required_any is None or cards & required_any:
                return name
    return "Other"


# ---------------------------------------------------------------------------
# Bracket rank (same logic as build_features.py)
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
# Step 1: Build deck metadata from events_{year}.json files
# ---------------------------------------------------------------------------

def build_deck_meta() -> dict[int, dict]:
    deck_meta: dict[int, dict] = {}
    for year in YEARS:
        path = RAW_DIR / f"events_{year}.json"
        if not path.exists():
            continue
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
# Step 2: Stream deck files, assign archetypes, accumulate stats
# ---------------------------------------------------------------------------

def compute_archetype_stats(
    deck_meta: dict[int, dict],
) -> tuple[
    dict[str, int],          # archetype → total decks
    dict[str, int],          # archetype → win decks (rank 1)
    dict[tuple, int],        # (archetype, card) → total decks with card
    dict[tuple, int],        # (archetype, card) → wins with card
]:
    arch_total:     dict[str, int]   = defaultdict(int)
    arch_wins:      dict[str, int]   = defaultdict(int)
    arch_card_total: dict[tuple, int] = defaultdict(int)
    arch_card_wins:  dict[tuple, int] = defaultdict(int)

    deck_files = sorted(RAW_DIR.glob("deck_*.json"))
    for path in tqdm(deck_files, desc="  reading decks", unit="deck"):
        try:
            deck = json.loads(path.read_text())
        except Exception:
            continue

        did = deck["deck_id"]
        meta = deck_meta.get(did, {})
        placement = meta.get("placement", 0)

        cards = {e["card_name"] for e in deck.get("mainboard", []) if e.get("card_name")}
        if not cards:
            continue

        rank = bracket_rank(placement)
        if rank is None:
            continue  # skip unranked decks — no win signal

        is_win = rank == 1
        archetype = assign_archetype(cards)

        arch_total[archetype] += 1
        if is_win:
            arch_wins[archetype] += 1

        for card in cards:
            arch_card_total[(archetype, card)] += 1
            if is_win:
                arch_card_wins[(archetype, card)] += 1

    return arch_total, arch_wins, arch_card_total, arch_card_wins


# ---------------------------------------------------------------------------
# Step 3: Write CSVs
# ---------------------------------------------------------------------------

def write_archetype_summary(
    out: Path,
    arch_total: dict[str, int],
    arch_wins: dict[str, int],
) -> None:
    rows = []
    total_decks = sum(arch_total.values())
    for arch, total in sorted(arch_total.items(), key=lambda x: -x[1]):
        wins = arch_wins.get(arch, 0)
        rows.append({
            "archetype":      arch,
            "total_decks":    total,
            "win_decks":      wins,
            "win_rate":       round(wins / total, 4) if total else 0,
            "pct_of_field":   round(total / total_decks, 4) if total_decks else 0,
        })

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  archetype_summary.csv: {len(rows)} archetypes")


def write_archetype_card_stats(
    out: Path,
    arch_total: dict[str, int],
    arch_wins: dict[str, int],
    arch_card_total: dict[tuple, int],
    arch_card_wins: dict[tuple, int],
    min_with: int,
    min_without: int,
) -> None:
    rows = []

    # Group by archetype for efficient lookups
    arch_cards: dict[str, set] = defaultdict(set)
    for (arch, card) in arch_card_total:
        arch_cards[arch].add(card)

    for arch in arch_cards:
        total_arch  = arch_total.get(arch, 0)
        wins_arch   = arch_wins.get(arch, 0)

        # Archetype-level win odds (for reference only; not used in within log-OR)
        arch_win_rate = wins_arch / total_arch if total_arch else 0

        for card in arch_cards[arch]:
            with_total = arch_card_total.get((arch, card), 0)
            with_wins  = arch_card_wins.get((arch, card), 0)

            without_total = total_arch - with_total
            without_wins  = wins_arch  - with_wins

            if with_total < min_with or without_total < min_without:
                continue

            # Within-archetype win log-OR (Laplace smoothed)
            with_odds    = (with_wins + 0.5) / (with_total - with_wins + 0.5)
            without_odds = (without_wins + 0.5) / (without_total - without_wins + 0.5)
            within_log_or = round(math.log(with_odds / without_odds), 3)

            rows.append({
                "archetype":       arch,
                "card_name":       card,
                "arch_total":      total_arch,
                "arch_win_rate":   round(arch_win_rate, 4),
                "with_total":      with_total,
                "with_wins":       with_wins,
                "win_rate_with":   round(with_wins / with_total, 4) if with_total else 0,
                "without_total":   without_total,
                "without_wins":    without_wins,
                "win_rate_without": round(without_wins / without_total, 4) if without_total else 0,
                "within_log_or":   within_log_or,
            })

    rows.sort(key=lambda r: (r["archetype"], -r["within_log_or"]))

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  archetype_card_stats.csv: {len(rows):,} (archetype, card) pairs")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Cluster decks by archetype and compute within-archetype win log-OR")
    parser.add_argument("--min-with",    type=int, default=20,
                        help="Min decks in archetype WITH the card (default: 20)")
    parser.add_argument("--min-without", type=int, default=20,
                        help="Min decks in archetype WITHOUT the card (default: 20)")
    args = parser.parse_args()

    print("Step 1/3: Building deck metadata from event files...")
    deck_meta = build_deck_meta()
    ranked = sum(1 for m in deck_meta.values() if bracket_rank(m["placement"]) is not None)
    print(f"  {len(deck_meta):,} deck placements indexed ({ranked:,} with a valid bracket rank)")

    print("\nStep 2/3: Assigning archetypes and accumulating stats...")
    arch_total, arch_wins, arch_card_total, arch_card_wins = compute_archetype_stats(deck_meta)

    print(f"\n  Archetype distribution (ranked decks only):")
    total_ranked = sum(arch_total.values())
    for arch, cnt in sorted(arch_total.items(), key=lambda x: -x[1]):
        wins = arch_wins.get(arch, 0)
        wr = wins / cnt if cnt else 0
        print(f"    {arch:<22}  {cnt:6,} decks ({cnt/total_ranked:.1%})  win rate {wr:.1%}")

    print("\nStep 3/3: Writing output CSVs...")
    write_archetype_summary(OUT_DIR / "archetype_summary.csv", arch_total, arch_wins)
    write_archetype_card_stats(
        OUT_DIR / "archetype_card_stats.csv",
        arch_total, arch_wins, arch_card_total, arch_card_wins,
        args.min_with, args.min_without,
    )

    print(f"\nDone. Outputs in {OUT_DIR}/")


if __name__ == "__main__":
    main()
