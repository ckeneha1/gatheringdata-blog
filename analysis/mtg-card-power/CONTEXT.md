# Project Context — MTG Card Power Analysis

Structured knowledge-capture file per the routine in `toolkit/working_with_me.md`. Append new sessions as `## Session — <date>` headers.

---

## Session — 2026-04-07

### 1. What we did / learned

**Goal:** Build and publish Post 2 of the gatheringdata.blog MTG series — "What Does a Mana Cost Buy You?" — covering ability-to-cost ratio and power creep across the full 34,000-card catalog.

**Analysis completed (prior sessions):**
- Two-layer classification pipeline built in `analyze.py`: Layer 1 = Scryfall `keywords` field, Layer 2 = regex against oracle text across 18 ability categories.
- All 5 charts generated: keywords per CMC over time, total abilities per CMC over time (with per-CMC breakdown), creep by ability type, distribution shift, exemplar comparison.
- Key findings: CMC=3 cards averaged 1.33 abilities in 1993 vs. 2.31 in 2025 (+74%). CMC=2 mean 1.39 → 1.99 (+43%). Keywords per CMC: 0.17 → 0.35.

**QA session (this session):**
- Identified root cause of Abbey Gargoyles being classified as "other": Scryfall stores `["Flying", "Protection"]` in keywords (not "Protection from red"), so stripping "Protection" left orphaned text `"from red"` that matched nothing. Fixed by pre-stripping `"protection from [qualifier]"` as a full phrase before stripping individual keyword names.
- Fixed 6 total root causes in the "other" bucket (see section 3).
- Reduced "other" from 33% → 25.3% of non-land, non-zero-CMC cards (rescued 2,592 cards).

**Blog post:**
- `src/content/blog/mtg-card-power.md` written from scratch (~2,100 words).
- PR #8 opened on `analysis/mtg-card-power` branch.

---

### 2. How we did it

**Diagnostic approach for the "other" bucket:**
1. Read rows from `other_bucket_trigrams.csv` (output by `analyze.py debug other_trigrams`) — sorted by frequency of the most common trigrams in cards classified as "other".
2. Sampled actual cards from the "other" rows in `cards_classified.csv` to understand what text was being left unclassified.
3. Read MTG Comprehensive Rules PDF (`pdftotext /path/to/MagicCompRules.pdf -`) to get the canonical list of 185 keyword abilities from sections 701 and 702.
4. Cross-referenced against `_PATTERNS` in `analyze.py` to find what was unhandled.

**Tools used:**
- `uv run python analyze.py debug other_trigrams` — generates `other_bucket_trigrams.csv`
- `pdftotext` (via `brew install poppler`) — extract text from MTG comp rules PDF
- `uv run python analyze.py charts keywords semantic total creep distribution` — regenerate charts
- Parquet cache at `.cache/cards--*.parquet`, keyed on Scryfall file timestamp. Must `rm -f .cache/cards--*.parquet` before rebuilding after any pattern changes.
- `git -C "/full/path"` pattern to avoid the apostrophe-in-path `cd` failure.

**Data sources:**
- Scryfall bulk data: `oracle_cards` and `all_cards` types. Fetched via Scryfall bulk data API. Cached locally.
- `first_print_year` mapping: computed from `all_cards` by finding the minimum `released_at` across all printings of each oracle_id.

---

### 3. What worked / what didn't

**Worked:**
- The trigram diagnostic approach was fast and targeted. Looking at top N-grams in "other" text directly surfaced the root causes without needing to write a full audit script.
- Pre-pass A/B/C structure in `strip_keyword_names` cleanly handled the three classes of keyword residual (compound qualifier, parametric, and base name).
- Post-pass B (orphaned trigger clause detection) fixed the Abzan Skycaptain class of phantom count inflation without impacting legitimate multi-clause cards.

**Didn't work / friction:**
- **Parquet cache invalidation**: The cache is keyed on Scryfall file timestamp, not on a hash of `_PATTERNS`. Every time a pattern changed, we had to manually `rm -f .cache/cards--*.parquet`. This caused two incorrect readings early in the session before we understood why numbers weren't updating.
- **`analyze.py charts` with no args**: Threw an argparse error rather than defaulting to "all charts". Required always passing all chart names explicitly.
- **CSVs accidentally staged**: `cards_classified.csv` (63K rows) and `other_bucket_trigrams.csv` (140K rows) were staged in the initial commit. Had to `git restore --staged` to back them out.
- **poppler not installed**: Required a Homebrew install mid-session to read the comp rules PDF. Not a blocker, but added friction.

