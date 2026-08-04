"""_triage_extract.py — build the sentiment-free blind-triage input (Gate 2 follow-up).

Reads the fetched set JSON (msh.json), keeps genuinely-NEW (non-reprint)
Legacy-legal cards, and writes a card-facts-only markdown for a BLIND evaluator.
No verdicts, no community data, no scores — facts only. We feed ALL new cheap/
land/screen-flagged cards (not just the screen's output) so the screen's known
recall bug cannot propagate into the recall safety-check.
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from spoiler_screen import screen_set, EXCLUDED_LAYOUTS  # noqa: E402

# Generalized: `_triage_extract.py [set.json] [out.md] [--prerelease]` (defaults msh.json →
# triage_input.md), so the blind-triage input reruns on any fetched set with no code edits.
# --prerelease: the set isn't out yet, so Scryfall still marks its cards legacy:not_legal;
# accept everything not explicitly banned (a new Standard/eternal set is Legacy-legal on release).
PRERELEASE = "--prerelease" in sys.argv
ALL = "--all" in sys.argv  # sweep EVERY new card, not just the cmc<=4/land/screen-flagged subset
_args = [a for a in sys.argv[1:] if not a.startswith("--")]
in_path = Path(_args[0]) if len(_args) > 0 else HERE / "msh.json"
out_path = Path(_args[1]) if len(_args) > 1 else HERE / "triage_input.md"
cards = json.loads(in_path.read_text())


def cmc(c):
    return float(c.get("cmc") or 0.0)


def is_land(c):
    tl = c.get("type_line", "") or ""
    return "Land" in tl and "Artifact" not in tl


def mana_cost(c):
    if c.get("mana_cost"):
        return c["mana_cost"]
    faces = c.get("card_faces")
    if faces:
        return " // ".join(f.get("mana_cost", "") or "" for f in faces)
    return ""


def faces_text(c):
    if c.get("oracle_text"):
        return c["oracle_text"]
    faces = c.get("card_faces")
    if faces:
        return "\n//\n".join(f.get("oracle_text", "") or "" for f in faces)
    return ""


def pt(c):
    if c.get("power") is not None:
        return f" • {c.get('power')}/{c.get('toughness')}"
    faces = c.get("card_faces") or []
    if faces and faces[0].get("power") is not None:
        return " • " + " // ".join(
            f"{f.get('power','?')}/{f.get('toughness','?')}" for f in faces)
    return ""


# new + legacy-legal + not a token/emblem layout.
# NOTE: `reprint == false` ("first-ever printing") is the correct "new card" test
# ONLY for ETERNAL formats, where the legal pool is monotonic — a reprint of an
# already-legal card is not a new adoption event. In ROTATING formats (Standard),
# a reprint re-enters the pool and IS a new event, so this filter must become a
# format-relative pool delta. See legacy-framework/open_questions.md.
def _legacy_ok(c):
    lg = (c.get("legalities") or {}).get("legacy")
    return lg != "banned" if PRERELEASE else lg == "legal"


new_legal = [
    c for c in cards
    if not c.get("reprint")
    and c.get("layout") not in EXCLUDED_LAYOUTS
    and _legacy_ok(c)
]

# names the screen flagged (front face too) — include regardless of cmc
screen_names = set()
for cand in screen_set(cards):
    screen_names.add(cand.name.lower())
    screen_names.add(cand.name.split(" // ")[0].lower())


def keep(c):
    nm = (c.get("name", "") or "").lower()
    return cmc(c) <= 4 or is_land(c) or nm in screen_names or nm.split(" // ")[0] in screen_names


triage = sorted((c for c in new_legal if (ALL or keep(c))), key=lambda c: (cmc(c), c.get("name", "")))

# stats
buckets = Counter(min(int(cmc(c)), 6) for c in new_legal)
print(f"total cards in {in_path.name}: {len(cards)}")
print(f"new (non-reprint) Legacy-legal, non-token: {len(new_legal)}")
print("  by cmc: " + ", ".join(
    f"{('5+' if k >= 5 else k)}:{buckets[k]}" for k in sorted(buckets)))
print(f"  lands among them: {sum(1 for c in new_legal if is_land(c))}")
print(f"triage subset (cmc<=4 OR land OR screen-flagged): {len(triage)}")

# write facts-only file
out_lines = [
    f"# Blind triage input — NEW cards from {in_path.stem} (facts only)",
    "",
    "Card facts only. No verdicts, no community sentiment, no scores. Evaluate "
    "each against the framework files and the field snapshot you were given.",
    "",
]
for c in triage:
    kw = ", ".join(c.get("keywords") or [])
    head = f"- {mana_cost(c) or '—'} • {c.get('type_line','')}{pt(c)}"
    if kw:
        head += f" • kw: {kw}"
    out_lines += [f"## {c.get('name','')}", head,
                  f"- {faces_text(c).strip() or '(no rules text)'}", ""]

out = out_path
out.write_text("\n".join(out_lines))
print(f"wrote {out} ({len(triage)} cards)")
