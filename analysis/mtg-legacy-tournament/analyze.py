"""
analyze.py — MTG Legacy Tournament Gap Analysis

Reads card_metrics.json and mtg-card-power-rankings.csv and outputs:
  data/gap_analysis.csv          — per-card gap scores under all weighting schemes
  public/images/mtg-legacy-tournament/*.png — 4 charts

Run:  uv run analyze.py
"""

import json
import re
import time
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import requests
from scipy.stats import percentileofscore

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR    = Path(__file__).parent / "data"
METRICS_PATH = DATA_DIR / "card_metrics.json"
POWER_CSV   = Path(__file__).parent.parent.parent / "public" / "data" / "mtg-card-power-rankings.csv"
GAP_CSV     = DATA_DIR / "gap_analysis.csv"
IMAGES_DIR  = Path(__file__).parent.parent.parent / "public" / "images" / "mtg-legacy-tournament"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

SCRYFALL_CACHE = DATA_DIR / "scryfall_unscored.json"

SCHEMES = ["flat", "placement", "prestige", "combined"]

# ---------------------------------------------------------------------------
# Style (match blog aesthetic from prior posts)
# ---------------------------------------------------------------------------

plt.rcParams.update({
    "figure.facecolor":  "#f8f7f4",
    "axes.facecolor":    "#f8f7f4",
    "axes.edgecolor":    "#ccc8c0",
    "axes.labelcolor":   "#444",
    "text.color":        "#1a1a1a",
    "xtick.color":       "#666",
    "ytick.color":       "#666",
    "grid.color":        "#e2ddd6",
    "grid.linestyle":    "--",
    "grid.alpha":        0.8,
    "font.family":       "monospace",
    "axes.titlesize":    13,
    "axes.labelsize":    11,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "legend.fontsize":   9,
    "legend.framealpha": 0.6,
    "legend.facecolor":  "#f8f7f4",
    "legend.edgecolor":  "#ccc8c0",
})

ACCENT   = "#3b82c4"
ACCENT2  = "#c45c3b"
NEUTRAL  = "#555"
GRID_COL = "#e2ddd6"


# ---------------------------------------------------------------------------
# Scryfall lookup for unscored card classification
# ---------------------------------------------------------------------------

def fetch_scryfall_card_data(card_names: list[str]) -> dict[str, dict]:
    """
    Batch-fetch Scryfall data for a list of card names using the /cards/collection
    endpoint (up to 75 names per request).

    Returns {card_name: {"type_line": str, "mana_cost": str}} for matched cards.
    Results are cached to SCRYFALL_CACHE — delete the file to re-fetch.
    """
    if SCRYFALL_CACHE.exists():
        cached = json.loads(SCRYFALL_CACHE.read_text())
        # Only re-fetch names not already in cache
        missing = [n for n in card_names if n not in cached]
        if not missing:
            return cached
        card_names = missing
        result = cached
    else:
        result = {}

    print(f"  Scryfall: fetching data for {len(card_names)} unscored cards...")
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; research-scraper/1.0)"})

    batch_size = 75
    for i in range(0, len(card_names), batch_size):
        batch = card_names[i : i + batch_size]
        identifiers = [{"name": n} for n in batch]
        time.sleep(0.1)  # Scryfall asks for ≥50-100ms between requests
        r = session.post(
            "https://api.scryfall.com/cards/collection",
            json={"identifiers": identifiers},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        for card in data.get("data", []):
            name = card.get("name", "")
            result[name] = {
                "type_line":  card.get("type_line", ""),
                "mana_cost":  card.get("mana_cost", ""),
                "oracle_text": card.get("oracle_text", ""),
            }

    SCRYFALL_CACHE.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"  Scryfall: cached {len(result)} cards → {SCRYFALL_CACHE}")
    return result


