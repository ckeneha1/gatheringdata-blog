# Registered Predictions — Marvel Super Heroes (Legacy)

**Status:** 🔒 LOCKED 2026-06-22 — the registration timestamp is this file's locking commit. Below the line is append-only (grading notes only); the per-card verdicts are frozen.
**Registration deadline:** 2026-06-19 (paper prerelease; first possible tournament play)
**Predictor:** Expert framework (`analysis/legacy-framework/evaluation.md`), pre-model
**Plan reference:** `.agent/briefs/legacy-value-model-rebuild.md` Phase 0

This document registers falsifiable predictions about which Marvel Super Heroes
cards will see competitive Legacy play, made **before any tournament outcome data
exists**. The git commit timestamp of the locking commit is the registration
timestamp. After registration, this file is append-only: grading notes may be
added below the line at the bottom; per-card predictions may not be edited.

---

## Conditioning set

Per the project ontology (brief §2.2), card value is conditional on pool and
field. These predictions are made against:

**Pool snapshot:** All Legacy-legal printings through Marvel Super Heroes
(spoilers complete 2026-06-08). No B&R changes assumed.

**Field snapshot (June 2026, third-party aggregators; canonical MTGTop8
recompute pending — step 0.1 runs locally):**

| Archetype | MTGGoldfish share | MTGDecks share |
|---|---|---|
| Delver / Izzet tempo | 10.7% | 7.75% (Izzet Cutter) |
| Dimir Tempo | 6.7% | 8.87% |
| Sneak and Show | 6.9% | 5.72% |
| Tron (Trini Karn) | — | 5.85% |
| Lands | 4.0% | 5.09% |
| Reanimator (Rakdos/Dimir) | 4.9% | 3.68% |
| Doomsday | 3.9% | 3.91% |
| Eldrazi Stompy | — | 3.86% |
| UWx Control | — | 3.00% |
| Death and Taxes | — | 2.69% |

Notable vs. the May 2026 snapshot used in the Strixhaven post: Izzet Delver has
declined from ~11.4% as Dimir Tempo variants rose. Field is tempo-heavy with
healthy combo (Sneak and Show, Doomsday, Reanimator) — reactive-permission and
graveyard axes are both live.

Sources: mtggoldfish.com/metagame/legacy, mtgdecks.net/Legacy,
aetherhub.com/Metagame/Legacy (accessed 2026-06-12).

---

## Method (corrected 2026-06-12 — see brief §Phase 0.3)

Three predictors, all registered before outcomes, graded together:

1. **Abilities-per-mana baseline** (Post 2 heuristic). Mechanical: ability
   count (keywords + semantic categories) ÷ CMC, mapped to verdicts by the
   declared rule below. No discretion.
2. **Expert framework** (`evaluation.md` staged checklist). Produced **blind**:
   the evaluator saw only `candidates-msh.md` (sentiment-free card specs +
   field snapshot) and the framework files. No web access, no community
   commentary. Knowledge cutoff precedes the set's spoiler season, so no
   training-data leakage of community opinion is possible.
3. **Community consensus** (`community-consensus-msh.md`, HELD OUT from the
   framework evaluator). The competitive community's early-spoiler judgment,
   registered as a predictor in its own right.

Candidate generation: interim list is community-sourced (provenance tagged) —
an acknowledged recall limitation. **Lock gate:** the empirical 14-signal
screen over the full eternal-legal spoiler runs before registration; any
screen-only candidates get the same blind evaluation, and every community card
the screen misses is logged as a screen defect. Oracle texts marked
[UNVERIFIED] in `candidates-msh.md` must be verified against Scryfall before
lock.

**Grading window:** 2026-08-15 (≈7 weeks of paper + MTGO results), graded
against MTGTop8 adoption and within-clump win log-OR where n permits.

---

## Predictor 1 — Abilities-per-mana baseline (registered)

