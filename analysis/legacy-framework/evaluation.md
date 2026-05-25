# Evaluation Toolkit

Ordered questions for assessing a card's Legacy relevance. Work through them in sequence.
Each question either gives you an answer or tells you which file to dig into next.

---

## Stage 1: Signal type — does this card belong in Legacy at all?

**Q1. Which of Legacy's strategic constraints does this card serve?**

Check against the value signal taxonomy (14 signals from primer extraction):
`free_spell`, `mana_denial`, `mana_acceleration`, `cantrip`, `tutor`, `combo_piece`,
`lock_piece`, `graveyard`, `resilience`, `protection`, `hate_piece`, `card_advantage`,
`tempo`, `archetype_synergy`

Historical win log-OR by signal (from 87K-deck tournament dataset):

| Signal | Mean log-OR | n cards |
|---|---|---|
| lock_piece | +0.122 | 29 |
| card_advantage | +0.081 | 57 |
| cantrip | +0.078 | 14 |
| mana_denial | +0.064 | 19 |
| tempo | +0.064 | 101 |
| tutor | +0.063 | 30 |
| archetype_synergy | +0.054 | 226 |
| protection | +0.050 | 40 |
| resilience | +0.048 | 42 |
| hate_piece | +0.027 | 27 |
| mana_acceleration | +0.007 | 49 |
| graveyard | −0.004 | 44 |
| free_spell | −0.007 | 44 |
| combo_piece | −0.040 | 89 |

Caveats: these are averages across all cards with that signal, including narrow and broad ones. Use as a prior, not a verdict. See `data_interpretation.md` for limitations.

**Q2. Does it serve multiple signals?**

Cards with 5+ signals in the dataset tend to be format-defining (Karakas, Force of Will, Cabal Therapy, Crop Rotation). A card that serves a single signal at high magnitude can also matter — but multiple signals hitting the right combination (e.g. lock_piece + mana_denial, or cantrip + tempo) is a strong indicator.

**If the card serves no Legacy-relevant signal: stop here. Raw power doesn't matter if it doesn't connect to a constraint the format rewards.**

---

## Stage 2: Archetype fit — where does it live?

**Q3. Which existing archetype cluster does it potentially join?**

Look up co-occurrence clusters in `cooccurrence.csv`. Find the cards most naturally paired with this card's function. Which tight Jaccard clusters do those partners belong to?

- Jaccard > 0.7: essentially always together — core engine pairing
- Jaccard 0.4–0.7: frequent pairing — same archetype, not always run together
- Jaccard < 0.2: coincidental — probably different archetypes

**Q4. What is the time profile of the archetype it fits?**

See `archetypes/` for worked examples. The key question: does this card's value improve or degrade as the game extends? Does it match the archetype's time profile?

A card that gets worse over time is a poor fit for Lands (which needs time). A card that requires setup is a poor fit for Oops (which has no time).

**Q5. What resource axis does it attack?**

- Mana denial → Delver, Lands
- Castability denial → Red Prison
- Land base → Lands
- Speed → fast combo

If the card attacks a resource axis that's already well-served in the archetype's engine, it's competing for an existing slot. If it opens a new axis, it might be extending the strategy.

---

## Stage 3: Signal magnitude — is it good enough?

**Q6. What is the current occupant of this slot, and does the new card beat it?**

This is the hardest question and the one most often skipped. Legacy is 30+ years optimized. Every slot has competition. Name the specific card(s) this would displace and make the case explicitly.

Key dimensions to compare:
- Mana cost (one mana difference is often format-defining at this level)
- Speed (instant vs sorcery)
- Net card advantage (Brainstorm draws 3/puts back 2 — if it drew 2/puts back 1, it's a different card entirely)
- Whether it's answerable and at what cost

**Q7. Does it clear the threshold?**

Threshold effects dominate because the format is so optimized. Being marginally above the threshold separates format-defining from unplayed. The threshold is set by the best currently-available card for that constraint.

Don't ask "is this card good?" Ask "is this card better than [specific competitor] for [specific job]?"

---

## Stage 4: New archetype potential (if Q3 finds no home)

**Q8. Does this card propose a new constraint combination the format can support?**

This is the hardest evaluation problem. Signs that a new archetype is possible:
- The card creates an interaction that Legacy's fast mana enables but doesn't currently exploit
- The card pairs with existing format staples in a way that creates a new game plan
- The card's constraint combination isn't currently represented in the archetype taxonomy

Signs that it probably doesn't work:
- The card requires resources (mana, time, cards) the format doesn't readily provide
- The strategy it enables has a known and easily-available answer already in wide use
- It requires a critical mass of support cards that don't exist yet in Legacy

**Q9. What does the archetype need around this card to function?**

If the new archetype requires cards that themselves don't see Legacy play, the evaluation ends here. If the support cards are already in the format (but just haven't been assembled this way), check the co-occurrence clusters to see if they're natural partners.

---

## Stage 5: For empirical assessment (new cards with tournament data)

**Q10. Is win log-OR rising?**

The most useful signal for detecting a format-warping card early. A card whose win log-OR is climbing — especially if inclusion rate is also climbing — is on a trajectory. Check `card_yearly.csv` for trend.

**Q11. Is it narrow or broad?**

Narrow cards (one archetype, or a few) produce meaningful win log-OR signals. Broad cards (cross-archetype staples) converge to field average regardless of power. If the card is in >20% of the field, win log-OR tells you about archetype quality, not card quality. Use inclusion rate and co-occurrence structure instead.

---

## Quick reference: what each data file answers

| File | Best question to answer |
|---|---|
| `card_features.csv` | How has this card historically performed? What signals is it labeled with? |
| `card_yearly.csv` | Is this card's win rate trending? When did it spike? When did it drop? |
| `cooccurrence.csv` | What does this card always appear with? What cluster does it belong to? |
| Primer extractions | Why is this card considered good — which format levers does it pull? |
