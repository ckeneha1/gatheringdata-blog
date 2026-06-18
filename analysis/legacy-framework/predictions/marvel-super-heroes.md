# Registered Predictions — Marvel Super Heroes (Legacy)

**Status:** DRAFT — predictions not yet locked
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
- [~] **Run the empirical 14-signal screen** over the full eternal-legal
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
- [ ] **Refresh the MTGTop8 panel** through June 2026; recompute the canonical
      field snapshot and update the conditioning table above. OWNER-LOCAL
      (gitignored cache, ~12h scrape, mtgtop8.com egress-blocked here).
- [ ] **Lock**: set status to LOCKED, commit. After that commit this file is
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

## Grading notes (append-only, post 2026-08-15)

*(Empty until grading.)*
