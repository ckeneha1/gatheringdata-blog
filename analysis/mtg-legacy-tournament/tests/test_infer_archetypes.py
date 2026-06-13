"""Tests for infer_archetypes.py — inferred archetype clustering.

Builds a synthetic panel of ~200 decks from 4 archetype templates plus noise,
writes it in the deck_*.json / events_*.json schema, and asserts the pipeline
recovers the templates (decks from one template cluster together) and that the
--validate path runs.
"""

import csv
import json
import sys
from pathlib import Path

_TOURNAMENT_DIR = Path(__file__).resolve().parent.parent
if str(_TOURNAMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_TOURNAMENT_DIR))

import pytest  # noqa: E402

import infer_archetypes as ia  # noqa: E402


# Four templates with disjoint core cards + a couple of shared staples (which
# the max-df filter should drop) + per-deck filler noise.
TEMPLATES = {
    "alpha":  [f"Alpha{i}" for i in range(8)],
    "bravo":  [f"Bravo{i}" for i in range(8)],
    "charlie": [f"Charlie{i}" for i in range(8)],
    "delta":  [f"Delta{i}" for i in range(8)],
}
STAPLES = ["Brainstorm", "Force of Will"]   # in nearly every deck → filtered by max-df


def _make_panel(tmp_path, decks_per_template=45, noise_decks=20, seed=1):
    import random
    rng = random.Random(seed)
    raw = tmp_path / "raw"
    raw.mkdir(parents=True)

    deck_id = 0
    event_decks = []
    truth = {}  # deck_id → template name

    for tname, core in TEMPLATES.items():
        for _ in range(decks_per_template):
            deck_id += 1
            # core + staples + 2 unique-ish filler cards
            filler = [f"Filler{rng.randint(0, 40)}" for _ in range(2)]
            cards = core + STAPLES + filler
            mainboard = [{"card_name": c, "quantity": 1} for c in cards]
            (raw / f"deck_{deck_id}.json").write_text(json.dumps(
                {"deck_id": deck_id, "mainboard": mainboard, "sideboard": []}))
            placement = rng.choice([1, 2, 6, 8, 10])
            event_decks.append({"deck_id": deck_id, "placement": placement,
                                "archetype_name": tname.title()})
            truth[deck_id] = tname

    # Noise decks: random filler only, no coherent core.
    for _ in range(noise_decks):
        deck_id += 1
        cards = [f"Filler{rng.randint(0, 40)}" for _ in range(6)] + STAPLES
        mainboard = [{"card_name": c, "quantity": 1} for c in cards]
        (raw / f"deck_{deck_id}.json").write_text(json.dumps(
            {"deck_id": deck_id, "mainboard": mainboard, "sideboard": []}))
        event_decks.append({"deck_id": deck_id, "placement": rng.choice([10, 16]),
                            "archetype_name": "Rogue"})
        truth[deck_id] = "noise"

    # One event holding all decks, with a parseable DD/MM/YY date.
    events = [{"event_id": 1, "event_name": "Synthetic Open", "date_str": "01/06/24",
               "player_count": deck_id, "star_count": 4, "decks": event_decks}]
    (raw / "events_2024.json").write_text(json.dumps(events))
    return tmp_path, truth


# ── unit-level ────────────────────────────────────────────────────────────────

def test_jaccard():
    a = frozenset({"x", "y", "z"})
    b = frozenset({"x", "y", "w"})
    assert ia._jaccard(a, b) == pytest.approx(2 / 4)
    assert ia._jaccard(frozenset(), a) == 0.0
    assert ia._jaccard(a, a) == 1.0


def test_build_reps_filters_staples_and_rare(tmp_path):
    data_dir, _ = _make_panel(tmp_path)
    decks = ia.load_decks(data_dir / "raw")
    reps, df = ia.build_reps(decks, min_df=3, max_df_frac=0.40)
    # Staples appear in >40% of decks → dropped from the similarity vocab.
    sample_rep = next(iter(reps.values()))
    all_rep_cards = set().union(*reps.values())
    assert "Brainstorm" not in all_rep_cards
    assert "Force of Will" not in all_rep_cards
    # Template core cards survive (each in 45 decks).
    assert "Alpha0" in all_rep_cards


def test_load_decks_missing_dir_exits(tmp_path):
    with pytest.raises(SystemExit):
        ia.load_decks(tmp_path / "does_not_exist")


# ── integration: full pipeline recovers templates ────────────────────────────

def _run_pipeline(data_dir, validate=False):
    argv = [
        "--data-dir", str(data_dir),
        "--sample", "500",
        "--threshold", "0.30",
        "--assign-threshold", "0.25",
        "--merge-threshold", "0.50",
        "--min-df", "3",
        "--max-df", "0.40",
        "--min-cluster-size", "5",
        "--min-with", "5",
        "--min-without", "5",
        "--seed", "7",
    ]
    if validate:
        argv.append("--validate")
    ia.main(argv)


def test_pipeline_recovers_four_templates(tmp_path):
    data_dir, truth = _make_panel(tmp_path)
    _run_pipeline(data_dir)

    clusters_csv = data_dir / "deck_clusters.csv"
    assert clusters_csv.exists()
    rows = list(csv.DictReader(clusters_csv.open()))
    assigned = {int(r["deck_id"]): r["cluster_id"] for r in rows}

    # For each template, the modal cluster of its decks should be a single
    # non-Other cluster covering the large majority of that template's decks.
    from collections import Counter
    for tname in TEMPLATES:
        ids = [did for did, t in truth.items() if t == tname]
        clusters_for = Counter(assigned[did] for did in ids)
        top_cluster, top_n = clusters_for.most_common(1)[0]
        assert top_cluster != "Other", f"{tname} decks landed mostly in Other"
        assert top_n / len(ids) >= 0.8, f"{tname} not cohesively clustered: {clusters_for}"

    # Distinct templates should map to distinct dominant clusters.
    dominant = {}
    for tname in TEMPLATES:
        ids = [did for did, t in truth.items() if t == tname]
        dominant[tname] = Counter(assigned[did] for did in ids).most_common(1)[0][0]
    assert len(set(dominant.values())) == 4, f"templates collapsed: {dominant}"


def test_noise_decks_mostly_other(tmp_path):
    data_dir, truth = _make_panel(tmp_path)
    _run_pipeline(data_dir)
    rows = list(csv.DictReader((data_dir / "deck_clusters.csv").open()))
    assigned = {int(r["deck_id"]): r["cluster_id"] for r in rows}
    noise_ids = [did for did, t in truth.items() if t == "noise"]
    other_frac = sum(1 for did in noise_ids if assigned[did] == "Other") / len(noise_ids)
    assert other_frac >= 0.5, f"noise decks unexpectedly clustered: {other_frac:.0%} Other"


def test_validate_mode_runs(tmp_path):
    data_dir, _ = _make_panel(tmp_path)
    _run_pipeline(data_dir, validate=True)
    # Validation cross-tab is written (recovery numbers vs. real anchor rules are
    # meaningless for synthetic cards; we only assert the path executes + emits).
    assert (data_dir / "cluster_validation.csv").exists()
    assert (data_dir / "cluster_summary.csv").exists()
    assert (data_dir / "cluster_card_stats.csv").exists()
