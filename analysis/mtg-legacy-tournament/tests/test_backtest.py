"""Tests for backtest.py — prediction grading against a fixture panel.

Covers the pure mappers (verdict mapping, within-archetype log-OR, name
normalization, bracket rank), prediction-file loading/validation, and an
end-to-end grade over a synthetic in-memory panel.
"""

import csv
import sys
from datetime import date
from pathlib import Path

_TOURNAMENT_DIR = Path(__file__).resolve().parent.parent
if str(_TOURNAMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_TOURNAMENT_DIR))

import pytest  # noqa: E402

import backtest as bt  # noqa: E402


# ── pure mappers ──────────────────────────────────────────────────────────────

def test_bracket_rank():
    assert bt.bracket_rank(1) == 1
    assert bt.bracket_rank(2) == 2
    assert bt.bracket_rank(6) == 3
    assert bt.bracket_rank(8) == 4
    assert bt.bracket_rank(16) == 8
    assert bt.bracket_rank(3) is None     # odd, not a real bracket value
    assert bt.bracket_rank(0) is None


def test_normalize_name():
    assert bt.normalize_name("Force of Will") == "force of will"
    assert bt.normalize_name("Fire // Ice") == "fire"          # front face
    assert bt.normalize_name("Lim-Dûl's Vault") == "limdls vault"  # punct stripped


def test_within_log_or_symmetry_and_sign():
    # Card present in winners more than absent → positive log-OR.
    pos = bt.within_log_or(with_total=100, with_wins=30, without_total=100, without_wins=10)
    assert pos > 0
    # Reverse → negative.
    neg = bt.within_log_or(with_total=100, with_wins=10, without_total=100, without_wins=30)
    assert neg < 0
    # Equal rates → ~0.
    flat = bt.within_log_or(with_total=100, with_wins=20, without_total=100, without_wins=20)
    assert abs(flat) < 1e-9


def test_map_verdict_not_played_floor():
    # ≤ NOT_PLAYED_MAX_LISTS appearances format-wide → NOT_PLAYED regardless.
    assert bt.map_verdict(n_all_with=2, n_all=1000, n_arch_with=2, n_arch=4) == "NOT_PLAYED"
    assert bt.map_verdict(n_all_with=0, n_all=1000, n_arch_with=None, n_arch=None) == "NOT_PLAYED"


def test_map_verdict_played_by_archetype_share():
    # 30/100 = 30% of the named archetype ≥ 25% → PLAYED.
    assert bt.map_verdict(n_all_with=30, n_all=5000, n_arch_with=30, n_arch=100) == "PLAYED"
    # 10/100 = 10% < 25%, and an archetype claim doesn't fall back to field → FRINGE.
    assert bt.map_verdict(n_all_with=10, n_all=50, n_arch_with=10, n_arch=100) == "FRINGE"


def test_map_verdict_played_by_field_share():
    # Format-wide claim (n_arch None): 200/5000 = 4% ≥ 2% → PLAYED.
    assert bt.map_verdict(n_all_with=200, n_all=5000, n_arch_with=None, n_arch=None) == "PLAYED"
    # 50/5000 = 1% < 2% but > NOT_PLAYED floor → FRINGE.
    assert bt.map_verdict(n_all_with=50, n_all=5000, n_arch_with=None, n_arch=None) == "FRINGE"


# ── prediction loading ────────────────────────────────────────────────────────

