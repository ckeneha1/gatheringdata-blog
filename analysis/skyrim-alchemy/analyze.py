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
from collections import defaultdict
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

    # 2) Ingredient conservation: Σ_{p using i} z[p] <= Σ_r x[r] * yield[r][i]
    #    One constraint per unique ingredient across all active recipes.
    #    This correctly prevents the same unit of ingredient i from being used
    #    simultaneously by multiple potions.
    #    Rewritten: Σ z[p] - Σ_r x[r] * yield[r][i] <= 0
    ing_to_potion_indices: dict[str, list[int]] = defaultdict(list)
    for j, potion in enumerate(active_potions):
        for ing_name in potion["ingredients"]:
            if ing_name in ing_yields:
                ing_to_potion_indices[ing_name].append(j)

    for ing_name, potion_indices in ing_to_potion_indices.items():
        row = np.zeros(n_vars)
        for j in potion_indices:
            row[R + j] = 1.0                                          # Σ z[p] coefficients
        for r_idx, region in enumerate(regions):
            row[r_idx] = -ing_yields[ing_name].get(region, 0.0)      # -Σ yield[r][i]
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
    region_hours = {regions[r]: round(x[r], 4) for r in range(R)}

    # Aggregate batches by potion name (multiple pairs may share the same potion name)
    batches_by_name: dict[str, float] = defaultdict(float)
    for j, p in enumerate(active_potions):
        batches_by_name[p["name"]] += x[R + j]
    potion_batches = {name: round(v, 4) for name, v in batches_by_name.items()}

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
# Stress test: full pair enumeration vs. canonical pair selection
# ---------------------------------------------------------------------------

def stress_test_pair_selection(
    build_name: str,
    weights: dict[str, float],
    potions_raw: list[dict],
    canonical_potions: list[dict],
    ing_yields: dict[str, dict[str, float]],
    regions: list[str],
    time_budget: float = 20.0,
) -> dict:
    """
    Test A: run the foraging LP with ALL valid ingredient pairs (not just the
    canonical highest-yield pair per potion type).  Each pair gets its own
    decision variable z[pair_idx]; the build weight is shared across all pairs
    for the same potion name, so the solver can freely pick whichever pair (or
    mix of pairs) maximises the weighted objective.

    Compares against the canonical-pair LP on:
      - objective value improvement (%)
      - L1 distance between regional allocations
    """
    # All valid pairs: both ingredients have yield data, potion has non-zero weight
    valid_pairs = [
        p for p in potions_raw
        if weights.get(p["name"], 0.0) > 0
        and p["ingredients"][0] in ing_yields
        and p["ingredients"][1] in ing_yields
    ]
    if not valid_pairs:
        return {"error": "no valid pairs"}

    canonical_result = build_and_solve(
        build_name, weights, canonical_potions, ing_yields, regions, time_budget
    )

    # --- Full-enumeration LP ------------------------------------------------
    R = len(regions)
    P = len(valid_pairs)
    n_vars = R + P

    c = np.zeros(n_vars)
    for j, p in enumerate(valid_pairs):
        c[R + j] = -weights.get(p["name"], 0.0)

    rows_A: list[np.ndarray] = []
    rows_b: list[float] = []

    # Time budget
    row = np.zeros(n_vars)
    row[:R] = 1.0
    rows_A.append(row)
    rows_b.append(time_budget)

    # Ingredient conservation (same fix as build_and_solve)
    ing_to_pair_indices: dict[str, list[int]] = defaultdict(list)
    for j, potion in enumerate(valid_pairs):
        for ing_name in potion["ingredients"]:
            ing_to_pair_indices[ing_name].append(j)

    for ing_name, pair_indices in ing_to_pair_indices.items():
        row = np.zeros(n_vars)
        for j in pair_indices:
            row[R + j] = 1.0
        for r_idx, region in enumerate(regions):
            row[r_idx] = -ing_yields[ing_name].get(region, 0.0)
        rows_A.append(row)
        rows_b.append(0.0)

    A_ub = np.array(rows_A)
    b_ub = np.array(rows_b)
    result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=[(0.0, None)] * n_vars, method="highs")

    if result.status != 0:
        return {"error": result.message}

    x = result.x
    full_region_hours = {regions[r]: round(x[r], 4) for r in range(R)}
    full_obj = round(-result.fun, 4)

    # Which pairs does the full-enum LP actually use (z > 0.01)?
    active_pairs_used = [
        {"name": valid_pairs[j]["name"], "ingredients": valid_pairs[j]["ingredients"],
         "batches": round(x[R + j], 3)}
        for j in range(P) if x[R + j] > 0.01
    ]

    canonical_vec = np.array([canonical_result.region_hours.get(r, 0.0) for r in regions])
    full_vec      = np.array([full_region_hours.get(r, 0.0) for r in regions])
    l1_dist = float(np.sum(np.abs(canonical_vec - full_vec)))

    obj_improvement_pct = round(
        100.0 * (full_obj - canonical_result.objective_value) / canonical_result.objective_value, 2
    ) if canonical_result.objective_value > 0 else 0.0

    return {
        "build_name":              build_name,
        "canonical_obj":           canonical_result.objective_value,
        "full_enum_obj":           full_obj,
        "obj_improvement_pct":     obj_improvement_pct,
        "canonical_region_hours":  canonical_result.region_hours,
        "full_region_hours":       full_region_hours,
        "l1_distance":             round(l1_dist, 4),
        "n_canonical_pairs":       len([p for p in canonical_potions if weights.get(p["name"], 0.0) > 0]),
        "n_valid_pairs":           P,
        "active_pairs_used":       active_pairs_used,
    }


