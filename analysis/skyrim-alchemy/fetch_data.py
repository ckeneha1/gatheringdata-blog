"""
fetch_data.py — UESP scraper for Skyrim alchemy ingredient data.

Fetches ingredient effects and spawn-counts-by-hold for all base-game
ingredients. Results are cached to data/raw/ so re-running is fast.

Usage:
    uv run python fetch_data.py                # fetch everything
    uv run python fetch_data.py --ingredient "Blue Mountain Flower"  # one ingredient

Output:
    data/raw/ingredients_list.json         — list of all ingredient names
    data/raw/ingredients/{name}.json       — per-ingredient effects + location data
"""

from __future__ import annotations
import argparse
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

UESP_API     = "https://en.uesp.net/w/api.php"
UESP_BASE    = "https://en.uesp.net/wiki/Skyrim:"
USER_AGENT   = "gatheringdata-blog-skyrim-scraper/1.0 (research project; contact via github.com/ckeneha1)"
REQUEST_DELAY = 0.6   # seconds between requests — polite crawling

RAW_DIR      = Path(__file__).parent / "data" / "raw"
ING_DIR      = RAW_DIR / "ingredients"
LIST_FILE    = RAW_DIR / "ingredients_list.json"

RAW_DIR.mkdir(parents=True, exist_ok=True)
ING_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# UESP hold names → canonical hold keys
# Some pages spell holds inconsistently; normalise here.
# ---------------------------------------------------------------------------

HOLD_ALIASES: dict[str, str] = {
    # The Rift
    "the rift": "The Rift",
    "riften": "The Rift",
    # Falkreath
    "falkreath hold": "Falkreath Hold",
    "falkreath": "Falkreath Hold",
    # Hjaalmarch
    "hjaalmarch": "Hjaalmarch",
    # The Pale
    "the pale": "The Pale",
    "dawnstar": "The Pale",
    # Whiterun Hold
    "whiterun hold": "Whiterun Hold",
    "whiterun": "Whiterun Hold",
    # Winterhold
    "winterhold": "Winterhold",
    # Eastmarch
    "eastmarch": "Eastmarch",
    "windhelm": "Eastmarch",
    # The Reach
    "the reach": "The Reach",
    "markarth": "The Reach",
    # Haafingar
    "haafingar": "Haafingar",
    "solitude": "Haafingar",
}


def normalise_hold(raw: str) -> str | None:
    """Return canonical hold name, or None if not a hold."""
    return HOLD_ALIASES.get(raw.strip().lower())


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT})


