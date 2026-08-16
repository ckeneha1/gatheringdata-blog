"""
backtest.py — Temporal backtest harness: grade adoption predictions against
the MTGTop8 deck panel (rebuild brief §2.5: train on ≤T, predict post-T
adoption, grade against history).

Predictions file format
───────────────────────
CSV (or a JSON list of objects) with these columns — this same format grades
the Marvel Super Heroes predictions in analysis/legacy-framework/predictions/
in August 2026:

  card_name          exact card name as it appears on MTGTop8 decklists
  predicted_verdict  PLAYED | FRINGE | NOT_PLAYED  ("NOT PLAYED" accepted)
  archetype          named archetype context, or empty for a format-wide
                     (cross-archetype) claim
  as_of_date         ISO YYYY-MM-DD — first day of the grading window
                     (prediction must have been locked before this date)
  window_end         optional ISO date; defaults to as_of_date + --window-days.
                     Automatically clipped to the card's Legacy ban date if it
                     has one (see LEGACY_BANS) — a banned card stops accruing
                     adoption, so a window running past the ban dilutes every
                     rate with decks that could not have played it.

Grading logic (operational definitions registered in
analysis/legacy-framework/predictions/framework-verdicts-msh.md)
────────────────────────────────────────────────────────────────
For each (card, window):
  (a) share of all panel decks in the window containing the card
  (b) share within the named archetype's lists
  (c) within-archetype win log-OR, 0.5 Laplace smoothing, reported only when
      n ≥ --min-with decks with AND n ≥ --min-without without the card
      (same conventions as build_features.py / archetype_cluster.py)

  actual verdict:
    NOT_PLAYED  card appears in ≤ 2 lists format-wide in the window
                ("zero appearances, or ≤2 isolated lists")
    PLAYED      archetype claim: in ≥ 25% of the archetype's lists;
                format-wide claim: in ≥ 2% of all decks
    FRINGE      anything in between (>2 lists but below the PLAYED bar)
  Tie-break: the ≤2-isolated-lists rule is checked first, so 2 lists in a
  4-deck archetype grade NOT_PLAYED, not PLAYED.

Archetype membership is resolved per prediction, in this order:
  1. --clusters deck_clusters.csv (from infer_archetypes.py): archetype
     matches a cluster_id or cluster_label (case-insensitive, exact)
  2. the 12 anchor-rule archetypes in archetype_cluster.py (exact name)
  3. substring match on the MTGTop8 archetype_name recorded in the event
     metadata (case-insensitive) — covers names like "Merfolk" or "8-Cast"
     that have no anchor rule

Holdout mode (--holdout T)
──────────────────────────
Lists every card first printed after year T that appears in the panel and
writes a predictions-file scaffold (predicted_verdict left blank) for the
model to fill in, so the train-on-≤T → grade-post-T loop closes. Printing
years come from public/data/mtg-card-power-rankings.csv (first_print_year
column, committed to the repo). That file excludes lands, X-cost and
zero-ability cards by construction, so coverage gaps are reported; pass
--release-dates JSON ({card_name: "YYYY-MM-DD" | year}) to supply exact
dates — the owner can generate it from the Scryfall all_cards bulk cache in
analysis/mtg-card-power (released_at per printing, min per oracle_id).

Worked example — the historical roster from the rebuild brief §2.5
(Wrenn and Six 2019, Uro 2020, Expressive Iteration 2021, Murktide Regent
2021, Initiative creatures 2022, Flow State 2026):

    uv run python backtest.py --write-example data/backtest_roster.csv
    uv run python backtest.py --predictions data/backtest_roster.csv

The example file carries the historical consensus (all PLAYED) as
predicted_verdict — it calibrates the *grader* (all six should grade PLAYED
in their windows). The Phase-1.4 model's own train-on-≤T verdicts replace
that column for the real backtest record.

Outputs
────────
  data/backtest_grades.csv       — per-prediction grading (default --out)
  data/backtest_holdout_{T}.csv  — holdout scaffold (with --holdout)

Usage
─────
    uv run python backtest.py --predictions FILE [--clusters data/deck_clusters.csv]
                              [--window-days 60] [--out PATH]
    uv run python backtest.py --holdout 2018 [--rankings PATH] [--release-dates PATH]
    uv run python backtest.py --write-example PATH
"""

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
RANKINGS_CSV = Path(__file__).parent.parent.parent / "public" / "data" / "mtg-card-power-rankings.csv"

