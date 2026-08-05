# Registered Predictions — The Hobbit (Legacy)

**Status:** 🔒 LOCKED 2026-08-04 — registration timestamp = this file's locking commit. Below the
line is append-only (grading notes only); per-card verdicts frozen.
**Test vehicle:** The Hobbit (HOB Standard-legal + HOC eternal; spoilers complete; prerelease
~2026-08-07, paper release 2026-08-14). Locked **pre-prerelease** — the cleanest prospective test
yet (before any paper play).
**Predictors (four, all registered before outcomes):** abilities-per-mana baseline · expert
framework (blind) · community consensus (held out) · **trained value model (pre-registered this
time, unlike Marvel's post-release model)**.
**Plan reference:** `.agent/briefs/legacy-value-model-rebuild.md` (the next-set rerun; §4).

The second genuinely prospective test, and the first to **pre-register the model** alongside the
others. It also validates brief §4 ("the pipeline reruns on the next set with less manual work"):
fetch → screen → blind triage → 4 predictors, in a single session.

---

## Conditioning set

**Pool snapshot:** all Legacy-legal printings through The Hobbit (HOB + HOC). No B&R changes assumed.

**Field snapshot (Aug 2026, post-Marvel):** Dimir Tempo ~12.5% · **The Fantasticar ~6% (the new
axis Marvel created)** · Izzet/UR Cutter ~6% · Sneak & Show ~6% · Cloudpost/Tron ~5% · UWx Control
~5% · Doomsday ~4% · Eldrazi ~4% · Boros Aggro ~4% · Lands ~3.4% · + Loki midrange. Reactive-
permission, combo, graveyard, and tempo axes all live. (Sources: MTGTop8/aggregator reads,
2026-08-04.)

---

## Method

Candidate list = the union of the blind framework shortlist (`hobbit-triage-verdicts.md`, a full
sweep of all 207 new cards) and the held-out community picks (`community-consensus-hobbit.md`).
Incumbents are named from the framework's slot read, so all four predictors judge the **same slot**
and differ only in *how* they judge "beats the incumbent."

1. **Baseline** (abilities-per-mana): ability count (keywords + effects) ÷ CMC; ≥~1.5 → PLAYED-lean,
   ≈1.0 → FRINGE, <1.0 → NOT PLAYED. Mechanical, front face for DFCs.
2. **Framework** (blind): `evaluation.md` staged checklist, produced from card facts only and
   committed at `51f44af` **before** the community sweep (git-timestamp-proven blind).
3. **Community** (held out): the competitive community's early read (`community-consensus-hobbit.md`).
4. **Model** (`value_model.py predict`): the trained pairwise ranker (leakage-free held-out ≈0.80),
   PLAYED ≥0.60 / NOT PLAYED ≤0.40 / else FRINGE. **Caveat:** evaluates the FRONT face of DFC/
   Adventure cards, so it under-reads adventure-side value (My Precious, Most Decrepit, Gandalf).
   Reproduce: `_build_hobbit_candidates.py` → `hobbit_candidates.json` → `predict`.

**Grading window:** ~2026-10-02 (≈7 weeks of paper + MTGO), graded against MTGTop8 adoption via the
2026 topcards scrape + `_grade_from_topcards.py` (reprints excluded).

---

## Predictions — four predictors compared

| Card | Baseline | Framework | Community | Model (P) |
|---|---|---|---|---|
| **Riddles in the Dark** {2}{U} | NOT PLAYED | **FRINGE** | **FRINGE** | **PLAYED** (0.69) |
| **Bilbo, Thief in the Night** {1}{U} | FRINGE | NOT PLAYED | **FRINGE→PLAYED** | **PLAYED** (0.64) |
| Gandalf, Goblins' Bane {2}{R} | NOT PLAYED | NOT PLAYED | **FRINGE** | NOT PLAYED (0.28) |
| Gollum, Riddle Master {1}{B} | NOT PLAYED | NOT PLAYED | **FRINGE** | NOT PLAYED (0.32) |
| An Unexpected Party {2}{W}{W} | NOT PLAYED | NOT PLAYED | **FRINGE** | NOT PLAYED (no slot) |
| Plunder the Trollshaws {1}{U} | FRINGE | NOT PLAYED (watch) | NOT PLAYED | FRINGE (0.56) |
| Confusticate and Bebother {2}{U} | NOT PLAYED | NOT PLAYED (watch) | NOT PLAYED | NOT PLAYED (0.24) |
| My Precious // Allure of Power | NOT PLAYED | NOT PLAYED (watch) | NOT PLAYED | FRINGE (0.54) |
| Most Decrepit Old Bird // Speak Secrets | **PLAYED** | NOT PLAYED (watch) | NOT PLAYED | FRINGE (0.56) |
| Bilbo's Deadly Slice {1}{B}{B} | NOT PLAYED | NOT PLAYED (watch) | NOT PLAYED | NOT PLAYED (0.18) |

**Tallies:** baseline 1 PLAYED / 2 FRINGE · framework 0 PLAYED / 1 FRINGE · community 0 PLAYED / 5
FRINGE (Bilbo leaning PLAYED) · model 2 PLAYED / 3 FRINGE.

## Discriminating disagreements (where grading separates the predictors)

1. **Riddles in the Dark** — the consensus pick, but graded *up* the more bullish you are:
   **model PLAYED (0.69) > framework/community FRINGE > baseline NOT.** If it settles as a 1–2-of
   FRINGE, framework + community win and the model over-calls (its Marvel pattern).
2. **Bilbo, Thief in the Night** — **model PLAYED + community FRINGE→PLAYED vs framework NOT PLAYED.**
   The model and community both back the graveyard/DRC engine; the framework says the {1}{U} 2/2 is
   too slow/narrow. The single most informative card (like Mole Man was for Marvel).
3. **Gandalf / Gollum / An Unexpected Party** — **community FRINGE, everyone else NOT.** Community-
   only bullishness — the Marvel-Fantasticar test: does the crowd see something the models don't?
4. **Most Decrepit Old Bird** — **baseline PLAYED, everyone else FRINGE/NOT.** The abilities-per-mana
   rate-without-a-home failure (cheap body, keyword soup), registered honestly.

## Set-level registered claims (framework)

- **No HOB/HOC card reaches PLAYED in Legacy** in the window (operationalized: no new card in ≥1%
  of MTGTop8 Legacy decks — i.e. clearly above the noise floor, well under Fantasticar's 3.4%).
- **No tier-1 maindeck change.**
- At most **1–2 FRINGE**, Riddles in the Dark the likeliest.
- **Recall watch (the Loki lesson):** everyone — including the empirical screen — missed Marvel's
  Loki. If a Hobbit card clears PLAYED, the base case is that it is one none of the four predictors
  listed. That is the failure mode to watch.

**Set-level falsification:** wrong if any new card reaches PLAYED (≥1% of Legacy decks), or if a
tier-1 archetype adopts a Hobbit card as a maindeck regular.

---

## Grading notes (append-only, post ~2026-10-02)

*(Empty until grading.)*
