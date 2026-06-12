# Marvel Super Heroes — Candidate Card Specs (sentiment-free)

**Purpose:** Input file for BLIND framework evaluation. This file contains card
facts only — no community sentiment, no adoption signals, no archetype
suggestions. Evaluators working from this file must not consult web sources or
any community commentary.

**Provenance:** All candidates below were produced by the interim triage step
(generator: `community` — see brief §Phase 0.3; the empirical full-spoiler
screen is pending and may add candidates with generator `screen`).

**Verification status:** Oracle text reconstructed from spoiler-season sources.
[VERIFIED] = consistent across independent sources. [UNVERIFIED] = single
source or uncertain wording — verdicts depending on unverified text must say so.
Final verification against Scryfall happens before prediction lock.

**Set facts:** Main set MSH (296 cards, Standard-legal and below). Commander
products MSC (4 precons × 30 new cards + Jumpstart, 180 new cards) — Legacy/
Vintage/Commander-legal, NOT Standard-legal. MAR = reprint bonus sheet (no new
legality). Paper-legal at prerelease 2026-06-19.

**Field snapshot (June 2026, conditioning set for all evaluations):**

| Archetype | Meta share (aggregator range) |
|---|---|
| Delver / Izzet tempo ("Izzet Cutter") | 7.8–10.7% |
| Dimir Tempo | 6.7–8.9% |
| Sneak and Show | 5.7–6.9% |
| Tron (Karn shells) | ~5.9% |
| Lands | 4.0–5.1% |
| Reanimator (Rakdos/Dimir) | 3.7–4.9% |
| Doomsday | ~3.9% |
| Eldrazi Stompy | ~3.9% |
| UWx Control | ~3.0% |
| Death and Taxes | ~2.7% |

---

## 1. The Fantasticar
- **Cost/type:** {3} • Legendary Artifact — Vehicle • 4/4 • Mythic
- **Product:** MSC #104 (Commander precon — Legacy-legal, not Standard-legal)
- **Text [VERIFIED; animation clause wording approximate]:**
  - Flying
  - Whenever you cast a noncreature spell, you may have The Fantasticar become
    an artifact creature until end of turn. *(No crew cost; this replaces crewing.)*
  - Whenever you cast your fourth noncreature spell each turn, you may sacrifice
    The Fantasticar. If you do, create four 4/4 colorless Construct artifact
    creature tokens with flying and haste.

## 2. Namor the Sub-Mariner
- **Cost/type:** {1}{U}{U} • Legendary Creature — Mutant Merfolk Villain • */4 • MSH #69
- **Text [VERIFIED]:**
  - Flying
  - Namor the Sub-Mariner's power is equal to the number of Merfolk you control.
  - Whenever you cast a noncreature spell with one or more blue mana symbols in
    its mana cost, create that many 1/1 blue Merfolk creature tokens.

## 3. Attuma, Atlantean Warlord
- **Cost/type:** {2}{U}{U} • Legendary Creature — Merfolk Warrior Villain • 3/4 • MSH #47
- **Text [VERIFIED]:**
  - Other Merfolk you control get +1/+1.
  - Whenever one or more Merfolk you control attack a player, draw a card.

## 4. King T'Challa // Black Panther, Hope Enduring
- **Cost/type:** {1}{W}{U} • Legendary Creature — Human Noble Hero • 3/2 • MSH #219 • Mythic • Transforming DFC
- **Front text [VERIFIED]:**
  - Flash
  - Whenever a player draws their second card each turn, you draw a card.
  - {4}{W}{U}: Transform King T'Challa. Activate only as a sorcery.
- **Back text [UNVERIFIED, including P/T]:** Flash, double strike. Prevent all
  damage that would be dealt to Black Panther. Whenever Black Panther deals
  combat damage to a player, draw a card.

## 5. Mole Man, Moloid Master
- **Cost/type:** {2}{G} • Legendary Creature — Human Villain • 1/1 • MSH #177 • Rare
- **Text [VERIFIED]:**
  - You may play lands from your graveyard.
  - Landfall — Whenever a land you control enters, create a 1/1 green Minion
    creature token named Moloid with "Whenever this token attacks, you may mill a card."

