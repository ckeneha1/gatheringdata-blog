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

## Method

1. Candidate list compiled from full-spoiler community discussion (the remote
   environment cannot ingest the full 600+ card spoiler; the systematic
   14-signal screen over all eternal-legal cards runs locally as a completeness
   check before lock — any additions get evaluated the same way).
2. Each candidate evaluated with the `evaluation.md` staged checklist
   (signal type → archetype fit → magnitude vs. named incumbent).
3. For each candidate, two registered verdicts:
   - **Framework verdict** (this document's prediction)
   - **Abilities-per-mana baseline verdict** (Post 2 heuristic, registered for
     honest comparison)
4. Each prediction states its falsification condition and grading window.

**Grading window:** 2026-08-15 (≈7 weeks of paper + MTGO results), graded
against MTGTop8 adoption and within-clump win log-OR where n permits.

---

## Predictions

*(Pending candidate research — to be filled and locked before 2026-06-19.)*

---

## Grading notes (append-only, post 2026-08-15)

*(Empty until grading.)*
