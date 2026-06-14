"""
value_model.py — the conditional value model (Phase 1.4).

Learns, from primer inclusion/exclusion data, a CONDITIONAL preference
function over Magic cards: given a card's ability-at-cost features and the
field state at a point in time, does it clear the threshold to occupy a slot
in a given Legacy archetype?

Design (brief §2.4): the exclusion dataset is already pairwise. Each row of
`exclusions.csv` is a preference observation —

    comparison_card (X, PLAYED in the primer)  ≻  excluded_card (Y, silently
    omitted though it was a function-neighbour in-pool)

in a context (archetype, pool date, field composition), with a
specification-quality `confidence_weight`. So the model is a PAIRWISE RANKER:
learn a scorer s(card | context) with

    P(X ≻ Y | context) = σ( w · [ φ(X) − φ(Y) ] )

where φ is the feature map. Ability features are intrinsic (Post 2 vector +
CMC); the model is made CONDITIONAL on the field by adding interaction
features between each ability feature and a context scalar (so a preference
can flip with the metagame — e.g. counterspells clear the bar in a
combo-heavy field but not a creature-heavy one). A plain feature difference
without interactions is field-blind (the shared context cancels in X−Y); the
interactions are what let context matter. See `pair_features`.

The learned weights are directly inspectable: each coefficient is "how much
this ability feature (optionally × field context) shifts the odds of clearing
a slot threshold." That is the whole point — thresholds become a learned
decision boundary in ability-at-cost space rather than expert feel.

Verdict mapping for a NEW candidate in archetype A reproduces the framework's
own threshold rule ("clear the lower bound of the cards currently in the
slot"): score the candidate against each in-archetype incumbent that shares
its function; if it beats even the weakest with margin → PLAYED, if it beats
none → NOT_PLAYED, in between → FRINGE.

This module's CORE (feature mapping, training, scoring, verdict mapping) is
pure-stdlib and unit-tested with fixtures. The CLI paths that read the real
`exclusions.csv` / Scryfall catalog / cluster files are thin wrappers; those
inputs are gitignored and live on the owner's machine (brief §5).

Usage:
    uv run python value_model.py train       # fit on exclusions.csv → model.json
    uv run python value_model.py eval         # held-out pairwise accuracy
    uv run python value_model.py predict --candidates <file>   # → verdicts.csv
"""

import argparse
import csv
import json
import math
import random
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path

_ANALYSIS_DIR = Path(__file__).resolve().parent.parent
if str(_ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_DIR))

from shared.ability_features import card_feature_set  # noqa: E402

# ── paths (real-data inputs are gitignored; see brief §5) ────────────────────
DATA_DIR = Path(__file__).parent / "data"
MODEL_JSON = DATA_DIR / "model.json"
VERDICTS_CSV = DATA_DIR / "verdicts.csv"
# Upstream artifacts produced by the other Phase 1 modules:
EXCLUSIONS_CSV = _ANALYSIS_DIR / "mtg-primers" / "data" / "exclusions.csv"

# Verdict thresholds on the candidate-vs-weakest-incumbent preference prob.
PLAYED_MARGIN = 0.60      # beats the weakest incumbent with margin → clears slot
NOT_PLAYED_MARGIN = 0.40  # loses to even the weakest incumbent → below threshold

CONTEXT_SCALAR = "field_concentration"  # the single v0 context feature (see below)


# ---------------------------------------------------------------------------
# Card representation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CardVec:
    """A card's intrinsic representation: ability feature set + CMC."""
    features: frozenset[str]
    cmc: float


def make_card_vec(oracle_text: str, keywords: list[str], cmc: float,
                  is_land: bool = False) -> CardVec:
    return CardVec(card_feature_set(oracle_text, keywords, is_land), float(cmc))


# ---------------------------------------------------------------------------
# Context features
# ---------------------------------------------------------------------------

def parse_field_top(field_top: str) -> dict[str, float]:
    """Parse exclusions.csv `field_top_archetypes` ("Arch:0.120|Other:0.080")."""
    out: dict[str, float] = {}
    for part in (field_top or "").split("|"):
        if ":" in part:
            name, _, share = part.rpartition(":")
            try:
                out[name] = float(share)
            except ValueError:
                continue
    return out


def field_concentration(field_top: str) -> float:
    """v0 context scalar: the top archetype's share — a proxy for how
    concentrated/optimized the field is (higher → a sharper threshold, since
    a few decks dominate). Returns 0.0 when no field snapshot was available.

    This is deliberately ONE scalar to keep the scaffold inspectable; richer
    context (per-axis pressure: tempo/combo/creature share) is the documented
    extension point — add scalars here and they flow into `pair_features`.
    """
    shares = parse_field_top(field_top)
    return max(shares.values()) if shares else 0.0


