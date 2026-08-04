"""
spoiler_screen.py — empirical candidate generation for a new set (Phase 0.3).

The brief (§0.3, corrected 2026-06-12) requires that the Legacy candidate
shortlist be generated EMPIRICALLY from card text — never seeded from
community attention, which caps recall and can't scale to formats nobody
follows. This module is that generator: it ingests a full set, maps each
eternal-legal card to the 14-signal value taxonomy using the Post 2 ability
features + cost rules, scores Legacy plausibility (signal mix weighted by the
historical win-log-OR priors, with the format's strong cheap-card bias), and
emits a ranked candidate list.

It is a RECALL tool, not a verdict. Its output feeds the blind framework
evaluation and the value model. Its `--audit` mode compares the screen's
candidates against a community list and reports MISSES — every community card
the screen failed to surface is a screen defect to fix, never a reason to
import community recall (brief §0.3).

Signal mapping is deliberately rule-based and inspectable. Lands (no CMC) are
handled on their own track (mana_denial / resilience / fixing matter; the
cheap-card bias doesn't apply).

Inputs:
  - A set's cards as Scryfall card dicts. CLI reads a JSON file
    (list of dicts, e.g. saved from the Scryfall search API
    `cards/search?q=set:msh+OR+set:msc`); the core takes the list directly so
    it is unit-testable without network or the gitignored bulk cache.

Usage:
    uv run python spoiler_screen.py screen --set-json msh.json --top 30
    uv run python spoiler_screen.py audit  --set-json msh.json \
        --community ../legacy-framework/predictions/candidates-msh.md
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path

_ANALYSIS_DIR = Path(__file__).resolve().parent.parent
if str(_ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(_ANALYSIS_DIR))

from shared.ability_features import (  # noqa: E402
    card_feature_set, strip_reminder_text,
)

# 14-signal taxonomy (mirrors mtg-primers/extract.py VALUE_SIGNALS).
VALUE_SIGNALS = [
    "free_spell", "mana_denial", "mana_acceleration", "cantrip", "tutor",
    "combo_piece", "lock_piece", "graveyard", "resilience", "protection",
    "hate_piece", "card_advantage", "tempo", "archetype_synergy",
]

# Historical mean win-log-OR by signal (evaluation.md Q1) — used as plausibility
# weights. A card firing high-prior signals is more likely Legacy-relevant.
SIGNAL_PRIOR = {
    "lock_piece": 0.122, "card_advantage": 0.081, "cantrip": 0.078,
    "mana_denial": 0.064, "tempo": 0.064, "tutor": 0.063,
    "archetype_synergy": 0.054, "protection": 0.050, "resilience": 0.048,
    "hate_piece": 0.027, "mana_acceleration": 0.007, "graveyard": -0.004,
    "free_spell": -0.007, "combo_piece": -0.040,
}
# free_spell's negative *average* hides that free interaction (FoW/Daze) is
# format-defining; treat its PRESENCE as a strong plausibility flag regardless
# of the noisy mean. Same for combo_piece (high variance). These get a floor.
SIGNAL_FLOOR = {"free_spell": 0.10, "combo_piece": 0.05}

EXCLUDED_LAYOUTS = {"token", "emblem", "art_series", "reversible_card", "double_faced_token"}


# ---------------------------------------------------------------------------
# Card view
# ---------------------------------------------------------------------------

@dataclass
class ScreenCard:
    name: str
    cmc: float
    type_line: str
    oracle_text: str
    keywords: list[str]
    is_land: bool
    set_code: str

    @classmethod
    def from_scryfall(cls, card: dict) -> "ScreenCard | None":
        if card.get("layout") in EXCLUDED_LAYOUTS:
            return None
        name = card.get("name")
        if not name:
            return None
        type_line = card.get("type_line", "") or ""
        mana_cost = card.get("mana_cost", "")
        oracle = card.get("oracle_text", "") or ""
        faces = card.get("card_faces")
        if faces:  # DFC/split — use the front face for cost, join text for detection
            front = faces[0]
            if not mana_cost:
                mana_cost = front.get("mana_cost", "") or ""
            if not oracle:
                oracle = "\n".join(f.get("oracle_text", "") or "" for f in faces)
        is_land = "Land" in type_line and "Artifact" not in type_line
        return cls(
            name=name,
            cmc=float(card.get("cmc") or card.get("mana_value") or 0.0),
            type_line=type_line,
            oracle_text=oracle,
            keywords=card.get("keywords") or [],
            is_land=is_land,
            set_code=(card.get("set") or "").lower(),
        )


# ---------------------------------------------------------------------------
# Signal detection (rule-based, inspectable)
# ---------------------------------------------------------------------------

_ALT_COST = re.compile(
    r"without paying its mana cost|without paying their mana cost|"
    r"rather than pay (?:this spell's mana cost|its mana cost)|"
    r"you may (?:exile|pay) .{0,40}rather than pay|"
    r"you may cast this spell.{0,30}(?:by|if)|"
    r"\bif you control|alternative cost|"
    r"\bpitch\b", re.I)
_FREE_KEYWORDS = {"convoke", "delve", "affinity", "improvise", "foretell", "evoke",
                  "emerge", "cascade", "suspend"}
_LAND_DENIAL = re.compile(
    r"destroy target (?:\w+ ){0,3}land|return target (?:\w+ ){0,3}land|"
    r"each opponent.{0,20}sacrifices? a land|"
    r"lands? .{0,20}(?:don't|doesn't|can't) untap|tap target land", re.I)
_LOCK = re.compile(
    r"(?:players?|opponents?|each player|your opponents) (?:can't|cannot)|"
    r"spells? cost .{0,20} more|"
    r"(?:can't|cannot) (?:cast|activate|attack|untap|search)|"
    r"don't untap during|"
    r"\bcost(?:s)? \{?\d+\}? .{0,12} more", re.I)
_HATE = re.compile(
    r"exile .{0,40}graveyard|graveyard.{0,20}(?:can't|exile)|"
    r"opponents? control|each opponent|target opponent.{0,30}(?:sacrifices?|discards?|exile)|"
    r"artifacts? and enchantments?|nonbasic lands?", re.I)
_TUTOR = re.compile(r"search your library for", re.I)
_DRAW = re.compile(r"draw (?:a|one|two|three|\d+|x) cards?", re.I)
_SELECT = re.compile(r"\bscry \d+|\bsurveil \d+|look at the top \d+|put .{0,30} on (?:the )?bottom", re.I)
_TOKENS_TRIBAL = re.compile(r"creatures? you control get|other .{0,20} you control get|"
                            r"\blandfall\b", re.I)
_RAMP = re.compile(r"add \{[^}]+\}|adds? .{0,20}mana", re.I)
_RECUR = re.compile(r"return .{0,40}from .{0,20}graveyard|from your graveyard|"
                    r"\bflashback\b|\bescape\b|\bunearth\b|\bdisturb\b", re.I)


def detect_signals(card: ScreenCard) -> set[str]:
    """Map a card to the value signals it plausibly serves."""
    text = strip_reminder_text(card.oracle_text or "")
    low = text.lower()
    kw = {k.lower() for k in card.keywords}
    feats = card_feature_set(card.oracle_text, card.keywords, card.is_land)
    cats = {f[len("cat:"):] for f in feats if f.startswith("cat:")}
    sigs: set[str] = set()

    # free_spell — alternative/zero casting cost
    if _ALT_COST.search(low) or (_FREE_KEYWORDS & kw) or card.cmc == 0 and not card.is_land:
        sigs.add("free_spell")
    # mana denial (incl. lands like Wasteland)
    if _LAND_DENIAL.search(low) or ("stax" in cats and "land" in low):
        sigs.add("mana_denial")
    # acceleration
    if "ramp" in cats or _RAMP.search(low):
        sigs.add("mana_acceleration")
    # cantrip vs raw card advantage (cantrip = cheap + replaces itself)
    if "card_advantage" in cats or _DRAW.search(low) or _SELECT.search(low):
        if card.cmc <= 2 and not card.is_land:
            sigs.add("cantrip")
        sigs.add("card_advantage")
    # tutor
    if "tutor" in cats or _TUTOR.search(low):
        sigs.add("tutor")
    # lock piece
    if "stax" in cats or _LOCK.search(low):
        sigs.add("lock_piece")
    # graveyard
    if "graveyard" in cats or _RECUR.search(low):
        sigs.add("graveyard")
    # resilience
    if kw & {"indestructible", "hexproof", "ward", "protection", "shroud"} or \
            re.search(r"can't be (?:countered|targeted|destroyed)|regenerate", low):
        sigs.add("resilience")
    # protection of own pieces
    if "protection" in cats or kw & {"protection", "hexproof", "ward"} or \
            re.search(r"prevent .{0,20}damage|hexproof|can't be the target", low):
        sigs.add("protection")
    # counterspell / free interaction → tempo + (often) free_spell already
    if "counterspell" in cats or re.search(r"counter target", low):
        sigs.add("tempo")
    # tempo (cheap evasive/bounce threats)
    if card.cmc <= 2 and (kw & {"flying", "flash", "haste"} or
                          re.search(r"return target .{0,30}to .{0,15}hand", low)):
        sigs.add("tempo")
    # hate piece
    if _HATE.search(low):
        sigs.add("hate_piece")
    # combo piece — untap loops / "for each" payoffs / infinite cues
    if re.search(r"untap target|whenever .{0,30}taps?|for each .{0,30}you control|"
                 r"\binfinite\b|deals damage equal to", low):
        sigs.add("combo_piece")
    # archetype synergy — tribal lords, landfall, "you control" scaling
    if _TOKENS_TRIBAL.search(low) or re.search(r"\bmerfolk\b|\belf\b|\belves\b|\bgoblin\b|"
                                               r"\bother .{0,20}you control\b", low):
        sigs.add("archetype_synergy")
    return sigs


# ---------------------------------------------------------------------------
# Plausibility scoring
# ---------------------------------------------------------------------------

@dataclass
class Candidate:
    name: str
    cmc: float
    type_line: str
    signals: list[str]
    score: float
    set_code: str
    notes: list[str] = dc_field(default_factory=list)


def cheap_bias(cmc: float, is_land: bool) -> float:
    """Legacy rewards low cost sharply (framework §5). Lands sidestep CMC."""
    if is_land:
        return 1.0
    if cmc <= 1:
        return 1.6
    if cmc <= 2:
        return 1.3
    if cmc <= 3:
        return 1.0
    if cmc <= 4:
        return 0.6
    return 0.3


def score_card(card: ScreenCard, signals: set[str]) -> float:
    """Plausibility = cheap-bias × Σ signal priors (floored for free/combo)."""
    if not signals:
        return 0.0
    sig_score = sum(max(SIGNAL_PRIOR.get(s, 0.0), SIGNAL_FLOOR.get(s, 0.0))
                    for s in signals)
    # multi-signal bonus (cards serving several constraints are format-definers)
    if len(signals) >= 4:
        sig_score *= 1.25
    return round(cheap_bias(card.cmc, card.is_land) * sig_score, 4)


def screen_set(cards: list[dict], min_score: float = 0.10) -> list[Candidate]:
    """Run the screen over a set's raw Scryfall card dicts → ranked candidates."""
    out: list[Candidate] = []
    for raw in cards:
        sc = ScreenCard.from_scryfall(raw)
        if sc is None:
            continue
        sigs = detect_signals(sc)
        score = score_card(sc, sigs)
        if score >= min_score:
            out.append(Candidate(sc.name, sc.cmc, sc.type_line,
                                 sorted(sigs), score, sc.set_code))
    out.sort(key=lambda c: (-c.score, c.name))
    return out


