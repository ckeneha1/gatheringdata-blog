# Legacy Card Value Model — Rebuild Plan & Registered Prediction Test

**Created:** 2026-06-12
**Status:** Active
**Test vehicle:** Marvel Super Heroes set (spoilers complete 2026-06-08; paper-legal at prerelease 2026-06-19; full release 2026-06-26; Legacy-legal)

---

## ▶ RESUME HERE — current state (updated 2026-06-22)

**This is the cross-session anchor. A fresh session has no memory; read this
block, then the rest of this file, to know exactly where we are.**

**Phase 0 is COMPLETE — predictions are LOCKED.** Commit `637a87d` (2026-06-22)
is the registration; `analysis/legacy-framework/predictions/marvel-super-heroes.md`
is now append-only (grading notes only; per-card verdicts frozen). Do NOT re-run
the lock or alter any verdict.

Done (branch `claude/gracious-albattani-smh3xh`):
- Phase 1.1 provenance refactor; 1.2 clustering, 1.3 exclusions, 1.5 backtest —
  built + fixture-tested (61 tests). 1.4 value model scaffolded + tested.
- Phase 0: 3 predictors registered; Gate 1 (texts) DONE 2026-06-14; **Gate 2
  DONE 2026-06-22** — empirical screen (poor 21.4% recall → logged Phase 1
  defects) + a full-set blind triage of all 525 new cards as the real recall
  gate, which added **#15 Jennifer Walters (FRINGE)** and **#16 Doctor Doom
  (watch)** and flagged that the independent pass did not reproduce the Mole Man
  PLAYED call (logged; verdict unchanged). **Gate 3 (panel) DEFERRED post-lock.
  LOCK DONE.**

Environment: this is a LOCAL session — network works (no egress allowlist), and
the gitignored panel + Scryfall caches are on this machine. The old
container-egress blocker is gone (it was specific to the ephemeral web containers).

NEXT ACTIONS (priority order; full detail in §3):
1. **Push** if not already pushed — makes the pre-registration tamper-evident on
   the remote (a local commit timestamp is self-asserted). Owner-gated.
2. **Phase 1.4 real-data** (the immediate build step): `cd analysis/mtg-primers &&
   uv run python build_exclusions.py build` against the real panel/primers, then in
   `analysis/legacy-value-model`: `uv run python value_model.py train` →
   `uv run python value_model.py eval` (held-out pairwise accuracy = the
   does-it-learn-anything gate) → wire prediction incumbents from inferred clusters.
3. **Phase 1 screen fixes** so the screen becomes a trustworthy recall tool: the
   `graveyard` prior ~0 drops Mole Man under min_score; add a new-card/reprint
   filter (format-aware — see `analysis/legacy-framework/open_questions.md`);
   recalibrate min_score. Do NOT hand-tune to the community list.
4. **Gate 3 panel refresh** (optional, ~12h local scrape): `cd
   analysis/mtg-legacy-tournament` → `fetch_data.py` → `build_dataset.py` →
   `infer_archetypes.py --validate`; recompute the field snapshot (conditioning
   refinement, append-only — cannot change locked verdicts).
5. **Phase 2** — model predictions on the same candidate list (target ~2026-07-03).
6. **Phase 3** — grading: re-scrape and grade all predictors at **2026-08-15**.

Tests anywhere: `uv run --with pytest pytest tests/` in each analysis project.

---

## 1. What this project is

Build a falsifiable, reusable system for predicting new-card adoption in Legacy,
then validate it prospectively: given a freshly released set, predict which cards
will see competitive play, in which deck contexts, in which slots — with predictions
locked **before** tournament outcomes exist.

The Secrets of Strixhaven post (`src/content/blog/legacy-card-evaluation.md`) was
a calibration exercise, not a prospective test: it was written ~4 weeks post-release
with adoption data already visible. The Marvel Super Heroes release is the first
genuinely prospective test. The deadline structure of this plan exists because the
clean version of that test requires predictions committed before 2026-06-19.

---

## 2. Design decisions (settled 2026-06-12)

These were settled in discussion and should be treated as the project's ontology.
Changing them requires explicit reconsideration, not drift.

### 2.1 The card is the unit of analysis; archetypes are outputs

An archetype is a compression label for a stable, winning clumping pattern of
cards — an *outcome* of card-level ability-at-cost value, not an input. Same for
"the meta": the field state is an equilibrium of the same optimization process,
made of the same cards.

