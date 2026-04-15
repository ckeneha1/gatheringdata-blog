"""
build_dataset.py — Aggregate UESP raw data into LP-ready datasets.

Reads:  data/raw/ingredients_list.json + data/raw/ingredients/*.json
Writes:
    data/ingredients.json   — {name, effects, hold_counts, region_yields, source_url}
    data/potions.json       — {name, effect, ingredients, is_poison}
    data/build_profiles.json — {build_name: {potion_name: weight}}

Usage:
    uv run python build_dataset.py

Hold → Region mapping (9 Skyrim holds → 6 model regions):
    The Rift                      → The Rift (Southeast)
    Falkreath Hold                → Falkreath (South)
    Hjaalmarch + The Pale         → Hjaalmarch / The Pale (North)
    Whiterun Hold                 → Whiterun Hold (Central Plains)
    Winterhold + Eastmarch        → Winterhold / Eastmarch (Northeast)
    The Reach + Haafingar         → The Reach / Haafingar (West)

Yield rate derivation (global normalization):
    global_max = max single-region spawn count of any ingredient (503: Dragon's Tongue NE)
    yield[ingredient][region] = region_spawn_count / global_max * 4.0

    All ingredients share the same denominator, so yield rates are comparable across
    ingredients. A rare item like Human Flesh (14 total spawns) scores ~0.03 per region;
    an abundant plant like Dragon's Tongue scores up to 4.0. Monster-drop ingredients
    with no UESP spawn data get a fixed yield of 0.3 in documented creature regions.

Potion derivation:
    Two ingredients sharing at least one effect → a valid potion of that effect.
    We keep only named potions (mapped from known effect names).
"""

from __future__ import annotations
import json
import re
from collections import defaultdict
from itertools import combinations
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RAW_DIR   = Path(__file__).parent / "data" / "raw"
DATA_DIR  = Path(__file__).parent / "data"
ING_DIR   = RAW_DIR / "ingredients"
LIST_FILE = RAW_DIR / "ingredients_list.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Hold → Region mapping
# ---------------------------------------------------------------------------

HOLD_TO_REGION: dict[str, str] = {
    "The Rift":        "The Rift (Southeast)",
    "Falkreath Hold":  "Falkreath (South)",
    "Hjaalmarch":      "Hjaalmarch / The Pale (North)",
    "The Pale":        "Hjaalmarch / The Pale (North)",
    "Whiterun Hold":   "Whiterun Hold (Central Plains)",
    "Winterhold":      "Winterhold / Eastmarch (Northeast)",
    "Eastmarch":       "Winterhold / Eastmarch (Northeast)",
    "The Reach":       "The Reach / Haafingar (West)",
    "Haafingar":       "The Reach / Haafingar (West)",
}

REGIONS = sorted(set(HOLD_TO_REGION.values()))

# ---------------------------------------------------------------------------
# Ingredients that are monster drops (no plant spawns on UESP).
# These get a small fixed yield per region based on creature distribution.
# ---------------------------------------------------------------------------