# ---------------------------------------------------------------------------
# Three-ingredient analysis
# ---------------------------------------------------------------------------

def effect_weights_from_build(build_weights: dict[str, float]) -> dict[str, float]:
    """
    Build profiles are keyed by full potion name ("Potion of Fortify Health").
    Ingredient effects use the bare name ("Fortify Health").
    Strip the prefix to get a per-effect weight dict.
    """
    return {
        name.replace("Potion of ", "").replace("Poison of ", ""): w
        for name, w in build_weights.items()
    }


def enumerate_pure_triples(
    ingredients: list[dict],
    ing_yields: dict[str, dict[str, float]],
    effect_weights: dict[str, float],
) -> list[dict]:
    """
    Enumerate all three-ingredient combinations where:
      - All three ingredients have region-yield data
      - The activated effects (shared by 2+ of the 3 ingredients) are all the same polarity
      - At least one activated effect has non-zero weight for this build

    Returns list of dicts sorted by synergy_gain (triple_weight - best_pair_weight) descending.
    """
    # Build per-ingredient effect list: {name: [(effect, polarity), ...]}
    ing_effects: dict[str, list[tuple[str, str]]] = {}
    for ing in ingredients:
        if ing["name"] in ing_yields:
            ing_effects[ing["name"]] = [
                (e["effect"], e["polarity"]) for e in ing.get("effects", [])
            ]

    names = list(ing_effects.keys())
    n = len(names)

    # Pre-build sets for fast intersection
    effect_sets: dict[str, set[str]] = {nm: {e for e, _ in ing_effects[nm]} for nm in names}
    polarity_map: dict[str, dict[str, str]] = {
        nm: {e: p for e, p in ing_effects[nm]} for nm in names
    }

    pure_triples: list[dict] = []

    for i in range(n):
        a = names[i]
        for j in range(i + 1, n):
            b = names[j]
            # Quick pre-check: do a and b share any effects at all?
            ab_shared = effect_sets[a] & effect_sets[b]
            for k in range(j + 1, n):
                c = names[k]
                # Activated effects: shared by 2+ of the 3
                ac_shared = effect_sets[a] & effect_sets[c]
                bc_shared = effect_sets[b] & effect_sets[c]
                activated = ab_shared | ac_shared | bc_shared

                if not activated:
                    continue

                # Polarity purity check — collect polarity for each activated effect
                # (use first ingredient that carries the effect as the authoritative source)
                polarities: set[str] = set()
                for eff in activated:
                    if eff in polarity_map[a]:
                        polarities.add(polarity_map[a][eff])
                    elif eff in polarity_map[b]:
                        polarities.add(polarity_map[b][eff])
                    elif eff in polarity_map[c]:
                        polarities.add(polarity_map[c][eff])

                if len(polarities) > 1:
                    continue  # mixed polarity — unsafe brew

                # Build-specific score
                triple_weight = sum(effect_weights.get(eff, 0.0) for eff in activated)
                if triple_weight <= 0.0:
                    continue

                # Best pure pair weight from the 3 possible pairs
                best_pair_w = 0.0
                for pa, pb, shared in [(a, b, ab_shared), (a, c, ac_shared), (b, c, bc_shared)]:
                    if not shared:
                        continue
                    pair_pols = {
                        polarity_map[pa].get(e) or polarity_map[pb].get(e)
                        for e in shared
                    }
                    if len(pair_pols) <= 1:  # pure pair
                        pw = sum(effect_weights.get(e, 0.0) for e in shared)
                        best_pair_w = max(best_pair_w, pw)

                synergy_gain = triple_weight - best_pair_w

                pure_triples.append({
                    "ingredients": [a, b, c],
                    "effects": sorted(activated),
                    "polarity": next(iter(polarities)),
                    "total_weight": triple_weight,
                    "best_pair_weight": best_pair_w,
                    "synergy_gain": round(synergy_gain, 4),
                })

    return sorted(pure_triples, key=lambda x: -x["synergy_gain"])