VERDICTS = ("PLAYED", "FRINGE", "NOT_PLAYED")
PLAYED_ARCHETYPE_SHARE = 0.25   # ≥25% of the named archetype's lists
PLAYED_FIELD_SHARE     = 0.02   # ≥2% of all decks (cross-archetype claims)
NOT_PLAYED_MAX_LISTS   = 2      # ≤2 isolated lists format-wide

PREDICTION_COLUMNS = ("card_name", "predicted_verdict", "archetype", "as_of_date")

# Legacy ban dates, keyed by exact MTGTop8 card name. A banned card stops
# accruing adoption on its effective date, so any grading window that runs past
# the ban mixes in decks that could not have played it — every share and the
# within-archetype log-OR get pulled toward zero. load_predictions clips
# window_end here so the clipping is enforced rather than remembered; the
# EXAMPLE_ROSTER below has always applied it by hand.
#
# Convention: clip *to* the effective date inclusive, matching the committed
# roster (White Plume Adventurer → 2023-03-06, its effective date). Events on
# the effective date itself are a one-day boundary ambiguity, immaterial next
# to a multi-week window; revisit only if a window ever gets that short.
LEGACY_BANS = {
    "Uro, Titan of Nature's Wrath": date(2021, 3, 15),
    "Expressive Iteration":         date(2023, 3, 6),
    "White Plume Adventurer":       date(2023, 3, 6),
    "Candelabra of Tawnos":         date(2026, 6, 29),
    "The Fantasticar":              date(2026, 8, 10),
}

# Historical roster from the rebuild brief §2.5. predicted_verdict = the known
# historical outcome (PLAYED), used to calibrate the grader; the model's own
# verdicts replace it for the real backtest. Dates: as_of_date = paper release
# of the printing set; window_end = one year later, clipped before any Legacy
# ban of the card (Uro banned 2021-03-15; Expressive Iteration and White Plume
# Adventurer banned 2023-03-06). Flow State's release date is provisional —
# set it to the real 2026 release before grading.
EXAMPLE_ROSTER = [
    {"card_name": "Wrenn and Six",                "predicted_verdict": "PLAYED", "archetype": "Lands",  "as_of_date": "2019-06-14", "window_end": "2020-06-14"},
    {"card_name": "Uro, Titan of Nature's Wrath", "predicted_verdict": "PLAYED", "archetype": "",       "as_of_date": "2020-01-24", "window_end": "2021-01-24"},
    {"card_name": "Expressive Iteration",         "predicted_verdict": "PLAYED", "archetype": "Delver", "as_of_date": "2021-04-23", "window_end": "2022-04-23"},
    {"card_name": "Murktide Regent",              "predicted_verdict": "PLAYED", "archetype": "Delver", "as_of_date": "2021-06-18", "window_end": "2022-06-18"},
    {"card_name": "White Plume Adventurer",       "predicted_verdict": "PLAYED", "archetype": "",       "as_of_date": "2022-06-10", "window_end": "2023-03-06"},
    {"card_name": "Seasoned Dungeoneer",          "predicted_verdict": "PLAYED", "archetype": "",       "as_of_date": "2022-06-10", "window_end": "2023-06-10"},
    {"card_name": "Flow State",                   "predicted_verdict": "PLAYED", "archetype": "",       "as_of_date": "2026-01-01", "window_end": "2026-12-31"},
]


# ---------------------------------------------------------------------------
# Shared helpers (same conventions as the existing pipeline)
# ---------------------------------------------------------------------------

def bracket_rank(placement: int) -> int | None:
    """MTGTop8 placement → ordinal bracket rank (same as build_features.py)."""
    if placement == 1:
        return 1
    if placement == 2:
        return 2
    if placement >= 6 and placement % 2 == 0:
        return (placement - 6) // 2 + 3
    return None


def parse_event_date(date_str: str) -> date | None:
    """Parse MTGTop8 DD/MM/YY date strings."""
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%y").date()
    except (ValueError, AttributeError):
        return None


