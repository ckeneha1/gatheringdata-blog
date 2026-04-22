"""
fetch_data.py — MTG Legacy Tournament Overlay
Fetches and caches all raw data from MTGTop8 and Scryfall.

Run:  uv run fetch_data.py [--topcards-only] [--events-only] [--decks-only] [--banlist-only]
      uv run fetch_data.py          (runs all four jobs)

All fetches are idempotent: cached files are skipped. Delete a file to re-fetch it.
"""

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL   = "https://mtgtop8.com"
HEADERS    = {"User-Agent": "Mozilla/5.0 (compatible; research-scraper/1.0)"}
RATE_LIMIT = 0.5  # seconds between requests

DATA_DIR = Path(__file__).parent / "data"
RAW_DIR  = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# MTGTop8 meta IDs for Legacy by year
YEAR_META = {
    2022: 237,
    2023: 245,
    2024: 275,
    2025: 316,
}

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

_retry = Retry(
    total=5,
    backoff_factor=1.5,       # waits 1.5, 3, 6, 12, 24s between retries
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"],
    raise_on_status=False,
)
_adapter = HTTPAdapter(max_retries=_retry)

_session = requests.Session()
_session.headers.update(HEADERS)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)


def get(url: str, **kwargs) -> requests.Response:
    time.sleep(RATE_LIMIT)
    r = _session.get(url, timeout=30, **kwargs)
    r.raise_for_status()
    return r


def post(url: str, **kwargs) -> requests.Response:
    time.sleep(RATE_LIMIT)
    r = _session.post(url, timeout=30, **kwargs)
    r.raise_for_status()
    return r


def load_cache(path: Path) -> dict | list | None:
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_cache(path: Path, data: dict | list) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Job 1: Banlist (Scryfall)
# ---------------------------------------------------------------------------

def fetch_banlist() -> None:
    """Fetch current Legacy banned list from Scryfall. Saves to data/banlist.json.

    Note: Scryfall provides the *current* banned list only, not historical ban dates.
    Cards that changed status during 2022–2025 are not tracked here. For the MVP,
    the current list is used to flag "banned" vs. "outclassed" in gap analysis.
    Historical tracking TODO: parse https://magic.wizards.com/en/banned-restricted-list
    """
    out = DATA_DIR / "banlist.json"
    if load_cache(out) is not None:
        print("  banlist: cache hit, skipping")
        return

    print("  banlist: fetching from Scryfall...")
    banned: list[str] = []
    url = "https://api.scryfall.com/cards/search"
    params = {"q": "banned:legacy", "format": "json"}

    while url:
        r = get(url, params=params)
        data = r.json()
        banned.extend(c["name"] for c in data["data"])
        url = data.get("next_page")
        params = {}  # next_page URL already has params

    result = {
        "fetched_at": datetime.utcnow().isoformat(),
        "source": "scryfall",
        "note": "Current Legacy banned list only. Does not include historical ban dates.",
        "banned": sorted(banned),
    }
    save_cache(out, result)
    print(f"  banlist: saved {len(banned)} banned cards → {out}")


# ---------------------------------------------------------------------------
# Job 2: Topcards (flat card frequency per year, mainboard + sideboard)
# ---------------------------------------------------------------------------

def fetch_topcards_page(year: int, zone: str) -> dict:
    """POST to topcards endpoint for one year + zone combo, paginating until empty.

    Row structure: <tr id="md{code}" onclick="AffCard('code','{deck_count}','','')">
      td[0] = card name (L14)
      td[1] = "53.1 %" percentage (L14 align=center)
      td[2] = "4.0" avg copies (L14 align=center)
    Deck count is in onclick second param, not a td column.

    Returns {card_name: {card_code, decks, pct, avg}}.
    """
    meta_id = YEAR_META[year]
    url = f"{BASE_URL}/topcards"
    cards = {}
    page = 1

    while True:
        data = {
            "metagame_sel[LE]": meta_id,
            "format": "LE",
            "maindeck": zone,  # "MD" or "SB"
            "current_page": str(page),
            "data": "1",
        }
        r = post(url, data=data)
        soup = BeautifulSoup(r.text, "html.parser")

        rows = soup.find_all("tr", id=re.compile(r"^md"))
        if not rows:
            break

        for row in rows:
            card_code = row["id"][2:]  # strip leading "md"

            name_td = row.find("td", class_="L14")
            if not name_td:
                continue
            card_name = name_td.get_text(strip=True)
            if not card_name:
                card_name = card_code

            tds = row.find_all("td")
            if len(tds) < 3:
                continue

            try:
                onclick = row.get("onclick", "")
                decks_m = re.search(r"AffCard\('[^']*','(\d+)'", onclick)
                decks = int(decks_m.group(1)) if decks_m else 0

                pct_raw = tds[1].get_text(strip=True).replace("%", "").strip()
                pct = float(pct_raw) if pct_raw else 0.0
                avg_raw = tds[2].get_text(strip=True)
                avg = float(avg_raw) if avg_raw else 0.0
            except (ValueError, IndexError):
                continue

            cards[card_name] = {"card_code": card_code, "decks": decks, "pct": pct, "avg": avg}

        page += 1

    return cards


