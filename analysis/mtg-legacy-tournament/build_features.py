"""
build_features.py — Build card feature dataset from MTGTop8 scrape.

Joins 87K deck files with event placement metadata to produce:

  data/card_stats.csv    — per-card aggregates: appearances, win rates, odds ratio vs field
  data/card_yearly.csv   — per-card per-year stats for time-series and ban-event analysis
  data/cooccurrence.csv  — pairwise mainboard co-occurrence with Jaccard and lift

MTGTop8 bracket placement encoding
───────────────────────────────────
The site uses a non-standard numbering. Distinct values observed:
  1  → rank 1 (winner)           6  → rank 3   10 → rank 5   14 → rank 7
  2  → rank 2 (finalist)         8  → rank 4   12 → rank 6   16 → rank 8  ...
Rule: rank = p if p ≤ 2, else rank = (p − 6) // 2 + 3 for even p ≥ 6.

Bracket finish thresholds used here:
  top1 (win)      placement == 1
  top2 (final)    placement ≤ 2
  top4 (semi)     placement in {1, 2, 6, 8}
  top8 (quarter)  placement in {1, 2, 6, 8, 10, 12, 14, 16}

Win odds ratio
──────────────
Odds ratio of reaching the top-1 relative to the field baseline:
  OR = (top1 / (total − top1)) / (field_top1 / (field_total − field_top1))
  log_OR = log(OR)   (symmetric around 0; positive = better than field)
Prefer this over avg_placement, which regresses toward the field median for
popular cards that appear in a large fraction of all recorded decks.

Min appearances threshold
─────────────────────────
Default: 20.  At n=20 the SE of a ~15% win rate is ≈10 pp; at n=100 it's ≈4 pp.
Setting the floor at 20 retains recently-printed cards, niche sideboard staples,
and the full LLM-labeled primer set (some combo pieces have <50 appearances).
Cards below 20 are pure noise in an 87K-deck, 15-year dataset.
Filter to n ≥ 100 downstream when win-rate precision matters.

Usage:
    uv run python build_features.py [--min-appearances N] [--min-cooccur N]
"""

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime
from itertools import combinations
from pathlib import Path

from tqdm import tqdm

RAW_DIR = Path(__file__).parent / "data" / "raw"
OUT_DIR = Path(__file__).parent / "data"
OUT_DIR.mkdir(exist_ok=True)

YEARS = list(range(2011, 2027))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_date(date_str: str) -> tuple[int | None, str | None]:
    """Parse DD/MM/YY → (year, iso_date). Returns (None, None) on failure."""
    try:
        dt = datetime.strptime(date_str.strip(), "%d/%m/%y")
        return dt.year, dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return None, None


def bracket_rank(placement: int) -> int | None:
    """Convert MTGTop8 placement number to ordinal bracket rank (1=best).

    MTGTop8 encodes bracket results with non-sequential placement numbers:
      1 → 1st, 2 → 2nd, 6 → 3rd, 8 → 4th, 10 → 5th, 12 → 6th, 14 → 7th, 16 → 8th, ...
    Returns None for unexpected values (e.g. 0 = unknown, odd numbers beyond 2).
    """
    if placement == 1:
        return 1
    if placement == 2:
        return 2
    if placement >= 6 and placement % 2 == 0:
        return (placement - 6) // 2 + 3
    return None


# ---------------------------------------------------------------------------
# Step 1: Build deck metadata index from event files
# ---------------------------------------------------------------------------

def build_deck_meta() -> dict[int, dict]:
    """Read all events_YYYY.json files → deck_id → {placement, year, date, ...}."""
    deck_meta: dict[int, dict] = {}
    for year in YEARS:
        path = RAW_DIR / f"events_{year}.json"
        if not path.exists():
            continue
        events = json.loads(path.read_text())
        for event in events:
            event_year, iso_date = parse_date(event.get("date_str", ""))
            yr = event_year or year  # fall back to file year if date missing
            for d in event.get("decks", []):
                did = d["deck_id"]
                if did not in deck_meta:  # first occurrence wins
                    deck_meta[did] = {
                        "placement":    d["placement"],
                        "archetype":    d.get("archetype_name", ""),
                        "year":         yr,
                        "date":         iso_date,
                        "event_id":     event["event_id"],
                        "player_count": event.get("player_count", 0),
                    }
    return deck_meta