def parse_iso_date(s: str, context: str) -> date:
    try:
        return date.fromisoformat(s.strip())
    except (ValueError, AttributeError):
        raise SystemExit(f"ERROR: {context}: expected ISO date YYYY-MM-DD, got {s!r}")


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation, front face of DFCs (same as analyze.py;
    copied here to avoid importing analyze.py's matplotlib/requests stack)."""
    name = name.split(" // ")[0]
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9 ]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def within_log_or(with_total: int, with_wins: int,
                  without_total: int, without_wins: int) -> float:
    """Within-context win log-OR, 0.5 Laplace smoothing (archetype_cluster.py
    conventions)."""
    with_odds    = (with_wins + 0.5) / (with_total - with_wins + 0.5)
    without_odds = (without_wins + 0.5) / (without_total - without_wins + 0.5)
    return round(math.log(with_odds / without_odds), 3)


def map_verdict(n_all_with: int, n_all: int,
                n_arch_with: int | None, n_arch: int | None) -> str:
    """Map window counts to a graded verdict per the operational definitions
    in framework-verdicts-msh.md. Pass n_arch=None for format-wide claims."""
    if n_all_with <= NOT_PLAYED_MAX_LISTS:
        return "NOT_PLAYED"
    if n_arch is not None:
        if n_arch > 0 and (n_arch_with or 0) / n_arch >= PLAYED_ARCHETYPE_SHARE:
            return "PLAYED"
    elif n_all > 0 and n_all_with / n_all >= PLAYED_FIELD_SHARE:
        return "PLAYED"
    return "FRINGE"


# ---------------------------------------------------------------------------
# Panel loading
# ---------------------------------------------------------------------------

def load_panel(raw_dir: Path, zone: str) -> dict[int, dict]:
    """Load the deck panel: deck_id → {cards, date, placement, mtgtop8_archetype}.

    zone: "mainboard" or "both" — which zones count as the card appearing in
    the list. Decks with no parseable event date are dropped (cannot be
    placed in a grading window).
    """
    if not raw_dir.is_dir():
        raise SystemExit(
            f"ERROR: raw data directory not found: {raw_dir}\n"
            "Expected the MTGTop8 scrape cache (deck_*.json, events_*.json) "
            "produced by fetch_data.py. This dataset is gitignored and lives "
            "on the owner's machine only."
        )
    event_files = sorted(raw_dir.glob("events_*.json"))
    if not event_files:
        raise SystemExit(f"ERROR: no events_*.json files in {raw_dir} — run fetch_data.py first.")

    meta: dict[int, dict] = {}
    for path in event_files:
        events = json.loads(path.read_text())
        for event in events:
            event_date = parse_event_date(event.get("date_str", ""))
            for d in event.get("decks", []):
                did = d["deck_id"]
                if did not in meta:
                    meta[did] = {
                        "date":              event_date,
                        "placement":         d.get("placement", 0),
                        "mtgtop8_archetype": d.get("archetype_name", ""),
                    }

    panel: dict[int, dict] = {}
    n_files = 0
    n_undated = 0
    for path in sorted(raw_dir.glob("deck_*.json")):
        n_files += 1
        try:
            deck = json.loads(path.read_text())
            did = deck["deck_id"]
        except Exception:
            print(f"  WARNING: skipping unreadable/malformed deck file {path.name} "
                  "(expected schema: {deck_id, mainboard: [{card_name, quantity}]})")
            continue
        zones = ("mainboard",) if zone == "mainboard" else ("mainboard", "sideboard")
        cards = frozenset(
            e["card_name"] for z in zones for e in deck.get(z, []) if e.get("card_name")
        )
        m = meta.get(did)
        if m is None or m["date"] is None:
            n_undated += 1
            continue
        if not cards:
            continue
        panel[did] = {"cards": cards, **m}
        if n_files % 10000 == 0:
            print(f"    {n_files:,} deck files read")

    if not panel:
        raise SystemExit(
            f"ERROR: no datable decks assembled from {raw_dir} — check that "
            "events_*.json files contain date_str (DD/MM/YY) and deck refs."
        )
    print(f"  panel: {len(panel):,} datable decks "
          f"({n_undated:,} skipped: no event date or no cached deck meta)")
    return panel


# ---------------------------------------------------------------------------
# Archetype membership
# ---------------------------------------------------------------------------

