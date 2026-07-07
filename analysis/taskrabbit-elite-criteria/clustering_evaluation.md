# Evaluating the Tasker-tiering clustering

A data-science audit of the clustering behind the Elite tiering: how "accurate" is
the k-means model the deck used, how do alternative unsupervised methods compare, and
what's the accuracy-vs-interpretability trade-off? Reproduce with
`clustering_evaluation.py` (fits on a fixed 5,000-Tasker standardized subsample of the
US supply; features = tasker-fault cancel rate, rolling % invoices, rolling % revenue).

---

## 1. There is no ground-truth "accuracy" — so we triangulate

Clustering is unsupervised: there is no label to be right or wrong about. "Accuracy"
is operationalized with the standard toolkit, in three independent lenses:

| Lens | Metric(s) | Reads as |
|---|---|---|
| **Internal validity** | Silhouette ↑, Davies–Bouldin ↓, Calinski–Harabasz ↑ | Are the clusters compact and separated? |
| **Stability** | Bootstrap ARI (refit on 80% resamples, ×6) | Does the partition survive resampling, or is it an artifact? |
| **Business recovery** | ARI / NMI vs a rule-based Volume × Reliability reference | Does the method find the segmentation we actually care about? |

Plus a **coverage** check — what share of Taskers actually receive a usable tier
(see §4, the HDBSCAN trap). The composite `accuracy` score in the matrix is the mean
of min–max-normalized {silhouette, −DB, CH, stability}, **coverage-adjusted** so a
method can't score well by tiering only the easy points.

## 2. Model selection: k=4 is a business choice, not a statistical one

`fig_model_selection.png`:
- **K-means elbow** is smooth — inertia declines steadily with no sharp knee.
- **Silhouette vs k** is flat-to-declining past k=3.
- **GMM BIC** keeps falling out to k≥8 (never bottoms in a sensible range).

None of these crisply nominate k=4. That's expected: the supply is a **continuum**,
not four natural blobs, so information criteria just keep splitting it. The honest
takeaway — and a good thing to say out loud — is that **k=4 was chosen for business
legibility** (four namable tiers), and the analysis below asks which *method*, given
k=4, produces the most valid and stable version of that partition.

## 3. The comparison

Eight approaches spanning the interpretability spectrum, all at k=4 where applicable:

| Method | Silhouette | DB ↓ | Stability (ARI) | Coverage | Business ARI | Interpretability | **Accuracy** |
|---|---|---|---|---|---|---|---|
| **K-means (k=4)** | 0.574 | 0.67 | **0.996** | 100% | **0.60** | 8 | **0.99** |
| **Fuzzy c-means (k=4)** | 0.566 | 0.67 | 0.994 | 100% | 0.56 | 5.5 | 0.98 |
| Ward hierarchical | 0.530 | 0.64 | 0.793 | 100% | 0.50 | 6 | 0.82 |
| Rule-based thresholds | 0.543 | 0.82 | 1.000 | 100% | 1.00* | 10 | 0.79 |
| Birch (k=4) | 0.556 | 0.84 | 0.707 | 100% | 0.54 | 7 | 0.65 |
| Spectral (k=4) | 0.125 | 0.73 | 0.949 | 100% | 0.14 | 3 | 0.46 |
| HDBSCAN (auto) | 0.658 | 0.55 | 0.834 | **30%** | −0.03 | 4 | 0.40 |
| GMM (k=4) | 0.375 | 0.92 | 0.383 | 100% | 0.53 | 6 | 0.33 |

\* Rule-based is the reference for the business-recovery metric, so its ARI is 1.0 by
construction — not evidence of quality. Its accuracy score comes only from the
validity + stability lenses.

**K-means is the sweet spot** (`fig_accuracy_interpretability.png`, upper-right):
highest coverage-adjusted accuracy, the best business recovery of any *learned*
method (ARI 0.60), near-perfect stability, and high interpretability (centroids you
can profile and hand to ops). This independently **validates the deck's choice** —
the pragmatic method also turns out to be the statistically strongest one here.

## 4. The two findings worth presenting

### (a) HDBSCAN — the coverage trap (why you never read silhouette alone)

On the raw internal indices, HDBSCAN looks like the **best** model: highest silhouette
(0.658), lowest Davies–Bouldin (0.55), Calinski–Harabasz 2.5× the field. It is also
the **worst** choice for this task — because it earns those clean numbers by dumping
**~70% of Taskers into "noise"** and scoring only on the dense 30% it kept. Its
recovery of the business structure is essentially random (ARI −0.03).

This is the classic density-clustering failure on a **continuum**: with no density
gaps to find, HDBSCAN keeps a few tight cores and discards the gradient. Internal
validity indices reward that cherry-picking. Coverage-adjusting the score (scaling
validity by the share of Taskers actually clustered) correctly drops it from a naive
0.93 to 0.40. **Lesson: an internal index computed on a subset is not comparable to
one computed on the whole population — always report coverage.**

### (b) Fuzzy c-means — the right tool for the boundaries

Fuzzy c-means lands almost exactly on K-means for accuracy (0.98 vs 0.99). That's
because a *defuzzified* FCM (argmax of the memberships) ≈ K-means — same objective,
same hard partition. So as a tier-assignment engine it adds nothing over K-means and
costs interpretability (extra fuzziness parameter + a defuzzification step).

Its payoff is different: it **refuses to pretend the boundaries are crisp**, which
matches the data.
- **Fuzzy partition coefficient = 0.77** (1 = crisp, 0.25 = maximally fuzzy) — the
  clusters genuinely overlap; this is not four clean blobs.
- **76%** of Taskers have a confident top membership (>0.7), but **~13% are genuinely
  mixed** (top membership 0.4–0.6) — they sit on a tier boundary where a hard
  "Elite / not-Elite" label is close to a coin-flip.

That 13% is decision-relevant. Hard K-means treats a 0.52-Elite Tasker identically to
a 0.95-Elite one. Fuzzy memberships let you handle the margin deliberately — a
provisional/at-risk Elite band, confidence-weighted incentives, or a review queue —
instead of a brittle cutoff.

## 5. Recommendation

- **Ship K-means (k=4) — or the rule-based thresholds — for the published tiers.** Both
  sit in the interpretable + valid corner. Rules trade a little validity for total
  transparency and zero model risk; K-means trades a little transparency for the
  strongest validity/stability and genuine data-driven boundaries. K-means to
  *discover* the cut points, rules to *operationalize* them, is a clean pairing.
- **Keep fuzzy c-means as a companion diagnostic for boundary cases**, since the data
  is a continuum (FPC 0.77) and ~13% of Taskers are true edge cases.
- **Avoid GMM (unstable here — stability ARI 0.38, label-switching across resamples),
  Spectral (poor validity, doesn't recover the business structure), and HDBSCAN
  (leaves ~70% of supply untiered)** for this particular problem shape.
- Revisit if the feature space changes: these conclusions are specific to a smooth,
  low-dimensional, continuum-shaped supply. Add sparse or non-convex structure and the
  density/graph methods could earn their place back.
