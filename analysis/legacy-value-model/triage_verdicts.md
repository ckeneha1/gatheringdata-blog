# Blind Triage Verdicts — Marvel Super Heroes (MSH / MSC) for Legacy

**Date: 2026-06-22**

Produced **blind** under pre-registration constraints: no web access; the
`analysis/legacy-framework/predictions/` directory was not opened; verdicts derive
**only** from card text (`triage_input.md`), the framework files
(`analysis/legacy-framework/`), general Magic *rules* knowledge, and the June 2026
field snapshot supplied in the task. No community sentiment about this set was used
or available (the set postdates training). This is a **recall safety-check**: the
failure mode being guarded against is a missed sleeper, so borderline cards are
INCLUDED (FRINGE / watch) rather than dropped.

All 525 NEW (non-reprint) Legacy-legal cards were read in full and triaged.

---

## Method recap

Threshold rule (from `framework.md` §5, `evaluation.md` Q6–Q7): a card earns play
iff, in some viable archetype, it **beats the weakest incumbent in its functional
slot**, conditional on the pool + field. "Roughly equivalent" defaults to NOT
PLAYED. Cheap-card bias: ≤1 strongly favored, ≤2 favored, ≥4 heavily penalized
unless it cheats cost or ends the game. Cross-archetype-staple convergence (C10)
and the time-profile taxonomy (H4) were applied where relevant.

---

## Triage criteria (the rejection pass — so it's auditable)

I dropped a card to NOT PLAYED without individual write-up if it matched one or more
of these buckets. The overwhelming majority of the 525 fell here. This set is a
"Universes Beyond" Standard + Commander product; its design center is multiplayer /
limited, not eternal constructed.

1. **Vanilla / French-vanilla creatures** (keyword soup, no constraint served):
   e.g. Quicksilver, Pietro Maximoff; The Whizzer; Scarlet Witch, Wanda Maximoff;
   Warriors of Wakanda; Glamorous Grapplers; A.I.M. Bot. Bodies that don't beat
   incumbents on rate.
2. **Commander / multiplayer payoffs** — text keyed to "your commander," the
   command zone, the **monarch**, "each opponent" politics, or 3+ player value:
   M'Baku; Nakia; Everett K. Ross; Okoye, Mighty and Adored; Hatut Zeraze Strike
   Force; Jocasta; W'Kabi; T'Chaka; Endless Ranks of HYDRA; etc. Legacy is 1v1.
3. **"Plan"/"Saga"/"Behold"/"Teamwork"/"Power-up" build-arounds** that require a
   board and multiple turns to pay off. Power-up's cost-reduction only offsets the
   creature's *own* MV the turn it lands (e.g. a {U} 1/1 with power-up {5}{U} costs
   {5} that turn) — these are slow midrange engines, anti-synergistic with every
   tempo/combo/Lands time profile in the field.
4. **Overcosted effects vs. a known cheaper incumbent** — removal/counters/
   reanimation/cantrips that cost more than the established Legacy card for that job
   (detailed cases below where the comparison is close enough to be worth showing).
5. **Pure midrange "good-stuff" legends** (the bulk of the set): 2–5 mana legendary
   creatures with attack-triggers, connive, draw-on-combat-damage, +1/+1-counter
   synergies. None create a turn-1–3 clock, free interaction, mana denial, a lock,
   or a cost-cheat. They serve `archetype_synergy`/`tempo` at magnitudes far below
   Legacy incumbents (DRC, Murktide, Orcish Bowmasters, Ragavan-tier).
6. **Restricted-mana / colorless-by-default lands & "Vibranium"/Treasure rocks**
   that don't fix Legacy manabases, aren't Sol-lands (tap-for-2), aren't Loam
   recursion targets, and don't make *free* mana. See the lands note below.

Categories I specifically swept for recall (per the task's "pay special attention"
list): cheap interaction, cantrips, free/alt-cost spells, mana denial, **lands**,
**Merfolk** enablers, **graveyard**-axis cards, and **cost-cheat / fast-clock**
cards. Findings for each are documented below, including the near-misses I rejected.

---

## SHORTLIST (PLAYED / FRINGE / watch)

### FRINGE

#### Jennifer Walters // The Sensational She-Hulk — FRINGE (front face is the reason)
`{1}{W}` 2/3 legendary creature. Front-face static: **"Your opponents can't cast
spells during your turn."**

- **Signal type:** `protection` + `lock_piece` (a permission *substitute*, the
  rarest and most format-relevant function in this set). It blanks instant-speed
  interaction — Force of Will, Daze, Swords to Plowshares, Bowmasters, removal — on
  *your* turn.