def brewing_allocation_lp(
    ingredient_totals: dict[str, float],
    canonical_pairs: list[dict],
    pure_triples: list[dict],
    build_weights: dict[str, float],
    top_triples: int = 50,
) -> dict:
    """
    Secondary LP: given ingredient_totals from the primary (foraging) LP,
    find the optimal mix of two-ingredient and three-ingredient brews.

    Returns dict with objective values for 2-ingredient-only and mixed strategies.
    """
    # Limit triples to top N by synergy gain to keep LP tractable
    triples = pure_triples[:top_triples]

    # Only include canonical pairs with non-zero weight
    active_pairs = [p for p in canonical_pairs if build_weights.get(p["name"], 0.0) > 0]

    def _solve(include_triples: bool) -> float:
        n_pairs = len(active_pairs)
        n_triples = len(triples) if include_triples else 0
        n_vars = n_pairs + n_triples

        if n_vars == 0:
            return 0.0

        # Objective: maximize Σ_p w_p*z2[p] + Σ_c w_c*z3[c]
        c_obj = np.zeros(n_vars)
        for j, p in enumerate(active_pairs):
            c_obj[j] = -build_weights.get(p["name"], 0.0)
        for k, t in enumerate(triples if include_triples else []):
            c_obj[n_pairs + k] = -t["total_weight"]

        # Ingredient constraints: for each ingredient i,
        # Σ_p (1 if i in pair[p]) * z2[p] + Σ_c (1 if i in triple[c]) * z3[c] <= totals[i]
        rows_A: list[np.ndarray] = []
        rows_b: list[float] = []

        # Collect all ingredients that appear in any recipe
        all_ings: set[str] = set()
        for p in active_pairs:
            all_ings.update(p["ingredients"])
        if include_triples:
            for t in triples:
                all_ings.update(t["ingredients"])

        for ing in all_ings:
            total = ingredient_totals.get(ing, 0.0)
            row = np.zeros(n_vars)
            for j, p in enumerate(active_pairs):
                if ing in p["ingredients"]:
                    row[j] = 1.0
            if include_triples:
                for k, t in enumerate(triples):
                    if ing in t["ingredients"]:
                        row[n_pairs + k] = 1.0
            rows_A.append(row)
            rows_b.append(total)

        if not rows_A:
            return 0.0

        A_ub = np.array(rows_A)
        b_ub = np.array(rows_b)
        bounds = [(0.0, None)] * n_vars

        result = linprog(c_obj, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
        return round(-result.fun, 4) if result.status == 0 else 0.0

    obj_2only = _solve(include_triples=False)
    obj_mixed = _solve(include_triples=True)
    gain_abs = round(obj_mixed - obj_2only, 4)
    gain_pct = round(100.0 * gain_abs / obj_2only, 1) if obj_2only > 0 else 0.0

    return {
        "obj_2only": obj_2only,
        "obj_mixed": obj_mixed,
        "gain_abs": gain_abs,
        "gain_pct": gain_pct,
        "n_triples_considered": len(triples),
    }


# ---------------------------------------------------------------------------
# Chart 6: Three-ingredient synergy gain
# ---------------------------------------------------------------------------

def chart_three_ingredient_synergy(
    brew_results: list[dict],
    build_names: list[str],
):
    """
    Grouped bar chart: for each build, show the weighted objective value
    from two-ingredient-only brewing vs. optimal mixed brewing.
    The gain is the value unlocked by three-ingredient combos.
    """
    n = len(build_names)
    x = np.arange(n)
    width = 0.35

    obj_2only = [brew_results[i]["obj_2only"] for i in range(n)]
    obj_mixed  = [brew_results[i]["obj_mixed"]  for i in range(n)]
    gains      = [brew_results[i]["gain_abs"]   for i in range(n)]

    fig, ax = plt.subplots(figsize=(11, 5))

    bars_2 = ax.bar(x - width / 2, obj_2only, width, label="Two-ingredient only",
                    color=ACCENT, alpha=0.9)
    bars_m = ax.bar(x + width / 2, obj_mixed,  width, label="Optimal mix (2- and 3-ingredient)",
                    color=ACCENT_DARK, alpha=0.9)

    # Annotate each mixed bar with "+X.X%" gain
    for i, (bar, gain, pct) in enumerate(zip(bars_m, gains, [r["gain_pct"] for r in brew_results])):
        if gain > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.3,
                f"+{pct:.1f}%",
                ha="center", va="bottom", fontsize=8, color=TEXT,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(build_names, rotation=15, ha="right", fontsize=9)

    apply_blog_style(
        ax,
        title="Brewing objective: two-ingredient only vs. optimal mix",
        ylabel="Weighted objective (Σ weight × batches)",
    )
    ax.legend(fontsize=9, frameon=False)

    save(fig, "three_ingredient_synergy.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", help="Run only this build")
    parser.add_argument("--budget", type=float, default=20.0, help="Time budget in hours")
    parser.add_argument("--no-charts", action="store_true", help="Skip chart generation")
    parser.add_argument("--stress-test", action="store_true", help="Run pair-selection stress test (Test A)")
    args = parser.parse_args()

    ingredients, potions_raw, build_profiles = load_data()

    # Index ingredient yields
    ing_yields = {ing["name"]: ing["region_yields"] for ing in ingredients}
    regions    = sorted(next(iter(ing_yields.values())).keys())

    print(f"Loaded {len(ingredients)} ingredients, {len(potions_raw)} potion combinations")

    # All valid pairs: both ingredients in the yield dataset.
    # The LP solver will choose the optimal mix of pairs for each build.
    valid_potions = [
        p for p in potions_raw
        if p["ingredients"][0] in ing_yields and p["ingredients"][1] in ing_yields
    ]
    print(f"  {len(valid_potions)} valid ingredient pairs with yield data")

    # Keep canonical selection available for the stress test only
    canonical_potions = select_canonical_pairs(potions_raw, ing_yields)

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
        res = build_and_solve(build_name, weights, valid_potions, ing_yields, regions, args.budget)
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

    # Stress test: full pair enumeration (optional)
    if args.stress_test:
        print("\n=== Stress Test A: Full Pair Enumeration ===")
        print(f"{'Build':<25} {'Canon obj':>10} {'Full obj':>10} {'Δobj%':>7} {'L1 dist':>9} {'N pairs':>8}")
        print("-" * 75)
        for res in results:
            st = stress_test_pair_selection(
                res.build_name, build_profiles[res.build_name],
                potions_raw, canonical_potions, ing_yields, regions, args.budget
            )
            if "error" in st:
                print(f"  {res.build_name}: ERROR — {st['error']}")
                continue
            print(
                f"  {st['build_name']:<23} {st['canonical_obj']:>10.2f} {st['full_enum_obj']:>10.2f}"
                f" {st['obj_improvement_pct']:>6.2f}% {st['l1_distance']:>9.3f}"
                f"  {st['n_canonical_pairs']}→{st['n_valid_pairs']}"
            )
            # Show allocation shifts > 0.5 hrs
            print("    Regional allocation changes (full-enum − canonical, hours):")
            for region in regions:
                delta = st["full_region_hours"].get(region, 0.0) - st["canonical_region_hours"].get(region, 0.0)
                if abs(delta) > 0.5:
                    print(f"      {region}: {delta:+.2f} hrs")
            # Show which alternative pairs the full-enum LP chose
            print("    Active pairs in full-enum solve (non-canonical pairs starred):")
            canonical_sigs = {
                (p["name"], tuple(sorted(p["ingredients"])))
                for p in canonical_potions
                if build_profiles[res.build_name].get(p["name"], 0.0) > 0
            }
            for ap in sorted(st["active_pairs_used"], key=lambda x: -x["batches"]):
                sig = (ap["name"], tuple(sorted(ap["ingredients"])))
                marker = " *" if sig not in canonical_sigs else "  "
                print(f"    {marker} {ap['name']}: {ap['ingredients']} ({ap['batches']:.2f} batches)")

    # Three-ingredient analysis (per-build)
    print("\nEnumerating pure three-ingredient combos and solving secondary brewing LP...")
    brew_results: list[dict] = []
    for res in results:
        ew = effect_weights_from_build(build_profiles[res.build_name])
        triples = enumerate_pure_triples(ingredients, ing_yields, ew)
        brew = brewing_allocation_lp(
            res.ingredient_totals, valid_potions, triples, build_profiles[res.build_name]
        )
        brew["build_name"] = res.build_name
        brew["top_triples"] = triples[:5]  # store top 5 for JSON output
        brew_results.append(brew)
        print(
            f"  {res.build_name}: 2-only={brew['obj_2only']:.2f}  "
            f"mixed={brew['obj_mixed']:.2f}  gain=+{brew['gain_pct']:.1f}%  "
            f"({brew['n_triples_considered']} triples considered)"
        )

    if not args.no_charts:
        print("\nGenerating charts...")

        # Chart 1: Region allocation (all builds)
        chart_region_allocation(results)

        # Chart 2: Sensitivity curve (top 3 builds or all if fewer)
        plot_builds = builds_to_run[:3]
        budgets = [5, 8, 10, 12, 15, 17, 20, 25, 30]
        chart_sensitivity(
            plot_builds, build_profiles, valid_potions, ing_yields, regions, budgets
        )

        # Chart 3: Single-region counterfactual for first build
        chart_single_region_counterfactual(
            results[0].build_name, build_profiles[results[0].build_name],
            valid_potions, ing_yields, regions, args.budget
        )

        # Chart 4: Ingredient yield heatmap
        chart_yield_heatmap(ing_yields, regions)

        # Chart 5: Potion comparison (up to 3 builds)
        chart_potion_comparison(results[:3])

        # Chart 6: Three-ingredient synergy gain
        chart_three_ingredient_synergy(brew_results, [r.build_name for r in results])

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

    # Write three-ingredient analysis JSON
    brew_out_path = DATA_DIR / "three_ingredient_analysis.json"
    with open(brew_out_path, "w") as f:
        json.dump(brew_results, f, indent=2)
    print(f"Wrote {brew_out_path}")


if __name__ == "__main__":
    main()
