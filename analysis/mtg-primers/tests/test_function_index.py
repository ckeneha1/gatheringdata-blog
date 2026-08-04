"""Tests for function_index.py — the function-at-cost similarity index.

Fixture-only: a small synthetic Scryfall-shaped catalog with engineered
feature neighbours. No network, no real bulk files.
"""

import sys
from pathlib import Path

_PRIMERS_DIR = Path(__file__).resolve().parent.parent
_ANALYSIS_DIR = _PRIMERS_DIR.parent
for p in (str(_PRIMERS_DIR), str(_ANALYSIS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest  # noqa: E402

from function_index import FunctionIndex, SchemaError  # noqa: E402


def _card(name, oracle_id, cmc, oracle_text, keywords=None, type_line="Instant",
          released_at="2000-01-01", layout="normal"):
    return {
        "name": name,
        "oracle_id": oracle_id,
        "cmc": cmc,
        "type_line": type_line,
        "oracle_text": oracle_text,
        "keywords": keywords or [],
        "released_at": released_at,
        "layout": layout,
    }


@pytest.fixture
def catalog():
    # Three cantrips at CMC 1 (all "draw a card") — mutual neighbours.
    # One cantrip at CMC 3 — out of band from the CMC-1 seeds (band=1).
    # One removal spell — different function, not a neighbour.
    # One land — excluded unless include_lands.
    return [
        _card("Brainstorm", "oid-brainstorm", 1, "Draw three cards, then put two cards from your hand on top of your library.", released_at="1997-10-01"),
        _card("Ponder", "oid-ponder", 1, "Look at the top three cards of your library, then put them back in any order. You may shuffle. Draw a card.", released_at="2008-02-01"),
        _card("Opt", "oid-opt", 1, "Scry 1. Draw a card.", released_at="2000-06-01"),
        _card("Glimmer", "oid-glimmer", 3, "Draw a card.", released_at="2015-01-01"),
        _card("Doom Blade", "oid-doomblade", 2, "Destroy target nonblack creature.", type_line="Instant", released_at="2010-01-01"),
        _card("Tropical Island", "oid-tropi", 0, "", type_line="Land — Forest Island", released_at="1994-01-01"),
        _card("Tokenizer", "oid-token", 1, "Create a 1/1 token.", layout="token", released_at="2018-01-01"),
    ]


@pytest.fixture
def index(catalog):
    # first_release: give Ponder a known first-printing date; leave others to
    # the oracle-printing fallback to exercise the release_basis flagging.
    first_release = {"oid-ponder": "2008-02-01"}
    return FunctionIndex.from_card_dicts(catalog, first_release=first_release)


def test_excluded_layouts_dropped(index):
    assert index.lookup("Tokenizer") is None  # token layout excluded


def test_lookup_case_insensitive(index):
    assert index.lookup("brainstorm") is not None
    assert index.lookup("  PONDER ") is not None


def test_cantrips_are_mutual_neighbours(index):
    names = {n.name for n in index.neighborhood("Ponder")}
    assert "Opt" in names          # both draw a card at CMC 1
    assert "Brainstorm" in names   # shares card_advantage at CMC 1


def test_cmc_band_excludes_distant_cmc(index):
    # Glimmer (CMC 3) is "draw a card" too, but outside ±1 of Ponder (CMC 1).
    names = {n.name for n in index.neighborhood("Ponder", cmc_band=1)}
    assert "Glimmer" not in names
    # Widen the band and it appears.
    names_wide = {n.name for n in index.neighborhood("Ponder", cmc_band=2)}
    assert "Glimmer" in names_wide


def test_different_function_not_neighbour(index):
    names = {n.name for n in index.neighborhood("Ponder")}
    assert "Doom Blade" not in names


def test_seed_never_returned(index):
    names = {n.name for n in index.neighborhood("Ponder")}
    assert "Ponder" not in names


def test_before_date_pool_filter(index):
    # Opt released 2000-06-01; with before_date just after, it's in-pool.
    after = {n.name for n in index.neighborhood("Ponder", before_date="2000-07-01")}
    assert "Opt" in after
    # Before Opt existed, it must not appear.
    before = {n.name for n in index.neighborhood("Ponder", before_date="2000-01-01")}
    assert "Opt" not in before


def test_lands_excluded_by_default(index):
    # Build a land-function seed scenario: lands are skipped unless asked.
    # Tropical Island has no features (land, empty text) so it can't be a seed;
    # assert it's never returned as a neighbour regardless.
    for seed in ("Ponder", "Brainstorm", "Opt"):
        assert "Tropical Island" not in {n.name for n in index.neighborhood(seed, include_lands=True)}


def test_release_basis_flags(index):
    # Ponder had a first_release entry → first_printing; others fall back.
    ponder = index.lookup("Ponder")
    assert ponder.release_basis == "first_printing"
    opt = index.lookup("Opt")
    assert opt.release_basis == "oracle_printing"


def test_unknown_seed_raises(index):
    with pytest.raises(KeyError):
        index.neighborhood("Nonexistent Card")


def test_neighbors_sorted_by_similarity(index):
    ns = index.neighborhood("Ponder", min_cosine=0.0)
    sims = [n.similarity for n in ns]
    assert sims == sorted(sims, reverse=True)


def test_malformed_catalog_raises():
    with pytest.raises(SchemaError):
        FunctionIndex.from_card_dicts("not a list")  # type: ignore[arg-type]
