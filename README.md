# gatheringdata.blog

A data science blog by Connor Kenehan. Quantitative analyses of topics worth measuring — currently focused on Magic: The Gathering, with more to come.

Live at **[gatheringdata.blog](https://gatheringdata.blog)**.

---

## What's here

```
├── analysis/               # Self-contained Python analysis projects
│   ├── mtg-distributions/  # Post 1: card supply over time
│   ├── mtg-card-power/     # Post 2: ability-to-cost ratio and power creep
│   └── tobins-q/           # In progress
├── public/
│   └── images/             # Chart exports (committed, not generated at build time)
├── src/
│   ├── content/blog/       # Markdown post files — one per post
│   ├── components/
│   ├── layouts/
│   └── pages/
├── SPEC.md                 # Site architecture and design spec
└── scheduler.yml           # Automated chart update workflow config
```

---

## Blog

Posts are Markdown files in `src/content/blog/`. Each post is written against the completed analysis; charts are static PNGs committed to `public/images/<post-slug>/`.

| Post | Status | Branch |
|---|---|---|
| [Thirty Years of Magic Cards, Measured](https://gatheringdata.blog/blog/mtg-distributions) | Published | `main` |
| What Does a Mana Cost Buy You? | In review | `analysis/mtg-card-power` |
| Tobin's Q (working title) | In progress | `analysis/tobins-q-post1` |

---

## Analysis projects

Each analysis lives in `analysis/<name>/` as an independent Python project managed with [uv](https://docs.astral.sh/uv/).

### Common setup

```sh
cd analysis/<name>
uv sync          # install dependencies into project venv
```

### mtg-distributions (Post 1)

Pulls Scryfall bulk data and measures card supply, set cadence, and word count trends across the full 33,998-card catalog.

```sh
uv run python analyze.py          # full pipeline
uv run python analyze.py charts   # regenerate charts only
```

### mtg-card-power (Post 2)

Measures ability count per mana cost for every non-land card, 1993–present, to quantify power creep.

Two classification layers:
1. Scryfall `keywords` field — named keyword abilities, already structured
2. Regex patterns against oracle text — 18 ability categories (card advantage, removal, ramp, etc.)

```sh
uv run python analyze.py                                      # full pipeline
uv run python analyze.py charts keywords semantic total creep distribution
uv run python analyze.py debug other_trigrams                 # diagnose unclassified cards
```

The pipeline caches intermediate results to `.cache/` (parquet, keyed on Scryfall file mtime). Delete `.cache/cards--*.parquet` after changing classification patterns to force a rebuild.

---

## Site development

Built with [Astro](https://astro.build), deployed to [Netlify](https://netlify.com) on push to `main`.

```sh
npm install       # install dependencies
npm run dev       # dev server at localhost:4321
npm run build     # production build to ./dist/
npm run preview   # preview production build locally
```

Every PR gets a Netlify deploy preview. The build must pass before merging to `main`.

---

## Workflow

- Analysis and post writing happens on feature branches
- Charts are generated locally, committed to `public/images/`, and reviewed in deploy previews
- No database, no CMS — the repo is the source of truth
