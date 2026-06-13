"""Tests for build_exclusions.py — the §2.4 silent-exclusion join.

Fixtures only. Covers: neighbourhood construction, pool-date filtering,
silent-vs-mentioned routing, confidence-weight ordering, field-snapshot
stamping, and the AST parity guard on the shared ability_features patterns.
"""

import ast
import sys
from pathlib import Path

_PRIMERS_DIR = Path(__file__).resolve().parent.parent
_ANALYSIS_DIR = _PRIMERS_DIR.parent
for p in (str(_PRIMERS_DIR), str(_ANALYSIS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest  # noqa: E402

import build_exclusions as bx  # noqa: E402
from function_index import FunctionIndex  # noqa: E402


def _card(name, oracle_id, cmc, oracle_text, keywords=None, type_line="Instant",
          released_at="2000-01-01"):
    return {
        "name": name, "oracle_id": oracle_id, "cmc": cmc, "type_line": type_line,
        "oracle_text": oracle_text, "keywords": keywords or [],
        "released_at": released_at, "layout": "normal",
    }


@pytest.fixture
def index():
    cards = [
        _card("Brainstorm", "oid-bs", 1, "Draw three cards, then put two cards from your hand on top of your library.", released_at="1997-10-01"),
        _card("Ponder", "oid-pon", 1, "Look at the top three cards of your library, then put them back in any order. You may shuffle. Draw a card.", released_at="2008-02-01"),
        _card("Opt", "oid-opt", 1, "Scry 1. Draw a card.", released_at="2000-06-01"),
        _card("Sleight of Hand", "oid-soh", 1, "Look at the top two cards of your library. Put one of them into your hand and the other on the bottom. Draw a card.", released_at="1997-04-01"),
        _card("Doom Blade", "oid-db", 2, "Destroy target nonblack creature.", released_at="2010-01-01"),
    ]
    return FunctionIndex.from_card_dicts(cards)  # no first_release → oracle fallback


def _primer(played, text, primer_date=None, fetched="2012-01-01", arch="Delver"):
    return bx.PrimerRecord(
        primer_id="delver", archetype=arch, primer_date=primer_date,
        fetched_date=fetched, played_cards=played, text=text,
    )


def test_silent_exclusion_basic(index):
    # Primer plays Brainstorm + Ponder, says nothing about Opt/Sleight of Hand.
    primer = _primer(
        played=["Brainstorm", "Ponder"],
        text="We run Brainstorm and Ponder as our cantrip suite.",
        primer_date="2012-01-01",
    )
    res = bx.build_exclusions_for_primer(primer, index)
    excluded = {r["excluded_card"] for r in res.silent}
    # Opt and Sleight of Hand existed by 2012, are CMC-1 cantrips, unmentioned.
    assert "Opt" in excluded
    assert "Sleight of Hand" in excluded
    # Played cards are never their own exclusions.
    assert "Brainstorm" not in excluded
    assert "Ponder" not in excluded
    # Different-function card never appears.
    assert "Doom Blade" not in excluded


def test_pool_date_filters_future_cards(index):
    # A primer dated before Opt (2000-06-01) existed must not exclude Opt.
    primer = _primer(
        played=["Brainstorm"],
        text="Brainstorm is the best cantrip.",
        primer_date="1999-01-01",
    )
    res = bx.build_exclusions_for_primer(primer, index)
    excluded = {r["excluded_card"] for r in res.silent}
    assert "Opt" not in excluded            # released 2000, after pool date
    assert "Sleight of Hand" in excluded     # released 1997, in pool


def test_mentioned_routes_away_from_silent(index):
    # The primer explicitly discusses Opt → it's NOT a silent exclusion.
    primer = _primer(
        played=["Brainstorm", "Ponder"],
        text="We run Brainstorm and Ponder. We considered Opt but it's too weak here.",
        primer_date="2012-01-01",
    )
    res = bx.build_exclusions_for_primer(primer, index)
    silent = {r["excluded_card"] for r in res.silent}
    mentioned = {r["excluded_card"] for r in res.mentioned}
    assert "Opt" in mentioned
    assert "Opt" not in silent
    # The mention row captured surrounding context.
    opt_row = next(r for r in res.mentioned if r["excluded_card"] == "Opt")
    assert "opt" in opt_row["mention_context"].lower()


def test_confidence_weight_dated_beats_undated(index):
    dated = _primer(["Brainstorm"], "Brainstorm only.", primer_date="2012-01-01")
    undated = _primer(["Brainstorm"], "Brainstorm only.", primer_date=None)
    d_row = bx.build_exclusions_for_primer(dated, index).silent[0]
    u_row = bx.build_exclusions_for_primer(undated, index).silent[0]
    assert d_row["confidence_weight"] > u_row["confidence_weight"]


def test_undated_primer_flagged_and_uses_fetched_date(index):
    primer = _primer(["Brainstorm"], "Brainstorm only.", primer_date=None, fetched="2012-01-01")
    row = bx.build_exclusions_for_primer(primer, index).silent[0]
    assert bx.FLAG_UNDATED in row["reason_flags"]
    assert row["pool_snapshot_date"] == "2012-01-01"  # falls back to fetched
    assert row["primer_date"] == ""


def test_no_panel_and_no_field_flags(index):
    primer = _primer(["Brainstorm"], "Brainstorm only.", primer_date="2012-01-01")
    row = bx.build_exclusions_for_primer(primer, index).silent[0]
    # No panel_first_seen and no field_snapshots passed → both flags present.
    assert bx.FLAG_NO_PANEL in row["reason_flags"]
    assert bx.FLAG_NO_FIELD in row["reason_flags"]
    assert row["slot_contestedness"] == ""


def test_field_snapshot_stamping(index):
    snaps = bx.FieldSnapshots({
        "2011-06-01": {"Delver": 0.12, "Lands": 0.05},
        "2013-06-01": {"Delver": 0.20},
    })
    primer = _primer(["Brainstorm"], "Brainstorm only.", primer_date="2012-01-01")
    row = bx.build_exclusions_for_primer(primer, index, field_snapshots=snaps).silent[0]
    # Latest snapshot dated ≤ 2012-01-01 is the 2011-06-01 one (no leakage).
    assert row["field_snapshot_date"] == "2011-06-01"
    assert "Delver:0.120" in row["field_top_archetypes"]
    assert bx.FLAG_NO_FIELD not in row["reason_flags"]


def test_contestedness_raises_confidence(index):
    # Among panel-PRESENT observations, a more-contested slot (more distinct
    # cards historically in the neighbourhood) yields a higher confidence weight.
    high_panel = {  # seed + all 3 neighbours seen before the pool date
        "opt": "2001-01-01", "sleight of hand": "1998-01-01",
        "brainstorm": "1998-01-01", "ponder": "2009-01-01",
    }
    low_panel = {  # only the seed seen → minimally contested
        "brainstorm": "1998-01-01",
    }
    primer = _primer(["Brainstorm"], "Brainstorm only.", primer_date="2012-01-01")
    high = bx.build_exclusions_for_primer(primer, index, panel_first_seen=high_panel).silent[0]
    low = bx.build_exclusions_for_primer(primer, index, panel_first_seen=low_panel).silent[0]
    assert high["confidence_weight"] > low["confidence_weight"]
    # Both are panel-present, so neither carries the no-panel flag.
    assert bx.FLAG_NO_PANEL not in high["reason_flags"]
    assert bx.FLAG_NO_PANEL not in low["reason_flags"]
    assert high["slot_contestedness"] == 4   # seed + 3 neighbours
    assert low["slot_contestedness"] == 1     # seed only


def test_played_card_not_in_catalog_warns(index):
    primer = _primer(["Made Up Card"], "We play Made Up Card.", primer_date="2012-01-01")
    res = bx.build_exclusions_for_primer(primer, index)
    assert res.silent == []
    assert any("not in catalog" in w for w in res.warnings)


# ── confidence_weight unit behaviour ──────────────────────────────────────────

def test_confidence_weight_monotonic_in_contestedness():
    w_low = bx.confidence_weight(dated=True, contestedness=0)
    w_high = bx.confidence_weight(dated=True, contestedness=bx.CONTESTEDNESS_SATURATION)
    assert w_high >= w_low
    assert 0.0 < w_low <= 1.0
    assert w_high <= 1.0


def test_confidence_weight_none_contestedness_uses_dated_only():
    assert bx.confidence_weight(dated=True, contestedness=None) == 1.0
    assert bx.confidence_weight(dated=False, contestedness=None) == bx.UNDATED_CONFIDENCE


# ── AST parity guard (referenced by shared/ability_features.py docstring) ─────

def test_patterns_parity_between_shared_and_analyze():
    """The shared module copies _PATTERNS verbatim from mtg-card-power/analyze.py.
    Guard against drift by comparing the (category, [regex]) structure via AST."""
    shared_path = _ANALYSIS_DIR / "shared" / "ability_features.py"
    analyze_path = _ANALYSIS_DIR / "mtg-card-power" / "analyze.py"
    if not analyze_path.exists():
        pytest.skip("canonical analyze.py not present")

    def extract_patterns(path, varname):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            # Both files declare the list with a type annotation (AnnAssign).
            if isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == varname:
                    return _pattern_signature(node.value)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == varname:
                        return _pattern_signature(node.value)
        raise AssertionError(f"{varname} not found in {path}")

    def _pattern_signature(list_node):
        # list of (str, [re.compile(r"...", flags)]) → [(cat, [raw_regex, ...]), ...]
        sig = []
        for elt in list_node.elts:
            cat = elt.elts[0].value
            regexes = []
            for call in elt.elts[1].elts:
                # call is re.compile(<str>, re.I) — take the first positional arg
                regexes.append(call.args[0].value)
            sig.append((cat, regexes))
        return sig

    shared_sig = extract_patterns(shared_path, "PATTERNS")
    analyze_sig = extract_patterns(analyze_path, "_PATTERNS")
    assert shared_sig == analyze_sig, (
        "ability_features.PATTERNS has drifted from analyze.py _PATTERNS — "
        "edit both (see ability_features.py module docstring)."
    )
