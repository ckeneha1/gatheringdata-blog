# Archetype: Oops All Spells (Necrotic Ooze / All-In Combo)

## Strategic constraints

1. Assemble fast mana sufficient to cast the mill creature on turn 1
2. Cast Balustrade Spy or Undercity Informer (with no lands in the deck, mills entire library)
3. Trigger Narcomoeba, Creeping Chill, Prized Amalgam from the graveyard
4. Flashback Dread Return targeting Thassa's Oracle to win

The deck runs 0 lands. This is not incidental — it is what makes the combo deterministic. Any lands in the deck would stop the mill effect.

## Permission profile

**None. Speed substitutes for permission entirely.**

This is the structural limit case of the permission taxonomy. Every other archetype has some disruption:
- Delver: reactive FoW and Daze
- Red Prison: permanent lock pieces
- Lands: recursive Wasteland denial
- Oops: nothing

The "answer" to the opponent's interaction is winning before they can use it. This is not a trade-off between permission quality and speed — it's the complete elimination of permission in favor of maximizing speed.

The one exception: Chancellor of the Annex, revealed from the opening hand, forces the opponent to pay 1 additional mana to cast interaction. This is pseudo-permission that costs zero resources during the combo turn. It's the model for what "protection" looks like in this archetype — must be free, must not require mana or card investment on the combo turn itself.

## Time profile

**Pure liability. The most time-sensitive archetype in the format.**

Every turn that passes:
- Opponent draws more interaction
- Force of Will, Daze, Thoughtseize, Surgical Extraction on Narcomoeba, Leyline of the Void — all become more available
- The fast mana drawn on turn 3 or 4 has diminishing utility
- The opponent may have had time to set up specific hate

The deck has a hard expiration date. There is no meaningful late game. Lands is the opposite extreme: time is always an asset. Oops is time-hostile at every point.

## Resource axis attacked

The opponent's untaken turn. Not their mana, not their land base, not their castability — the deck wins before the opponent has taken a meaningful action. The resource being attacked is their tempo.

This is only viable because Legacy's card pool includes enough zero-cost mana acceleration (Lotus Petal, Elvish Spirit Guide, rituals, Chancellor of the Tangle from hand) to assemble 3+ mana on turn 1 without any lands.

## The 0-lands construction

Running zero lands means:
- Every card in the deck is functional toward the combo — no "wasted" slots
- Immune to Wasteland and Blood Moon (irrelevant axes)
- The mill is guaranteed deterministic (no lands to stop it)
- The deck cannot rebuild if the first attempt fails

The downside of zero lands is that the deck is a one-shot engine. There is no plan B requiring lands. Either the combo goes off or the game is functionally over.

## Cost structure

Fast mana costs are all upfront and non-recurring:
- Lotus Petal: free, exiles permanently
- Elvish Spirit Guide: free from hand, exiled permanently
- Chrome Mox: exiles a card
- Dark Ritual / Cabal Ritual: requires black mana source, but generates net positive
- Chancellor of the Tangle: revealed from opening hand, no resource cost

All consumed in a single burst. Unlike Ancient Tomb (continuous life drain), these costs are paid once and gone.

## Vulnerability

**Turn-1 reactive permission on the draw.**

- Force of Will: can counter Balustrade Spy or Undercity Informer before the mill happens
- Thoughtseize / Duress: strips the combo piece from hand before it's cast
- Leyline of the Void: prevents Narcomoeba, Prized Amalgam from triggering from the graveyard — shuts down the combo entirely if in opening hand
- Surgical Extraction on Narcomoeba: removes the creatures needed to flashback Dread Return
- Chancellor of the Annex (opponent's): mirrors the deck's own protection

The opponent's position on the play vs. draw matters enormously: on the draw, the opponent has had no action, FoW is their most available answer. On the play, they've potentially passed without action, giving you a clean turn 1.

## What a new card needs to fit here

The evaluation collapses to two questions:

1. **Does it make the combo faster?** — mana production that costs less or enables the combo with fewer pieces. If it reduces the combo from 3 mana to 2 mana or makes a missing piece more redundant, it's relevant.

2. **Does it protect the combo at zero cost on the combo turn?** — Chancellor of the Annex is the model. Any card that provides a protection effect from the opening hand without requiring mana investment during the combo turn is directly on-axis.

Everything else is irrelevant:
- Card advantage: no late game to use it
- Late-game threats: no late game
- Setup-requiring cards: no turns to set up
- Interactive spells: the strategy doesn't interact, it ignores

This is the sharpest application of the "signal type vs magnitude" principle: the signal type list has two items. Magnitude then determines whether the specific card clears the threshold. A mana-producing card that generates 1 mana but costs 1 card at sorcery speed (net 0 at slow speed) is worse than Lotus Petal (net +1 at instant speed, free). The difference is magnitude.

## Within-archetype win log-OR (from `archetype_card_stats.csv`)

Among the 1,191 classified Oops All Spells decks (baseline win rate 11.9%):

| Card | within_log_or | n with |
|---|---|---|
| Wild Cantor | +0.629 | 313 |
| Summoner's Pact | +0.583 | 336 |
| Turntimber Symbiosis | +0.547 | 222 |
| Grief | +0.397 | 32 |
| Jack-o'-Lantern | −0.479 | 758 |
| Fell the Profane | −0.519 | 870 |
| Lion's Eye Diamond | −1.785 | 21 |

Wild Cantor, Summoner's Pact, and Turntimber Symbiosis all serve the same function: making the combo more consistent by providing additional mana sources or redundancy. Their positive signals confirm the "does it make the combo faster/more consistent?" evaluation.

Grief (+0.397) is the protection signal: the 32 builds running it won meaningfully more, consistent with the Chancellor of the Annex model (free protection from hand).

Lion's Eye Diamond (−1.785) is at the minimum threshold (n=21) and should be read cautiously, but the direction is notable — LED is high-variance fast mana that commits cards in a way that could strand the hand.

Jack-o'-Lantern (−0.479) and Fell the Profane (−0.519) are both utility cards that appear in many Oops builds. Their negative within-archetype signals suggest that building toward consistency (Wild Cantor, Pact) outperforms building toward resilience (graveyard interaction). In a pure speed deck, slots spent on anything other than speed are a net loss.

## Note on raw power relevance

Even for Oops, raw numbers matter at the margin. A fast mana card generating 0.5 mana instead of 1 mana doesn't enable a turn-1 combo. The threshold here is exact: you need exactly enough mana to cast the mill creature by turn 1. Cards that hit that threshold are valuable; cards that fall short are not, regardless of how "close" they are.
