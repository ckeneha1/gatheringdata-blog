# Archetype: Delver (Tempo)

> **Rendered view** — canonical claims in `../claims.md`. Data-validated
> content: cantrip compensation →C2 (Ponder +0.713); delve-engine ban
> trajectory →C3; insurance-vs-clock conflict →C9. The FoW time-profile
> framing →H1 is a HYPOTHESIS (analytical+primer), not validated.

## Strategic constraints

1. Deploy a cheap threat on turn 1 that demands an answer
2. Back it up with interaction that costs less than it costs the opponent to deal with
3. Use cantrips to maintain the right threat/answer ratio throughout the game
4. Close the game before self-imposed resource constraints become decisive

The threat vehicle has changed repeatedly across eras (Delver of Secrets, Tarmogoyf, Nimble Mongoose, Dragon's Rage Channeler, Murktide Regent) without changing the strategy. The constraints are stable; the implementations aren't.

## Permission profile

**Force of Will**: reactive, one-time, costs 2 cards. Value is card-dependent, not time-dependent — as good on turn 15 as turn 1. Does NOT bleed out over time. This is a common misstatement; correct it when encountered.

**Daze**: reactive, one-time, explicitly time-limited. Opponents pay the 1 in mid/late game; the land bounce hurts more as the game extends. Bleeds out.

Both are reactive and consumable — each use depletes your hand.

## Time profile

Roughly neutral, with nuance:
- FoW is stable over time
- Daze degrades over time
- Card disadvantage from FoW accumulates over time — the deck is 2-for-1ing itself with every FoW activation

The net result is a deck that can operate efficiently in the early and mid game but faces increasing resource pressure as the game extends. The clock compensates for this pressure.

## Why the fast clock

Not because permission bleeds out (FoW doesn't). Because:
- FoW trades 2 cards for 1 effect. This self-imposed card disadvantage compounds. Lose too many fights with FoW and you run out of cards.
- 18–19 land mana base. Delver can't compete in a late-game mana race — it's not built for casting multiple spells per turn in turns 8–12.
- Daze does lose effectiveness specifically.

The fast clock ends the game before the card disadvantage becomes decisive, not before the permission stops working.

## Resource axis attacked

Opponent's mana. Daze and Wasteland (in some builds) force the opponent to spend mana or lose land access, creating an asymmetric tempo gap. The threat exploits that gap.

## Cost structure

- Cards: FoW trades 2-for-1 repeatedly
- Mana base: land-light by design; no late-game mana advantage
- No life cost, no upfront resource burn

## Vulnerability

- Decks that don't care about tempo — Show and Tell, Reanimator can ignore the permission and just win faster
- Grindy decks with card advantage engines that outlast the FoW supply
- Decks that attack the land base (Wasteland mirrors, Loam recursion)
- Any deck that can profitably trade resources and play a longer game

## What a new card needs to fit here

One of:
- A cheaper or more efficient threat (must compare favorably to current threat vehicle on clock speed and resilience)
- Better cantrip (must beat Brainstorm/Ponder threshold — very high bar, see `framework.md` §5 on magnitude)
- Free/cheap permission with lower card cost than FoW
- A card that reduces the land-light tension (enables fewer lands without losing consistency)

Cards that provide late-game value, cost multiple mana, or slow the clock are anti-synergistic with the core resource structure.

## Within-archetype win log-OR (from `archetype_card_stats.csv`)

Top signals among the 15,498 classified Delver decks (baseline win rate 14.8%):

| Card | within_log_or | n with |
|---|---|---|
| Dig Through Time | +1.014 | 131 |
| Ponder | +0.713 | 15,404 |
| Treasure Cruise | +0.676 | 135 |

**Ponder's entry is the most important**: 15,404 of 15,498 Delver decks run it; the 94 that don't win significantly less. Ponder is not optional in this archetype. The two banned delve cards (+1.014, +0.676) show the highest within-archetype signals of any non-banned card — direct evidence of why they were removed.

Negative signals:
- Seal of Removal (−1.200, n=49): defensive insurance that conflicts with the clock imperative
- Moonshadow (−1.968, n=20): at the minimum threshold, but directionally consistent
