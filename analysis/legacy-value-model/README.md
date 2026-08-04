# legacy-value-model — conditional value model (Phase 1.4)

Learns, from primer inclusion/exclusion data, a **conditional preference
function** over Magic cards: given a card's ability-at-cost features and the
field state, does it clear the threshold to occupy a slot in a Legacy
archetype? See `.agent/briefs/legacy-value-model-rebuild.md` §1.4 / §2.4.

## The idea in one line

The exclusion dataset is already pairwise — each `exclusions.csv` row says
*played card X was preferred over silently-omitted neighbour Y, in this
archetype/pool/field*. So the model is a **pairwise ranker** learning
`P(X ≻ Y | context)`, and a new card's verdict reproduces the framework's own
threshold rule: it clears a slot iff it beats the **weakest** incumbent that
currently occupies the function (the lower bound of the played set).

## Why it's *conditional*

A plain feature-difference model is field-blind: the shared context cancels in
`φ(X) − φ(Y)`. Conditionality is restored by **interaction features** — each
ability feature times a field-context scalar — so a preference can flip with
the metagame (counterspells clear the bar in a combo-heavy field, not a
creature-heavy one). v0 uses one context scalar (`field_concentration` = top
archetype's share); adding per-axis pressure scalars (tempo/combo/creature
share) is the documented extension point in `field_concentration` /
`pair_features`.

## Inputs (gitignored — owner's machine, brief §5)

| Input | From | Used for |
|---|---|---|
| `../mtg-primers/data/exclusions.csv` | `build_exclusions.py build` | pairwise preference labels (+ confidence weights, field stamps) |
| Scryfall oracle/all-cards cache | shared with Post 1/2 | card → ability feature vector (via `mtg-primers/function_index.py`) |
| `../mtg-legacy-tournament/data/deck_clusters.csv` | `infer_archetypes.py` | (future) cluster-based incumbent slots for prediction |

The trained scorer's coefficients are directly inspectable — each is "how much
this ability feature (optionally × field context) shifts the odds of clearing
a slot threshold." Thresholds become a learned decision boundary in
ability-at-cost space rather than expert feel.

## Run order (local)

```
# prerequisites (other Phase 1 modules, against the real panel/primers):
#   cd ../mtg-primers && uv run python build_exclusions.py build
uv run python value_model.py train     # fit on exclusions.csv → data/model.json
uv run python value_model.py eval       # k-fold held-out pairwise accuracy
uv run python value_model.py predict --candidates <candidates.json>   # → data/verdicts.csv
```

`eval` is the honesty check: ~0.5 held-out pairwise accuracy means the
exclusion labels carry no learnable threshold signal (the model adds nothing);
materially above 0.5 means the silences are informative. This number, plus the
`backtest.py` temporal holdouts, gates how much authority the model claims
(brief §2.5).

## Predict input format

`--candidates` is JSON: a list of
`{name, oracle_text, keywords, cmc, archetype, field_top, incumbents:[{name,
oracle_text, keywords, cmc}]}`. The `incumbents` are the in-archetype,
in-function cards the candidate competes with (named, so each verdict is
explainable). For the Marvel run (Phase 2), incumbents come from the framework
verdicts' named slot occupants and/or the inferred-cluster characteristic cards.

## Tests

`uv run pytest` (fixture-only, no real data/network): feature mapping, the
field-conditionality property, learning separable preferences, confidence
weighting, verdict mapping (all three outcomes + the weakest-incumbent rule),
k-fold CV, and persistence.
