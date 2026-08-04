"""Tests for fetch_spoiler.py — pagination/accumulation/dedup (pure parts only;
the network fetch itself is not exercised)."""

import sys
from pathlib import Path

_MODEL_DIR = Path(__file__).resolve().parent.parent
if str(_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(_MODEL_DIR))

import pytest  # noqa: E402

import fetch_spoiler as fsp  # noqa: E402


def test_accumulate_pages():
    pages = [
        {"data": [{"name": "A"}, {"name": "B"}], "has_more": True, "next_page": "x"},
        {"data": [{"name": "C"}], "has_more": False},
    ]
    cards = fsp.accumulate_pages(pages)
    assert [c["name"] for c in cards] == ["A", "B", "C"]


def test_accumulate_pages_rejects_malformed():
    with pytest.raises(ValueError):
        fsp.accumulate_pages([{"not_data": []}])


def test_dedup_by_oracle_id_keeps_first():
    cards = [
        {"name": "Card (full art)", "oracle_id": "oid-1"},
        {"name": "Card", "oracle_id": "oid-1"},          # same card, variant printing
        {"name": "Other", "oracle_id": "oid-2"},
    ]
    out = fsp.dedup_by_oracle_id(cards)
    assert [c["oracle_id"] for c in out] == ["oid-1", "oid-2"]
    assert out[0]["name"] == "Card (full art)"  # first kept


def test_dedup_keeps_cards_without_oracle_id():
    cards = [{"name": "Weird", "layout": "token"}, {"name": "X", "oracle_id": "oid-1"}]
    out = fsp.dedup_by_oracle_id(cards)
    assert len(out) == 2
