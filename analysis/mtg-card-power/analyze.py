"""
MTG ability-to-cost ratio analysis for gatheringdata.blog post:
"What Does a Mana Cost Buy You? — Ability-to-Cost Ratio and Power Creep"

Two analysis layers:
  1. Keyword layer:  Scryfall's `keywords` array — structured, no NLP needed.
     Captures named keyword abilities: flying, trample, deathtouch, hexproof, etc.
  2. Semantic layer: Regex patterns against stripped oracle text.
     Captures oracle-text abilities that aren't named keywords:
     draw a card, create a token, counter target spell, deal damage, etc.

Cost dimensions:
  - CMC: primary cost axis (Scryfall's computed value; X treated as 0)
  - x_count: number of X symbols (XX costs 2x as much as X at parity)
  - Oracle costs: equip/activated ability mana costs, additional casting costs
  - Alternative casting costs (Force of Will pattern): parsed and flagged

Data: Scryfall bulk data, reused from Post 1 cache by default.

Usage:
    cd analysis/mtg-card-power
    uv run python analyze.py
    uv run python analyze.py --scryfall-cache-dir ../mtg-distributions/.cache
"""

import argparse
import json
import re
from pathlib import Path

import ijson
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent.parent / "public" / "images" / "mtg-card-power"
_DEFAULT_SCRYFALL_CACHE = Path(__file__).parent.parent / "mtg-distributions" / ".cache"

OUTPUT_DIR: Path       # set in main()
SCRYFALL_CACHE_DIR: Path  # set in main()

LOCAL_CACHE_DIR = Path(__file__).parent / ".cache"
LOCAL_CACHE_DIR.mkdir(exist_ok=True)

CURRENT_YEAR = pd.Timestamp.now().year
EXCLUDED_LAYOUTS = {"token", "emblem", "art_series", "reversible_card"}

# Blog accent colors (matches global.css)
ACCENT = "#b2d4e5"
ACCENT_DARK = "#7aafc9"
TEXT = "#363737"
TEXT_SECONDARY = "#868787"
BORDER = "#dddddd"


# ---------------------------------------------------------------------------
# Semantic layer: regex classification
#
# Layer 1 (keywords field) captures named keyword abilities:
#   flying, trample, deathtouch, hexproof, indestructible, ward, etc.
# Layer 2 (this section) captures oracle-text abilities that aren't keywords.
# The two layers don't overlap — we strip keyword names from oracle text
# before running regex so abilities like "Flying" in oracle text aren't
# double-counted against the keywords field.
# ---------------------------------------------------------------------------

# Each entry: (category_name, list_of_compiled_patterns)
# A card gets a category if ANY pattern matches its stripped oracle text.

