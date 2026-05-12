# MTG Legacy Tournament Overlay — Spec

## 1. Problem Statement

Post 2 scored every Magic card by a static metric: keyword density, semantic complexity, and raw stat efficiency relative to mana cost. That metric captures what a card *says*. This post introduces a second, independent signal: what the competitive community *reveals* it values through actual tournament play.

**These are two different things, and we don't assume one is more correct than the other.** Our metric is derived from card text. Tournament prevalence is derived from revealed player preference under real stakes. Where they agree, confidence in both is higher. Where they diverge, the divergence is the finding — and it could mean several different things:

- The static metric is missing something (e.g., alternative costs, mana denial, cantrip consistency are hard to score from text alone)
- The community has a blind spot or is running a suboptimal consensus (groupthink in established archetypes is well-documented in competitive Magic)
- The card is genuinely powerful but outclassed by Legacy's specific power ceiling
- The card's value is format-specific and our metric, which scores across all ~27K cards, can't capture that context

The research question is: **where do our text-derived power scores and competitive Legacy prevalence diverge, and what does the pattern of divergence suggest about where each methodology has room to improve?**

Legacy is the right starting format. The card pool is enormous (~27K cards) but the tournament meta is narrow (~200–300 cards in regular play). That concentration means signal is dense — the gaps that appear are meaningful, not noise from a scattered field.

---

## 2. Decision It Unlocks

- **For the post:** A comparison of two valuation methodologies — static text analysis vs. competitive revealed preference — with honest characterization of where they agree, where they diverge, and what might explain the divergence in each direction.
- **Metric improvement:** Where divergence is systematic (e.g., all alternative-cost spells score lower than their tournament prevalence predicts), that's a specific, testable hypothesis about a gap in the Post 2 methodology worth addressing in a future iteration.
- **Community insight:** Where our metric scores a card higher than the community plays it, that's either a genuine overlooked card or evidence of meta groupthink — both worth naming.
- **For future posts:** Pipeline is reusable for Modern, Pioneer, Standard by changing the format ID. Banlist-aware filtering is portable across formats.

---

## 3. Inputs and Outputs

### Inputs

| Source | What | How |
|---|---|---|
| `mtgtop8.com/topcards?f=LE&meta={year}` | Flat card frequency (% of decks, avg copies), mainboard + sideboard separately | POST request per year per zone |
| `mtgtop8.com/format?f=LE&meta={year}&cp={page}` | Event ID enumeration, paginated | GET per year per page |
| `mtgtop8.com/event?e={id}&f=LE` | Event metadata: name, date, player count, star count, placements, deck IDs | GET per event |
| `mtgtop8.com/event?e={id}&d={deck_id}&f=LE` | Card list per deck: card name, quantity, mainboard/sideboard | GET per deck |
| MTGJson ban history (`mtgjson.com/api/v5/Legacy.json`) | Per-card ban/unban dates for Legacy | Single fetch, cached |
| `public/data/mtg-card-power-rankings.csv` | Card power scores from Post 2 | Local file |

### Year meta IDs (MTGTop8)
- 2022: `meta=237`
- 2023: `meta=245`
- 2024: `meta=275`
- 2025: `meta=316`

### Outputs

| File | Description |
|---|---|
| `data/raw/topcards_{year}_{zone}.json` | Flat card frequency from topcards endpoint, one file per year per zone |
| `data/raw/events_{year}.json` | Event metadata list per year (id, name, date, player_count, stars) |
| `data/raw/event_{id}.json` | Per-event: placements, deck IDs, archetype names |
| `data/raw/deck_{id}.json` | Per-deck: card list with quantity and zone |
| `data/banlist.json` | Legacy ban history: card name, action (ban/unban), date |
| `data/decks.csv` | Master flat table: one row per (event_id, deck_id, card_name, quantity, zone) with all event metadata joined |
| `data/card_metrics.json` | Per-card aggregated metrics under all weighting variants |
| `data/gap_analysis.csv` | Final output: card_name, power_score, prevalence_{4 variants}, gap_{4 variants} |
| `public/images/mtg-legacy-tournament/*.png` | Charts (see §7) |

### Master flat table schema
```
event_id        int       MTGTop8 event ID
event_name      str       e.g. "SCG Legacy Open - Columbus"
event_date      date      parsed from DD/MM/YY
player_count    int
star_count      int       prestige proxy (0–3+)
placement       int       1 = winner
deck_id         int       MTGTop8 deck ID
archetype_name  str       e.g. "Dimir Tempo"
card_name       str       normalized
quantity        int       copies in deck
zone            str       "mainboard" | "sideboard"
legal           bool      was card legal on event_date per banlist
```

