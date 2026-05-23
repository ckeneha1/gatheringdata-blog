# gatheringdata-blog

Source for [gatheringdata.blog](https://gatheringdata.blog) — a data science blog publishing quantitative analyses of topics worth measuring.

Each post starts as an independent Python analysis pipeline, gets reviewed through [agent-framework](https://github.com/ckeneha1/agent-framework), and ships as static Markdown on an Astro + Netlify site. The repo is the source of truth — no CMS, no database.

---

## Posts

| Post | Status | Branch |
|------|--------|--------|
| [Thirty Years of Magic Cards, Measured](https://gatheringdata.blog/blog/mtg-distributions) | Published | `main` |
| What Does a Mana Cost Buy You? | In review | `analysis/mtg-card-power` |
| Tobin's Q (working title) | In progress | `analysis/tobins-q-post1` |

---

## Repository layout

```
├── analysis/               # Self-contained Python analysis projects
│   ├── mtg-distributions/  # Post 1: card supply, set cadence, word count over 33 years
│   ├── mtg-card-power/     # Post 2: ability-to-cost ratio and power creep
│   └── tobins-q/           # In progress
├── public/
│   └── images/             # Chart exports — committed, not generated at build time
├── src/
│   ├── content/blog/       # Markdown post files — one per post
│   ├── components/
│   ├── layouts/
│   └── pages/
├── SPEC.md                 # Site architecture and design spec
└── scheduler.yml           # Automated chart update workflow config
```

---

## Analysis projects

Each analysis lives in `analysis/<name>/` as an independent Python project managed with [uv](https://docs.astral.sh/uv/).

### Setup

```bash
cd analysis/<name>
uv sync          # install dependencies into project venv
```

### mtg-distributions (Post 1)

Pulls Scryfall bulk data and measures card supply, set cadence, and word count trends across the full 33,998-card catalog.

```bash
uv run python analyze.py          # full pipeline
uv run python analyze.py charts   # regenerate charts only
```

### mtg-card-power (Post 2)

Measures ability count per mana cost for every non-land card, 1993–present, to quantify power creep. Two classification layers:

1. Scryfall `keywords` field — named keyword abilities, already structured
2. Regex patterns against oracle text — 18 ability categories (card advantage, removal, ramp, etc.)

```bash
uv run python analyze.py
uv run python analyze.py charts keywords semantic total creep distribution
uv run python analyze.py debug other_trigrams   # diagnose unclassified cards
```

Intermediate results cache to `.cache/` (parquet, keyed on Scryfall file mtime). Delete `cards--*.parquet` after changing classification patterns to force a rebuild.

---

## Site development

Built with [Astro](https://astro.build), deployed to [Netlify](https://netlify.com) on push to `main`. Every PR gets a Netlify deploy preview — charts are reviewed there before merging.

```bash
npm install       # dev dependencies
npm run dev       # dev server at localhost:4321
npm run build     # production build to ./dist/
npm run preview   # preview production build locally
```

---

## Workflow

Analysis and writing happens on feature branches. Charts are generated locally, committed to `public/images/`, and reviewed in deploy previews before merging to `main`. Each analysis goes through [agent-framework](https://github.com/ckeneha1/agent-framework) QA before the post ships.
