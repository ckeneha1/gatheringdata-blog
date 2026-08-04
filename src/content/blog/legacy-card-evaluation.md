---
title: "A Better Way to Evaluate New Cards: Secrets of Strixhaven for Legacy"
description: "The abilities-per-mana heuristic predicts which cards are efficient. It can't predict which ones matter. Here's a framework that can — and a test case."
pubDate: "2026-05-27"
---

[Post 2](./mtg-card-power) established that Magic cards have gotten significantly more efficient over thirty years — roughly twice as many abilities per mana as in 1993. It also introduced a heuristic for evaluating that efficiency: count a card's abilities, divide by its mana cost, compare to its contemporaries.

That heuristic does real work. Deathrite Shaman scores near the top of all one-drops; the data didn't know it was banned in two formats. Tamiyo, Compleated Sage tops the five-drop list; she was discussed as a ban candidate when she was printed. The methodology catches something real.

But it can't tell you what matters in Legacy.

## The problem with ability counting in optimized formats

Legacy has been running on essentially the same card pool for 30 years. The decks aren't built by players deciding which cards are efficient — they've been refined across tens of thousands of tournament matches, with inefficient choices losing and efficient ones propagating. What's left is close to the local optimum.

In that environment, the question isn't "is this card efficient?" It's "is this card more efficient than the specific card it would replace?"

Those are different questions. Lightning Bolt costs 1 mana and deals 3 damage — a ratio the ability-per-mana framework scores as average in 2026, when the average one-drop has nearly 2 abilities. But Lightning Bolt hasn't been displaced from Legacy burn sideboards in thirty years, because the relevant comparison isn't against all one-drops in the abstract. It's against every direct-damage spell ever printed at 1 mana — a list that has never produced a better option.

To evaluate a newly printed card for Legacy, you need to ask a different set of questions.

## The framework

The core insight is that Legacy archetypes aren't card lists. They're **constraint sets**: strategic decisions about how to win (and how to prevent the opponent from winning) that impose specific requirements on every card in the deck. Understanding those constraints tells you exactly what a new card needs to do to matter.

Four dimensions define any Legacy archetype:

**Permission profile**: how does the deck prevent the opponent from executing their plan? Reactive and consumable (Force of Will, Daze), proactive and permanent (Blood Moon, Chalice of the Void), recursive and compounding (Wasteland + Life from the Loam), or none — speed substitutes entirely (Oops All Spells).

**Time profile**: does time work for the deck or against it? Lands wants the game to go long — every additional Wasteland activation increases the mana denial. Oops All Spells wants to win before the opponent has taken a meaningful action; every passing turn makes the combo less likely to succeed.

**Resource axis**: which of the opponent's resources does the deck attack? Mana (Lands, Wasteland), spell-casting (Red Prison, Blood Moon), tempo (Delver, Daze), life total (Burn), the stack (Storm).

**Cost structure**: what does the deck pay for its advantages? FoW costs 2-for-1 card disadvantage per activation. Ancient Tomb costs life. Chrome Mox costs card parity. Understanding the costs determines what the deck can afford.

These four dimensions let you evaluate a new card without needing tournament results. For each archetype, the question becomes: does this card provide a signal type that archetype actually needs, and if so, does it clear the magnitude threshold to displace the current occupant of that slot?

Both conditions are necessary. The right type at insufficient magnitude doesn't make the cut. The wrong type at any magnitude doesn't matter.

## The magnitude thresholds

We have 87,000 Legacy tournament decks spanning 2011–2026, which makes the magnitude question empirical rather than speculative. We can compute the **win log-OR** of every card that appears in the dataset: the log-odds ratio of tournament wins for decks containing that card versus the field baseline. Positive values mean the card correlates with winning more than average; negative values, less.

More valuably, we can compute this **within archetypes**. Using anchor-card clustering to assign each deck to one of twelve named archetypes, the within-archetype win log-OR answers a sharper question: among decks already playing this strategy, do the ones running this card win more often than those that don't?

A few calibration numbers that set the thresholds for what "good enough" looks like:

| Card | Archetype | Within log-OR | n with |
|---|---|---|---|
| Ponder | Delver | +0.713 | 15,404 |
| Brainstorm | Delver | (universal — no control group) | 15,482 |
| Force of Will | Delver | (universal) | 15,487 |
| Prismatic Ending | Lands | +0.813 | 101 |
| Force of Will | Lands | **−0.992** | 41 |

That last row is the most important one in the dataset. 41 Lands builds added Force of Will — a card widely considered one of the best cards in the format — and won *less* often than the ones that didn't. Not slightly less. Meaningfully less. Force of Will is the wrong signal type for Lands: the archetype's permission is the land base itself, and adding reactive counterspells consumes slots that should be recursive engines. Its efficiency in the abstract is irrelevant. In Lands, it's actively harmful.

