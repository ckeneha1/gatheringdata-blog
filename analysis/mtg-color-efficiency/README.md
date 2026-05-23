# MTG Color Efficiency Analysis

Analysis for the post "Does Color Identity Actually Predict Efficiency?"

## Scripts

- **`permutation_test.py`** — permutation test (η²) and pairwise comparisons (Cohen's d).
  Reads `public/data/mtg-card-power-rankings.csv` and prints results to stdout.
- **`charts.py`** — generates the three post charts and saves them to
  `public/images/mtg-color-efficiency/`.

## Setup

```bash
uv sync
uv run python permutation_test.py   # ~60s for 5,000 permutations
uv run python charts.py
```

## Dependencies

Reads `mtg-card-power-rankings.csv` produced by the `analysis/mtg-card-power` pipeline.
No additional data fetching required.
