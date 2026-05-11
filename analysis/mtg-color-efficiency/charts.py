"""
Three charts for the color-vs-efficiency post:
  1. Null distribution — permuted eta² histogram + observed value
  2. Multicolor anomaly — per-color residual means (lollipop)
  3. Density curves — Blue vs each other color, efficiency distributions
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.stats import gaussian_kde
from pathlib import Path

np.random.seed(42)
N_PERM = 5_000

# --- Style ---
ACCENT       = "#b2d4e5"
ACCENT_DARK  = "#7aafc9"
TEXT         = "#363737"
TEXT_SECONDARY = "#868787"
BORDER       = "#dddddd"

CSV = Path("/Users/connorkenehan/Documents/Documents - Connor's MacBook Air/GitHub/gatheringdata-blog/public/data/mtg-card-power-rankings.csv")
OUT = Path("/tmp")

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
df = pd.read_csv(CSV)
df["cmc_bin"] = df["cmc"].clip(upper=7).astype(int)
df = df[df["cmc_bin"] >= 1]

COLOR_ORDER = ["White", "Blue", "Black", "Red", "Green", "Multicolor", "Colorless"]
df = df[df["color"].isin(COLOR_ORDER)].copy()

# CMC-residualize
df["residual"] = df["abilities_per_cmc"] - df.groupby("cmc_bin")["abilities_per_cmc"].transform("mean")

vals   = df["residual"].values
labels = df["color"].values

# ---------------------------------------------------------------------------
# Eta² (vectorized)
# ---------------------------------------------------------------------------
def eta_squared_vec(v, l):
    gm = v.mean()
    ss_total = ((v - gm) ** 2).sum()
    if ss_total == 0: return 0.0
    groups = np.unique(l)
    return sum(len(v[l==g]) * (v[l==g].mean() - gm)**2 for g in groups) / ss_total

# Observed
obs_eta = eta_squared_vec(vals, labels)

# Permutation null (shuffle values — equivalent to shuffling labels)
group_sizes = {g: (labels == g).sum() for g in np.unique(labels)}
null_etas = np.array([
    eta_squared_vec(np.random.permutation(vals), labels)
    for _ in range(N_PERM)
])
p_val = (null_etas >= obs_eta).mean()

print(f"Observed eta² = {obs_eta:.4f}  p = {p_val:.4f}")

# Per-color residual means
residual_means = (
    df.groupby("color")["residual"].mean()
    .reindex(COLOR_ORDER)
    .sort_values()
)

# ---------------------------------------------------------------------------
# Chart 1 — Null distribution
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 4.5), facecolor="white")
ax.set_facecolor("white")

ax.hist(null_etas, bins=60, color=ACCENT, edgecolor="white", linewidth=0.4, alpha=0.9,
        label="Permuted η² (null distribution)")
ax.axvline(obs_eta, color=ACCENT_DARK, linewidth=2.2, linestyle="-",
           label=f"Observed η² = {obs_eta:.4f}")

# Shade the tail
tail_vals = null_etas[null_etas >= obs_eta]
if len(tail_vals):
    ax.axvspan(obs_eta, null_etas.max() * 1.05, color=ACCENT_DARK, alpha=0.12)

ax.annotate(
    f"p < 0.001\n(0 of {N_PERM:,} permutations\nexceed observed)",
    xy=(obs_eta, 20),
    xytext=(obs_eta * 0.55, 180),
    xycoords="data", textcoords="data",
    fontsize=9, color=TEXT_SECONDARY,
    va="bottom", ha="center",
    arrowprops=dict(arrowstyle="-", color=BORDER, lw=1.2),
)

for spine in ax.spines.values():
    spine.set_edgecolor(BORDER)
ax.tick_params(colors=TEXT_SECONDARY, labelsize=10)
ax.xaxis.label.set_color(TEXT_SECONDARY)
ax.yaxis.label.set_color(TEXT_SECONDARY)
ax.grid(axis="y", color=BORDER, linewidth=0.8)
ax.set_axisbelow(True)
ax.set_xlabel("η² (variance explained by color)", labelpad=8)
ax.set_ylabel("Permutation count", labelpad=8)
ax.set_title("Color's effect on card efficiency is real — but tiny",
             color=TEXT, fontsize=13, fontweight="bold", pad=12)
ax.legend(fontsize=9, frameon=False, labelcolor=TEXT_SECONDARY)

fig.tight_layout()
fig.savefig(OUT / "color_null_distribution.png", dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Saved: {OUT / 'color_null_distribution.png'}")

# ---------------------------------------------------------------------------
# Chart 2 — Per-color residual means (lollipop), Multicolor anomaly
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.5, 4.5), facecolor="white")
ax.set_facecolor("white")

colors_sorted = residual_means.index.tolist()
y_pos = range(len(colors_sorted))

for i, color_name in enumerate(colors_sorted):
    val = residual_means[color_name]
    is_highlight = color_name in ("Blue", "Multicolor")
    bar_color = ACCENT_DARK if is_highlight else ACCENT
    lw = 2.2 if is_highlight else 1.5

    # Stem
    ax.hlines(i, 0, val, color=bar_color, linewidth=lw, zorder=2)
    # Dot
    ax.scatter(val, i, color=bar_color, s=90, zorder=3, linewidth=0)
    # Zero line
    ax.axvline(0, color=BORDER, linewidth=1.0, zorder=1)

    # Value label
    offset = 0.003 if val >= 0 else -0.003
    ha = "left" if val >= 0 else "right"
    label_color = ACCENT_DARK if is_highlight else TEXT_SECONDARY
    ax.text(val + offset, i, f"{val:+.3f}",
            ha=ha, va="center", fontsize=9, color=label_color,
            fontweight="bold" if is_highlight else "normal")

ax.set_yticks(list(y_pos))
ax.set_yticklabels(colors_sorted, fontsize=10, color=TEXT_SECONDARY)
ax.set_xlabel("Mean efficiency residual (after removing CMC effect)", labelpad=8,
              color=TEXT_SECONDARY, fontsize=10)
ax.set_title("Multicolor cards punch above their mana cost — more than Blue does",
             color=TEXT, fontsize=13, fontweight="bold", pad=12)

for spine in ax.spines.values():
    spine.set_edgecolor(BORDER)
ax.tick_params(colors=TEXT_SECONDARY, labelsize=10)
ax.grid(axis="x", color=BORDER, linewidth=0.8)
ax.set_axisbelow(True)

# Annotation for Multicolor — anchored below and left to avoid Blue label
mc_val = residual_means["Multicolor"]
mc_idx = colors_sorted.index("Multicolor")
ax.annotate("More text justifies\nthe color requirement",
            xy=(mc_val, mc_idx),
            xytext=(0.045, mc_idx - 1.6),
            fontsize=8.5, color=TEXT_SECONDARY,
            arrowprops=dict(arrowstyle="-", color=BORDER, lw=1.2),
            ha="left", va="top")

fig.tight_layout()
fig.savefig(OUT / "color_residual_means.png", dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Saved: {OUT / 'color_residual_means.png'}")

# ---------------------------------------------------------------------------
# Chart 3 — Density curves: Blue vs others
# ---------------------------------------------------------------------------
# Show Blue + the two most different colors (Red = lowest, Multicolor = highest non-Blue)
SHOW_COLORS = ["Blue", "Red", "Multicolor"]

# MTG-adjacent colors that read well on white
CURVE_COLORS = {
    "Blue":       ACCENT_DARK,
    "Red":        "#E07060",
    "Multicolor": "#C9A227",
}

fig, ax = plt.subplots(figsize=(8.5, 4.5), facecolor="white")
ax.set_facecolor("white")

x_range = np.linspace(-1.8, 1.8, 500)

for color_name in SHOW_COLORS:
    sub = df[df["color"] == color_name]["residual"].values
    kde = gaussian_kde(sub, bw_method=0.25)
    density = kde(x_range)
    c = CURVE_COLORS[color_name]
    mean_val = sub.mean()

    ax.plot(x_range, density, color=c, linewidth=2.2, label=color_name)
    ax.fill_between(x_range, density, alpha=0.10, color=c)

    # Mean tick — stagger label heights to avoid overlap
    label_y_offsets = {"Blue": 0.22, "Red": 0.08, "Multicolor": 0.15}
    ax.axvline(mean_val, color=c, linewidth=1.2, linestyle="--", alpha=0.7)
    ax.text(mean_val, kde(np.array([mean_val]))[0] + label_y_offsets[color_name],
            f"μ={mean_val:+.3f}", fontsize=8, color=c, ha="center", va="bottom")

ax.axvline(0, color=BORDER, linewidth=1.0)
ax.set_xlabel("Efficiency residual (after removing CMC effect)", labelpad=8,
              color=TEXT_SECONDARY, fontsize=10)
ax.set_ylabel("Density", labelpad=8, color=TEXT_SECONDARY, fontsize=10)
ax.set_title("The distributions mostly overlap — the means are what differ",
             color=TEXT, fontsize=13, fontweight="bold", pad=12)

for spine in ax.spines.values():
    spine.set_edgecolor(BORDER)
ax.tick_params(colors=TEXT_SECONDARY, labelsize=10)
ax.grid(axis="y", color=BORDER, linewidth=0.8)
ax.set_axisbelow(True)
ax.set_xlim(-1.8, 1.8)

legend = ax.legend(fontsize=10, frameon=False, labelcolor=TEXT_SECONDARY)

fig.tight_layout()
fig.savefig(OUT / "color_density_curves.png", dpi=150, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Saved: {OUT / 'color_density_curves.png'}")