**Root causes fixed in `analyze.py` (this session):**

| Fix | Cards rescued |
|---|---|
| Ramp pattern: `add[s]? mana` → `add[s]? \{[^}]+\}` (modern oracle text never says "mana") | ~387 |
| card_advantage: `draw a card` pattern didn't match word-spelled numbers (two, three...) | ~277 |
| stax: `"doesn't untap during its controller's untap step"` not handled | ~169 |
| protection-from qualifier stripping: pre-pass now strips full phrase before stripping base keyword | ~131 |
| parametric keyword residuals: `Bloodthirst 3`, `Modular 2` etc. left bare digit | ~130 |
| Added `protection` and `evasion` as new categories (were in spec, not implemented) | ~100 |
| ~50 additional named keyword abilities from sections 701/702 not in `_PATTERNS` | ~1398 |
| **Total** | **~2,592** |

---

### 4. How to improve

- **Parquet cache should include a pattern hash.** The current cache key is `Scryfall file mtime`. It should be `hash(Scryfall mtime + sha256(serialize(_PATTERNS)))`. This would auto-invalidate on any pattern change and eliminate the manual `rm` step.
- **`analyze.py charts` should default to all charts.** Passing all names explicitly every time is noisy. A `charts --all` flag or argparse default would clean this up.
- **`.gitignore` should explicitly exclude the large CSVs.** `cards_classified.csv` and `other_bucket_trigrams.csv` are large diagnostic outputs, not source data. They should be in `.gitignore` to prevent accidental staging.
- **The "other" category still at 25%.** Remaining sources: triggered abilities where the trigger condition doesn't encode the effect (e.g., "Whenever this creature attacks..."), Aura text ("enchanted creature gets +X/+X"), and lord effects ("other creatures you control have..."). These require either clause-level parsing or a different classification approach (possibly Claude API for the residual).
- **Abbey Gargoyles class of residual**: Worth another audit pass after the current changes settle. The protection-from fix and parametric fix likely cover the main cases, but there may be other compound keywords (e.g., "ward — discard a card") that leave similar orphans.

---

### 5. Automation opportunities

**A. Pattern hash cache key**
- What: Add `sha256(str(_PATTERNS))` to the parquet cache key so pattern changes auto-invalidate.
- Input: No change to the analysis interface. Change is internal to `_cache_path()` or wherever the parquet path is constructed.
- Output: Analysts never need to manually `rm .cache/cards--*.parquet`.
- Effort: ~10 lines.

**B. `.gitignore` update**
- What: Add `cards_classified.csv`, `other_bucket_trigrams.csv`, and any other large diagnostic CSVs to `.gitignore`.
- Effort: 3 lines.

**C. `analyze.py charts --all` default**
- What: If no chart names passed to `charts` subcommand, run all charts. Or add a `--all` flag.
- Effort: ~5 lines of argparse change.

**D. Residual audit script**
- What: A script (or `analyze.py debug residual_audit`) that samples N cards from "other" and, for each, shows: original oracle text, stripped oracle text, why nothing matched. Currently this is done manually by reading CSVs. A structured audit loop would surface new root causes faster.
- Input: `other_bucket_trigrams.csv` + `cards_classified.csv`.
- Output: A sorted report of "un-matched text fragments" with frequency + example cards.
- Effort: ~50 lines.

---

### 6. Recommendation on item 5

| Opportunity | Recommendation | Reasoning |
|---|---|---|
| A. Pattern hash cache key | **Build now** | Directly fixes a repeated friction point that caused bad data in this session. Tiny effort. |
| B. `.gitignore` update | **Build now** | Two-minute fix. Prevents future staging accidents. |
| C. `charts --all` default | **Build now** | Trivial. The explicit-names pattern is just noise. |
| D. Residual audit script | **Defer** | The "other" bucket is now at 25% and the remaining sources are structurally harder (triggered abilities, auras). We need to decide whether to tackle those before building more tooling around diagnosing them. Revisit at start of next analysis session. |

---

### 7. Outcome

- **A (pattern hash cache key):** Not yet built. Deferred to next session — didn't want to modify `analyze.py` after charts were generated and committed.
- **B (`.gitignore` update):** Not yet built. Deferred alongside A.
- **C (`charts --all` default):** Not yet built. Deferred alongside A.
- **D (residual audit script):** Deferred per recommendation.

All three quick wins (A, B, C) should be the first commits on the next session touching `analyze.py`.
