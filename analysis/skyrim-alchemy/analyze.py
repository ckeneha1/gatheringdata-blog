"""
analyze.py — LP model + charts for the Skyrim Alchemy Optimizer blog post.

Reads:
    data/ingredients.json
    data/potions.json
    data/build_profiles.json

Outputs:
    ../../public/images/skyrim-alchemy/*.png (5 charts)
    results.json (LP results for all builds, referenced by the React component)

Usage:
    uv run python analyze.py                 # all builds, default 20-hr budget
    uv run python analyze.py --build "Stealth Archer" --budget 15
"""

from __future__ import annotations
import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy.optimize import linprog

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR   = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "public" / "images" / "skyrim-alchemy"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Blog chart style (matches mtg-distributions/analyze.py)
# ---------------------------------------------------------------------------

ACCENT      = "#b2d4e5"
ACCENT_DARK = "#7aafc9"
TEXT        = "#363737"
TEXT_SEC    = "#868787"
BORDER      = "#dddddd"

BUILD_COLORS = {
    "Heavy Armor Warrior": "#c8906a",
    "Stealth Archer":      "#7ab87a",
    "Pure Mage":           "#7aafc9",
    "Illusion Assassin":   "#9a8fa0",
    "Paladin":             "#e8d080",
    "Necromancer":         "#a07878",
}


def apply_blog_style(ax, title=None, xlabel=None, ylabel=None):
    ax.set_facecolor("white")
    ax.figure.set_facecolor("white")
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    ax.tick_params(colors=TEXT_SEC, labelsize=9)
    ax.xaxis.label.set_color(TEXT_SEC)
    ax.yaxis.label.set_color(TEXT_SEC)
    if title:
        ax.set_title(title, color=TEXT, fontsize=12, fontweight="bold", pad=10)
    if xlabel:
        ax.set_xlabel(xlabel, labelpad=6)
    if ylabel:
        ax.set_ylabel(ylabel, labelpad=6)
    ax.grid(axis="y", color=BORDER, linewidth=0.7, linestyle="-")
    ax.set_axisbelow(True)


def save(fig, filename: str):
    path = OUTPUT_DIR / filename
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"  Saved {path}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data():
    with open(DATA_DIR / "ingredients.json") as f:
        ingredients = json.load(f)
    with open(DATA_DIR / "potions.json") as f:
        potions_raw = json.load(f)
    with open(DATA_DIR / "build_profiles.json") as f:
        build_profiles = json.load(f)
    return ingredients, potions_raw, build_profiles


def select_canonical_pairs(potions_raw: list[dict], ing_yields: dict[str, dict[str, float]]) -> list[dict]:
    """
    For each unique potion name, select the single ingredient pair with the highest
    combined total yield across all regions. This gives the "most obtainable" pair
    and keeps the LP tractable (one recipe per potion).
    """
    from collections import defaultdict

    def pair_total_yield(ing1: str, ing2: str) -> float:
        y1 = sum(ing_yields.get(ing1, {}).values())
        y2 = sum(ing_yields.get(ing2, {}).values())
        return y1 + y2

    # Group by potion name
    by_potion: dict[str, list] = defaultdict(list)
    for p in potions_raw:
        by_potion[p["name"]].append(p)

    canonical = []
    for potion_name, pairs in sorted(by_potion.items()):
        # Filter to pairs where both ingredients have yield data
        valid_pairs = [
            p for p in pairs
            if p["ingredients"][0] in ing_yields and p["ingredients"][1] in ing_yields
        ]
        if not valid_pairs:
            continue
        best = max(valid_pairs, key=lambda p: pair_total_yield(*p["ingredients"]))
        canonical.append(best)

    return canonical


# ---------------------------------------------------------------------------
# LP Model
# ---------------------------------------------------------------------------

@dataclass
class LPResult:
    build_name:       str
    time_budget:      float
    region_hours:     dict[str, float]
    potion_batches:   dict[str, float]
    ingredient_totals: dict[str, float]
    objective_value:  float
    status:           str
    shadow_price_time: float = 0.0
    regions:          list[str] = field(default_factory=list)
    potions:          list[str] = field(default_factory=list)


