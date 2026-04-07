---
title: "What Does a Mana Cost Buy You?"
description: "Building a data-driven definition of 'good' — and finding thirty years of power creep hiding in plain sight."
pubDate: "2026-04-13"
---

[Post 1](./mtg-distributions) established the supply side: Magic prints roughly 2,400–2,600 new card designs per year, cards have gotten longer, and as of early 2026 the total catalog sits at just under 34,000 unique designs. The closing question was the obvious one — which of those cards are actually worth caring about? In other words, which are *good*?

My brother asked me the same question in a less academic register when he reviewed my early decks.

## "Good" is a moving target

The obvious complication with "good" in Magic is that the definition depends on almost everything around it: which format you're playing, which decks dominate the meta that week, what synergies your deck enables, whether your opponent is on aggro or combo. A card that belongs in every Pioneer sideboard might be unplayable in Standard. A card that's been rotting in bulk bins for a decade can suddenly go from $0.50 to $40 the week a new combo deck gets a key piece printed.

Even the game's designers resist the framing. Cards aren't designed in isolation — they're designed relative to what already exists, what the format needs, and what the story calls for. "Good" in that context is not a fixed standard but a negotiation between design intent, card pool state, and whatever the community decides to do with a given piece of cardboard.

All of that is true, and none of it is especially useful if you want to measure whether Magic cards have gotten more powerful over time.

## The resource management argument

Here's what makes an objective foundation possible despite the above: Magic is, at its core, a resource management game. Every card costs mana to play. Mana is the universal currency. You and your opponent are both drawing from the same well — a land-drop per turn, accumulating over the course of a game — and spending that mana on abilities which advance your game state and impede theirs.

This structure gives us a denominator that doesn't change. A card that costs three mana in 1993 and a card that costs three mana in 2024 are both asking you to make the same investment. What varies is what they give you in return.

So here's the heuristic: **a card is "good" to the extent that it delivers more ability per mana spent than its contemporaries and predecessors at the same cost.** A card that gives you flying, first strike, lifelink, and protection from two creature types for five mana (Baneslayer Angel, 2009) is more efficient than a card that gives you flying and vigilance for the same five mana (Serra Angel, 1993). One is objectively a better deal in the currency of the game.

This isn't a complete theory of card quality. It says nothing about synergy, nothing about the specific matchups where a conditional removal spell outperforms a raw one, nothing about the ceiling of a card that wins the game when it goes unanswered. But it's an objective first foundation — one that's measurable, consistent across eras, and doesn't depend on tournament results we haven't collected yet. Post 3 will introduce tournament data and let us test whether the community, in aggregate, has converged on the same judgment.

## The methodology

To measure ability-to-cost ratio, I needed to count two things for each card: what it costs, and what it does.

**Cost** is straightforward: converted mana cost (CMC), which Scryfall provides as a structured field. A card costing `{2}{W}` has CMC=3. Cards with X in their cost (like `{X}{G}`) treat X as 0 in CMC, so their cost is the non-X floor — I track X-count separately and flag these cards rather than trying to guess the "intended" value of X.<sup>1</sup>

**Abilities** come from two sources:

*Layer 1: Scryfall's keywords field.* Scryfall maintains a structured `keywords` array for each card — an explicit list of named keyword abilities: flying, deathtouch, haste, trample, lifelink, vigilance, first strike, double strike, hexproof, indestructible, ward, and roughly 170 others, all drawn from the Comprehensive Rules' section 702. This is clean, complete, and requires no parsing. A card's `keyword_count` is simply the length of this array.

*Layer 2: Regex classification against oracle text.* Scryfall's keywords field captures named keywords, but a large portion of what cards *do* lives in free-form oracle text: "draw a card," "create a 1/1 token," "counter target spell," "search your library for a land card." I classify this oracle text using a set of regex patterns against 18 ability categories — card advantage, removal, direct damage, tokens, counters, ramp, graveyard, counterspell, discard, stax, tutor, life, pump, protection, evasion, steal, copy, and blink.

