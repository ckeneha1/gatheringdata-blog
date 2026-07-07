# Elite Metric Regroup — synthetic dataset & methodology recreation

A **fully synthetic** mock of the supply dataset behind the *Elite Metric Regroup*
deck (Taskrabbit Tasker quality tiering). It contains **no real company data** — it
is reverse-engineered from the charts (slides 12–34) so the *methodology* can be
presented in an interview setting without exposing anything proprietary.

The goal was to reproduce the **shapes** and the **analytical story**, with headline
numbers in the right ballpark — not to leak or exactly reconstruct real figures.

## What's here

| File | What it is |
|---|---|
| `generate_data.py` | Builds the 77,818-Tasker population (one row per Tasker × metro-category). |
| `make_charts.py` | Runs the k-means progression and renders the clean slides 12–34 into `figures/`. |
| `make_annotated_charts.py` | Deck-style annotated versions (green dashed circles/boxes, yellow callouts). |
| `build_summary.py` | Assigns cohorts/Elite and prints the tier tables (slides 30, 35–37). |
| `impact_analysis.py` | Post-rollout invoice/revenue projection from the 1.5× compliance fact (+ 2 charts, memo). |
| `clustering_evaluation.py` | Evaluates 8 unsupervised methods (validity/stability/recovery) → accuracy-vs-interpretability matrix. |
| `build_deck.cjs` | Assembles `Elite_Metric_Regroup_methodology.pptx` from the figures. |
| `taskers.csv` | Raw + derived per-Tasker fields. |
| `taskers_clustered.csv` | Above + every cluster label, `cohort`, `is_elite`. |
| `summary_*_tiers.csv`, `summary_slide30_aggregate.csv` | The closing tables. |
| `impact_analysis.md`, `impact_results.csv` | Impact memo + scenario table. |
| `clustering_evaluation.md`, `clustering_evaluation.csv` | Model-evaluation memo + metrics table. |
| `figures/` | The recreated charts (clean + `_annotated`) plus impact & evaluation charts. |
| `Elite_Metric_Regroup_methodology.pptx` | 22-slide deck: methodology + model-evaluation + impact. Upload to Google Drive → "Open with Google Slides". |

Run order (from repo root):
```bash
python3 analysis/taskrabbit-elite-criteria/generate_data.py         # -> taskers.csv
python3 analysis/taskrabbit-elite-criteria/make_charts.py           # -> figures/ + taskers_clustered.csv
python3 analysis/taskrabbit-elite-criteria/make_annotated_charts.py # -> figures/*_annotated.png
python3 analysis/taskrabbit-elite-criteria/build_summary.py         # -> summary_*.csv (+cohort/is_elite)
python3 analysis/taskrabbit-elite-criteria/impact_analysis.py       # -> impact_* + impact charts
python3 analysis/taskrabbit-elite-criteria/clustering_evaluation.py # -> clustering_evaluation.* + matrix
node   analysis/taskrabbit-elite-criteria/build_deck.cjs            # -> .pptx  (then: python3 <pptx-skill>/scripts/rezip.py <file>)
```
Seeded (`np.random.default_rng(20240619)`), so it's fully reproducible. The deck
builder needs `pptxgenjs` (`npm install -g pptxgenjs`).

### Getting it into Google Slides
The `.pptx` imports losslessly: upload it to Google Drive, right-click → **Open with
→ Google Slides** (or in Slides, *File → Import slides*). Images and the table come
through as native, editable objects.

## The data model (why everything is "rolling" and "within metcat")

The unit is a **Tasker inside a metro-category (metcat)**. The deck's whole question
is *"who performs well **relative to their local peers**"* (slide 9), so the headline
features are computed **within each metcat**:

- `rolling_percent_total_invoices` (x-axis of most charts): rank a metcat's Taskers
  by invoice contribution **descending**, take the running cumulative share (0–100).
  **Top contributors sit at low values (~5–20)**; the long tail of marginal Taskers
  piles up near 100. (This is exactly the slide-10 "rolling % of MetCat invoices"
  table.)
- `rolling_percent_total_revenue_cents`: same cumulative trick for revenue. Strongly
  (not perfectly) correlated with the invoice version → the left-light/right-dark hue
  gradient on slides 12–15.