Declared mapping, fixed before grading: ratio ≥1.5× a same-CMC contemporary
average ≈ 1.0 abilities/CMC → PLAYED-leaning; ≈1.0 → FRINGE; <1.0 → NOT
PLAYED. (Exact same-CMC percentile placement recomputes locally pre-lock; the
counts below are the registered inputs.)

| Card | CMC | Ability count | Ratio | Baseline verdict |
|---|---|---|---|---|
| The Fantasticar | 3 | 3 (flying, animation, tokens) | 1.00 | FRINGE |
| Namor the Sub-Mariner | 3 | 3 (flying, CDA power, tokens) | 1.00 | FRINGE |
| Attuma, Atlantean Warlord | 4 | 2 (lord pump, draw) | 0.50 | NOT PLAYED |
| King T'Challa // Black Panther | 3 | 3 front (flash, draw, transform); ~7 both faces | 1.00 / 2.33 | FRINGE / PLAYED† |
| Mole Man, Moloid Master | 3 | 2 (graveyard lands, tokens) | 0.67 | NOT PLAYED |
| Hex Magic | 3 | 2 (draw, impulse-play) | 0.67 | NOT PLAYED |
| Avengers Disassembled | 3 | 2 (sweep, land destruction) | 0.67 | NOT PLAYED |
| World War Hulk | 5 | 3 (cost cheat, counters, pump) | 0.60 | NOT PLAYED |
| Mjölnir, Hammer of Thor | 4 | 3–4 (ETB damage, doubling, equip[, sweep]) | 0.75–1.00 | NOT PLAYED–FRINGE |
| Hawkeye's Bow | 1 | 3 (pump, reach, ping) | 3.00 | PLAYED |
| Elektra, Daughter of the Hand | 4 | 2 (sneak alt-cost, removal) | 0.50 | NOT PLAYED |
| Thanos, the Mad Titan | 3 | 4 (deathtouch, lifelink, counters, parity wrath) | 1.33 | PLAYED-leaning |
| Cosmic Cube | 5 | 2 (ward, attack-cast) | 0.40 | NOT PLAYED |
| The Coming of Galactus | 4 | ≥1 (token; text incomplete) | n/a | NO VERDICT (insufficient text) |

† Post 2's methodology has no settled DFC convention; both counts registered.
The baseline's top picks are Hawkeye's Bow, Thanos, and double-faced
T'Challa — registered as-is. The baseline is a real predictor here, not a
straw man: it gets graded on these calls.

---

## Predictions — three predictors compared

Full registered entries: baseline above; framework in
`framework-verdicts-msh.md` (verbatim blind report, includes per-card
falsification conditions and PLAYED/FRINGE/NOT PLAYED operational
definitions); community in `community-consensus-msh.md`.

| Card | Baseline (Post 2) | Framework (blind) | Community |
|---|---|---|---|
| The Fantasticar | FRINGE | **FRINGE** (8-Cast, 1–2x) | PLAYED |
| Namor the Sub-Mariner | FRINGE | **FRINGE** (Merfolk, 1–3x) | PLAYED |
| Attuma, Atlantean Warlord | NOT PLAYED | NOT PLAYED | FRINGE-to-PLAYED |
| King T'Challa // Black Panther | FRINGE / PLAYED† | **NOT PLAYED** | FRINGE |
| Mole Man, Moloid Master | NOT PLAYED | **PLAYED** (Lands, 1–2 MD) | FRINGE |
| Hex Magic | NOT PLAYED | NOT PLAYED | NOT PLAYED |
| Avengers Disassembled | NOT PLAYED | NOT PLAYED | NOT PLAYED |
| World War Hulk | NOT PLAYED | NOT PLAYED | NOT PLAYED |
| Mjölnir, Hammer of Thor | NOT PLAYED–FRINGE | NOT PLAYED | NOT PLAYED |
| Hawkeye's Bow | **PLAYED** | NOT PLAYED | NOT PLAYED |
| Elektra, Daughter of the Hand | NOT PLAYED | NOT PLAYED | NOT PLAYED |
| Thanos, the Mad Titan | **PLAYED-leaning** | NOT PLAYED | NOT PLAYED |
| Cosmic Cube | NOT PLAYED | NOT PLAYED | NOT PLAYED |
| The Coming of Galactus | NO VERDICT | NOT PLAYED | NOT PLAYED |
| *Jennifer Walters // She-Hulk* ‡ | NOT PLAYED | **FRINGE** (combo protection / D&T) | NOT PLAYED (unflagged) |
| *Doctor Doom, Unrivaled* ‡ | NOT PLAYED | NOT PLAYED — watch | NOT PLAYED (unflagged) |