# ---------------------------------------------------------------------------
# Recall audit against a community list
# ---------------------------------------------------------------------------

def parse_community_candidates(md_text: str) -> list[str]:
    """Extract candidate card names from candidates-msh.md ('## N. Name')."""
    names = []
    for m in re.finditer(r"^##\s+\d+\.\s+(.+?)\s*$", md_text, re.M):
        name = m.group(1).strip()
        # Use the front face for DFCs in the heading ("A // B").
        names.append(name)
    return names


def recall_audit(candidates: list[Candidate], community: list[str]) -> dict:
    """Which community cards did the screen surface? Misses = screen defects."""
    surfaced = {c.name.lower() for c in candidates}
    surfaced |= {c.name.split(" // ")[0].lower() for c in candidates}
    hit, miss = [], []
    for name in community:
        front = name.split(" // ")[0].lower()
        if name.lower() in surfaced or front in surfaced:
            hit.append(name)
        else:
            miss.append(name)
    return {"hit": hit, "miss": miss,
            "recall": round(len(hit) / len(community), 3) if community else 0.0}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_set_json(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(
            f"ERROR: set JSON not found: {path}\n"
            "Save the set's cards from the Scryfall search API, e.g.:\n"
            "  curl 'https://api.scryfall.com/cards/search?q=set:msh+OR+set:msc&format=json' "
            "(paginate via next_page) → a JSON list of card objects.")
    data = json.loads(path.read_text())
    if isinstance(data, dict) and "data" in data:  # raw Scryfall search page
        data = data["data"]
    if not isinstance(data, list):
        raise SystemExit(f"ERROR: {path}: expected a JSON list of card objects (or a "
                         "Scryfall search page with a 'data' array)")
    return data


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("screen", help="rank Legacy candidates from a set JSON")
    sp.add_argument("--set-json", type=Path, required=True)
    sp.add_argument("--top", type=int, default=30)
    sp.add_argument("--min-score", type=float, default=0.10)
    ap = sub.add_parser("audit", help="recall check vs a community candidate list")
    ap.add_argument("--set-json", type=Path, required=True)
    ap.add_argument("--community", type=Path, required=True)
    ap.add_argument("--min-score", type=float, default=0.10)
    args = parser.parse_args(argv)

    cards = _load_set_json(args.set_json)
    candidates = screen_set(cards, min_score=args.min_score)

    if args.cmd == "screen":
        print(f"{len(candidates)} candidates (min_score={args.min_score}):\n")
        for c in candidates[:args.top]:
            print(f"  {c.score:5.2f}  {c.name}  [{c.cmc:g} {c.type_line}]")
            print(f"         signals: {', '.join(c.signals)}")
    elif args.cmd == "audit":
        community = parse_community_candidates(args.community.read_text())
        res = recall_audit(candidates, community)
        print(f"Recall vs community ({len(community)} cards): {res['recall']:.1%}")
        print(f"  surfaced: {len(res['hit'])}/{len(community)}")
        if res["miss"]:
            print("\n  SCREEN DEFECTS (community cards the screen missed — fix the screen, "
                  "do NOT import community recall):")
            for name in res["miss"]:
                print(f"    - {name}")
        else:
            print("  no misses — screen recall covers the community list.")


if __name__ == "__main__":
    main()
