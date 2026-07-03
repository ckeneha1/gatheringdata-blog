"""
Recreate the slides 12-34 visuals from the synthetic taskers.csv.

Runs the same k-means progression the deck walks through and saves each figure to
figures/. The point is to show the *methodology*:

  fig_12  comet scatter (close rate vs rolling invoices, hue = rolling revenue)
  fig_15  same, with eyeball tier partitions
  fig_17  naive k-means k=4  -> vertical stripes ("good cohort too large")
  fig_18  naive k-means k=5
  fig_19  naive k-means k=6
  fig_24  cancel-floor k-means k=4 (cancel vs rolling invoices) -> 2-D structure
  fig_26  cancel-floor k-means k=4 (cancel vs rolling revenue)
  fig_27  cancel-floor k-means with the volume x reliability box overlay
  fig_28  cancel-floor k-means k=15 -> best-of-best cohort shrinks
  fig_29  rolling invoices vs rolling revenue, cancel-floor clusters
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

sns.set_theme(style="darkgrid")
FIG = "analysis/taskrabbit-elite-criteria/figures"
df = pd.read_csv("analysis/taskrabbit-elite-criteria/taskers.csv")

CLUSTER_PALETTE = "rocket"          # pink -> purple -> navy, matches the deck
CONT_CMAP = "rocket_r"             # light(low) -> dark(high) continuous hue


def kmeans_label(frame, feats, k):
    X = StandardScaler().fit_transform(frame[feats].to_numpy())
    km = KMeans(n_clusters=k, n_init=10, random_state=7)
    lab = km.fit_predict(X)
    # Relabel clusters by mean rolling_percent_total_invoices so colours are
    # stable/interpretable: 0 = top-volume cohort ... high = marginal cohort.
    order = (pd.Series(frame["rolling_percent_total_invoices"].to_numpy())
             .groupby(lab).mean().sort_values().index)
    remap = {old: new for new, old in enumerate(order)}
    return np.array([remap[v] for v in lab])


def scatter(x, y, hue, data, title, fname, hue_continuous=False, legend_title=None,
            partitions=None, boxes=None):
    fig, ax = plt.subplots(figsize=(10, 5.6))
    if hue_continuous:
        sc = ax.scatter(data[x], data[y], c=data[hue], cmap=CONT_CMAP,
                        s=6, alpha=0.55, linewidths=0)
        cb = fig.colorbar(sc, ax=ax, pad=0.01)
        cb.set_label(legend_title or hue, fontsize=8)
    else:
        ncol = data[hue].nunique()
        pal = sns.color_palette(CLUSTER_PALETTE, ncol)
        sns.scatterplot(data=data, x=x, y=y, hue=hue, palette=pal,
                        s=7, alpha=0.6, linewidth=0, ax=ax,
                        legend="full")
        leg = ax.legend(title=legend_title or hue, fontsize=7, title_fontsize=8,
                        markerscale=1.4, loc="upper left", framealpha=0.85)
    if partitions:
        for xpos, lbl in partitions:
            ax.axvline(xpos, color="darkgreen", ls="--", lw=2)
            ax.text(xpos - 1, ax.get_ylim()[1] * 0.98, lbl, ha="right", va="top",
                    fontsize=9, color="darkgreen")
    if boxes:
        for (x0, x1, y0, y1, lbl) in boxes:
            ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False,
                                       edgecolor="limegreen", ls="--", lw=2.2))
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, lbl, ha="center", va="center",
                    fontsize=13, fontweight="bold", color="darkgreen")
    ax.set_title(title, fontsize=12, fontweight="bold", loc="left")
    ax.set_xlabel(x.upper(), fontsize=8)
    ax.set_ylabel(y.upper(), fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{FIG}/{fname}.png", dpi=130)
    plt.close(fig)
    print("saved", fname)


# ---- Slide 12 & 15: the comet, plain and partitioned --------------------------
scatter("rolling_percent_total_invoices", "percent_of_bookings_invoiced",
        "rolling_percent_total_revenue_cents", df,
        "Plotting & Comparing Each Tasker", "fig_12_comet",
        hue_continuous=True, legend_title="ROLLING_PERCENT_TOTAL_REVENUE_CENTS")

scatter("rolling_percent_total_invoices", "percent_of_bookings_invoiced",
        "rolling_percent_total_revenue_cents", df,
        "...then partition those Taskers into tiers?", "fig_15_eyeball",
        hue_continuous=True, legend_title="ROLLING_PERCENT_TOTAL_REVENUE_CENTS",
        partitions=[(12, "Best"), (30, "Very good"), (50, "Good"),
                    (80, "Okay")])

# ---- Slides 17-19: naive k-means (close rate + rolling vol + rolling rev) ------
naive_feats = ["percent_of_bookings_invoiced", "rolling_percent_total_invoices",
               "rolling_percent_total_revenue_cents"]
for k, fid in [(4, "fig_17_naive_k4"), (5, "fig_18_naive_k5"), (6, "fig_19_naive_k6")]:
    df[f"naive_k{k}"] = kmeans_label(df, naive_feats, k)
    scatter("rolling_percent_total_invoices", "percent_of_bookings_invoiced",
            f"naive_k{k}", df,
            f"A very quick pass at k-means clustering doesn't seem helpful (K={k})",
            fid, legend_title="cluster_label")

# ---- Slides 24-29: add the tasker-fault cancel "floor" ------------------------
floor_feats = ["percent_of_bookings_tasker_canceled",
               "rolling_percent_total_invoices",
               "rolling_percent_total_revenue_cents"]
df["floor_k4"] = kmeans_label(df, floor_feats, 4)

scatter("rolling_percent_total_invoices", "percent_of_bookings_tasker_canceled",
        "floor_k4", df, "Adding Tasker-fault cancels improves the look of our results!",
        "fig_24_floor_k4", legend_title="kmeans_cluster_label")

scatter("rolling_percent_total_revenue_cents", "percent_of_bookings_tasker_canceled",
        "floor_k4", df, "Adding Tasker-fault cancels improves the look of our results!",
        "fig_26_floor_k4_rev", legend_title="kmeans_cluster_label")

scatter("rolling_percent_total_revenue_cents", "rolling_percent_total_invoices",
        "floor_k4", df, "Adding Tasker-fault cancels improves the look of our results!",
        "fig_29_floor_k4_rollroll", legend_title="kmeans_cluster_label")

# Slide 27: volume x reliability box overlay
scatter("rolling_percent_total_invoices", "percent_of_bookings_tasker_canceled",
        "floor_k4", df, "Why was this exercise worth doing? (Volume x Reliability)",
        "fig_27_boxes", legend_title="kmeans_cluster_label",
        boxes=[(0, 55, 0, 0.15, "1"), (55, 78, 0, 0.15, "2"),
               (78, 101, 0, 0.15, "3"), (78, 101, 0.15, 0.9, "4")])

# ---- Slides 28/32-34: high cluster count -------------------------------------
df["floor_k15"] = kmeans_label(df, floor_feats, 15)
scatter("rolling_percent_total_invoices", "percent_of_bookings_tasker_canceled",
        "floor_k15", df, "What happens when we generate a lot of clusters? (K=15)",
        "fig_28_floor_k15", legend_title="kmeans_cluster_label")

df.to_csv("analysis/taskrabbit-elite-criteria/taskers_clustered.csv", index=False)
print("wrote taskers_clustered.csv")
