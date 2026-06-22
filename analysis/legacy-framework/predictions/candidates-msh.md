# Marvel Super Heroes — Candidate Card Specs (sentiment-free)

**Purpose:** Input file for BLIND framework evaluation. This file contains card
facts only — no community sentiment, no adoption signals, no archetype
suggestions. Evaluators working from this file must not consult web sources or
any community commentary.

**Provenance:** Candidates #1–14 were produced by the interim triage step
(generator: `community` — see brief §Phase 0.3). The empirical full-spoiler
screen AND a full-set blind triage were run 2026-06-22 (Gate 2); they added
candidates #15–16 below (generator: `blind-triage`, dated, additive). The
screen's recall vs. the community list was poor (21.4%, 3/14) — logged as a
screen defect for Phase 1, never a reason to alter a registered verdict (see
`marvel-super-heroes.md` §Gate 2 results).

**Verification status:** ✅ VERIFIED 2026-06-14 (Gate 1 of the lock checklist).
All previously [UNVERIFIED]/[INCOMPLETE] texts were re-checked via WebSearch
across ≥2 independent sources each (Scryfall + secondary). See the
"Verification log" at the foot of this file. **Outcome: every verified text
confirms the assumption the blind framework evaluator made — no verdict
changes.** Corrections to the specs below are factual (cost/chapters/subtypes)
and verdict-neutral; the verdict-critical conditional flags
(Cosmic Cube attack-trigger, Fantasticar free animation) resolved in favor of
the registered verdicts. Direct api.scryfall.com access remains egress-blocked
in this environment; pixel-verification against rendered card images is the one
residual step (low risk given the source agreement).

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
- **Text [VERIFIED 2026-06-14]:**
  - Flying
  - Whenever you cast a noncreature spell, you may have The Fantasticar become
    an artifact creature until end of turn.
  - Whenever you cast your fourth noncreature spell each turn, you may sacrifice
    The Fantasticar. If you do, create four 4/4 colorless Construct artifact
    creature tokens with flying and haste.
  - *Verdict-critical confirmation: the animation is FREE — a triggered
    ability, no crew cost and no mana. The evaluator's FRINGE verdict was
    conditioned on this (it would drop to NOT PLAYED only if animation cost
    mana/crew); FRINGE holds.*

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
- **Back text [VERIFIED 2026-06-14 — Black Panther, 3/3]:** Flash, double strike.
  Prevent all damage that would be dealt to Black Panther. Whenever Black Panther
  deals combat damage to a player, draw a card. *(Damage prevention, not
  indestructible. Verdict-neutral — no Legacy line transforms it. Front-face
  cost {1}{W}{U} ≡ {1}{U}{W}; one source orders it {1}{U}{W}.)*

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
- **Text [VERIFIED 2026-06-14]:**
  - When Mjölnir enters, it deals 4 damage to up to one target creature.
  - Double all damage the equipped creature would deal.
  - Equip worthy {1} *(A creature is worthy if it's a legendary non-Villain
    that's red and/or white.)*
  - {2}{R}, Discard this card: It deals 2 damage to each creature.
    *(Confirmed to exist — was [UNVERIFIED]; verdict-neutral per the evaluator.)*

## 10. Hawkeye's Bow
- **Cost/type:** {R} • Artifact — Equipment • MSH #132 • Common
  *(Verified {R}, a single red — NOT {1} generic as previously guessed.
  Verdict-neutral: NOT PLAYED holds at any cost.)*
- **Text [VERIFIED 2026-06-14]:**
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
- **Cost/type:** {5} • Artifact • MSH #312 • Mythic
  *(Collector # corrected #245→#312; #245 was wrong. Do not confuse with
  "Construct a Cosmic Cube", MSH #90, a separate Plan enchantment.)*
- **Text [VERIFIED 2026-06-14 — was single-source, now ≥2 sources]:**
  - Ward {2}
  - Whenever you attack, look at the top six cards of your library. You may
    cast a spell from among them with mana value less than or equal to the
    greatest power among attacking creatures you control without paying its
    mana cost. Put the rest on the bottom of your library in a random order.
  - *Verdict-critical confirmation: triggers on ATTACK (not cast), at {5}.
    The blind evaluator's NOT PLAYED was explicitly conditioned on exactly
    this — verdict holds.*

## 14. The Coming of Galactus
- **Cost/type:** {2}{B}{B}{G} • Enchantment — Saga • MSH #212
- **Text [VERIFIED 2026-06-14 — chapters now complete]:**
  - I — Destroy up to one target nonland permanent.
  - II, III — Each opponent loses 2 life.
  - IV — Create Galactus, a legendary 16/16 black Elder Alien creature token
    with flying, trample, and "Whenever Galactus attacks, destroy target land."
  - *Verdict-neutral: a 5-mana three-color saga paying off on turn 8 fails
    every archetype's time profile regardless; NOT PLAYED holds.*

## 15. Jennifer Walters // The Sensational She-Hulk
- **Cost/type:** {1}{W} • Legendary Creature — Human Advisor Hero • 2/3 •
  Transforming DFC (back: The Sensational She-Hulk, {3}{G}{W}{W} 6/6, reach/trample)
- **Provenance:** generator `blind-triage` (full new-card sweep) — added 2026-06-22, additive
- **Front text:**
  - Your opponents can't cast spells during your turn.
  - {3}{G}{W}{W}: Transform Jennifer Walters. Activate only as a sorcery.

## 16. Doctor Doom, Unrivaled
- **Cost/type:** {2}{B}{B} • Legendary Creature — Human Sorcerer Villain • 4/4
- **Provenance:** generator `blind-triage` (full new-card sweep) — added 2026-06-22, additive
- **Text:**
  - Lifelink
  - {T}: You draw a card and lose 1 life. Then if your library has no cards in
    it, you win the game. (You win even if you have 0 life or didn't draw a card.)
  - *(Distinct from "Doctor Doom, King of Latveria" {1}{U}{B}{R}, a separate card.)*

---

## Verification log — Gate 1 (2026-06-14)

Method: WebSearch across ≥2 independent sources per card (Scryfall + secondary:
MTGRocks, Cards Realm, Wargamer, Untapped, Pojo, MTGGoldfish, CardKingdom).
api.scryfall.com is egress-blocked in this environment, so this is
source-agreement verification, not pixel-verification against rendered images —
the one residual (low-risk) step before lock.

**Headline: no verdict changes.** Every previously-uncertain text resolved in
favor of the registered blind-evaluator verdict.

| Card | Was | Verified | Verdict impact |
|---|---|---|---|
| Cosmic Cube | text single-source; trigger uncertain (attack vs cast) | {5}, Ward {2}, **"whenever you attack"** | none — NOT PLAYED was conditioned on attack-trigger |
| The Fantasticar | animation cost uncertain | animation is **free** (no crew/mana) | none — FRINGE was conditioned on free animation |
| Mjölnir | discard sweeper [UNVERIFIED] | confirmed exists; ETB is "up to one target" | none — NOT PLAYED |
| Hawkeye's Bow | cost guessed {1} | cost is **{R}** | none — NOT PLAYED at any cost |
| T'Challa back | back face [UNVERIFIED] | Black Panther 3/3, double strike, dmg prevention | none — back face irrelevant |
| Galactus | chapters I–III unknown | I destroy nonland perm; II/III each opp −2; IV 16/16 | none — NOT PLAYED |
| Mole Man | [VERIFIED] | confirmed verbatim (subtype Human Villain) | **PLAYED holds** (live call, now confirmed) |
| Namor | [VERIFIED] | confirmed verbatim (token = blue-pip count) | **FRINGE holds** (live call, now confirmed) |

Minor factual corrections (verdict-neutral): Cosmic Cube collector # #245→#312;
Hawkeye's Bow {1}→{R}; fuller subtypes on Mole Man/Namor/Thanos. Set facts
confirmed: MSH main set is Standard-legal (∴ Legacy/Vintage); MSC Commander
cards are Legacy/Vintage/Commander-legal but not Standard-legal; prerelease
2026-06-19, release 2026-06-26. No separate Jumpstart product confirmed (the
non-main product is the four Commander precons) — does not affect any candidate.