def fetch_topcards(years: list[int] | None = None) -> None:
    """Fetch flat card frequency for all years and both zones."""
    years = years or list(YEAR_META.keys())
    for year in years:
        for zone in ("MD", "SB"):
            out = RAW_DIR / f"topcards_{year}_{zone}.json"
            if load_cache(out) is not None:
                print(f"  topcards {year} {zone}: cache hit, skipping")
                continue
            print(f"  topcards {year} {zone}: fetching...")
            cards = fetch_topcards_page(year, zone)
            save_cache(out, {"year": year, "zone": zone, "cards": cards})
            print(f"  topcards {year} {zone}: {len(cards)} cards → {out}")


# ---------------------------------------------------------------------------
# Job 3: Event enumeration + event metadata
# ---------------------------------------------------------------------------

def parse_event_listing_page(html: str) -> tuple[list[int], bool]:
    """Parse one page of the format event listing.

    Returns (event_ids, has_next_page).
    """
    soup = BeautifulSoup(html, "html.parser")

    # Event links: href="event?e={id}&f=LE"
    event_ids = set()
    for a in soup.find_all("a", href=re.compile(r"event\?e=\d+&f=LE")):
        m = re.search(r"e=(\d+)", a["href"])
        if m:
            event_ids.add(int(m.group(1)))

    # Pagination: look for a "Next" nav link that isn't disabled
    has_next = bool(soup.find("a", class_="Nav_norm", string=re.compile(r"Next")))

    return sorted(event_ids), has_next


def parse_event_page(html: str, event_id: int) -> dict:
    """Parse an event page for metadata and deck list.

    Returns dict with: event_name, date_str, player_count, star_count,
                       decks [{placement, deck_id, archetype_name}]
    """
    soup = BeautifulSoup(html, "html.parser")

    # Event name: first event_title div (not the ones with # placements)
    event_name = ""
    for div in soup.find_all("div", class_="event_title"):
        text = div.get_text(strip=True)
        if text and not text.startswith("#") and "→" not in text and "←" not in text:
            event_name = text
            break

    # Date + player count: "N players - DD/MM/YY"
    player_count = 0
    date_str = ""
    player_date_div = soup.find(string=re.compile(r"\d+ players - \d{2}/\d{2}/\d{2}"))
    if player_date_div:
        m = re.match(r"(\d+) players - (\d{2}/\d{2}/\d{2})", player_date_div.strip())
        if m:
            player_count = int(m.group(1))
            date_str = m.group(2)

    # Star count: count star.png occurrences inside the meta_arch div
    star_count = 0
    meta_div = soup.find("div", class_="meta_arch")
    if meta_div:
        star_count = len(meta_div.find_all("img", src=re.compile(r"star\.png")))

    # Deck placements: numbered event_title divs like "#4 Archetype - Player"
    # and deck links href="?e={eid}&d={did}&f=LE"
    decks = []
    placement_divs = [
        d for d in soup.find_all("div", class_="event_title")
        if d.get_text(strip=True).startswith("#")
    ]
    # Also collect deck IDs + archetype names from the placement table
    # Structure: <div class=S14>N</div> placement, <div class=S14>archetype link</div>
    placement = 1
    for a in soup.find_all("a", href=re.compile(rf"e={event_id}&d=\d+&f=LE")):
        m = re.search(r"d=(\d+)", a["href"])
        if not m:
            continue
        deck_id = int(m.group(1))
        archetype_name = a.get_text(strip=True)
        # Placement comes from sibling div with a number
        parent = a.find_parent("div", class_="S14")
        if parent:
            prev = parent.find_previous_sibling("div")
            if prev and prev.get_text(strip=True).isdigit():
                placement = int(prev.get_text(strip=True))
        decks.append({
            "placement": placement,
            "deck_id": deck_id,
            "archetype_name": archetype_name,
        })
        placement += 1

    # Deduplicate deck_ids (same deck may link multiple times)
    seen = set()
    unique_decks = []
    for d in decks:
        if d["deck_id"] not in seen:
            seen.add(d["deck_id"])
            unique_decks.append(d)

    return {
        "event_id": event_id,
        "event_name": event_name,
        "date_str": date_str,
        "player_count": player_count,
        "star_count": star_count,
        "decks": unique_decks,
    }


