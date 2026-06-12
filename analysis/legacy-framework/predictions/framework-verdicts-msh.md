# Framework Predictor — Blind Evaluation Report (registered verbatim)

**Predictor:** Expert framework (`evaluation.md` staged checklist)
**Produced:** 2026-06-12, by a blind evaluator per the protocol in
`marvel-super-heroes.md` §Method: inputs were `candidates-msh.md` (sentiment-
free specs + June 2026 field snapshot) and the framework files only. No
network access; no community commentary; evaluator knowledge cutoff precedes
the set's spoiler season. Report registered unedited below.

---

# BLIND Framework Evaluation — Marvel Super Heroes (MSH/MSC), Legacy
**Predictor:** Legacy evaluation framework (`analysis/legacy-framework/`), applied per `evaluation.md` staged checklist.
**Conditioning:** June 2026 field snapshot in `candidates-msh.md`. No community signal consulted.
**Grading window:** MTGTop8 Legacy results, 2026-06-19 through 2026-08-15.

**Prediction definitions (apply to every card below):**
- **PLAYED** — appears at the stated copy count in ≥25% of the named archetype's MTGTop8 lists in the window (or, for cross-archetype claims, ≥2% of all recorded Legacy decks).
- **FRINGE** — appears in at least one but fewer than 25% of the relevant archetype's lists, predominantly as 1–2-ofs; no stable adoption.
- **NOT PLAYED** — zero appearances, or ≤2 isolated lists across the entire window.

---

## 1. The Fantasticar — {3} Legendary Artifact Vehicle 4/4 (MSC)

**Signals:** threat, archetype_synergy (artifact-spell density), resilience (non-creature most of the time — dodges sorcery-speed removal and Plow/Push windows when not animated).

**Archetype fit:** The animation condition ("cast a noncreature spell") fires near-automatically only in 8-Cast/Affinity, where nearly every spell is a cheap artifact. It fails the Delver/Izzet Cutter cost-structure test: a 3-mana threat with no immediate impact in an 18-land deck is exactly what `delver.md` flags as anti-synergistic, and Izzet's token/threat slot is already held by the deck's namesake at {1}{R}. The four-spells-in-a-turn Construct payoff is real only in 8-Cast nut draws — treat it as a bonus, not the card.

**Current slot occupant:** In 8-Cast, the flex threat slots behind Kappa Cannoneer, Thought Monitor, and Urza's Saga tokens — concretely, Patchwork Automaton or the 3rd–4th Cannoneer.

**Threshold verdict:** Does not clear Kappa Cannoneer (unblockable, ward, scales — actually ends games through blockers; a 4/4 flier does not end games through a Murktide). Against the flex incumbents the case is closer: removal-dodging is genuine resilience in a Plow/Bolt meta, and the animation condition is near-unconditional in this archetype. A conditional, marginal upgrade to a flex slot, not a structural one.

**Prediction:** FRINGE. 1–2 copies in a minority of 8-Cast lists; no stable adoption. **Wrong if** it appears as a 2+ of in ≥25% of 8-Cast/Affinity MTGTop8 lists in the window (under-call) or never appears in any list (over-call).

**Confidence:** Medium-low. Main uncertainty: how tight current 8-Cast flex slots are. The "[animation clause wording approximate]" tag matters little — but if animation turned out to require mana or a crew cost, the verdict drops to NOT PLAYED.

---

## 2. Namor the Sub-Mariner — {1}{U}{U} Merfolk, */4 flying (MSH)

**Signals:** threat, archetype_synergy (Merfolk tribal), tempo (token generation off blue noncreature spells).

**Archetype fit:** Merfolk only. Merfolk's constraints: Vial-deployed creature density, lords stacking, permission that doubles as tribal cards. Namor's body is on-curve and adds the evasion the tribe lacks (flying, scaling power, 4 toughness dodges Bolt). But the token trigger is weak precisely here: Merfolk runs ~12 noncreature spells, and the best ones (Aether Vial) have no blue pips; only FoW (2 tokens) and Daze (1) feed him, and Vial-deployed creatures never trigger anything. In a cantrip-dense Izzet/Dimir shell the trigger fires constantly, but there he's a 3-mana sorcery-speed engine in decks whose threat slots are held by Cori-Steel Cutter ({1}{R}, removal-resilient) and Psychic Frog ({U}{B}) — fails the cost-structure test decisively.

