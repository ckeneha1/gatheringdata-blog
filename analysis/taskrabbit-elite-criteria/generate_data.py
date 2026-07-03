"""
Mock Tasker supply dataset for the "Elite Metric Regroup" methodology deck.

This is SYNTHETIC data. It contains no real Taskrabbit data. It is engineered to
reproduce the *shapes* and the *analytical story* of slides 12-34 of the deck so
the methodology can be presented without using company data.

The unit of analysis is a Tasker WITHIN a metro-category (metcat). Every "rolling"
metric is computed within the Tasker's own metcat, because the whole point of the
exercise is to compare a Tasker to their local peers (slide 9).

Key engineered properties (so the downstream clustering story lands):
  * Volume per metcat is heavy-tailed  -> the cumulative "comet/tadpole" shape.
  * Close rate and cancel rate come from BINOMIAL draws on a Tasker's booking
    count -> low-volume Taskers show the discrete horizontal lines at y = 1, 1/2,
    1/3 ... and the cancel-rate "funnel" that widens at low volume.
  * rolling_revenue is strongly (but not perfectly) correlated with rolling_invoices
    -> the left-light / right-dark hue gradient on slides 12-15.
  * Tasker-fault cancels are a genuinely separate axis from volume -> naive k-means
    over {close_rate, rolling_inv, rolling_rev} collapses to vertical stripes
    (cohort too large), but adding the cancel "floor" unlocks a 2-D
    volume x reliability structure.

Outputs:
  taskers.csv          one row per Tasker-metcat, all raw + derived + cluster fields
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(20240619)  # deterministic; nods to the deck's lock date

# ----------------------------------------------------------------------------
# 1. Population frame: how many Taskers, in how many metro-categories, per region
# ----------------------------------------------------------------------------
# US tier table totals (slide 35): 6431 + 13701 + 33857 + 4582 = 58,571
# Global tier table totals (slide 36): 8713 + 17764 + 44872 + 6469 = 77,818
# Global is a superset of US; rest-of-world = 77,818 - 58,571 = 19,247.
TARGET = {
    "US":   {"n_taskers": 58_571, "n_metros": 61,  "n_categories": 54},
    "INTL": {"n_taskers": 19_247, "n_metros": 174, "n_categories": 55},
}


def build_metcats(n_taskers, n_metros, n_categories, metro_offset, region, rng):
    """Allocate Taskers into metro-category cells with heavy-tailed cell sizes.

    Not every (metro, category) pair is active. Cell sizes are lognormal so a few
    big-city / popular-category cells hold hundreds of Taskers while niche cells
    hold a handful -- this dispersion is what makes the within-cell cumulative
    curves look like the deck.
    """
    rows = []
    assigned = 0
    # Candidate cells: sample (metro, category) pairs without replacement-ish.
    # Popularity weights make some metros/categories much denser than others.
    metro_pop = rng.pareto(1.6, n_metros) + 0.3
    cat_pop = rng.pareto(1.6, n_categories) + 0.3
    metro_pop /= metro_pop.sum()
    cat_pop /= cat_pop.sum()

    # Build a pool of active cells (roughly: a Tasker-rich region populates more cells)
    target_cells = max(1, int(n_taskers / 26))  # avg ~26 Taskers per active metcat
    cell_set = set()
    guard = 0
    while len(cell_set) < target_cells and guard < target_cells * 20:
        m = rng.choice(n_metros, p=metro_pop)
        c = rng.choice(n_categories, p=cat_pop)
        cell_set.add((int(m), int(c)))
        guard += 1
    cells = list(cell_set)

    # Heavy-tailed size per cell, then rescale so sizes sum to n_taskers.
    raw_sizes = rng.lognormal(mean=2.7, sigma=0.9, size=len(cells)) + 3
    raw_sizes = raw_sizes / raw_sizes.sum() * n_taskers
    sizes = np.maximum(3, np.round(raw_sizes).astype(int))

    # Trim/pad to hit the target exactly.
    diff = n_taskers - sizes.sum()
    if diff != 0:
        # adjust the largest cells to absorb the rounding difference
        order = np.argsort(sizes)[::-1]
        i = 0
        step = 1 if diff > 0 else -1
        while diff != 0:
            idx = order[i % len(order)]
            if sizes[idx] + step >= 3:
                sizes[idx] += step
                diff -= step
            i += 1

    for (m, c), size in zip(cells, sizes):
        for _ in range(int(size)):
            rows.append((region, m + metro_offset, c))
        assigned += size

    df = pd.DataFrame(rows, columns=["region", "metro_id", "category_id"])
    return df


frames = []
frames.append(build_metcats(**{k: TARGET["US"][k] for k in
                               ("n_taskers", "n_metros", "n_categories")},
                            metro_offset=0, region="US", rng=RNG))
frames.append(build_metcats(**{k: TARGET["INTL"][k] for k in
                               ("n_taskers", "n_metros", "n_categories")},
                            metro_offset=1000, region="INTL", rng=RNG))
df = pd.concat(frames, ignore_index=True)
n = len(df)
print(f"Total Taskers: {n:,}  (US {(df.region=='US').sum():,} / "
      f"INTL {(df.region=='INTL').sum():,})")

# ----------------------------------------------------------------------------
# 2. Per-Tasker latent quality + activity over a 90-day (3-month) window
# ----------------------------------------------------------------------------
# Each Tasker has a latent "engagement" that drives booking volume (heavy-tailed),
# a latent close-propensity, and a latent cancel-propensity. Good Taskers tend to
# be high-volume + high-close + low-cancel, but the correlations are loose so the
# axes don't collapse into one another.
latent = RNG.normal(0, 1, n)                      # general "good Tasker" factor

# --- Booking volume over 90 days: heavy-tailed, lifted by latent quality ---
# Median ~exp(2.15)=8.6 bookings/90d; the top few percent reach 60-120, which is
# what lets the elite cohort hit ~12 monthly invoices. Higher volumes also mean
# close/cancel rates come from larger binomial denominators -> softer discreteness.
log_bookings = 1.00 * latent + RNG.normal(1.22, 0.95, n)
booking_count = np.maximum(1, np.round(np.exp(log_bookings)).astype(int))
# clip a sensible ceiling so a single Tasker doesn't dominate a metcat absurdly
booking_count = np.minimum(booking_count, 400)

# --- Close rate: Beta mean ~0.66, nudged up by latent quality. Binomial draw on
#     bookings makes low-volume Taskers land on discrete fractions / 1.0 ---
close_mu = 1 / (1 + np.exp(-(0.45 * latent + 0.55)))   # logistic, mean ~0.63
close_kappa = 14.0                                      # concentration
a = close_mu * close_kappa
b = (1 - close_mu) * close_kappa
close_true = RNG.beta(a, b)
invoice_count = RNG.binomial(booking_count, close_true)
percent_of_bookings_invoiced = invoice_count / booking_count

# --- Tasker-fault cancel rate: low mean (~0.05), HIGHER for low-quality Taskers,
#     binomial draw -> discrete lines + funnel that widens at low volume ---
cancel_mu = 1 / (1 + np.exp(-(-0.8 * latent - 2.7)))   # logistic, mean ~0.06
cancel_kappa = 9.0
ca = cancel_mu * cancel_kappa
cb = (1 - cancel_mu) * cancel_kappa
cancel_true = RNG.beta(ca, cb)
tasker_canceled_count = RNG.binomial(booking_count, cancel_true)
percent_of_bookings_tasker_canceled = tasker_canceled_count / booking_count

# --- Revenue: per-invoice price is lognormal, loosely lifted by quality, so
#     revenue correlates with volume but adds an independent wrinkle ---
avg_price_usd = np.exp(RNG.normal(3.5, 0.45, n) + 0.10 * latent)   # ~$33 median
avg_price_usd = np.clip(avg_price_usd, 8, 400)
revenue_cents = np.round(invoice_count * avg_price_usd * 100).astype(np.int64)

# --- Policy points (slide 4 / 45): mostly low, fatter tail for low-quality ---
policy_points_sum = RNG.poisson(np.maximum(0.05, 1.6 - 0.7 * latent))

# --- Lifetime invoices (slide 42/45): the 90-day count plus accumulated history ---
tenure_months = np.maximum(1, np.round(np.exp(RNG.normal(2.6, 0.7, n))).astype(int))
lifetime_invoice_count = invoice_count + RNG.poisson(
    np.maximum(0.0, invoice_count / 3.0) * tenure_months)

df = df.assign(
    booking_count=booking_count,
    invoice_count=invoice_count,
    tasker_canceled_count=tasker_canceled_count,
    revenue_cents=revenue_cents,
    avg_price_usd=np.round(avg_price_usd, 2),
    percent_of_bookings_invoiced=percent_of_bookings_invoiced,
    percent_of_bookings_tasker_canceled=percent_of_bookings_tasker_canceled,
    policy_points_sum=policy_points_sum,
    lifetime_invoice_count=lifetime_invoice_count,
    tenure_months=tenure_months,
)

# ----------------------------------------------------------------------------
# 3. Within-metcat rolling cumulative metrics  (the comet's x-axis & hue)
# ----------------------------------------------------------------------------
# For each metro-category: rank Taskers by contribution DESCENDING, take the
# running cumulative share (0-100). Top contributors -> low values; the long tail
# of marginal Taskers piles up near 100. This is exactly the slide-10 table logic.
def rolling_cum_pct(group_values):
    order = np.argsort(group_values)[::-1]          # largest first
    cum = np.cumsum(group_values[order])
    total = cum[-1] if cum[-1] > 0 else 1
    rolling_sorted = cum / total * 100.0
    out = np.empty_like(rolling_sorted)
    out[order] = rolling_sorted
    return out


df["metcat"] = df["region"] + "_" + df["metro_id"].astype(str) + "_" + df["category_id"].astype(str)

for src, dst in [("invoice_count", "rolling_percent_total_invoices"),
                 ("revenue_cents", "rolling_percent_total_revenue_cents")]:
    vals = df[src].to_numpy(dtype=float)
    out = np.empty(len(df))
    for _, idx in df.groupby("metcat").indices.items():
        idx = np.asarray(idx)
        out[idx] = rolling_cum_pct(vals[idx])
    df[dst] = out

df = df.reset_index(drop=True)
df.insert(0, "tasker_id", np.arange(1, len(df) + 1))

# ----------------------------------------------------------------------------
# 4. Monthly normalizations (slide 30/32 footnote: per-Tasker, per-month)
# ----------------------------------------------------------------------------
WINDOW_MONTHS = 3.0
df["monthly_invoice_count"] = df["invoice_count"] / WINDOW_MONTHS
df["monthly_revenue_usd"] = df["revenue_cents"] / 100.0 / WINDOW_MONTHS
df["monthly_times_tasker_canceled"] = df["tasker_canceled_count"] / WINDOW_MONTHS

out_path = "analysis/taskrabbit-elite-criteria/taskers.csv"
df.to_csv(out_path, index=False)
print(f"Wrote {out_path}  ({len(df):,} rows, {df.shape[1]} cols)")
print("\nColumns:", list(df.columns))
print("\nSanity (US):")
us = df[df.region == "US"]
print("  median close rate      ", round(us.percent_of_bookings_invoiced.median(), 3))
print("  median cancel rate     ", round(us.percent_of_bookings_tasker_canceled.median(), 3))
print("  mean monthly invoices  ", round(us.monthly_invoice_count.mean(), 2))
print("  mean monthly revenue $ ", round(us.monthly_revenue_usd.mean(), 2))
print("  metcats (US)           ", us.metcat.nunique())