‡ Additive, registered 2026-06-22 via the full-set blind triage (Gate 2) — not on the
original community candidate list. See §Gate 2 results and `framework-verdicts-msh.md`.

**The discriminating disagreements** (where grading separates the predictors):

1. **Mole Man** — three-way split: framework PLAYED (clean displacement case
   vs. Crucible of Worlds in Lands), community FRINGE (speculative), baseline
   NOT PLAYED (0.67 abilities/CMC). The single most informative card in the
   experiment.
2. **The Fantasticar & Namor** — community PLAYED vs. framework FRINGE: the
   framework's threshold rule (Kappa Cannoneer and Svyelun/Hexcatcher hold the
   slots) against community hype. Tests whether "roughly equivalent to the
   incumbent defaults to NOT PLAYED" survives contact with tribal/synergy
   enthusiasm.
3. **Hawkeye's Bow & Thanos** — baseline PLAYED vs. both others NOT PLAYED:
   the abilities-per-mana failure mode (rate without a home), registered
   honestly.
4. **King T'Challa** — baseline (DFC counting) PLAYED vs. framework NOT
   PLAYED on the Faerie Mastermind precedent. Framework flags this its
   "closest miss" candidate.

**Set-level registered claims** (framework; see verdicts file for
operationalization): no MSH/MSC card in ≥5% of all decklists in the window;
no tier-1 maindeck change; exactly one PLAYED card (Mole Man), 1–3 FRINGE.

---

## Lock checklist (gates before status → LOCKED, deadline 2026-06-19)

- [x] **Verify [UNVERIFIED] oracle texts** — DONE 2026-06-14 via WebSearch
      (api.scryfall.com egress-blocked, so source-agreement not pixel-verified;
      ≥2 sources/card). Outcome: **no verdict changes** — every uncertain text,
      including the two verdict-critical conditionals (Cosmic Cube attack-trigger,
      Fantasticar free animation), resolved in favor of the registered verdict.
      See `candidates-msh.md` → Verification log. No blind re-evaluation needed.
      Residual (low risk): pixel-verify against rendered images when Scryfall
      access exists.
- [x] **Run the empirical 14-signal screen** — DONE 2026-06-22 (result: 21.4% recall; see §Gate 2 results below). [Original plan retained:] over the full eternal-legal
      MSH/MSC spoiler. TOOLS BUILT (+ tests): a Scryfall fetcher and the screen.
      Three commands in a session WITH api.scryfall.com egress (the allowlist
      now lists it; needs a container created AFTER that edit):
        `cd analysis/legacy-value-model`
        `uv run python fetch_spoiler.py --query "set:msh or set:msc" --out msh.json`
        `uv run python spoiler_screen.py screen --set-json msh.json`
        `uv run python spoiler_screen.py audit --set-json msh.json --community ../legacy-framework/predictions/candidates-msh.md`
      The audit lists community cards the screen missed = screen defects to fix.
      Blind-evaluate any screen-only additions (new dated entries; can only ADD,
      never alter a registered verdict).
- [⏭] **Refresh the MTGTop8 panel** — DEFERRED post-lock (owner's call; conditioning-only, cannot change a new card's verdict). [Original:] through June 2026; recompute the canonical
      field snapshot and update the conditioning table above. OWNER-LOCAL
      (gitignored cache, ~12h scrape, mtgtop8.com egress-blocked here).
