"""
Annotated, presentation-ready versions of the key charts -- matching the deck's
own markup style: dark-green dashed circles/boxes for callout regions and
pale-yellow sticky-note text boxes.

Reuses taskers_clustered.csv (cluster labels + cohort already computed by
make_charts.py / build_summary.py), so no k-means rerun is needed.

Outputs to figures/ with an `_annotated` suffix.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle
import seaborn as sns

sns.set_theme(style="darkgrid")
BG = "#FFFCE4"                          # cream figure background to match the deck
plt.rcParams.update({"figure.facecolor": BG, "savefig.facecolor": BG,
                     "savefig.edgecolor": BG})
FIG = "analysis/taskrabbit-elite-criteria/figures"
df = pd.read_csv("analysis/taskrabbit-elite-criteria/taskers_clustered.csv")

GREEN = "#1b5e20"
DASH = (0, (6, 4))
NOTE_BBOX = dict(boxstyle="round,pad=0.6", facecolor="#fbfbd6",
                 edgecolor="0.55", linewidth=1.0)
CLUSTER_PALETTE = "rocket"
CONT_CMAP = "rocket_r"


def base_fig(title):
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.set_title(title, fontsize=13, fontweight="bold", loc="left")
    return fig, ax


def comet_scatter(ax):
    """Close rate vs rolling invoices, hue = rolling revenue, deck-style discrete
    legend binned at 20/40/60/80/100."""
    bins = [0, 20, 40, 60, 80, 100.01]
    labels = ["20", "40", "60", "80", "100"]
    cat = pd.cut(df["rolling_percent_total_revenue_cents"], bins=bins, labels=labels,
                 include_lowest=True)
    pal = sns.color_palette(CONT_CMAP, 5)
    sns.scatterplot(x=df["rolling_percent_total_invoices"],
                    y=df["percent_of_bookings_invoiced"],
                    hue=cat, palette=pal, hue_order=labels,
                    s=6, alpha=0.55, linewidth=0, ax=ax)
    ax.legend(title="ROLLING_PERCENT_TOTAL_REVENUE_CENTS", fontsize=7,
              title_fontsize=7, loc="lower left", markerscale=1.4, framealpha=0.9)
    ax.set_xlabel("ROLLING_PERCENT_TOTAL_INVOICES", fontsize=8)
    ax.set_ylabel("PERCENT_OF_BOOKINGS_INVOICED", fontsize=8)


def cluster_scatter(ax, x, y, hue):
    ncol = df[hue].nunique()
    pal = sns.color_palette(CLUSTER_PALETTE, ncol)
    sns.scatterplot(data=df, x=x, y=y, hue=hue, palette=pal, s=7, alpha=0.6,
                    linewidth=0, ax=ax, legend="full")
    ax.legend(title="kmeans_cluster_label", fontsize=7, title_fontsize=8,
              markerscale=1.4, loc="upper left", framealpha=0.85)
    ax.set_xlabel(x.upper(), fontsize=8)
    ax.set_ylabel(y.upper(), fontsize=8)


def ellipse(ax, xy, w, h):
    ax.add_patch(Ellipse(xy, w, h, fill=False, edgecolor=GREEN, lw=3, ls=DASH))


def box(ax, x0, y0, w, h, color=GREEN):
    ax.add_patch(Rectangle((x0, y0), w, h, fill=False, edgecolor=color, lw=3, ls=DASH))


def note(ax, x, y, text, ha="left", va="center"):
    ax.text(x, y, text, fontsize=10, ha=ha, va=va, bbox=NOTE_BBOX, zorder=10)


def badge(ax, text):
    ax.text(0.01, 0.02, text, transform=ax.transAxes, fontsize=11, fontweight="bold",
            ha="left", va="bottom",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#fbfbd6", edgecolor="0.55"))


def save(fig, name):
    fig.tight_layout()
    fig.savefig(f"{FIG}/{name}.png", dpi=130)
    plt.close(fig)
    print("saved", name)


# --- Slide 13: the "good" Taskers, circled + callout -------------------------
fig, ax = base_fig("Next steps - how does each Tasker compare to their metcat?")
comet_scatter(ax)
ellipse(ax, (12, 0.66), 26, 0.52)
note(ax, 30, 0.55,
     "These Taskers earn a lot of\ninvoices and revenue relative\n"
     "to their peers*, and close a\nhigh % of their jobs!\n\n"
     "*other Taskers in the same metro-category")
save(fig, "fig_13_annotated_good_cohort")

# --- Slide 14: can we group like Taskers (4 circles) -------------------------
fig, ax = base_fig("Can we group like Taskers...")
comet_scatter(ax)
for cx in (12, 38, 62, 86):
    ellipse(ax, (cx, 0.55), 24, 0.78)
save(fig, "fig_14_annotated_groups")

# --- Slide 15: eyeball partitions into tiers --------------------------------
fig, ax = base_fig("...then partition those Taskers into tiers?")
comet_scatter(ax)
for xpos, lbl in [(12, "Best"), (30, "Very good"), (50, "Good"), (80, "Okay")]:
    ax.axvline(xpos, color=GREEN, ls="--", lw=2)
    ax.text(xpos - 1, 1.05, lbl, ha="right", va="bottom", fontsize=10, color=GREEN)
ax.text(90, 1.05, "Needing support", ha="center", va="bottom", fontsize=10, color=GREEN)
save(fig, "fig_15_annotated_tiers")

# --- Slide 17: naive k-means, "good cohort too large" -----------------------
fig, ax = base_fig("A very quick pass at k-means clustering doesn't seem helpful")
cluster_scatter(ax, "rolling_percent_total_invoices",
                "percent_of_bookings_invoiced", "naive_k4")
note(ax, 38, 0.30,
     "This is interesting to look\nat, but the \"good\" cohort is\n"
     "too large to base Elite\ncriteria on")
badge(ax, "K = 4")
save(fig, "fig_17_annotated_naive_k4")

# --- Slide 25: cancel floor, Elite region boxed -----------------------------
fig, ax = base_fig("Adding Tasker-fault cancels improves the look of our results!")
cluster_scatter(ax, "rolling_percent_total_invoices",
                "percent_of_bookings_tasker_canceled", "floor_k4")
box(ax, 0, 0.0, 45, 0.16, color="limegreen")
note(ax, 60, 0.55,
     "Low rolling-invoice rank (high\nvolume) AND a low cancel\n"
     "floor = our Elite candidates")
save(fig, "fig_25_annotated_elite_box")

# --- Slide 27: Volume x Reliability matrix ----------------------------------
fig, ax = base_fig("Why was this exercise worth doing?  (Volume x Reliability)")
cluster_scatter(ax, "rolling_percent_total_invoices",
                "percent_of_bookings_tasker_canceled", "floor_k4")
for (x0, x1, lbl) in [(0, 55, "1"), (55, 78, "2"), (78, 101, "3")]:
    box(ax, x0, 0.0, x1 - x0, 0.16, color="limegreen")
    ax.text((x0 + x1) / 2, 0.08, lbl, ha="center", va="center", fontsize=15,
            fontweight="bold", color=GREEN, zorder=11)
box(ax, 78, 0.16, 23, 0.74, color="limegreen")
ax.text(89, 0.5, "4", ha="center", va="center", fontsize=15, fontweight="bold",
        color=GREEN, zorder=11)
note(ax, 30, 0.62,
     "1 = high volume, reliable\n2 = mid volume, reliable\n"
     "3 = low volume, reliable\n4 = high cancel = needs support")
save(fig, "fig_27_annotated_matrix")

# --- Slide 28: high cluster count, best cohort shrinks -----------------------
fig, ax = base_fig("What happens when we generate a lot of clusters?")
cluster_scatter(ax, "rolling_percent_total_invoices",
                "percent_of_bookings_tasker_canceled", "floor_k15")
ellipse(ax, (10, 0.04), 18, 0.13)
note(ax, 45, 0.55,
     "Our best-of-the-best cohort\ngradually shrinks as we add\nclusters!")
badge(ax, "K = 15")
save(fig, "fig_28_annotated_k15")

# --- Slide 29: rolling vs rolling, main cohort circled ----------------------
fig, ax = base_fig("Adding Tasker-fault cancels improves the look of our results!")
cluster_scatter(ax, "rolling_percent_total_revenue_cents",
                "rolling_percent_total_invoices", "floor_k4")
ellipse(ax, (38, 40), 70, 78)
save(fig, "fig_29_annotated_circle")

print("\nAll annotated figures written to", FIG)
