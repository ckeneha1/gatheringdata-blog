"""Tests for build_field_snapshots.py — trailing-window archetype shares.

Pure-function coverage of compute_snapshots / month_starts, plus a guard on the
no-leakage property (a snapshot dated D only summarizes decks strictly before D)
and producer/consumer schema consistency with build_exclusions.FieldSnapshots.
"""

import sys
from datetime import date
from pathlib import Path

_PRIMERS_DIR = Path(__file__).resolve().parent.parent
_ANALYSIS_DIR = _PRIMERS_DIR.parent
for p in (str(_PRIMERS_DIR), str(_ANALYSIS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import build_field_snapshots as bfs  # noqa: E402
import build_exclusions as bx  # noqa: E402


def test_month_starts_spans_panel():
    starts = bfs.month_starts(date(2024, 1, 15), date(2024, 4, 10))
    assert date(2024, 2, 1) in starts
    assert date(2024, 4, 1) in starts
    assert all(d.day == 1 for d in starts)


def test_compute_snapshots_shares_sum_to_one():
    decks = (
        [(date(2024, 1, 10), "Delver")] * 6
        + [(date(2024, 1, 20), "Lands")] * 4
    )
    rows = bfs.compute_snapshots(decks, window_days=90)
    # The 2024-02-01 snapshot covers Jan → both archetypes present.
    feb = [r for r in rows if r["snapshot_date"] == "2024-02-01"]
    assert feb, "expected a 2024-02-01 snapshot"
    assert sum(r["share"] for r in feb) == 1.0
    shares = {r["archetype"]: r["share"] for r in feb}
    assert shares["Delver"] == 0.6
    assert shares["Lands"] == 0.4


def test_compute_snapshots_no_leakage():
    # A deck dated exactly on a snapshot date must NOT be counted in it
    # (window is [window_start, snap) — strictly before).
    decks = [(date(2024, 3, 1), "Delver"), (date(2024, 2, 15), "Lands")]
    rows = bfs.compute_snapshots(decks, window_days=90)
    mar = [r for r in rows if r["snapshot_date"] == "2024-03-01"]
    archs = {r["archetype"] for r in mar}
    assert "Lands" in archs       # Feb 15 is before Mar 1
    assert "Delver" not in archs  # Mar 1 deck excluded from the Mar 1 snapshot


def test_empty_panel_returns_no_rows():
    assert bfs.compute_snapshots([], window_days=90) == []


def test_output_schema_matches_fieldsnapshots_consumer(tmp_path):
    # Producer columns must include what build_exclusions.FieldSnapshots requires.
    decks = [(date(2024, 1, 10), "Delver")] * 5
    rows = bfs.compute_snapshots(decks, window_days=90)
    produced_cols = set(rows[0].keys())
    required_by_consumer = {"snapshot_date", "archetype", "share"}
    assert required_by_consumer <= produced_cols

    # Round-trip through a CSV and load it with the consumer.
    import csv
    csv_path = tmp_path / "field_snapshots.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    snaps = bx.FieldSnapshots.from_csv(csv_path)
    assert snaps is not None
    hit = snaps.lookup("2024-12-31")
    assert hit is not None
    _, shares = hit
    assert "Delver" in shares
