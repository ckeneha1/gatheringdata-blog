# Registered Predictions — Marvel Super Heroes (Legacy): Predictor 4 — the trained value model

**Status:** 🔒 REGISTERED 2026-06-29 — registration timestamp = this file's committing commit. Append-only below the line.
**Predictor:** Conditional value model (`analysis/legacy-value-model/`, Phase 1.4) — the trained, mechanical 4th predictor.
**Plan reference:** `.agent/briefs/legacy-value-model-rebuild.md` §Phase 2.

**Timing (honest label):** Produced **pre-tournament-data, NOT pre-release.** The set released
2026-06-26; no competitive Legacy results exist yet. The other three predictors (baseline,
framework, community) were locked **pre-release** 2026-06-22 (`marvel-super-heroes.md`); this one
is registered 3 days post-release but before any outcome data. Nothing post-release informed it
(see Integrity). It registers the trained model's verdicts on the **same 16 candidates** so all
four predictors can be graded together at 2026-08-15.

---

## Method

- **Model:** pairwise preference ranker (`value_model.py`), trained on the primer-silence
  exclusion dataset (145,626 pairs — "played card X ≻ silently-omitted neighbor Y", conditional
  on pool + field; brief §2.4). Leakage-free held-out ≈ 0.80 (Phase 1.4, `_eval_dedup.py`).
  Mechanical — no human discretion at prediction time.
- **Verdict rule:** for each candidate vs its incumbents, P(candidate ≻ weakest incumbent);
  **≥0.60 → PLAYED, ≤0.40 → NOT PLAYED, else FRINGE.** No incumbents (no archetype slot) → NOT PLAYED.
- **Incumbents:** named from the registered (locked) framework verdicts (`framework-verdicts-msh.md`).
  ⚠ **Caveat:** inferred-cluster incumbents (needs Gate 3) aren't built yet, so baseline/framework/
  model share the framework's slot definitions and differ only in **how** they judge "beats the
  incumbent." Wiring incumbents from inferred clusters is the documented upgrade.
- **Context:** `field_concentration` scalar from the June 2026 snapshot (top share 0.107).
- **Reproduce:** `analysis/legacy-value-model/_build_msh_candidates.py` → `msh_candidates.json` →
  `uv run python value_model.py predict --candidates msh_candidates.json`.

## Integrity — why this is still a clean prediction

The model's verdicts are fully determined by (a) weights trained on pre-2026 exclusion data,
(b) the locked candidate + incumbent definitions (2026-06-22), and (c) the June field scalar.
No tournament results exist yet and none were consulted; the 3-day post-release gap carries no
outcome information. The model is deterministic — re-running reproduces these verdicts exactly.

## Four-predictor comparison

P = model's P(candidate ≻ weakest incumbent). Baseline/framework/community verdicts are the
locked ones from `marvel-super-heroes.md`.

| Card | Baseline | Framework | Community | **Model** (P) |
|---|---|---|---|---|
| The Fantasticar | FRINGE | FRINGE | PLAYED | **PLAYED** (0.96) |
| Namor the Sub-Mariner | FRINGE | FRINGE | PLAYED | **FRINGE** (0.44) |
| Attuma, Atlantean Warlord | NOT PLAYED | NOT PLAYED | FRINGE-to-PLAYED | **NOT PLAYED** (0.28) |
| King T'Challa // Black Panther | FRINGE/PLAYED | NOT PLAYED | FRINGE | **NOT PLAYED** (0.20) |
| Mole Man, Moloid Master | NOT PLAYED | **PLAYED** | FRINGE | **PLAYED** (0.73) |
| Hex Magic | NOT PLAYED | NOT PLAYED | NOT PLAYED | **PLAYED** (0.92) ⚠ |
| Avengers Disassembled | NOT PLAYED | NOT PLAYED | NOT PLAYED | **PLAYED** (0.73) ⚠ |
| World War Hulk | NOT PLAYED | NOT PLAYED | NOT PLAYED | **NOT PLAYED** (0.21) |
| Mjölnir, Hammer of Thor | NOT–FRINGE | NOT PLAYED | NOT PLAYED | **FRINGE** (0.57) |
| Hawkeye's Bow | **PLAYED** | NOT PLAYED | NOT PLAYED | **NOT PLAYED** (no slot) |
| Elektra, Daughter of the Hand | NOT PLAYED | NOT PLAYED | NOT PLAYED | **PLAYED** (0.95) ⚠ |
| Thanos, the Mad Titan | **PLAYED-lean** | NOT PLAYED | NOT PLAYED | **NOT PLAYED** (no slot) |
| Cosmic Cube | NOT PLAYED | NOT PLAYED | NOT PLAYED | **NOT PLAYED** (0.35) |
| The Coming of Galactus | NO VERDICT | NOT PLAYED | NOT PLAYED | **NOT PLAYED** (no slot) |
| Jennifer Walters // She-Hulk | NOT PLAYED | FRINGE | NOT PLAYED | **PLAYED** (0.89) |
| Doctor Doom, Unrivaled | NOT PLAYED | NOT PLAYED (watch) | NOT PLAYED | **NOT PLAYED** (0.29) |

**Model tally: 6 PLAYED, 2 FRINGE, 8 NOT PLAYED.**

## Discriminating disagreements (where grading separates the model)

**The model is systematically more bullish than the framework (6 PLAYED vs 1).** This is the
"rate without context" failure mode: the model compares card features against the named incumbent
but does **not** capture archetype anti-synergy, counterability, or curve fit. Notably the *trained*
model exhibits it, not just the abilities-per-mana baseline — evidence that a features-only pairwise
model inherits the baseline's blind spot. The sharpest registered model-vs-field splits:

1. **Hex Magic** — model PLAYED (0.92) vs framework + community NOT PLAYED. Likely a model error:
   it rates the card-advantage spell over Echo of Eons on features, missing that Hex Magic is dead
   with an empty hand — anti-synergistic with the very Storm/ANT lines that would want a refill.
2. **Avengers Disassembled** — model PLAYED (0.73) vs all others NOT PLAYED. Misses that the land
   mode refunds the opponent a basic and it loses Fiery Confluence's artifact mode.
3. **Elektra** — model PLAYED (0.95) vs all others NOT PLAYED. Misses that her sneak is a
   counterable 3-mana cast and her removal is power-capped (whiffs on Murktide).
4. **The Fantasticar** — model PLAYED (0.96) vs framework FRINGE: clears the weakest flex incumbent
   (Thought Monitor) decisively on features.
5. **Jennifer Walters** — model PLAYED (0.89) vs blind-triage FRINGE.

**Notable agreement on the flagship card.** The model rates **Mole Man PLAYED (0.73)** — siding with
the registered framework, and *against* the independent blind triage's NOT PLAYED. So on the single
most-informative card: baseline NOT PLAYED, framework + model PLAYED, community FRINGE, triage NOT
PLAYED. Mole Man is now the crux of the whole experiment.

## Grading (2026-08-15 — append-only below)

Grade all four predictors against MTGTop8 adoption and within-clump win log-OR. Success for the model
is not raw accuracy but: (a) beating the abilities-per-mana baseline, and (b) revealing *which* card
types it misjudges — the over-bullish PLAYED calls (Hex Magic / Avengers / Elektra) are the test. If
those three flop (expected), the framework's context reasoning beats the model there; if any sees play,
the model caught something the experts dismissed.

*(Empty until grading.)*
