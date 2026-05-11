"""
MTG card distribution analysis for gatheringdata.blog post:
"Thirty Years of Magic Cards, Measured"

Data sources: Scryfall bulk data API
  - oracle_cards: one entry per unique card design (properties, text, colors, types)
  - all_cards: every printing of every card (used only to compute accurate first-print year)

Why two sources?
  oracle_cards picks the "most recent" canonical printing per card, so its released_at
  reflects the latest reprint — not the first appearance. To get accurate net-new counts
  (when a design was introduced), we need to find the minimum released_at per oracle_id
  across all_cards.

Outputs: PNG charts to ../../public/images/mtg-distributions/
"""

import argparse
import json
from pathlib import Path

import ijson
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import requests

# --- Config ---

# OUTPUT_DIR is set in main() from CLI args. Default keeps backward compat for local runs.
_DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent.parent / "public" / "images" / "mtg-distributions"
OUTPUT_DIR: Path  # set in main()

CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

# Blog accent color from global.css
ACCENT = "#b2d4e5"
ACCENT_DARK = "#7aafc9"
TEXT = "#363737"
TEXT_SECONDARY = "#868787"
BORDER = "#dddddd"

EXCLUDED_LAYOUTS = {"token", "emblem", "art_series", "reversible_card"}

CURRENT_YEAR = pd.Timestamp.now().year

COLOR_PALETTE = {
    "White": "#f5e6c8",
    "Blue": "#a8c8e8",
    "Black": "#9a8fa0",
    "Red": "#e8a090",
    "Green": "#90c890",
    "Multicolor": "#e8d080",
    "Colorless": "#c0c0c0",
}

TYPE_ORDER = ["Creature", "Instant", "Sorcery", "Enchantment", "Artifact", "Land", "Planeswalker", "Other"]
TYPE_PALETTE = {
    "Creature": "#90c890",
    "Instant": "#a8c8e8",
    "Sorcery": "#e8a090",
    "Enchantment": "#c8a8e8",
    "Artifact": "#c0c0c0",
    "Land": "#d4b896",
    "Planeswalker": "#e8d080",
    "Other": "#d0d0d0",
}


# --- Bulk data fetching with caching ---