- **Archetype + slot:** (a) protection for combo turns in **Sneak and Show /
  Storm / Doomsday** — resolve your payoff through a counter-wall; (b) a cheap
  disruptive hatebear in **Death & Taxes / white tempo**, taxing reactive decks.
- **Incumbent it competes with:** Teferi, Time Raveler (`{1}{W}{U}`, the gold
  standard "opponents act only at sorcery speed," but 3 mana and a blue splash).
  Jennifer is a **mono-white 2-mana creature** doing a narrower version of the
  Teferi static — cheaper, splashless, tutorable by creature tutors, recurable.
  Also adjacent to Thalia, Guardian of Thaben as a white 2-drop tax body.
- **Clears the bar?** Marginally, on cost/color — this is a genuinely new cheap
  permission-substitute, and the field is tempo- and permission-heavy (the exact
  metagame this hoses). Held back to FRINGE (not PLAYED) because a **2/3 dies to
  every cheap removal/ping in the field** (Bolt, Push, Bowmasters, Solitude,
  Plague Engineer-types) and the static only bites on your own turn, so it doesn't
  stop sorcery-speed hate or proactive disruption. Real but fragile.
- **Falsification:** if, after data exists, it shows **no** SB/MD presence in any
  white tempo/hatebears list or as combo protection (e.g. it never appears in
  Sneak-Show/D&T 75s), the FRINGE call is wrong — downgrade to NOT PLAYED.

### Watch (NOT PLAYED, but flagged for a second look)

#### Doctor Doom, Unrivaled — watch
`{2}{B}{B}` 4/4 lifelink. **"{T}: You draw a card and lose 1 life. Then if your
library has no cards in it, you win the game."**

- **Signal type:** `combo_piece` (alternate win-con) + `card_advantage`.
- **Archetype + slot:** a Thassa's Oracle / Laboratory Maniac–style "win when decked"
  payoff, plus a self-mill/draw engine — theoretically relevant to **Doomsday** and
  draw-your-deck combo as a backup win that also assembles the win.
- **Incumbent it competes with:** Thassa's Oracle (`{U}{U}`, **immediate** ETB win,
  no survival needed) and Jace, Wielder of Mysteries / Lab Maniac.
- **Clears the bar?** No. At `{2}{B}{B}` it must **survive a full turn cycle and be
  untapped** to win — telegraphed, removal-vulnerable, and off-color for the blue
  combo shells. Strictly worse than Thassa's Oracle for the established job.
- **Why flagged anyway:** it's a *new* 4-mana "you win the game" engine that *also*
  draws your library, which is a novel shape; recall demands we not bury it.
- **Falsification:** appears as a Thassa's Oracle alternative or a dedicated mill-Doom
  win in any combo list → upgrade. (Expected: it does not.)

#### Jersey-of-honorable-mentions I considered and rejected, listed for audit
These are the closest NOT-PLAYED calls in each "pay special attention" lane. None
make the shortlist; documented so the rejection is reviewable.

- **Dark Deed** `{1}{B}` instant, −4/−4. Removal slot. Incumbents: Fatal Push
  (`{B}`), Dismember (`{1}{B/P}{B/P}`, −5/−5, castable for 1 mana + 4 life),
  Snuff Out (free). −4/−4 at `{1}{B}` doesn't kill Murktide/large threats and is
  out-flexed by Dismember/Push. **NOT PLAYED.** (Falsify: shows up as a maindeck
  removal 4-of in a B tempo deck.)
- **Repulsor Rays** `{R}` sorcery, 3 dmg to a creature. Strictly worse than
  Lightning Bolt (instant, any target) for the burn/removal slot. **NOT PLAYED.**
- **Pym Particles** `{U}` — draw a card + make a creature unblockable/vigilant.
  Cantrip + evasion, but **no card selection**, so it can't approach the
  Brainstorm/Ponder/Preordain threshold for the cantrip slot; as an unblockable
  enabler it's a worse Slip Through Space. **NOT PLAYED.** (Falsify: appears as the
  evasion enabler in a creature-combo kill.)
- **Quicksilver, Brash Blur** `{R}` 1/1 haste — **"may begin the game on the
  battlefield"** (only such card in the set). A free turn-0 body, but a vanilla 1/1
  with no protection and no mana production. Fails both Oops/combo tests
  (`oops.md`: must accelerate the combo *or* protect it at zero cost — this does
  neither) and doesn't beat DRC as a Delver threat. **NOT PLAYED.**
- **We Say Thee Nay!** `{1}{U}` — Mana Leak that taxes 2 (4 with teamwork).
  Soft counters are outclassed by Daze (free) / Force of Will / Spell Pierce in
  Legacy tempo. **NOT PLAYED.**
- **Dismissive Denial** `{2}{U}{U}` — hard counter + basic landcycling. Four-mana
  hard counters don't see Legacy play (Counterspell is `{U}{U}`). **NOT PLAYED.**