# effect name → friendly yield hint (regions where creature is broadly present)
MONSTER_DROP_REGIONS: dict[str, list[str]] = {
    # Bears are everywhere, but especially in forested/snowy areas
    "Bear Claws":         ["The Rift (Southeast)", "Falkreath (South)",
                           "Hjaalmarch / The Pale (North)", "Winterhold / Eastmarch (Northeast)",
                           "The Reach / Haafingar (West)"],
    "Large Antlers":      ["The Rift (Southeast)", "Falkreath (South)",
                           "Hjaalmarch / The Pale (North)", "Whiterun Hold (Central Plains)",
                           "The Reach / Haafingar (West)"],
    "Hawk Feathers":      ["The Rift (Southeast)", "Falkreath (South)",
                           "Whiterun Hold (Central Plains)", "The Reach / Haafingar (West)"],
    "Hawk's Egg":         ["Whiterun Hold (Central Plains)", "The Reach / Haafingar (West)"],
    "Frostbite Venom":    ["Hjaalmarch / The Pale (North)", "Winterhold / Eastmarch (Northeast)",
                           "The Rift (Southeast)"],
    "Giant's Toe":        ["Whiterun Hold (Central Plains)", "The Rift (Southeast)",
                           "Hjaalmarch / The Pale (North)"],
    "Slaughterfish Egg":  ["Hjaalmarch / The Pale (North)", "Winterhold / Eastmarch (Northeast)"],
    "Slaughterfish Scales": ["Hjaalmarch / The Pale (North)", "Winterhold / Eastmarch (Northeast)",
                             "The Rift (Southeast)"],
    "Abecean Longfin":    ["The Reach / Haafingar (West)", "Hjaalmarch / The Pale (North)"],
    "Juvenile Mudcrab":   ["Hjaalmarch / The Pale (North)", "Winterhold / Eastmarch (Northeast)",
                           "The Reach / Haafingar (West)"],
    "Mudcrab Chitin":     ["Hjaalmarch / The Pale (North)", "Winterhold / Eastmarch (Northeast)",
                           "The Reach / Haafingar (West)"],
    "Sabre Cat Tooth":    ["Hjaalmarch / The Pale (North)", "Winterhold / Eastmarch (Northeast)"],
    "Sabre Cat Eye":      ["Hjaalmarch / The Pale (North)", "Winterhold / Eastmarch (Northeast)"],
    "Bone Meal":          ["The Rift (Southeast)", "Falkreath (South)",
                           "Winterhold / Eastmarch (Northeast)"],
    "Chaurus Eggs":       ["Winterhold / Eastmarch (Northeast)", "The Rift (Southeast)"],
    "Chaurus Hunter Antennae": ["Winterhold / Eastmarch (Northeast)"],
    "Troll Fat":          ["The Rift (Southeast)", "Falkreath (South)",
                           "Hjaalmarch / The Pale (North)", "The Reach / Haafingar (West)"],
    "Void Salts":         ["Winterhold / Eastmarch (Northeast)", "The Rift (Southeast)"],
    "Daedra Heart":       ["Winterhold / Eastmarch (Northeast)"],
    "Vampire Dust":       ["The Rift (Southeast)", "Falkreath (South)",
                           "Winterhold / Eastmarch (Northeast)"],
    "Dragon's Tongue":    ["The Reach / Haafingar (West)", "The Rift (Southeast)"],
    "Netch Jelly":        [],   # Dragonborn DLC (Solstheim only — not a Skyrim region)
    "Ash Hopper Jelly":   [],   # Dragonborn DLC
    "Ancestor Moth Wing": ["The Rift (Southeast)"],
    "Burnt Spriggan Wood": [],  # Dragonborn DLC
    "Chicken's Egg":      ["Whiterun Hold (Central Plains)", "The Reach / Haafingar (West)"],
}

MONSTER_DROP_YIELD = 0.3   # units/hour (difficulty-adjusted; harder to obtain than plants)

# ---------------------------------------------------------------------------
# Effect → named potion/poison mapping
# ---------------------------------------------------------------------------

