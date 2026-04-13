# Spec: Skyrim Alchemy Optimizer
## gatheringdata.blog — Linear Programming + Skyrim

**Status:** In progress
**Created:** April 2026
**Branch:** `analysis/skyrim-alchemy`

---

## Problem Statement

Skyrim's alchemy system has a hidden optimization structure that most players never formalize:

- Ingredients are geographically distributed across Skyrim's nine holds
- Potions require specific ingredients whose recipes are derivable from the game's effect system
- Different character builds care about completely different potions
- You have a finite amount of time (or patience) to forage

The question: **given your build and a time budget, which regions of Skyrim should you prioritize foraging in?**

This is a linear program. The prior version of this model existed but used invented yield rates and proxy ingredient names. This version rebuilds the data pipeline from scratch using verified game data from UESP.

---

## Decision It Unlocks

A defensible LP model on real game data:
1. Gives a concrete answer to a question every Skyrim player has implicitly faced
2. Demonstrates the LP modeling technique on a domain anyone can verify
3. Produces an interactive tool readers can use for their own builds
4. Makes the data pipeline auditable — anyone can check the ingredient data against UESP

---

## Data Pipeline

### Layer 0: UESP Scrape (`fetch_data.py`)

UESP (Unofficial Elder Scrolls Pages) is the authoritative community source for Skyrim game data. It has:
- Every ingredient with its exact 4 alchemy effects
- Every spawn location, with hold attribution, and spawn counts

**Scrape targets:**
- `https://en.uesp.net/wiki/Skyrim:Ingredients` — full ingredient list (91 base game)
- `https://en.uesp.net/wiki/Skyrim:{Ingredient_Name}` — per-ingredient effects + locations
- API endpoint: `https://en.uesp.net/w/api.php?action=parse&page=Skyrim:{Name}&prop=wikitext&format=json`

**What we extract per ingredient:**
- Name, game ID, weight, value
- Effects: eff1, eff2, eff3, eff4 (exact names from `{{Ingredient Summary}}` template)
- Effect polarities: positive/negative (from `type1`–`type4` params)
- Spawn counts by hold: parsed from `==Ingredients==` and `==Plants==` sections
  - Each bullet: `* N in [[Location]] ([[Hold]])` → aggregate N by Hold name

**Output:** `data/raw/ingredients_list.json` + `data/raw/ingredients/{name}.json` per ingredient

Rate limiting: 0.5s delay between requests, User-Agent header set.
Cache: skip fetch if file already exists.

### Layer 1: Dataset Build (`build_dataset.py`)

**Hold → Region mapping (6 regions from 9 holds):**

| UESP Hold(s) | Model Region |
|---|---|
| The Rift | The Rift (Southeast) |
| Falkreath Hold | Falkreath (South) |
| Hjaalmarch, The Pale | Hjaalmarch / The Pale (North) |
| Whiterun Hold | Whiterun Hold (Central Plains) |
| Winterhold, Eastmarch | Winterhold / Eastmarch (Northeast) |
| The Reach, Haafingar | The Reach / Haafingar (West) |

**Yield rate derivation:**
`yield[region][ingredient] = spawn_count_in_region / max_spawn_count_any_region`

Scaled to [0, 4] range (matching intuitive "units per hour" framing). Monster-drop ingredients (fish, venom, toes) get a difficulty penalty: ×0.2 of plant yield.

**Potion recipe derivation:**
Two ingredients that share at least one effect can be combined to create a potion of that effect. We generate all valid two-ingredient combinations, map them to named potions where the effect corresponds to a known potion type, and flag the primary effect (eff1 of each ingredient is strongest in-game).

**Build profiles:**
Derived from the thegamer.com build list, filtered to builds where alchemy makes a meaningful difference:
- Heavy Armor Warrior
- Stealth Archer
- Pure Mage
- Illusion Assassin (new)
- Paladin (new)
- Necromancer / Conjurer (new)

**Outputs:**
- `data/ingredients.json` — name, effects (4), region yield rates, source URLs
- `data/potions.json` — name, effect, ingredient pairs, build relevance weights
- `data/build_profiles.json` — build name → potion weight dict

### Layer 2: LP Model + Charts (`analyze.py`)

Identical formulation to prior version. Rebuild from `data/` files.

**Charts (5):**
1. Region allocation bar chart — hours per region, grouped by build
2. Sensitivity curve — objective value vs. time budget, 3 builds overlaid
3. Single-region counterfactual — what each build gets if forced into one region
4. Ingredient yield heatmap — 6 regions × top ingredients, colored by yield rate
5. Potion output comparison — side-by-side batches per potion, 3 builds at 20 hrs

---

## Interactive Component

`SkyrimAlchemyOptimizer.jsx` → `src/components/SkyrimAlchemyOptimizer.jsx`

Requires adding `@astrojs/react` to the blog project. The component contains an inline simplex solver and all game data; no backend required.

The blog post will use `.mdx` to embed the component.

---

## Validation

Before trusting any results:
1. Verify eff1–eff4 for 5 known ingredients against UESP directly
2. Confirm `sum(region_hours) <= time_budget` for all solve results
3. Confirm ingredient totals satisfy `potion_batches * recipe_qty` for all potions
4. Confirm objective is monotonically non-decreasing in time_budget
5. Manually check 3 region allocation results make geographic sense

---

## What This Post Is Not

- Not a claim that yield rates are exact — they're proportional to UESP spawn counts, with documented assumptions
- Not a complete alchemy simulator — no leveling, no perk effects, no enchanted equipment
- Not a speedrun guide — the "hours" unit is abstract, not a real-time measurement

---

## Open Questions (resolved at build time)

- How many ingredients will be relevant after deriving potions from effects? (Likely 25–40)
- Will Winterhold / Eastmarch be sparse enough that it's never optimal for any build? (Interesting if so)
- What does the Illusion Assassin build's region allocation look like vs. Stealth Archer? (Hypothesis: more Falkreath for Juniper Berries / Luna Moth Wing)
