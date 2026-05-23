"""
fetch_primers.py
----------------
For each Legacy archetype, find the best available primer via DuckDuckGo,
fetch the full text, and store it as a structured JSON record.

Run:  uv run python fetch_primers.py
Output:
  data/primers.json          — index: archetype → {url, source, fetched_at}
  data/raw/<slug>.txt        — raw extracted text per archetype
"""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

# ── Archetype list (from MTGTop8 Legacy meta page) ────────────────────────────
ARCHETYPES = [
    "Dimir Tempo", "UR Tempo", "Eldrazi Aggro", "Boros Aggro", "Artifacts Blue",
    "Death & Taxes", "Mardu Aggro", "Maverick", "Mono Black Aggro", "Death's Shadow",
    "Initiative Stompy", "Dragon Stompy", "Goblins", "Esper Aggro", "BUG Midrange",
    "Merfolk", "MUD", "Grixis Aggro", "Delver (Other)", "Canadian Threshold",
    "Bant Aggro", "Humans", "Other - Aggro", "Artifacts Prison", "Lands",
    "UWx Control", "Pox", "4/5c Control", "Cradle Control", "Stoneblade",
    "Cloudpost / Tron Ramp", "Bant Control", "Stiflenought", "BUG Control",
    "Grixis Control", "Nic Fit", "Other - Control", "Show and Tell", "Doomsday",
    "Oops, All Spells!", "Reanimator", "Storm", "Aluren", "Dark Depths",
    "Painter", "Dredge", "Hogaak", "Mystic Forge", "Ruby Storm", "Infect",
    "Thassa's Oracle", "Food Chain", "Cephalid Breakfast", "Mono Black Combo",
    "Other - Combo",
]

# ── Known high-quality primers (skip search for these) ───────────────────────
# These are well-known, stable URLs worth hardcoding over search results.
KNOWN_PRIMERS = {
    # Dedicated wiki / external sites
    "Doomsday":            "https://ddft.wiki/",
    "Initiative Stompy":   "https://minmaxblog.com/a-new-legacy-deck-innit/",
    "Thassa's Oracle":     "https://minmaxblog.com/tainted-pact",

    # Legacy-established MTGSalvation threads
    "Death & Taxes":       "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/established-legacy/control/179856-deck-death-and-taxes",
    "Lands":               "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/established-legacy/control/535484-primer-lands",
    "Maverick":            "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/established-legacy/midrange/179841-deck-maverick",
    "Show and Tell":       "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/established-legacy/combo/179810-deck-sneak-show",

    # Legacy-developing MTGSalvation threads
    "Cloudpost / Tron Ramp": "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/developing-legacy/181890-primer-12-post",
    "Dimir Tempo":           "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/developing-legacy/180605-ub-tempo",
    "Delver (Other)":        "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/developing-legacy/607477-primer-deck-liechtenstein-delver",
    "Food Chain":            "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/budget-legacy/185969-primer-food-chain-elves-fast-combo-elves",
}

# ── Priority search sources (in order of preference) ─────────────────────────
SEARCH_SUFFIXES = [
    "site:mtgsalvation.com",
    "site:reddit.com/r/MTGLegacy",
    "site:mtgthesource.com",
]

DATA_DIR  = Path("data")
RAW_DIR   = DATA_DIR / "raw"
INDEX_FILE = DATA_DIR / "primers.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (research bot; gatheringdata.blog)"}
FETCH_DELAY  = 2.5  # seconds between page fetches — be polite
SEARCH_DELAY = 5.0  # seconds between DDG searches — avoid rate limiting


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def search_primer(archetype: str) -> str | None:
    """Return the best primer URL for an archetype via DuckDuckGo."""
    query = f'MTG Legacy "{archetype}" primer'
    with DDGS() as ddgs:
        for suffix in SEARCH_SUFFIXES:
            time.sleep(SEARCH_DELAY)
            try:
                results = list(ddgs.text(f"{query} {suffix}", max_results=3))
                if results:
                    return results[0]["href"]
            except Exception:
                continue
        # Fallback: no source filter
        time.sleep(SEARCH_DELAY)
        try:
            results = list(ddgs.text(query, max_results=5))
            return results[0]["href"] if results else None
        except Exception:
            return None


def fetch_text(url: str) -> str:
    """Fetch a URL and return clean body text."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return f"[fetch error: {e}]"

    soup = BeautifulSoup(r.text, "html.parser")

    # Remove nav, scripts, styles, sidebars
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    # Reddit: extract post + top-level comment bodies
    if "reddit.com" in url:
        parts = []
        for el in soup.select("[data-testid='post-content'], .usertext-body, .md"):
            parts.append(el.get_text(" ", strip=True))
        return "\n\n".join(parts) if parts else soup.get_text(" ", strip=True)

    # MTG Salvation: extract post bodies
    if "mtgsalvation" in url:
        parts = []
        for el in soup.select(".bbWrapper, .message-body"):
            parts.append(el.get_text(" ", strip=True))
        return "\n\n".join(parts) if parts else soup.get_text(" ", strip=True)

    # Generic fallback
    main = soup.find("main") or soup.find("article") or soup.body
    return main.get_text(" ", strip=True) if main else soup.get_text(" ", strip=True)


def run():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing index so reruns skip already-fetched archetypes
    index: dict = json.loads(INDEX_FILE.read_text()) if INDEX_FILE.exists() else {}

    for archetype in ARCHETYPES:
        if archetype in index:
            print(f"  skip  {archetype}  (already fetched)")
            continue

        print(f"  fetch {archetype}...", end=" ", flush=True)

        # 1. Resolve URL
        url = KNOWN_PRIMERS.get(archetype) or search_primer(archetype)
        if not url:
            print("no URL found")
            index[archetype] = {"url": None, "source": None, "fetched_at": None, "error": "no URL"}
            continue

        # 2. Fetch text
        time.sleep(FETCH_DELAY)
        text = fetch_text(url)

        # 3. Save raw text
        raw_path = RAW_DIR / f"{slug(archetype)}.txt"
        raw_path.write_text(text, encoding="utf-8")

        # 4. Update index
        source = (
            "ddft.wiki"        if "ddft.wiki"       in url else
            "mtgsalvation"     if "mtgsalvation"     in url else
            "reddit"           if "reddit.com"       in url else
            "mtgthesource"     if "mtgthesource.com" in url else
            "other"
        )
        index[archetype] = {
            "url":        url,
            "source":     source,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "char_count": len(text),
        }
        print(f"ok  ({len(text):,} chars)  [{source}]")

        # 5. Persist index after every archetype so partial runs are recoverable
        INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False))

    print(f"\nDone. {len(index)} archetypes in index.")
    found    = sum(1 for v in index.values() if v.get("url"))
    errored  = sum(1 for v in index.values() if v.get("error"))
    print(f"  {found} with URLs,  {errored} errors")


if __name__ == "__main__":
    run()