- [x] **Lock** — DONE 2026-06-22; status LOCKED above; registration timestamp = the locking commit. Original plan was: set status to LOCKED, commit; after that this file is
      append-only.

**State 2026-06-14:** Gate 1 complete with no verdict impact — the registered
predictions are robust to text verification. Gates 2–3 are blocked in this
environment purely by network egress (api.scryfall.com / mtgtop8.com not in the
allowlist; GitHub etc. work). Both are one-/two-command runs locally; the
tooling and run instructions are in place. The predictions can be LOCKED now on
the verified texts if the empirical screen is accepted as a post-lock recall
audit (it can only ADD candidates, each separately blind-evaluated and dated —
it cannot change an existing registered verdict), or after the local screen +
panel refresh if a pre-lock screen is preferred. That call is the owner's.

---

## Gate 2 results & lock notes (2026-06-22)

**Checklist status at lock** (authoritative; supersedes any in-progress markers
above): Gate 1 ✅ (2026-06-14, no verdict changes) · Gate 2 ✅ (empirical screen +
full-set blind triage) · Gate 3 ⏭ deferred post-lock (MTGTop8 panel recompute,
conditioning-only) · **Lock ✅ (2026-06-22)**.

**Environment note:** the prior blocker was ephemeral-container network egress. This
lock was performed locally, where api.scryfall.com / mtgtop8.com are reachable —
egress is no longer a factor.

**Empirical screen (`spoiler_screen.py`):** ran over 893 unique MSH/MSC cards.
**Recall vs. the community list was poor — 21.4% (3/14)**, missing Mole Man + 10
others, with low precision (112 candidates, including reprints — the screen has no
new-card filter). Per protocol these are **screen defects logged for Phase 1**, not a
reason to alter any verdict, and the screen must not be hand-tuned to the community
list (that re-imports community recall). It surfaced no trustworthy candidate the
triage didn't also see.

**Full-set blind triage (the actual recall gate):** because the screen could not be
trusted as the recall gate, all **525 new (non-reprint) Legacy-legal cards** were
evaluated by a fresh blind evaluator (no community sentiment, no web, `predictions/`
off-limits; record: `analysis/legacy-value-model/triage_verdicts.md`). Outcome: **no
new PLAYED card**; **1 new FRINGE** (Jennifer Walters // She-Hulk, a mono-white
2-mana permission-substitute) and **1 watch** (Doctor Doom, Unrivaled). Both were on
neither the community list nor surfaced usefully by the screen → registered additively
as #15–16 (full verdicts in `framework-verdicts-msh.md`). The independent pass also
**agreed** with the registered NOT PLAYED on Attuma, corroborating that call.