def _get_bulk_index() -> list[dict]:
    resp = requests.get(
        "https://api.scryfall.com/bulk-data",
        headers={"User-Agent": "gatheringdata-blog-analysis/1.0"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"]


def _download_to_file(url: str, dest: Path):
    resp = requests.get(
        url,
        headers={"User-Agent": "gatheringdata-blog-analysis/1.0"},
        timeout=300,
        stream=True,
    )
    resp.raise_for_status()
    total = 0
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
            total += len(chunk)
            print(f"\r  Downloaded {total / 1024 / 1024:.0f} MB...", end="", flush=True)
    print()


def fetch_bulk_file(bulk_type: str) -> Path:
    """
    Return path to a locally-cached Scryfall bulk data file.
    Downloads only when the cached version is outdated.
    """
    print(f"Checking Scryfall index for {bulk_type}...")
    index = _get_bulk_index()
    entry = next(f for f in index if f["type"] == bulk_type)

    # Use updated_at as the cache key
    cache_key = entry["updated_at"][:19].replace(":", "-")
    cache_file = CACHE_DIR / f"{bulk_type}--{cache_key}.json"

    if cache_file.exists():
        print(f"  Cache hit: {cache_file.name}")
        return cache_file

    # Remove stale cache for this type
    for stale in CACHE_DIR.glob(f"{bulk_type}--*.json"):
        print(f"  Removing stale cache: {stale.name}")
        stale.unlink()

    print(f"  Downloading {bulk_type} from {entry['download_uri']}...")
    _download_to_file(entry["download_uri"], cache_file)
    print(f"  Cached to {cache_file.name}")
    return cache_file


# --- First-print year computation (from all_cards) ---

def compute_first_print_years(all_cards_path: Path) -> dict[str, int]:
    """
    Stream-parse all_cards and return {oracle_id: first_print_year}.

    all_cards contains every printing of every card in every set. We find the
    minimum released_at per oracle_id to determine when each design first appeared.

    Uses ijson for streaming so we don't load the full file (~500MB+) into memory.
    """
    # Cache the mapping separately — it's tiny (~2MB) even though all_cards is huge
    mapping_cache = CACHE_DIR / f"first_print_years--{all_cards_path.stem}.json"
    if mapping_cache.exists():
        print(f"  First-print year mapping: cache hit")
        with open(mapping_cache) as f:
            return json.load(f)

    print(f"  Computing first-print years from {all_cards_path.name} (streaming)...")
    first_prints: dict[str, str] = {}

    with open(all_cards_path, "rb") as f:
        for card in ijson.items(f, "item"):
            oid = card.get("oracle_id")
            released = card.get("released_at")
            if not oid or not released:
                continue
            if oid not in first_prints or released < first_prints[oid]:
                first_prints[oid] = released

    result = {oid: int(date[:4]) for oid, date in first_prints.items()}

    with open(mapping_cache, "w") as f:
        json.dump(result, f)
    print(f"  Saved mapping for {len(result):,} cards")
    return result


# --- Data prep ---

def get_main_type(type_line: str) -> str:
    """Extract the primary card type (first match in priority order)."""
    for t in TYPE_ORDER[:-1]:  # skip "Other"
        if t in type_line:
            return t
    return "Other"


def get_color_category(colors: list) -> str:
    """Classify a card as Multicolor, or one of the five colors, or Colorless."""
    if len(colors) >= 2:
        return "Multicolor"
    if len(colors) == 1:
        mapping = {"W": "White", "U": "Blue", "B": "Black", "R": "Red", "G": "Green"}
        return mapping.get(colors[0], "Colorless")
    return "Colorless"


def build_dataframe(oracle_cards: list[dict], first_print_years: dict[str, int]) -> pd.DataFrame:
    """
    Merge oracle_cards properties with accurate first-print years from all_cards.
    """
    rows = []
    for card in oracle_cards:
        if card.get("layout") in EXCLUDED_LAYOUTS:
            continue

        oracle_id = card.get("oracle_id", "")
        colors = card.get("colors", [])
        type_line = card.get("type_line", "")

        # Accurate first-print year from all_cards; fall back to oracle_cards date
        first_year = first_print_years.get(oracle_id)
        if not first_year:
            released = card.get("released_at", "")
            first_year = int(released[:4]) if released else None

        rows.append({
            "name": card.get("name"),
            "oracle_id": oracle_id,
            "oracle_released_at": card.get("released_at"),  # canonical (latest) printing date
            "first_print_year": first_year,
            "set": card.get("set"),
            "set_name": card.get("set_name"),
            "rarity": card.get("rarity"),
            "colors": colors,
            "type_line": type_line,
            "oracle_text": card.get("oracle_text", ""),
            "mana_value": card.get("mana_value") or card.get("cmc"),
            "color_category": get_color_category(colors),
            "main_type": get_main_type(type_line),
            "is_legendary": "Legendary" in (type_line.split("—")[0] if "—" in type_line else type_line),
        })

    df = pd.DataFrame(rows)
    df["oracle_released_year"] = pd.to_datetime(df["oracle_released_at"]).dt.year
    df["text_length"] = df["oracle_text"].str.len().fillna(0).astype(int)

    print(f"DataFrame: {len(df):,} cards, first prints {df['first_print_year'].min()}–{df['first_print_year'].max()}")
    return df


# --- Chart helpers ---

def apply_blog_style(ax, title=None, xlabel=None, ylabel=None):
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

def chart_net_new_vs_all_per_year(df: pd.DataFrame):
    """
    Two-line chart comparing:
    - Net-new: unique card designs introduced for the first time each year (first_print_year)
    - All: oracle_cards canonical year (Scryfall's most-recent-printing selection)

    The gap between the lines represents reprints being credited to the wrong year
    in a naive oracle_cards analysis.
    """
    net_new = (
        df[df["first_print_year"] < CURRENT_YEAR]
        .groupby("first_print_year").size()
        .reset_index(name="net_new")
        .rename(columns={"first_print_year": "year"})
    )
    canonical = (
        df[df["oracle_released_year"] < CURRENT_YEAR]
        .groupby("oracle_released_year").size()
        .reset_index(name="canonical")
        .rename(columns={"oracle_released_year": "year"})
    )
    combined = pd.merge(net_new, canonical, on="year", how="outer").sort_values("year")

    fig, ax = plt.subplots(figsize=(9, 4.5))

    ax.fill_between(combined["year"], combined["net_new"], alpha=0.2, color=ACCENT)
    ax.plot(combined["year"], combined["net_new"], color=ACCENT_DARK, linewidth=2, label="Net-new designs")
    ax.plot(combined["year"], combined["canonical"], color="#e07070", linewidth=1.5,
            linestyle="--", alpha=0.8, label="Oracle canonical (naive)")

    ax.legend(fontsize=10, frameon=False)
    apply_blog_style(
        ax,
        title="New card designs per year: net-new vs. canonical",
        xlabel="Year",
        ylabel="Unique cards",
    )
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_xlim(1992.5, combined["year"].max() + 0.5)

    fig.tight_layout()
    save(fig, "net_new_vs_canonical.png")

    print("\nNet-new vs canonical (last 10 years):")
    print(combined[combined["year"] >= CURRENT_YEAR - 10].to_string(index=False))
    return combined


def chart_cards_per_year(df: pd.DataFrame):
    """Net-new card designs per year (using accurate first_print_year)."""
    by_year = (
        df[df["first_print_year"] < CURRENT_YEAR]
        .groupby("first_print_year").size()
        .reset_index(name="cards")
        .rename(columns={"first_print_year": "year"})
        .sort_values("year")
    )

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.fill_between(by_year["year"], by_year["cards"], alpha=0.25, color=ACCENT)
    ax.plot(by_year["year"], by_year["cards"], color=ACCENT_DARK, linewidth=2)

    ax.axvline(x=2017, color=TEXT_SECONDARY, linewidth=1, linestyle="--", alpha=0.6)
    inflection_y = by_year.loc[by_year["year"] == 2017, "cards"].values
    if len(inflection_y):
        ax.text(2017.3, inflection_y[0] + 40, "Commander becomes\nyear-round product",
                color=TEXT_SECONDARY, fontsize=8.5)

    apply_blog_style(ax, title="Net-new Magic card designs per year", xlabel="Year", ylabel="Unique cards")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_xlim(1992.5, by_year["year"].max() + 0.5)

    fig.tight_layout()
    save(fig, "cards_per_year.png")

    peak = by_year.loc[by_year["cards"].idxmax()]
    print(f"\nPeak year (net-new): {int(peak['year'])} — {int(peak['cards']):,} designs")
    return by_year


def chart_set_size_distribution(df: pd.DataFrame):
    """Histogram of set sizes with mean and median annotated."""
    set_sizes = df.groupby("set_name").size().reset_index(name="cards")
    mean_size = set_sizes["cards"].mean()
    median_size = set_sizes["cards"].median()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.hist(set_sizes["cards"], bins=40, color=ACCENT, edgecolor="white", linewidth=0.5)
    ax.axvline(mean_size, color="#e07070", linewidth=1.5, linestyle="--", label=f"Mean: {mean_size:.0f}")
    ax.axvline(median_size, color=ACCENT_DARK, linewidth=1.5, linestyle="--", label=f"Median: {median_size:.0f}")
    ax.legend(fontsize=10, frameon=False)

    apply_blog_style(ax, title="How many cards does a Magic set contain?",
                     xlabel="Cards in set", ylabel="Number of sets")
    fig.tight_layout()
    save(fig, "set_size_distribution.png")

    print(f"\nSet size: mean {mean_size:.1f}, median {median_size:.1f}, "
          f"max {set_sizes['cards'].max()} ({set_sizes.loc[set_sizes['cards'].idxmax(), 'set_name']})")


def chart_color_complexity_over_time(df: pd.DataFrame):
    """
    Stacked area: % of new card designs that are multicolor, monocolored, or colorless each year.
    Shows the multicolor era and Commander-driven gold card explosion.
    """
    by_year = (
        df[df["first_print_year"] < CURRENT_YEAR]
        .groupby(["first_print_year", "color_category"])
        .size()
        .reset_index(name="count")
        .rename(columns={"first_print_year": "year"})
    )
    pivot = by_year.pivot(index="year", columns="color_category", values="count").fillna(0)

    # Reorder columns
    col_order = ["Multicolor", "White", "Blue", "Black", "Red", "Green", "Colorless"]
    pivot = pivot.reindex(columns=[c for c in col_order if c in pivot.columns], fill_value=0)

    # Convert to percentages
    pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(9, 4.5))
    colors_plot = [COLOR_PALETTE[c] for c in pct.columns]
    ax.stackplot(pct.index, [pct[c] for c in pct.columns],
                 labels=pct.columns, colors=colors_plot, alpha=0.85)

    ax.legend(loc="upper left", fontsize=9, frameon=False, ncol=2)
    apply_blog_style(ax, title="Color complexity of new card designs over time",
                     xlabel="Year", ylabel="% of new designs")
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x)}%"))
    ax.set_xlim(1992.5, pct.index.max() + 0.5)

    fig.tight_layout()
    save(fig, "color_complexity_over_time.png")