Consequences:
- Knowledge should be stored as **card-level interaction claims** (e.g. "reactive
  consumable permission antagonizes recursive engine slots"), with archetype files
  as rendered, human-readable views over those claims — not as the storage format.
- Archetype assignment in the data pipeline should be **inferred** (co-occurrence
  clustering), not hand-authored anchor rules. The 12 named archetypes are a
  validation check on the inference — they should fall out, not go in.
- Within-archetype win log-OR is a **confounder control** (conditioning on deck
  context to estimate a card's marginal contribution), not a fact about archetypes.

### 2.2 Card value is conditional, and the conditioning set must be recorded

There is no environment-independent card value. Value = f(card features, card pool,
field composition). Every observation — inclusion, exclusion, win log-OR — must be
stamped with:
- **Pool snapshot**: what was printed/legal at observation time
- **Field snapshot**: the empirical clump-prevalence distribution at observation
  time (computable from the tournament panel for any date)

Cross-era disagreement between observations is *data about the conditional
structure* (interaction curves), not label noise to be averaged away.

Known omission (acceptable for Legacy, required eventually for faster formats):
the field can shift endogenously in response to the card being evaluated. Legacy's
near-stationarity makes first-order conditioning adequate. Logged in
`analysis/legacy-framework/open_questions.md`.

### 2.3 Primers are bootstrap supervision, destined to become a benchmark

Primers exist in the pipeline because play-by-play game data is unobtainable; they
are the only qualitative window into in-play card function. Use them **no more
than necessary**, and only for what the unsupervised decklist-outcome data cannot
provide:
1. **Hypothesis generation** (interaction mechanisms, function/role labels)
2. **Exclusion labels** (see 2.4)

End state: once the model is validated in Legacy (the "liquid market"), primers in
other formats become *test data* — community judgments to grade the model against,
where model-community disagreement in illiquid formats is potential alpha, not
presumed model error. This requires **provenance tagging now**: every claim in the
knowledge base is marked primer-attested vs. data-validated, with a graduation
pipeline (primer claim → tested against tournament data → promoted or retained as
unvalidated hypothesis). Nothing in the trusted core may silently depend on a
primer, or future testing is train/test contamination.

### 2.4 Primer silences are labeled data (the exclusion dataset)

Every card that (a) existed at primer-writing time, (b) is functionally proximate
to a card the primer plays, and (c) goes unmentioned, is an implicit
"below threshold given pool + field" observation. This is the supervision that
turns slot thresholds from expert feel into learnable decision boundaries — the
part that scales to formats nobody on the project knows by hand.

Construction notes:
- LLM extraction cannot capture silence. The negative set is built by **joining**
  primer decklists against a function-similarity index over the full catalog,
  filtered to cards printed before the primer date.
- The Post 2 abilities-per-mana feature set is the similarity metric for defining
  the comparison class ("Brainstorm-like at this cost"). It failed as a quality
  metric; it is serviceable as a similarity metric.
- Exclusion labels carry **confidence weights** based on specification quality:
  primer date known? format optimization depth (how contested was the slot)?
  was the omission addressed in text? — not based on "qualitative = untrustworthy."

### 2.5 Authority is earned via temporal backtests before it is claimed

"Disagreement = alpha" in illiquid formats is only a legitimate reading after
calibration is demonstrated in Legacy. Mechanism: temporal holdouts. Train on
everything ≤ year T, predict adoption of cards printed after T, grade against
the historical record (Wrenn and Six 2019, Uro 2020, Expressive Iteration 2021,
Murktide Regent 2021, Initiative package 2022, Flow State 2026, …). The backtest
record gates how much authority the model claims in public predictions.

In less liquid formats, model-community disagreements are **registered
predictions** with observable settlement: the community converges to the model's
call (price discovery), or early adopters post positive within-clump win log-OR
before the field catches on.

---

## 3. The plan

Two tracks. Track A is on the clock; Track B is the durable build.

### Phase 0 — Lock registered predictions (DEADLINE: 2026-06-19)

Uses the existing expert framework (`analysis/legacy-framework/evaluation.md`),
not the rebuilt model. The discipline that matters is the timestamp.

- [ ] **0.1 Refresh tournament panel** through June 2026
      (`analysis/mtg-legacy-tournament/fetch_data.py`). Recompute the current
      field-composition snapshot — it is part of the predictions' conditioning
      set and gets recorded with them.
      ⚠️ *The scraped dataset is gitignored and exists only on the owner's
      machine. Remote/cloud sessions cannot re-scrape (egress allowlist +
      ~12h runtime). This step runs locally.*
- [ ] **0.2 Ingest Marvel Super Heroes spoiler** from Scryfall (check set codes —
      MAR and MSC are the eternal-legal codes per WPN; filter to Legacy-legal
      cards). 600+ cards.
- [ ] **0.3 Triage** to ~15–30 Legacy-plausible candidates. **Protocol
      (corrected 2026-06-12 — community lists must not generate candidates):**
      - *Generation* is empirical only: signal-type screen (14-signal taxonomy
        + Post 2 features) over the full eternal-legal spoiler. A pipeline
        whose recall depends on community attention cannot scale to illiquid
        formats and cannot detect what the community missed — which is the
        thesis.
      - *Framework verdicts are produced blind*: evaluator sees card text,
        framework files, and field snapshot only. No community commentary,
        no web access. Sentiment-exposed contexts may not write verdicts
        (anchoring).
      - *Community shortlists* have exactly two post-hoc uses: (a) recall
        audit on the screen — every community-flagged card the screen missed
        is a screen bug, logged and fixed; (b) **registered third comparator
        predictor** (baseline vs. framework vs. community consensus, all
        graded). This mirrors §2.3: community judgment is benchmark, not input.
      - Every candidate carries provenance: which generator(s) produced it.
- [ ] **0.4 Write and commit `analysis/legacy-framework/predictions/marvel-super-heroes.md`**
      before 2026-06-19. Per candidate: signal type, archetype/clump fit, slot,
      current occupant, threshold verdict, expected adoption (copies,
      maindeck/sideboard), and the observation that would falsify the call.
      Also register the abilities-per-mana baseline's verdict on each candidate,
      so the baseline-vs-framework comparison is preserved honestly.
      Git commit timestamp = registration timestamp.

### Phase 1 — Infra rebuild (parallel; ~2026-06-15 → 2026-07-10)

- [ ] **1.1 Provenance refactor** of `analysis/legacy-framework/`: tag every claim
      primer-attested vs. data-validated; restructure storage as card-level
      interaction claims; archetype files become rendered views.
- [ ] **1.2 Inferred archetype clustering**: replace anchor-card rules in
      `archetype_cluster.py` with co-occurrence-based clustering. Validation:
      the 12 named archetypes fall out; "Other" share drops materially from 51.5%.
- [ ] **1.3 Exclusion dataset**: date-stamp primers; build function-similarity
      index from Post 2 features; join primer decklists vs. pre-primer-date pool;
      attach pool + field snapshots; assign confidence weights.
- [~] **1.4 Conditional value model**: card features + pool + field state →
      threshold clearance. SCAFFOLDED + tested (`analysis/legacy-value-model/`):
      pairwise preference ranker over the exclusion dataset (X played ≻ Y
      silently omitted), conditional on field via ability×context interactions;
      verdict mapping reproduces the framework threshold rule (beat the weakest
      incumbent). 14 fixture tests green. REMAINING (owner, needs real data):
      train on the real `exclusions.csv`, run `eval` (held-out pairwise accuracy
      — the does-it-learn-anything gate), wire prediction incumbents from
      inferred clusters.
- [ ] **1.5 Backtest harness**: temporal holdouts per §2.5. Produces the
      calibration record that gates Phase 2's authority claims.

### Phase 2 — Model predictions on the Marvel set (lock by ~2026-07-03)

- [ ] **2.1** Run the trained model on the same candidate list; commit timestamped
      model calls. Label honestly: "pre-tournament-data," not "pre-release."
      Three predictors now registered: naive baseline, expert framework, model.

### Phase 3 — Grading and publication (August 2026, after 4–8 weeks of meta data)

- [ ] **3.1** Re-scrape; grade all three predictors against actual adoption and
      within-clump win log-OR.
- [ ] **3.2** Amend the Strixhaven post: frame as calibration/retrodiction.
- [ ] **3.3** New post: the registered-prediction experiment — three predictors,
      all locked before outcomes, graded in public.

### Phase 4 — Cross-format scaling (after Legacy validation only)

Not scheduled. Preconditions: backtest record from 1.5 is strong; provenance
separation from 1.1 is complete (so new-format primers can be test data, not
input). Candidate next formats: Modern or Pauper (eternal-ish pools, deep
MTGTop8 coverage) before rotating formats.

---

## 4. Success criteria

- **Phase 0:** predictions committed before 2026-06-19, each falsifiable
  (named slot, named incumbent, expected adoption, failure condition).
- **Phase 1:** inferred clusters recover the named archetypes; exclusion dataset
  exists with conditioning stamps; every framework claim has provenance.
- **Phase 2:** model predictions differ from the framework's somewhere
  (if they never disagree, the model adds nothing testable).
- **Phase 3:** graded scorecard published. Success is not 100% accuracy; it is
  beating the abilities-per-mana baseline, and knowing *which kinds* of calls
  the framework/model get wrong.
- **Program-level:** the pipeline reruns on the next set with less manual work
  than this one.

---

## 5. Practical constraints (remote sessions)

- `analysis/mtg-legacy-tournament/data/` and `analysis/mtg-primers/data/raw|guides`
  are gitignored — derived datasets live only on the owner's machine. Remote
  sessions can build code and write analysis but cannot regenerate the 87K-deck
  panel (network egress allowlist blocks api.scryfall.com and mtgtop8.com;
  harness WebFetch/WebSearch may partially substitute for small fetches).
- Anything a remote session produces that downstream steps depend on must be
  committed (containers are ephemeral).