# ---------------------------------------------------------------------------
# Step 2: Stream deck files, accumulate stats
# ---------------------------------------------------------------------------

def compute_stats(
    deck_meta: dict[int, dict],
) -> tuple[Counter, Counter, Counter, Counter, Counter, Counter, Counter, Counter, Counter]:
    card_total: Counter = Counter()  # card → total deck appearances
    card_top8:  Counter = Counter()  # card → rank ≤ 8  (quarterfinal or better)
    card_top4:  Counter = Counter()  # card → rank ≤ 4  (semifinal or better)
    card_top2:  Counter = Counter()  # card → rank ≤ 2  (finalist or better)
    card_top1:  Counter = Counter()  # card → rank == 1 (tournament winner)

    yearly_total: Counter = Counter()  # (card, year) → total
    yearly_top8:  Counter = Counter()  # (card, year) → rank ≤ 8
    yearly_top1:  Counter = Counter()  # (card, year) → rank == 1

    cooccur: Counter = Counter()  # (card_a, card_b) → co-occurrence count

    deck_files = sorted(RAW_DIR.glob("deck_*.json"))
    for path in tqdm(deck_files, desc="  reading decks", unit="deck"):
        try:
            deck = json.loads(path.read_text())
        except Exception:
            continue

        did = deck["deck_id"]
        meta = deck_meta.get(did, {})
        placement = meta.get("placement", 0)
        year = meta.get("year")

        # Unique mainboard card names (quantities ignored for presence-based stats)
        cards = {e["card_name"] for e in deck.get("mainboard", []) if e.get("card_name")}
        if not cards:
            continue

        rank = bracket_rank(placement)  # None if placement is 0 or unexpected
        is_top8 = rank is not None and rank <= 8
        is_top4 = rank is not None and rank <= 4
        is_top2 = rank is not None and rank <= 2
        is_top1 = rank == 1

        for card in cards:
            card_total[card] += 1
            if is_top8: card_top8[card] += 1
            if is_top4: card_top4[card] += 1
            if is_top2: card_top2[card] += 1
            if is_top1: card_top1[card] += 1

            if year:
                yearly_total[(card, year)] += 1
                if is_top8: yearly_top8[(card, year)] += 1
                if is_top1: yearly_top1[(card, year)] += 1

        # Pairwise co-occurrence (sorted pair → canonical order, no duplicates)
        cooccur.update(combinations(sorted(cards), 2))

    return (
        card_total, card_top8, card_top4, card_top2, card_top1,
        yearly_total, yearly_top8, yearly_top1,
        cooccur,
    )


# ---------------------------------------------------------------------------
# Step 3: Write CSVs
# ---------------------------------------------------------------------------