def classify_unscored_reason(card_name: str, scryfall_data: dict) -> str:
    """
    Classify why a card was excluded from the Post 2 power rankings.

    Post 2 exclusion rules (from analyze.py export_rankings):
      - Lands (is_land)
      - CMC = 0 non-lands
      - X-cost cards (has_x: mana_cost contains {X})
      - No confirmed abilities: categories == ["other"] AND keyword_count == 0

    Returns one of: "land", "x_cost", "no_abilities", "unknown"
    """
    info = scryfall_data.get(card_name, {})
    type_line  = info.get("type_line", "")
    mana_cost  = info.get("mana_cost", "")

    if "Land" in type_line:
        return "land"
    if "{X}" in mana_cost or "{x}" in mana_cost.lower():
        return "x_cost"
    if mana_cost in ("{0}", "") and "Land" not in type_line:
        return "x_cost"  # CMC=0 non-land (e.g. Chrome Mox {0})
    # Remaining unscored cards have text the Post 2 parser couldn't classify
    return "no_abilities"


# ---------------------------------------------------------------------------
# Step 1: Name normalization
# ---------------------------------------------------------------------------

def normalize_name(name: str) -> str:
    """Lowercase, strip whitespace, drop punctuation, resolve known DFC aliases."""
    # DFCs: keep only the front face
    name = name.split(" // ")[0]
    name = name.lower().strip()
    # strip non-alphanumeric except spaces
    name = re.sub(r"[^a-z0-9 ]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


# ---------------------------------------------------------------------------
# Step 2: Build joined DataFrame
# ---------------------------------------------------------------------------

def build_gap_df() -> pd.DataFrame:
    metrics = json.loads(METRICS_PATH.read_text())
    power   = pd.read_csv(POWER_CSV)

    # Power scores: rank 1 = highest score. Invert to a 0-based score so higher = better.
    # Use (max_rank + 1 - rank) so rank-1 card gets the highest score.
    max_rank = power["rank"].max()
    power["power_score"] = max_rank + 1 - power["rank"]
    power["name_norm"]   = power["name"].apply(normalize_name)

    # Deduplicate on normalized name: keep highest-ranked entry (lowest rank number).
    # Duplicates arise from un-set reprints and punctuation variants (e.g. "Gather, the
    # Townsfolk" vs "Gather the Townsfolk"). For Legacy cards none of these are relevant,
    # but the dedup is needed to avoid a ValueError on .to_dict("index").
    power = power.sort_values("rank").drop_duplicates(subset="name_norm", keep="first")

    power_lookup = power.set_index("name_norm")[["power_score", "rank", "name", "cmc", "card_type", "color"]].to_dict("index")

    rows = []
    for card_name, zones in metrics.items():
        mb = zones.get("mainboard", {})
        if not mb:
            continue

        name_norm = normalize_name(card_name)
        power_info = power_lookup.get(name_norm)

        row = {
            "card_name":   card_name,
            "name_norm":   name_norm,
            "deck_count":  mb.get("deck_count", 0),
            "total_copies": mb.get("total_copies", 0),
            "unscored":    power_info is None,
        }

        for s in SCHEMES:
            row[f"prevalence_{s}"] = mb.get(f"prevalence_{s}", 0.0)

        if power_info:
            row["power_score"] = power_info["power_score"]
            row["power_rank"]  = power_info["rank"]
            row["cmc"]         = power_info["cmc"]
            row["card_type"]   = power_info["card_type"]
            row["color"]       = power_info["color"]
        else:
            row["power_score"] = np.nan
            row["power_rank"]  = np.nan
            row["cmc"]         = np.nan
            row["card_type"]   = "Unknown"
            row["color"]       = "Unknown"

        rows.append(row)

    df = pd.DataFrame(rows)

    # Classify unscored cards via Scryfall
    unscored_names = df.loc[df["unscored"], "card_name"].tolist()
    scryfall_data = fetch_scryfall_card_data(unscored_names)
    df["unscored_reason"] = df.apply(
        lambda r: "scored" if not r["unscored"]
                  else classify_unscored_reason(r["card_name"], scryfall_data),
        axis=1,
    )

    reason_counts = df["unscored_reason"].value_counts().to_dict()
    print(f"  Joined: {reason_counts.get('scored', 0)} scored, "
          f"{reason_counts.get('land', 0)} lands, "
          f"{reason_counts.get('x_cost', 0)} x-cost, "
          f"{reason_counts.get('no_abilities', 0)} no-abilities, "
          f"{reason_counts.get('unknown', 0)} unknown")

    # Percentile ranks (0–100) for both dimensions, computed on scored cards only
    scored = df[~df["unscored"]].copy()
    all_power_scores = scored["power_score"].values

    for s in SCHEMES:
        all_prev = df[f"prevalence_{s}"].values
        df[f"pctrank_prevalence_{s}"] = df[f"prevalence_{s}"].apply(
            lambda v: percentileofscore(all_prev, v, kind="rank")
        )

    df["pctrank_power"] = df["power_score"].apply(
        lambda v: percentileofscore(all_power_scores, v, kind="rank") if not np.isnan(v) else np.nan
    )

    for s in SCHEMES:
        df[f"gap_{s}"] = df[f"pctrank_prevalence_{s}"] - df["pctrank_power"]

    return df


# ---------------------------------------------------------------------------
# Chart 1: Scatter — power score percentile vs. prevalence percentile
# ---------------------------------------------------------------------------

def chart_scatter(df: pd.DataFrame) -> None:
    scored = df[~df["unscored"]].copy()
    scheme = "flat"

    fig, ax = plt.subplots(figsize=(10, 8))

    x = scored["pctrank_power"]
    y = scored[f"pctrank_prevalence_{scheme}"]

    ax.scatter(x, y, s=18, alpha=0.4, color=ACCENT, linewidths=0)

    # Quadrant lines
    ax.axvline(50, color=NEUTRAL, linewidth=0.6, alpha=0.4)
    ax.axhline(50, color=NEUTRAL, linewidth=0.6, alpha=0.4)

    # Quadrant labels
    ax.text(5,  95, "High community value\nlower text score",  fontsize=8, alpha=0.6, va="top")
    ax.text(72, 10, "High text score\nlower community value", fontsize=8, alpha=0.6, va="bottom")

    # Label top outliers in each quadrant
    # Q2: high prevalence (y>70), low power (x<40) — community values more than metric
    q2 = scored[(y > 70) & (x < 40)].copy()
    q2["dist"] = (70 - q2["pctrank_power"]) + (q2[f"pctrank_prevalence_{scheme}"] - 70)
    for _, row in q2.nlargest(12, "dist").iterrows():
        ax.annotate(row["card_name"], (row["pctrank_power"], row[f"pctrank_prevalence_{scheme}"]),
                    fontsize=7, alpha=0.85, xytext=(4, 2), textcoords="offset points")

    # Q4: high power (x>70), low prevalence (y<40) — metric scores higher than community plays
    q4 = scored[(x > 70) & (y < 40)].copy()
    q4["dist"] = (q4["pctrank_power"] - 70) + (40 - q4[f"pctrank_prevalence_{scheme}"])
    for _, row in q4.nlargest(12, "dist").iterrows():
        ax.annotate(row["card_name"], (row["pctrank_power"], row[f"pctrank_prevalence_{scheme}"]),
                    fontsize=7, alpha=0.85, xytext=(4, 2), textcoords="offset points")

    ax.set_xlabel("Power Score Percentile (text-derived)")
    ax.set_ylabel("Mainboard Prevalence Percentile (tournament, flat)")
    ax.set_title("MTG Legacy: Text-Derived Power Score vs. Tournament Prevalence\n2022–2025, Scored Cards Only")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.grid(True)

    plt.tight_layout()
    out = IMAGES_DIR / "scatter_power_vs_prevalence.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="#f8f7f4")
    plt.close()
    print(f"  Saved → {out}")


# ---------------------------------------------------------------------------
# Chart 2: Divergence leaderboard (two-panel bar chart)
# ---------------------------------------------------------------------------

def chart_divergence(df: pd.DataFrame) -> None:
    scored = df[~df["unscored"]].copy()
    scheme = "flat"
    gap_col = f"gap_{scheme}"
    n = 15

    # Community > metric (positive gap): high prevalence, lower power score
    over = scored.nlargest(n, gap_col)[["card_name", gap_col]].reset_index(drop=True)
    # Metric > community (negative gap): high power score, lower prevalence
    under = scored.nsmallest(n, gap_col)[["card_name", gap_col]].reset_index(drop=True)
    under = under.iloc[::-1].reset_index(drop=True)  # reverse so most extreme is at bottom

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

    # Panel 1: community prevalence > text score
    bars1 = ax1.barh(over["card_name"], over[gap_col], color=ACCENT, alpha=0.85)
    ax1.set_title("Community values more than\ntext score predicts", fontsize=11)
    ax1.set_xlabel("Prevalence percentile − Power score percentile")
    ax1.axvline(0, color=NEUTRAL, linewidth=0.8)
    ax1.grid(True, axis="x")
    ax1.invert_yaxis()

    # Panel 2: text score > community prevalence
    bars2 = ax2.barh(under["card_name"], under[gap_col].abs(), color=ACCENT2, alpha=0.85)
    ax2.set_title("Text score predicts more\nthan community plays", fontsize=11)
    ax2.set_xlabel("Power score percentile − Prevalence percentile")
    ax2.axvline(0, color=NEUTRAL, linewidth=0.8)
    ax2.grid(True, axis="x")
    ax2.invert_yaxis()

    fig.suptitle("MTG Legacy: Where Text Score and Tournament Prevalence Diverge Most\n2022–2025, Flat Weighting", y=1.01)
    plt.tight_layout()
    out = IMAGES_DIR / "divergence_leaderboard.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="#f8f7f4")
    plt.close()
    print(f"  Saved → {out}")


# ---------------------------------------------------------------------------
# Chart 3: Weighting sensitivity — top 20 by combined, rank under all 4 schemes
# ---------------------------------------------------------------------------

def chart_weighting_sensitivity(df: pd.DataFrame) -> None:
    scored = df[~df["unscored"]].copy()

    # Top 20 cards by combined prevalence percentile
    top20 = scored.nlargest(20, "pctrank_prevalence_combined")[["card_name"] + [f"pctrank_prevalence_{s}" for s in SCHEMES]].reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(12, 7))

    n = len(top20)
    x = np.arange(n)
    width = 0.2
    colors = [ACCENT, "#e0d07e", "#7ee0a0", ACCENT2]

    for i, (s, color) in enumerate(zip(SCHEMES, colors)):
        ax.bar(x + i * width, top20[f"pctrank_prevalence_{s}"], width, label=s, color=color, alpha=0.85)

    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(top20["card_name"], rotation=40, ha="right", fontsize=8)
    ax.set_ylabel("Prevalence Percentile")
    ax.set_title("Top 20 Cards by Combined Prevalence: Rank Stability Across Weighting Schemes\nMTG Legacy 2022–2025")
    ax.legend(title="Scheme")
    ax.grid(True, axis="y")
    ax.set_ylim(80, 105)

    plt.tight_layout()
    out = IMAGES_DIR / "weighting_sensitivity.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="#f8f7f4")
    plt.close()
    print(f"  Saved → {out}")