def load_clusters(path: Path) -> dict[int, tuple[str, str]]:
    """Read deck_clusters.csv (from infer_archetypes.py) → deck_id →
    (cluster_id, cluster_label)."""
    if not path.exists():
        raise SystemExit(f"ERROR: cluster assignment file not found: {path}\n"
                         "Run infer_archetypes.py first, or omit --clusters.")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"deck_id", "cluster_id", "cluster_label"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"ERROR: {path} is missing expected columns: {sorted(missing)} "
                             f"(expected the deck_clusters.csv written by infer_archetypes.py)")
        return {int(r["deck_id"]): (r["cluster_id"], r["cluster_label"]) for r in reader}


def build_archetype_matcher(panel: dict[int, dict],
                            clusters: dict[int, tuple[str, str]] | None):
    """Return match(deck_id, archetype_name) → bool, plus a resolver-name
    function for reporting which source resolved each archetype name."""
    try:
        from infer_archetypes import load_anchor_rules
        _, assign_anchor = load_anchor_rules()
        anchor_names = {name.lower() for name, _, _ in
                        __import__("archetype_cluster").ARCHETYPES}
    except Exception as exc:  # archetype_cluster.py missing/unimportable
        print(f"  WARNING: anchor rules unavailable ({exc}) — "
              "falling back to MTGTop8 archetype names only")
        assign_anchor = None
        anchor_names = set()

    anchor_cache: dict[int, str] = {}

    def resolver_for(arch: str) -> str:
        a = arch.lower()
        if clusters is not None and any(
                a in (cid.lower(), label.lower()) for cid, label in set(clusters.values())):
            return "clusters"
        if assign_anchor is not None and a in anchor_names:
            return "anchor_rules"
        return "mtgtop8_name"

    def match(did: int, arch: str, resolver: str) -> bool:
        a = arch.lower()
        if resolver == "clusters":
            cid, label = clusters.get(did, ("Other", ""))
            return a in (cid.lower(), label.lower())
        if resolver == "anchor_rules":
            if did not in anchor_cache:
                anchor_cache[did] = assign_anchor(panel[did]["cards"])
            return anchor_cache[did].lower() == a
        return a in panel[did]["mtgtop8_archetype"].lower()

    return match, resolver_for


# ---------------------------------------------------------------------------
# Predictions loading
# ---------------------------------------------------------------------------

def load_predictions(path: Path, window_days: int) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"ERROR: predictions file not found: {path}")

    if path.suffix.lower() == ".json":
        records = json.loads(path.read_text())
        if not isinstance(records, list):
            raise SystemExit(f"ERROR: {path}: expected a JSON list of prediction objects")
    else:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            missing = set(PREDICTION_COLUMNS) - set(reader.fieldnames or [])
            if missing:
                raise SystemExit(
                    f"ERROR: {path} is missing expected columns: {sorted(missing)}\n"
                    f"Required columns: {', '.join(PREDICTION_COLUMNS)} "
                    f"(optional: window_end). See the module docstring for the format."
                )
            records = list(reader)

    preds = []
    for i, r in enumerate(records, 1):
        ctx = f"{path.name} row {i}"
        for col in PREDICTION_COLUMNS:
            if col not in r:
                raise SystemExit(f"ERROR: {ctx}: missing field {col!r}")
        verdict = (r["predicted_verdict"] or "").strip().upper().replace(" ", "_").replace("-", "_")
        if verdict not in VERDICTS:
            raise SystemExit(f"ERROR: {ctx}: predicted_verdict must be one of "
                             f"{'/'.join(VERDICTS)}, got {r['predicted_verdict']!r}")
        as_of = parse_iso_date(r["as_of_date"], f"{ctx} as_of_date")
        end_raw = (r.get("window_end") or "").strip()
        end = (parse_iso_date(end_raw, f"{ctx} window_end") if end_raw
               else as_of + timedelta(days=window_days))
        if end < as_of:
            raise SystemExit(f"ERROR: {ctx}: window_end {end} precedes as_of_date {as_of}")
        name = r["card_name"].strip()
        ban = LEGACY_BANS.get(name)
        if ban is not None:
            if ban <= as_of:
                raise SystemExit(
                    f"ERROR: {ctx}: {name} was banned in Legacy on {ban}, on or before "
                    f"as_of_date {as_of} — the whole window is post-ban and gradeable "
                    "adoption is zero by construction. Fix the window or drop the row.")
            if end > ban:
                print(f"  NOTE: {ctx}: clipping window_end {end} → {ban} "
                      f"({name} banned in Legacy) — post-ban decks cannot play it.")
                end = ban
        preds.append({
            "card_name": name,
            "predicted_verdict": verdict,
            "archetype": (r["archetype"] or "").strip(),
            "as_of_date": as_of,
            "window_end": end,
        })
    if not preds:
        raise SystemExit(f"ERROR: {path} contains no predictions")
    return preds


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------

