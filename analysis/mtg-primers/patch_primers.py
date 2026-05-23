"""
patch_primers.py
----------------
Fix bad/missing primer entries identified during audit:
  - 37-char Reddit wiki entries (Death & Taxes, Initiative Stompy, Lands)
  - Wrong-page hits (Show & Tell card page, Food Chain card page, Mystic Forge rulings page)
  - Completely wrong threads (Delver→Treefolk, Cloudpost→custom-card-creation)
  - Duplicate hit (Thassa's Oracle = same URL as Cephalid Breakfast)
  - Wrong-format forums (Maverick→Modern, Dimir Tempo→Standard, 4/5c Control→Lands URL)

Run:  uv run python patch_primers.py
"""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DATA_DIR   = Path("data")
RAW_DIR    = DATA_DIR / "raw"
INDEX_FILE = DATA_DIR / "primers.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (research bot; gatheringdata.blog)"}
FETCH_DELAY = 2.5

# ── Corrected URLs ─────────────────────────────────────────────────────────────
# Keyed by archetype name exactly as it appears in primers.json
CORRECTIONS = {
    # Was: Reddit wiki anchor → 37 chars of javascript redirect
    "Death & Taxes": "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/established-legacy/control/179856-deck-death-and-taxes",

    # Was: Reddit discussion post → 37 chars (javascript-heavy page)
    # No MTGSalvation primer exists for this newer archetype
    "Initiative Stompy": "https://minmaxblog.com/a-new-legacy-deck-innit/",

    # Was: Reddit wiki anchor → 37 chars
    "Lands": "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/established-legacy/control/535484-primer-lands",

    # Was: MTGSalvation card page (not a forum primer)
    "Show and Tell": "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/established-legacy/combo/179810-deck-sneak-show",

    # Was: MTGSalvation card page (not a forum primer)
    "Food Chain": "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/budget-legacy/185969-primer-food-chain-elves-fast-combo-elves",

    # Was: Treefolk thread in Modern (completely wrong deck and format)
    "Delver (Other)": "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/developing-legacy/607477-primer-deck-liechtenstein-delver",

    # Was: Custom card creation thread (completely wrong section)
    "Cloudpost / Tron Ramp": "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/developing-legacy/181890-primer-12-post",

    # Was: Modern archives (Maverick is a Legacy archetype with its own established thread)
    "Maverick": "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/established-legacy/midrange/179841-deck-maverick",

    # Was: Standard archives (Dimir Tempo is Legacy)
    "Dimir Tempo": "https://www.mtgsalvation.com/forums/the-game/legacy-type-1-5/developing-legacy/180605-ub-tempo",
}

# Entries with no good primer found — clear them so they show as known gaps
NO_PRIMER = {
    # Was: MTGSalvation rulings thread (not a deck primer)
    "Mystic Forge": "no dedicated Legacy primer found",

    # Was: same URL as Cephalid Breakfast (duplicate, 64k chars)
    "Thassa's Oracle": "no dedicated Legacy primer found (Doomsday covers the Oracle-win archetype)",

    # Was: Lands primer URL (535484) — wrong deck entirely
    "4/5c Control": "no dedicated Legacy primer found",
}


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def fetch_text(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return f"[fetch error: {e}]"

    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    if "reddit.com" in url:
        parts = []
        for el in soup.select("[data-testid='post-content'], .usertext-body, .md"):
            parts.append(el.get_text(" ", strip=True))
        return "\n\n".join(parts) if parts else soup.get_text(" ", strip=True)

    if "mtgsalvation" in url:
        parts = []
        for el in soup.select(".bbWrapper, .message-body"):
            parts.append(el.get_text(" ", strip=True))
        return "\n\n".join(parts) if parts else soup.get_text(" ", strip=True)

    main = soup.find("main") or soup.find("article") or soup.body
    return main.get_text(" ", strip=True) if main else soup.get_text(" ", strip=True)


def source_label(url: str) -> str:
    if "ddft.wiki"        in url: return "ddft.wiki"
    if "mtgsalvation"     in url: return "mtgsalvation"
    if "reddit.com"       in url: return "reddit"
    if "mtgthesource.com" in url: return "mtgthesource"
    if "minmaxblog.com"   in url: return "minmaxblog"
    return "other"


def run():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    index: dict = json.loads(INDEX_FILE.read_text()) if INDEX_FILE.exists() else {}

    print("=== Applying corrections ===\n")

    for archetype, url in CORRECTIONS.items():
        old = index.get(archetype, {})
        old_chars = old.get("char_count", "N/A")
        print(f"  fix  {archetype}  (was {old_chars} chars)  ...", end=" ", flush=True)

        time.sleep(FETCH_DELAY)
        text = fetch_text(url)
        raw_path = RAW_DIR / f"{slug(archetype)}.txt"
        raw_path.write_text(text, encoding="utf-8")

        source = source_label(url)
        index[archetype] = {
            "url":        url,
            "source":     source,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "char_count": len(text),
        }
        print(f"ok  ({len(text):,} chars)  [{source}]")
        INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False))

    print("\n=== Clearing no-primer entries ===\n")

    for archetype, reason in NO_PRIMER.items():
        old = index.get(archetype, {})
        old_url = old.get("url", "N/A")
        print(f"  clear  {archetype}  (was: {old_url})")
        index[archetype] = {
            "url":        None,
            "source":     None,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error":      reason,
        }
        # Remove stale raw file if present
        raw_path = RAW_DIR / f"{slug(archetype)}.txt"
        if raw_path.exists():
            raw_path.unlink()

    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False))

    print("\nDone.")
    found   = sum(1 for v in index.values() if v.get("url"))
    errored = sum(1 for v in index.values() if v.get("error"))
    print(f"  {found} with URLs,  {errored} errors/gaps")


if __name__ == "__main__":
    run()