def chart_type_breakdown_over_time(df: pd.DataFrame):
    """
    Stacked area: composition of new card designs by card type each year.
    Shows creature dominance growing over time.
    """
    by_year = (
        df[df["first_print_year"] < CURRENT_YEAR]
        .groupby(["first_print_year", "main_type"])
        .size()
        .reset_index(name="count")
        .rename(columns={"first_print_year": "year"})
    )
    pivot = by_year.pivot(index="year", columns="main_type", values="count").fillna(0)
    pivot = pivot.reindex(columns=[t for t in TYPE_ORDER if t in pivot.columns], fill_value=0)

    # Percentage
    pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(9, 4.5))
    colors_plot = [TYPE_PALETTE[t] for t in pct.columns]
    ax.stackplot(pct.index, [pct[t] for t in pct.columns],
                 labels=pct.columns, colors=colors_plot, alpha=0.85)

    ax.legend(loc="upper right", fontsize=9, frameon=False, ncol=2)
    apply_blog_style(ax, title="Card type composition of new designs over time",
                     xlabel="Year", ylabel="% of new designs")
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x)}%"))
    ax.set_xlim(1992.5, pct.index.max() + 0.5)

    fig.tight_layout()
    save(fig, "type_breakdown_over_time.png")

    # Print creature % for a few key years
    print("\nCreature % of new designs by era:")
    for year in [1993, 2000, 2010, 2020, 2024]:
        if year in pct.index and "Creature" in pct.columns:
            print(f"  {year}: {pct.loc[year, 'Creature']:.0f}%")