def _write_pred_csv(path, rows, header=None):
    header = header or list(bt.PREDICTION_COLUMNS) + ["window_end"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


def test_load_predictions_csv(tmp_path):
    p = tmp_path / "preds.csv"
    _write_pred_csv(p, [
        {"card_name": "Mole Man, Moloid Master", "predicted_verdict": "PLAYED",
         "archetype": "Lands", "as_of_date": "2026-06-19", "window_end": "2026-08-15"},
        {"card_name": "Hawkeye's Bow", "predicted_verdict": "NOT PLAYED",
         "archetype": "", "as_of_date": "2026-06-19", "window_end": ""},
    ])
    preds = bt.load_predictions(p, window_days=57)
    assert preds[0]["predicted_verdict"] == "PLAYED"
    # "NOT PLAYED" normalizes to NOT_PLAYED; blank window_end → as_of + window_days.
    assert preds[1]["predicted_verdict"] == "NOT_PLAYED"
    assert preds[1]["window_end"] == date(2026, 6, 19) + (date(2026, 8, 15) - date(2026, 6, 19))


def test_load_predictions_bad_verdict(tmp_path):
    p = tmp_path / "bad.csv"
    _write_pred_csv(p, [
        {"card_name": "X", "predicted_verdict": "MAYBE",
         "archetype": "", "as_of_date": "2026-06-19", "window_end": ""},
    ])
    with pytest.raises(SystemExit):
        bt.load_predictions(p, window_days=57)


def test_load_predictions_missing_column(tmp_path):
    p = tmp_path / "missing.csv"
    _write_pred_csv(p, [{"card_name": "X", "predicted_verdict": "PLAYED",
                         "as_of_date": "2026-06-19"}],
                    header=["card_name", "predicted_verdict", "as_of_date"])
    with pytest.raises(SystemExit):
        bt.load_predictions(p, window_days=57)


# ── end-to-end grading over an in-memory panel ────────────────────────────────

def _panel():
    """200 decks in-window. 'Staple Card' is in 60 (30%) of the 'Lands' decks;
    'Dead Card' appears once. Cluster labels supplied so the matcher uses them."""
    panel = {}
    clusters = {}
    d = date(2026, 7, 1)
    did = 0
    # 100 Lands decks; 60 run Staple Card, and Staple Card wins often.
    for k in range(100):
        did += 1
        has_staple = k < 60
        cards = {"Mox Diamond", "Wasteland"}
        if has_staple:
            cards.add("Staple Card")
        # winners: first 20 staple decks placed 1st; others mid.
        placement = 1 if (has_staple and k < 20) else 10
        panel[did] = {"cards": frozenset(cards), "date": d,
                      "placement": placement, "mtgtop8_archetype": "Lands"}
        clusters[did] = ("C01", "Lands")
    # 100 non-Lands decks, none run Staple Card.
    for k in range(100):
        did += 1
        panel[did] = {"cards": frozenset({"Brainstorm", "Ponder"}), "date": d,
                      "placement": 1 if k < 10 else 16, "mtgtop8_archetype": "Delver"}
        clusters[did] = ("C02", "Delver")
    # one dead card appearance
    panel[1]["cards"] = panel[1]["cards"] | {"Dead Card"}
    return panel, clusters


def test_grade_played_in_archetype():
    panel, clusters = _panel()
    preds = [{
        "card_name": "Staple Card", "predicted_verdict": "PLAYED", "archetype": "Lands",
        "as_of_date": date(2026, 6, 1), "window_end": date(2026, 8, 1),
    }]
    rows = bt.grade_predictions(preds, panel, clusters, min_with=5, min_without=5)
    row = rows[0]
    # 60/100 Lands decks = 60% ≥ 25% → actual PLAYED, prediction correct.
    assert row["actual_verdict"] == "PLAYED"
    assert row["correct"] == 1
    assert row["share_archetype"] == pytest.approx(0.60)
    assert row["archetype_source"] == "clusters"
    # log-OR computed (enough decks with/without) and positive (staple wins more).
    assert row["within_log_or"] != ""
    assert float(row["within_log_or"]) > 0


def test_grade_not_played_dead_card():
    panel, clusters = _panel()
    preds = [{
        "card_name": "Dead Card", "predicted_verdict": "NOT_PLAYED", "archetype": "",
        "as_of_date": date(2026, 6, 1), "window_end": date(2026, 8, 1),
    }]
    rows = bt.grade_predictions(preds, panel, clusters, min_with=5, min_without=5)
    assert rows[0]["actual_verdict"] == "NOT_PLAYED"  # appears once ≤ floor
    assert rows[0]["correct"] == 1


def test_grade_window_excludes_out_of_range_decks():
    panel, clusters = _panel()
    # Window entirely before the panel's decks (2026-07-01) → nothing in window.
    preds = [{
        "card_name": "Staple Card", "predicted_verdict": "PLAYED", "archetype": "Lands",
        "as_of_date": date(2026, 1, 1), "window_end": date(2026, 2, 1),
    }]
    rows = bt.grade_predictions(preds, panel, clusters, min_with=5, min_without=5)
    assert rows[0]["n_decks_window"] == 0
    assert rows[0]["actual_verdict"] == "NOT_PLAYED"