def grade_predictions(
    preds: list[dict],
    panel: dict[int, dict],
    clusters: dict[int, tuple[str, str]] | None,
    min_with: int,
    min_without: int,
) -> list[dict]:
    match, resolver_for = build_archetype_matcher(panel, clusters)
    all_cards_ever = frozenset().union(*(d["cards"] for d in panel.values()))

    rows = []
    for p in preds:
        card, arch = p["card_name"], p["archetype"]
        start, end = p["as_of_date"], p["window_end"]
        if card not in all_cards_ever:
            print(f"  NOTE: {card!r} never appears anywhere in the panel — "
                  "verify the spelling matches MTGTop8 (or the card truly saw zero play).")

        resolver = resolver_for(arch) if arch else ""
        window = [did for did, d in panel.items() if start <= d["date"] <= end]

        n_all = len(window)
        n_all_with = sum(1 for did in window if card in panel[did]["cards"])
        if arch:
            arch_ids = [did for did in window if match(did, arch, resolver)]
            n_arch = len(arch_ids)
            n_arch_with = sum(1 for did in arch_ids if card in panel[did]["cards"])
            if n_arch == 0:
                print(f"  WARNING: archetype {arch!r} matched 0 decks in window "
                      f"{start}..{end} (resolved via {resolver}) — "
                      "check the name against cluster labels / anchor names / MTGTop8 names.")
        else:
            arch_ids, n_arch, n_arch_with = [], None, None

        actual = map_verdict(n_all_with, n_all, n_arch_with, n_arch)

        # Within-context win log-OR over bracket-ranked decks in the window.
        # Conditioning set = the named archetype, or the whole field for
        # format-wide claims.
        context_ids = arch_ids if arch else window
        ranked = [did for did in context_ids
                  if bracket_rank(panel[did]["placement"]) is not None]
        with_total = sum(1 for did in ranked if card in panel[did]["cards"])
        with_wins = sum(1 for did in ranked
                        if card in panel[did]["cards"]
                        and bracket_rank(panel[did]["placement"]) == 1)
        without_total = len(ranked) - with_total
        without_wins = sum(1 for did in ranked
                           if bracket_rank(panel[did]["placement"]) == 1) - with_wins
        if with_total >= min_with and without_total >= min_without:
            log_or = within_log_or(with_total, with_wins, without_total, without_wins)
        else:
            log_or = ""  # insufficient n — reported blank, thresholds per build_features.py

        rows.append({
            "card_name":          card,
            "archetype":          arch,
            "archetype_source":   resolver,
            "as_of_date":         start.isoformat(),
            "window_end":         end.isoformat(),
            "predicted_verdict":  p["predicted_verdict"],
            "actual_verdict":     actual,
            "correct":            int(p["predicted_verdict"] == actual),
            "n_decks_window":     n_all,
            "n_decks_with_card":  n_all_with,
            "share_all":          round(n_all_with / n_all, 4) if n_all else 0,
            "n_archetype_decks":  n_arch if n_arch is not None else "",
            "n_archetype_with":   n_arch_with if n_arch_with is not None else "",
            "share_archetype":    (round(n_arch_with / n_arch, 4)
                                   if n_arch else ""),
            "within_log_or":      log_or,
            "log_or_n_with":      with_total,
            "log_or_n_without":   without_total,
        })
    return rows


def write_grades(out: Path, rows: list[dict]) -> None:
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  backtest grades: {len(rows)} predictions → {out}")