**Current slot occupant:** Svyelun of Sea and Sky and Vodalian Hexcatcher at the {1}{U}{U} slot in Merfolk.

**Threshold verdict:** Svyelun (ward for the team, conditional indestructible, attack-draw) is a strictly better resilience-and-grind package; Hexcatcher is a lord plus free permission. Namor is "roughly equivalent" to the marginal third-best 3-drop — per the quality bar, that defaults to the incumbents holding the slots. The evasion is the only differentiated axis.

**Prediction:** FRINGE. 1–3 copies in some Merfolk lists (Merfolk itself is sub-1% of the field), no stable 4-of adoption. **Wrong if** Namor is a 3–4-of in ≥25% of Merfolk MTGTop8 lists in the window, or never appears at all.

**Confidence:** Medium. Main uncertainty: thin-pool tribal decks adopt new on-tribe mythics faster than the threshold model predicts (the Hexcatcher precedent).

---

## 3. Attuma, Atlantean Warlord — {2}{U}{U} Merfolk 3/4 lord (MSH)

**Signals:** archetype_synergy, card_advantage (attack-trigger draw).

**Archetype fit:** Merfolk only, and it fails Merfolk's cost structure. The deck's curve tops at 3 mana by design — Vial is set at 2 (sometimes 3), lords cost 2, the premium 3-drops are Svyelun/Hexcatcher. A 4-mana lord misses Vial, misses Daze-protected turns, and arrives a full turn after the deck wants to be finishing its board.

**Current slot occupant:** No 4-mana slot exists in Merfolk; effectively competing with Svyelun/Hexcatcher and losing on mana cost. Per `framework.md` §5, one mana of difference is format-defining at this level — here it is disqualifying.

**Threshold verdict:** Does not clear. The lord effect is redundant (Merfolk has 8+ lords at 2 mana) and the draw trigger duplicates Svyelun's at +1 mana with worse defensive text.

**Prediction:** NOT PLAYED. **Wrong if** Attuma appears in 3+ distinct Merfolk MTGTop8 lists in the window.

**Confidence:** High. No verdict-relevant unverified text.

---

## 4. King T'Challa // Black Panther, Hope Enduring — {1}{W}{U} 3/2 flash DFC (MSH)

**Signals:** card_advantage (second-draw trigger; in a Brainstorm format the condition fires on most turn cycles, yours and theirs).

**Archetype fit:** UWx Control or a Dimir/Azorius midrange shell. The trigger is genuinely strong in Legacy — opponents Brainstorm into it, and your own cantrips trigger it. But the body is a 3-mana 3/2 with no protection in a format defining its tempo decks around {U}{B} Psychic Frog and {1}{R} Cori-Steel Cutter. The transform is irrelevant (6 mana sorcery-speed, and the back face is [UNVERIFIED] anyway).

**Current slot occupant:** The direct precedent is Faerie Mastermind ({1}{U}, near-identical trigger restricted to opponents), which is itself only fringe in Legacy. In UWx the 3-mana value-creature slot competes with Stoneforge Mystic packages and planeswalkers.

**Threshold verdict:** Costs one more mana than a card that already failed to stick in the format, adds a white pip, and trades the upside (also counts your own draws — meaningfully better trigger) against a removal-magnet body that dies to every played removal spell at card parity. The conditionality fires reliably; the magnitude per mana does not clear.

**Prediction:** NOT PLAYED. **Wrong if** T'Challa appears as a 2+ of maindeck in ≥25% of any blue archetype's lists, or in ≥10 total MTGTop8 lists in the window.

**Confidence:** Medium. Main uncertainty: the trigger counting your own draws is a bigger jump over Mastermind than the +1 mana suggests; a Brainstorm becoming "draw 4, put back 2" is the kind of small-magnitude shift `framework.md` §5 warns can be nonlinear. The [UNVERIFIED] back face does not affect the verdict — no Legacy line ever transforms it.