## 6. Hex Magic
- **Cost/type:** {2}{R} • Sorcery — Arcane • MSH #133 • Uncommon
- **Text [VERIFIED]:**
  - Exile all the cards from your hand, then draw that many cards. Until the
    end of your next turn, you may play cards exiled this way.

## 7. Avengers Disassembled
- **Cost/type:** {1}{R}{R} • Sorcery • MSH #302 • Rare
- **Text [VERIFIED; modal wording approximate]:**
  - Choose one or both —
  - • Avengers Disassembled deals 3 damage to each creature.
  - • Destroy target land. Its controller may search their library for a basic
    land card, put it onto the battlefield tapped, then shuffle.

## 8. World War Hulk
- **Cost/type:** {3}{G}{G} • Enchantment — Saga • MSH #197 • Rare
- **Text [VERIFIED]:**
  - I — The next red or green creature spell you cast this turn can be cast
    without paying its mana cost.
  - II — Put three +1/+1 counters on target creature you control.
  - III — Choose target creature you control. Until end of turn, double its
    power and toughness and it gains trample.

## 9. Mjölnir, Hammer of Thor
- **Cost/type:** {3}{R} • Legendary Artifact — Equipment • MSH #146 • Mythic
- **Text [PARTIALLY UNVERIFIED — last ability single-source]:**
  - When Mjölnir enters, it deals 4 damage to up to one target creature.
  - Double all damage the equipped creature would deal.
  - Equip worthy {1} *(A creature is worthy if it's a legendary non-Villain
    that's red and/or white.)*
  - [UNVERIFIED] {2}{R}, Discard this card: It deals 2 damage to each creature.

## 10. Hawkeye's Bow
- **Cost/type:** [UNVERIFIED, likely {1}] • Artifact — Equipment • MSH #132 • Common
- **Text [VERIFIED except mana cost]:**
  - Equipped creature gets +1/+0 and has reach.
  - Whenever equipped creature becomes tapped, it deals 1 damage to each opponent.
  - Equip {1}

## 11. Elektra, Daughter of the Hand
- **Cost/type:** {2}{B}{B} • Legendary Creature — Human Ninja Villain • 3/3 • MSH #326
- **Text [VERIFIED; sneak reminder paraphrased]:**
  - Sneak {1}{B}{B} *(You may cast this spell for its sneak cost if you return
    an unblocked attacker you control to hand during the declare blockers step.
    It enters tapped and attacking. Sneak is a cast — counterable, unlike ninjutsu.)*
  - When Elektra enters, destroy target creature an opponent controls with
    power 3 or less.

## 12. Thanos, the Mad Titan
- **Cost/type:** {R}{W}{B} • Legendary Creature — Eternal Villain • 4/4 • MSH #233 • Mythic
- **Text [VERIFIED]:**
  - Deathtouch, lifelink
  - Power-up — {C}{W}{U}{B}{R}{G}: Put two +1/+1 counters on Thanos. Choose odd
    or even. Destroy each other creature with mana value of the chosen quality.
    *(Activate each power-up ability only once. This costs less to activate by
    his mana cost if he entered this turn. Zero is even. Requires {C}.)*

## 13. Cosmic Cube
- **Cost/type:** {5} • Artifact • MSH #245 • Mythic
- **Text [UNVERIFIED — single source]:**
  - Ward {2}
  - Whenever you attack, look at the top six cards of your library. You may
    cast a spell from among them with mana value less than or equal to the
    greatest power among attacking creatures you control without paying its
    mana cost. Put the rest on the bottom of your library in a random order.

## 14. The Coming of Galactus
- **Cost/type:** {2}{B}{B}{G} • Enchantment — Saga • MSH #212
- **Text [INCOMPLETE — chapters I–III unknown]:**
  - IV — Create a 16/16 legendary Galactus creature token. [Other chapter
    abilities and token details unverified.]