**Robustness flag — Mole Man:** the independent blind pass did **not** reproduce the
registered flagship PLAYED call (it triaged Mole Man to NOT PLAYED). The disagreement
lands exactly on the registered call's own stated main uncertainty (1/1 fragility in a
Bolt-dense field). The registered verdict **stands unchanged** — pre-registration
means we grade the call we made — and the split is logged as evaluator-variance data
and a natural test of that axis at grading. (The sub-agent could not be re-queried for
its explicit rationale — no subagent-continue tool here — so this is grounded in the
triage record + the registered call's documented uncertainty, not fabricated wording.)

**Set-level claim survives the recall sweep.** The set-level caveat flagged risk from
a missed *lock piece*; the sweep found one (Jennifer Walters) but at FRINGE, not
PLAYED. Revised tally incl. additions: **1 PLAYED (Mole Man), 3 FRINGE (Fantasticar,
Namor, Jennifer Walters), 12 NOT PLAYED.** The "≤1 PLAYED / no tier-1 maindeck change
/ 1–3 FRINGE" claims hold.

**Timing:** locked 2026-06-22, before any competitive Legacy outcome data exists (set
releases 2026-06-26; the 2026-06-19 prerelease is sealed/casual, not competitive
Legacy). The nominal 2026-06-19 target slipped, but the prospective integrity —
predictions committed before outcomes — is intact.

---

## Grading notes (append-only, post 2026-08-15)

### Preliminary grade — 2026-08-03 (formal grade still due 2026-08-15)

**Source:** MTGTop8 2026 Legacy topcards (maindeck + sideboard play frequency), scraped
2026-08-03 via `fetch_data.py --years 2026`; `pct` = share of 2026 Legacy decks playing the
card. **Caveats:** (a) the 2026 window includes ~5 pre-Marvel months, so Marvel cards' true
post-release rates run *higher* than shown (dilution); (b) ~5.5 weeks of data, ahead of the
declared 08-15 window; (c) within-clump win log-OR (the deeper metric) awaits a larger
decklist sample. Qualitative calls are robust. Reproduce via
`analysis/legacy-value-model/_grade_from_topcards.py`.

**Actual new-card adoption** (reprints excluded — Swords to Plowshares, Dark Ritual, Lightning
Bolt etc. are MSH reprints, not adoption events):

| Card | 2026 Legacy adoption | Verdict |
|---|---|---|
| **The Fantasticar** | **3.4% MD (325 decks)** | **PLAYED** — the set's Legacy story (≈ Doomsday's 4.2%; community reports higher + ban-watched) |
| **Loki, God of Mischief** | **0.8% MD (76 decks)** | **PLAYED — and on nobody's candidate list** |
| all 16 candidates except Fantasticar | ≤0.1% (≤9 decks) | NOT PLAYED |

**Per-card grade** (registered verdict → ✓/✗ vs actual):

| Card | Actual | Baseline | Framework | Community | Model |
|---|---|---|---|---|---|
| The Fantasticar | PLAYED | FRINGE ✗ | FRINGE ✗ | PLAYED ✓ | PLAYED ✓ |
| Mole Man | NOT (0.1%) | NOT ✓ | **PLAYED ✗** | FRINGE ✗ | **PLAYED ✗** |
| Namor | NOT | FRINGE ✗ | FRINGE ✗ | PLAYED ✗ | FRINGE ✗ |
| Hex Magic | NOT | NOT ✓ | NOT ✓ | NOT ✓ | **PLAYED ✗** |
| Avengers Disassembled | NOT | NOT ✓ | NOT ✓ | NOT ✓ | **PLAYED ✗** |
| Elektra | NOT | NOT ✓ | NOT ✓ | NOT ✓ | **PLAYED ✗** |
| Jennifer Walters | NOT | NOT ✓ | FRINGE ✗ | NOT ✓ | **PLAYED ✗** |
| Hawkeye's Bow | NOT | **PLAYED ✗** | NOT ✓ | NOT ✓ | NOT ✓ |
| Thanos | NOT | **PLAYED-lean ✗** | NOT ✓ | NOT ✓ | NOT ✓ |
| King T'Challa | NOT | FRINGE/PLAYED ✗ | NOT ✓ | FRINGE ✗ | NOT ✓ |
| Mjölnir | NOT | NOT–FRINGE | NOT ✓ | NOT ✓ | FRINGE ✗ |
| Attuma | NOT | NOT ✓ | NOT ✓ | FRINGE-PLAYED ✗ | NOT ✓ |
| Cosmic Cube | NOT | NOT ✓ | NOT ✓ | NOT ✓ | NOT ✓ |
| World War Hulk | NOT | NOT ✓ | NOT ✓ | NOT ✓ | NOT ✓ |
| The Coming of Galactus | NOT | NO VERDICT | NOT ✓ | NOT ✓ | NOT ✓ |
| Doctor Doom | NOT | NOT ✓ | NOT ✓ | NOT ✓ | NOT ✓ |
| *Loki* (unlisted) | PLAYED (0.8%) | missed | missed | missed | missed |

