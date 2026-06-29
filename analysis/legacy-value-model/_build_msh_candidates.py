"""Build the candidate JSON for Phase 2 model predictions on Marvel Super Heroes.

Per brief Phase 2: run the trained value model on the SAME 16 registered candidates.
Incumbents are named from the registered (locked) framework verdicts
(framework-verdicts-msh.md) — inferred-cluster incumbents (needs Gate 3) aren't
built yet, so this is the documented fallback; baseline/framework/model thus share
the same slot definition and differ only in HOW they judge "beats the incumbent".

Candidate card data: spoiler snapshot msh.json. Incumbent data: Scryfall oracle
cache. DFCs use the FRONT face (text + face keywords), as the framework evaluated.

  uv run python _build_msh_candidates.py   ->  msh_candidates.json
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MSH = json.load(open(HERE / "msh.json"))
ORACLE_PATH = next((HERE.parent / "mtg-card-power" / ".cache").glob("oracle_cards--*.json"))
ORACLE = json.load(open(ORACLE_PATH))

# Representative June 2026 field snapshot; field_concentration() uses the max share.
FIELD_TOP = ("Izzet Delver:0.107|Dimir Tempo:0.089|Sneak and Show:0.069|Tron:0.059|"
             "Lands:0.051|Reanimator:0.049|Doomsday:0.039|Eldrazi:0.039|"
             "UWx Control:0.030|Death and Taxes:0.027")

# (display name, msh.json match needle, archetype, [incumbents from framework verdicts])
CANDS = [
    ("The Fantasticar", "Fantasticar", "8-Cast/Affinity",
     ["Kappa Cannoneer", "Patchwork Automaton", "Thought Monitor"]),
    ("Namor the Sub-Mariner", "Namor the Sub-Mariner", "Merfolk",
     ["Svyelun of Sea and Sky", "Vodalian Hexcatcher"]),
    ("Attuma, Atlantean Warlord", "Attuma, Atlantean Warlord", "Merfolk",
     ["Svyelun of Sea and Sky", "Vodalian Hexcatcher"]),
    ("King T'Challa // Black Panther", "King T'Challa", "UWx/blue midrange",
     ["Faerie Mastermind"]),
    ("Mole Man, Moloid Master", "Mole Man, Moloid Master", "Lands",
     ["Crucible of Worlds", "Life from the Loam"]),
    ("Hex Magic", "Hex Magic", "Red refill",
     ["Echo of Eons", "Wheel of Fortune"]),
    ("Avengers Disassembled", "Avengers Disassembled", "Red sideboard",
     ["Fiery Confluence", "Pyroclasm"]),
    ("World War Hulk", "World War Hulk", "Cheat-into-play",
     ["Natural Order", "Show and Tell", "Sneak Attack"]),
    ("Mjölnir, Hammer of Thor", "Hammer of Thor", "Stoneforge packages",
     ["Kaldra Compleat", "Umezawa's Jitte"]),
    ("Hawkeye's Bow", "Hawkeye's Bow", "(no slot)", []),
    ("Elektra, Daughter of the Hand", "Elektra, Daughter of the Hand", "Ninjas/Dimir",
     ["Murktide Regent", "Fatal Push"]),
    ("Thanos, the Mad Titan", "Thanos, the Mad Titan", "(no slot)", []),
    ("Cosmic Cube", "Cosmic Cube", "Eldrazi/Tron",
     ["Karn, the Great Creator"]),
    ("The Coming of Galactus", "The Coming of Galactus", "(no slot)", []),
    ("Jennifer Walters // The Sensational She-Hulk", "Jennifer Walters", "Combo protection/D&T",
     ["Teferi, Time Raveler", "Thalia, Guardian of Thraben"]),
    ("Doctor Doom, Unrivaled", "Doctor Doom, Unrivaled", "Doomsday combo",
     ["Thassa's Oracle", "Jace, Wielder of Mysteries"]),
]

msh_by_name = {c["name"]: c for c in MSH}
oracle_by_name = {}
for c in ORACLE:
    oracle_by_name.setdefault(c["name"], c)


def front(c):
    if c.get("card_faces"):
        f = c["card_faces"][0]
        return (f.get("oracle_text", "") or "", f.get("keywords", []) or [], c.get("cmc", 0) or 0)
    return (c.get("oracle_text", "") or "", c.get("keywords", []) or [], c.get("cmc", 0) or 0)


def find_msh(needle):
    if needle in msh_by_name:
        return msh_by_name[needle]
    hits = [n for n in msh_by_name if needle.lower() in n.lower()]
    return msh_by_name[hits[0]] if hits else None


def find_oracle(name):
    if name in oracle_by_name:
        return oracle_by_name[name]
    low = {n.lower(): c for n, c in oracle_by_name.items()}
    if name.lower() in low:
        return low[name.lower()]
    hits = [c for n, c in oracle_by_name.items() if n.lower().split(" // ")[0] == name.lower()]
    return hits[0] if hits else None


out = []
for disp, needle, arch, incs in CANDS:
    card = find_msh(needle)
    if not card:
        print("MISSING candidate:", disp); continue
    ot, kw, cmc = front(card)
    inc_objs = []
    for iname in incs:
        ic = find_oracle(iname)
        if not ic:
            print(f"  MISSING incumbent for {disp}: {iname!r}"); continue
        iot, ikw, icmc = front(ic)
        inc_objs.append({"name": ic["name"], "oracle_text": iot, "keywords": ikw, "cmc": icmc})
    out.append({"name": disp, "archetype": arch, "oracle_text": ot, "keywords": kw,
                "cmc": cmc, "field_top": FIELD_TOP, "incumbents": inc_objs})
    print(f"{disp:44.44} cmc={cmc:<4} kw={len(kw)} incumbents={len(inc_objs)}/{len(incs)}")

(HERE / "msh_candidates.json").write_text(json.dumps(out, indent=2))
print(f"\nWROTE msh_candidates.json ({len(out)}/16 candidates)")
