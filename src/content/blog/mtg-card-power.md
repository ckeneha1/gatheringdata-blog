---
title: "What Does Your Mana Buy You?"
description: "Building a data-driven definition of 'good' Magic cards."
pubDate: "2026-04-13"
---

[Post 1](./mtg-distributions) established that the supply side of Magic: the Gathering is vast. As of early 2026, the total catalog sits at just under 34,000 unique designs. Which of those cards are actually worth caring about? Which are *good*?

## "Good" is a moving target

Magic is a dynamic, multifaceted game. So is the deckbuilding meta. The format you're playing, the synergies your deck enables, the synergies your opponent's deck might enable... these are all important parts of deciding whether card A is "good", let alone better than B. A card that belongs in every Pioneer sideboard might be unplayable in Standard. A card that's been rotting in bulk bins for a decade can suddenly go from $0.50 to $40 the week a new combo deck gets a key piece printed.

Even the [game's designers](https://magic.wizards.com/en/news/making-magic/state-of-design-2025) resist the framing. Cards aren't designed in isolation: they're designed relative to what already exists, what the various formats need, and what the story calls for. "Good" in that context is not a fixed standard but a negotiation between design intent, card pool state, and whatever the community decides to do with a given piece of cardboard.

All of that is true, and none of it is useful if you want to measure which Magic cards are good.

## The resource management argument

Here's what makes an objective foundation possible despite the above: Magic is, at its core, a resource management game. Every card costs something, usually mana, to play. Mana is the game's universal currency. You and your opponent are both drawing from similar wells — one mana-fungible land played per turn, accumulating over the course of a game, spent on abilities which advance your game state or impede your opponent's.

This structure gives us a denominator that doesn't change. A card that costs three mana in 1993 and a card that costs three mana in 2024 are both asking you to make the same investment. What varies is what they give you in return.

So here's the heuristic: **a card is "good" to the extent that it delivers more ability per mana spent than its contemporaries and predecessors at the same cost.** A card that gives you flying, first strike, lifelink, and protection from two creature types for five mana (Baneslayer Angel, 2009) is more efficient than a card that gives you flying and vigilance for the same five mana (Serra Angel, 1993). One is objectively a better deal in the currency of the game.

This isn't a complete theory of card quality. It says nothing about alternate casting costs, nothing about synergy, nothing about the specific matchups where a conditional removal spell outperforms a raw one, nothing about the ceiling of a card that wins the game when it goes unanswered. But it's an objective first foundation — one that's measurable, consistent across eras, and doesn't depend on tournament results we haven't collected yet. Post 3 will introduce tournament data and let us test whether the competitive Magic community, in aggregate, agrees with our heuristic.

## The methodology

To measure ability-to-cost ratio, I needed to count two things for each card: what it costs, and what it does.

**Cost** is straightforward: converted mana cost (CMC), which Scryfall provides as a structured field. A card costing `{2}{W}` has CMC=3. Cards with X in their cost (like `{X}{G}`) treat X as 0 in CMC, so their cost is the non-X floor — I track X-count separately and flag these cards rather than trying to guess the "intended" value of X.<sup>1</sup>

**Abilities** come from two sources:

*Layer 1: Scryfall's keywords field.* Scryfall maintains a structured `keywords` array for each card — an explicit list of named keyword abilities: flying, deathtouch, haste, trample, lifelink, vigilance, first strike, double strike, hexproof, indestructible, ward, and roughly 170 others, all drawn from the Comprehensive Rules' section 702. This is clean, complete, and requires no parsing. A card's `keyword_count` is simply the length of this array.

*Layer 2: Regex classification against oracle text.* Scryfall's keywords field captures named keywords, but a large portion of what cards *do* lives in free-form oracle text: "draw a card," "create a 1/1 token," "counter target spell," "search your library for a land card." I classify this oracle text using a set of regex patterns against 18 ability categories: card advantage, removal, direct damage, tokens, counters, ramp, graveyard, counterspell, discard, stax, tutor, life, pump, protection, evasion, steal, copy, and blink.

Before running patterns, I strip reminder text (the parenthetical rules explanations like *(Flying means this creature can't be blocked except by creatures with flying or reach.)*) and remove the Scryfall keywords themselves from the oracle text, to avoid double-counting abilities already captured by Layer 1.

A card's **total ability count** is keyword count plus the number of distinct oracle-text categories matched. Its **abilities-per-CMC ratio** divides that total by CMC.

One important note on what this measures: the categories are unweighted. A counterspell and a life gain spell each contribute 1 to a card's ability count, even though any experienced player would tell you counterspells are worth more. That's a deliberate choice at this stage — equal weighting is simpler, more defensible, and immune to the subjectivity I'm trying to avoid. Post 3's tournament overlay will be where we find out if the weighting matters empirically.<sup>2</sup>

## The results

### Keywords per cost over time

The simplest version of the story: how many keywords does the average card at a given mana cost carry, and has that changed?

![Average keyword count divided by CMC for non-land cards, 1993–present, showing a rising trend](/images/mtg-card-power/keywords_per_cmc.png)

The trend is initially gradual: through the '90s and 2000s, keywords per mana value held roughly flat. Then, starting around 2012–2014, it climbs. A card printed in 2025 carries about twice the keyword density per mana spent as one printed in 1993: **0.35 keywords per CMC vs. 0.17 in 1993.**

### Abilities per cost over time

Adding the oracle-text layer makes the signal stronger:

![Total abilities (keywords + oracle categories) per CMC, 1993–present, with per-CMC breakdown for 2-mana, 3-mana, and 4-mana cards](/images/mtg-card-power/total_abilities_per_cmc.png)

The left panel shows the overall trend. The right panel breaks it out by mana cost to confirm that the trend isn't an artifact of the card pool shifting toward cheaper or more expensive cards. At every mana value, cards are doing more than they used to.

The CMC=3 numbers are a good anchor: the average three-mana card in 1993 had **1.33 abilities**. By 2025 it had **2.31 — a 74% increase.** That's not a marginal drift. A player from 1993 dropped into a 2025 game would be undercosting their cards in every exchange.

### Where the creep has happened

Not all ability types have gotten cheaper at the same rate. This chart shows average CMC of cards carrying each oracle-text ability category — a downward trend means that category has been steadily attached to cheaper cards:

![Small multiples showing average CMC per ability category over time](/images/mtg-card-power/creep_by_ability_type.png)

A few patterns stand out. Ramp (mana acceleration and cost reduction) has gotten significantly cheaper: effects that used to live on four- and five-mana cards now appear routinely on two-mana ones. Card advantage has similarly migrated downward. Direct damage has actually held fairly steady, which tracks with the competitive community's intuitions: Lightning Bolt at one mana has never been printed with an upgrade.

### The distribution shift

The trend chart shows averages; the distribution chart shows the full shape of what's changed:

![Side-by-side histograms of ability count for 2-mana and 3-mana cards, comparing 1993–2000 to 2015–2025](/images/mtg-card-power/distribution_shift.png)

At CMC=2, the average card from 1993–2000 had **1.39 abilities**. The same mana cost from 2015–2025 averages **1.99**. At CMC=3, the shift is from **1.36 to 2.12**. The distributions, however, tell the full story: the old distributions peak at 1 ability (vanilla and near-vanilla creatures were the norm at low mana costs). The modern distributions shift their mass to 2 and 3 abilities. Vanilla creatures haven't disappeared: they're still printed, but they're no longer representative of what a given mana cost buys in competitive play.

## The leaderboard

The heuristic exists, so let's use it. These are the top cards by abilities-per-CMC at each mana cost — "best one-drop," "best two-drop," and so on. Ranking within CMC brackets is fairer than a single global list, because a 1-mana card with 3 abilities doesn't compete with a 3-mana card with 3 abilities on the same terms.

Two caveats before the tables. First, X-cost cards are excluded — their floor CMC understates the real investment, so ranking them against fixed-cost cards isn't meaningful. Second, the top slots at each CMC are heavily occupied by cards from Universes Beyond crossover sets (Fallout, Doctor Who, Avatar, Final Fantasy). Those sets tend to pack multiple set-specific named keywords — Stimpak, RadAway, Check Map — onto individual cards. Under equal weighting, those keywords count the same as Flying or Deathtouch. That's a real limitation: the methodology correctly identifies mechanical complexity but doesn't distinguish between a keyword that does something generically powerful and one that does something specific to one set's flavor. Both caveats are already flagged in the methodology notes; the leaderboard just makes them concrete.

### Best one-mana cards

| Card | Year | Abilities | Ratio | Keywords + categories |
|---|---|---|---|---|
| Three Steps Ahead | 2024 | 6 | 6.0 | Spree; card advantage, tokens, counterspell, copy |
| Cling to Dust | 2020 | 5 | 5.0 | Escape; card advantage, removal, graveyard, life |
| Ocelot Pride | 2024 | 5 | 5.0 | Lifelink, Ascend, First strike; tokens, copy |
| Deathrite Shaman | 2012 | 4 | 4.0 | removal, ramp, graveyard, life |
| Mausoleum Wanderer | 2016 | 3 | 3.0 | Flying; counterspell |

The crossover cards dominate the raw top of the CMC=1 list, but once you look past them, the methodology converges on cards experienced players already know are strong. Deathrite Shaman was banned in both Modern and Legacy — the consensus view is that it does too much for one mana. The heuristic independently scores it among the highest non-crossover one-drops. Three Steps Ahead is a Spree spell (multiple selectable modes on a single card) that sees play in competitive formats. Mausoleum Wanderer is a one-mana flying creature that can counter spells and scales with your board — a card that briefly warped Standard. The methodology didn't know any of that.

### Best two-mana cards

| Card | Year | Abilities | Ratio | Keywords + categories |
|---|---|---|---|---|
| Old Fogey | 2004 | 11 | 5.5 | Landwalk, Flanking, Fading, Protection, Banding, Plainswalk, Rampage, Phasing, Echo, Cumulative upkeep |
| Everything Pizza | 2026 | 7 | 3.5 | card advantage, direct damage, counters, ramp, discard, tutor, life |
| Dennick, Pious Apprentice | 2021 | 6 | 3.0 | Flying, Lifelink, Investigate, Transform, Disturb |
| Charming Scoundrel | 2023 | 6 | 3.0 | Role token, Treasure, Haste; card advantage, tokens, discard |
| Path to the World Tree | 2021 | 6 | 3.0 | card advantage, direct damage, tokens, ramp, tutor, life |

Old Fogey is the most useful result on this table. It's a parody card printed in Unhinged specifically as an homage to old-school keywords by deliberately packing every such keyword onto one body. The methodology scores it first among all two-drops not because it's a good card (it isn't; most of those abilities actively hurt you) but because it was designed to illustrate exactly the phenomenon being measured. If the methodology didn't score Old Fogey highly, something would be wrong with the methodology. That the player consensus is that it's unplayable points directly at the methodology's equal-weighting problem: keywords aren't equivalent, and some of Old Fogey's are actively negative. This is the footnote 2 problem made visible.

Everything Pizza matches seven of the 18 oracle-text categories at CMC=2. That's the power creep story in one data point.

### Best three-mana cards

| Card | Year | Abilities | Ratio | Keywords + categories |
|---|---|---|---|---|
| Odric, Blood-Cursed | 2021 | 11 | 3.67 | Deathtouch, Lifelink, Reach, Indestructible, Hexproof, First strike, Haste, Trample, Menace, Double strike; tokens |
| Blast from the Past | 2004 | 7 | 2.33 | Madness, Buyback, Flashback, Cycling, Kicker; direct damage, tokens |
| Graveyard Trespasser | 2021 | 6 | 2.0 | Daybound, Ward, Nightbound; graveyard, discard, life |
| Sword of Once and Future | 2023 | 6 | 2.0 | Surveil, Equip; ramp, graveyard, pump, protection |
| Jace, Mirror Mage | 2020 | 6 | 2.0 | Scry, Kicker; card advantage, tokens, counters, copy |

Odric ranks first because his oracle text lists keywords as conditions: "create a token for each keyword ability among creatures you control". Our methodology counts those listed keyword names as the card's own abilities. That's a genuine classification edge case. The card is strong, but not for the reasons the score implies.

Blast from the Past is more interesting: it has five different alternate casting mechanics plus deals damage and makes a token, all at three mana. It's a deliberately absurdist Un-set design, but its score here reflects exactly what's being measured. A player from 1993 comparing it to a contemporary three-mana spell would be confused by what they were looking at.

Graveyard Trespasser and Sword of Once and Future are legitimate competitive cards. Both saw or see play in Standard and Pioneer. Getting them right at this CMC is the methodology working as intended.

### Best four-mana cards

| Card | Year | Abilities | Ratio | Keywords + categories |
|---|---|---|---|---|
| Elusen, the Giving | 2023 | 8 | 2.0 | Flying, Lifelink, Vigilance, Treasure, Haste; card advantage, tokens, life |
| Nahiri, the Unforgiving | 2023 | 7 | 1.75 | Compleated; card advantage, removal, tokens, graveyard, discard, copy |
| Life of the Party | 2022 | 7 | 1.75 | Goad, First strike, Haste, Trample; tokens, pump, copy |
| Eradicator Valkyrie | 2021 | 6 | 1.5 | Flying, Lifelink, Hexproof, Boast |
| The Legend of Kuruk | 2025 | 6 | 1.5 | Transform, Exhaust, Waterbend, Scry; card advantage, blink |

Nahiri is a legitimately strong planeswalker that sees Pioneer play. The methodology gives her second at CMC=4. She's behind Elusen, a Commander-facing group-hug card that does a lot but in a slower, less competitive context. The ordering is imperfect, but it gets the direction right: both are modern cards that do substantially more than four-mana cards from earlier eras.

### Best five-or-more-mana cards

| Card | Year | CMC | Abilities | Ratio | Keywords + categories |
|---|---|---|---|---|---|
| Tamiyo, Compleated Sage | 2022 | 5 | 8 | 1.60 | Compleated; card advantage, removal, tokens, ramp, graveyard, stax, copy |
| Chromanticore | 2014 | 5 | 7 | 1.40 | Flying, Lifelink, Vigilance, First strike, Trample, Bestow; pump |
| Loot, the Pathfinder | 2025 | 5 | 7 | 1.40 | Vigilance, Haste, Double strike; card advantage, direct damage, ramp |
| Lunar Hatchling | 2023 | 6 | 8 | 1.33 | Flying, Landcycling, Trample, Basic landcycling, Escape, Typecycling, Cycling; graveyard |
| Cosmic Spider-Man | 2025 | 5 | 6 | 1.20 | Flying, Lifelink, First strike, Haste, Trample |

Tamiyo, Compleated Sage is the clearest validation in the dataset. When she was printed in 2022, the competitive consensus was that she was too powerful — she draws cards, creates tokens, and ultimately generates an emblem letting you cast spells for free from your graveyard. She was actively discussed as a potential ban candidate in Pioneer. Our methodology gives her the top score among all five-drops, with eight distinct abilities at ratio 1.60. It doesn't know any of that. It just counts.

### By color and card type

**Color leaders** (highest abilities-per-CMC):

White: Ocelot Pride (2024, CMC=1, ratio 5.0). Blue: Three Steps Ahead (2024, CMC=1, ratio 6.0). Black: Cling to Dust (2020, CMC=1, ratio 5.0). Red: Reckless Lackey (2024, CMC=1, ratio 5.0 — first strike, haste; card advantage, tokens). Green: for competitive purposes, Deathrite Shaman (2012, CMC=1, ratio 4.0) — the actual #1 green card by this metric is HONK!, a Doctor Who novelty instant, which tells you something about the crossover-card problem.

**Card type leaders:**

Creature: Odric, Blood-Cursed (CMC=3, ratio 3.67, with the classification caveat above). Instant: Three Steps Ahead (CMC=1, ratio 6.0). Sorcery: Shamble Back (2016, CMC=1, ratio 4.0 — removal, tokens, graveyard, life). Enchantment: Three-way tie between Sentinel's Eyes, Escape Velocity, and Mogis's Favor — all 2020 Escape enchantments at CMC=1, ratio 4.0. Planeswalker: Jace, Mirror Mage and Ob Nixilis, the Adversary tied at CMC=3, ratio 2.0.

### The full dataset

Every non-land card in the catalog, ranked by abilities-per-CMC, with color, card type, keywords, oracle-text categories, and score:

**[Download: mtg-card-power-rankings.csv (27,743 cards)](/data/mtg-card-power-rankings.csv)**

Filter it, sort it, disagree with it. That's the point.

## What this sets up

The ability-to-cost ratio gives us a principled, data-grounded definition of "efficient" — one that's agnostic to format, meta, and the subjective judgments of any particular player or era. By that definition, Magic cards have gotten significantly more efficient over the past thirty years.

We already know our methodology has limitations. What we don't yet know is whether those limitations led us astray from cards which are "good" by virtue of seeing consistent competitive play. Tournament data will bridge that gap. If our heuristic is doing real work, cards that score well on ability-to-cost ratio should be more likely to show up in competitive decks.

We'll do that evaluation in Post 3. I'll pull historical tournament results and overlay them against our ability-to-cost scores. The goal is to see whether, at each CMC and color, our high-scoring cards see tournament play. If we don't see that result (for example, maybe we see tournament-popular cards clustering around a narrow band of costs, regardless of ability-to-cost ratio), then our heuristic, while real, may be inadequate at describing "good" cards. We'll shuffle up and try again!

---

## Methodology notes

**<sup>1</sup> X-cost spells and alternative costs.** Cards with X in their mana cost (e.g., `{X}{R}`) have CMC that treats X as 0, matching Scryfall's convention. I track X-count separately — a card costing `{X}{X}{G}` scales at twice the rate of one costing `{X}{G}`. X-cost cards are included in the analysis but marked distinctly. Cards with alternative casting costs (Force of Will, Force of Negation) present a harder problem: they have two real costs, and which is "cheaper" depends on game state. I record both but defer the "which cost matters?" question to Post 3 where tournament data will ground it.

**<sup>2</sup> The equal-weighting assumption.** The current model counts a tutor and a life-gain spell as the same +1 contribution to ability count. That's obviously false in practice — tutors are among the most powerful effects in the game, and life gain is frequently dismissed as low-impact. The reason to proceed with equal weighting now is that introducing weights requires a source of weights: either expert judgment (which defeats the point of measuring this objectively) or empirical data about which abilities correlate with competitive success (which is what Post 3 is for). The unweighted count is the right first pass.

**<sup>3</sup> The "other" category.** After classifying oracle text against the 18-category taxonomy, approximately 25% of non-land cards have text that doesn't match any category pattern. This bucket contains two types: cards with genuinely niche or complex effects that don't map to the standard taxonomy (real "other"), and cards with triggered ability structures — "Whenever X, do Y" — where the trigger condition doesn't encode the effect category without clause-level parsing. The "other" cards still contribute 1 to semantic ability count when they have non-empty oracle text, which may slightly overstate ability counts for cards in this bucket. The bias is consistent across eras, so the trend analysis should be directionally reliable even if the absolute numbers are imprecise.

**<sup>4</sup> Color identity.** Colored mana pips constrain a card's playability independently of its raw CMC. `{U}{U}{U}` is harder to cast than `{3}` in most decks, even at the same mana value. This analysis doesn't model that cost — CMC is the only cost axis used. Color identity is a real factor in evaluating cards practically, and it's left for future work.
