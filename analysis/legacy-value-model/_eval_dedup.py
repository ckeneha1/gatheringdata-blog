"""Leakage-free held-out eval for the conditional value model.

`value_model.py eval` does k-fold by INDEX, but exclusions.csv is ~88% duplicate
at the (x, y, ctx) feature-signature level (145,626 pairs -> 17,991 unique; a few
preferences recur up to 19x because many primers omit the same card near the same
played card). Index splitting lets identical examples straddle train/test AND lets
high-multiplicity duplicates dominate the metric. This script dedups to distinct
preference constraints first, then does a single 80/20 split (no duplicate can
straddle) — the honest "does it learn anything" estimate.

  uv run python _eval_dedup.py [--epochs N]

Result (epochs=30): held-out 0.798 vs in-sample 0.801 — no overfit gap, a real
generalizing signal well above the 0.5 no-signal baseline. (200 epochs >= this;
the unvectorized trainer is slow at 865 features, so 30 is the quick default.)
The eventual fix belongs in value_model.cross_val_accuracy: dedup + group-aware
folds. See legacy-framework/open_questions.md.
"""
import argparse
import random

from value_model import (_require_catalog, load_pairs_from_exclusions, train,
                         pairwise_accuracy, FeatureSpace, collect_ability_features,
                         EXCLUSIONS_CSV)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    catalog, _ = _require_catalog()
    pairs = load_pairs_from_exclusions(EXCLUSIONS_CSV, catalog)
    seen, dedup = set(), []
    for p in pairs:
        k = (p.x, p.y, round(p.ctx_scalar, 3))
        if k not in seen:
            seen.add(k)
            dedup.append(p)
    print(f"pairs {len(pairs):,} -> dedup {len(dedup):,} "
          f"({len(dedup)/len(pairs):.1%} unique by feature-signature)")

    idx = list(range(len(dedup)))
    random.Random(args.seed).shuffle(idx)
    cut = len(idx) // 5
    test = [dedup[i] for i in idx[:cut]]
    trn = [dedup[i] for i in idx[cut:]]
    fs = FeatureSpace.from_ability_features(collect_ability_features(dedup))
    m = train(trn, feature_space=fs, seed=args.seed, epochs=args.epochs, lr=0.1, l2=1e-3)
    print(f"feature_space={len(fs)}  n_train={len(trn):,}  n_test={len(test):,}  epochs={args.epochs}")
    print(f"[dedup] held-out pairwise accuracy: {pairwise_accuracy(m, test):.3f}")
    print(f"[dedup] in-sample (train split):    {pairwise_accuracy(m, trn):.3f}")


if __name__ == "__main__":
    main()
