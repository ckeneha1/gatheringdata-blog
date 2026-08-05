"""Build the candidate JSON for the Hobbit model predictions (Phase 2, next set).

Same shape as _build_msh_candidates.py: candidate card data from the spoiler snapshot
hobbit.json; incumbent (existing-card) data from the Scryfall oracle cache. Candidate
list = the union of the blind framework shortlist (hobbit-triage-verdicts.md) and the
held-out community picks (community-consensus-hobbit.md). Incumbents are named from the
framework's slot analysis, so all four predictors share the slot definition.

  uv run python _build_hobbit_candidates.py   ->  hobbit_candidates.json
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOB = json.load(open(HERE / "hobbit.json"))
ORACLE_PATH = next((HERE.parent / "mtg-card-power" / ".cache").glob("oracle_cards--*.json"))
ORACLE = json.load(open(ORACLE_PATH))

# Current post-Marvel Legacy field (field_concentration = top share).
FIELD_TOP = ("Dimir Tempo:0.125|Fantasticar:0.063|Izzet Cutter:0.060|Sneak and Show:0.058|"
             "Cloudpost:0.054|UWx Control:0.047|Doomsday:0.040|Boros Aggro:0.040|"
             "Eldrazi:0.037|Lands:0.034")

# (display, hobbit.json match needle, archetype, [incumbents from the framework slot read])
CANDS = [
    ("Riddles in the Dark", "Riddles in the Dark", "Dimir/delve control", ["Fact or Fiction"]),
    ("Bilbo, Thief in the Night", "Bilbo, Thief in the Night", "Izzet DRC / graveyard tempo",
     ["Dragon's Rage Channeler"]),
    ("Gandalf, Goblins' Bane", "Gandalf, Goblins' Bane", "Storm / spellslinger",
     ["Young Pyromancer"]),
    ("Gollum, Riddle Master", "Gollum, Riddle Master", "Mono-black midrange", ["Dark Confidant"]),
    ("An Unexpected Party", "An Unexpected Party", "Boros go-wide", []),
    ("Plunder the Trollshaws", "Plunder the Trollshaws", "cantrip slot", ["Brainstorm"]),
    ("Confusticate and Bebother", "Confusticate and Bebother", "control counter", ["Counterspell"]),
    ("My Precious // Allure of Power", "My Precious", "aristocrats card draw", ["Night's Whisper"]),
    ("Most Decrepit Old Bird // Speak Secrets", "Most Decrepit Old Bird", "delve / graveyard fuel",
     ["Brainstorm"]),
    ("Bilbo's Deadly Slice", "Bilbo's Deadly Slice", "removal", ["Fatal Push"]),
]

hob_by_name = {c["name"]: c for c in HOB}
oracle_by_name = {}
for c in ORACLE:
    oracle_by_name.setdefault(c["name"], c)


def front(c):
    if c.get("card_faces"):
        f = c["card_faces"][0]
        return (f.get("oracle_text", "") or "", f.get("keywords", []) or [], c.get("cmc", 0) or 0)
    return (c.get("oracle_text", "") or "", c.get("keywords", []) or [], c.get("cmc", 0) or 0)


def find_hob(needle):
    if needle in hob_by_name:
        return hob_by_name[needle]
    hits = [n for n in hob_by_name if needle.lower() in n.lower()]
    return hob_by_name[hits[0]] if hits else None


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
    card = find_hob(needle)
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

(HERE / "hobbit_candidates.json").write_text(json.dumps(out, indent=2))
print(f"\nWROTE hobbit_candidates.json ({len(out)}/{len(CANDS)} candidates)")