def fetch_events(years: list[int] | None = None) -> None:
    """Enumerate all Legacy events for each year and scrape event metadata."""
    years = years or list(YEAR_META.keys())

    for year in years:
        events_out = RAW_DIR / f"events_{year}.json"
        if load_cache(events_out) is not None:
            print(f"  events {year}: cache hit, skipping")
            continue

        print(f"  events {year}: enumerating pages...")
        meta_id = YEAR_META[year]
        all_event_ids: set[int] = set()
        page = 1

        while True:
            url = f"{BASE_URL}/format"
            params = {"f": "LE", "meta": meta_id, "cp": page}
            r = get(url, params=params)
            ids, has_next = parse_event_listing_page(r.text)
            all_event_ids.update(ids)
            print(f"    page {page}: {len(ids)} event IDs (total so far: {len(all_event_ids)})")
            if not has_next:
                break
            page += 1

        print(f"  events {year}: scraping {len(all_event_ids)} event pages...")
        events = []
        for i, eid in enumerate(sorted(all_event_ids), 1):
            event_cache = RAW_DIR / f"event_{eid}.json"
            if load_cache(event_cache) is not None:
                cached = load_cache(event_cache)
                events.append(cached)
                continue

            r = get(f"{BASE_URL}/event", params={"e": eid, "f": "LE"})
            event_data = parse_event_page(r.text, eid)
            save_cache(event_cache, event_data)
            events.append(event_data)

            if i % 50 == 0:
                print(f"    {i}/{len(all_event_ids)} events scraped")

        save_cache(events_out, events)
        n_decks = sum(len(e["decks"]) for e in events)
        print(f"  events {year}: {len(events)} events, {n_decks} deck refs → {events_out}")


# ---------------------------------------------------------------------------
# Job 4: Deck card lists
# ---------------------------------------------------------------------------

def parse_deck_page(html: str, deck_id: int) -> dict:
    """Parse a deck page for its card list.

    Returns {deck_id, mainboard: [{card_name, quantity}], sideboard: [{card_name, quantity}]}
    Card names come from AffCard onclick: AffCard('code','Card Name','','')
    Zone comes from div ID prefix: md = mainboard, sb = sideboard.
    """
    soup = BeautifulSoup(html, "html.parser")

    mainboard = []
    sideboard = []

    for div in soup.find_all("div", id=re.compile(r"^(md|sb)")):
        zone = "mainboard" if div["id"].startswith("md") else "sideboard"

        # Card name from onclick: AffCard('code','Card+Name','','')
        # Apostrophes in card names are JS-escaped as \' — use (?:[^'\\]|\\.)+ to
        # match through escaped quotes, then unescape \' → '
        onclick = div.get("onclick", "")
        m = re.search(r"AffCard\('[^']*','((?:[^'\\]|\\.)+)'", onclick)
        if not m:
            continue
        card_name = m.group(1).replace("\\'", "'").replace("+", " ")

        # Quantity from text node before the <span class=L14>
        text = div.get_text(separator=" ", strip=True)
        qty_m = re.match(r"^(\d+)", text)
        if not qty_m:
            continue
        quantity = int(qty_m.group(1))

        entry = {"card_name": card_name, "quantity": quantity}
        if zone == "mainboard":
            mainboard.append(entry)
        else:
            sideboard.append(entry)

    return {"deck_id": deck_id, "mainboard": mainboard, "sideboard": sideboard}


def fetch_decks(years: list[int] | None = None) -> None:
    """Fetch card lists for all decks found in the event cache."""
    years = years or list(YEAR_META.keys())

    # Collect all deck IDs from event caches
    all_deck_ids: set[int] = set()
    for year in years:
        events_cache = RAW_DIR / f"events_{year}.json"
        events = load_cache(events_cache)
        if not events:
            print(f"  decks: no events cache for {year}, run --events-only first")
            continue
        for event in events:
            for d in event.get("decks", []):
                all_deck_ids.add(d["deck_id"])

    already_cached = sum(1 for did in all_deck_ids if (RAW_DIR / f"deck_{did}.json").exists())
    to_fetch = sorted(all_deck_ids - {did for did in all_deck_ids if (RAW_DIR / f"deck_{did}.json").exists()})
    print(f"  decks: {len(all_deck_ids)} total, {already_cached} cached, {len(to_fetch)} to fetch")

    for i, deck_id in enumerate(to_fetch, 1):
        r = get(f"{BASE_URL}/event", params={"d": deck_id, "f": "LE"})
        deck_data = parse_deck_page(r.text, deck_id)
        save_cache(RAW_DIR / f"deck_{deck_id}.json", deck_data)
        if i % 100 == 0:
            print(f"    {i}/{len(to_fetch)} decks fetched")

    print(f"  decks: done ({len(all_deck_ids)} total deck files in cache)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Fetch MTG Legacy tournament data")
    parser.add_argument("--banlist-only",  action="store_true")
    parser.add_argument("--topcards-only", action="store_true")
    parser.add_argument("--events-only",   action="store_true")
    parser.add_argument("--decks-only",    action="store_true")
    parser.add_argument("--years", nargs="+", type=int, help="e.g. --years 2024 2025")
    args = parser.parse_args()

    years = args.years or None
    run_all = not any([args.banlist_only, args.topcards_only, args.events_only, args.decks_only])

    if run_all or args.banlist_only:
        print("\n[1/4] Banlist")
        fetch_banlist()

    if run_all or args.topcards_only:
        print("\n[2/4] Topcards (flat card frequency)")
        fetch_topcards(years)

    if run_all or args.events_only:
        print("\n[3/4] Events")
        fetch_events(years)

    if run_all or args.decks_only:
        print("\n[4/4] Decks")
        fetch_decks(years)

    print("\nDone.")


if __name__ == "__main__":
    main()
