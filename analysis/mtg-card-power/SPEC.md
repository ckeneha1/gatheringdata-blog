# Spec: What Does a Mana Cost Buy You?
## MTG Post 2 — Ability-to-Cost Ratio and Power Creep

**Status:** Draft
**Last updated:** April 2026

---

## Problem Statement

Post 1 showed that Magic has been releasing 2,400–2,600 new card designs per year and that cards have gotten longer. Longer isn't necessarily more powerful — it could just be more verbose. This post asks a sharper question: for a given mana cost, how much *ability* does a card buy you, and has that changed over time?

The intuition: if a card printed in 2024 has the same abilities as a card printed in 2005 but costs one less mana, that's power creep. If it costs the same but has one additional ability on top, that's also power creep. Done at scale across 30+ years of cards, this gives us a data-driven heuristic for "good" that's agnostic of tournament results.

---

## Decision It Unlocks

A per-card ability-to-cost ratio:
1. Gives us a principled definition of "good" that we can defend analytically
2. Lets us measure power creep directly rather than inferring it from word count
3. Sets up Post 3's tournament overlay — we can ask what ability-to-cost ratio threshold a card needs to see competitive play

---

## The Two Analysis Layers

### Layer 1: Keyword Abilities (Scryfall `keywords` field)

Scryfall's `oracle_cards` bulk data includes a `keywords` array that already extracts all named keyword abilities: flying, deathtouch, haste, trample, lifelink, vigilance, first strike, double strike, hexproof, indestructible, menace, reach, flash, ward, etc. (~200 distinct keywords in the full pool).

This is clean, complete, and requires no NLP. For each card:
- `keyword_count` = length of `keywords` array
- `keywords_per_cmc` = keyword_count / cmc (for cards with cmc > 0)