def chart_legendary_over_time(df: pd.DataFrame):
    """
    Dual-axis chart: absolute count of legendary new designs per year (bars)
    and % of new designs that are legendary (line).
    Shows Commander-driven legendary explosion post-2011.
    """
    by_year = (
        df[df["first_print_year"] < CURRENT_YEAR]
        .groupby("first_print_year")
        .agg(total=("name", "count"), legendary=("is_legendary", "sum"))
        .reset_index()
        .rename(columns={"first_print_year": "year"})
    )
    by_year["pct_legendary"] = by_year["legendary"] / by_year["total"] * 100

    fig, ax1 = plt.subplots(figsize=(9, 4.5))
    ax2 = ax1.twinx()

    ax1.bar(by_year["year"], by_year["legendary"], color=ACCENT, alpha=0.6, width=0.8, label="Legendary count")
    ax2.plot(by_year["year"], by_year["pct_legendary"], color=ACCENT_DARK, linewidth=2, label="% legendary")

    # Annotate Commander's first big year
    ax2.axvline(x=2011, color=TEXT_SECONDARY, linewidth=1, linestyle="--", alpha=0.5)
    ax2.text(2011.2, by_year["pct_legendary"].max() * 0.85, "Commander\nlaunches",
             color=TEXT_SECONDARY, fontsize=8.5)

    apply_blog_style(ax1, title="Annual legendary Magic: the Gathering cards released", xlabel="Year", ylabel="Legendary cards")
    ax2.set_ylabel("% of new designs", color=TEXT_SECONDARY, fontsize=10)
    ax2.tick_params(colors=TEXT_SECONDARY, labelsize=10)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax2.set_facecolor("white")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=9, frameon=False)

    ax1.set_xlim(1992.5, by_year["year"].max() + 0.5)

    fig.tight_layout()
    save(fig, "legendary_over_time.png")

    print("\nLegendary % by era:")
    for year in [1993, 2000, 2010, 2015, 2020, 2024]:
        row = by_year[by_year["year"] == year]
        if not row.empty:
            print(f"  {year}: {row['pct_legendary'].values[0]:.0f}% ({int(row['legendary'].values[0])} cards)")