EFFECT_TO_POTION: dict[str, tuple[str, bool]] = {
    # effect name → (potion display name, is_poison)
    "Restore Health":           ("Potion of Restore Health",          False),
    "Restore Stamina":          ("Potion of Restore Stamina",         False),
    "Restore Magicka":          ("Potion of Restore Magicka",         False),
    "Fortify Health":           ("Potion of Fortify Health",          False),
    "Fortify Stamina":          ("Potion of Fortify Stamina",         False),
    "Fortify Magicka":          ("Potion of Fortify Magicka",         False),
    "Regenerate Health":        ("Potion of Regenerate Health",       False),
    "Regenerate Stamina":       ("Potion of Regenerate Stamina",      False),
    "Regenerate Magicka":       ("Potion of Regenerate Magicka",      False),
    "Fortify One-handed":       ("Potion of Fortify One-handed",      False),
    "Fortify Two-handed":       ("Potion of Fortify Two-handed",      False),
    "Fortify Heavy Armor":      ("Potion of Fortify Heavy Armor",     False),
    "Fortify Light Armor":      ("Potion of Fortify Light Armor",     False),
    "Fortify Block":            ("Potion of Fortify Block",           False),
    "Fortify Archery":          ("Potion of Fortify Marksman",        False),
    "Fortify Marksman":         ("Potion of Fortify Marksman",        False),
    "Fortify Sneak":            ("Potion of Fortify Sneak",           False),
    "Fortify Illusion":         ("Potion of Fortify Illusion",        False),
    "Fortify Destruction":      ("Potion of Fortify Destruction",     False),
    "Fortify Conjuration":      ("Potion of Fortify Conjuration",     False),
    "Fortify Alteration":       ("Potion of Fortify Alteration",      False),
    "Fortify Restoration":      ("Potion of Fortify Restoration",     False),
    "Fortify Enchanting":       ("Potion of Fortify Enchanting",      False),
    "Fortify Smithing":         ("Potion of Fortify Smithing",        False),
    "Fortify Barter":           ("Potion of Fortify Barter",          False),
    "Fortify Carry Weight":     ("Potion of Fortify Carry Weight",    False),
    "Invisibility":             ("Potion of Invisibility",            False),
    "Invisibility (effect)":    ("Potion of Invisibility",            False),
    "Waterbreathing (effect)":  ("Potion of Waterbreathing",         False),
    "Waterbreathing":           ("Potion of Waterbreathing",         False),
    "Cure Disease":             ("Potion of Cure Disease",            False),
    "Resist Fire":              ("Potion of Resist Fire",             False),
    "Resist Frost":             ("Potion of Resist Frost",            False),
    "Resist Shock":             ("Potion of Resist Shock",            False),
    "Resist Magic":             ("Potion of Resist Magic",            False),
    "Resist Poison":            ("Potion of Resist Poison",           False),
    "Damage Health":            ("Poison of Damage Health",           True),
    "Damage Stamina":           ("Poison of Damage Stamina",          True),
    "Damage Magicka":           ("Poison of Damage Magicka",          True),
    "Damage Stamina Regen":     ("Poison of Damage Stamina Regen",    True),
    "Damage Magicka Regen":     ("Poison of Damage Magicka Regen",    True),
    "Lingering Damage Health":  ("Poison of Lingering Damage Health", True),
    "Lingering Damage Stamina": ("Poison of Lingering Damage Stamina", True),
    "Lingering Damage Magicka": ("Poison of Lingering Damage Magicka", True),
    "Paralysis":                ("Poison of Paralysis",               True),
    "Slow":                     ("Poison of Slow",                    True),
    "Frenzy (effect)":          ("Poison of Frenzy",                  True),
    "Fear (effect)":            ("Poison of Fear",                    True),
    "Weakness to Fire":         ("Poison of Weakness to Fire",        True),
    "Weakness to Frost":        ("Poison of Weakness to Frost",       True),
    "Weakness to Shock":        ("Poison of Weakness to Shock",       True),
    "Weakness to Magic":        ("Poison of Weakness to Magic",       True),
    "Weakness to Poison":       ("Poison of Weakness to Poison",      True),
}

# ---------------------------------------------------------------------------
# Build profiles (6 builds from thegamer.com archetypes)
# ---------------------------------------------------------------------------

