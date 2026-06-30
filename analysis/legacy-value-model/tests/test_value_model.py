"""Tests for value_model.py — the conditional pairwise value model.

Fixture-only. Covers feature mapping, the field-conditionality property,
learning a separable preference, confidence weighting, verdict mapping
(framework threshold rule), cross-validation, and persistence.
"""

import sys
from pathlib import Path

_MODEL_DIR = Path(__file__).resolve().parent.parent
_ANALYSIS_DIR = _MODEL_DIR.parent
for p in (str(_MODEL_DIR), str(_ANALYSIS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest  # noqa: E402

import value_model as vm  # noqa: E402


def _vec(features, cmc):
    return vm.CardVec(frozenset(features), float(cmc))


# ── context parsing ───────────────────────────────────────────────────────────

def test_parse_field_top_and_concentration():
    shares = vm.parse_field_top("Delver:0.120|Lands:0.050|Sneak:0.069")
    assert shares["Delver"] == 0.120
    assert vm.field_concentration("Delver:0.120|Lands:0.050") == 0.120
    assert vm.field_concentration("") == 0.0


# ── feature map ────────────────────────────────────────────────────────────────

def test_pair_features_cmc_and_diff():
    fs = vm.FeatureSpace.from_ability_features({"cat:card_advantage", "cat:removal"})
    x = _vec({"cat:card_advantage"}, 1)
    y = _vec({"cat:card_advantage"}, 2)
    feats = vm.pair_features(x, y, ctx_scalar=0.0, fs=fs)
    # cmc_diff = y.cmc - x.cmc = 1 (X is cheaper → favours X)
    assert feats[fs.index["cmc_diff"]] == 1.0
    # both share card_advantage → diff 0; neither has removal → diff 0
    assert feats[fs.index["diff:cat:card_advantage"]] == 0.0
    assert feats[fs.index["diff:cat:removal"]] == 0.0


def test_pair_features_field_conditionality():
    # The ctx terms are the ONLY way field state enters; with ctx_scalar 0 they
    # vanish, with ctx_scalar>0 they scale the ability diff.
    fs = vm.FeatureSpace.from_ability_features({"cat:counterspell"})
    x = _vec({"cat:counterspell"}, 2)
    y = _vec(set(), 2)
    no_ctx = vm.pair_features(x, y, 0.0, fs)
    with_ctx = vm.pair_features(x, y, 0.3, fs)
    assert no_ctx[fs.index["ctx:cat:counterspell"]] == 0.0
    assert with_ctx[fs.index["ctx:cat:counterspell"]] == pytest.approx(0.3)
    # The intrinsic diff term is unaffected by context.
    assert with_ctx[fs.index["diff:cat:counterspell"]] == 1.0


# ── learning ───────────────────────────────────────────────────────────────────

def test_learns_cheaper_is_better():
    # Separable signal: the cheaper card is always preferred, same abilities.
    cheap = _vec({"cat:card_advantage"}, 1)
    pricey = _vec({"cat:card_advantage"}, 3)
    pairs = [vm.Pair(cheap, pricey, ctx_scalar=0.1, weight=1.0) for _ in range(40)]
    model = vm.train(pairs, epochs=300, seed=1)
    # Model should strongly prefer the cheaper card and respect ordering.
    assert model.prefer_prob(cheap, pricey, 0.1) > 0.8
    assert model.prefer_prob(pricey, cheap, 0.1) < 0.2
    assert vm.pairwise_accuracy(model, pairs) == 1.0


def test_learns_ability_advantage():
    # Same cost; the card WITH card_advantage is preferred.
    rich = _vec({"cat:card_advantage"}, 2)
    poor = _vec(set(), 2)
    pairs = [vm.Pair(rich, poor, ctx_scalar=0.1, weight=1.0) for _ in range(40)]
    model = vm.train(pairs, epochs=300, seed=2)
    assert model.prefer_prob(rich, poor, 0.1) > 0.8


def test_learns_field_conditional_preference():
    # Counterspells preferred ONLY in a concentrated (combo-ish) field.
    # High-concentration context: counterspell card ≻ vanilla.
    # Low-concentration context: vanilla ≻ counterspell card.
    cs = _vec({"cat:counterspell"}, 2)
    van = _vec(set(), 2)
    pairs = []
    for _ in range(40):
        pairs.append(vm.Pair(cs, van, ctx_scalar=0.30, weight=1.0))   # combo field: cs wins
        pairs.append(vm.Pair(van, cs, ctx_scalar=0.05, weight=1.0))   # creature field: cs loses
    model = vm.train(pairs, epochs=400, seed=3)
    # Same two cards, preference flips with the field — only possible via ctx terms.
    assert model.prefer_prob(cs, van, 0.30) > 0.6
    assert model.prefer_prob(cs, van, 0.05) < 0.4


def test_confidence_weight_influences_fit():
    # Two contradictory signals; the higher-confidence one should win out.
    a = _vec({"cat:removal"}, 2)
    b = _vec(set(), 2)
    pairs = (
        [vm.Pair(a, b, 0.1, weight=5.0) for _ in range(20)]   # strong: a ≻ b
        + [vm.Pair(b, a, 0.1, weight=0.2) for _ in range(20)]  # weak: b ≻ a
    )
    model = vm.train(pairs, epochs=300, seed=4)
    assert model.prefer_prob(a, b, 0.1) > 0.5


def test_train_empty_raises():
    with pytest.raises(ValueError):
        vm.train([])


# ── verdict mapping (framework threshold rule) ────────────────────────────────

def _trained_cheap_better():
    cheap = _vec({"cat:card_advantage"}, 1)
    pricey = _vec({"cat:card_advantage"}, 4)
    pairs = [vm.Pair(cheap, pricey, 0.1, 1.0) for _ in range(60)]
    return vm.train(pairs, epochs=400, seed=5)


def test_verdict_played_when_beats_weakest():
    model = _trained_cheap_better()
    candidate = _vec({"cat:card_advantage"}, 1)            # cheap → strong
    incumbents = [("Expensive Incumbent", _vec({"cat:card_advantage"}, 4))]
    res = vm.predict_verdict(model, candidate, incumbents, ctx_scalar=0.1)
    assert res.verdict == "PLAYED"
    assert res.weakest_incumbent == "Expensive Incumbent"
    assert res.beats_weakest_prob >= vm.PLAYED_MARGIN


def test_verdict_not_played_when_loses():
    model = _trained_cheap_better()
    candidate = _vec({"cat:card_advantage"}, 4)            # expensive → weak
    incumbents = [("Cheap Incumbent", _vec({"cat:card_advantage"}, 1))]
    res = vm.predict_verdict(model, candidate, incumbents, ctx_scalar=0.1)
    assert res.verdict == "NOT_PLAYED"


def test_verdict_no_incumbents_is_not_played():
    model = _trained_cheap_better()
    res = vm.predict_verdict(model, _vec({"cat:card_advantage"}, 1), [], 0.1)
    assert res.verdict == "NOT_PLAYED"
    assert res.n_incumbents == 0


def test_verdict_uses_weakest_incumbent():
    # Candidate beats the weak incumbent but not the strong one → still clears
    # the slot (framework rule: beat the lower bound of the played set).
    model = _trained_cheap_better()
    candidate = _vec({"cat:card_advantage"}, 2)
    incumbents = [
        ("Strong (cheap)", _vec({"cat:card_advantage"}, 1)),
        ("Weak (expensive)", _vec({"cat:card_advantage"}, 4)),
    ]
    res = vm.predict_verdict(model, candidate, incumbents, 0.1)
    assert res.weakest_incumbent == "Weak (expensive)"
    assert res.verdict in {"PLAYED", "FRINGE"}  # judged vs the weakest, not the strongest


# ── cross-validation + persistence ────────────────────────────────────────────

def test_cross_val_separable_high_accuracy():
    cheap = _vec({"cat:card_advantage"}, 1)
    pricey = _vec({"cat:card_advantage"}, 3)
    pairs = [vm.Pair(cheap, pricey, 0.1, 1.0) for _ in range(50)]
    # dedup=False: this fixture intentionally replicates one separable pair.
    acc = vm.cross_val_accuracy(pairs, folds=5, epochs=200, seed=6, dedup=False)
    assert acc > 0.9


def test_cross_val_dedup_collapses_duplicates():
    # Default dedup=True collapses replicated (x, y, ctx) constraints to one vote
    # each, so identical-pair leakage can't inflate the score. Four distinct
    # cheaper-is-better constraints, each replicated 10x → 4 after dedup.
    pairs = []
    for ab in ("cat:card_advantage", "cat:removal", "cat:counterspell", "cat:tempo"):
        cheap, pricey = _vec({ab}, 1), _vec({ab}, 3)
        pairs += [vm.Pair(cheap, pricey, 0.1, 1.0) for _ in range(10)]
    assert len(pairs) == 40
    acc = vm.cross_val_accuracy(pairs, folds=2, epochs=200, seed=7)  # dedup=True (default)
    assert acc > 0.9


def test_save_load_roundtrip(tmp_path):
    model = _trained_cheap_better()
    path = tmp_path / "model.json"
    model.save(path)
    loaded = vm.ValueModel.load(path)
    x = _vec({"cat:card_advantage"}, 1)
    y = _vec({"cat:card_advantage"}, 4)
    assert loaded.prefer_prob(x, y, 0.1) == pytest.approx(model.prefer_prob(x, y, 0.1))
    assert loaded.feature_space.names == model.feature_space.names
