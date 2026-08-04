# Legacy Card Evaluation Framework

A working knowledge base for evaluating Legacy Magic cards and archetypes.
Built iteratively from data analysis and analytical reasoning. Treat as a living document.

**Structure (provenance refactor, 2026-06-13 — brief §2.1/§2.3):** the
canonical knowledge store is `claims.md` — card-level interaction claims with
provenance tags (`data` / `primer` / `analytical`) and graduation status
(HYPOTHESIS → VALIDATED, or REFUTED). `framework.md` and the archetype files
are **rendered views**: readable narrative over the registry, citing claim IDs
(C1–C10, H1–H5). If a view and the registry disagree, the registry wins.
Primer-derived content may enter only as hypothesis or exclusion label, never
directly as validated knowledge — this keeps primers clean for their future
role as benchmark data.

---

## Files

| File | Purpose |
|---|---|
| `claims.md` | **Canonical claims registry** — provenance-tagged, graduated card-level interaction claims |
| `framework.md` | View: core principles — archetypes as constraints, permission taxonomy, signal type vs magnitude |
| `evaluation.md` | **The toolkit** — ordered questions to work through when assessing a card or archetype |
| `data_interpretation.md` | What the empirical metrics mean, where they break down, known biases |
| `archetypes/delver.md` | View: worked example — Delver |
| `archetypes/red_prison.md` | View: worked example — Red Prison |
| `archetypes/lands.md` | View: worked example — Lands |
| `archetypes/oops.md` | View: worked example — Oops All Spells |
| `predictions/` | Registered prediction experiments (per set): candidates, predictor entries, lock protocol |
| `open_questions.md` | Unresolved tensions, things to investigate |

---

## How to use this

**Evaluating a new card:** Start at `evaluation.md`. It gives you an ordered set of questions. Reference `framework.md` for the principles behind each question and the relevant archetype file for context on specific decks.

**Evaluating an archetype:** Read the relevant file in `archetypes/`. Each file follows the same structure so they're directly comparable.

**Interpreting data from card_features.csv / card_yearly.csv / cooccurrence.csv:** Read `data_interpretation.md` first. Several metrics have known failure modes that will lead you wrong if you don't account for them.

**Refining the framework:** When new evidence or analysis changes a principle, update the specific file it lives in. Note what changed and why. The archetype files are the most likely to need updates as the meta evolves; `framework.md` should be more stable.

---

## Core claims (summary — detail in `framework.md`)

1. An archetype is a recurring set of strategic constraints, not a card list. The cards are implementations; the constraints are what persists.
2. Every archetype has a "permission" structure. Permission types differ in time profile: some bleed out, some are stable, some compound.
3. Evaluating a card requires both signal type (which constraint does it serve?) and signal magnitude (does it clear the threshold?). Neither alone is sufficient.
4. Legacy's card pool is so optimized that threshold effects dominate — being marginally above or below the threshold for a given slot separates format-defining from unplayed.