Before running patterns, I strip reminder text (the parenthetical rules explanations like *(Flying means this creature can't be blocked except by creatures with flying or reach.)*) and remove the keyword names themselves from the oracle text, to avoid double-counting abilities already captured by Layer 1.

A card's **total ability count** is keyword count plus the number of distinct oracle-text categories matched. Its **abilities-per-CMC ratio** divides that total by CMC.

One important note on what this measures: the categories are unweighted. A counterspell and a life gain spell each contribute 1 to a card's ability count, even though any experienced player would tell you counterspells are worth more. That's a deliberate choice at this stage — equal weighting is simpler, more defensible, and immune to the subjectivity I'm trying to avoid. Post 3's tournament overlay will be where we find out if the weighting matters empirically.<sup>2</sup>

## The results

### Keywords per mana value, 1993–present

The simplest version of the story: how many keywords does the average card at a given mana cost carry, and has that changed?

![Average keyword count divided by CMC for non-land cards, 1993–present, showing a rising trend](/images/mtg-card-power/keywords_per_cmc.png)

The trend is gradual and then not. Through the '90s and 2000s, keywords per mana value held roughly flat. Then, starting around 2012–2014, it climbs. A card printed in 2025 carries about twice the keyword density per mana spent as one printed in 1993: **0.35 keywords per CMC vs. 0.17 in 1993.**

### Total abilities per mana value over time

Adding the oracle-text layer makes the signal stronger:

![Total abilities (keywords + oracle categories) per CMC, 1993–present, with per-CMC breakdown for 2-mana, 3-mana, and 4-mana cards](/images/mtg-card-power/total_abilities_per_cmc.png)

The left panel shows the overall trend. The right panel breaks it out by mana cost — confirming that the trend isn't an artifact of the card pool shifting toward cheaper or more expensive cards. At every mana value, cards are doing more than they used to.

The CMC=3 numbers are a good anchor: the average three-mana card in 1993 had **1.33 abilities**. By 2025 it had **2.31 — a 74% increase.** That's not a marginal drift. A player from 1993 dropped into a 2025 game would be undercosting their cards in every exchange.

### Where the creep has happened

Not all ability types have gotten cheaper at the same rate. This chart shows average CMC of cards carrying each oracle-text ability category — a downward trend means that category has been steadily attached to cheaper cards:

![Small multiples showing average CMC per ability category over time](/images/mtg-card-power/creep_by_ability_type.png)

A few patterns stand out. Ramp — mana acceleration and cost reduction — has gotten significantly cheaper: effects that used to live on four- and five-mana cards now appear routinely on two-mana ones. Card advantage has similarly migrated downward. Direct damage has actually held fairly steady, which tracks with the competitive community's intuitions: Lightning Bolt at one mana has never been printed with an upgrade.

### The distribution shift

The trend chart shows averages; the distribution chart shows the full shape of what's changed:

![Side-by-side histograms of ability count for 2-mana and 3-mana cards, comparing 1993–2000 to 2015–2025](/images/mtg-card-power/distribution_shift.png)

At CMC=2, the average card from 1993–2000 had **1.39 abilities**. The same mana cost from 2015–2025 averages **1.99**. At CMC=3, the shift is from **1.36 to 2.12**. But the distributions tell the fuller story: the old distributions peak at 1 ability (vanilla and near-vanilla creatures were the norm at low mana costs). The modern distributions shift their mass to 2 and 3 abilities. Vanilla creatures haven't disappeared — they're still printed, primarily for Limited — but they're no longer representative of what a given mana cost buys.

### The exemplar case

Abstract trends are useful. Specific examples make them concrete.

Compare **Serra Angel** (1993, CMC=5) with **Baneslayer Angel** (2009, CMC=5). Serra has two abilities: flying and vigilance. Baneslayer has four: flying, first strike, lifelink, and protection from Demons and from Dragons. Same cost. Same body (5/5). Fourteen years of printing later, the five-mana angel got twice as many abilities stapled on.

Or compare **Grizzly Bears** (1993, CMC=2) with **Garruk's Companion** (2010, CMC=2). Grizzly Bears is a 2/2 with no abilities — a vanilla creature, the historical baseline. Garruk's Companion is a 3/2 with trample. The body got bigger *and* gained an ability at the same mana cost.

These aren't cherry-picked outliers. They're representative of the direction and magnitude of the trend measured at scale across all 34,000 cards.

## What this sets up

The ability-to-cost ratio gives us a principled, data-grounded definition of "efficient" — one that's agnostic to format, meta, and the subjective judgments of any particular player or era. By that definition, Magic cards have gotten significantly more efficient over the past thirty years.

What we don't yet know is whether the game's competitive community has implicitly arrived at the same conclusion. If the heuristic is doing real work, cards that score well on ability-to-cost ratio should be more likely to show up in competitive decks. If it isn't — if tournament-legal cards cluster around a narrow band of ability-to-cost ratios regardless of era — then the heuristic, while real, may be less predictive of practical quality than the trend suggests.

That's the question Post 3 will answer. I'll pull historical tournament results and overlay them against the ability-to-cost scores built here. The goal is to find out whether there's a threshold — some abilities-per-CMC floor — above which cards reliably see competitive play, and whether that threshold has shifted over time in ways that confirm or complicate the power creep story.

---

## Methodology notes

**<sup>1</sup> X-cost spells and alternative costs.** Cards with X in their mana cost (e.g., `{X}{R}`) have CMC that treats X as 0, matching Scryfall's convention. I track X-count separately — a card costing `{X}{X}{G}` scales at twice the rate of one costing `{X}{G}`. X-cost cards are included in the analysis but marked distinctly. Cards with alternative casting costs (Force of Will, Force of Negation) present a harder problem: they have two real costs, and which is "cheaper" depends on game state. I record both but defer the "which cost matters?" question to Post 3 where tournament data will ground it.

**<sup>2</sup> The equal-weighting assumption.** The current model counts a tutor and a life-gain spell as the same +1 contribution to ability count. That's obviously false in practice — tutors are among the most powerful effects in the game, and life gain is frequently dismissed as low-impact. The reason to proceed with equal weighting now is that introducing weights requires a source of weights: either expert judgment (which defeats the point of measuring this objectively) or empirical data about which abilities correlate with competitive success (which is what Post 3 is for). The unweighted count is the right first pass.

**<sup>3</sup> The "other" category.** After classifying oracle text against the 18-category taxonomy, approximately 25% of non-land cards have text that doesn't match any category pattern. This bucket contains two types: cards with genuinely niche or complex effects that don't map to the standard taxonomy (real "other"), and cards with triggered ability structures — "Whenever X, do Y" — where the trigger condition doesn't encode the effect category without clause-level parsing. The "other" cards still contribute 1 to semantic ability count when they have non-empty oracle text, which may slightly overstate ability counts for cards in this bucket. The bias is consistent across eras, so the trend analysis should be directionally reliable even if the absolute numbers are imprecise.

**<sup>4</sup> Color identity.** Colored mana pips constrain a card's playability independently of its raw CMC. `{U}{U}{U}` is harder to cast than `{3}` in most decks, even at the same mana value. This analysis doesn't model that cost — CMC is the only cost axis used. Color identity is a real factor in evaluating cards practically, and it's left for future work.