def chart_complexity_creep(df: pd.DataFrame):
    """Median oracle text length by first-print year (excluding lands)."""
    by_year = (
        df[(df["text_length"] > 0) & (df["first_print_year"] < CURRENT_YEAR)]
        .groupby("first_print_year")["text_length"]
        .median()
        .reset_index()
        .rename(columns={"text_length": "median_text_length", "first_print_year": "year"})
        .sort_values("year")
    )

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.fill_between(by_year["year"], by_year["median_text_length"], alpha=0.25, color=ACCENT)
    ax.plot(by_year["year"], by_year["median_text_length"], color=ACCENT_DARK, linewidth=2)

    apply_blog_style(ax, title="Card text length over time (median characters, excluding lands)",
                     xlabel="Year", ylabel="Median characters")
    ax.set_xlim(1992.5, by_year["year"].max() + 0.5)

    fig.tight_layout()
    save(fig, "complexity_creep.png")


def print_summary(df: pd.DataFrame):
    print("\n--- Summary numbers ---")
    print(f"Unique card designs: {len(df):,}")
    print(f"Unique sets: {df['set'].nunique():,}")
    print(f"Year range: {df['first_print_year'].min()}–{df['first_print_year'].max()}")
    recent = df[df["first_print_year"] == 2024]
    print(f"2024 net-new designs: {len(recent):,}")
    print(f"  Legendary: {recent['is_legendary'].sum():,} ({recent['is_legendary'].mean()*100:.0f}%)")
    print(f"  Multicolor: {(recent['color_category']=='Multicolor').sum():,} ({(recent['color_category']=='Multicolor').mean()*100:.0f}%)")


# --- Main ---

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate MTG distribution charts")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_DEFAULT_OUTPUT_DIR,
        help="Directory to write chart PNGs (default: public/images/mtg-distributions/)",
    )
    return parser.parse_args()


def main():
    global OUTPUT_DIR
    args = parse_args()
    OUTPUT_DIR = args.output_dir
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")

    # Fetch oracle_cards (card properties)
    oracle_path = fetch_bulk_file("oracle_cards")
    print("Loading oracle_cards...")
    with open(oracle_path) as f:
        oracle_cards = json.load(f)
    print(f"  {len(oracle_cards):,} entries")

    # Fetch all_cards (for accurate first-print years)
    all_cards_path = fetch_bulk_file("all_cards")
    first_print_years = compute_first_print_years(all_cards_path)

    # Build merged DataFrame
    df = build_dataframe(oracle_cards, first_print_years)

    # Generate charts
    chart_net_new_vs_all_per_year(df)
    chart_cards_per_year(df)
    chart_set_size_distribution(df)
    chart_color_complexity_over_time(df)
    chart_type_breakdown_over_time(df)
    chart_legendary_over_time(df)
    chart_complexity_creep(df)
    print_summary(df)


if __name__ == "__main__":
    main()