---

## 5. Mole Man, Moloid Master — {2}{G} 1/1, lands from graveyard + landfall tokens (MSH)

**Signals:** graveyard, mana_denial (Wasteland-recursion enabler), archetype_synergy, resilience (engine redundancy).

**Archetype fit:** Lands, near-perfectly. Time profile matches (`lands.md`: value compounds indefinitely); it is a second recursion engine — exactly the "additional recursion target / engine redundancy" the archetype file names as a fit. Mole Man + Wasteland is the Crucible lock without dredging; the Moloid tokens give Lands board presence and Delver-blockers from a card it wanted anyway; the attack-mill clause feeds Loam and Punishing Fire. Castable off Mox Diamond/Taiga/Forest on turn 2. Secondary fit: Green Sun's Zenith decks (Maverick) get a tutorable Crucible at X=3.

**Current slot occupant:** Crucible of Worlds (the 0–1 flex copy in Lands lists), and functionally the 5th+ copy of Life from the Loam.

**Threshold verdict:** Clears Crucible: one mana cheaper, in-color, and generates tokens on every land drop including Exploration extras. The honest cost is fragility — a 1/1 dies to Bolt/Plow that opponents hold against Lands anyway (for Marit Lage), and it pays the deck's own Tabernacle. That fragility is why it supplements rather than replaces Loam. Conditionality test: the recursion ability is unconditional; the token clause fires every turn in a deck built to play multiple lands. This is the only card in the set with a clean displacement case.

**Prediction:** PLAYED — Lands, 1–2 copies, maindeck. **Wrong if** Mole Man appears in fewer than 25% of Lands MTGTop8 lists in the window, or only as isolated 1-ofs in ≤2 lists.

**Confidence:** Medium. Main uncertainty: a Bolt-dense meta (Izzet Cutter at 7.8–10.7%) may punish the creature-ness enough that Lands pilots keep the artifact version or no version; and Lands at 4–5% share means few lists to grade.

---

## 6. Hex Magic — {2}{R} Sorcery, exile hand / draw that many / play exiled through next turn (MSH)

**Signals:** card_advantage (nominally — net zero cards; it temporarily doubles hand access).