def write_card_stats(
    out: Path,
    card_total, card_top8, card_top4, card_top2, card_top1,
    field_top1: int, field_total: int,
    min_appearances: int,
) -> int:
    # Field-level win odds (used for per-card odds ratio)
    field_win_odds = field_top1 / (field_total - field_top1)

    rows = []
    for card, total in card_total.items():
        if total < min_appearances:
            continue
        t1 = card_top1[card]
        t2 = card_top2[card]
        t4 = card_top4[card]
        t8 = card_top8[card]

        # Odds ratio: how much better/worse does this card perform vs. field baseline?
        # OR > 1 → more likely to win than field average; log_OR > 0 same.
        # Add 0.5 Laplace smoothing to avoid divide-by-zero on t1=0 or t1=total.
        card_win_odds = (t1 + 0.5) / (total - t1 + 0.5)
        win_or = card_win_odds / field_win_odds
        log_win_or = round(math.log(win_or), 3)

        rows.append({
            "card_name":   card,
            "total_decks": total,
            "top1_decks":  t1,
            "top2_decks":  t2,
            "top4_decks":  t4,
            "top8_decks":  t8,
            "win_rate":    round(t1 / total, 4),     # P(win | in deck)
            "final_rate":  round(t2 / total, 4),     # P(reach final | in deck)
            "semi_rate":   round(t4 / total, 4),     # P(reach semi | in deck)
            "qf_rate":     round(t8 / total, 4),     # P(reach quarters | in deck)
            "win_log_or":  log_win_or,               # log-odds ratio vs field baseline
        })
    rows.sort(key=lambda r: -r["total_decks"])

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def write_card_yearly(
    out: Path,
    card_total, yearly_total, yearly_top8, yearly_top1,
    min_appearances: int,
) -> int:
    rows = []
    for (card, year), total in yearly_total.items():
        if card_total[card] < min_appearances:
            continue
        t8  = yearly_top8.get((card, year), 0)
        t1  = yearly_top1.get((card, year), 0)
        rows.append({
            "card_name":   card,
            "year":        year,
            "total_decks": total,
            "top8_decks":  t8,
            "top1_decks":  t1,
            "qf_rate":     round(t8 / total, 4) if total else 0,  # rank ≤ 8
            "win_rate":    round(t1 / total, 4) if total else 0,  # rank == 1
        })
    rows.sort(key=lambda r: (r["card_name"], r["year"]))

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def write_cooccurrence(
    out: Path,
    cooccur: Counter,
    card_total: Counter,
    n_decks: int,
    min_appearances: int,
    min_cooccur: int,
) -> int:
    pairs = [
        (a, b, cnt)
        for (a, b), cnt in cooccur.items()
        if cnt >= min_cooccur
        and card_total[a] >= min_appearances
        and card_total[b] >= min_appearances
    ]
    pairs.sort(key=lambda x: -x[2])

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["card_a", "card_b", "cooccur_count", "card_a_total", "card_b_total", "jaccard", "lift"])
        for a, b, cnt in pairs:
            ta = card_total[a]
            tb = card_total[b]
            union = ta + tb - cnt
            jaccard = cnt / union if union else 0
            # Lift = P(A∩B) / (P(A)·P(B)) = (cnt/N) / ((ta/N)·(tb/N)) = cnt·N / (ta·tb)
            lift = (cnt * n_decks) / (ta * tb) if ta and tb else 0
            w.writerow([a, b, cnt, ta, tb, round(jaccard, 4), round(lift, 3)])
    return len(pairs)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build card feature dataset")
    parser.add_argument("--min-appearances", type=int, default=20,
                        help="Min total deck appearances to include a card (default: 20)")
    parser.add_argument("--min-cooccur", type=int, default=20,
                        help="Min co-occurrence count to include a pair (default: 20)")
    args = parser.parse_args()

    print("Step 1/3: Building deck metadata index from event files...")
    deck_meta = build_deck_meta()
    print(f"  {len(deck_meta):,} deck placements indexed")

    n_decks = len(list(RAW_DIR.glob("deck_*.json")))
    print(f"  {n_decks:,} deck files found")

    # Field-level win counts (needed for odds ratio baseline)
    field_top1   = sum(1 for m in deck_meta.values() if bracket_rank(m["placement"]) == 1)
    field_total  = sum(1 for m in deck_meta.values() if bracket_rank(m["placement"]) is not None)
    field_win_rate = field_top1 / field_total if field_total else 0
    print(f"  Field baseline: {field_top1:,} winners / {field_total:,} ranked decks "
          f"= {field_win_rate:.1%} win rate")

    print("\nStep 2/3: Streaming deck files — computing card stats and co-occurrence...")
    (
        card_total, card_top8, card_top4, card_top2, card_top1,
        yearly_total, yearly_top8, yearly_top1,
        cooccur,
    ) = compute_stats(deck_meta)

    print(f"  {len(card_total):,} unique cards across {n_decks:,} decks")
    print(f"  {len(cooccur):,} unique card pairs in co-occurrence counter")

    print("\nStep 3/3: Writing output CSVs...")

    n1 = write_card_stats(
        OUT_DIR / "card_stats.csv",
        card_total, card_top8, card_top4, card_top2, card_top1,
        field_top1, field_total,
        args.min_appearances,
    )
    print(f"  card_stats.csv:    {n1:,} cards (≥{args.min_appearances} appearances)")

    n2 = write_card_yearly(
        OUT_DIR / "card_yearly.csv",
        card_total, yearly_total, yearly_top8, yearly_top1,
        args.min_appearances,
    )
    print(f"  card_yearly.csv:   {n2:,} card-year rows")

    n3 = write_cooccurrence(
        OUT_DIR / "cooccurrence.csv",
        cooccur, card_total, n_decks,
        args.min_appearances, args.min_cooccur,
    )
    print(f"  cooccurrence.csv:  {n3:,} pairs (≥{args.min_cooccur} co-occurrences)")

    print(f"\nDone. Outputs in {OUT_DIR}/")


if __name__ == "__main__":
    main()