def build_and_solve(
    build_name: str,
    weights: dict[str, float],
    canonical_potions: list[dict],
    ing_yields: dict[str, dict[str, float]],
    regions: list[str],
    time_budget: float = 20.0,
) -> LPResult:
    """
    LP formulation:
    Variables: x[r] = hours in region r (R regions)
               z[p] = batches of potion p (P potions)
    Objective: maximize Σ_p w_p * z_p
    Constraints:
      Σ_r x_r <= T                          (time budget)
      z_p <= Σ_r x_r * yield[r][i]          ∀ p, ∀ ingredient i in recipe[p]
      x_r >= 0, z_p >= 0
    """
    R = len(regions)

    # Only include potions that have a non-zero weight for this build
    active_potions = [p for p in canonical_potions if weights.get(p["name"], 0.0) > 0]
    P = len(active_potions)

    if P == 0:
        return LPResult(
            build_name=build_name, time_budget=time_budget,
            region_hours={}, potion_batches={}, ingredient_totals={},
            objective_value=0.0, status="No active potions", regions=regions, potions=[],
        )

    # Variable order: [x_0, ..., x_{R-1}, z_0, ..., z_{P-1}]
    n_vars = R + P

    # Objective: minimize -Σ w_p * z_p (linprog minimizes)
    c = np.zeros(n_vars)
    for j, p in enumerate(active_potions):
        c[R + j] = -weights.get(p["name"], 0.0)

    # Inequality constraints: A_ub @ v <= b_ub
    rows_A: list[np.ndarray] = []
    rows_b: list[float] = []

    # 1) Time budget: Σ x_r <= T
    row = np.zeros(n_vars)
    row[:R] = 1.0
    rows_A.append(row)
    rows_b.append(time_budget)

    # 2) Supply constraints: z_p <= Σ_r x_r * yield[r][i]  for each ingredient i in recipe[p]
    #    Rewritten: z_p - Σ_r x_r * yield[r][i] <= 0
    for j, potion in enumerate(active_potions):
        for ing_name in potion["ingredients"]:
            if ing_name not in ing_yields:
                continue
            row = np.zeros(n_vars)
            row[R + j] = 1.0  # z_p coefficient
            for r_idx, region in enumerate(regions):
                row[r_idx] = -ing_yields[ing_name].get(region, 0.0)  # -yield[r][i]
            rows_A.append(row)
            rows_b.append(0.0)

    A_ub = np.array(rows_A)
    b_ub = np.array(rows_b)

    # Bounds: all variables >= 0
    bounds = [(0.0, None)] * n_vars

    result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")

    if result.status != 0:
        return LPResult(
            build_name=build_name, time_budget=time_budget,
            region_hours={}, potion_batches={}, ingredient_totals={},
            objective_value=0.0, status=f"Infeasible: {result.message}",
            regions=regions, potions=[p["name"] for p in active_potions],
        )

    x = result.x
    region_hours  = {regions[r]: round(x[r], 4) for r in range(R)}
    potion_batches = {active_potions[j]["name"]: round(x[R + j], 4) for j in range(P)}

    # Compute ingredient totals
    ingredient_totals: dict[str, float] = {}
    for ing_name, yields in ing_yields.items():
        total = sum(region_hours.get(region, 0.0) * yields.get(region, 0.0) for region in regions)
        if total > 1e-6:
            ingredient_totals[ing_name] = round(total, 4)

    # Shadow price on time budget constraint (dual variable for constraint 0)
    shadow_price_time = 0.0
    if hasattr(result, "ineqlin") and result.ineqlin is not None:
        shadow_price_time = abs(float(result.ineqlin.marginals[0]))

    return LPResult(
        build_name=build_name,
        time_budget=time_budget,
        region_hours=region_hours,
        potion_batches=potion_batches,
        ingredient_totals=ingredient_totals,
        objective_value=round(-result.fun, 4),
        status="Optimal",
        shadow_price_time=round(shadow_price_time, 4),
        regions=regions,
        potions=[p["name"] for p in active_potions],
    )


# ---------------------------------------------------------------------------
# Chart 1: Region allocation bar chart (grouped by build)
# ---------------------------------------------------------------------------

def chart_region_allocation(results: list[LPResult]):
    """Grouped bar chart: hours per region, one group per region, one bar per build."""
    regions = results[0].regions
    builds  = [r.build_name for r in results]
    n_builds = len(builds)
    n_regions = len(regions)

    x = np.arange(n_regions)
    width = 0.8 / n_builds

    fig, ax = plt.subplots(figsize=(11, 5))

    for i, res in enumerate(results):
        hours = [res.region_hours.get(region, 0.0) for region in regions]
        offset = (i - n_builds / 2 + 0.5) * width
        color = BUILD_COLORS.get(res.build_name, ACCENT)
        ax.bar(x + offset, hours, width, label=res.build_name, color=color, alpha=0.85)

    # Short region labels
    short_labels = [r.split(" (")[0] for r in regions]
    ax.set_xticks(x)
    ax.set_xticklabels(short_labels, rotation=20, ha="right")

    apply_blog_style(
        ax,
        title=f"Optimal foraging time by region ({results[0].time_budget:.0f}-hour budget)",
        xlabel="Region",
        ylabel="Hours allocated",
    )
    ax.legend(fontsize=8, frameon=False, loc="upper right")

    save(fig, "region_allocation.png")


# ---------------------------------------------------------------------------
# Chart 2: Sensitivity curve (objective vs time budget)
# ---------------------------------------------------------------------------