_PATTERNS: list[tuple[str, list[re.Pattern]]] = [
    ("card_advantage", [
        re.compile(r"draw[s]? (?:a|\d+|X) card", re.I),
        re.compile(r"\bscry \d+\b", re.I),
        re.compile(r"\bsurveil \d+\b", re.I),
        re.compile(r"look at the top \d+", re.I),
        re.compile(r"reveal the top \d+", re.I),
        re.compile(r"you may play the top", re.I),
        re.compile(r"exile the top .{0,30} and (?:you may )?(?:play|cast) it", re.I),
    ]),
    ("removal", [
        re.compile(r"destroy target", re.I),
        re.compile(r"exile target", re.I),
        re.compile(r"return target .{0,60} to .{0,20} (?:owner.s|its owner.s) hand", re.I),
        re.compile(r"puts? .{0,40} into .{0,20} owner.s graveyard", re.I),
        re.compile(r"gets? -\d+/-\d+ until end of turn", re.I),
        re.compile(r"gets? -X/-X", re.I),
        re.compile(r"destroy all", re.I),
        re.compile(r"exile all", re.I),
    ]),
    ("direct_damage", [
        re.compile(r"deals? \d+ damage", re.I),
        re.compile(r"deals? X damage", re.I),
        re.compile(r"deals? .{0,30} damage to (?:any target|target (?:player|opponent|creature|planeswalker|battle))", re.I),
    ]),
    ("tokens", [
        re.compile(r"creates? .{0,60} token", re.I),
        re.compile(r"puts? .{0,60} token .{0,20} (?:onto|into|on) the battlefield", re.I),
    ]),
    ("counters", [
        re.compile(r"\bproliferate\b", re.I),
        re.compile(r"puts? .{0,20} \+\d+/\+\d+ counter", re.I),
        re.compile(r"puts? .{0,20} -\d+/-\d+ counter", re.I),
        re.compile(r"puts? .{0,20} counter[s]? .{0,30} on", re.I),
        re.compile(r"removes? .{0,20} counter", re.I),
    ]),
    ("ramp", [
        re.compile(r"add[s]? [^\n.]{0,40} mana", re.I),
        re.compile(r"search .{0,40} library .{0,40} (?:basic )?land card", re.I),
        re.compile(r"costs? \{?\d+\}? (?:generic )?(?:mana )?less", re.I),
        re.compile(r"without paying .{0,20} mana cost", re.I),
        re.compile(r"land .{0,30} additional .{0,30} land", re.I),
    ]),
    ("graveyard", [
        re.compile(r"return[s]? .{0,60} from .{0,20} graveyard", re.I),
        re.compile(r"\bmills?\b \d+", re.I),
        re.compile(r"puts? .{0,30} card[s]? .{0,20} into .{0,20} graveyard from .{0,20} library", re.I),
        re.compile(r"from your graveyard", re.I),
        re.compile(r"exile .{0,30} from .{0,20} (?:your |a |the )?graveyard", re.I),
    ]),
    # disruption split into three distinct categories:
    ("counterspell", [
        re.compile(r"counter target spell", re.I),
        re.compile(r"counter target .{0,40} spell", re.I),
        re.compile(r"counter that spell", re.I),
        re.compile(r"counter target activated", re.I),
        re.compile(r"counter target triggered", re.I),
        re.compile(r"counters? .{0,20} spell unless", re.I),
    ]),
    ("discard", [
        re.compile(r"(?:target player|that player|opponent|each player|each opponent) discards?", re.I),
        re.compile(r"discards? .{0,20} card[s]? (?:at random|of your choice|from hand)", re.I),
        re.compile(r"discards? their hand", re.I),
        re.compile(r"discards? a card", re.I),
    ]),
    ("stax", [
        re.compile(r"(?:can't|cannot) cast spells", re.I),
        re.compile(r"(?:can't|cannot) cast .{0,40} spells", re.I),
        re.compile(r"(?:can't|cannot) activate abilities", re.I),
        re.compile(r"(?:can't|cannot) attack", re.I),
        re.compile(r"spells? .{0,30} (?:can't|cannot) be cast", re.I),
        re.compile(r"(?:players?|opponents?) (?:can't|cannot) .{0,30} (?:more than|unless)", re.I),
    ]),
    ("tutor", [
        re.compile(r"search your library for .{0,60} card", re.I),
    ]),
    ("life", [
        re.compile(r"you gain \d+ life", re.I),
        re.compile(r"gain[s]? \d+ life", re.I),
        re.compile(r"you gain X life", re.I),
        re.compile(r"your life total becomes", re.I),
        re.compile(r"each opponent loses \d+ life", re.I),
    ]),
    ("pump", [
        re.compile(r"gets? \+\d+/[+\-]\d+", re.I),
        re.compile(r"gets? \+X/\+\d", re.I),
        re.compile(r"gets? \+\d/\+X", re.I),
        re.compile(r"gets? \+X/\+X", re.I),
        re.compile(r"base power and toughness", re.I),
        re.compile(r"creatures? you control get \+", re.I),
    ]),
    ("steal", [
        re.compile(r"gain control of target", re.I),
        re.compile(r"gain control of .{0,40} target", re.I),
        re.compile(r"gains? control of (?:target|all|each|that)", re.I),
        re.compile(r"exchange control", re.I),
    ]),
    ("copy", [
        re.compile(r"copy target spell", re.I),
        re.compile(r"copy of target", re.I),
        re.compile(r"copy of .{0,40} spell", re.I),
        re.compile(r"becomes? a copy of", re.I),
        re.compile(r"create[s]? a token that.s a copy", re.I),
    ]),
    ("blink", [
        re.compile(r"exile target .{0,60} you control.{0,20} return it", re.I),
        re.compile(r"exile .{0,40} then return .{0,40} to the battlefield", re.I),
        re.compile(r"phases? out", re.I),
    ]),
]


