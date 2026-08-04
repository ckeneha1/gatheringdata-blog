# mtg-primers — primer corpus + exclusion dataset

Two pipelines share this project:

1. **Value-signal extraction** (original): scrape Legacy deck primers, extract
   per-card value signals with the Batches API. Files: `fetch_primers.py`,
   `extract.py`, `patch_primers.py`.
2. **Exclusion dataset** (Phase 1.3 of the value-model rebuild — see
   `.agent/briefs/legacy-value-model-rebuild.md` §2.4): turn what primers
   *don't* mention into labeled "below-threshold" observations. Files:
   `function_index.py`, `build_field_snapshots.py`, `build_exclusions.py`,
   and the shared `../shared/ability_features.py`.

## Why the exclusion dataset

A primer's silences are data. If a card existed when the primer was written,
is functionally close to a card the primer plays, and goes unmentioned, that is
an implicit "not worth the slot, given the pool and field at the time." These
labels turn slot thresholds from expert feel into learnable decision
boundaries — the part that scales to formats nobody on the project knows by
hand. Every observation is stamped with its conditioning set (pool date + field
snapshot) and a specification-quality confidence weight.

## Modules

| Module | Role |
|---|---|
| `../shared/ability_features.py` | Post 2 ability-feature vector (keywords + 18 regex categories), reused as a **similarity** metric. Verbatim copy of `analyze.py` `_PATTERNS`, guarded by an AST parity test. |
| `function_index.py` | Function-at-cost neighbourhood: for a card, the cards with cosine-similar feature vectors at ±1 CMC, optionally filtered to those first-released before a pool date. |
| `build_field_snapshots.py` | Trailing-window archetype shares from the tournament panel → `data/field_snapshots.csv` (the field conditioning stamp). Snapshot dated D summarizes decks strictly before D — no leakage. |
| `build_exclusions.py` | The join: for each played card, its neighbourhood minus the decklist minus text-mentioned cards = silent exclusions. Text-mentioned neighbours route to `mentioned_exclusions.csv` for later LLM classification. Outputs `data/exclusions.csv`. |

## Data interfaces (gitignored — owner's machine only)

- `data/primers.json` (committed): metadata index, archetype → `{url, source,
  fetched_at, char_count}`. **No decklists, no written-date** — only a scrape
  timestamp.
- `data/raw/<slug>.txt`: raw primer text (mention scanning).
- `data/extractions.json`: `extract.py` output, `{slug: {archetype, key_cards:
  [{card_name, ...}], ...}}` — the played-card seed sets.
- `data/primer_dates.json`: manual sidecar mapping archetype → written date
  (`fetched_at` is when scraped, not written). Undated primers are weighted
  down, not dropped. Initialize the template with
  `build_exclusions.py init-dates`.
- `data/field_snapshots.csv`: from `build_field_snapshots.py`.
- `../mtg-legacy-tournament/data/decks.csv`: panel for field snapshots and the
  optional slot-contestedness confidence component. Absent → those components
  are nullable (flagged), not errors (brief §5).
- Scryfall bulk cache (`oracle_cards--*.json`, `all_cards--*.json`) shared with
  the Post 1/2 projects — `function_index.py` finds the newest automatically.

## Run order (local)

```
uv run python fetch_primers.py            # scrape primers → data/raw/ (one-time)
uv run python extract.py run              # value signals → data/extractions.json
uv run python build_exclusions.py init-dates   # write data/primer_dates.json template, then fill it
uv run python build_field_snapshots.py    # data/field_snapshots.csv  (needs the panel)
uv run python build_exclusions.py build   # data/exclusions.csv + mentioned_exclusions.csv
```

## Tests

`uv run pytest` (fixture-only — no real data or network):
`tests/test_function_index.py`, `tests/test_build_exclusions.py` (incl. the AST
parity guard on the shared patterns), `tests/test_build_field_snapshots.py`.