def chart_sensitivity(
    builds_to_plot: list[str],
    weights_by_build: dict[str, dict[str, float]],
    canonical_potions: list[dict],
    ing_yields: dict[str, dict[str, float]],
    regions: list[str],
    budgets: list[float],
):
    """Line chart: weighted potion output vs. time budget for 3 builds."""
    fig, ax = plt.subplots(figsize=(9, 5))

    for build_name in builds_to_plot:
        weights = weights_by_build[build_name]
        objs = []
        for t in budgets:
            res = build_and_solve(build_name, weights, canonical_potions, ing_yields, regions, t)
            objs.append(res.objective_value)
        color = BUILD_COLORS.get(build_name, ACCENT)
        ax.plot(budgets, objs, "-o", color=color, label=build_name, linewidth=2, markersize=5)

    apply_blog_style(
        ax,
        title="Weighted potion output vs. foraging budget",
        xlabel="Hours available",
        ylabel="Weighted objective (Σ weight × batches)",
    )
    ax.legend(fontsize=9, frameon=False)

    save(fig, "sensitivity_curve.png")


# ---------------------------------------------------------------------------
# Chart 3: Single-region counterfactual
# ---------------------------------------------------------------------------

def chart_single_region_counterfactual(
    build_name: str,
    weights: dict[str, float],
    canonical_potions: list[dict],
    ing_yields: dict[str, dict[str, float]],
    regions: list[str],
    time_budget: float = 20.0,
):
    """Bar chart: what you'd get if forced to forage in only one region."""
    objectives = {}
    for region in regions:
        forced_yields = {
            ing: {r: (v if r == region else 0.0) for r, v in yields.items()}
            for ing, yields in ing_yields.items()
        }
        res = build_and_solve(build_name, weights, canonical_potions, forced_yields, regions, time_budget)
        objectives[region] = res.objective_value

    # Sort descending
    sorted_regions = sorted(objectives, key=objectives.get, reverse=True)
    values = [objectives[r] for r in sorted_regions]
    short_labels = [r.split(" (")[0] for r in sorted_regions]

    fig, ax = plt.subplots(figsize=(8, 4))
    colors = [ACCENT_DARK if i == 0 else ACCENT for i in range(len(sorted_regions))]
    ax.barh(short_labels[::-1], values[::-1], color=colors[::-1], height=0.6)

    apply_blog_style(
        ax,
        title=f"{build_name}: if you could only forage in one region",
        xlabel=f"Weighted objective ({time_budget:.0f}-hr budget)",
    )
    ax.grid(axis="x", color=BORDER, linewidth=0.7)
    ax.grid(axis="y", visible=False)

    save(fig, f"single_region_{build_name.lower().replace(' ', '_')}.png")
    return objectives


# ---------------------------------------------------------------------------
# Chart 4: Ingredient yield heatmap
# ---------------------------------------------------------------------------

def chart_yield_heatmap(ing_yields: dict[str, dict[str, float]], regions: list[str], top_n: int = 20):
    """Heatmap: regions × top-N ingredients by total yield."""
    # Rank ingredients by total yield across all regions
    totals = {ing: sum(yields.values()) for ing, yields in ing_yields.items()}
    top_ings = sorted(totals, key=totals.get, reverse=True)[:top_n]

    # Build matrix
    matrix = np.array([[ing_yields[ing].get(r, 0.0) for r in regions] for ing in top_ings])

    short_regions = [r.split(" (")[0] for r in regions]
    short_ings = [i[:28] for i in top_ings]  # truncate long names

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(matrix, aspect="auto", cmap="Blues", vmin=0)

    ax.set_xticks(range(len(regions)))
    ax.set_xticklabels(short_regions, rotation=30, ha="right", fontsize=8, color=TEXT_SEC)
    ax.set_yticks(range(top_n))
    ax.set_yticklabels(short_ings, fontsize=8, color=TEXT_SEC)

    ax.set_facecolor("white")
    ax.figure.set_facecolor("white")
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)

    cbar = fig.colorbar(im, ax=ax, shrink=0.6)
    cbar.set_label("Yield rate (units/hr, relative)", color=TEXT_SEC, fontsize=9)
    cbar.ax.tick_params(colors=TEXT_SEC, labelsize=8)

    ax.set_title("Ingredient yield rates by region (top 20 by total yield)",
                 color=TEXT, fontsize=12, fontweight="bold", pad=10)
    fig.tight_layout()

    save(fig, "ingredient_heatmap.png")


# ---------------------------------------------------------------------------
# Chart 5: Potion output comparison (3 builds side-by-side)
# ---------------------------------------------------------------------------