Track both over time using `first_print_year` (computed via `all_cards` in Post 1's pipeline).

### Layer 2: Semantic Ability Classification (Claude API)

For non-keyword abilities described in oracle text (e.g., "draw a card", "deals 3 damage to any target", "create a 1/1 token"), we use Claude to classify each card into a fixed ability taxonomy.

**Pre-processing before sending to Claude:**
1. Strip reminder text (parenthetical rules explanations) — e.g., `(This creature can't be blocked.)` adds no ability information
2. Strip flavor text (already separate in Scryfall data)
3. Exclude lands from classification (their "abilities" are mostly mana production by type, not relevant to the ability-to-cost question)
4. Exclude cards with no oracle text
5. Keep only the front face of double-faced cards

**Fixed ability taxonomy (Claude classifies each card against this list):**

| Category | What it covers |
|---|---|
| `evasion` | Flying, menace, unblockable, shadow, horsemanship, fear — anything that makes blocking harder |
| `combat_keywords` | Trample, first strike, double strike, deathtouch, lifelink, vigilance, haste, reach |
| `protection` | Hexproof, shroud, indestructible, ward, protection from X |
| `card_advantage` | Draw cards, scry, surveil, loot, impulse draw, look at top of library |
| `removal` | Destroy/exile/bounce a permanent, -X/-X |
| `direct_damage` | Deal X damage to a target or player |
| `tokens` | Create creature, artifact, or other tokens |
| `counters` | Add/remove +1/+1 or other counters, proliferate |
| `ramp` | Add mana beyond normal land drops, search for land, cost reduction |
| `graveyard` | Return from graveyard, mill, flashback-like effects, graveyard hate |
| `disruption` | Counter spells, force discard, prevent abilities |
| `tutor` | Search library for a specific card |
| `life` | Gain life (separate from lifelink, which is a combat keyword) |
| `pump` | Grant +X/+X temporarily |
| `other` | Anything that doesn't fit cleanly above |

**API call structure:**
- Model: `claude-haiku-4-5-20251001` (fast, cheap, more than capable for structured classification)
- Batch size: 50 cards per request
- Response format: JSON array of `{oracle_id, categories: [list of taxonomy tags]}`
- A card can have multiple categories (e.g., a creature with flying + draw a card gets `["evasion", "card_advantage"]`)
- Cache: keyed on `oracle_id + sha256(oracle_text)` — never re-call for a card already classified; auto-invalidates if oracle text changes

**Category count per card:**
- `semantic_category_count` = number of distinct categories assigned
- Combined with keyword count: `total_ability_count` = `keyword_count + semantic_category_count`
- `abilities_per_cmc` = `total_ability_count / cmc`

---

## Cost Measurement

**Primary cost measure: CMC (converted mana cost)**
- Already a structured field in Scryfall (`cmc`)
- Excludes X in X-cost spells (counted as 0 in CMC) — we'll note this limitation

**Cards excluded from ability-to-cost ratio:**
- Lands (CMC = 0 and "abilities" are structural)
- Cards with CMC = 0 that aren't lands (Moxen, zero-cost spells) — include but flag separately, they're part of the power story
- Split cards: use the CMC of each half separately

**X-cost spells:**
Cards with X in their mana cost (e.g., `{X}{R}`, `{X}{X}{G}`) have CMC that treats each X as 0. We parse the mana cost string to count the number of X symbols separately. A card costing `{X}{X}{G}` has `x_count=2`, which means it scales at twice the rate of a card costing `{X}{G}`. When computing ability-to-cost ratios for X-cost spells, CMC is the floor cost (the non-X portion) and X-count is noted as an additional cost dimension. X-cost spells are included in the analysis but kept visually distinct in charts.

**Oracle-based costs (parsed and included):**
Many cards have costs embedded in their oracle text beyond the casting cost. These are real costs that affect a card's power level and are parseable from standardized oracle language:

- *Activated ability costs*: `{N}: [ability]` and `{T}: [ability]` — an equipment with "Equip {0}" is categorically different from "Equip {3}". We parse mana and tap symbols from activated ability costs and include them in the cost profile.
- *Additional casting costs*: "As an additional cost to cast this spell, discard a card" — increases true cost beyond CMC.
- *Alternative casting costs*: Force of Will and Force of Negation are among the most powerful counterspells in the game precisely because of their oracle costs — they can be cast for free by paying an alternative (exile a card + pay life). These are parseable (alternative cost language is standardized), but present a genuine analytical problem: **when a card has two costs (CMC and an alternative), deciding which is "cheaper" depends on game state.** We parse and record both, but defer the "which cost do we use?" determination to Post 3 where tournament data will ground the comparison. For Post 2, we flag these cards and note they likely understate their true competitive cost at CMC.

**Color identity (noted, not modeled):**
Colored mana pips are a constraint beyond raw CMC — `{U}{U}{U}` is more restrictive than `{3}` even at the same CMC. We'll note this in the methodology section and defer it to Post 3.

---

## Validation

Before trusting the semantic classifications at scale, validate on a sample:

1. **Spot-check 50 random cards manually** — do the assigned categories match a human reading?
2. **Check known exemplars** — Lightning Bolt should get `direct_damage`. Counterspell should get `disruption`. Serra Angel should get `evasion` + `combat_keywords` (flying + vigilance). Ancestral Recall should get `card_advantage`. Force of Will should get `disruption` with an alternative cost flagged.
3. **Distribution sanity check** — is the category distribution plausible? (`evasion` and `combat_keywords` should be the most common; `tutor` should be rare)
4. **Misclassification rate estimate** — from the manual spot-check, estimate what % of cards are mis-tagged and note it in the post's methodology section

---

## Charts (6 planned)

1. **Keywords per mana value, 1993–present** — line chart of average keyword count per CMC by year. The simplest version of the power creep story. Does a 3-mana card in 2024 come with more keywords than a 3-mana card in 2005?

2. **Ability categories per mana value over time** — same structure but using semantic category count. Richer signal than keywords alone.

3. **Total abilities per mana value over time** — the combined measure. This is the headline "power creep" chart.

4. **Power creep by ability type** — small multiples or stacked chart: for each category, how has its "cost" (average CMC of cards carrying that ability) changed over time? Has removal gotten cheaper? Has card draw gotten cheaper?

5. **The distribution shift** — at fixed CMC (e.g., 2-mana cards, 3-mana cards), show the distribution of ability counts in 1993–2000 vs. 2015–2025. Are the distributions visually different?

6. **Exemplar comparison** — a manually curated table or visual showing 3–5 pairs like Seismic Tutelage / Level Up: same ability bundle, different cost, different year. Makes the abstract finding concrete.

---

## Data Pipeline

Builds on the Post 1 pipeline (`analysis/mtg-distributions/analyze.py`):
- `oracle_cards` bulk download from Scryfall (already cached)
- `first_print_year` mapping from `all_cards` (already computed and cached in Post 1)
- New: Claude API classification, cached to `.cache/ability_classifications.json`
- New: reminder text stripper (regex on parenthetical content)

New analysis lives in `analysis/mtg-card-power/` (separate directory, separate uv project).

---

## Design Decisions (Resolved)

1. **X-cost spells**: Include. Parse X-count from mana cost string. CMC is the floor; X-count is noted separately. `{X}{X}` cards scale at 2x the rate of `{X}` cards.

2. **Oracle-based costs**: Parse and include. Equip costs, activated ability mana costs, and additional casting costs are all real costs that affect power level and use standardized language. Alternative casting costs (Force of Will pattern) are parsed and recorded but deferred to Post 3 for the "which cost is cheaper" determination.

3. **Color identity**: Note in methodology, put a pin in it. Not modeled in Post 2.

4. **Ability weighting**: Note in methodology, put a pin in it. Cards like Psychic Frog illustrate how synergy between cheap abilities compounds — tournament data in Post 3 will help assess whether equal weighting holds up.

---

## What This Post Is Not

- Not a claim that CMC is the only relevant cost — it's the best available structured cost measure
- Not a claim that more abilities = better card — it's a heuristic, not a complete theory of card quality
- Not a tournament analysis — that's Post 3

---

## Relationship to Other Posts

- **Post 1** (published): established the supply-side story — how many cards exist, what types
- **This post**: establishes the ability-to-cost heuristic and measures power creep
- **Post 3**: overlays tournament play data to test what ability-to-cost ratio threshold correlates with competitive play