**Archetype fit:** None passes the cost-structure test. Storm/ANT/TES: produces no mana, no storm efficiency, and is dead with a dumped hand (draws 0 after LED/rituals — directly anti-synergistic with the archetype's signature line; the FoW-in-Lands pattern). Reanimator: it exiles the hand rather than discarding it — the exact opposite of what the archetype's graveyard axis wants. Red Prison: `red_prison.md` is explicit that long-game card advantage is not what the archetype needs. Delver shells: 3-mana sorcery, disqualified.

**Current slot occupant:** Echo of Eons / Wheel of Fortune for red hand-refills; both are strictly better at refilling from empty, which is the only state in which a refill is wanted.

**Threshold verdict:** Fails. The card is best with a full hand, and no Legacy archetype wants to pay 3 mana at sorcery speed while holding a full hand.

**Prediction:** NOT PLAYED. **Wrong if** it appears in 3+ MTGTop8 Legacy lists in the window.

**Confidence:** High.

---

## 7. Avengers Disassembled — {1}{R}{R} Sorcery, modal sweeper / land destruction (MSH)

**Signals:** hate_piece (creature sweep), mana_denial (nominal — the basic-land clause largely refunds it).

**Archetype fit:** The only natural home for a red 3-mana sweeper is Red Prison / Painter / Eldrazi sideboards against D&T, Merfolk, Elves. But note the anti-synergy: the land-destruction mode fetches the opponent a basic — in the one archetype that wants this card, that clause actively repairs the opponent's mana against your own Blood Moon. This is the FoW-in-Lands lesson in miniature: the mode that looks like extra value undermines the archetype's primary lock axis.

**Current slot occupant:** Fiery Confluence ({2}{R}{R}: any combination of 2-to-each-creature / shatter / 2-to-opponent — hits 8-Cast and Painter mirrors too) and Pyroclasm-class cards.

**Threshold verdict:** Fails. One mana cheaper than Confluence but loses the artifact mode (critical in a Saga format) and 3-to-each misses the same things Confluence misses while the land mode is anti-synergistic.

**Prediction:** NOT PLAYED. **Wrong if** it appears in 3+ MTGTop8 sideboards/maindecks in the window.

**Confidence:** High. The "[modal wording approximate]" tag doesn't change the verdict unless the land mode loses the basic-fetch clause entirely — even then, a 3-mana sorcery Stone Rain is below the Wasteland threshold.

---

## 8. World War Hulk — {3}{G}{G} Saga (MSH)

**Signals:** mana_acceleration / combo_piece (one-turn free cast of a red/green creature spell).

**Archetype fit:** None. The cheat clause requires you to already have 5 mana and to cast the fattie the same turn from hand — at that point you nearly could have cast it. Compare the incumbents for cheating creatures into play: Show and Tell ({2}{U}), Sneak Attack, Natural Order ({2}{G}{G}, tutors the body from the library and doesn't need it in hand). The red/green restriction excludes Emrakul, Atraxa, Griselbrand — the actual cheat targets the format cares about.

**Current slot occupant:** Natural Order / Show and Tell. Not close.

**Threshold verdict:** Fails by multiple mana and by target quality. Chapters II–III are battlecruiser text with no Legacy relevance.

**Prediction:** NOT PLAYED. **Wrong if** it appears in any MTGTop8 Legacy list in the window.

**Confidence:** High.

---

## 9. Mjölnir, Hammer of Thor — {3}{R} Equipment (MSH)

**Signals:** tempo (ETB 4 damage = removal stapled to a Stoneforge target), threat (damage doubling), archetype_synergy (equipment packages).

**Archetype fit:** The only Legacy-relevant line is Stoneforge Mystic putting it into play for the ETB removal — SFM dodges the {3}{R} cast, so the red pip only matters for hardcasting. The "worthy" equip restriction (legendary non-Villain red/white) is nearly empty in D&T: Thalia is the lone realistic carrier, and doubling Thalia's damage is not a game plan.

**Current slot occupant:** Kaldra Compleat (the SFM haymaker) and Umezawa's Jitte (the SFM toolbox 1-of).

**Threshold verdict:** Fails. Kaldra brings a 5/5 first-strike haste germ — a threat plus removal-through-blocks; Jitte takes over creature mirrors permanently. Mjölnir's one-shot 4 damage plus a near-uncarryable equipment does not displace either, and D&T's 1-of toolbox slots (Cataclysm-class effects, Pithing Needle equivalents) outvalue a Flame Slash on a stick.

**Prediction:** NOT PLAYED. **Wrong if** it appears in 3+ SFM-deck lists (D&T, UWx Stoneblade) in the window.

**Confidence:** Medium-high. The [UNVERIFIED] discard ability ({2}{R}, discard: 2 to each creature) does not affect the verdict — no SFM deck wants a discarded sweeper at that rate; if the text is wrong, nothing changes.

---

## 10. Hawkeye's Bow — likely {1} Equipment (MSH)

**Signals:** combo_piece (in principle: "becomes tapped" loops), archetype_synergy (none real).

**Archetype fit:** The drain trigger only matters with a repeatable tap/untap engine, and Legacy's playable card pool contains none at competitive rates (the Cephalid Breakfast engine taps nothing; Emry taps once per turn for value already spent). One damage per tap with no loop is unplayably below rate.

**Current slot occupant:** N/A — no archetype has a slot for this effect. Stage 4 check (new archetype): the required support cards (efficient untappers) do not exist in Legacy, which per Q9 ends the evaluation.

**Threshold verdict:** Fails Stage 1 — serves no Legacy-relevant signal at relevant magnitude.

**Prediction:** NOT PLAYED. **Wrong if** it appears in any MTGTop8 Legacy list in the window.

**Confidence:** High. The [UNVERIFIED] mana cost is irrelevant — the verdict is the same at {0}.

---

## 11. Elektra, Daughter of the Hand — {2}{B}{B} Ninja 3/3, Sneak {1}{B}{B} (MSH)

**Signals:** tempo (ETB removal of power ≤3), archetype_synergy (Ninjas).

**Archetype fit:** Ninjas (Yuriko shells) is the only deck that can use the sneak mechanic's attack-return structure, and Dimir Tempo superficially wants the body-plus-removal. Both fail on cost: Ninjas' engine card is Yuriko at ninjutsu {U}{B} — uncounterable by being an activation-like ability, and generating compounding card advantage. Elektra's sneak is explicitly a cast (counterable — into Daze/FoW in a tempo format), costs 3, and her removal is capped at power 3, which hits DRC and Frog but whiffs on Murktide and germ tokens. Dimir Tempo's 3–4 mana slots belong to Murktide-class threats; a 3/3 with a conditional Snuff Out attached doesn't fit the curve.

**Current slot occupant:** In Ninjas: the non-Yuriko ninja slots (and the deck would rather spend 3 mana redeploying enablers). In Dimir: Murktide Regent / the removal suite itself (Snuff Out, Fatal Push), which is cheaper and unconditional.

**Threshold verdict:** Fails both. Conditionality test: sneak requires an unblocked attacker mid-combat — reliable only in the archetype where Yuriko already owns that resource.

**Prediction:** NOT PLAYED. **Wrong if** she appears in 3+ MTGTop8 lists in the window.

**Confidence:** Medium-high. Ninjas posts so few results that grading FRINGE vs NOT PLAYED is noisy; the verdict claim is about the broader format.

---

## 12. Thanos, the Mad Titan — {R}{W}{B} 4/4 deathtouch lifelink (MSH)

**Signals:** threat; the power-up is a one-shot parity sweeper (hate_piece, marginally).

**Archetype fit:** None. No competitive Legacy archetype is in Mardu colors with creature slots at 3 mana — the snapshot's top ten contains zero candidate shells. The activation requires {C}{W}{U}{B}{R}{G} (or {C}{U}{G} the turn he enters): even with ABUR duals, the hard {C} requirement plus five colors is a constraint no real manabase in the format meets incidentally.

**Current slot occupant:** N/A — there is no deck whose slot this contests. The nearest comparison for "efficient gold midrange body" slots is the format's rejection of similar rate monsters whenever the colors don't match an existing constraint set.

**Threshold verdict:** Fails Stage 2 — strong rate, no home. Raw power without a constraint match is explicitly insufficient (`evaluation.md` Q2 stop condition).

**Prediction:** NOT PLAYED. **Wrong if** he appears in 3+ MTGTop8 Legacy lists in the window.

**Confidence:** High.

---

## 13. Cosmic Cube — {5} Artifact, ward {2}, attack-trigger free cast (MSH)

**Signals:** card_advantage.

**Archetype fit:** Only decks that can pay {5} and attack with big bodies: Eldrazi Stompy, Karn Tron shells. But the time profile is wrong: it does nothing the turn it lands, then requires surviving to combat with attackers — a win-more state for these decks. When Eldrazi is attacking with Reality Smasher, it is already winning; when it needs help, Cube does nothing.

**Current slot occupant:** The 4–5 mana haymaker slots in Eldrazi/Tron: Karn, the Great Creator and the top of the threat curve. Karn locks artifacts and fetches a wishboard the turn it resolves; Cube needs a full additional turn plus an established board.

**Threshold verdict:** Fails. Sol-land decks pay for immediate board impact; deferred conditional value is below the slot's threshold.

**Prediction:** NOT PLAYED. **Wrong if** it appears in 3+ MTGTop8 lists in the window.

**Confidence:** Medium-high — the **entire text is [UNVERIFIED — single source]**. If the real card triggers on cast rather than attack, or costs {3}–{4}, the evaluation must be redone (a {3} version in 8-Cast would be a live FRINGE candidate). Verdict as written assumes the listed text.

---

## 14. The Coming of Galactus — {2}{B}{B}{G} Saga (MSH)

**Signals:** threat (chapter IV token).

**Archetype fit:** None. A 5-mana, three-color enchantment that takes four turns to produce its payoff fails every archetype's time profile, including Lands (which wants time but wants its slots to deny resources meanwhile, not idle). As an enchantment it cannot be Reanimated/Animated into play, and no Legacy shell cheats sagas to their final chapter at competitive rates.

**Current slot occupant:** N/A — for "spend big mana, get a giant threat," the incumbents are Show and Tell targets, which arrive turn 1–2, not turn 8.

**Threshold verdict:** Fails Stage 1–2. Chapters I–III are [INCOMPLETE], but no plausible chapter text rescues a 5-mana BBG saga in this format; the verdict would change only if a chapter were itself a format-rate effect (e.g., a one-sided mass resource denial), which the cost and product context make very unlikely.

**Prediction:** NOT PLAYED. **Wrong if** it appears in any MTGTop8 Legacy list in the window.

**Confidence:** High (with the stated incomplete-text caveat).

---

# Set-level verdict

**Aggregate prediction: minimal Legacy impact.** This set contains no free spell, no fast mana, no sub-2-mana cantrip or permission, and no lock piece — none of the signal types that historically clear Legacy's thresholds arrive here at Legacy rates. The one clean adoption case (Mole Man) lives in a 4–5% meta-share archetype.

Specifically:
1. **No card from MSH/MSC reaches the top-20 most-played new cards in Legacy** for the window (operationalized: no MSH/MSC card appears in ≥5% of all MTGTop8 Legacy decklists, 2026-06-19 → 2026-08-15).
2. **No tier-1 archetype (Izzet Cutter, Dimir Tempo, Sneak and Show, Tron) changes its maindeck because of this set** (operationalized: no MSH/MSC card becomes a 2+-copy maindeck regular in ≥25% of any of those four archetypes' lists in the window).
3. Expected total: one PLAYED card in a tier-2 archetype (Mole Man in Lands), one to three FRINGE appearances (Fantasticar, Namor, possibly T'Challa experiments).

**Set-level falsification:** this verdict is wrong if any MSH/MSC card violates (1) or (2) above, or if two or more cards from the set achieve PLAYED status as defined per-card.

**Caveat:** these 14 candidates came from the community-triage generator only; the empirical full-spoiler screen is pending. The set-level verdict covers the full set on the assumption the triage captured the strongest candidates — if the screen later surfaces a free spell / fast mana / lock piece missed here, the set-level claim is at risk independently of the 14 per-card verdicts.

---

# Ranked list — expected Legacy impact (highest first)

| Rank | Card | Prediction | Home |
|---|---|---|---|
| 1 | Mole Man, Moloid Master | PLAYED (1–2 MD) | Lands |
| 2 | Namor the Sub-Mariner | FRINGE | Merfolk |
| 3 | The Fantasticar | FRINGE | 8-Cast/Affinity |
| 4 | King T'Challa // Black Panther | NOT PLAYED (closest miss) | UWx / blue midrange |
| 5 | Elektra, Daughter of the Hand | NOT PLAYED | Ninjas |
| 6 | Mjölnir, Hammer of Thor | NOT PLAYED | SFM packages |
| 7 | Cosmic Cube | NOT PLAYED | Eldrazi/Tron |
| 8 | Hex Magic | NOT PLAYED | — |
| 9 | Avengers Disassembled | NOT PLAYED | (red sideboards) |
| 10 | Attuma, Atlantean Warlord | NOT PLAYED | Merfolk |
| 11 | Thanos, the Mad Titan | NOT PLAYED | — |
| 12 | World War Hulk | NOT PLAYED | — |
| 13 | Hawkeye's Bow | NOT PLAYED | — |
| 14 | The Coming of Galactus | NOT PLAYED | — |

**Scorecard summary:** 1 PLAYED, 2 FRINGE, 11 NOT PLAYED. The framework's discriminating calls — the ones that will separate it from a naive "nothing from a crossover set matters" baseline — are Mole Man (positive call into Lands over Crucible of Worlds) and T'Challa (negative call despite a reliably-firing draw trigger, on the Faerie Mastermind precedent plus the +1-mana threshold rule).
