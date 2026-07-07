"""
Build the cohort / tier summary tables that close out the deck (slides 30, 35-37).

Cohort assignment comes from the cancel-floor k-means (floor_k4), relabelled:
  cohort 1 = top-volume + reliable   (floor cluster 0)
  cohort 2 = mid-volume + reliable   (floor cluster 1)
  cohort 3 = low-volume + reliable   (floor cluster 2)
  cohort 4 = unreliable / high-cancel(floor cluster 3)

Elite is the best-of-cohort-1 group. Per the deck (slide 28), how tight "best of
the best" is depends on how many clusters you carve -- so Elite is defined as the
tightest low-cancel / high-volume cluster from the k=15 pass, intersected with
cohort 1. We report it per region; it lands near the deck's ~3% of supply.
"""

import numpy as np
import pandas as pd

df = pd.read_csv("analysis/taskrabbit-elite-criteria/taskers_clustered.csv")

# floor_k4 was already relabelled 0..3 by ascending rolling invoices, BUT the
# high-cancel cluster can land anywhere; identify it as the max-cancel cluster.
cancel_by_cluster = df.groupby("floor_k4")["percent_of_bookings_tasker_canceled"].mean()
unreliable = cancel_by_cluster.idxmax()
reliable_order = [c for c in cancel_by_cluster.sort_index().index if c != unreliable]
# reliable clusters ordered by volume (ascending rolling invoices => cohort 1,2,3)
vol_order = (df[df.floor_k4.isin(reliable_order)]
             .groupby("floor_k4")["rolling_percent_total_invoices"].mean()
             .sort_values().index.tolist())
cohort_map = {vol_order[0]: 1, vol_order[1]: 2, vol_order[2]: 3, unreliable: 4}
df["cohort"] = df.floor_k4.map(cohort_map)

# Elite: tightest high-volume/low-cancel k=15 cluster, within cohort 1.
k15_stats = df.groupby("floor_k15").agg(
    roll=("rolling_percent_total_invoices", "mean"),
    cancel=("percent_of_bookings_tasker_canceled", "mean"),
)
elite_k15 = k15_stats.query("cancel < 0.10").sort_values("roll").index[0]
df["is_elite"] = (df.floor_k15 == elite_k15) & (df.cohort == 1)

WINDOW_MONTHS = 3.0


def tier_table(sub, region_name):
    rows = []
    total = len(sub)
    groups = [("Cohort 1 (Elite)", sub[sub.is_elite]),
              ("Cohort 1 (Total)", sub[sub.cohort == 1]),
              ("Cohort 2", sub[sub.cohort == 2]),
              ("Cohort 3", sub[sub.cohort == 3]),
              ("Cohort 4", sub[sub.cohort == 4])]
    for name, g in groups:
        rows.append({
            "tier": name,
            "tasker_count": len(g),
            "pct_of_supply": round(len(g) / total * 100, 1),
            "metros": g.metro_id.nunique(),
            "categories": g.category_id.nunique(),
            "monthly_revenue_usd": round(g.monthly_revenue_usd.mean(), 0),
            "monthly_invoices": round(g.monthly_invoice_count.mean(), 1),
            "monthly_cancels": round(g.monthly_times_tasker_canceled.mean(), 2),
            "cancel_pct": round(g.percent_of_bookings_tasker_canceled.mean() * 100, 1),
            "lifetime_invoices": round(g.lifetime_invoice_count.mean(), 0),
            "policy_points": round(g.policy_points_sum.mean(), 2),
        })
    t = pd.DataFrame(rows)
    print(f"\n================  {region_name} TASKER QUALITY TIERS  ================")
    print(t.to_string(index=False))
    return t


us_tbl = tier_table(df[df.region == "US"], "US")
global_tbl = tier_table(df, "GLOBAL (US + INTL)")

# Slide-30 style aggregate: per-cohort recommended-tasker count + per-tasker rates
slide30 = df.groupby("cohort").agg(
    recommended_tasker_count=("tasker_id", "nunique"),
    metros=("metro_id", "nunique"),
    categories=("category_id", "nunique"),
    monthly_invoice_count_per_tasker=("monthly_invoice_count", "mean"),
    times_tasker_canceled_per_tasker=("tasker_canceled_count", "mean"),
    monthly_times_tasker_canceled_per_tasker=("monthly_times_tasker_canceled", "mean"),
).round(4)
print("\n================  SLIDE 30 AGGREGATE (by cohort)  ================")
print(slide30.to_string())

us_tbl.to_csv("analysis/taskrabbit-elite-criteria/summary_us_tiers.csv", index=False)
global_tbl.to_csv("analysis/taskrabbit-elite-criteria/summary_global_tiers.csv", index=False)
slide30.to_csv("analysis/taskrabbit-elite-criteria/summary_slide30_aggregate.csv")
df.to_csv("analysis/taskrabbit-elite-criteria/taskers_clustered.csv", index=False)
print("\nWrote summary_us_tiers.csv, summary_global_tiers.csv, "
      "summary_slide30_aggregate.csv; updated taskers_clustered.csv (+cohort,+is_elite)")
