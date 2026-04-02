"""
MTG card distribution analysis for gatheringdata.blog post:
"Thirty Years of Magic Cards, Measured"

Data source: Scryfall bulk data API (oracle_cards)
  - One entry per unique card (reprints deduplicated)
  - No auth required
  - Updated daily

Outputs: PNG charts to ../../public/images/mtg-distributions/
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import requests

# --- Config ---

OUTPUT_DIR = Path(__file__).parent.parent.parent / "public" / "images" / "mtg-distributions"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Blog accent color from global.css
ACCENT = "#b2d4e5"
ACCENT_DARK = "#7aafc9"
TEXT = "#363737"
TEXT_SECONDARY = "#868787"
BORDER = "#dddddd"

# Scryfall excludes digital-only cards, tokens, and joke sets by default in oracle_cards.
# We additionally exclude: oversized cards, art cards, memorabilia.
# This keeps us on tournament-legal + near-legal card types.
EXCLUDED_LAYOUTS = {"token", "emblem", "art_series", "reversible_card"}


# --- Data fetching ---

def fetch_oracle_cards() -> list[dict]:
    """
    Pull oracle_cards bulk data from Scryfall.
    Returns a list of card dicts (one per unique card).
    """
    print("Fetching bulk data index from Scryfall...")
    index_resp = requests.get(
        "https://api.scryfall.com/bulk-data",
        headers={"User-Agent": "gatheringdata-blog-analysis/1.0"},
        timeout=30,
    )
    index_resp.raise_for_status()

    bulk_files = index_resp.json()["data"]
    oracle_entry = next(f for f in bulk_files if f["type"] == "oracle_cards")

    download_url = oracle_entry["download_uri"]
    updated_at = oracle_entry.get("updated_at", "unknown")
    print(f"Downloading oracle_cards (updated {updated_at})...")
    print(f"URL: {download_url}")

    data_resp = requests.get(
        download_url,
        headers={"User-Agent": "gatheringdata-blog-analysis/1.0"},
        timeout=120,
        stream=True,
    )
    data_resp.raise_for_status()

    # Stream into memory — file is ~100MB
    chunks = []
    total = 0
    for chunk in data_resp.iter_content(chunk_size=1024 * 1024):
        chunks.append(chunk)
        total += len(chunk)
        print(f"\r  Downloaded {total / 1024 / 1024:.1f} MB...", end="", flush=True)
    print()

    cards = json.loads(b"".join(chunks))
    print(f"Loaded {len(cards):,} cards from Scryfall oracle_cards")
    return cards


# --- Data prep ---

def build_dataframe(cards: list[dict]) -> pd.DataFrame:
    """
    Flatten card dicts into an analysis-ready DataFrame.

    Key fields:
    - released_at: release date of the set Scryfall selected as the canonical
      printing. Not guaranteed to be the absolute first printing, but close
      enough for year-over-year analysis.
    - mana_value: CMC. Scryfall has used both "cmc" and "mana_value" as field
      names across API versions — we handle both.
    - oracle_text: normalized card text, empty string for cards with no text.
    """
    rows = []
    for card in cards:
        if card.get("layout") in EXCLUDED_LAYOUTS:
            continue

        # Handle cmc/mana_value field rename
        mana_value = card.get("mana_value") or card.get("cmc")

        rows.append({
            "name": card.get("name"),
            "released_at": card.get("released_at"),
            "set": card.get("set"),
            "set_name": card.get("set_name"),
            "rarity": card.get("rarity"),
            "colors": card.get("colors", []),
            "color_identity": card.get("color_identity", []),
            "type_line": card.get("type_line", ""),
            "oracle_text": card.get("oracle_text", ""),
            "mana_value": mana_value,
            "layout": card.get("layout"),
        })

    df = pd.DataFrame(rows)
    df["released_at"] = pd.to_datetime(df["released_at"])
    df["year"] = df["released_at"].dt.year
    df["text_length"] = df["oracle_text"].str.len().fillna(0).astype(int)
    df["is_creature"] = df["type_line"].str.contains("Creature", na=False)

    print(f"DataFrame built: {len(df):,} cards, {df['year'].min()}–{df['year'].max()}")
    return df


# --- Chart helpers ---

def apply_blog_style(ax, title=None, xlabel=None, ylabel=None):
    """Apply consistent styling matching the blog's aesthetic."""
    ax.set_facecolor("white")
    ax.figure.set_facecolor("white")

    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=10)
    ax.xaxis.label.set_color(TEXT_SECONDARY)
    ax.yaxis.label.set_color(TEXT_SECONDARY)

    if title:
        ax.set_title(title, color=TEXT, fontsize=13, fontweight="bold", pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, labelpad=8)
    if ylabel:
        ax.set_ylabel(ylabel, labelpad=8)

    ax.grid(axis="y", color=BORDER, linewidth=0.8, linestyle="-")
    ax.set_axisbelow(True)


def save(fig, filename: str):
    path = OUTPUT_DIR / filename
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"Saved: {path}")
    plt.close(fig)


# --- Analyses ---