def print_scorecard(rows: list[dict]) -> None:
    n = len(rows)
    n_correct = sum(r["correct"] for r in rows)
    print(f"\nScorecard: {n_correct}/{n} correct ({n_correct / n:.0%})")
    print(f"  {'card':<32} {'archetype':<12} {'predicted':<11} {'actual':<11} "
          f"{'share_all':>9} {'share_arch':>10} {'log_OR':>7}")
    for r in rows:
        mark = "+" if r["correct"] else "x"
        print(f"  {r['card_name'][:32]:<32} {str(r['archetype'])[:12]:<12} "
              f"{r['predicted_verdict']:<11} {r['actual_verdict']:<11} "
              f"{r['share_all']:>9} {str(r['share_archetype']):>10} "
              f"{str(r['within_log_or']):>7}  {mark}")
    confusion: dict[tuple, int] = defaultdict(int)
    for r in rows:
        confusion[(r["predicted_verdict"], r["actual_verdict"])] += 1
    print("\n  Confusion (predicted → actual):")
    for (pv, av), cnt in sorted(confusion.items()):
        print(f"    {pv:<11} → {av:<11}  {cnt}")


# ---------------------------------------------------------------------------
# Holdout mode — list post-T printings and produce the grading scaffold
# ---------------------------------------------------------------------------

def load_print_years(rankings_path: Path,
                     release_dates_path: Path | None) -> dict[str, tuple[int, str | None]]:
    """normalized card name → (first_print_year, exact_release_date_or_None).

    Primary source: the committed power-rankings CSV (first_print_year
    column). Optional --release-dates JSON ({card_name: "YYYY-MM-DD" | year})
    supplements and overrides it with exact dates.
    """
    years: dict[str, tuple[int, str | None]] = {}
    if not rankings_path.exists():
        raise SystemExit(
            f"ERROR: rankings file not found: {rankings_path}\n"
            "Expected public/data/mtg-card-power-rankings.csv (columns: name, "
            "first_print_year, ...) — committed to the repo, or pass --rankings."
        )
    with open(rankings_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = {"name", "first_print_year"} - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"ERROR: {rankings_path} is missing expected columns: "
                             f"{sorted(missing)} (expected name, first_print_year)")
        for r in reader:
            try:
                years[normalize_name(r["name"])] = (int(float(r["first_print_year"])), None)
            except (ValueError, TypeError):
                continue

    if release_dates_path is not None:
        if not release_dates_path.exists():
            raise SystemExit(f"ERROR: release-dates file not found: {release_dates_path}")
        data = json.loads(release_dates_path.read_text())
        if not isinstance(data, dict):
            raise SystemExit(f"ERROR: {release_dates_path}: expected a JSON object "
                             '{card_name: "YYYY-MM-DD" | year}')
        for name, val in data.items():
            if isinstance(val, int):
                years[normalize_name(name)] = (val, None)
            else:
                d = parse_iso_date(str(val), f"{release_dates_path.name} entry {name!r}")
                years[normalize_name(name)] = (d.year, d.isoformat())
    return years


def run_holdout(panel: dict[int, dict], holdout_year: int,
                print_years: dict[str, tuple[int, str | None]],
                out: Path, min_lists: int) -> list[dict]:
    """Write a predictions-file scaffold for every card first printed after
    the holdout year that shows up in the panel."""
    card_lists: dict[str, int] = defaultdict(int)
    first_seen: dict[str, date] = {}
    for d in panel.values():
        for card in d["cards"]:
            card_lists[card] += 1
            if card not in first_seen or d["date"] < first_seen[card]:
                first_seen[card] = d["date"]

    n_unknown = sum(1 for c in card_lists if normalize_name(c) not in print_years)
    print(f"  {len(card_lists):,} distinct cards in panel; "
          f"{n_unknown:,} have no known printing year "
          "(rankings CSV excludes lands/X-cost/zero-ability cards — "
          "pass --release-dates to fill the gaps)")

    rows = []
    for card, n_lists in sorted(card_lists.items()):
        info = print_years.get(normalize_name(card))
        if info is None:
            continue
        year, exact = info
        if year <= holdout_year or n_lists < min_lists:
            continue
        as_of = exact or f"{year}-01-01"
        end = (parse_iso_date(as_of, f"as_of for {card}") + timedelta(days=365)).isoformat()
        rows.append({
            "card_name":         card,
            "predicted_verdict": "",          # ← model fills this in
            "archetype":         "",          # ← optional archetype claim
            "as_of_date":        as_of,
            "window_end":        end,
            "first_print_year":  year,
            "n_lists_total":     n_lists,
            "first_seen_date":   first_seen[card].isoformat(),
        })
    rows.sort(key=lambda r: (r["first_print_year"], -r["n_lists_total"]))

    if not rows:
        print(f"  WARNING: no panel cards first printed after {holdout_year} "
              f"with ≥ {min_lists} lists — nothing to scaffold.")
        return rows
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  holdout T={holdout_year}: {len(rows)} post-{holdout_year} cards → {out}")
    print("  Fill predicted_verdict (train on ≤T data only!) and grade with: "
          f"backtest.py --predictions {out}")
    return rows


