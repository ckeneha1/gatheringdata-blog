"""
build_field_snapshots.py — field-composition snapshots from the tournament panel.

Per brief §2.2, every observation must be stamped with the FIELD snapshot:
the empirical archetype-prevalence distribution at observation time. This
script materializes that as a date-indexed lookup table that
build_exclusions.py (and later the conditional value model) joins against.

Input (gitignored — exists on the owner's machine only):
    ../mtg-legacy-tournament/data/decks.csv
        produced by `uv run python build_dataset.py` in
        analysis/mtg-legacy-tournament; one row per (deck, card, zone) with
        columns: event_id, event_name, event_date, player_count, star_count,
        placement, deck_id, archetype_name, card_name, quantity, zone, legal

Output:
    data/field_snapshots.csv — one row per (snapshot_date, archetype):
        snapshot_date  ISO date (first of each month, from panel start to end)
        window_start   ISO date — snapshot covers [window_start, snapshot_date)
        n_decks        decks in the window (all archetypes)
        archetype      MTGTop8 archetype_name (raw panel label; archetype
                       inference is Phase 1.2's job — these are field shares,
                       not the inferred clusters)
        deck_count     decks of this archetype in the window
        share          deck_count / n_decks

Snapshot semantics: a snapshot dated D summarizes the trailing WINDOW_DAYS
days strictly BEFORE D, so looking up the latest snapshot_date ≤ primer_date
never leaks post-primer field information into the conditioning set.

Run:  uv run python build_field_snapshots.py [--window-days 90]
"""

import argparse
import csv
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
PANEL_DECKS_CSV = Path(__file__).parent.parent / "mtg-legacy-tournament" / "data" / "decks.csv"
OUTPUT_CSV = DATA_DIR / "field_snapshots.csv"

REQUIRED_COLUMNS = {"deck_id", "event_date", "archetype_name"}
DEFAULT_WINDOW_DAYS = 90


class SchemaError(RuntimeError):
    pass


def load_panel_decks(path: Path = PANEL_DECKS_CSV) -> list[tuple[date, str]]:
    """
    Stream decks.csv and return one (event_date, archetype_name) per deck_id.
    Rows without a parseable event_date are skipped (counted in a warning).
    """
    if not path.exists():
        raise SchemaError(
            f"Tournament panel not found: {path}\n"
            "This file is gitignored and lives on the owner's machine. Produce it with:\n"
            "  cd analysis/mtg-legacy-tournament && uv run python build_dataset.py"
        )

    decks: dict[str, tuple[date, str]] = {}
    undated = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise SchemaError(
                f"{path} is missing expected columns: {sorted(missing)}\n"
                f"Found columns: {reader.fieldnames}\n"
                "Expected the decks.csv schema produced by "
                "analysis/mtg-legacy-tournament/build_dataset.py"
            )
        for row in reader:
            deck_id = row["deck_id"]
            if deck_id in decks:
                continue  # one row per deck — card rows repeat deck attributes
            raw = (row["event_date"] or "").strip()
            try:
                d = date.fromisoformat(raw)
            except ValueError:
                undated += 1
                decks[deck_id] = (date.min, "")  # mark seen; excluded below
                continue
            decks[deck_id] = (d, row["archetype_name"] or "Unknown")

    out = [(d, a) for d, a in decks.values() if d != date.min]
    if undated:
        print(f"  WARNING: {undated:,} decks had no parseable event_date — excluded")
    print(f"  Panel: {len(out):,} dated decks")
    return out


def month_starts(start: date, end: date) -> list[date]:
    """First-of-month dates from the month AFTER start's month through end's next month."""
    months = []
    y, m = start.year, start.month
    # first snapshot is the first month boundary after the panel starts
    m += 1
    if m > 12:
        y, m = y + 1, 1
    cur = date(y, m, 1)
    while cur <= end + timedelta(days=31):
        months.append(cur)
        y, m = (cur.year, cur.month + 1) if cur.month < 12 else (cur.year + 1, 1)
        cur = date(y, m, 1)
    return months


def compute_snapshots(
    decks: list[tuple[date, str]],
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> list[dict]:
    """Monthly trailing-window archetype shares. Pure function — unit-testable."""
    if not decks:
        return []
    dates = [d for d, _ in decks]
    rows: list[dict] = []
    for snap in month_starts(min(dates), max(dates)):
        window_start = snap - timedelta(days=window_days)
        in_window = [a for d, a in decks if window_start <= d < snap]
        n = len(in_window)
        if n == 0:
            continue
        for archetype, count in sorted(Counter(in_window).items(), key=lambda kv: -kv[1]):
            rows.append({
                "snapshot_date": snap.isoformat(),
                "window_start": window_start.isoformat(),
                "n_decks": n,
                "archetype": archetype,
                "deck_count": count,
                "share": round(count / n, 6),
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build field-composition snapshots from the tournament panel")
    parser.add_argument("--window-days", type=int, default=DEFAULT_WINDOW_DAYS,
                        help=f"Trailing window per snapshot (default: {DEFAULT_WINDOW_DAYS})")
    args = parser.parse_args()

    print("[1/2] Loading panel decks")
    try:
        decks = load_panel_decks()
    except SchemaError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print("[2/2] Computing monthly snapshots")
    rows = compute_snapshots(decks, args.window_days)
    if not rows:
        print("ERROR: no snapshots computed (empty panel?)", file=sys.stderr)
        sys.exit(1)

    DATA_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    n_snaps = len({r["snapshot_date"] for r in rows})
    print(f"  Saved {len(rows):,} rows across {n_snaps} snapshots → {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
