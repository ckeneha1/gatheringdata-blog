"""
Post-rollout impact projection for the Elite cancellation threshold.

Shareable observed fact: after rollout, 1.5x as many Taskers met the Elite
cancellation-rate bar as before -> broad downward pressure on tasker-fault
cancellation.

This script projects the invoice-volume and revenue impact of that behavior
change, at $135 revenue per invoice. It is built on the synthetic US dataset for
scale, with an explicit, sensitivity-tested bridge from "1.5x compliance" to a
cancellation reduction.

Mechanism (the core identity):
    an avoided tasker-fault cancellation = a booking that now completes
    = +1 invoice = +$135 (x a completion haircut for residual fall-through).

    Delta revenue = (avoided cancellations) x completion x $135
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm

sns.set_theme(style="whitegrid")
BG = "#FFFCE4"                          # cream background to match the deck (was white)
plt.rcParams.update({"figure.facecolor": BG, "savefig.facecolor": BG,
                     "savefig.edgecolor": BG, "axes.facecolor": BG})
FIG = "analysis/taskrabbit-elite-criteria/figures"
PRICE = 135.0

df = pd.read_csv("analysis/taskrabbit-elite-criteria/taskers_clustered.csv")
us = df[df.region == "US"].copy()
us["rate"] = us.percent_of_bookings_tasker_canceled
us["m_bookings"] = us.booking_count / 3.0
us["m_cancels"] = us.monthly_times_tasker_canceled

# ---------------------------------------------------------------------------
# 1. Baseline scale (from data)
# ---------------------------------------------------------------------------
N = len(us)
m_cancels_all = us.m_cancels.sum()
m_invoices = us.monthly_invoice_count.sum()
a_cancels_all = m_cancels_all * 12
a_invoices = m_invoices * 12
a_revenue = a_invoices * PRICE

# Program-responsive supply = Taskers doing >= 2 jobs/month (the supply that
# actually chases Elite status). Casual <2/mo Taskers assumed unaffected.
RESP_MIN = 2.0
resp = us[us.m_bookings >= RESP_MIN]
resp_share = resp.m_cancels.sum() / m_cancels_all
a_cancels_resp = resp.m_cancels.sum() * 12

print("=" * 70)
print("BASELINE (synthetic US supply)")
print("=" * 70)
print(f"  Taskers:                    {N:,}")
print(f"  Annual invoices:            {a_invoices:,.0f}")
print(f"  Annual revenue @ ${PRICE:.0f}:      ${a_revenue/1e6:,.1f}M")
print(f"  Annual tasker-fault cancels:{a_cancels_all:,.0f}")
print(f"  ...in responsive supply (>= {RESP_MIN:.0f}/mo): {a_cancels_resp:,.0f} "
      f"({resp_share*100:.0f}% of cancels, N={len(resp):,})")
print(f"  Ceiling if 100% eliminated: ${a_cancels_all*PRICE/1e6:,.1f}M/yr")

# ---------------------------------------------------------------------------
# 2. Bridge: 1.5x compliance  ->  % reduction in cancellations
#    Lognormal cancel-rate model. If P(rate < bar) rises p0 -> 1.5*p0, the mean
#    cancellation rate (=> total cancellations) scales by exp(-sigma*(z1 - z0)).
# ---------------------------------------------------------------------------
pos = resp[resp.rate > 0]
sigma = float(np.log(pos.rate).std())
print("\n" + "=" * 70)
print("BRIDGE: 1.5x compliance -> cancellation reduction (lognormal, sigma=%.2f)" % sigma)
print("=" * 70)
print("  pre-rollout compliance p0 | post 1.5*p0 |  cancels x  | reduction")
bridge = {}
for p0 in [0.45, 0.50, 0.55, 0.60]:
    p1 = min(1.5 * p0, 0.999)
    ratio = float(np.exp(-sigma * (norm.ppf(p1) - norm.ppf(p0))))
    bridge[p0] = 1 - ratio
    print(f"        {p0:.2f}               {p1:.2f}         x{ratio:.3f}      {(1-ratio)*100:4.1f}%")
print("  -> central pre-rollout compliance ~0.52-0.55 => ~45% fewer cancellations")

# ---------------------------------------------------------------------------
# 3. Projection
# ---------------------------------------------------------------------------
def project(reduction, completion, base_cancels=a_cancels_resp):
    recovered_invoices = base_cancels * reduction * completion
    return recovered_invoices, recovered_invoices * PRICE

RED_C, COMP_C = 0.45, 0.85          # central
scenarios = {
    "Conservative": (0.35, 0.70),
    "Central":      (RED_C, COMP_C),
    "Optimistic":   (0.55, 1.00),
}
print("\n" + "=" * 70)
print("PROJECTED ANNUAL IMPACT (applied to responsive-supply cancellations)")
print("=" * 70)
rows = []
for name, (r, c) in scenarios.items():
    inv, rev = project(r, c)
    rows.append((name, r, c, inv, rev, inv / a_invoices * 100, rev / a_revenue * 100))
    print(f"  {name:12s}  reduction {r*100:.0f}%  completion {c:.2f}  ->  "
          f"+{inv:,.0f} invoices/yr  (+{inv/a_invoices*100:.1f}%)  |  "
          f"+${rev/1e6:.2f}M/yr  (+{rev/a_revenue*100:.1f}%)")

# ---------------------------------------------------------------------------
# 4. Sensitivity grid + scenario chart
# ---------------------------------------------------------------------------
reductions = np.array([0.30, 0.35, 0.40, 0.45, 0.50, 0.55])
completions = np.array([0.70, 0.85, 1.00])
grid = np.array([[project(r, c)[1] / 1e6 for c in completions] for r in reductions])

fig, ax = plt.subplots(figsize=(7.2, 5.0))
sns.heatmap(grid, annot=True, fmt=".2f", cmap="YlGn",
            xticklabels=[f"{c:.2f}" for c in completions],
            yticklabels=[f"{int(r*100)}%" for r in reductions],
            cbar_kws={"label": "Annual revenue impact ($M)"}, ax=ax)
ax.set_xlabel("Completion factor (avoided cancel -> paid invoice)")
ax.set_ylabel("Reduction in tasker-fault cancellations")
ax.set_title(r"Projected annual revenue impact (\$M) at \$135 / invoice",
             fontsize=12, fontweight="bold", loc="left")
# outline the central cell
ci, cj = list(reductions).index(RED_C), list(completions).index(COMP_C)
ax.add_patch(plt.Rectangle((cj, ci), 1, 1, fill=False, edgecolor="#b8003a", lw=3))
fig.tight_layout()
fig.savefig(f"{FIG}/fig_impact_sensitivity.png", dpi=130)
plt.close(fig)
print("\nsaved fig_impact_sensitivity.png")

# scenario bar (invoices + revenue)
fig, ax = plt.subplots(figsize=(7.6, 4.4))
names = [r[0] for r in rows]
revs = [r[4] / 1e6 for r in rows]
invs = [r[3] for r in rows]
colors = ["#9ecae1", "#238b45", "#a1d99b"]
bars = ax.bar(names, revs, color=colors, width=0.6)
for b, rev, inv in zip(bars, revs, invs):
    ax.text(b.get_x() + b.get_width()/2, rev + 0.05,
            f"${rev:.1f}M\n+{inv/1000:.0f}k invoices", ha="center", va="bottom",
            fontsize=10, fontweight="bold")
ax.set_ylabel("Annual revenue impact ($M)")
ax.set_ylim(0, max(revs) * 1.3)
ax.set_title("Elite cancellation threshold — projected annual impact (US supply)",
             fontsize=12, fontweight="bold", loc="left")
fig.tight_layout()
fig.savefig(f"{FIG}/fig_impact_scenarios.png", dpi=130)
plt.close(fig)
print("saved fig_impact_scenarios.png")

# ---------------------------------------------------------------------------
# 5. Save a tidy results table
# ---------------------------------------------------------------------------
out = pd.DataFrame(rows, columns=["scenario", "cancel_reduction", "completion",
                                  "recovered_invoices_yr", "revenue_impact_yr",
                                  "invoice_lift_pct", "revenue_lift_pct"])
out.to_csv("analysis/taskrabbit-elite-criteria/impact_results.csv", index=False)
print("wrote impact_results.csv")
