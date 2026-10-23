"""Eindanker-check: false positives vermijden (rust, carry, a–g, resolve-fout)."""

from __future__ import annotations

from vsa.mvsa_bar_anchors import is_valid_bar_anchor
from vsa.mvsa_validate import validate_mvsa_text


def _anker_errors(text: str) -> list[str]:
    return [
        d.message
        for d in validate_mvsa_text(text)
        if d.code == "MVSA-BAR-ANKER"
    ]


def test_bar_anchor_ok_after_rest_slots():
    """Klinkende a–g/EHM + rusten: lopende toon blijft voor ``|f#4``."""
    text = """\
@do G4
@mode major
@oct S=0 A=-1 T=-1 B=-2

@sectie demo
L: U,~&~&~&~ ||
S: f#4&r&r&r ||f#4
A: d#4&r&r&r ||d#4
T: b3&c4&b3&a3 ||a3
B: b2&c3&b2&a2 ||a2
"""
    assert _anker_errors(text) == []


def test_bar_anchor_ok_after_relative_ehm_then_rests():
    """Laatste klinkende slot is relatieve EHM (a–g-resultaat), daarna rusten."""
    text = """\
@do G4
@mode major

@sectie demo
L: a_~&.&~ ||
S: g4&/&r ||a4
A: e4&/&r ||f#4
T: b3&/&r ||c4
B: e3&/&r ||f#3
"""
    assert _anker_errors(text) == []


def test_bar_anchor_ok_absolute_ag_letter_then_anchor():
    """Laatste noot absolute a–g (letter of scientific) matcht eindanker."""
    text = """\
@do G4
@mode major

@sectie demo
L: a_ ||
S: g4 a ||a
A: e4 a ||a4
T: b3 c4 ||c4
B: e3 g3 ||g3
"""
    assert _anker_errors(text) == []


def test_bar_anchor_ok_softwrap_carry_then_only_rests():
    """Volgend systeem: alleen rusten; carry levert de berekende toon."""
    text = """\
@do G4
@mode major

@sectie demo
L: a_ |
S: g4 |
A: e4 |
T: b3 |
B: e3 |

L: ()~ ||
S: r ||g4
A: r ||e4
T: r ||b3
B: r ||e3
"""
    assert _anker_errors(text) == []


def test_bar_anchor_ok_softwrap_carry_hold():
    text = """\
@do G4
@mode major

@sectie demo
L: a_ |
S: g4 |
A: e4 |
T: b3 |
B: e3 |

L: b_ ||
S: - ||g4
A: - ||e4
T: - ||b3
B: - ||e3
"""
    assert _anker_errors(text) == []


def test_bar_anchor_rejects_rest_as_anchor():
    assert not is_valid_bar_anchor("r")
    assert not is_valid_bar_anchor("R")
    text = """\
@do G4
@mode major

@sectie demo
L: a_ ||
S: g4 ||r
A: e4 ||e4
T: b3 ||b3
B: e3 ||e3
"""
    msgs = _anker_errors(text)
    assert any("ongeldig eindanker" in m and "S:" in m for m in msgs), msgs


def test_bar_anchor_no_sounding_still_errors():
    """Echt geen toon (geen carry, alleen rust): blijft fout."""
    text = """\
@do G4
@mode major

@sectie demo
L: ()~ ||
S: r ||g4
A: r ||e4
T: r ||b3
B: r ||e3
"""
    msgs = _anker_errors(text)
    assert any("geen berekende toon" in m for m in msgs), msgs


def test_bar_anchor_mismatch_still_reported():
    text = """\
@do G4
@mode major

@sectie demo
L: a_ ||
S: g4 ||a4
A: e4 ||e4
T: b3 ||b3
B: e3 ||e3
"""
    msgs = _anker_errors(text)
    assert any("berekend" in m and "verwacht" in m and "S:" in m for m in msgs), msgs