# ---------------------------------------------------------------------------
# Pairwise feature map
# ---------------------------------------------------------------------------

class FeatureSpace:
    """Stable mapping feature-name → column index, learned from training rows
    and persisted with the model so prediction uses the same columns."""

    def __init__(self, names: list[str]):
        self.names = names
        self.index = {n: i for i, n in enumerate(names)}

    @classmethod
    def from_ability_features(cls, ability_feats: set[str]) -> "FeatureSpace":
        base = sorted(ability_feats)
        names = ["cmc_diff"]
        names += [f"diff:{f}" for f in base]
        names += [f"ctx:{f}" for f in base]  # ability × field_concentration
        return cls(names)

    def __len__(self) -> int:
        return len(self.names)


def pair_features(x: CardVec, y: CardVec, ctx_scalar: float,
                  fs: FeatureSpace) -> list[float]:
    """Feature vector for the ordered pair (X preferred over Y) in context.

    Dimensions:
      - cmc_diff:    y.cmc − x.cmc  (cheaper X → positive → favours X; one mana
                     is format-defining, framework §5)
      - diff:<f>:    1{f in X} − 1{f in Y}   (intrinsic ability advantage)
      - ctx:<f>:     diff:<f> × ctx_scalar   (field-conditional ability value)
    The intrinsic-only model is field-blind because the shared context cancels
    in X−Y; the ctx terms restore conditionality.
    """
    vec = [0.0] * len(fs)
    vec[fs.index["cmc_diff"]] = y.cmc - x.cmc
    for f in fs.names:
        if f.startswith("diff:"):
            ability = f[len("diff:"):]
            d = (1.0 if ability in x.features else 0.0) - (1.0 if ability in y.features else 0.0)
            vec[fs.index[f]] = d
            ctx_key = f"ctx:{ability}"
            if ctx_key in fs.index:
                vec[fs.index[ctx_key]] = d * ctx_scalar
    return vec


# ---------------------------------------------------------------------------
# Training data
# ---------------------------------------------------------------------------

@dataclass
class Pair:
    x: CardVec          # preferred (played) card
    y: CardVec          # not-preferred (excluded) card
    ctx_scalar: float
    weight: float
    archetype: str = ""


def collect_ability_features(pairs: list[Pair]) -> set[str]:
    feats: set[str] = set()
    for p in pairs:
        feats |= p.x.features
        feats |= p.y.features
    return feats


# ---------------------------------------------------------------------------
# Logistic-regression pairwise ranker (pure-stdlib SGD)
# ---------------------------------------------------------------------------

def _sigmoid(z: float) -> float:
    if z < -30:
        return 0.0
    if z > 30:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


@dataclass
class ValueModel:
    feature_space: FeatureSpace
    weights: list[float]
    bias: float = 0.0

    def score_pair(self, feats: list[float]) -> float:
        z = self.bias + sum(w * f for w, f in zip(self.weights, feats))
        return _sigmoid(z)

    def prefer_prob(self, x: CardVec, y: CardVec, ctx_scalar: float) -> float:
        """P(x ≻ y | context)."""
        return self.score_pair(pair_features(x, y, ctx_scalar, self.feature_space))

    # ── persistence ──────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {"feature_names": self.feature_space.names,
                "weights": self.weights, "bias": self.bias}

    @classmethod
    def from_dict(cls, d: dict) -> "ValueModel":
        fs = FeatureSpace(d["feature_names"])
        return cls(fs, list(d["weights"]), float(d.get("bias", 0.0)))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path) -> "ValueModel":
        return cls.from_dict(json.loads(path.read_text()))


def train(pairs: list[Pair], *, epochs: int = 200, lr: float = 0.1,
          l2: float = 1e-3, seed: int = 0,
          feature_space: FeatureSpace | None = None) -> ValueModel:
    """Confidence-weighted logistic regression on pairwise preferences.

    Each pair contributes BOTH orderings: (X≻Y, label 1) and (Y≻X, label 0),
    so the bias can't shortcut and the scorer is order-consistent.
    """
    if not pairs:
        raise ValueError("no training pairs")
    fs = feature_space or FeatureSpace.from_ability_features(collect_ability_features(pairs))
    w = [0.0] * len(fs)
    bias = 0.0
    rng = random.Random(seed)

    # Pre-compute both-direction examples once.
    examples: list[tuple[list[float], float, float]] = []  # (feats, label, weight)
    for p in pairs:
        fwd = pair_features(p.x, p.y, p.ctx_scalar, fs)
        rev = pair_features(p.y, p.x, p.ctx_scalar, fs)
        examples.append((fwd, 1.0, p.weight))
        examples.append((rev, 0.0, p.weight))

    for _ in range(epochs):
        rng.shuffle(examples)
        for feats, label, weight in examples:
            z = bias + sum(wi * fi for wi, fi in zip(w, feats))
            pred = _sigmoid(z)
            g = weight * (pred - label)
            for i, fi in enumerate(feats):
                w[i] -= lr * (g * fi + l2 * w[i])
            bias -= lr * g
    return ValueModel(fs, w, bias)