The ability-per-mana heuristic can't predict this. The framework can.

## Secrets of Strixhaven: applying both lenses

Secrets of Strixhaven was released on April 24, 2026. It's a 261-card set focused on the five colleges of Strixhaven (Lorehold, Prismari, Quandrix, Silverquill, Witherbloom) plus 65 Mystical Archive reprints. The reprints — Force of Will, Demonic Tutor, Counterspell, and others — are already Legacy-legal elsewhere, so they don't change the format. The main set does.

Here are the cards the competitive Legacy community has identified as potentially relevant, evaluated through both frameworks.

---

### Flow State ({1}{U} — Sorcery)

**What it does**: Look at the top three cards of your library. Put one into your hand and the rest on the bottom in any order. If there is an instant card and a sorcery card in your graveyard, instead put two of them into your hand and the rest on the bottom.

**Ability-per-mana view**: CMC=2, delivers card selection plus conditional card advantage. The average two-drop in 2026 scores roughly 2.0 abilities per CMC by Post 2's methodology; Flow State scores around 1.0–1.5 depending on whether you count the conditional mode as a distinct ability. By that framework: below-average efficiency. Worth considering with reservations, but not an obvious slam-dunk.

**Framework view**:

Signal type first. Delver is the format's dominant tempo archetype. Its cost structure is defined by one tension: Force of Will provides powerful reactive permission but costs two cards per activation. The deck compensates with cantrips — Brainstorm and Ponder — that maintain card parity while finding the right threat or answer at the right time. More card selection is exactly the signal type Delver needs.

Signal magnitude second. The threshold to clear is Ponder: one mana, looks at the top three, draws one.<sup>1</sup> Does Flow State clear that threshold?

Ponder costs 1 mana and draws 1. Flow State active costs 2 mana and draws 2. On a raw card-parity basis: spending 1 additional mana to draw 1 additional card is the exact same rate as Ponder. This makes Flow State a strong candidate if — and only if — the condition can be reliably met.

In Izzet Delver, it can. A typical turn 2 has already seen Brainstorm or Ponder on turn 1, plus a Daze or Lightning Bolt in response to something. By turn 2, the "instant and sorcery in graveyard" condition is almost always live. A card that draws 2 for 2 mana — resolving into +1 net card compared to Ponder — is exceptionally strong in a deck that is bleeding cards to Force of Will activations.

Sorcery speed is a real cost: it can't be played reactively in the opponent's turn. But Delver is almost always the aggressor; sorcery speed on a card-advantage spell is fine in the development window where you'd cast it anyway.

**What the tournament data says**: Flow State is already running at 4 copies in Izzet Delver, the format's most-played archetype at ~11.4% meta share. Builds with the full four copies are appearing in tournament results within weeks of the set's release. The framework predicted this card would slot directly into the archetype's cantrip suite; the tournament data confirms it immediately.

This is the ability-per-mana heuristic's worst prediction and the framework's best one. By raw efficiency, Flow State looks like a conditional, below-average cantrip. By the framework, it's a 2-for-1 for 2 mana in the format's most card-hungry archetype — and that's the evaluation that matters.

---

### Erode ({W} — Instant or Sorcery)

**What it does**: Exile target creature. Its controller gets a basic land.

**Ability-per-mana view**: CMC=1, delivers exile removal. The comparison is Swords to Plowshares ({W}: exile target creature, controller gains life). By raw ability count, both deliver "removal" at CMC=1 — the same score. The question is which is better. Life is often irrelevant in Legacy; a basic land could theoretically help the opponent establish a color, though it doesn't enable their nonbasic-dependent mana base. Erode is probably marginally better than StoP in matchups against Blood Moon (where the land matters) and marginally worse elsewhere. The ability-per-mana framework calls this a draw.

**Framework view**: Signal type is efficient targeted removal. Archetypes that need this: Death and Taxes (already runs 4 StoP), Miracles (runs 4 StoP), white-based control. Does Erode clear the StoP threshold?

In the abstract, it's roughly equivalent. The rub is that Legacy already has StoP — a card that has occupied this slot for thirty years without being displaced. Being "roughly equivalent to StoP" means you don't make the cut, because the current occupant is equally efficient and doesn't require you to give up the slot. You'd only run Erode if you wanted copies 5–8 of exile removal, which white-based decks occasionally do want — but typically prefer a diversified suite (StoP + Prismatic Ending) over pure redundancy.

The within-archetype data shows Prismatic Ending at +0.813 in Lands (the best removal signal in that archetype). Prismatic Ending beats Erode on versatility (hits any permanent type) even if it costs more mana. The clearer upgrade path for removal runs through versatility, not speed.

**Assessment**: Sideboard card or additional removal for white-splash builds that already have 4 StoP. Correct archetype fit; insufficient magnitude over the incumbent.