---

## 4. Architecture

Three scripts, two data stages:

```
fetch_data.py        → data/raw/          (all HTTP, cached, idempotent)
build_dataset.py     → data/decks.csv     (parse + join + banlist filter)
                     → data/card_metrics.json
analyze.py           → data/gap_analysis.csv + charts
```

### fetch_data.py

Four fetch jobs, all rate-limited at 0.5s between requests, all cached (skip if file exists):

1. **`fetch_topcards(year, zone)`** — POST to topcards endpoint with `maindeck=MD|SB` and the year's meta ID. Parse the `<table>` of card rows: card code (row ID), deck count, percentage, avg copies. Cache as `data/raw/topcards_{year}_{zone}.json`.

2. **`fetch_events(year)`** — Paginate through `format?f=LE&meta={meta_id}&cp={page}`. Per page: extract unique event IDs from `href` patterns. Stop when no "Next" link. Cache as `data/raw/events_{year}.json`. Also fetch each event page and cache as `data/raw/event_{id}.json` (event name, date string "DD/MM/YY", player count from "N players - DD/MM/YY" pattern, star count = number of `star.png` occurrences in `meta_arch` div, placements from numbered `event_title` divs, deck IDs from `?e={id}&d={deck_id}` href patterns).

3. **`fetch_decks(event_ids)`** — For each deck ID found across all events, fetch `event?e={eid}&d={did}&f=LE`. Parse `deck_line` divs: `md` prefix = mainboard, `sb` prefix = sideboard. Card name from `onclick="AffCard('{code}','{name}','','')"` (URL-decode, `+` → space). Quantity from text node before `<span class=L14>`. Cache as `data/raw/deck_{id}.json`.

4. **`fetch_banlist()`** — Fetch `https://mtgjson.com/api/v5/Legacy.json`. Extract ban history: list of `{card_name, date, action}` entries. Cache as `data/banlist.json`.

### build_dataset.py

1. Load all cached raw files.
2. Parse event dates (DD/MM/YY → `datetime.date`).
3. Build legality index: for each (card_name, date) pair, determine whether the card was legal using the banlist. A card is legal at date `d` if no ban predates `d` without a subsequent unban. Handle unknown cards as legal (conservative).
4. Assemble master flat table `decks.csv` — one row per (deck_id, card_name, quantity, zone) joined with event metadata. Set `legal` flag.
5. Compute `card_metrics.json` — for each card, under each of four weighting schemes, aggregating only `legal=True` rows:

**Four weighting schemes:**

| Scheme | `weight(deck)` |
|---|---|
| `flat` | 1 |
| `placement` | `max(0, 9 - placement)` — 8 for 1st, 1 for 8th, 0 if unplaced |
| `prestige` | `star_count` (0-star events contribute 0; excluded) |
| `combined` | `(9 - placement) × star_count` |

For each card `c` and scheme `w`:
```
weighted_copies(c, w) = Σ_{decks d containing c, legal} weight_w(d) × quantity(c, d)
total_weight(w)       = Σ_{all decks d, legal} weight_w(d)
prevalence(c, w)      = weighted_copies(c, w) / total_weight(w)
```

Compute separately for `zone=mainboard` and `zone=sideboard`.

Flat mainboard from the `topcards` endpoint is computed independently as a cross-check — it should closely match the `flat` scheme from the deck-level data.

### analyze.py

1. Load `card_metrics.json` and `mtg-card-power-rankings.csv`.
2. Normalize card names: lowercase, strip punctuation, handle known aliases (split cards `Fire // Ice` → `fire ice`; DFCs `Delver of Secrets // Insectile Aberration` → `delver of secrets`).
3. Left join: tournament cards → power scores. Cards with no power score are retained but flagged as `unscored`.
4. Compute gap: `gap(c, w) = percentile_rank(prevalence(c, w)) - percentile_rank(power_score(c))`. Using percentile ranks (0–100) keeps the scales comparable.
5. Generate charts (see §7).
6. Write `gap_analysis.csv`.

---

## 5. Testing Plan

