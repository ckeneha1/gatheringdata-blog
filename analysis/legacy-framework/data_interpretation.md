# Data Interpretation Guide

Known biases, failure modes, and correct usage for each metric in the dataset.
Read this before drawing conclusions from the numbers.

---

## The dataset

- **Source**: MTGTop8.com, Legacy format, 2011–2026
- **Scale**: ~13,000 events, ~87,600 deck files, 16 years
- **Critical limitation**: MTGTop8 records top finishers only — typically top 8, sometimes top 16 or 32. It does not record all participants. This is not a full-field dataset.

---

## Placement encoding

MTGTop8 uses non-standard placement numbers. They are not sequential 1–N.

| Placement value | Actual bracket rank |
|---|---|
| 1 | 1st (winner) |
| 2 | 2nd (finalist) |
| 6 | 3rd (semifinal loser) |
| 8 | 4th (semifinal loser) |
| 10 | 5th (quarterfinal loser) |
| 12 | 6th |
| 14 | 7th |
| 16 | 8th |
| 18 | 9th |
| ... | Formula: rank = (placement − 6) // 2 + 3 for even values ≥ 6 |

**What the column names in card_stats.csv actually mean:**

| Column | What it measures |
|---|---|
| `win_rate` | P(deck won the tournament \| card in deck) |
| `final_rate` | P(reached the final \| card in deck) — rank ≤ 2 |
| `semi_rate` | P(reached the semis \| card in deck) — rank ≤ 4 |
| `qf_rate` | P(reached the quarters \| card in deck) — rank ≤ 8 |
| `win_log_or` | Log-odds ratio vs field baseline. Positive = better than average, negative = worse |

The earlier (incorrect) column names `top8_rate` and `top4_rate` were computing top-4 and top-2 respectively due to the non-sequential placement encoding. This was fixed when the encoding was decoded.

---

## win_log_or: when it's useful and when it isn't

**Useful for**: narrow cards that primarily appear in a specific archetype during a specific era.

Examples of meaningful signals:
- Treasure Cruise: +0.656 (appeared almost exclusively in Delver variants when it was broken)
- Sensei's Divining Top: +0.347 (appeared in Miracles during its dominant era)
- Umezawa's Jitte: +0.148 (Death & Taxes staple, consistent performer)

**Not useful for**: cross-archetype staples.

Force of Will (47K appearances, 54% of the field): log-OR = +0.017 — essentially field average. This doesn't mean FoW is mediocre. It means its win rate reflects the average quality of all the diverse archetypes running it. The metric measures archetype quality, not card contribution, for cards this broadly played.

**The threshold**: roughly, cards in >20% of the field will converge to near-zero log-OR regardless of power. For those cards, use inclusion rate and co-occurrence structure instead.

**The Laplace smoothing caveat**: win_log_or uses 0.5 Laplace smoothing to handle cards with 0 wins or 0 non-wins. Cards with very few appearances (near the 20-appearance floor) will have win_log_or estimates dominated by the smoothing prior, not the data. Filter to n ≥ 100 when precision matters.

---

## avg_placement: why we stopped using it

Average placement is biased by popularity. A card in 54% of all recorded decks will necessarily have an average placement near the field median, because its appearances are distributed throughout the bracket. This is a mathematical consequence of coverage, not a signal about card quality.

Confirmed empirically: Pearson r(log total_decks, avg_placement) = +0.223. More appearances correlates with worse (higher) average placement.

avg_placement retains some value for narrow cards (where it's less confounded), but win_log_or is strictly better as a metric and should be used instead. avg_placement is not present in the current card_stats.csv.

---

## Top-of-field selection bias

Because MTGTop8 only records top finishers, the dataset cannot answer:

- "What fraction of all tournament players who ran this card made top 8?" (denominator is missing)
- "Does adding this card to a deck improve its win rate?" (true counterfactual is unavailable)

What the dataset can answer: among decks that were competitive enough to be recorded, which cards appeared disproportionately in the winners?

The field_win_rate baseline (14.8%) is the fraction of all **recorded** decks that won their event. This is not the probability of any random Legacy player winning a tournament. It's the probability that a top-8 (or top-16) deck went on to win.

---

## Min appearances threshold

Current default: 20 appearances.

| Threshold | Cards included | SE of ~15% win rate |
|---|---|---|
| 10 | ~3,000 | ±10% (noisy) |
| 20 | ~1,555 | ±8% |
| 50 | ~1,185 | ±5% |
| 100 | ~800 | ±4% |

The 20-appearance floor retains:
- Recently-printed cards without accumulated history
- Niche sideboard staples
- The full LLM-labeled primer set (some combo pieces have <50 appearances)

For win-rate analysis where precision matters, filter to n ≥ 100 before drawing conclusions. For exploratory work or signal detection, 20 is fine.

---

## Card yearly data and ban signals

`card_yearly.csv` contains per-year stats for each card. The most useful application is detecting ban signals in historical data:

Pattern of a format-warping card:
1. Appears (low total_decks initially)
2. Win rate and inclusion rate rise together — the card is being discovered
3. Win log-OR reaches an elevated level (for narrow cards: typically >0.2)
4. Ban or rotation removes it; total_decks drops to ~0

Confirmed examples:
- Treasure Cruise: win_rate 0.25 in 2014 (field baseline 14.8%), banned January 2015
- Sensei's Divining Top: win_rate 0.20, consistent over many years, banned April 2017
- Deathrite Shaman: win_rate 0.16 at peak, banned September 2018

The rising log-OR trend is the leading indicator. Static log-OR alone doesn't tell you if a card is still climbing.

---

## Co-occurrence metrics

| Metric | Interpretation |
|---|---|
| `cooccur_count` | Raw count of decks where both cards appear in the mainboard |
| `jaccard` | Intersection / union of the two cards' appearance sets. Range 0–1. High = always together |
| `lift` | How much more often they appear together than chance predicts. 1.0 = independent |

**Jaccard** is the better metric for identifying archetype membership. A Jaccard of 0.92 (Brainstorm + Ponder) means these cards appear in nearly the same set of decks — they are effectively defining the same archetype engine.

**Lift** captures statistical co-occurrence beyond base rates. Useful for finding unexpected pairings that aren't just "both are popular cards."

**Limitation**: co-occurrence is computed on mainboard only. Sideboard relationships are not captured.