---

### Prismari Charm ({1}{U}{R} — Instant)

**What it does** (three modes): Counter target spell unless its controller pays {3}. / Deal 3 damage to target creature or planeswalker. / Target player draws a card then discards a card.

**Ability-per-mana view**: CMC=3, delivers a permission mode, a removal mode, and a selection mode. Three distinct abilities for three mana — ratio 1.0, which is at the lower end of modern three-drops. The constraint is the color requirement: {1}{U}{R} demands both blue and red, limiting which decks can cast it.

**Framework view**: The specific archetype this targets is Sneak and Show — the deck uses Show and Tell to put Omniscience or Sneak Attack into play on turn 2-3. Sneak and Show's vulnerability is permission: Force of Will can counter Show and Tell on the stack before the game-winning permanent enters.

What does Sneak and Show need? The primary gap is speed and resilience to interaction — either presenting the combo faster or protecting it through resolution. A modal spell at {1}{U}{R} fits the deck's color requirements (both Volcanic Island and Underground Sea are common), but the question is which mode matters and whether it clears the relevant threshold.

The "counter unless pay {3}" mode is essentially Quench — a permission spell that stops on the draw when opponents have sufficient mana. Uninspiring. The "3 damage" mode is fine removal but irrelevant to Sneak and Show's game plan. The "draw then discard" mode is Faithless Looting without the graveyard recursion — sometimes useful for digging toward Show and Tell.

None of these modes clears the threshold of the cards already in this role. Sneak and Show's interaction suite runs Force of Will (free), Flusterstorm (free or mana-efficient against combo), and Pact of Negation (free). A 3-mana counterspell mode doesn't compete with free permission. Three-mana is expensive in a strategy that wins on turn 2.

**Assessment**: Interesting design; wrong magnitude at every mode for the archetype where it fits best.

---

### Mathemagics ({2}{U}{U} — Sorcery)

**What it does**: Draw cards equal to the number of instant and sorcery cards in your graveyard. Then discard that many cards.

**Ability-per-mana view**: CMC=4, delivers card selection (draw-then-discard scaled to graveyard depth). At 4 mana, this could generate significant selection in the right deck. Abilities ratio: 1–2 depending on how you count the scaling effect. Roughly average for a four-drop in 2026.

**Framework view**: The archetype that wants this is High Tide — a combo deck that uses High Tide + Candelabra of Tawnos + blue card draw to chain into enough mana to cast Braingeyser or Time Spiral for the win. High Tide needs to fill its graveyard with instants and sorceries anyway, and a draw-discard effect scaled to that count functions as a tutor for the missing combo piece.

But the cost is 4 mana for a sorcery. High Tide's entire game plan is built around generating that mana efficiently; at 4 mana at sorcery speed, this asks you to have your engine established *before* you can use it. The selection it provides is real, but Brainstorm at 1 mana provides it immediately on turn 1 when the engine needs to be found, not turn 4+ when the engine is already running.

The framework question: does Mathemagics provide a signal type High Tide needs, at a magnitude that clears the threshold of existing options? Signal type yes. Magnitude: probably not. By the time you're casting this, you either win with the existing cards or you don't. The role of a 4-mana sorcery in a deck that spends turns 1-3 setting up the engine isn't clear.

**Assessment**: Corner-case role player in grind-oriented High Tide builds. Too expensive to clear the threshold for the primary game plan.

---

### Petrified Hamlet (Land)

**What it does**: Enters untapped. Produces one mana of any color. If you control six or more lands, it's indestructible and can't be sacrificed. (Tutor-accessible via Crop Rotation in Lands.)

**Ability-per-mana view**: Lands don't have CMC. This framework can't evaluate it.

**Framework view**: The archetype this belongs in is Lands, which uses Wasteland + Life from the Loam recursion to deny the opponent's mana base. Its primary vulnerability is fast combo that wins before the engine is established. A land that becomes indestructible with six lands in play is effectively Wasteland-immune — Wasteland can't destroy it once the condition is met.

Signal type: resilience to mana denial, which is Lands' own weapon. Archetype fit: exactly right — a land that insulates the archetype's own mana base from mirror-style Wasteland exchanges and from Blood Moon. Cost structure: lands don't cost mana to play (Crop Rotation accesses it for {G}).

Signal magnitude: the threshold is Dark Depths and Thespian's Stage, which serve the combo kill function, and The Tabernacle at Pendrell Vale and Rishadan Port, which serve denial. Petrified Hamlet doesn't compete with those — it fills a different slot: resilient colored mana production that the archetype sometimes struggles with against Blood Moon strategies.