def _get_wikitext(page: str) -> str:
    """Fetch raw wikitext for a UESP page via the MediaWiki API."""
    resp = _session.get(
        UESP_API,
        params={"action": "parse", "page": page, "prop": "wikitext", "format": "json"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise ValueError(f"UESP API error for '{page}': {data['error']}")
    return data["parse"]["wikitext"]["*"]


def _get_html(page: str) -> BeautifulSoup:
    """Fetch rendered HTML for a UESP page."""
    resp = _session.get(
        UESP_API,
        params={"action": "parse", "page": page, "prop": "text", "format": "json"},
        timeout=30,
    )
    resp.raise_for_status()
    html = resp.json()["parse"]["text"]["*"]
    return BeautifulSoup(html, "html.parser")


# ---------------------------------------------------------------------------
# Parse ingredient list page
# ---------------------------------------------------------------------------

def fetch_ingredient_list() -> list[str]:
    """
    Return list of all Skyrim alchemy ingredient names (base + DLC) using
    the UESP category API.

    Uses Category:Skyrim-Alchemy-Ingredients rather than parsing the
    Ingredients page HTML — the category is authoritative and includes all
    110 ingredients (base + Dawnguard + Dragonborn + Hearthfire) without
    picking up non-ingredient pages.
    """
    if LIST_FILE.exists():
        print(f"  Ingredient list: cache hit ({LIST_FILE.name})")
        with open(LIST_FILE) as f:
            return json.load(f)

    print("Fetching ingredient list from UESP category API...")
    names: list[str] = []
    params: dict = {
        "action":      "query",
        "list":        "categorymembers",
        "cmtitle":     "Category:Skyrim-Ingredients",
        "cmlimit":     "500",
        "format":      "json",
    }

    while True:
        time.sleep(REQUEST_DELAY)
        resp = _session.get(UESP_API, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        for member in data["query"]["categorymembers"]:
            title = member["title"]
            # Titles are "Skyrim:Ingredient Name" — strip the namespace prefix
            if title.startswith("Skyrim:"):
                names.append(title[len("Skyrim:"):])

        # Follow API continuation cursor if there are more results
        if "continue" in data:
            params.update(data["continue"])
        else:
            break

    print(f"  Found {len(names)} ingredient names")
    with open(LIST_FILE, "w") as f:
        json.dump(names, f, indent=2)
    return names


# ---------------------------------------------------------------------------
# Parse individual ingredient page
# ---------------------------------------------------------------------------

# Matches: * 6 in [[Skyrim:Location|Display]] ([[Skyrim:Hold|Hold]])
# Also handles: * 6 around [[...]] ([[...]])
_LOCATION_RE = re.compile(
    r"\*\s*(\d+)\s+(?:in|around|inside|at|near|on|from)\s+"
    r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]"           # location name (display)
    r"\s*\(?(?:\[\[(?:[^\]|]+\|)?([^\]]+)\]\])?\)?",  # optional hold in parens
    re.I,
)

# Fallback: * 6 in Location (Hold) — unlinked hold
_LOCATION_PLAIN_RE = re.compile(
    r"\*\s*(\d+)\s+(?:in|around|inside|at|near|on|from)\s+"
    r"[^\(]+\(([^\)]+)\)",
    re.I,
)

# Ingredient Summary template parameters
_PARAM_RE = re.compile(r"\|\s*(\w+)\s*=\s*([^|\n}]+)")


def _extract_template_params(wikitext: str, template_name: str) -> dict[str, str]:
    """Extract key=value params from a named template in wikitext."""
    # Find the template block
    start = wikitext.find("{{" + template_name)
    if start == -1:
        return {}
    # Find matching closing }} — use while loop to skip by 2 after each match
    # so overlapping braces (e.g. }}}}) count as 2 pairs, not 3.
    depth = 0
    end = start
    i = start
    while i < len(wikitext):
        c2 = wikitext[i:i+2]
        if c2 == "{{":
            depth += 1
            i += 2
        elif c2 == "}}":
            depth -= 1
            if depth == 0:
                end = i + 2
                break
            i += 2
        else:
            i += 1
    block = wikitext[start:end]
    return {m.group(1).strip(): m.group(2).strip() for m in _PARAM_RE.finditer(block)}


def _clean_wikitext(text: str) -> str:
    """Strip wikilinks, templates, and HTML tags, returning plain text."""
    # [[Page|Display]] → Display
    text = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", text)
    # [[Page]] → Page
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    # {{Template|...}} → ''
    text = re.sub(r"\{\{[^}]+\}\}", "", text)
    # HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def _parse_section(wikitext: str, header: str) -> str:
    """Extract text of a named ==Section== from wikitext."""
    # Find section start (==Header== or ===Header===)
    pattern = re.compile(r"^={2,3}\s*" + re.escape(header) + r"\s*={2,3}", re.M)
    m = pattern.search(wikitext)
    if not m:
        return ""
    start = m.end()
    # Find next section of same or higher level
    next_section = re.compile(r"^={2,3}[^=]", re.M)
    nm = next_section.search(wikitext, start)
    end = nm.start() if nm else len(wikitext)
    return wikitext[start:end]


def fetch_ingredient(name: str) -> dict:
    """
    Fetch and parse one ingredient page from UESP.
    Returns a dict with effects, spawn data, and source URL.
    Caches result to data/raw/ingredients/{name}.json.
    """
    # Sanitise name for filesystem: replace spaces, apostrophes, slashes, ampersands
    safe_name = re.sub(r"[^\w\-]", "_", name)
    cache_path = ING_DIR / f"{safe_name}.json"
    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)

    print(f"  Fetching: {name}")
    time.sleep(REQUEST_DELAY)

    try:
        wikitext = _get_wikitext(f"Skyrim:{name}")
    except Exception as e:
        print(f"    ERROR: {e}")
        return {}

    # -- Effects from {{Ingredient Summary}} template --
    params = _extract_template_params(wikitext, "Ingredient Summary")
    effects: list[dict] = []
    for i in range(1, 5):
        eff_name = _clean_wikitext(params.get(f"eff{i}", ""))
        if eff_name:
            polarity = "negative" if params.get(f"type{i}", "").lower() in ("neg", "negative") else "positive"
            effects.append({"effect": eff_name, "polarity": polarity, "slot": i})

    # -- Spawn locations: aggregate by hold --
    hold_counts: dict[str, int] = {}

    def _process_location_line(line: str) -> None:
        """Parse one bullet line and add spawn count to hold_counts."""
        # Try linked format first
        m = _LOCATION_RE.match(line)
        if m:
            count = int(m.group(1))
            hold_raw = m.group(3) or ""
            hold = normalise_hold(hold_raw)
            if hold:
                hold_counts[hold] = hold_counts.get(hold, 0) + count
            return
        # Try plain-text hold in parens
        m2 = _LOCATION_PLAIN_RE.match(line)
        if m2:
            count = int(m2.group(1))
            hold = normalise_hold(m2.group(2))
            if hold:
                hold_counts[hold] = hold_counts.get(hold, 0) + count

    # Parse both ==Ingredients== (guaranteed samples) and ==Plants== (harvestable)
    for section_name in ("Ingredients", "Plants"):
        section = _parse_section(wikitext, section_name)
        for line in section.splitlines():
            if line.strip().startswith("*"):
                _process_location_line(line.strip())

    result = {
        "name": name,
        "source_url": f"https://en.uesp.net/wiki/Skyrim:{name.replace(' ', '_')}",
        "game_id": params.get("id", ""),
        "value": params.get("value", ""),
        "weight": params.get("weight", ""),
        "effects": effects,
        "hold_counts": hold_counts,
        "total_spawn_count": sum(hold_counts.values()),
    }

    with open(cache_path, "w") as f:
        json.dump(result, f, indent=2)

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Fetch Skyrim ingredient data from UESP")
    parser.add_argument("--ingredient", help="Fetch a single ingredient by name")
    parser.add_argument("--limit", type=int, help="Fetch only first N ingredients (for testing)")
    args = parser.parse_args()

    if args.ingredient:
        result = fetch_ingredient(args.ingredient)
        print(json.dumps(result, indent=2))
        return

    names = fetch_ingredient_list()
    if args.limit:
        names = names[:args.limit]

    print(f"\nFetching {len(names)} ingredients...")
    success, errors = 0, []
    for name in names:
        result = fetch_ingredient(name)
        if result:
            success += 1
        else:
            errors.append(name)

    print(f"\nDone: {success} succeeded, {len(errors)} errors")
    if errors:
        print("Errors:", errors)


if __name__ == "__main__":
    main()
