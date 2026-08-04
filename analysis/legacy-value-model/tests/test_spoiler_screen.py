"""Tests for spoiler_screen.py — empirical candidate generation + recall audit.

Fixture-only. Synthetic Scryfall card dicts (incl. analogues of the known
Marvel candidates) verify signal detection, the cheap-card bias, ranking,
land handling, and the recall-audit logic.
"""

import sys
from pathlib import Path

_MODEL_DIR = Path(__file__).resolve().parent.parent
_ANALYSIS_DIR = _MODEL_DIR.parent
for p in (str(_MODEL_DIR), str(_ANALYSIS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest  # noqa: E402

import spoiler_screen as ss  # noqa: E402


def _card(name, cmc, type_line, oracle, keywords=None, layout="normal", set_code="msh"):
    return {"name": name, "cmc": cmc, "type_line": type_line, "oracle_text": oracle,
            "keywords": keywords or [], "layout": layout, "set": set_code}


# Analogues of real candidates + control cards.
FLOW_STATE_LIKE = _card("Cantrip Two", 2, "Sorcery",
                        "Look at the top three cards of your library. Draw a card.")
MOLE_MAN_LIKE = _card("Graveyard Lander", 3, "Legendary Creature — Human",
                      "You may play lands from your graveyard. Landfall — Whenever a land you "
                      "control enters, create a 1/1 green Minion creature token.")
NAMOR_LIKE = _card("Merfolk Lord", 3, "Legendary Creature — Merfolk",
                   "Flying. Other Merfolk you control get +1/+1. Whenever you cast a noncreature "
                   "spell, create a 1/1 blue Merfolk creature token.", keywords=["Flying"])
WASTELAND_LIKE = _card("Land Killer", 0, "Land",
                       "{T}: Add {C}. {T}, Sacrifice this land: Destroy target nonbasic land.")
FREE_COUNTER = _card("Free Counter", 4, "Instant",
                     "You may exile a blue card from your hand rather than pay this spell's mana "
                     "cost. Counter target spell.")
VANILLA = _card("Big Dumb Beast", 6, "Creature — Beast", "")
LOCK_PIECE = _card("Tax Sphere", 2, "Artifact",
                   "Noncreature spells cost {1} more to cast.")
TOKEN = _card("Some Token", 0, "Token Creature", "", layout="token")


def test_detect_cantrip_and_card_advantage():
    sc = ss.ScreenCard.from_scryfall(FLOW_STATE_LIKE)
    sigs = ss.detect_signals(sc)
    assert "cantrip" in sigs          # cheap + draws/selects
    assert "card_advantage" in sigs


def test_detect_graveyard_and_synergy_mole_man():
    sc = ss.ScreenCard.from_scryfall(MOLE_MAN_LIKE)
    sigs = ss.detect_signals(sc)
    assert "graveyard" in sigs        # plays lands from graveyard
    assert "archetype_synergy" in sigs  # landfall


def test_detect_tribal_synergy_namor():
    sc = ss.ScreenCard.from_scryfall(NAMOR_LIKE)
    sigs = ss.detect_signals(sc)
    assert "archetype_synergy" in sigs  # Merfolk lord + "you control"


def test_detect_mana_denial_land():
    sc = ss.ScreenCard.from_scryfall(WASTELAND_LIKE)
    sigs = ss.detect_signals(sc)
    assert "mana_denial" in sigs
    assert sc.is_land


def test_detect_free_spell():
    sc = ss.ScreenCard.from_scryfall(FREE_COUNTER)
    sigs = ss.detect_signals(sc)
    assert "free_spell" in sigs
    assert "tempo" in sigs            # counter target spell


def test_detect_lock_piece():
    sc = ss.ScreenCard.from_scryfall(LOCK_PIECE)
    assert "lock_piece" in ss.detect_signals(sc)


def test_vanilla_no_signals():
    sc = ss.ScreenCard.from_scryfall(VANILLA)
    assert ss.detect_signals(sc) == set()
    assert ss.score_card(sc, set()) == 0.0


def test_token_layout_excluded():
    assert ss.ScreenCard.from_scryfall(TOKEN) is None


def test_cheap_bias_monotonic():
    assert ss.cheap_bias(1, False) > ss.cheap_bias(3, False) > ss.cheap_bias(6, False)
    assert ss.cheap_bias(5, True) == 1.0  # lands sidestep CMC


def test_screen_ranks_and_filters():
    cards = [FLOW_STATE_LIKE, MOLE_MAN_LIKE, NAMOR_LIKE, WASTELAND_LIKE,
             FREE_COUNTER, VANILLA, LOCK_PIECE, TOKEN]
    cands = ss.screen_set(cards, min_score=0.05)
    names = [c.name for c in cands]
    # Vanilla 6-drop and the token are filtered out.
    assert "Big Dumb Beast" not in names
    assert "Some Token" not in names
    # The signal-bearing cards surface.
    for expected in ["Cantrip Two", "Graveyard Lander", "Merfolk Lord",
                     "Land Killer", "Free Counter", "Tax Sphere"]:
        assert expected in names
    # Sorted by descending score.
    scores = [c.score for c in cands]
    assert scores == sorted(scores, reverse=True)


def test_recall_audit():
    cards = [FLOW_STATE_LIKE, MOLE_MAN_LIKE, NAMOR_LIKE, VANILLA]
    cands = ss.screen_set(cards, min_score=0.05)
    community = ["Cantrip Two", "Graveyard Lander", "Missing Card"]
    res = ss.recall_audit(cands, community)
    assert "Cantrip Two" in res["hit"]
    assert "Graveyard Lander" in res["hit"]
    assert "Missing Card" in res["miss"]
    assert res["recall"] == pytest.approx(2 / 3, abs=1e-3)  # module rounds to 3dp


def test_parse_community_candidates():
    md = (
        "# Candidate Card Specs\n\n"
        "## 1. The Fantasticar\n- Cost: {3}\n\n"
        "## 2. Namor the Sub-Mariner\n- Cost: {1}{U}{U}\n\n"
        "## 14. The Coming of Galactus\n"
    )
    names = ss.parse_community_candidates(md)
    assert names == ["The Fantasticar", "Namor the Sub-Mariner", "The Coming of Galactus"]


def test_screen_handles_dfc():
    dfc = {"name": "Front // Back", "cmc": 2, "type_line": "Creature — Human",
           "layout": "transform", "set": "msh",
           "card_faces": [
               {"mana_cost": "{1}{U}", "oracle_text": "Flash. Draw a card."},
               {"mana_cost": "", "oracle_text": "Whenever this deals combat damage, draw a card."},
           ]}
    sc = ss.ScreenCard.from_scryfall(dfc)
    assert sc.cmc == 2
    sigs = ss.detect_signals(sc)
    assert "card_advantage" in sigs