def pairwise_accuracy(model: ValueModel, pairs: list[Pair]) -> float:
    """Fraction of pairs where the preferred card outscores the excluded one."""
    if not pairs:
        return 0.0
    correct = sum(1 for p in pairs
                  if model.prefer_prob(p.x, p.y, p.ctx_scalar) > 0.5)
    return correct / len(pairs)


def cross_val_accuracy(pairs: list[Pair], *, folds: int = 5, seed: int = 0,
                       **train_kwargs) -> float:
    """Held-out pairwise accuracy, k-fold. Splits by INDEX (not value): pairs
    are frequently identical (cards sharing a feature profile), so an
    equality-based split would wrongly collapse the train set."""
    if len(pairs) < folds:
        folds = max(2, len(pairs))
    rng = random.Random(seed)
    order = list(range(len(pairs)))
    rng.shuffle(order)
    fold_size = max(1, len(order) // folds)
    # Fix the feature space across folds so columns are comparable.
    fs = FeatureSpace.from_ability_features(collect_ability_features(pairs))
    accs = []
    for k in range(folds):
        test_idx = set(order[k * fold_size:(k + 1) * fold_size])
        if not test_idx:
            continue
        test = [pairs[i] for i in test_idx]
        train_set = [pairs[i] for i in range(len(pairs)) if i not in test_idx]
        if not train_set:
            continue
        m = train(train_set, feature_space=fs, seed=seed, **train_kwargs)
        accs.append(pairwise_accuracy(m, test))
    return sum(accs) / len(accs) if accs else 0.0


# ---------------------------------------------------------------------------
# Verdict mapping (framework threshold rule)
# ---------------------------------------------------------------------------

@dataclass
class VerdictResult:
    verdict: str                     # PLAYED | FRINGE | NOT_PLAYED
    beats_weakest_prob: float        # P(candidate ≻ weakest incumbent)
    weakest_incumbent: str
    n_incumbents: int
    detail: list[tuple[str, float]] = dc_field(default_factory=list)


def predict_verdict(model: ValueModel, candidate: CardVec,
                    incumbents: list[tuple[str, CardVec]],
                    ctx_scalar: float) -> VerdictResult:
    """Map the candidate to a verdict in one archetype, per the framework's
    threshold rule: it clears the slot iff it beats the WEAKEST incumbent that
    currently occupies the function (the lower bound of the played set).

    `incumbents` = the in-archetype, in-function cards the candidate would
    compete with (named, so the verdict is explainable). Empty → no slot in
    this archetype → NOT_PLAYED.
    """
    if not incumbents:
        return VerdictResult("NOT_PLAYED", 0.0, "", 0)
    probs = [(name, model.prefer_prob(candidate, inc, ctx_scalar))
             for name, inc in incumbents]
    # Weakest incumbent = the one the candidate most easily beats (highest prob).
    weakest_name, weakest_prob = max(probs, key=lambda t: t[1])
    if weakest_prob >= PLAYED_MARGIN:
        verdict = "PLAYED"
    elif weakest_prob <= NOT_PLAYED_MARGIN:
        verdict = "NOT_PLAYED"
    else:
        verdict = "FRINGE"
    return VerdictResult(verdict, round(weakest_prob, 4), weakest_name,
                         len(incumbents), [(n, round(p, 4)) for n, p in probs])


# ---------------------------------------------------------------------------
# CLI plumbing (real-data wrappers — thin, untested against live files here)
# ---------------------------------------------------------------------------

def _require_catalog():
    """Build a name→CardVec catalog from the shared Scryfall cache via the
    mtg-primers FunctionIndex. Imported lazily so the core stays dependency-free."""
    primers_dir = _ANALYSIS_DIR / "mtg-primers"
    if str(primers_dir) not in sys.path:
        sys.path.insert(0, str(primers_dir))
    from function_index import FunctionIndex, find_oracle_cards_file  # noqa: E402
    index = FunctionIndex.from_scryfall_file(find_oracle_cards_file())
    return {c.name: CardVec(c.features, c.cmc) for c in index.cards}, index


def load_pairs_from_exclusions(path: Path, catalog: dict[str, CardVec]) -> list[Pair]:
    """Read exclusions.csv → pairwise preferences, vectorizing both cards via
    the catalog. Rows whose cards aren't in the catalog are skipped (warned)."""
    if not path.exists():
        raise SystemExit(
            f"ERROR: exclusions not found: {path}\n"
            "Produce it with: cd analysis/mtg-primers && uv run python build_exclusions.py build"
        )
    pairs: list[Pair] = []
    skipped = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"comparison_card", "excluded_card", "field_top_archetypes",
                    "confidence_weight", "archetype"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"ERROR: {path} missing columns: {sorted(missing)} "
                             "(expected build_exclusions.py SILENT_COLUMNS)")
        for row in reader:
            x = catalog.get(row["comparison_card"])
            y = catalog.get(row["excluded_card"])
            if x is None or y is None:
                skipped += 1
                continue
            try:
                weight = float(row["confidence_weight"])
            except (TypeError, ValueError):
                weight = 1.0
            pairs.append(Pair(x, y, field_concentration(row["field_top_archetypes"]),
                              weight, row.get("archetype", "")))
    if skipped:
        print(f"  NOTE: skipped {skipped} rows with cards absent from the catalog")
    if not pairs:
        raise SystemExit(f"ERROR: no usable pairs in {path}")
    return pairs