def write_example(out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["card_name", "predicted_verdict",
                                          "archetype", "as_of_date", "window_end"])
        w.writeheader()
        w.writerows(EXAMPLE_ROSTER)
    print(f"Wrote worked-example roster ({len(EXAMPLE_ROSTER)} historical cases) → {out}")
    print("Grade it with:  uv run python backtest.py --predictions " + str(out))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Grade card-adoption predictions against the MTGTop8 deck panel")
    parser.add_argument("--predictions", type=Path,
                        help="Predictions CSV/JSON (see module docstring for format)")
    parser.add_argument("--holdout", type=int, metavar="T",
                        help="List cards first printed after year T and write a "
                             "predictions scaffold for them")
    parser.add_argument("--write-example", type=Path, metavar="PATH",
                        help="Write the worked-example historical roster (brief §2.5) and exit")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR,
                        help="Data directory containing raw/ (default: ./data)")
    parser.add_argument("--clusters", type=Path,
                        help="deck_clusters.csv from infer_archetypes.py — resolve "
                             "archetype names against inferred clusters first")
    parser.add_argument("--rankings", type=Path, default=RANKINGS_CSV,
                        help="Power-rankings CSV with first_print_year (holdout mode)")
    parser.add_argument("--release-dates", type=Path,
                        help='JSON {card_name: "YYYY-MM-DD" | year} with exact release '
                             "dates (holdout mode; overrides the rankings CSV)")
    parser.add_argument("--out", type=Path,
                        help="Output CSV (default: data/backtest_grades.csv or "
                             "data/backtest_holdout_{T}.csv)")
    parser.add_argument("--window-days", type=int, default=60,
                        help="Grading window length when window_end is omitted (default: 60)")
    parser.add_argument("--zone", choices=["both", "mainboard"], default="both",
                        help='Zones that count as "appears in the list" (default: both)')
    parser.add_argument("--min-with", type=int, default=20,
                        help="Min decks WITH the card for the log-OR to be reported (default: 20)")
    parser.add_argument("--min-without", type=int, default=20,
                        help="Min decks WITHOUT the card for the log-OR to be reported (default: 20)")
    parser.add_argument("--min-lists", type=int, default=3,
                        help="Holdout mode: min total lists for a card to enter the scaffold (default: 3)")
    args = parser.parse_args(argv)

    if args.write_example:
        write_example(args.write_example)
        return

    if not args.predictions and args.holdout is None:
        parser.error("one of --predictions, --holdout or --write-example is required")

    print("Loading deck panel...")
    panel = load_panel(args.data_dir / "raw", args.zone)

    if args.holdout is not None:
        print(f"\nHoldout mode: cards first printed after {args.holdout}")
        print_years = load_print_years(args.rankings, args.release_dates)
        out = args.out or args.data_dir / f"backtest_holdout_{args.holdout}.csv"
        run_holdout(panel, args.holdout, print_years, out, args.min_lists)
        return

    print("\nLoading predictions...")
    preds = load_predictions(args.predictions, args.window_days)
    print(f"  {len(preds)} predictions from {args.predictions}")
    clusters = load_clusters(args.clusters) if args.clusters else None

    print("\nGrading...")
    rows = grade_predictions(preds, panel, clusters, args.min_with, args.min_without)
    out = args.out or args.data_dir / "backtest_grades.csv"
    write_grades(out, rows)
    print_scorecard(rows)


if __name__ == "__main__":
    main()
