# Archetype: Red Prison (Stompy / Prison)

> **Rendered view** — canonical claims in `../claims.md`. Data-validated
> content: fast-mana card-cost drag →C4 (Chrome Mox −0.804); self-resilience
> to own lock →C5 (Mountain +0.642).

## Strategic constraints

1. Produce 3+ mana on turn 1 using fast mana enablers
2. Deploy a lock piece that shuts off the opponent's ability to execute their game plan
3. Present a threat that wins through the lock

The lock pieces in use: Chalice of the Void (hits 1-mana spells), Blood Moon (converts nonbasic lands to mountains), Trinisphere (makes everything cost 3). The specific combination varies by build and meta.

## Permission profile

**Proactive and permanent.** Unlike Delver's reactive permission, Red Prison's disruption is deployed preemptively and remains in play.

Chalice of the Void on 1 counters every 1-mana spell the opponent draws for the rest of the game. You paid once; the effect compounds as the opponent draws more uncastable cards. Blood Moon and Trinisphere have the same structure: pay once, restrict permanently.

This is more durable than FoW in a specific sense: FoW is consumed on use and costs 2 cards per activation. The lock pieces are not consumed. They require the opponent to find and resolve an answer (Abrupt Decay, Force of Will targeting the lock piece) to escape.

## Time profile

**Asset after setup. Neutral-to-favorable thereafter.**

Once the lock lands on turn 1, time works in Red Prison's favor. The opponent is drawing dead cards while you develop your threat at whatever pace you choose. The deck can afford a slower clock than Delver precisely because the lock pieces don't deplete.

The time pressure runs in the opposite direction from Delver: Red Prison must establish the lock *before* the opponent can interact, not close the game before resources run out.

## Why the fast setup (not fast clock)

The clock is decoupled from the permission in Red Prison. The lock handles the opponent; the clock just needs to close eventually. What's urgent is getting the lock down before the opponent has mana to answer it.

The fast mana (Ancient Tomb, City of Traitors, Chrome Mox) is what enables turn-1 lock pieces. These come with real costs:

- **Ancient Tomb**: 2 colorless mana, deals 2 damage when tapped. Burning your own life total.
- **City of Traitors**: 2 colorless mana, sacrifices itself when you play another land. Temporary fast mana.
- **Chrome Mox**: imprint (exile) a card to add one mana of its color. Card disadvantage.

These costs are paid upfront. After setup, the deck operates without continued resource drain.

## Resource axis attacked

Opponent's ability to cast spells. Blood Moon removes colored mana from nonbasic lands. Chalice prevents specific mana costs from resolving. Trinisphere makes cheap spells expensive. The opponent is not mana-denied outright (they still have lands) but is prevented from executing their planned spell sequence.

This is distinct from Lands' mana denial: Red Prison doesn't destroy lands, it makes the spells uncastable given the mana the opponent has.

## Cost structure

- Life: Ancient Tomb drains life over the course of the game. This is the primary ongoing cost once the setup is paid.
- Cards: Chrome Mox exiles one card per activation.
- Future mana: City of Traitors sacrifices itself.
- No card disadvantage on lock pieces themselves — they don't cost you cards beyond their initial mana cost.

## Vulnerability

- Fast answers to the lock before it matters: Force of Will can counter Chalice or Blood Moon on the stack. Daze is less relevant because Red Prison often deploys 3+ mana on turn 1, paying through it.
- Basics-heavy manabases: decks running many basics are less affected by Blood Moon and Wasteland.
- Decks whose game plan doesn't care about 1-mana spells: if your plan is to cast Show and Tell for 3 mana, Chalice on 1 does nothing to you.
- Late game inevitability: if the lock is answered and Red Prison has no backup plan, it can get ground out. Ancient Tomb self-damage also becomes a clock against the pilot.

## What a new card needs to fit here

One of:
- Additional fast mana that doesn't deal damage (the holy grail — makes the same turn-1 lock without the life cost)
- A lock piece that's harder to answer than existing options (hits a broader range of strategies, has hexproof/shroud, etc.)
- A threat that wins faster or more resiliently through the lock
- A lock piece that hits a new axis the current suite doesn't cover

Cards providing reactive permission, card advantage for long games, or requiring turns of setup are not what this archetype needs — it's already solved those problems with the lock.

## Within-archetype win log-OR (from `archetype_card_stats.csv`)

Among the 1,430 classified Red Prison decks (baseline win rate 13.2%):

| Card | within_log_or | n with |
|---|---|---|
| Mountain | +0.642 | 1,333 |
| Chrome Mox | **−0.804** | 1,405 |

**Mountain (+0.642)** confirms that basic land resilience is a real win condition: the 97 Red Prison builds that skipped basics — leaving themselves fully exposed to their own Blood Moon — won significantly less than the 1,333 that ran them.

**Chrome Mox (−0.804)** is the more striking result: 1,405 of 1,430 Red Prison decks run Chrome Mox, and those builds underperform the 25 that don't. The card-disadvantage cost of imprinting is a real drag in a strategy that's already burning life with Ancient Tomb. This doesn't mean Chrome Mox should be cut — the fast mana is necessary to deploy the lock on turn 1 — but it means the fast mana has a real cost that limits the ceiling of the archetype. Any new fast mana that doesn't cost a card (like the Holy Grail of "lands that tap for 2") would be a structural improvement, not just an incremental one.
