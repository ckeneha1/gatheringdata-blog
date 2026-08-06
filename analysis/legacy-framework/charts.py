"""Charts for the 'calling our shot' Legacy registered-prediction post.

Matches the blog aesthetic from prior posts (warm off-white #f8f7f4, monospace,
blue/rust accents). All data is the committed registered predictions + the Marvel
grade (see predictions/*.md); hardcoded here so the figures are self-contained.

  uv run --with matplotlib --with numpy python charts.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from datetime import date
from pathlib import Path

plt.rcParams.update({
    "figure.facecolor": "#f8f7f4", "axes.facecolor": "#f8f7f4",
    "axes.edgecolor": "#ccc8c0", "axes.labelcolor": "#444",
    "text.color": "#1a1a1a", "xtick.color": "#666", "ytick.color": "#666",
    "grid.color": "#e2ddd6", "font.family": "monospace",
    "axes.titlesize": 12.5, "axes.labelsize": 10, "xtick.labelsize": 9,
    "ytick.labelsize": 9, "legend.fontsize": 8.5,
    "legend.facecolor": "#f8f7f4", "legend.edgecolor": "#ccc8c0",
})
BG = "#f8f7f4"
ACCENT = "#3b82c4"      # blue  (positive / PLAYED / hit)
ACCENT2 = "#c45c3b"     # rust  (negative / wrong / miss)
LIGHT = "#b2d4e5"       # light blue (FRINGE)
NEUTRAL = "#cfcabf"     # muted (NOT PLAYED)
GREEN = "#5a9e6f"       # correct
AMBER = "#d9a441"       # partial
GRID = "#e2ddd6"

OUT = Path(__file__).resolve().parents[2] / "public" / "images" / "legacy-calling-our-shot"
OUT.mkdir(parents=True, exist_ok=True)


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print("wrote", name)


def no_spines(ax, keep=()):
    for s in ("top", "right", "left", "bottom"):
        if s not in keep:
            ax.spines[s].set_visible(False)


# ---------------------------------------------------------------------------
# 1) Signal priors — the framework's empirical prior (win log-OR by signal)
# ---------------------------------------------------------------------------
sig = [("lock_piece", 0.122), ("card_advantage", 0.081), ("cantrip", 0.078),
       ("mana_denial", 0.064), ("tempo", 0.064), ("tutor", 0.063),
       ("archetype_synergy", 0.054), ("protection", 0.050), ("resilience", 0.048),
       ("hate_piece", 0.027), ("mana_acceleration", 0.007), ("graveyard", -0.004),
       ("free_spell", -0.007), ("combo_piece", -0.040)]
sig = sig[::-1]
names = [s[0] for s in sig]
vals = [s[1] for s in sig]
fig, ax = plt.subplots(figsize=(8, 5), facecolor=BG)
ax.barh(names, vals, color=[ACCENT if v >= 0 else ACCENT2 for v in vals],
        edgecolor="#00000018", height=0.7)
ax.axvline(0, color="#888", lw=0.8)
ax.set_xlabel("mean within-format win log-OR  (87K Legacy decks, 2011–2026)")
ax.set_title("The framework's empirical prior: which signal types win",
             loc="left", pad=10)
ax.grid(axis="x", lw=0.5)
ax.set_axisbelow(True)
no_spines(ax)
save(fig, "signal_priors.png")


# ---------------------------------------------------------------------------
# 2) Marvel adoption reality — actual Legacy footprint of new Marvel cards
# ---------------------------------------------------------------------------
cards = [("The Fantasticar", 3.4, "hit"), ("Loki, God of Mischief", 0.8, "miss"),
         ("Mole Man", 0.1, "n"), ("King T'Challa", 0.1, "n"),
         ("Hawkeye, Master Marksman", 0.1, "n"), ("Namor the Sub-Mariner", 0.04, "n"),
         ("Hex / Avengers / Elektra / +", 0.02, "n")]
cards = cards[::-1]
nm = [c[0] for c in cards]
vv = [c[1] for c in cards]
cm = {"hit": ACCENT, "miss": ACCENT2, "n": NEUTRAL}
fig, ax = plt.subplots(figsize=(8.4, 4.6), facecolor=BG)
bars = ax.barh(nm, vv, color=[cm[c[2]] for c in cards], edgecolor="#00000018", height=0.72)
ax.axvline(1.0, color=AMBER, ls="--", lw=1.3)
ax.text(1.03, 0.15, "~PLAYED floor\n(≈1% of decks)", color="#b07d1f",
        fontsize=8, va="bottom")
for b, c in zip(bars, cards):
    ax.text(b.get_width() + 0.05, b.get_y() + b.get_height() / 2,
            f"{c[1]:.1f}%" if c[1] >= 0.1 else "~0%", va="center", fontsize=8.5, color="#444")
ax.text(0.35, 5.52, "Loki — played, yet on nobody's candidate list", color=ACCENT2,
        fontsize=8, va="center")
ax.set_xlim(0, 4.1)
ax.set_xlabel("share of 2026 Legacy decks playing the card  (new cards only, reprints excluded)")
ax.set_title("Marvel's real Legacy footprint: two new cards mattered", loc="left", pad=10)
ax.grid(axis="x", lw=0.5)
ax.set_axisbelow(True)
no_spines(ax)
save(fig, "marvel_adoption.png")


# ---------------------------------------------------------------------------
# Grid heatmap helper (predictors x cards)
# ---------------------------------------------------------------------------
def draw_grid(ax, cols, rows, cell_text, cell_color, title, col_note=None,
              highlight_cols=()):
    nC, nR = len(cols), len(rows)
    for j in range(nC):
        for i in range(nR):
            y = nR - 1 - i
            ax.add_patch(Rectangle((j, y), 1, 1, facecolor=cell_color[i][j],
                                   edgecolor=BG, lw=2))
            ax.text(j + 0.5, y + 0.5, cell_text[i][j], ha="center", va="center",
                    fontsize=10, fontweight="bold", color="#1a1a1a")
    for j in highlight_cols:
        ax.add_patch(Rectangle((j, 0), 1, nR, fill=False, edgecolor="#1a1a1a",
                               lw=1.6, zorder=5))
    ax.set_xlim(0, nC)
    ax.set_ylim(0, nR + 0.95)  # header band above the grid for title + note
    ax.set_xticks([j + 0.5 for j in range(nC)])
    ax.set_xticklabels(cols, rotation=40, ha="right", fontsize=8.5)
    ax.set_yticks([nR - 1 - i + 0.5 for i in range(nR)])
    ax.set_yticklabels(rows, fontsize=9.5)
    ax.tick_params(length=0)
    no_spines(ax)
    ax.text(0, nR + 0.58, title, fontsize=12.5, fontweight="bold", color="#1a1a1a", va="center")
    if col_note:
        ax.text(0, nR + 0.22, col_note, fontsize=8.5, color="#555", style="italic", va="center")


# ---------------------------------------------------------------------------
# 3) Marvel scorecard — predicted vs actual, colored by correctness
# ---------------------------------------------------------------------------
P, F, N, DASH = "P", "F", "N", "–"
mcols = ["Fantasticar", "Loki*", "Mole Man", "Namor", "Hawkeye's Bow", "Thanos",
         "Hex Magic", "Avengers", "Elektra", "Jennifer W."]
actual = [P, P, N, N, N, N, N, N, N, N]  # Loki actual PLAYED (but unlisted)
rows = ["Baseline", "Framework", "Community", "Model"]
pred = {
    "Baseline":  [F, DASH, N, F, P, P, N, N, N, N],
    "Framework": [F, DASH, P, F, N, N, N, N, N, F],
    "Community": [P, DASH, F, P, N, N, N, N, N, N],
    "Model":     [P, DASH, P, F, N, N, P, P, P, P],
}


def score_color(p, a):
    if p == DASH:
        return ACCENT2  # missed (Loki: unlisted but played)
    if a == P:
        return {P: GREEN, F: AMBER, N: ACCENT2}[p]
    return {N: GREEN, F: AMBER, P: ACCENT2}[p]  # a == N


text = [[pred[r][j] for j in range(len(mcols))] for r in rows]
color = [[score_color(pred[r][j], actual[j]) for j in range(len(mcols))] for r in rows]
fig, ax = plt.subplots(figsize=(9.5, 4.2), facecolor=BG)
draw_grid(ax, mcols, rows, text, color,
          "Marvel scorecard: who called what  (green=right, amber=half, red=wrong/missed)",
          col_note="Actual: Fantasticar & Loki PLAYED; all others NOT PLAYED. "
                   "*Loki was on no predictor's list.", highlight_cols=[0, 1])
save(fig, "marvel_scorecard.png")


# ---------------------------------------------------------------------------
# 4) The Hobbit call-your-shot — predicted verdicts (no outcome yet)
# ---------------------------------------------------------------------------
hcols = ["Riddles\nin the Dark", "Bilbo,\nThief", "Gandalf,\nGoblins'", "Gollum,\nRiddle M.",
         "An Unexpected\nParty", "Plunder\nTrollshaws", "Confusticate", "My Precious\n//Allure",
         "Most Decrepit\nBird", "Bilbo's\nDeadly Slice"]
hrows = ["Baseline", "Framework", "Community", "Model"]
hpred = {
    "Baseline":  [N, F, N, N, N, F, N, N, P, N],
    "Framework": [F, N, N, N, N, N, N, N, N, N],
    "Community": [F, P, F, F, F, N, N, N, N, N],
    "Model":     [P, P, N, N, N, F, N, F, F, N],
}
level = {P: ACCENT, F: LIGHT, N: NEUTRAL, DASH: NEUTRAL}
htext = [[hpred[r][j] for j in range(len(hcols))] for r in hrows]
hcolor = [[level[hpred[r][j]] for j in range(len(hcols))] for r in hrows]
fig, ax = plt.subplots(figsize=(11, 4.2), facecolor=BG)
draw_grid(ax, hcols, hrows, htext, hcolor,
          "The shot: The Hobbit predictions, locked pre-release",
          col_note="No outcomes yet — graded 2026-10-02. Boxed = the sharpest disagreements.",
          highlight_cols=[0, 1])
leg = [Line2D([0], [0], marker="s", color="none", markerfacecolor=ACCENT, markersize=11, label="PLAYED"),
       Line2D([0], [0], marker="s", color="none", markerfacecolor=LIGHT, markersize=11, label="FRINGE"),
       Line2D([0], [0], marker="s", color="none", markerfacecolor=NEUTRAL, markersize=11, label="NOT PLAYED")]
ax.legend(handles=leg, loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=3, frameon=False)
save(fig, "hobbit_predictions.png")


# ---------------------------------------------------------------------------
# 5) Timeline — lock -> release -> grade, both sets
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9.5, 3.4), facecolor=BG)
lanes = [
    ("Marvel Super Heroes", 1, ACCENT, [
        (date(2026, 6, 22), "lock", "o"), (date(2026, 6, 26), "release", "s"),
        (date(2026, 8, 3), "prelim grade", "^"), (date(2026, 8, 15), "formal grade", "*")]),
    ("The Hobbit", 0, ACCENT2, [
        (date(2026, 8, 4), "lock", "o"), (date(2026, 8, 14), "release", "s"),
        (date(2026, 10, 2), "grade", "*")]),
]
for label, y, col, pts in lanes:
    xs = [d for d, _, _ in pts]
    ax.plot(xs, [y] * len(xs), color=col, lw=1.4, zorder=1, alpha=0.6)
    for d, lbl, mk in pts:
        ax.scatter([d], [y], s=130 if mk == "*" else 70, marker=mk, color=col,
                   zorder=3, edgecolor=BG, lw=1)
        va, dy = ("bottom", 0.09) if lbl in ("lock", "prelim grade", "grade") else ("top", -0.09)
        ax.annotate(f"{lbl}\n{d:%b %d}", (d, y), xytext=(0, dy * 100), textcoords="offset points",
                    ha="center", va=va, fontsize=7.6, color="#444")
    ax.text(date(2026, 6, 16), y, label, ha="right", va="center", fontsize=9.5,
            fontweight="bold", color=col)
today = date(2026, 8, 6)
ax.axvline(today, color="#888", ls=":", lw=1.1)
ax.text(today, 1.6, " today", fontsize=8, color="#666")
ax.set_ylim(-0.6, 1.75)
ax.set_xlim(date(2026, 5, 20), date(2026, 10, 18))
ax.set_yticks([])
no_spines(ax, keep=("bottom",))
ax.set_title("Timeline: when we find out if the shots landed", loc="left", pad=10)
ax.grid(axis="x", lw=0.5)
ax.set_axisbelow(True)
save(fig, "timeline.png")

print("done ->", OUT)