The within-archetype data shows Island at −1.088 in Lands — builds that splash blue for interaction lose. But that doesn't mean colored mana is unwanted; it means the *reason* for the splash (reactive permission) is wrong. A colored mana source that doesn't invite splashing spells is a different thing. The 25 Lands builds running Underground Mortuary post in the win log-OR data at −0.937, which suggests black splash builds underperform — but Hamlet provides the color with fewer commitments to off-strategy cards.

**Assessment**: Legitimate new tool for Lands. Not a flagship card but fills a gap in the archetype's mana-resilience profile. Worth watching in Lands builds post-rotation.

---

## What the tournament data says

Four weeks after Secrets of Strixhaven's release, the Legacy metagame picture has clarified:

**Flow State is the set's Legacy card.** It's in the most-played archetype at full four-copy density. The competitive community converged on this within the first week of play, well ahead of any formal data collection.

**Erode is showing up in sideboards** in some Death and Taxes and white-based prison builds. Not as a maindeck staple — exactly as the framework predicted: supplementary removal for builds that already have full StoP counts.

**The rest has largely not appeared.** Prismari Charm, Mathemagics, Flashback — none have broken into meaningful play counts at the time of writing.

The set's Mystical Archive reprints (Force of Will, Demonic Tutor, Counterspell, Vampiric Tutor) are already in the format from other printings. They're not "new" cards even if they're in new packs. The framework has nothing to say about them.

## Why the ability-per-mana heuristic missed Flow State

The Post 2 framework scores Flow State as below-average for its mana cost. In the abstract, that's technically correct: a conditional cantrip at 2 mana is less efficient than the 1-mana unconditional options that already exist.

What the framework misses is that **the condition is trivially met in Delver**, and **the payoff when met is a material upgrade over Ponder**. The threshold argument requires knowing the specific deck's cost structure, the specific card's condition trigger, and the specific gap between the new card's active state and the incumbent's best-case performance. None of those can be read off a mana cost and an ability list.

This is the pattern that repeats across thirty years of Legacy. When Expressive Iteration was printed, it scored at roughly average efficiency for a two-mana card. In Izzet Delver, where you almost always had an instant or sorcery in your graveyard by turn 2, it was consistently drawing two cards — and was subsequently banned in both Pioneer and Legacy. Flow State drew comparisons to Expressive Iteration at preview. The framework predicts it would land in the same archetype, serve the same function, and see a similar level of play — which is what the first month of tournament results confirms.

## The checklist

For any newly printed card, evaluated against Legacy specifically:

1. **What signal type is it?** Map it to one of the major categories: threat, cantrip/card advantage, reactive permission, proactive lock piece, fast mana, graveyard enabler, mana denial.
2. **Which archetypes need that signal?** Use the archetype constraint profiles to identify where this type is valuable.
3. **What's the current occupant of that slot?** Name the specific card(s) the new one would displace.
4. **Does it clear the threshold?** This is the kill shot. A "slightly better Ponder" doesn't get played; Ponder is already close to optimal. The new card needs a meaningful, format-relevant advantage.
5. **Is the advantage conditional?** If so, how reliably is the condition met in the target archetype? A conditional upgrade that fires 90% of the time is close to unconditional. One that fires 30% of the time is roughly Ponder-at-2 mana: a downgrade.
6. **Does the cost structure fit the archetype?** Card disadvantage costs hurt Delver; life costs hurt Red Prison; mana costs matter more for Oops than anywhere else.

Flow State passes every step. Prismari Charm fails step 4 on every mode. Erode fails step 4 narrowly — close but StoP holds the slot. Mathemagics has the right signal type but the wrong cost for the archetype that wants it.

The broader point: Legacy is nearly optimal. The cards that break through don't do so by being efficient in the abstract — they do so by being the exact right thing at the exact right threshold for the deck that needs them. The data makes that threshold visible. The framework makes the path to clearing it legible.

---

## Data and methodology

Archetype assignment uses anchor-card rules across 87,581 ranked tournament decks (2011–2026) scraped from MTGTop8. Each deck is assigned to the first matching archetype in priority order; unmatched decks are labelled "Other" (~51.5% of the dataset). Win log-OR is the log-odds ratio of winning (placement = 1) relative to the field baseline, with 0.5 Laplace smoothing. Within-archetype win log-OR uses the same formula but restricts the field to decks in that archetype, requiring ≥20 decks with and ≥20 without the card. Cards appearing universally within an archetype (&gt;95% inclusion rate) have no meaningful control group and are excluded from within-archetype tables.

Tournament validation data reflects the Legacy metagame as of May 2026. Flow State meta share from MTGGoldfish Legacy metagame data.

---

*<sup>1</sup> Ponder looks at the top three, arranges them in any order (or shuffles), then draws the top card. Brainstorm, the other 1-mana cantrip, draws three and puts two back — a different effect that's not directly substitutable. Flow State doesn't replace Brainstorm; it competes with Ponder for the "additional cantrip" slots beyond the full Brainstorm playset.*