def chart_cards_per_year(df: pd.DataFrame):
    """
    Line chart: unique cards first printed per year.
    Shows the dramatic acceleration in the modern era.
    """
    by_year = (
        df.groupby("year")
        .size()
        .reset_index(name="cards")
        .sort_values("year")
    )
    # Drop current partial year
    current_year = pd.Timestamp.now().year
    by_year = by_year[by_year["year"] < current_year]

    fig, ax = plt.subplots(figsize=(9, 4.5))

    ax.fill_between(by_year["year"], by_year["cards"], alpha=0.25, color=ACCENT)
    ax.plot(by_year["year"], by_year["cards"], color=ACCENT_DARK, linewidth=2)

    # Annotate the inflection — post-2017 acceleration
    inflection_year = 2017
    inflection_y = by_year.loc[by_year["year"] == inflection_year, "cards"].values
    if len(inflection_y):
        ax.axvline(x=inflection_year, color=TEXT_SECONDARY, linewidth=1, linestyle="--", alpha=0.6)
        ax.text(
            inflection_year + 0.3,
            inflection_y[0] + 30,
            "Modern era begins",
            color=TEXT_SECONDARY,
            fontsize=9,
        )

    apply_blog_style(
        ax,
        title="New Magic cards printed per year",
        xlabel="Year",
        ylabel="Unique cards",
    )
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_xlim(by_year["year"].min() - 0.5, by_year["year"].max() + 0.5)

    fig.tight_layout()
    save(fig, "cards_per_year.png")
    return by_year


def chart_set_size_distribution(df: pd.DataFrame):
    """
    Histogram: distribution of set sizes with mean and median annotated.
    Illustrates right-skewed distribution and mean vs. median divergence.
    """
    set_sizes = df.groupby("set_name").size().reset_index(name="cards")

    mean_size = set_sizes["cards"].mean()
    median_size = set_sizes["cards"].median()

    fig, ax = plt.subplots(figsize=(9, 4.5))

    ax.hist(set_sizes["cards"], bins=40, color=ACCENT, edgecolor="white", linewidth=0.5)

    ax.axvline(mean_size, color="#e07070", linewidth=1.5, linestyle="--", label=f"Mean: {mean_size:.0f}")
    ax.axvline(median_size, color=ACCENT_DARK, linewidth=1.5, linestyle="--", label=f"Median: {median_size:.0f}")

    ax.legend(fontsize=10, frameon=False)

    apply_blog_style(
        ax,
        title="How many cards does a Magic set contain?",
        xlabel="Cards in set",
        ylabel="Number of sets",
    )

    fig.tight_layout()
    save(fig, "set_size_distribution.png")

    print(f"\nSet size stats:")
    print(f"  Sets: {len(set_sizes):,}")
    print(f"  Mean: {mean_size:.1f} cards")
    print(f"  Median: {median_size:.1f} cards")
    print(f"  Min: {set_sizes['cards'].min()}")
    print(f"  Max: {set_sizes['cards'].max()} ({set_sizes.loc[set_sizes['cards'].idxmax(), 'set_name']})")

    return set_sizes


def chart_complexity_creep(df: pd.DataFrame):
    """
    Line chart: median oracle text length by year.
    Shows complexity growth over time.
    Uses median (not mean) to avoid outliers from rules-heavy Sagas, MDFCs, etc.
    """
    by_year = (
        df[df["text_length"] > 0]  # exclude lands and cards with no text
        .groupby("year")["text_length"]
        .median()
        .reset_index()
        .rename(columns={"text_length": "median_text_length"})
        .sort_values("year")
    )
    current_year = pd.Timestamp.now().year
    by_year = by_year[by_year["year"] < current_year]

    fig, ax = plt.subplots(figsize=(9, 4.5))

    ax.fill_between(by_year["year"], by_year["median_text_length"], alpha=0.25, color=ACCENT)
    ax.plot(by_year["year"], by_year["median_text_length"], color=ACCENT_DARK, linewidth=2)

    apply_blog_style(
        ax,
        title="Card text length over time (median characters, excluding lands)",
        xlabel="Year",
        ylabel="Median characters",
    )
    ax.set_xlim(by_year["year"].min() - 0.5, by_year["year"].max() + 0.5)

    fig.tight_layout()
    save(fig, "complexity_creep.png")
    return by_year


def print_summary(df: pd.DataFrame, by_year: pd.DataFrame):
    print("\n--- Summary numbers for the post ---")
    print(f"Total unique cards: {len(df):,}")
    print(f"Unique sets: {df['set'].nunique():,}")
    print(f"Date range: {df['year'].min()} – {df['year'].max()}")
    print(f"Peak year by new cards: {by_year.loc[by_year['cards'].idxmax(), 'year']} "
          f"({by_year['cards'].max():,} cards)")


# --- Main ---

def main():
    cards = fetch_oracle_cards()
    df = build_dataframe(cards)

    by_year = chart_cards_per_year(df)
    chart_set_size_distribution(df)
    chart_complexity_creep(df)
    print_summary(df, by_year)


if __name__ == "__main__":
    main()