- `percent_of_bookings_invoiced`: close rate (y-axis, slides 12–20).
- `percent_of_bookings_tasker_canceled`: tasker-fault cancel rate (y-axis, 24–37).

### How the shapes are engineered
- **Heavy-tailed volume per metcat** → the cumulative curve produces the
  **comet/tadpole** shape (dense "head" of top contributors on the left, marginal
  Taskers bunched near 100 on the right).
- Close rate and cancel rate are **binomial draws** on each Tasker's booking count.
  Low-volume Taskers therefore land on **discrete fractions** (1/1, 1/2, 1/3 …) —
  that's the authentic horizontal striping and the `y = 1.0` band, and it's why the
  **cancel-rate funnel widens at low volume** (small denominators = high variance).
- A latent "good Tasker" factor loosely lifts volume + close rate and lowers cancel
  rate, but the correlations are deliberately **loose** so cancellation stays a
  genuinely separate axis from volume. That separation is the entire payoff below.

## The methodology arc (this is the part to present)

The deck is really an argument about **how to partition supply**, and which feature
set makes clustering *useful*. The synthetic data reproduces each beat:

1. **Eyeball it (slides 12–15 → `fig_12`, `fig_15`).** Plot close rate vs rolling
   invoices, hue = rolling revenue. You *can* draw Best→Needing-support bands by
   hand — quick, but biased and not iterable.

2. **Naive k-means fails (slides 17–19 → `fig_17/18/19`).** Cluster on
   `{close_rate, rolling_invoices, rolling_revenue}`. Because the two rolling
   features dominate and are collinear, k-means just produces **vertical stripes** —
   it re-discovers the volume axis and nothing else. The resulting "good" cohort is
   **far too large** (top band ≈ 30%+ of supply) to base an Elite program on. *This
   is the key teaching point: unsupervised learning is "very dependent on a few
   inputs" (slide 16) — feed it redundant features and it tells you nothing new.*

3. **Add a behavioral "floor" and it works (slides 22–29 → `fig_24/26/27/29`).**
   Swap in `percent_of_bookings_tasker_canceled` (tasker-fault cancels). Now k-means
   has an **orthogonal reliability axis**, and k=4 resolves into a clean
   **Volume × Reliability** matrix:

   | Cohort | Volume | Reliability | ~% of supply |
   |---|---|---|---|
   | 1 | ✅ high | ✅ low cancel | ~10% |
   | 2 | ~ mid | ✅ low cancel | ~21% |
   | 3 | ❌ low | ✅ low cancel | ~61% |
   | 4 | ❌ low | ❌ high cancel | ~7% |

   The single feature change is what turns a useless clustering into a defensible
   tiering. That's the headline.

4. **More clusters → tighter Elite (slides 28, 32–34 → `fig_28`).** Push k to 15 and
   the best-of-the-best cluster **progressively shrinks** to a tight, defensible
   Elite group. Elite is defined here as that tightest high-volume/low-cancel k=15
   cluster intersected with Cohort 1 — i.e., **how "elite" you want to be is a
   choice of k**, which is exactly the deck's point.

## Fidelity vs the deck (US tiers)

| Tier | This mock (inv/mo, rev/mo, %) | Deck (slide 35/38) |
|---|---|---|
| Cohort 1 — Elite | 12.9, $580, 2.4% | 12, $530, 3% |
| Cohort 1 — Total | 9.4, $416, 10.4% | 8, $350, 11% |
| Cohort 2 | 3.5, $141, 21.4% | 2, $80, 23% |
| Cohort 3 | 0.6, $22, 61.3% | <1, $15, 58% |
| Cohort 4 | 0.3, $11, 6.9% (cancel 80%) | <1, <$15, 8% (cancel >20%) |

Cohort **proportions** (10/21/61/7 vs 11/23/58/8) and the Elite headline (≈13 inv,
≈$580 vs 12 inv, $530) land close. Known approximations, by design:
- Per-Tasker volumes/revenue in the mid cohorts run a bit hot (~1.5×).
- The Cohort-4 mean cancel rate is high (~80%) because k-means isolates the extreme
  low-volume cancellers; the deck's threshold framing (">20%") is gentler. The
  *existence of a distinct unreliable cohort* is what matters and is reproduced.
- Geography is modeled as US + an "INTL" remainder to hit the ~58.6k US / ~77.8k
  global totals; metro/category IDs are arbitrary integers, not real geographies.