# ---------------------------------------------------------------------------
# Chart 4: Mainboard vs. sideboard prevalence
# ---------------------------------------------------------------------------

def chart_mb_vs_sb(df: pd.DataFrame, metrics: dict) -> None:
    # Build sideboard prevalence series
    sb_prev = {}
    for card_name, zones in metrics.items():
        sb = zones.get("sideboard", {})
        if sb:
            sb_prev[card_name] = sb.get("prevalence_flat", 0.0)

    mb_df = df[["card_name", "prevalence_flat"]].copy()
    mb_df["prevalence_sb"] = mb_df["card_name"].map(sb_prev).fillna(0.0)

    fig, ax = plt.subplots(figsize=(9, 8))

    ax.scatter(mb_df["prevalence_flat"], mb_df["prevalence_sb"],
               s=14, alpha=0.35, color=ACCENT, linewidths=0)

    # Label primarily sideboard-only cards (high SB, low MB)
    threshold_sb   = mb_df["prevalence_sb"].quantile(0.90)
    threshold_mb   = mb_df["prevalence_flat"].quantile(0.70)
    sb_only = mb_df[(mb_df["prevalence_sb"] > threshold_sb) & (mb_df["prevalence_flat"] < threshold_mb)]
    for _, row in sb_only.iterrows():
        ax.annotate(row["card_name"], (row["prevalence_flat"], row["prevalence_sb"]),
                    fontsize=7, alpha=0.85, xytext=(3, 2), textcoords="offset points")

    # Label primarily mainboard-dominant cards (high MB, near-zero SB)
    mb_dominant = mb_df[(mb_df["prevalence_flat"] > mb_df["prevalence_flat"].quantile(0.92)) &
                        (mb_df["prevalence_sb"] < mb_df["prevalence_sb"].quantile(0.10))]
    for _, row in mb_dominant.iterrows():
        ax.annotate(row["card_name"], (row["prevalence_flat"], row["prevalence_sb"]),
                    fontsize=7, alpha=0.85, xytext=(3, 2), textcoords="offset points")

    ax.set_xlabel("Mainboard Prevalence (avg copies / total decks, flat)")
    ax.set_ylabel("Sideboard Prevalence (avg copies / total decks, flat)")
    ax.set_title("MTG Legacy: Mainboard vs. Sideboard Prevalence\n2022–2025")
    ax.grid(True)

    plt.tight_layout()
    out = IMAGES_DIR / "mb_vs_sb.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="#f8f7f4")
    plt.close()
    print(f"  Saved → {out}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print("\n[1/3] Building gap analysis DataFrame")
    df = build_gap_df()

    print("\n[2/3] Writing gap_analysis.csv")
    cols = (
        ["card_name", "card_type", "color", "cmc", "power_rank", "power_score",
         "pctrank_power", "deck_count", "total_copies", "unscored", "unscored_reason"]
        + [f"prevalence_{s}" for s in SCHEMES]
        + [f"pctrank_prevalence_{s}" for s in SCHEMES]
        + [f"gap_{s}" for s in SCHEMES]
    )
    df[cols].sort_values("gap_flat", ascending=False).to_csv(GAP_CSV, index=False)
    print(f"  Saved → {GAP_CSV}")

    print("\n[3/3] Generating charts")
    metrics = json.loads(METRICS_PATH.read_text())
    chart_scatter(df)
    chart_divergence(df)
    chart_weighting_sensitivity(df)
    chart_mb_vs_sb(df, metrics)

    print("\nDone.")
    print(f"\nTop 10 by gap_flat (community > metric):")
    top = df[~df["unscored"]].nlargest(10, "gap_flat")[["card_name", "pctrank_prevalence_flat", "pctrank_power", "gap_flat"]]
    print(top.to_string(index=False))

    print(f"\nTop 10 by gap_flat (metric > community):")
    bot = df[~df["unscored"]].nsmallest(10, "gap_flat")[["card_name", "pctrank_prevalence_flat", "pctrank_power", "gap_flat"]]
    print(bot.to_string(index=False))


if __name__ == "__main__":
    main()