def strip_keyword_names(text: str, keywords: list[str]) -> str:
    """
    Remove named keyword strings from oracle text before Layer 2 regex.

    Prevents double-counting abilities already captured by the keywords field.
    E.g., a card with Flying in its keywords field may also have "Flying" at
    the start of its oracle text — stripping it avoids counting it twice.
    """
    for kw in keywords:
        text = re.sub(rf'\b{re.escape(kw)}\b', '', text, flags=re.I)
    # Clean up leftover punctuation/whitespace artifacts
    text = re.sub(r',\s*,', ',', text)
    text = re.sub(r'^[\s,;]+|[\s,;]+$', '', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


def classify_with_regex(text_after_keyword_strip: str) -> list[str]:
    """
    Return ability category tags matched by regex against oracle text.
    Returns ["other"] if no patterns match but text is non-empty.
    Returns [] for blank oracle text (e.g. vanilla creatures, lands).
    """
    if not text_after_keyword_strip.strip():
        return []
    matched = [cat for cat, patterns in _PATTERNS if any(p.search(text_after_keyword_strip) for p in patterns)]
    return matched if matched else ["other"]


# ---------------------------------------------------------------------------
# Mana / oracle cost parsing
# ---------------------------------------------------------------------------

_REMINDER_RE = re.compile(r'\([^)]+\)')
_MANA_SYM_RE = re.compile(r'\{([^}]+)\}')
_ALT_COST_RE = re.compile(
    r'(?:rather than pay[^,.]*cost|you may (?:cast|play) .{0,40} without paying)',
    re.I,
)
_ADDITIONAL_COST_RE = re.compile(r'[Aa]s an additional cost to cast (?:this spell|it)', re.I)


def strip_reminder_text(text: str) -> str:
    return _REMINDER_RE.sub('', text).strip()


def _mana_symbol_value(sym: str) -> float:
    sym = sym.strip()
    if sym.isdigit():
        return float(sym)
    if sym.upper() in ('X', 'Y', 'Z'):
        return 0.0
    if '/' in sym:
        return 1.0  # hybrid / phyrexian
    return 1.0


def parse_mana_cost_string(mana_cost: str | None) -> tuple[float, int]:
    """Returns (cmc, x_count). CMC treats X as 0, matching Scryfall's convention."""
    if not mana_cost:
        return 0.0, 0
    symbols = _MANA_SYM_RE.findall(mana_cost)
    x_count = sum(1 for s in symbols if s.strip().upper() == 'X')
    cmc = sum(_mana_symbol_value(s) for s in symbols)
    return float(cmc), x_count


def parse_activated_ability_mana_costs(oracle_text: str) -> list[float]:
    """Extract mana values from activated ability cost portions (text before ':' on each line)."""
    costs = []
    for line in oracle_text.split('\n'):
        colon_idx = line.find(':')
        if colon_idx == -1 or '{' not in line[:colon_idx]:
            continue
        symbols = _MANA_SYM_RE.findall(line[:colon_idx])
        mana_sum = sum(_mana_symbol_value(s) for s in symbols if s.strip().upper() not in ('T', 'Q'))
        costs.append(mana_sum)
    return costs


# ---------------------------------------------------------------------------
# Scryfall bulk data (mirrors Post 1 — uses shared cache by default)
# ---------------------------------------------------------------------------

def _get_bulk_index() -> list[dict]:
    resp = requests.get(
        "https://api.scryfall.com/bulk-data",
        headers={"User-Agent": "gatheringdata-blog-analysis/1.0"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"]


def _download_to_file(url: str, dest: Path) -> None:
    resp = requests.get(
        url, headers={"User-Agent": "gatheringdata-blog-analysis/1.0"},
        timeout=300, stream=True,
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
    """Return path to a locally-cached Scryfall bulk file. Downloads only when stale."""
    print(f"Checking Scryfall index for {bulk_type}...")
    index = _get_bulk_index()
    entry = next(f for f in index if f["type"] == bulk_type)
    cache_key = entry["updated_at"][:19].replace(":", "-")

    # Check shared Post 1 cache first
    for search_dir in [SCRYFALL_CACHE_DIR, LOCAL_CACHE_DIR]:
        candidate = search_dir / f"{bulk_type}--{cache_key}.json"
        if candidate.exists():
            print(f"  Cache hit: {candidate}")
            return candidate

    # Stale — remove old local copies and download fresh
    for stale in LOCAL_CACHE_DIR.glob(f"{bulk_type}--*.json"):
        stale.unlink()

    dest = LOCAL_CACHE_DIR / f"{bulk_type}--{cache_key}.json"
    print(f"  Downloading from {entry['download_uri']}...")
    _download_to_file(entry["download_uri"], dest)
    return dest


def compute_first_print_years(all_cards_path: Path) -> dict[str, int]:
    mapping_cache = LOCAL_CACHE_DIR / f"first_print_years--{all_cards_path.stem}.json"
    if mapping_cache.exists():
        print("  First-print year mapping: cache hit")
        with open(mapping_cache) as f:
            return json.load(f)

    print(f"  Computing first-print years from {all_cards_path.name} (streaming)...")
    first_prints: dict[str, str] = {}
    with open(all_cards_path, "rb") as f:
        for card in ijson.items(f, "item"):
            oid = card.get("oracle_id")
            released = card.get("released_at")
            if oid and released:
                if oid not in first_prints or released < first_prints[oid]:
                    first_prints[oid] = released

    result = {oid: int(d[:4]) for oid, d in first_prints.items()}
    with open(mapping_cache, "w") as f:
        json.dump(result, f)
    print(f"  Saved mapping for {len(result):,} cards")
    return result


# ---------------------------------------------------------------------------
# DataFrame construction
# ---------------------------------------------------------------------------

def _get_oracle_text_and_mana(card: dict) -> tuple[str, str]:
    """Extract oracle text and mana cost, using front face for double-faced cards."""
    mana_cost = card.get("mana_cost", "") or ""
    oracle_text = card.get("oracle_text", "") or ""
    faces = card.get("card_faces")
    if faces:
        front = faces[0]
        if not mana_cost:
            mana_cost = front.get("mana_cost", "") or ""
        if not oracle_text:
            oracle_text = front.get("oracle_text", "") or ""
    return oracle_text, mana_cost


def build_dataframe(
    oracle_cards: list[dict],
    first_print_years: dict[str, int],
) -> pd.DataFrame:
    rows = []
    for card in oracle_cards:
        if card.get("layout") in EXCLUDED_LAYOUTS:
            continue

        oracle_id = card.get("oracle_id", "")
        type_line = card.get("type_line", "")
        is_land = "Land" in type_line and "Artifact" not in type_line

        first_year = first_print_years.get(oracle_id)
        if not first_year:
            released = card.get("released_at", "")
            first_year = int(released[:4]) if released else None

        oracle_text, mana_cost = _get_oracle_text_and_mana(card)
        stripped_text = strip_reminder_text(oracle_text)

        cmc = float(card.get("cmc") or card.get("mana_value") or 0.0)
        _, x_count = parse_mana_cost_string(mana_cost)

        activated_costs = parse_activated_ability_mana_costs(stripped_text)
        alt_cost = bool(_ALT_COST_RE.search(oracle_text))
        additional_cost = bool(_ADDITIONAL_COST_RE.search(oracle_text))

        # Layer 1: named keyword abilities
        keywords = card.get("keywords") or []
        keyword_count = len(keywords)

        # Layer 2: oracle-text abilities via regex
        # Strip keyword names first so Layer 1 and Layer 2 don't overlap
        text_for_regex = strip_keyword_names(stripped_text, keywords)
        categories = [] if is_land else classify_with_regex(text_for_regex)
        semantic_count = len([c for c in categories if c != "other"])
        # "other" counts as 1 only if the card has text we couldn't classify
        if categories == ["other"]:
            semantic_count = 1

        total_ability_count = keyword_count + semantic_count

        rows.append({
            "name": card.get("name"),
            "oracle_id": oracle_id,
            "first_print_year": first_year,
            "type_line": type_line,
            "is_land": is_land,
            "mana_cost": mana_cost,
            "cmc": cmc,
            "x_count": x_count,
            "has_x": x_count > 0,
            "has_alt_cost": alt_cost,
            "has_additional_cost": additional_cost,
            "activated_costs": activated_costs,
            "keywords": keywords,
            "keyword_count": keyword_count,
            "categories": categories,
            "semantic_count": semantic_count,
            "total_ability_count": total_ability_count,
        })

    df = pd.DataFrame(rows)
    df["keywords_per_cmc"] = df.apply(
        lambda r: r["keyword_count"] / r["cmc"] if r["cmc"] > 0 else None, axis=1
    )
    df["semantic_per_cmc"] = df.apply(
        lambda r: r["semantic_count"] / r["cmc"] if r["cmc"] > 0 else None, axis=1
    )
    df["abilities_per_cmc"] = df.apply(
        lambda r: r["total_ability_count"] / r["cmc"] if r["cmc"] > 0 else None, axis=1
    )

    print(f"DataFrame: {len(df):,} cards, years {df['first_print_year'].min()}–{df['first_print_year'].max()}")
    return df


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------

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


def _smooth(series: pd.Series, window: int = 3) -> pd.Series:
    return series.rolling(window, center=True, min_periods=1).mean()


# ---------------------------------------------------------------------------
# Chart 1: Keywords per mana value over time
# ---------------------------------------------------------------------------

def chart_keywords_per_cmc(df: pd.DataFrame):
    d = (
        df[~df["is_land"] & (df["cmc"] > 0) & (df["first_print_year"] < CURRENT_YEAR)]
        .groupby("first_print_year")["keywords_per_cmc"].mean()
        .reset_index().rename(columns={"first_print_year": "year", "keywords_per_cmc": "mean"})
        .sort_values("year")
    )
    d["smoothed"] = _smooth(d["mean"])

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.fill_between(d["year"], d["mean"], alpha=0.15, color=ACCENT)
    ax.plot(d["year"], d["mean"], color=ACCENT, linewidth=1, alpha=0.5, label="Annual avg")
    ax.plot(d["year"], d["smoothed"], color=ACCENT_DARK, linewidth=2.5, label="3-year rolling avg")
    ax.legend(fontsize=10, frameon=False)
    apply_blog_style(ax, title="Keywords per mana value, 1993–present",
                     xlabel="Year", ylabel="Avg keyword count ÷ CMC")
    ax.set_xlim(1992.5, d["year"].max() + 0.5)
    fig.tight_layout()
    save(fig, "keywords_per_cmc.png")

    print("\nKeywords per CMC (selected years):")
    for yr in [1993, 2000, 2010, 2020, CURRENT_YEAR - 1]:
        row = d[d["year"] == yr]
        if not row.empty:
            print(f"  {yr}: {row['mean'].values[0]:.3f}")


# ---------------------------------------------------------------------------
# Chart 2: Semantic ability categories per mana value over time
# ---------------------------------------------------------------------------

def chart_semantic_per_cmc(df: pd.DataFrame):
    d = (
        df[~df["is_land"] & (df["cmc"] > 0) & (df["first_print_year"] < CURRENT_YEAR)]
        .groupby("first_print_year")["semantic_per_cmc"].mean()
        .reset_index().rename(columns={"first_print_year": "year", "semantic_per_cmc": "mean"})
        .sort_values("year")
    )
    d["smoothed"] = _smooth(d["mean"])

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.fill_between(d["year"], d["mean"], alpha=0.15, color=ACCENT)
    ax.plot(d["year"], d["mean"], color=ACCENT, linewidth=1, alpha=0.5, label="Annual avg")
    ax.plot(d["year"], d["smoothed"], color=ACCENT_DARK, linewidth=2.5, label="3-year rolling avg")
    ax.legend(fontsize=10, frameon=False)
    apply_blog_style(ax, title="Oracle-text ability categories per mana value, 1993–present",
                     xlabel="Year", ylabel="Avg category count ÷ CMC")
    ax.set_xlim(1992.5, d["year"].max() + 0.5)
    fig.tight_layout()
    save(fig, "semantic_per_cmc.png")


# ---------------------------------------------------------------------------
# Chart 3: Total abilities per mana value — the headline chart
# ---------------------------------------------------------------------------

def chart_total_abilities_per_cmc(df: pd.DataFrame):
    base = df[~df["is_land"] & (df["cmc"] > 0) & ~df["has_x"] & (df["first_print_year"] < CURRENT_YEAR)]

    overall = (
        base.groupby("first_print_year")["abilities_per_cmc"].mean()
        .reset_index().rename(columns={"first_print_year": "year", "abilities_per_cmc": "mean"})
        .sort_values("year")
    )
    overall["smoothed"] = _smooth(overall["mean"])

    cmc_colors = {2: "#e08080", 3: "#80a0e0", 4: "#80c080"}
    cmc_data = {}
    for cmc_val in [2, 3, 4]:
        d = (
            base[base["cmc"] == cmc_val]
            .groupby("first_print_year")["total_ability_count"].mean()
            .reset_index().rename(columns={"first_print_year": "year", "total_ability_count": "mean"})
            .sort_values("year")
        )
        d["smoothed"] = _smooth(d["mean"])
        cmc_data[cmc_val] = d

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.fill_between(overall["year"], overall["mean"], alpha=0.15, color=ACCENT)
    ax1.plot(overall["year"], overall["mean"], color=ACCENT, linewidth=1, alpha=0.5)
    ax1.plot(overall["year"], overall["smoothed"], color=ACCENT_DARK, linewidth=2.5)
    apply_blog_style(ax1, title="Total abilities per mana value (all cards)",
                     xlabel="Year", ylabel="Avg (keywords + categories) ÷ CMC")
    ax1.set_xlim(1992.5, overall["year"].max() + 0.5)

    for cmc_val, d in cmc_data.items():
        ax2.plot(d["year"], d["smoothed"], color=cmc_colors[cmc_val],
                 linewidth=2.5, label=f"CMC {cmc_val}")
    ax2.legend(fontsize=10, frameon=False)
    apply_blog_style(ax2, title="Ability count by CMC over time",
                     xlabel="Year", ylabel="Avg ability count (keywords + categories)")
    ax2.set_xlim(1992.5, max(d["year"].max() for d in cmc_data.values()) + 0.5)

    fig.tight_layout()
    save(fig, "total_abilities_per_cmc.png")

    print("\nTotal ability count at CMC=3 (selected years):")
    d3 = cmc_data[3]
    for yr in [1993, 2000, 2010, 2020, CURRENT_YEAR - 1]:
        row = d3[d3["year"] == yr]
        if not row.empty:
            print(f"  {yr}: {row['smoothed'].values[0]:.2f}")


# ---------------------------------------------------------------------------
# Chart 4: Power creep by ability type
# ---------------------------------------------------------------------------

def chart_creep_by_ability_type(df: pd.DataFrame):
    """
    Small multiples: for each oracle-text ability category, how has the average
    CMC of cards carrying that ability changed over time?
    Downward trend = that ability type got cheaper = power creep.
    """
    base = df[
        ~df["is_land"] & (df["cmc"] > 0) & (df["first_print_year"] < CURRENT_YEAR)
        & df["categories"].apply(lambda c: bool(c) and c != ["other"])
    ].copy()

    records = [
        {"year": row["first_print_year"], "category": cat, "cmc": row["cmc"]}
        for _, row in base.iterrows()
        for cat in row["categories"]
        if cat != "other"
    ]
    if not records:
        print("No data for creep-by-ability-type chart")
        return

    long_df = pd.DataFrame(records)
    top_cats = (
        long_df.groupby("category").size().sort_values(ascending=False)
        .head(12).index.tolist()
    )

    nrows, ncols = 3, 4
    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 9), sharex=True)
    axes_flat = axes.flatten()

    for i, cat in enumerate(top_cats):
        ax = axes_flat[i]
        d = (
            long_df[long_df["category"] == cat]
            .groupby("year")["cmc"].mean().reset_index().sort_values("year")
        )
        d["smoothed"] = _smooth(d["cmc"])
        ax.fill_between(d["year"], d["cmc"], alpha=0.1, color=ACCENT)
        ax.plot(d["year"], d["cmc"], color=ACCENT, linewidth=0.8, alpha=0.4)
        ax.plot(d["year"], d["smoothed"], color=ACCENT_DARK, linewidth=2)
        ax.set_title(cat, color=TEXT, fontsize=10, fontweight="bold")
        ax.set_facecolor("white")
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
        ax.grid(axis="y", color=BORDER, linewidth=0.5)
        ax.set_axisbelow(True)
        ax.set_xlim(1992.5, d["year"].max() + 0.5)

    for j in range(len(top_cats), len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.suptitle(
        "Average CMC of cards carrying each oracle-text ability, 1993–present\n"
        "(downward trend = that ability type got cheaper over time)",
        color=TEXT, fontsize=12, fontweight="bold", y=1.01,
    )
    fig.text(0.5, -0.01, "Year", ha="center", color=TEXT_SECONDARY, fontsize=11)
    fig.text(-0.01, 0.5, "Average CMC", va="center", rotation="vertical",
             color=TEXT_SECONDARY, fontsize=11)
    fig.tight_layout()
    save(fig, "creep_by_ability_type.png")

    print("\nTop oracle-text categories by card count:")
    for cat, count in long_df.groupby("category").size().sort_values(ascending=False).head(12).items():
        print(f"  {cat}: {count:,}")


# ---------------------------------------------------------------------------
# Chart 5: Distribution shift at fixed CMC
# ---------------------------------------------------------------------------

def chart_distribution_shift(df: pd.DataFrame):
    """
    For CMC=2 and CMC=3 cards, compare the distribution of total ability counts
    in 1993–2000 vs 2015–2025. Are newer cards at the same cost more ability-rich?
    """
    base = df[~df["is_land"] & df["cmc"].isin([2.0, 3.0]) & ~df["has_x"] & df["first_print_year"].notna()]
    early  = base[base["first_print_year"].between(1993, 2000)]
    recent = base[base["first_print_year"].between(2015, 2025)]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for i, cmc_val in enumerate([2, 3]):
        ax = axes[i]
        e = early[early["cmc"] == cmc_val]["total_ability_count"]
        r = recent[recent["cmc"] == cmc_val]["total_ability_count"]
        max_val = max(e.max() if len(e) else 0, r.max() if len(r) else 0)
        bins = range(0, int(max_val) + 3)

        ax.hist(e, bins=bins, density=True, alpha=0.65, color=ACCENT_DARK,
                label=f"1993–2000 (n={len(e):,})", width=0.4, align="left")
        ax.hist(r, bins=bins, density=True, alpha=0.65, color="#e08080",
                label=f"2015–2025 (n={len(r):,})", width=0.4, align="mid")
        ax.axvline(e.mean(), color=ACCENT_DARK, linewidth=1.5, linestyle="--", alpha=0.9)
        ax.axvline(r.mean(), color="#e08080", linewidth=1.5, linestyle="--", alpha=0.9)
        ax.legend(fontsize=9, frameon=False)
        apply_blog_style(ax, title=f"CMC = {cmc_val}: ability count distribution by era",
                         xlabel="Total ability count", ylabel="Density")

        print(f"\nCMC={cmc_val} distribution shift:")
        print(f"  1993–2000: mean={e.mean():.2f}, median={e.median():.1f} (n={len(e):,})")
        print(f"  2015–2025: mean={r.mean():.2f}, median={r.median():.1f} (n={len(r):,})")

    fig.tight_layout()
    save(fig, "distribution_shift.png")


# ---------------------------------------------------------------------------
# Exemplar output
# ---------------------------------------------------------------------------

EXEMPLAR_PAIRS = [
    ("Lightning Bolt",     "Shock",             "Direct damage: same cost, less effect over time"),
    ("Counterspell",       "Mana Leak",          "Disruption: similar effect, lower cost"),
    ("Serra Angel",        "Baneslayer Angel",   "Combat: same cost (CMC 5), far more abilities"),
    ("Terror",             "Go for the Throat",  "Removal: same cost, fewer restrictions"),
    ("Grizzly Bears",      "Garruk's Companion", "Body: CMC 2 → 2, vanilla → 3/2 trample"),
    ("Force of Will",      "Force of Negation",  "Alternative cost: newer, narrower effect"),
    ("Wrath of God",       "Day of Judgment",    "Mass removal: same CMC, same effect"),
    ("Ancestral Recall",   "Ponder",             "Card advantage: different cost-to-draw ratio"),
]
EXEMPLAR_NAMES = {name for pair in EXEMPLAR_PAIRS for name in pair[:2]}


def output_exemplar_table(df: pd.DataFrame):
    cols = ["name", "first_print_year", "cmc", "x_count", "keywords",
            "keyword_count", "categories", "semantic_count", "total_ability_count"]
    exemplars = df[df["name"].isin(EXEMPLAR_NAMES)][cols].copy()
    exemplars["keywords"]   = exemplars["keywords"].apply(lambda x: ", ".join(x) if x else "")
    exemplars["categories"] = exemplars["categories"].apply(lambda x: ", ".join(x) if x else "")
    exemplars = exemplars.sort_values("name")

    csv_path = OUTPUT_DIR / "exemplar_profiles.csv"
    exemplars.to_csv(csv_path, index=False)
    print(f"\nExemplar profiles → {csv_path}")
    print(exemplars.to_string(index=False))

    print("\nExemplar pairs (Δ CMC, Δ abilities):")
    for early_name, late_name, theme in EXEMPLAR_PAIRS:
        e = exemplars[exemplars["name"] == early_name]
        l = exemplars[exemplars["name"] == late_name]
        if e.empty or l.empty:
            print(f"  {theme}: card not found")
            continue
        er, lr = e.iloc[0], l.iloc[0]
        print(f"  {theme}")
        print(f"    {er['name']} ({int(er['first_print_year'])}, CMC={er['cmc']:.0f}, "
              f"abilities={int(er['total_ability_count'])})")
        print(f"    {lr['name']} ({int(lr['first_print_year'])}, CMC={lr['cmc']:.0f}, "
              f"abilities={int(lr['total_ability_count'])})")
        print(f"    Δ CMC={lr['cmc']-er['cmc']:+.0f}, Δ abilities={int(lr['total_ability_count'])-int(er['total_ability_count']):+d}")


# ---------------------------------------------------------------------------
# "Other" bucket exploration
# ---------------------------------------------------------------------------

# Words to ignore in the word cloud / phrase analysis
_STOPWORDS = {
    "a", "an", "the", "of", "to", "in", "is", "it", "its", "that", "this",
    "and", "or", "you", "your", "may", "not", "no", "at", "on", "by", "be",
    "for", "from", "as", "with", "any", "each", "all", "one", "if", "when",
    "than", "have", "has", "until", "end", "turn", "put", "get", "gets",
    "are", "were", "was", "would", "those", "then", "they", "them", "their",
    "which", "who", "that", "into", "onto", "can", "do", "up", "out", "so",
    "also", "only", "more", "other", "another", "same", "under", "over",
}


def _ngrams(words: list[str], n: int) -> list[str]:
    return [" ".join(words[i:i+n]) for i in range(len(words) - n + 1)]


def _tokenize(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z']+", text.lower()) if w not in _STOPWORDS and len(w) > 2]


def explore_other_bucket(df: pd.DataFrame, oracle_cards_raw: list[dict]):
    """
    Diagnostic charts for cards landing in the 'other' category.
    Goal: understand what abilities we're not capturing so we can improve patterns.
    """
    from collections import Counter
    from wordcloud import WordCloud

    other_ids = set(
        df[(df["categories"].apply(lambda c: c == ["other"])) & ~df["is_land"]]["oracle_id"]
    )
    other_df = df[df["oracle_id"].isin(other_ids)].copy()
    all_nonland = df[~df["is_land"] & (df["cmc"] > 0)]

    print(f"\n--- Other bucket: {len(other_df):,} cards ({len(other_df)/len(all_nonland)*100:.0f}% of non-land) ---")

    # Pull oracle text for other cards (after keyword stripping, use raw stripped text)
    id_to_raw = {c.get("oracle_id"): c for c in oracle_cards_raw}
    other_texts = []
    for oid in other_ids:
        card = id_to_raw.get(oid)
        if not card:
            continue
        text, _ = _get_oracle_text_and_mana(card)
        stripped = strip_reminder_text(text)
        kws = card.get("keywords") or []
        cleaned = strip_keyword_names(stripped, kws)
        if cleaned.strip():
            other_texts.append(cleaned)

    all_other_text = " ".join(other_texts)
    all_words = _tokenize(all_other_text)
    word_freq = Counter(all_words)

    # --- Trigrams (most actionable for pattern-writing) ---
    all_trigrams = Counter()
    for text in other_texts:
        words = _tokenize(text)
        all_trigrams.update(_ngrams(words, 3))
    top_trigrams = all_trigrams.most_common(30)

    # --- Fig 1: Top trigrams bar chart ---
    fig, ax = plt.subplots(figsize=(10, 8))
    phrases, counts = zip(*top_trigrams) if top_trigrams else ([], [])
    y = range(len(phrases))
    ax.barh(list(y), list(counts), color=ACCENT_DARK, alpha=0.8)
    ax.set_yticks(list(y))
    ax.set_yticklabels(list(phrases), fontsize=9)
    ax.invert_yaxis()
    apply_blog_style(ax, title='Most common 3-word phrases in "other" oracle text',
                     xlabel="Occurrences", ylabel="")
    ax.yaxis.label.set_visible(False)
    fig.tight_layout()
    save(fig, "other_top_trigrams.png")

    # --- Fig 2: Word cloud ---
    if word_freq:
        wc = WordCloud(
            width=1200, height=600, background_color="white",
            colormap="Blues", max_words=150,
            prefer_horizontal=0.9,
        ).generate_from_frequencies(word_freq)
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        ax.set_title('Word cloud: "other" oracle text', color=TEXT,
                     fontsize=13, fontweight="bold", pad=12)
        fig.tight_layout()
        save(fig, "other_word_cloud.png")

    # --- Fig 3: Card type breakdown — other vs. all ---
    def get_main_type(type_line: str) -> str:
        for t in ["Creature", "Instant", "Sorcery", "Enchantment", "Artifact",
                  "Planeswalker", "Land", "Battle"]:
            if t in type_line:
                return t
        return "Other"

    other_types = other_df["type_line"].apply(get_main_type).value_counts(normalize=True) * 100
    all_types   = all_nonland["type_line"].apply(get_main_type).value_counts(normalize=True) * 100
    type_index  = other_types.index.union(all_types.index)

    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(type_index))
    w = 0.4
    ax.bar([i - w/2 for i in x], [other_types.get(t, 0) for t in type_index],
           width=w, color=ACCENT_DARK, alpha=0.85, label='"other" cards')
    ax.bar([i + w/2 for i in x], [all_types.get(t, 0) for t in type_index],
           width=w, color="#e08080", alpha=0.7, label="all non-land cards")
    ax.set_xticks(list(x))
    ax.set_xticklabels(list(type_index), fontsize=10)
    ax.legend(fontsize=10, frameon=False)
    apply_blog_style(ax, title='Card types: "other" vs. all non-land cards',
                     xlabel="Card type", ylabel="% of cards")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    fig.tight_layout()
    save(fig, "other_types.png")

    # --- Fig 4: Color breakdown — other vs. all ---
    def get_color(card_row) -> str:
        # Use type_line as proxy; actual colors need the raw data
        return "Unknown"

    # Pull colors from raw data for other cards
    color_map = {"W": "White", "U": "Blue", "B": "Black", "R": "Red", "G": "Green"}

    def card_color_cat(raw_card: dict) -> str:
        colors = raw_card.get("colors") or []
        if len(colors) >= 2:
            return "Multicolor"
        if len(colors) == 1:
            return color_map.get(colors[0], "Colorless")
        return "Colorless"

    other_color_counts: Counter = Counter()
    all_color_counts: Counter = Counter()
    for card in oracle_cards_raw:
        oid = card.get("oracle_id", "")
        cat = card_color_cat(card)
        all_color_counts[cat] += 1
        if oid in other_ids:
            other_color_counts[cat] += 1

    color_order = ["White", "Blue", "Black", "Red", "Green", "Multicolor", "Colorless"]
    color_palette = {
        "White": "#f5e6c8", "Blue": "#a8c8e8", "Black": "#9a8fa0",
        "Red": "#e8a090", "Green": "#90c890", "Multicolor": "#e8d080", "Colorless": "#c0c0c0",
    }
    o_total = sum(other_color_counts.values()) or 1
    a_total = sum(all_color_counts.values()) or 1

    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(color_order))
    w = 0.4
    ax.bar([i - w/2 for i in x],
           [other_color_counts.get(c, 0) / o_total * 100 for c in color_order],
           width=w, color=[color_palette[c] for c in color_order],
           edgecolor=ACCENT_DARK, linewidth=0.8, label='"other" cards')
    ax.bar([i + w/2 for i in x],
           [all_color_counts.get(c, 0) / a_total * 100 for c in color_order],
           width=w, color=[color_palette[c] for c in color_order],
           edgecolor="#e08080", linewidth=0.8, alpha=0.5, label="all cards")
    ax.set_xticks(list(x))
    ax.set_xticklabels(color_order, fontsize=10)
    ax.legend(fontsize=10, frameon=False)
    apply_blog_style(ax, title='Color identity: "other" vs. all cards',
                     xlabel="Color", ylabel="% of cards")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    fig.tight_layout()
    save(fig, "other_colors.png")

    # --- Fig 5: First-print year — other vs. all ---
    other_years = other_df[other_df["first_print_year"] < CURRENT_YEAR]["first_print_year"].value_counts().sort_index()
    all_years   = all_nonland[all_nonland["first_print_year"] < CURRENT_YEAR]["first_print_year"].value_counts().sort_index()
    other_pct   = (other_years / all_years * 100).dropna()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    ax1.bar(other_years.index, other_years.values, color=ACCENT_DARK, alpha=0.8, width=0.8)
    apply_blog_style(ax1, title='Cards in "other" by first-print year', ylabel="Card count")
    ax2.plot(other_pct.index, _smooth(other_pct), color=ACCENT_DARK, linewidth=2)
    ax2.fill_between(other_pct.index, _smooth(other_pct), alpha=0.15, color=ACCENT)
    apply_blog_style(ax2, title='% of each year\'s cards landing in "other"',
                     xlabel="Year", ylabel="% of year's cards")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax2.set_xlim(1992.5, other_pct.index.max() + 0.5)
    fig.tight_layout()
    save(fig, "other_by_year.png")

    # Print top trigrams to console for pattern-writing reference
    print("\nTop trigrams in 'other' oracle text (use these to write new patterns):")
    for phrase, count in top_trigrams:
        print(f"  {count:>5}  {phrase}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(df: pd.DataFrame):
    from collections import Counter
    print("\n--- Summary ---")
    nl = df[~df["is_land"] & (df["cmc"] > 0)]
    print(f"Total cards: {len(df):,}  |  Non-land, non-zero-CMC: {len(nl):,}")
    print(f"  With ≥1 keyword:       {(nl['keyword_count'] > 0).sum():,} ({(nl['keyword_count'] > 0).mean()*100:.0f}%)")
    print(f"  With ≥1 oracle-text cat: {(nl['semantic_count'] > 0).sum():,} ({(nl['semantic_count'] > 0).mean()*100:.0f}%)")
    print(f"  Has X in cost:         {nl['has_x'].sum():,}")
    print(f"  Has alt cost:          {nl['has_alt_cost'].sum():,}")
    print(f"  Has additional cost:   {nl['has_additional_cost'].sum():,}")

    print("\nTop oracle-text categories:")
    all_cats: list[str] = [c for cats in df["categories"] for c in cats]
    for cat, n in Counter(all_cats).most_common(20):
        print(f"  {cat}: {n:,}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="MTG ability-to-cost ratio analysis")
    p.add_argument("--output-dir", type=Path, default=_DEFAULT_OUTPUT_DIR)
    p.add_argument("--scryfall-cache-dir", type=Path, default=_DEFAULT_SCRYFALL_CACHE)
    return p.parse_args()


def main():
    global OUTPUT_DIR, SCRYFALL_CACHE_DIR
    args = parse_args()
    OUTPUT_DIR = args.output_dir
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCRYFALL_CACHE_DIR = args.scryfall_cache_dir
    if not SCRYFALL_CACHE_DIR.exists():
        print(f"  Scryfall cache dir not found ({SCRYFALL_CACHE_DIR}); will download fresh")
        SCRYFALL_CACHE_DIR = LOCAL_CACHE_DIR

    oracle_path = fetch_bulk_file("oracle_cards")
    print("Loading oracle_cards...")
    with open(oracle_path) as f:
        oracle_cards: list[dict] = json.load(f)
    print(f"  {len(oracle_cards):,} entries")

    all_cards_path = fetch_bulk_file("all_cards")
    first_print_years = compute_first_print_years(all_cards_path)

    df = build_dataframe(oracle_cards, first_print_years)

    print("\nGenerating charts...")
    chart_keywords_per_cmc(df)
    chart_semantic_per_cmc(df)
    chart_total_abilities_per_cmc(df)
    chart_creep_by_ability_type(df)
    chart_distribution_shift(df)
    output_exemplar_table(df)
    explore_other_bucket(df, oracle_cards)
    print_summary(df)


if __name__ == "__main__":
    main()
