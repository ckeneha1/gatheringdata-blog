"""
fetch_spoiler.py — pull a set's eternal-legal cards from the Scryfall search API
and save a set JSON for spoiler_screen.py.

Network step for Phase 0 Gate 2. Requires api.scryfall.com egress (the Domain
allowlist must include it AND the container must have been created after it was
added — egress policy is fixed at container start). Run in a session that has
that access.

The pagination/accumulation/dedup logic is factored into pure functions
(`accumulate_pages`, `dedup_by_oracle_id`) that are unit-tested with fixtures;
only `fetch_set` touches the network.

Usage:
    uv run python fetch_spoiler.py --query "set:msh or set:msc" --out msh.json
    # then:
    uv run python spoiler_screen.py screen --set-json msh.json
    uv run python spoiler_screen.py audit  --set-json msh.json \
        --community ../legacy-framework/predictions/candidates-msh.md
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SCRYFALL_SEARCH = "https://api.scryfall.com/cards/search"
RATE_LIMIT_S = 0.1  # Scryfall asks for 50–100ms between requests
USER_AGENT = "gatheringdata-blog-research/1.0 (spoiler screen)"


def accumulate_pages(pages: list[dict]) -> list[dict]:
    """Flatten Scryfall search pages ({data:[...], has_more, next_page}) into
    one card list. Pure — takes already-fetched page dicts."""
    cards: list[dict] = []
    for page in pages:
        if not isinstance(page, dict) or "data" not in page:
            raise ValueError("each page must be a Scryfall search response with a 'data' array")
        cards.extend(page["data"])
    return cards


def dedup_by_oracle_id(cards: list[dict]) -> list[dict]:
    """One entry per oracle_id (a set lists alt-art/variant printings of the
    same card); keep the first. Cards lacking oracle_id (rare) are kept as-is."""
    seen: set[str] = set()
    out: list[dict] = []
    for c in cards:
        oid = c.get("oracle_id")
        if oid is None:
            out.append(c)
            continue
        if oid in seen:
            continue
        seen.add(oid)
        out.append(c)
    return out


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_set(query: str, *, unique: str = "cards", include_extras: bool = True) -> list[dict]:
    """Fetch all pages of a Scryfall search. Network only here."""
    params = {"q": query, "unique": unique,
              "include_extras": "true" if include_extras else "false"}
    url = f"{SCRYFALL_SEARCH}?{urllib.parse.urlencode(params)}"
    pages: list[dict] = []
    while url:
        page = _get_json(url)
        pages.append(page)
        print(f"  fetched {len(page.get('data', []))} cards "
              f"(total so far {sum(len(p.get('data', [])) for p in pages)})")
        url = page.get("next_page") if page.get("has_more") else None
        if url:
            time.sleep(RATE_LIMIT_S)
    return dedup_by_oracle_id(accumulate_pages(pages))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--query", default="set:msh or set:msc",
                        help="Scryfall search query (default: MSH main + MSC commander)")
    parser.add_argument("--out", type=Path, required=True, help="output JSON path")
    parser.add_argument("--unique", default="cards", choices=["cards", "prints", "art"])
    args = parser.parse_args(argv)

    try:
        cards = fetch_set(args.query, unique=args.unique)
    except Exception as e:  # noqa: BLE001 — surface the egress/network cause clearly
        raise SystemExit(
            f"ERROR fetching from Scryfall: {e}\n"
            "If this is a 403 'Host not in allowlist', the running container's "
            "egress policy predates the allowlist edit — start a fresh session "
            "after adding api.scryfall.com, then re-run."
        )
    args.out.write_text(json.dumps(cards, indent=2))
    print(f"Saved {len(cards)} unique cards → {args.out}")


if __name__ == "__main__":
    main()