BUILD_PROFILES: dict[str, dict[str, float]] = {
    "Heavy Armor Warrior": {
        "Potion of Fortify Health":       4.0,
        "Potion of Fortify Heavy Armor":  3.0,
        "Potion of Fortify Block":        3.0,
        "Potion of Restore Health":       3.0,
        "Potion of Restore Stamina":      2.0,
        "Potion of Fortify One-handed":   2.0,
        "Potion of Fortify Two-handed":   1.0,
        "Poison of Damage Health":        2.0,
        "Poison of Paralysis":            2.0,
    },
    "Stealth Archer": {
        "Potion of Fortify Marksman":     4.0,
        "Potion of Invisibility":         4.0,
        "Potion of Fortify Sneak":        3.0,
        "Poison of Damage Health":        3.0,
        "Poison of Slow":                 2.0,
        "Potion of Restore Stamina":      2.0,
        "Potion of Fortify Light Armor":  1.0,
    },
    "Pure Mage": {
        "Potion of Fortify Destruction":  4.0,
        "Potion of Fortify Magicka":      3.0,
        "Potion of Regenerate Magicka":   3.0,
        "Potion of Restore Magicka":      3.0,
        "Potion of Invisibility":         2.0,
        "Poison of Damage Health":        2.0,
        "Potion of Fortify Restoration":  1.0,
        "Potion of Fortify Conjuration":  1.0,
    },
    "Illusion Assassin": {
        "Potion of Invisibility":         4.0,
        "Potion of Fortify Illusion":     4.0,
        "Potion of Fortify Sneak":        3.0,
        "Poison of Damage Health":        3.0,
        "Poison of Paralysis":            3.0,
        "Poison of Lingering Damage Health": 2.0,
        "Potion of Restore Health":       1.0,
    },
    "Paladin": {
        "Potion of Restore Health":       4.0,
        "Potion of Fortify Heavy Armor":  3.0,
        "Potion of Fortify Block":        3.0,
        "Potion of Cure Disease":         3.0,
        "Potion of Fortify Restoration":  2.0,
        "Potion of Resist Magic":         2.0,
        "Potion of Fortify One-handed":   2.0,
    },
    "Necromancer": {
        "Potion of Fortify Conjuration":  4.0,
        "Potion of Fortify Magicka":      3.0,
        "Potion of Regenerate Magicka":   3.0,
        "Poison of Damage Health":        3.0,
        "Poison of Frenzy":               2.0,
        "Potion of Fortify Destruction":  2.0,
        "Potion of Invisibility":         1.0,
    },
}

# ---------------------------------------------------------------------------
# Load raw ingredient data
# ---------------------------------------------------------------------------

def load_ingredients() -> list[dict]:
    """Load all cached ingredient JSON files from the list."""
    with open(LIST_FILE) as f:
        names = json.load(f)

    ingredients = []
    for name in names:
        safe = re.sub(r"[^\w\-]", "_", name)
        path = ING_DIR / f"{safe}.json"
        if not path.exists():
            continue
        with open(path) as f:
            d = json.load(f)
        # Only include real alchemy ingredients: need game_id and >=1 effect
        if not d.get("game_id") or not d.get("effects"):
            continue
        ingredients.append(d)
    return ingredients


# ---------------------------------------------------------------------------
# Build region yield rates
# ---------------------------------------------------------------------------

def build_region_yields(ingredients: list[dict]) -> dict[str, dict[str, float]]:
    """
    Returns {ingredient_name: {region: yield_rate}} for all ingredients.

    Yield rate uses GLOBAL normalization:
        yield = region_count / global_max_count * 4.0

    where global_max_count is the highest single-region count of ANY ingredient
    across all ingredients and all regions.

    This means yield rates are comparable across ingredients — a rare ingredient
    with few spawn points (e.g. Human Flesh, 14 total) will score much lower than
    a common plant (e.g. Dragon's Tongue, 503 spawns in one region).

    Monster drops with no UESP plant-spawn data get a fixed small yield in regions
    where their creature is documented to appear.
    """
    # --- Pass 1: aggregate all region counts ---
    all_region_counts: dict[str, dict[str, int]] = {}

    for ing in ingredients:
        name = ing["name"]
        hold_counts: dict[str, int] = ing.get("hold_counts", {})

        region_counts: dict[str, int] = defaultdict(int)
        for hold, count in hold_counts.items():
            region = HOLD_TO_REGION.get(hold)
            if region:
                region_counts[region] += count

        if sum(region_counts.values()) > 0:
            all_region_counts[name] = dict(region_counts)

    # --- Global max: highest single-region count across all ingredients ---
    global_max = max(
        count
        for region_counts in all_region_counts.values()
        for count in region_counts.values()
    )

    # --- Pass 2: compute scaled yields ---
    yields: dict[str, dict[str, float]] = {}

    for ing in ingredients:
        name = ing["name"]

        if name in all_region_counts:
            region_counts = all_region_counts[name]
            region_yield = {
                r: (region_counts.get(r, 0) / global_max) * 4.0
                for r in REGIONS
            }
        elif name in MONSTER_DROP_REGIONS:
            # Monster drop with no UESP spawn data — use fixed difficulty-adjusted yield
            region_yield = {r: 0.0 for r in REGIONS}
            for r in MONSTER_DROP_REGIONS[name]:
                region_yield[r] = MONSTER_DROP_YIELD
        else:
            # No spawn data — skip
            continue

        yields[name] = region_yield

    return yields


