# Core Framework

## 1. Archetypes as strategic constraints

An archetype is not a card list. It is a recurring **set of strategic constraints** that a deck imposes on the game state, implemented through whatever cards best satisfy those constraints at a given time.

The cards are implementations. The constraints are what persists across years and rotations.

**Delver** illustrates this: the threat vehicle has been Delver of Secrets, Tarmogoyf, Nimble Mongoose, Dragon's Rage Channeler, and Murktide Regent across different eras. The game plan — cheap threat, free/cheap permission, cantrips to maintain ratio, close before resource asymmetry bleeds out — is structurally identical across all of them.

Implication for evaluation: when assessing a new card, ask which constraint it serves, not which previous card it resembles.

---

## 2. Permission taxonomy

Every competitive Legacy archetype has some form of disruption. They differ fundamentally in their **time profile** — whether the disruption gets stronger, weaker, or stays constant as the game goes on.

### Reactive consumable permission
*Example: Force of Will, Daze*

One-time effects. Each use depletes your resources.

- **Daze**: explicitly time-limited. Opponents pay the 1 in mid/late game; the land bounce hurts you more as the game extends. Bleeds out.
- **Force of Will**: does NOT bleed out. Countering a game-winning spell on turn 15 is as good as on turn 3. Its value is card-dependent (needs blue cards to pitch), not time-dependent. This was a correction — the common framing that "free permission bleeds out" is only true of Daze, not FoW.

The reason Delver needs a fast clock is **not** that FoW loses effectiveness. It's that:
- FoW trades 2 cards for 1 effect. Card disadvantage accumulates over a long game.
- Delver runs 18-19 lands by design. No late-game mana advantage.
- Daze does specifically lose effectiveness.

The clock compensates for self-imposed resource constraints, not for permission decay.

### Proactive permanent lock
*Example: Blood Moon, Chalice of the Void, Trinisphere*

Deployed once, effective permanently (until answered). Does not bleed out. Time-neutral to slightly favorable once the lock is established.

The "cost" is in the setup: Ancient Tomb deals 2 damage per activation, Chrome Mox exiles a card, City of Traitors sacrifices itself. These costs are paid upfront. After the lock lands, time is on your side — you're not spending additional resources to maintain it.

Red Prison needs a fast **setup**, not a fast clock.

### Recursive compounding denial
*Example: Wasteland + Life from the Loam*

Permission that improves over time. Each Loam activation returns Wasteland (and other lands) to hand. The disruption is functionally unlimited — there's no way to permanently answer it because the recursion keeps restoring it.

Stronger than a permanent lock in durability terms: a Blood Moon can be answered with Abrupt Decay; Wasteland + Loam cannot be permanently answered by removal.

Lands is designed for time to be an asset. Slow games are winning games.

### Speed as permission substitute
*Example: Oops All Spells*

No traditional permission at all. The "answer" to the opponent's interaction is winning before they can use it.

This is viable only in a format where turn-1 wins are achievable. It trades all resilience for pure speed.

Time is a pure liability. Every turn that passes, the opponent draws more interaction. The deck has a hard expiration date.

---

## 3. Resource axes

Each archetype attacks a different axis of opponent resources:

| Archetype type | Resource attacked |
|---|---|
| Delver / tempo | Opponent's mana (Daze, Wasteland) |
| Red Prison | Opponent's ability to cast spells (Chalice, Blood Moon, Trinisphere) |
| Lands | Opponent's land base (Wasteland recursion, Tabernacle) |
| Fast combo (Oops) | Opponent's untaken turn |

Understanding which axis an archetype attacks tells you what kind of cards strengthen it and what kind of meta shifts threaten it.

---

## 4. The time profile taxonomy

Four archetypes, four relationships with time:

| Archetype | Time relationship | Permission type |
|---|---|---|
| Delver | Neutral (FoW stable, Daze bleeds, card disadvantage accumulates) | Reactive, consumable |
| Red Prison | Asset after setup | Proactive, permanent |
| Lands | Always an asset, improves indefinitely | Recursive, compounding |
| Oops All Spells | Pure liability | None — speed substitutes |

This axis is probably the most useful single lens for understanding why a deck is built the way it is.

---

## 5. Signal type vs signal magnitude

Evaluating whether a card is good in Legacy requires both components. Neither alone is sufficient.

**Signal type**: which constraint does this card serve? Does that constraint matter in Legacy? This is the archetype fit question. A card can be powerful in a vacuum and completely irrelevant to Legacy if it doesn't serve a constraint the format rewards.

**Signal magnitude**: does this card serve that constraint well enough to displace whatever currently occupies that slot? Legacy's card pool is 30+ years deep and highly optimized. Every slot has competition. The question isn't "is this card good at X?" but "is this card better at X than what's already available?"

**The threshold effect**: because the format is so optimized, threshold effects dominate. Being marginally above the threshold for a given slot separates format-defining from unplayed. The difference between Brainstorm (draws 3, puts back 2) and a hypothetical version that draws 2 (puts back 1) is not linear — the 3-card look changes the combinatorial odds of finding both a threat and permission simultaneously, and the interaction with fetchland shuffles only works cleanly with 2 cards to put back. Small differences in magnitude translate to large differences in power at this level of competition.

---

## 6. The cross-archetype staple problem

Cards that appear across many archetypes (Force of Will: 54% of all Legacy decks) have win rates that converge to the field average. This is not because they're mediocre — it's because their win rate reflects the average quality of all the diverse archetypes running them, both strong and weak.

Win log-OR (or any win-rate metric) is only a meaningful signal for **narrow cards** that primarily appear in specific, dominant archetypes at a specific time. For cross-archetype staples, inclusion rate, co-occurrence structure, and the value signal taxonomy carry more of the explanatory weight.

This is not a flaw in the metric. It's telling you something true: FoW is a necessary condition for many strategies, not a differentiator between them.