**Findings (all registered before these outcomes):**
1. **Community** best-called the one card that mattered (Fantasticar PLAYED); modest over-calls (Namor, Attuma).
2. **Model = high recall, low precision:** caught Fantasticar (P=0.96) but **5 false-positive PLAYEDs**. The three flagged in `model-verdicts-msh.md` as *likely errors* (Hex Magic, Avengers, Elektra) **all flopped** — the registered failure-mode prediction held exactly.
3. **Framework** was precise on the NOTs (correctly rejected the model's error-cards) but under-called Fantasticar and its lone PLAYED (Mole Man) flopped. **This falsifies the set-level claim** ("no tier-1 change; exactly one PLAYED (Mole Man)") — the real one PLAYED was Fantasticar, which reshaped the field (the new-archetype blind spot, per `open_questions.md`).
4. **Baseline** worst: missed Fantasticar; its two PLAYEDs (Hawkeye's Bow, Thanos) flopped.
5. **Blind-triage vindicated on Mole Man** — its independent NOT PLAYED (vs framework + model PLAYED) was correct.
6. **Shared recall gap = Loki** (0.8%), missed by every predictor **and the empirical screen** — the screen's logged recall defect bit us on a real card. Fix before the next set.

**Net:** no predictor dominated — community caught the winner; the model was boldest (caught it) but noisiest; the framework was most precise but missed the winner and its flagship; the baseline was weakest; everyone missed Loki. Next-set authority (§2.5) weights accordingly.

### Formal grade (2026-08-15)

**Source/methodology:** this session had no local topcards scrape or Scryfall cache
(`analysis/mtg-legacy-tournament/data/raw/topcards_2026_*.json`,
`analysis/mtg-card-power/.cache/oracle_cards--*.json` — both absent; this is a
remote/ephemeral session, gitignored data doesn't exist here), so
`_grade_from_topcards.py` could not be run. Graded via WebSearch instead
(direct WebFetch to mtggoldfish.com, aetherhub.com, mtgdecks.net, and
mtg.cardsrealm.com is egress-blocked in this environment; aggregator snippets
and secondary coverage substituted). **Within-clump win log-OR still requires
a local run** — not computable from search snippets. Quantitative shares below
should be read as corroborating, not exact-reproducible, given the source.

**Headline development since the 08-03 preliminary: The Fantasticar was
banned in Legacy**, per the B&R announcement issued 2026-08-10 (also
restricted in Vintage in the same announcement). Per MTGGoldfish's own
coverage and community reaction, adoption kept climbing after the prelim's
3.4%/325-deck snapshot — aetherhub's rolling window had it at **6.30%** of
the Legacy metagame in early-to-mid August, "running rampant... popping up in
the most varied decks" (combo, fair blue, and colorless piles), with the
turn-one-kill line cited as the banning rationale. This is not a marginal
PLAYED call — it is the strongest possible confirmation of adoption, and it
sharpens rather than changes the 08-03 verdict.

**Loki, God of Mischief — recall miss, now corroborated from multiple
independent sources.** Confirmed as genuine competitive Legacy adoption, not
Commander noise: it slots into **Goblin Welder** and **Cephalid Breakfast**
combo shells as a card-draw engine off targeted-ability triggers (Shuko,
Nomads en-Kor). Coverage: mtgrocks ("sees a ton of play... in particular"),
a dedicated Legacy deck-tech video, and metagame trackers placing it in the
0.4–0.8% range depending on window (the 08-03 prelim's rigorous topcards
figure — 0.8% MD, 76 decks — is the trustworthy number; a live-scrape
snippet's 0.4%/4-deck figure looks like a thinner recent-window slice, not a
contradiction). **Loki was on nobody's registered candidate list** — not the
baseline, not the blind framework, not the community consensus, not the
trained model — and not caught by the empirical 14-signal screen either. It
is the cleanest recall failure in the experiment.

**The other 14 registered NOT-PLAYED cards: no adoption signal found.**
Targeted searches for Namor (Merfolk), Mole Man (Lands), King T'Challa,
Hex Magic, Avengers Disassembled, and Elektra turned up only pre-release set
reviews and card-mechanics descriptions — no tournament decklists, no
metagame-share entries, no "sees play" claims from post-release coverage.
Consistent with the 08-03 topcards read (≤0.1%, ≤9 decks each). No verdict
changes from the preliminary on any of these 14.

**Per-card scorecard (formal; unchanged from 08-03 except Fantasticar's
magnitude and the Loki write-up above):**

| Card | Actual (formal) | Baseline | Framework | Community | Model |
|---|---|---|---|---|---|
| The Fantasticar | **PLAYED → BANNED 2026-08-10** (6.3%+ pre-ban) | FRINGE ✗ | FRINGE ✗ | PLAYED ✓ | PLAYED ✓ |
| Mole Man | NOT (≤0.1%) | NOT ✓ | **PLAYED ✗** | FRINGE ✗ | **PLAYED ✗** |
| Namor | NOT | FRINGE ✗ | FRINGE ✗ | PLAYED ✗ | FRINGE ✗ |
| Hex Magic | NOT | NOT ✓ | NOT ✓ | NOT ✓ | **PLAYED ✗** |
| Avengers Disassembled | NOT | NOT ✓ | NOT ✓ | NOT ✓ | **PLAYED ✗** |
| Elektra | NOT | NOT ✓ | NOT ✓ | NOT ✓ | **PLAYED ✗** |
| Jennifer Walters | NOT | NOT ✓ | FRINGE ✗ | NOT ✓ | **PLAYED ✗** |
| Hawkeye's Bow | NOT | **PLAYED ✗** | NOT ✓ | NOT ✓ | NOT ✓ |
| Thanos | NOT | **PLAYED-lean ✗** | NOT ✓ | NOT ✓ | NOT ✓ |
| King T'Challa | NOT | FRINGE/PLAYED ✗ | NOT ✓ | FRINGE ✗ | NOT ✓ |
| Mjölnir | NOT | NOT–FRINGE | NOT ✓ | NOT ✓ | FRINGE ✗ |
| Attuma | NOT | NOT ✓ | NOT ✓ | FRINGE-PLAYED ✗ | NOT ✓ |
| Cosmic Cube | NOT | NOT ✓ | NOT ✓ | NOT ✓ | NOT ✓ |
| World War Hulk | NOT | NOT ✓ | NOT ✓ | NOT ✓ | NOT ✓ |
| The Coming of Galactus | NOT | NO VERDICT | NOT ✓ | NOT ✓ | NOT ✓ |
| Doctor Doom | NOT | NOT ✓ | NOT ✓ | NOT ✓ | NOT ✓ |
| *Loki, God of Mischief* (unlisted) | **PLAYED** (Goblin Welder / Cephalid Breakfast) | missed | missed | missed | missed |

**Findings:**

1. **Community best-called the one card that mattered**, and mattered more
   than anyone registered for: PLAYED on a card that went on to get banned.
   Its over-calls (Namor, Attuma) are minor relative to that hit.
2. **Model: high recall, low precision, confirmed at scale.** It caught the
   banned card (P=0.96) but posted **5 false-positive PLAYEDs** (Mole Man,
   Hex Magic, Avengers Disassembled, Elektra, Jennifer Walters), all of which
   flopped with no adoption signal found at the formal grading window either.
   Recall on registered-candidate PLAYED calls: 1/1. Precision: 1/6 (16.7%).
   The three the model itself flagged as likely errors (Hex Magic, Avengers,
   Elektra) **all flopped exactly as predicted** — the registered
   failure-mode caveat held.
3. **Framework was precise on the NOTs but wrong on both calls that mattered
   most**: it under-called the eventual banned card to FRINGE, and its lone
   flagship PLAYED call (Mole Man) flopped. **This decisively falsifies the
   set-level claim** ("no tier-1 maindeck change; exactly one PLAYED card
   (Mole Man)") — the real PLAYED card was Fantasticar, and it didn't just
   see tier-1 play, it got **banned** for warping the format. The framework's
   threshold-rule reasoning (beat the weakest incumbent) has no mechanism for
   detecting a new archetype-enabling combo piece, which is exactly what
   Fantasticar was (per the ban rationale: turn-one kills across combo, fair
   blue, and colorless shells) — this is the concrete instance of the
   "new-archetype blind spot" flagged in `open_questions.md`.
4. **Baseline weakest**: missed the banned card entirely (FRINGE) and its two
   PLAYED calls (Hawkeye's Bow, Thanos) both flopped.
5. **Blind-triage vindicated on Mole Man** a second time: its independent NOT
   PLAYED call (against framework + model PLAYED) was correct at both the
   preliminary and formal grading windows.
6. **Loki is the shared recall gap**, missed by all four registered
   predictors *and* the empirical 14-signal screen — the screen's logged
   recall defect (21.4% at Gate 2) cost a real card twice now. Fix the
   new-card/reprint filter and recall calibration before the next set
   (Phase 1 backlog item, brief §NEXT ACTIONS #1).

**Net (formal, supersedes the preliminary's hedge):** community wins this
round outright — it called the winner cleanly, with no compounding false
positives. Model is the best *bold* predictor (matches community's recall,
adds nothing extra correct, costs precision) — useful as a recall net, not
yet a precise oracle. Framework is the best *conservative* predictor but its
one affirmative bet (Mole Man) and its set-level claim both failed, and its
threshold-rule has a demonstrated blind spot for archetype-enabling combo
pieces. Baseline is weakest across the board. Every predictor and the
recall screen missed Loki. Authority weighting for the next registered set
(§2.5): trust community + model for recall, framework for precision on
rejections, and treat "beats the weakest incumbent" as insufficient alone
when a candidate could enable a new line rather than displace an existing
slot.
---

### Window addendum to the formal grade — 2026-08-15

The formal grade above was produced in a remote session with no local panel, and flags that **the within-clump win log-OR still needs a local run**. This note constrains that pending run. Verdicts are unchanged; this is method, not revision.

**The window closes 2026-08-10.** Marvel's clean window is **2026-06-26 → 2026-08-10** (~6.5 weeks), not the ~7 weeks assumed in §Method at registration. A banned card stops accruing adoption on its effective date, so any window running past 2026-08-10 counts decks that *could not* have played it, pulling both `share_*` and `within_log_or` toward zero. `backtest.py` now enforces this: `LEGACY_BANS` clips `window_end` automatically. This is the existing convention (White Plume Adventurer is clipped to its 2023-03-06 ban in `EXAMPLE_ROSTER`), now applied by the code rather than remembered.

This matters for the *next* local run specifically: the panel ends 2026-08-02 as of this writing, so the Phase 3.1 re-scrape is the first to reach past the ban.

**One caution on the aggregator figures above.** The formal grade cites aetherhub's rolling-window 6.30% for early-to-mid August. Any such window that spans 2026-08-10 is already mixing pre- and post-ban days, so treat 6.30% as directional — the grade says as much ("corroborating, not exact-reproducible"). The clipped local run is what settles the magnitude.

**Second labeled case now available.** Candelabra of Tawnos was banned 2026-06-29 ([B&R](https://magic.wizards.com/en/news/announcements/banned-and-restricted-june-29-2026)) and, unlike Fantasticar, has a long pre-ban trajectory in the 2011–2026 panel: 15 decks (2023) → 95 (2024) → 442 (2025) → 263 (2026 partial); as a share of Force-of-Will decks (a scrape-volume proxy), 0.26% → 1.23% → 5.02% → 8.30%. A ~32× rise in share ending in a ban — a retrospective test of whether the pipeline sees bans coming, gradeable now rather than in October. **Caveat before using it:** High Tide itself shows only 4/12/4/3 decks over those years, `card_features.csv` tags Candelabra "Cloudpost / Tron Ramp (12-Post)", and `archetype_card_stats.csv` buckets it under "Other" — the archetype labels need work before this becomes a claim.