- **Too Evil to Stay Dead** `{2}{B}` — teamwork reanimation (MV≤4 baseline; any
  with a power-4 board). Reanimate (`{B}`)/Animate Dead/Exhume (`{1}{B}`) dominate;
  needing a board to hit fatties is anti-tempo. **NOT PLAYED.**
- **Attuma, Atlantean Warlord** `{2}{U}{U}` Merfolk lord (+1/+1 to other Merfolk,
  card on attack). Merfolk's incumbent lords are **one-pip** (`{U}{U}`): Lord of
  Atlantis, Master of the Pearl Trident, Merfolk Mistbinder. A 4-mana lord is too
  slow for the aggressive fish shell. **NOT PLAYED.** (Falsify: appears as a 5th–8th
  lord in a Merfolk list.)
- **Hit-Monkey** `{3}{G}` — can't be countered; 3/3 reach/vig/deathtouch/hexproof/
  haste. Resilient but green (off-axis for blue tempo) and a 4-mana 3/3 is too slow
  to clock. **NOT PLAYED.**

---

## Recall sweep notes (the categories the task flagged)

- **Lands / manabase:** No survivors. The gainland cycle (A.I.M. Labs, Asgardian
  Citadel, Hell's Kitchen, …) enters **tapped** — below Legacy's untapped-dual /
  fetch / Horizon standard. Surveillance Room is a slow rainbow (`{1}{T}` for a
  color) worse than City of Brass / Gemstone Mine. The "{T}: C, or dual if you
  control a basic" lands (Dark Fortress, Gathering Place, Gleaming Bastion, Hidden
  Lair, Training Compound) default to **colorless**, which Legacy manabases don't
  want, and are out-fixed by ABUR duals/fetches. None are **Sol-lands** (tap-for-2,
  the Ancient Tomb / City of Traitors class Red Prison & Tron need), none are **Loam
  recursion targets** with on-return value (`lands.md` "what a new card needs"),
  none make **free** mana, and none deny mana. The "Vibranium" token producers make
  **artifact-only** colorless mana — useless for casting Karn/Eldrazi/spells.
- **Free / alternative-cost spells:** No pitch/Force-class permission, no free
  interaction. Sneak (Elektra), Escape, Mayhem, Flashback, Rebound appear but only
  on midrange bodies/spells, never as *free interaction* — off-axis for every
  archetype in the field.
- **Mana denial:** None. No Wasteland/Rishadan Port/Stifle/Pithing Needle class.
  Avengers Disassembled is a 3-mana sorcery LD that *ramps* the opponent — anti-deny.
- **Graveyard axis (Reanimator/Doomsday/Loam):** No `{B}`/`{1}{B}` reanimation
  beating Reanimate/Animate Dead; reanimation here is 3+ mana and conditional. No
  Loam-class recursion engine, no fast deterministic self-mill enabler. The set's
  fatties (The Incredible Hulk back-face, Super-Skrull, Fin Fang Foom, **The Sentry
  — which gifts the opponent a 5/5**) are **worse reanimation/Show targets** than
  Archon of Cruelty / Atraxa / Griselbrand-tier incumbents.
- **Cost-cheat / fast clock:** Quicksilver (free turn-0 body, does nothing) and
  Doctor Doom (4-mana alt-win) are the only genuine cost-cheats, both rejected
  above. No turn-1–2 kill enabler, no Show-and-Tell upgrade, no ritual/Lotus-Petal-
  class free mana.
- **Cheap permission substitute:** the one real hit — **Jennifer Walters** (above).

---

## Final shortlist table (the deliverable)

| Card | Verdict | Archetype + slot | Incumbent it competes with | One-line rationale | Falsification |
|---|---|---|---|---|---|
| Jennifer Walters // The Sensational She-Hulk | FRINGE | Combo protection (Sneak-Show/Storm/Doomsday) + white hatebear (D&T/tempo) | Teferi, Time Raveler; Thalia, Guardian of Thraben | Mono-white 2-mana 2/3 with "opponents can't cast spells on your turn" — cheap, splashless permission-substitute in a permission-heavy field | No MD/SB presence in any white tempo/hatebears or combo-protection 75 once data exists |
| Doctor Doom, Unrivaled | NOT PLAYED (watch) | Alt win-con / draw-your-deck (Doomsday-adjacent combo) | Thassa's Oracle; Jace, Wielder of Mysteries | New 4-mana "win when decked" + self-mill engine, but must survive untapped a full turn and is off-color vs. Thassa's Oracle | Appears as a Thassa's Oracle alternative or dedicated mill-Doom win in a combo list |

**Tally: 525 cards triaged; 2 made the shortlist (1 FRINGE, 1 watch).**
