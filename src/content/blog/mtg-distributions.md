---
title: "Thirty Years of Magic Cards, Measured"
description: "How do 33 years of card printing look as data? Stranger than you'd expect."
pubDate: "2026-04-03"
---

In the '00s my brother, cousins, and I played as much Magic: The Gathering as the next tween. I stopped in high school, wrongly deciding to spend my free time elsewhere. My brother reintroduced me to The Beautiful Game during covid. As I re-learned Magic's actual rules, and un-learned some truly inspired kitchen table ones, I got into the game all over again for the same reasons many do. There's no other game which blends such an elegant ruleset with choose-your-own-adventure pace of play: despite a well-earned reputation for intricacy, the feel of Magic's many formats ranges from pickup basketball to speed chess. I won't even bother describing the somatic experience of cracking open a new pack of cards. If you're among the initiated, it goes without saying.

As I came to appreciate what this game has always been, I also felt how much it has changed: more sets, more mechanics, harder to keep up. However, feelings aren't measurements. I wanted to see what the data actually said.

So I pulled the full card catalog from [Scryfall](https://scryfall.com), which maintains a daily-updated database of every Magic card ever printed, and started asking questions.

## The scale is larger than you think

Magic has been running since 1993. As of this analysis (April 2026), Scryfall contains **33,998 unique card designs** across **377 sets**.

The unique card count is probably higher than your intuition suggested. Mine had it somewhere around 15,000 before I looked. The true number is hard to estimate because most players see only a slice of the card pool at any given time — the sets that were legal when they played, the cards their friends owned, and whatever showed up in tournaments they followed.

Thirty-four thousand is the *full* catalog: every format, every era, going back to Alpha in 1993.

## The typical set is not what you'd expect

377 sets across 33 years is also more than most people would guess. That's roughly 11 sets per year on average, but the average is misleading.

Here's the distribution of set sizes:

![Distribution of Magic set sizes, showing a right-skewed histogram with mean at 90 and median at 64](/images/mtg-distributions/set_size_distribution.png)

The **mean** set size is 90 cards. The **median** is 64. That 40% gap between them is a signal: the distribution is skewed, and the mean is being pulled upward by outliers.

On the right tail, you have massive reprint sets: Commander Masters, at 481 cards, is the largest in the dataset. These sets exist to reprint expensive, hard-to-find cards at scale. They contain hundreds of cards, but there are only a handful of them.

On the left, there's a dense cluster of tiny sets: Secret Lairs (limited-run promotional sets, typically 5–10 cards), Commander preconstructed decks, and various special releases. None of these look like traditional Magic sets, but they all count.

The median is the more honest number here. A "typical" Magic set contains around 64 cards. The 250-card main-set expansions you might think of as "normal" are a minority of the total set count.

This is a useful pattern to recognize in data generally: when the mean and median diverge significantly, there's a story in the distribution. Here, the story is that Wizards has been releasing a very large number of very small sets alongside a small number of very large ones. The mean gets dragged toward the large sets even though they're rare.

## The acceleration — and how to measure it correctly

Knowing the set count is one thing. Seeing how card volume has changed over time is another. But measuring it correctly requires some care.

Scryfall picks one canonical printing, typically the most recent, per unique card. That means a card first printed in 1993 and reprinted in a 2024 Commander precon gets credited to 2024 in a naive count. To find out how many genuinely *new* card designs were introduced each year, you need to track the earliest appearance of each design across all printings.

Here's what the naive count and the corrected count look like side by side:

![Two-line chart comparing net-new card designs vs. oracle canonical count per year](/images/mtg-distributions/net_new_vs_canonical.png)

The gap matters. In 2024, a naive count would attribute 3,660 unique cards to that year. The true net-new figure, new designs appearing for the first time, is **2,538**. The difference representing old designs being reprinted into new sets is **~1,100 cards. A 44% difference!** That gap has widened significantly since 2017, which is itself a finding: reprints are not just increasing in absolute terms, they're growing as a share of what gets released each year.

Using the corrected numbers:

![Net-new Magic card designs per year, 1993–2025](/images/mtg-distributions/cards_per_year.png)

For roughly the first two decades of Magic, 1993 through 2013, Wizards introduced somewhere between 400 and 700 net-new designs per year. Then it starts climbing.

**Net-new card introductions peaked in 2022 at 2,604 designs** — about five times the historical baseline. 2023, 2024, and 2025 remain in the 2,200–2,600 range. Whatever caused the acceleration appears to be a sustained structural shift, not a one-year spike.

What changed? A few compounding factors: Commander became a year-round product line (introducing new legendary cards with every release), Secret Lairs launched in 2019 as a direct-to-consumer channel with no fixed release schedule, and Universes Beyond brought licensed crossovers that each contribute new-to-Magic designs.

## What kinds of cards are being introduced?

The volume increase is the top-line story. The composition of what's being introduced is at least as interesting.

### Color complexity

Magic's five colors (white, blue, black, red, and green) have always been roughly balanced in terms of how many cards each gets. But the *complexity* of color identity (mono, multi, or colorless) has shifted:

![Stacked area chart showing percentage of new card designs by color complexity over time](/images/mtg-distributions/color_complexity_over_time.png)

Multicolor cards — cards requiring two or more colors to cast — have grown as a share of new designs. This tracks with the game's design history: the Ravnica sets (2005, 2012, 2019) each flooded the card pool with gold cards. Commander also heavily favors multicolor identities, since the format's deck-building rules are organized around color identity.

### Card type composition

Across the game's history, creatures have always been the most common card type. But how much they dominate has changed:

![Stacked area chart showing percentage of new card designs by card type over time](/images/mtg-distributions/type_breakdown_over_time.png)

Creatures represented 36% of new designs in 1993. By 2020 they were 61%, and have settled around 57% in recent years. Wizards has been explicit about this, talking openly about making creatures more powerful and central to gameplay over the past two decades. The data confirms it.

One thing visible in the type chart: Planeswalkers, introduced in 2007, appear as a small but consistent slice of new designs going forward. They're not dominant numerically, but they've been a consistent presence since their introduction.

### The legendary explosion

This trend has been noticed before: [Draftsim](https://draftsim.com/mtg-fewer-legendary-creatures/) has tracked legendary creature counts by era, and [sjschmitt's MTG Set Analysis](https://sjschmitt.github.io/MTG_Set_Analysis/) charts legendary percentage per set using Scryfall data. What the reprint-corrected methodology adds is a cleaner signal: by counting only the year a design *first appeared*, the jump is attributable to new creative output rather than reprints of old legends cycling into new sets.

Perhaps the starkest finding of any of these analyses:

![Dual-axis chart showing legendary card count and percentage over time](/images/mtg-distributions/legendary_over_time.png)

In 1993, Magic had essentially zero legendary cards. The legendary supertype existed, but was used sparingly as a mark of prestige for a handful of powerful, storied characters. Through the 2000s, legendary remained a minority: roughly 3–6% of new designs in any given year.

Then, around 2017–2020, it jumped. **By 2020, 19% of all new card designs were legendary. Things have stayed near that level since.** In 2024 specifically, 481 of 2,538 net-new designs (again, 19%) were legendary.

The driver is Commander. The format, which builds decks around a specific legendary creature as a "commander," incentivizes Wizards to constantly produce new legendary cards that players will want to build around. Every Commander product introduces a roster of new legendary creatures and planeswalkers. At 19% of the card pool, legendary is no longer a mark of rarity. It's a design strategy.

## Cards have also gotten harder to read

The volume and composition shifts are structural. There's also a per-card complexity trend running underneath them, one that others have measured before. [SumNeuron at Commander's Herald](https://commandersherald.com/a-basic-metric-of-complexity-creep/) did a Scryfall-based complexity analysis in 2021, and Wizards itself [acknowledged internally](https://magic.wizards.com/en/news/card-preview/word-heist-theros-beyond-death-caper-2020-01-07) that Throne of Eldraine was pushing word-count records. The finding isn't new, but the time series below covers the full game history and uses median rather than mean, which is more robust to the increasingly long-tail of rules-heavy cards.

![Median card text length in characters by year, excluding lands](/images/mtg-distributions/complexity_creep.png)

This chart shows the median oracle text length (in characters) for new designs each year, excluding lands, which typically have little or no rules text.

The long plateau from roughly 1997 through 2018, about 20 years where median text length held steady around 100–135 characters, reflects the game stabilizing its vocabulary. Keywords like "flying," "trample," and "haste" let designers compress a lot of meaning into a single word.

Post-2019, the line climbs sharply to around 190 characters, roughly a 50% increase over the historical plateau. This coincides with mechanics that resist keyword compression: Sagas (with numbered chapter abilities), modal double-faced cards (effectively two cards), and adventure cards. Each requires explicit text that a single keyword can't replace.

More cards, more complex cards, and as of 2020, nearly one in five of them legendary.

## What this sets up

There are now ~34,000 unique Magic card designs. Roughly 2,400–2,600 new ones are introduced each year.

For any collectors or players trying to evaluate Magic cards, this volume poses an obvious problem: which of those cards are actually worth caring about? Scryfall can tell us what cards *exist*, but it can't tell us which ones are *good*.

Per my brother's feedback on my early decks, neither can I, but in subsequent posts I'll certainly try!