# ---------------------------------------------------------------------------
# Derive potions from shared effects
# ---------------------------------------------------------------------------

def derive_potions(ingredients: list[dict]) -> list[dict]:
    """
    Find all pairs of ingredients that share at least one effect.
    Map shared effects to named potions via EFFECT_TO_POTION.
    Returns list of unique potions with their ingredient pairs.
    """
    # Index: effect → list of ingredient names that have it
    effect_to_ings: dict[str, list[str]] = defaultdict(list)
    for ing in ingredients:
        for eff in ing["effects"]:
            effect_to_ings[eff["effect"]].append(ing["name"])

    # Build potions: one per (potion_name, frozenset of ingredient pair)
    seen: set[tuple[str, frozenset]] = set()
    potions: list[dict] = []

    for effect, ings_with_effect in effect_to_ings.items():
        if effect not in EFFECT_TO_POTION:
            continue
        potion_name, is_poison = EFFECT_TO_POTION[effect]

        # All pairs of ingredients sharing this effect
        for ing1, ing2 in combinations(ings_with_effect, 2):
            key = (potion_name, frozenset([ing1, ing2]))
            if key in seen:
                continue
            seen.add(key)
            potions.append({
                "name":        potion_name,
                "effect":      effect,
                "ingredients": sorted([ing1, ing2]),
                "is_poison":   is_poison,
            })

    potions.sort(key=lambda p: (p["name"], p["ingredients"][0]))
    return potions


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading raw ingredient data...")
    ingredients = load_ingredients()
    print(f"  {len(ingredients)} valid ingredients loaded")

    print("Computing region yield rates...")
    region_yields = build_region_yields(ingredients)
    print(f"  {len(region_yields)} ingredients with yield data")

    # Build ingredients output: augment each ingredient dict with region yields
    ing_output = []
    for ing in ingredients:
        name = ing["name"]
        if name not in region_yields:
            continue
        ing_output.append({
            "name":         name,
            "game_id":      ing["game_id"],
            "value":        ing.get("value", ""),
            "weight":       ing.get("weight", ""),
            "effects":      ing["effects"],
            "hold_counts":  ing.get("hold_counts", {}),
            "region_yields": region_yields[name],
            "source_url":   ing["source_url"],
        })

    out_path = DATA_DIR / "ingredients.json"
    with open(out_path, "w") as f:
        json.dump(ing_output, f, indent=2)
    print(f"  Wrote {out_path} ({len(ing_output)} ingredients)")

    print("Deriving potions from shared effects...")
    potions = derive_potions(ingredients)

    # Report unique potion names
    potion_names = sorted(set(p["name"] for p in potions))
    print(f"  {len(potions)} potion combinations → {len(potion_names)} unique potions")

    out_path = DATA_DIR / "potions.json"
    with open(out_path, "w") as f:
        json.dump(potions, f, indent=2)
    print(f"  Wrote {out_path}")

    print("Writing build profiles...")
    # Filter build profiles to only include potions that can actually be crafted
    craftable = set(p["name"] for p in potions)
    filtered_profiles: dict[str, dict[str, float]] = {}
    for build, weights in BUILD_PROFILES.items():
        filtered_profiles[build] = {
            potion: w for potion, w in weights.items() if potion in craftable
        }
        removed = [p for p in weights if p not in craftable]
        if removed:
            print(f"  {build}: removed uncraftable potions: {removed}")

    out_path = DATA_DIR / "build_profiles.json"
    with open(out_path, "w") as f:
        json.dump(filtered_profiles, f, indent=2)
    print(f"  Wrote {out_path}")

    # Summary stats
    print()
    print("=== Summary ===")
    print(f"Regions: {len(REGIONS)}")
    for r in REGIONS:
        print(f"  {r}")
    print(f"Ingredients with yield data: {len(ing_output)}")
    print(f"Unique craftable potions: {len(potion_names)}")
    for pn in potion_names:
        combos = [p for p in potions if p["name"] == pn]
        print(f"  {pn} ({len(combos)} ingredient pair(s))")


if __name__ == "__main__":
    main()
