"""
Rigorous unsupervised-learning evaluation of the Tasker-tiering clustering.

Clustering has no ground-truth accuracy, so we operationalize "accuracy" with the
conventional toolkit:
  * internal validity  : silhouette (up), Davies-Bouldin (down), Calinski-Harabasz (up)
  * model selection     : k-means elbow + silhouette-vs-k, GMM BIC-vs-k
  * stability           : bootstrap ARI (refit on resamples, measure agreement)
  * business recovery   : ARI / NMI vs a rule-based Volume x Reliability reference

We compare six approaches spanning the interpretability spectrum and place them on an
accuracy-vs-interpretability matrix.

Fit on a fixed standardized subsample of the US supply (fair + tractable for the
O(n^2) methods).
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import (KMeans, AgglomerativeClustering, SpectralClustering,
                             HDBSCAN, Birch)
from sklearn.mixture import GaussianMixture
from sklearn.metrics import (silhouette_score, davies_bouldin_score,
                             calinski_harabasz_score, adjusted_rand_score,
                             normalized_mutual_info_score)

sns.set_theme(style="whitegrid")
FIG = "analysis/taskrabbit-elite-criteria/figures"
RNG = np.random.default_rng(11)
K = 4                      # target cluster count for the parametric methods
N = 5000                   # subsample size
B = 6                      # bootstrap resamples for stability

FEATS = ["percent_of_bookings_tasker_canceled",
         "rolling_percent_total_invoices",
         "rolling_percent_total_revenue_cents"]

df = pd.read_csv("analysis/taskrabbit-elite-criteria/taskers_clustered.csv")
us = df[df.region == "US"].reset_index(drop=True)
idx = RNG.choice(len(us), size=N, replace=False)
sub = us.iloc[idx].reset_index(drop=True)
X = StandardScaler().fit_transform(sub[FEATS].to_numpy())

# --- rule-based Volume x Reliability reference (deterministic, max interpretable) --
def rule_labels(frame):
    cr = frame["percent_of_bookings_tasker_canceled"].to_numpy()
    rv = frame["rolling_percent_total_invoices"].to_numpy()
    lab = np.where(cr >= 0.20, 3,                    # cohort 4: unreliable
          np.where(rv <= 40, 0,                       # cohort 1: top volume
          np.where(rv <= 75, 1, 2)))                  # cohort 2 / 3
    return lab.astype(int)

ref = rule_labels(sub)

# ---------------------------------------------------------------------------
# Model selection curves (conventional k / component selection)
# ---------------------------------------------------------------------------
ks = range(2, 9)
inertia, sil_k, bic = [], [], []
for k in ks:
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(X)
    inertia.append(km.inertia_)
    sil_k.append(silhouette_score(X, km.labels_, sample_size=3000, random_state=0))
    bic.append(GaussianMixture(k, covariance_type="full", random_state=0).fit(X).bic(X))

fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
ax[0].plot(list(ks), inertia, "o-", color="#238b45", label="Inertia (elbow)")
ax[0].set_xlabel("k"); ax[0].set_ylabel("K-means inertia", color="#238b45")
ax2 = ax[0].twinx()
ax2.plot(list(ks), sil_k, "s--", color="#b8003a", label="Silhouette")
ax2.set_ylabel("Silhouette", color="#b8003a")
ax[0].set_title("K-means model selection", fontweight="bold", loc="left")
ax[0].axvline(4, color="0.6", ls=":")
ax[1].plot(list(ks), bic, "o-", color="#2b6cb0")
ax[1].set_xlabel("k (components)"); ax[1].set_ylabel("GMM BIC (lower better)")
ax[1].set_title("GMM model selection (BIC)", fontweight="bold", loc="left")
ax[1].axvline(np.argmin(bic) + 2, color="0.6", ls=":")
fig.tight_layout(); fig.savefig(f"{FIG}/fig_model_selection.png", dpi=130); plt.close(fig)
print("saved fig_model_selection.png   best-BIC k =", np.argmin(bic) + 2)

# ---------------------------------------------------------------------------
# Fitters (return labels for a given matrix)
# ---------------------------------------------------------------------------
def f_kmeans(Z):   return KMeans(K, n_init=10, random_state=0).fit_predict(Z)
def f_gmm(Z):      return GaussianMixture(K, covariance_type="full", random_state=0).fit_predict(Z)
def f_ward(Z):     return AgglomerativeClustering(K, linkage="ward").fit_predict(Z)
def f_spectral(Z): return SpectralClustering(K, affinity="nearest_neighbors",
                                             n_neighbors=15, random_state=0,
                                             assign_labels="kmeans").fit_predict(Z)
def f_hdbscan(Z):  return HDBSCAN(min_cluster_size=150, min_samples=5).fit_predict(Z)
def f_birch(Z):    return Birch(n_clusters=K).fit_predict(Z)

def fuzzy_cmeans(Z, c=K, m=2.0, max_iter=200, tol=1e-5, seed=0):
    """Fuzzy c-means. Returns the membership matrix U (n x c); rows sum to 1.

    Soft clustering: each point holds a *degree* of membership in every cluster,
    which is the honest model for a continuum with no crisp boundaries. m is the
    fuzziness exponent (m->1 approaches hard k-means; m=2 is the standard choice).
    """
    rng = np.random.default_rng(seed)
    U = rng.random((Z.shape[0], c)); U /= U.sum(1, keepdims=True)
    for _ in range(max_iter):
        Um = U ** m
        V = (Um.T @ Z) / Um.sum(0)[:, None]                     # centroids c x d
        D = np.fmax(np.linalg.norm(Z[:, None, :] - V[None, :, :], axis=2), 1e-10)
        Unew = 1.0 / ((D[:, :, None] / D[:, None, :]) ** (2 / (m - 1))).sum(2)
        if np.linalg.norm(Unew - U) < tol:
            U = Unew; break
        U = Unew
    return U

def f_fcm(Z):      return fuzzy_cmeans(Z).argmax(1)             # defuzzified labels

METHODS = {
    "Rule-based thresholds": (None, 10.0),   # reference; labels = ref
    "K-means (k=4)":         (f_kmeans, 8.0),
    "Birch (k=4)":           (f_birch, 7.0),
    "Fuzzy c-means (k=4)":   (f_fcm, 5.5),
    "GMM (k=4)":             (f_gmm, 6.0),
    "Ward hierarchical":     (f_ward, 6.0),
    "Spectral (k=4)":        (f_spectral, 3.0),
    "HDBSCAN (auto)":        (f_hdbscan, 4.0),
}

# fuzzy partition coefficient (1 = crisp, 1/c = maximally fuzzy) -- how overlapping
# the clusters really are; low FPC confirms the "continuum, not blobs" story.
_U = fuzzy_cmeans(X)
FPC = float((_U ** 2).sum() / len(X))
print("Fuzzy partition coefficient (FPC): %.3f   (1=crisp, %.2f=max fuzzy)" % (FPC, 1 / K))

def internal(Z, lab):
    """Validity indices, ignoring HDBSCAN noise (-1)."""
    m = lab >= 0
    if len(np.unique(lab[m])) < 2:
        return np.nan, np.nan, np.nan
    return (silhouette_score(Z[m], lab[m]),
            davies_bouldin_score(Z[m], lab[m]),
            calinski_harabasz_score(Z[m], lab[m]))

def stability(fitter):
    """Mean bootstrap ARI: refit on 80% resamples, compare to full labelling on overlap."""
    full = fitter(X)
    scores = []
    for _ in range(B):
        bi = RNG.choice(len(X), size=int(0.8 * len(X)), replace=False)
        lb = fitter(X[bi])
        scores.append(adjusted_rand_score(full[bi], lb))
    return float(np.mean(scores))

rows = []
labels_store = {}
for name, (fitter, interp) in METHODS.items():
    lab = ref.copy() if fitter is None else fitter(X)
    labels_store[name] = lab
    sil, db, ch = internal(X, lab)
    n_clusters = len(np.unique(lab[lab >= 0]))
    noise = float(np.mean(lab < 0)) * 100
    stab = 1.0 if fitter is None else stability(fitter)
    ari = adjusted_rand_score(ref, lab)
    nmi = normalized_mutual_info_score(ref, lab)
    rows.append(dict(method=name, interpretability=interp, n_clusters=n_clusters,
                     noise_pct=round(noise, 1), silhouette=round(sil, 3),
                     davies_bouldin=round(db, 3), calinski_harabasz=round(ch, 0),
                     stability_ari=round(stab, 3), business_ari=round(ari, 3),
                     business_nmi=round(nmi, 3)))
    print(f"  {name:22s} clusters={n_clusters} noise={noise:4.1f}%  sil={sil:.3f} "
          f"DB={db:.2f} CH={ch:6.0f}  stab={stab:.3f}  bizARI={ari:.3f}")

res = pd.DataFrame(rows)

# ---------------------------------------------------------------------------
# Composite "accuracy" = mean of min-max normalized [silhouette, -DB, CH, stability].
#
# CRITICAL: internal indices are computed only on CLUSTERED points, so a method that
# dumps hard points into "noise" (HDBSCAN here, ~70%) gets a flatteringly clean score
# on the easy 30% it kept. Leaving most of the supply untiered is a failure for this
# task, so we coverage-adjust the validity indices before scoring:
#     adj_sil = sil * coverage,  adj_CH = CH * coverage,  adj_DB = DB / coverage
# (coverage = share of Taskers assigned to a usable cluster). Stability is left as-is.
# ---------------------------------------------------------------------------
def nrm(s, invert=False):
    s = s.astype(float)
    v = (s.max() - s) if invert else (s - s.min())
    rng = (s.max() - s.min())
    return v / rng if rng else s * 0 + 0.5

res["coverage_pct"] = (100 - res.noise_pct).round(1)
cov = res.coverage_pct / 100.0
adj_sil = res.silhouette * cov
adj_ch = res.calinski_harabasz * cov
adj_db = res.davies_bouldin / cov
res["accuracy"] = (nrm(adj_sil) + nrm(adj_db, invert=True)
                   + nrm(adj_ch) + nrm(res.stability_ari)) / 4
res = res.sort_values("accuracy", ascending=False).reset_index(drop=True)
res.to_csv("analysis/taskrabbit-elite-criteria/clustering_evaluation.csv", index=False)
print("\n", res[["method", "silhouette", "davies_bouldin", "stability_ari",
                  "coverage_pct", "business_ari", "interpretability", "accuracy"]].to_string(index=False))

# ---------------------------------------------------------------------------
# Accuracy vs interpretability matrix
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9.6, 6.4))
xmid, ymid = 5.5, res.accuracy.median()
ax.axvspan(xmid, 10.7, ymin=0, ymax=1, color="#f0f7f0", alpha=0.5, zorder=0)
ax.axhline(ymid, color="0.85", lw=1); ax.axvline(xmid, color="0.85", lw=1)
sizes = 240 + res.business_ari.clip(lower=0) * 700
colors = sns.color_palette("viridis", len(res))
# per-method label offsets (points) to avoid collisions among close points
OFFSETS = {"GMM (k=4)": (0, -18), "Fuzzy c-means (k=4)": (0, -18),
           "Spectral (k=4)": (0, -18), "K-means (k=4)": (0, 14),
           "Ward hierarchical": (0, 14), "Rule-based thresholds": (0, 14),
           "Birch (k=4)": (0, 14), "HDBSCAN (auto)": (34, -4)}
for i, r in res.iterrows():
    ax.scatter(r.interpretability, r.accuracy, s=sizes[i], color=colors[i],
               edgecolor="white", linewidth=1.5, zorder=3)
    ox, oy = OFFSETS.get(r.method, (0, 14))
    ax.annotate(r.method, (r.interpretability, r.accuracy), xytext=(ox, oy),
                textcoords="offset points", ha="center", fontsize=9.5, fontweight="bold")
ax.text(10.55, 0.02, "bubble = business recovery (ARI vs rule cohorts)",
        fontsize=8, color="0.4", ha="right")
ax.text(8.0, 0.90, "SWEET SPOT\ninterpretable + valid", fontsize=9.5, color="#2f7d32",
        ha="center", va="top", style="italic")
ax.set_xlabel("Interpretability  (stakeholder-explainable, thresholdable) →", fontsize=11)
ax.set_ylabel("Cluster accuracy  (coverage-adj. validity + stability, norm.) →", fontsize=11)
ax.set_xlim(2, 10.6); ax.set_ylim(-0.05, 1.05)
ax.set_title("Accuracy vs interpretability — Tasker-tiering approaches",
             fontsize=13, fontweight="bold", loc="left")
fig.tight_layout(); fig.savefig(f"{FIG}/fig_accuracy_interpretability.png", dpi=130)
plt.close(fig)
print("\nsaved fig_accuracy_interpretability.png")
print("wrote clustering_evaluation.csv")
