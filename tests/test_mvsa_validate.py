"""Tests for mvsa draft validate (structuur + sync)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vsa.mvsa_validate import (
    _l_position_slots,
    _voice_position_slots,
    validate_mvsa_text,
)

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "mvsa"


def test_l_recite_and_melisma_slots():
    assert _l_position_slots(
        "~Al-le-lu-ia, ~Al-le-lu-ia, al-le- lu_&-&-&_ i_ a__"
    ) == [1, 1, 1, 1, 4, 1, 1]
    assert _l_position_slots("O Hei_.-li~&~-ge God_.&_.") == [1, 1, 2, 1, 2]
    assert _voice_position_slots("f#4 g4 f#4&g4 a4 g4&a4") == [1, 1, 2, 1, 2]


def test_validate_minimal_ok():
    text = """\
@do F4
@mode major

@sectie demo
L: a_ b_ ||
S: do re ||
A: do re ||
T: do re ||
B: do re ||
"""
    assert validate_mvsa_text(text) == []


def test_validate_sync_mismatch():
    text = """\
@sectie demo
L: a_ b_ c_ ||
S: do re ||
"""
    diags = validate_mvsa_text(text)
    assert any(d.code == "MVSA-SYNC" for d in diags)


def test_validate_unknown_directive():
    text = """\
@voices =:x
@sectie demo
L: a_ ||
S: do ||
"""
    diags = validate_mvsa_text(text)
    assert any(d.code == "MVSA-DIRECTIVE" for d in diags)


def test_validate_missing_section_end():
    text = """\
@sectie demo
L: a_ |
S: do |
"""
    diags = validate_mvsa_text(text)
    assert any(d.code == "MVSA-SECTIE-END" for d in diags)


@pytest.mark.parametrize(
    "name",
    [
        "alleluia-toon-1.mvsa",
        "alleluia-toon-8.mvsa",
        "kleine-intocht-zondag-hemelum.mvsa",
        "trisagion-8a-slav-hemelum.mvsa",
    ],
)
def test_examples_mvsa_ok(name: str):
    path = EXAMPLES / name
    diags = validate_mvsa_text(path.read_text(encoding="utf-8"), source=str(path))
    errors = [d for d in diags if d.severity == "error"]
    assert errors == [], errors