**Contract: the flat topcards metric must agree with the deck-level flat metric within noise.**
Force of Will should appear in ~50% of Legacy mainboards in the topcards data. After scraping individual decks and computing the flat metric from those, the number should be within ~3 percentage points. A large divergence indicates a parsing bug in one of the two paths.

**Spot-check known staples:**
After joining with power scores, Force of Will, Brainstorm, Wasteland, and Ponder should all appear in the high-prevalence / lower-power-score region (they are low-CMC, contextually powerful, but not keyword-dense). If any of these has a *positive* gap (power score > prevalence), something is wrong.

**Banlist sanity check:**
Pick a card that was banned mid-period (check the ban history). Its deck appearances should drop to zero after its ban date in the filtered dataset.

**Weighting sensitivity check:**
Run the top-20 cards ranked by `combined` weighting and compare to the top-20 by `flat`. If they are identical, log a warning — this either means prestige/placement data isn't parsing (all weights = 1) or the meta is genuinely homogeneous (interesting finding, document it).

**Name normalization check:**
After the join, log the count of tournament cards that failed to match any power score entry. Expect <5% miss rate on mainboard staples (some will legitimately be unscored if they postdate Post 2's dataset).

---

## 6. Scale Considerations

**Request volume:**
- ~4 years × ~4 pages/year = ~16 event listing page fetches (negligible)
- ~4 years × ~200 events/year = ~800 event page fetches
- ~800 events × ~6 decks/event = ~4,800 deck page fetches
- At 0.5s between requests: ~2,400 seconds ≈ 40 minutes for initial scrape

This is a one-time cost. All raw files are cached — re-runs skip already-fetched pages. 2022–2024 data is static; only 2025 changes.

**What breaks at 10x:**
If we extend to all formats (Modern, Pioneer, Standard), the deck count grows to ~50,000. Fetching is still fine (cache), but the flat `decks.csv` becomes memory-heavy in pandas at ~2M rows. Switch to DuckDB or chunked processing if extending beyond Legacy.

**MTGTop8 rate limiting:**
The site doesn't publish rate limits. 0.5s between requests is conservative. If requests start returning 429s or empty responses, back off to 1.0s. The scraper should log HTTP status codes and abort gracefully rather than silently dropping data.

---

## 7. Charts

| Chart | What it shows |
|---|---|
| **Scatter: power score vs. prevalence** | One dot per card. X = power score percentile, Y = flat mainboard prevalence. Quadrant labels: "High community value, lower text score" (high Y, low X) and "High text score, lower community value" (high X, low Y). Label top 20 outliers in each quadrant. |
| **Divergence leaderboard** | Two-panel bar chart: top 15 cards where community prevalence exceeds text score (possible metric gap or format-specific value), and top 15 where text score exceeds prevalence (possible community blind spot or outclassed by power ceiling). Cards labeled, no predetermined verdict on which signal is "right." |
| **Weighting sensitivity** | For the top 20 cards by combined-weighted prevalence: grouped bars showing their rank under each of the 4 weighting schemes. Reveals whether weighting changes the story. |
| **Mainboard vs. sideboard** | Scatter: mainboard prevalence vs. sideboard prevalence. Labels cards that are primarily sideboard-only (graveyard hate, combo hate) vs. mainboard-only vs. both. |

---

## 8. Open Questions

- **MTGJson ban history format:** Need to verify that `Legacy.json` contains dated ban/unban entries (not just the current list). If it only has the current list, fall back to parsing the WOTC banned/restricted page for the historical log, or hardcode the ~5 Legacy ban events from 2022–2025.
- **Star count range:** We've seen 1-star events. Need to observe 2- and 3-star events to calibrate the prestige weight scale. If all events in the dataset turn out to be 1-star, prestige weighting collapses to flat.
- **Event listing completeness:** The format page shows "N players - DD/MM/YY" only on event pages, not the listing page. Event listing pages show event IDs but may not show player counts. Confirm player count is available on the event page (confirmed in HTML analysis) and not needed from the listing.
- **topcards card name resolution:** The topcards page identifies cards by set+collector-number code (e.g., `all054`), not by name. The deck-level data gives names directly. For the topcards cross-check, we either map set+number to name via Scryfall or skip name-level matching and just validate aggregate statistics (total inclusion rates should sum similarly).
- **Archetype classification granularity:** MTGTop8 archetype names vary (e.g., "Dimir Tempo", "Ub Tempo" both appear for the same archetype). May need a normalization mapping. Defer to post-analysis if archetype breakdowns become a section.
