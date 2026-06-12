# Open Questions

Things identified during analysis that are unresolved, need more data, or need further reasoning.
Update this file when something is resolved — move it to the relevant framework file.

---

## On the framework

**Q: How do you handle archetypes that span multiple time profiles?**

Some archetypes operate in different modes depending on the game state. Lands can either grind (time is an asset) or combo-kill instantly (time profile irrelevant). Does the framework need a "conditional time profile" concept?

Tentative answer: the combo mode is an insurance policy, not the primary plan. The archetype's time profile is defined by the primary mode, and the secondary mode is noted as an escape valve. But this needs to be tested against more archetypes.

---

**Q: Where does Miracles fit in the taxonomy?**

Miracles (Counterbalance + Sensei's Divining Top, Terminus, Swords to Plowshares) has elements of:
- Reactive permission (FoW, Counterspell, Counterbalance)
- Permanent lock (Counterbalance + Top, once established)
- Long-game inevitability (Jace, the Mind Sculptor + card advantage)

It might be a hybrid of Delver's permission profile and Lands' time-as-asset profile. Or it might represent a distinct category: **permission-as-lock**, where reactive cards are assembled into a quasi-permanent denial structure. Needs a dedicated archetype file.

---

**Q: Is there a principled way to determine the "threshold" for signal magnitude?**

The framework says: "does this card clear the threshold to displace the current occupant of this slot?" But how do you measure the threshold quantitatively rather than by feel?

Data approach: for each archetype cluster (from co-occurrence), identify the cards currently filling each role (threat, permission, cantrip, mana). Look at their win log-OR and inclusion rates. The threshold is the lower bound of the currently-played cards. A new card needs to exceed that lower bound.

This is possible to compute from `card_features.csv` + co-occurrence clustering. Not yet done.

---

**Q: The combo_piece signal has the lowest win log-OR (−0.040). Why?**

Hypothesis 1: Combo decks have high variance — sometimes they win before the opponent does anything, sometimes they lose to a single piece of hate. The average win rate across this variance is lower than more consistent strategies.

Hypothesis 2: The combo_piece signal captures cards in very different types of combo decks — some fast and reliable (Oops), some slow and inconsistent. The average drags down good combos.

Hypothesis 3: Cards labeled combo_piece often have archetype_synergy co-labeled, which means they're useless outside their specific combo context. When the combo deck loses, it loses hard.

Not yet resolved. Check whether filtering to "large fast combo" vs "slow/grind combo" separates the log-OR distribution.

---

## On the data

**Q: Can we compute win log-OR within archetype rather than across the whole format?**

**Resolved.** See `archetype_cluster.py` and `data/archetype_card_stats.csv`.

Used anchor-card assignment (not co-occurrence clustering — the `archetype_name` field from MTGTop8 events was essentially empty). Each archetype defined by a required card set plus at least one discriminator card. Priority order handles decks matching multiple rules. 12 named archetypes + Other.

Key findings from within-archetype win log-OR:
- Force of Will in Lands: −0.992 (empirical confirmation that reactive permission is anti-synergistic with the archetype's land-recursion permission structure)
- Chrome Mox in Red Prison: −0.804 (the card-disadvantage cost of fast mana is a real drag)
- Ponder in Delver: +0.713 across 15,404 decks (the 94 Delver builds without it win significantly less)
- Dig Through Time in Delver/Miracles: +1.014/+1.339 (explains the ban)
- Wild Cantor/Summoner's Pact in Oops: +0.629/+0.583 (consistency > resilience in pure speed)

Limitation: ~51.5% of ranked decks fall into "Other" — archetypes with broader or more heterogeneous card pools (Stoneblade, 4-Color Control, various creature builds) aren't cleanly captured by the anchor rules. Within-archetype results are most reliable for the archetypes with tight, stable card pools (Elves, Oops, Miracles, Lands).

---

**Q: How reliable is the archetype_name field from MTGTop8 event data?**

Event files contain `archetype_name` from the deck stub. This could enable archetype-level win rate analysis without requiring co-occurrence clustering first. But the quality of MTGTop8's archetype labeling is unknown — it may be inconsistent across years and submitters.

Needs spot-checking: pull a sample of decks for a known archetype (e.g. Delver), check whether the archetype_name labels are consistent with the actual card lists.

---

**Q: The dataset has no full-field data. Can we estimate the full-field win rate any other way?**

Currently the baseline (14.8%) is the fraction of recorded decks that won their event. This is not the probability that any arbitrary Legacy player wins a tournament.

For a truer baseline, we'd need the total player counts from events. The `player_count` field exists in event data but is missing for many events (only 9,591 of ~13,000 events have it populated). Could use the available player counts to estimate an adjusted baseline for the subset of events with known attendance.

---

**Q: Card value is conditional on the field — but the field responds to new cards. When does first-order conditioning break?**

The framework evaluates a new card against the field composition at evaluation time. But a strong new card shifts the equilibrium it's being evaluated against (second-order effect). In Legacy this is acceptable: the field is near-stationary and shifts slowly even for format-warping printings. For faster formats (Phase 4 scaling), the endogenous field response needs explicit modeling — a card's predicted adoption should account for the meta that forms *because of* the card, not just the meta that preceded it. Known omission, accepted for Legacy, logged 2026-06-12. See `.agent/briefs/legacy-value-model-rebuild.md` §2.2.

---

## On new card evaluation

**Q: How do you evaluate a card that creates a new archetype rather than fitting an existing one?**

The framework handles "fit into existing cluster" well. The "new archetype" case is identified by Q8/Q9 in `evaluation.md` but not deeply developed. Need more worked examples — what did the introduction of Wrenn and Six or Uro look like from a first-principles perspective before tournament data existed?

---

**Q: Is the value signal taxonomy complete?**

The 14 signals from primer extraction were defined before the data analysis. Now that we have 15 years of tournament data, are there patterns in the data that suggest missing signals?

One candidate: **resilience to graveyard hate** — cards that perform well even under active hate. This might be captured by `resilience` already but may warrant its own signal given how prevalent graveyard strategies are.
