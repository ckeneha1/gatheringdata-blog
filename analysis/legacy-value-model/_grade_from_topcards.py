"""Reproduce the Marvel Super Heroes Legacy adoption grade from the 2026 topcards scrape.

  uv run python _grade_from_topcards.py [path/to/marvel_spoiler.json]

Reads mtg-legacy-tournament/data/raw/topcards_2026_{MD,SB}.json (pct = % of 2026 Legacy
decks playing each card) and a Marvel spoiler (default msh.json) to exclude reprints — since
a reprint of an already-Legacy-legal card is not a new-adoption event. Prints every NEW
Marvel card seeing play, so the per-card grade and the recall audit are reproducible.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "mtg-legacy-tournament" / "data" / "raw"
spoiler = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "msh.json"

md = json.load(open(RAW / "topcards_2026_MD.json"))["cards"]
sb = json.load(open(RAW / "topcards_2026_SB.json"))["cards"]

new = set()
for c in json.load(open(spoiler)):
    if c.get("reprint"):
        continue
    new.add(c["name"])
    if " // " in c["name"]:
        new.add(c["name"].split(" // ")[0])

peak = {}
for zone, data in (("MD", md), ("SB", sb)):
    for nm, v in data.items():
        if nm in new and (nm not in peak or v["pct"] > peak[nm][0]):
            peak[nm] = (v["pct"], zone, v["decks"])

rows = sorted(((p, z, nm, d) for nm, (p, z, d) in peak.items()), reverse=True)
print(f"NEW (non-reprint) Marvel cards in 2026 Legacy (>=0.1% of decks):")
for p, z, nm, d in rows:
    if p >= 0.1:
        print(f"  {p:5.2f}% {z}  {nm} ({d} decks)")