def cmd_train(args) -> None:
    catalog, _ = _require_catalog()
    pairs = load_pairs_from_exclusions(EXCLUSIONS_CSV, catalog)
    print(f"[train] {len(pairs):,} preference pairs")
    model = train(pairs, epochs=args.epochs, lr=args.lr, l2=args.l2, seed=args.seed)
    model.save(MODEL_JSON)
    print(f"[train] in-sample pairwise accuracy: {pairwise_accuracy(model, pairs):.3f}")
    print(f"[train] saved → {MODEL_JSON}")


def cmd_eval(args) -> None:
    catalog, _ = _require_catalog()
    pairs = load_pairs_from_exclusions(EXCLUSIONS_CSV, catalog)
    acc = cross_val_accuracy(pairs, folds=args.folds, epochs=args.epochs,
                             lr=args.lr, l2=args.l2, seed=args.seed)
    print(f"[eval] {args.folds}-fold held-out pairwise accuracy: {acc:.3f}")
    print("  (0.5 = no signal; the exclusion labels carry no learnable threshold)")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("train", "eval"):
        sp = sub.add_parser(name)
        sp.add_argument("--epochs", type=int, default=200)
        sp.add_argument("--lr", type=float, default=0.1)
        sp.add_argument("--l2", type=float, default=1e-3)
        sp.add_argument("--seed", type=int, default=0)
        if name == "eval":
            sp.add_argument("--folds", type=int, default=5)
    p_pred = sub.add_parser("predict")
    p_pred.add_argument("--candidates", type=Path, required=True,
                        help="JSON: [{name, oracle_text, keywords, cmc, archetype, "
                             "incumbents:[{name,oracle_text,keywords,cmc}], field_top}]")
    args = parser.parse_args(argv)

    if args.cmd == "train":
        cmd_train(args)
    elif args.cmd == "eval":
        cmd_eval(args)
    elif args.cmd == "predict":
        cmd_predict(args)


def cmd_predict(args) -> None:
    model = ValueModel.load(MODEL_JSON)
    cands = json.loads(args.candidates.read_text())
    rows = []
    for c in cands:
        cand = make_card_vec(c.get("oracle_text", ""), c.get("keywords", []), c.get("cmc", 0))
        incs = [(i["name"], make_card_vec(i.get("oracle_text", ""), i.get("keywords", []), i.get("cmc", 0)))
                for i in c.get("incumbents", [])]
        res = predict_verdict(model, cand, incs, field_concentration(c.get("field_top", "")))
        rows.append({"card_name": c["name"], "archetype": c.get("archetype", ""),
                     "verdict": res.verdict, "beats_weakest_prob": res.beats_weakest_prob,
                     "weakest_incumbent": res.weakest_incumbent,
                     "n_incumbents": res.n_incumbents})
    VERDICTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(VERDICTS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[predict] {len(rows)} candidates → {VERDICTS_CSV}")


if __name__ == "__main__":
    main()
