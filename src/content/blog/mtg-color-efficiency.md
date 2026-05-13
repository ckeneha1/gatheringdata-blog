---
title: "Does Color Identity Actually Predict Efficiency?"
description: "A permutation test on 27,000 Magic cards to find out how much color really explains."
pubDate: "2026-05-11"
draft: true
---

[Post 2](./mtg-card-power) made a claim in passing: mana cost is a far stronger predictor of card efficiency than color, but Blue pulls ahead — particularly at low CMC, where it averages 13% more abilities per mana than Green. That's a meaningful gap in a game where small margins shape formats.

But "meaningful gap" and "statistically rigorous" aren't the same thing. This post does the work to settle the question properly: does color identity actually explain card efficiency, or is the Blue advantage something that could have shown up in a random dataset?

## Why not just run an A/A test?

You might reasonably ask: why not take the simple path? Split the cards into Blue and non-Blue, bootstrap random samples from each group a few thousand times, compute a Z-score for the mean difference, and call it done. If the Z-score is large enough, Blue is real.

That approach works. But it answers a narrower question than the one we actually care about.

Think of it this way. Imagine you have 27,000 Magic cards laid out on a table, each with a color tag. You want to know: **does the color tag carry information about how efficient the card is?** A bootstrap Z-score for Blue vs. non-Blue is like asking "does this one specific tag tell me something?" You'd have to run the same test six more times — once for each other color pair — and then figure out how to combine the results.

A permutation test asks the question once, across all seven colors simultaneously: *if I randomly scrambled every card's color tag, how often would I see color groups as different from each other as the real ones are?* Run that shuffle 10,000 times and you get a full picture of what "color doesn't matter" looks like. Compare the real observed difference to that picture. If the real value sits way out in the tail — far past every random shuffle — that's your answer.

The other thing the permutation test gives you is **η² (eta-squared)**: a single number for how much of the total variance in efficiency is explained by color. That's the quantity we actually want. A Z-score tells you whether a gap is distinguishable from noise. η² tells you how big that gap is relative to everything else going on. Both matter; we want both.

(We do run the pairwise comparisons afterward — Blue vs. each other color individually — so nothing gets buried.)

## Methodology

The analysis uses the 27,742 non-land cards from the [Post 2 dataset](/data/mtg-card-power-rankings.csv), scored by abilities-per-CMC. Before testing color, we remove CMC's dominant effect by replacing each card's raw efficiency with its **residual**: the difference between its abilities-per-CMC and the average for cards at the same CMC. This isolates the color signal from the mana-cost signal, which would otherwise swamp everything.

We then compute η² for the real color assignments and compare it to 10,000 permuted versions where color labels are randomly shuffled. The permutation p-value is the fraction of shuffles that produce η² as large or larger than the observed value.

## Results

### Color's effect is statistically real — and genuinely small

Zero of 10,000 random shuffles produced as much color-group variance as the real color assignments.

![Histogram of permuted eta² values with observed value far to the right](/images/mtg-color-efficiency/color_null_distribution.png)

The observed η² is **0.0106** — color explains about **1.1% of efficiency variance** after accounting for CMC. By conventional benchmarks (small ≈ 0.01, medium ≈ 0.06), that's a small effect. Statistically unambiguous; practically modest.

The honest read: the heatmap in Post 2 wasn't lying, but it wasn't telling the whole story either. The Blue advantage at CMC 1 is real. It's also the kind of real that explains 1% of what's going on after you account for mana cost.

### The Multicolor anomaly

Here's the part that didn't appear in the heatmap:

![Lollipop chart of per-color residual means](/images/mtg-color-efficiency/color_residual_means.png)

Multicolor cards punch further above their CMC average than any other color — including Blue. Their mean residual is **+0.091**, more than twice Blue's **+0.035**. Every other color sits below zero.

Here's what that number does *not* mean: Multicolor is not the most efficient color to play. On the raw metric — abilities-per-CMC with no adjustment — Multicolor sits at **0.674**, the lowest of all seven colors. Blue is at 0.781. Red is at 0.726. Multicolor is last. The high residual and the low raw mean are not a contradiction; they're the same thing described from two angles.

The explanation is structural. Multicolor cards require you to produce two or more colors of mana, a real cost that the CMC number ignores entirely. Designers compensate by making Multicolor cards more text-dense: a three-mana gold card usually does more than a three-mana mono-blue card, because it has to justify the added constraint of its second color pip. What this means in practice is that Multicolor cards tend to cluster at higher CMC tiers where the average efficiency is already lower, and within those tiers they overperform the bucket average. Our metric sees the extra text and calls it efficiency. Whether it actually *is* more efficient — or just more complex to compensate for a constraint the model doesn't measure — is the right question to ask, and the answer is: mostly the latter.

**The practical implication:** if you're choosing a color to maximize text per mana, the +0.091 Multicolor residual is not evidence that Multicolor is the right pick. It's evidence that Multicolor cards are internally consistent with the design logic of needing to earn their pip cost. Blue is still the mono-color leader (+0.035), and it doesn't carry the hidden cost. This limitation is the same one flagged in [Post 2's footnote 4](./mtg-card-power#methodology-notes): the metric treats all mana as equivalent when it isn't.

### What "1% of variance" looks like

To make the effect size tangible:

![Density curves for Blue, Red, and Multicolor efficiency distributions](/images/mtg-color-efficiency/color_density_curves.png)

The three distributions are nearly identical in shape. The peaks overlap almost perfectly. What differs is where each mean sits — by a few hundredths on the residual axis, well within a single standard deviation of any group. That's the 1%.

Red has a slightly fatter left tail, meaning more Red cards with zero abilities relative to their CMC — creature-heavy sets where vanilla or French vanilla cards (no abilities beyond basic keyword(s)) are more common in the color. That's a real design pattern, but it shows up as a shape difference rather than a mean difference.

## Summary

| | Value |
|---|---|
| η² (marginal, ignoring CMC) | 0.0032 (0.32%) |
| η² (CMC-residualized) | **0.0106 (1.06%)** |
| Permutation p-value | < 0.001 |
| Blue vs. Red Cohen's d | 0.159 (small) |
| Blue vs. Green Cohen's d | 0.144 (small) |

Color identity predicts card efficiency. The signal is statistically unambiguous across 27,000 cards and survives 10,000 attempts to destroy it with random shuffles. The effect size is small — about 1% of remaining variance once CMC is accounted for. Blue leads among mono-colors. Multicolor's residual is highest, but that reflects a design compensation for color pip costs the model doesn't measure — not an argument for playing gold cards.

The Post 2 heuristic holds up: mana cost is what drives efficiency. Color is a real but secondary signal. Blue is the right color to play if you want to maximize text per mana, and now there's math behind that.