def chart_potion_comparison(results: list[LPResult]):
    """Horizontal bar chart comparing potion batches for 3 builds at 20 hrs."""
    # Get all potions any build produces (> 0.1 batches)
    all_potions: set[str] = set()
    for res in results:
        for p, v in res.potion_batches.items():
            if v > 0.1:
                all_potions.add(p)
    potions = sorted(all_potions)

    if not potions:
        print("  No potions to chart in comparison")
        return

    n_p = len(potions)
    n_b = len(results)
    y = np.arange(n_p)
    height = 0.75 / n_b

    fig, ax = plt.subplots(figsize=(10, max(5, 0.4 * n_p)))

    for i, res in enumerate(results):
        vals = [res.potion_batches.get(p, 0.0) for p in potions]
        offset = (i - n_b / 2 + 0.5) * height
        color = BUILD_COLORS.get(res.build_name, ACCENT)
        ax.barh(y + offset, vals, height, label=res.build_name, color=color, alpha=0.85)

    ax.set_yticks(y)
    ax.set_yticklabels(potions, fontsize=8)

    apply_blog_style(
        ax,
        title=f"Craftable potion batches by build ({results[0].time_budget:.0f}-hr budget)",
        xlabel="Batches craftable",
    )
    ax.grid(axis="x", color=BORDER, linewidth=0.7)
    ax.grid(axis="y", visible=False)
    ax.legend(fontsize=8, frameon=False, loc="lower right")

    save(fig, "potion_comparison.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", help="Run only this build")
    parser.add_argument("--budget", type=float, default=20.0, help="Time budget in hours")
    parser.add_argument("--no-charts", action="store_true", help="Skip chart generation")
    args = parser.parse_args()

    ingredients, potions_raw, build_profiles = load_data()

    # Index ingredient yields
    ing_yields = {ing["name"]: ing["region_yields"] for ing in ingredients}
    regions    = sorted(next(iter(ing_yields.values())).keys())

    print(f"Loaded {len(ingredients)} ingredients, {len(potions_raw)} potion combinations")
    print(f"Selecting canonical ingredient pair per potion...")
    canonical_potions = select_canonical_pairs(potions_raw, ing_yields)
    print(f"  {len(canonical_potions)} canonical potion recipes")

    # Builds to run
    if args.build:
        if args.build not in build_profiles:
            print(f"Unknown build '{args.build}'. Available: {list(build_profiles)}")
            return
        builds_to_run = [args.build]
    else:
        builds_to_run = list(build_profiles.keys())

    # Solve for each build
    print(f"\nSolving LP for {len(builds_to_run)} build(s) at {args.budget:.0f}-hr budget...")
    results: list[LPResult] = []
    for build_name in builds_to_run:
        weights = build_profiles[build_name]
        res = build_and_solve(build_name, weights, canonical_potions, ing_yields, regions, args.budget)
        results.append(res)
        print(f"\n=== {build_name} ===")
        print(f"  Status: {res.status}  |  Objective: {res.objective_value:.2f}")
        print(f"  Region hours:")
        for region, hrs in sorted(res.region_hours.items(), key=lambda x: -x[1]):
            if hrs > 0.01:
                print(f"    {region}: {hrs:.2f} hrs")
        print(f"  Top potions:")
        for potion, batches in sorted(res.potion_batches.items(), key=lambda x: -x[1])[:5]:
            if batches > 0.01:
                print(f"    {potion}: {batches:.2f} batches")
        if res.shadow_price_time > 0:
            print(f"  Shadow price (time): {res.shadow_price_time:.3f} obj/hr")

    if not args.no_charts:
        print("\nGenerating charts...")

        # Chart 1: Region allocation (all builds)
        chart_region_allocation(results)

        # Chart 2: Sensitivity curve (top 3 builds or all if fewer)
        plot_builds = builds_to_run[:3]
        budgets = [5, 8, 10, 12, 15, 17, 20, 25, 30]
        chart_sensitivity(
            plot_builds, build_profiles, canonical_potions, ing_yields, regions, budgets
        )

        # Chart 3: Single-region counterfactual for first build
        chart_single_region_counterfactual(
            results[0].build_name, build_profiles[results[0].build_name],
            canonical_potions, ing_yields, regions, args.budget
        )

        # Chart 4: Ingredient yield heatmap
        chart_yield_heatmap(ing_yields, regions)

        # Chart 5: Potion comparison (up to 3 builds)
        chart_potion_comparison(results[:3])

    # Write results JSON for the React component
    results_json = []
    for res in results:
        results_json.append({
            "build_name":       res.build_name,
            "time_budget":      res.time_budget,
            "status":           res.status,
            "objective_value":  res.objective_value,
            "shadow_price_time": res.shadow_price_time,
            "region_hours":     res.region_hours,
            "potion_batches":   res.potion_batches,
        })

    out_path = DATA_DIR / "results.json"
    with open(out_path, "w") as f:
        json.dump(results_json, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
