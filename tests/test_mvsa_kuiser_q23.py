"""Kuiser Q2 (@-blok) + Q3 (#maat) — docs/formats/kuiser.md."""

from __future__ import annotations

import re

from vsa.mvsa_kuiser import kuiser_mvsa_text
from vsa.mvsa_kuiser_q23 import (
    apply_q2_q3,
    kuiser_tempo_for_soort,
    should_replace_tempo,
)
from vsa.mvsa_validate import validate_mvsa_text

_MIN = """\
@do F4
@mode major
@sectie a
L: hei ge ||
S: fa so ||
A: re re ||
T: la- so- ||
B: re re ||
"""


def test_kuiser_tempo_fingerprint():
    assert kuiser_tempo_for_soort("stichier") == 181
    assert kuiser_tempo_for_soort("tropaar") == 181
    assert kuiser_tempo_for_soort("kondak") == 181
    assert kuiser_tempo_for_soort("alleluia") == 131
    assert kuiser_tempo_for_soort(None) == 131
    assert should_replace_tempo(None)
    assert should_replace_tempo(130)
    assert should_replace_tempo(180)
    assert not should_replace_tempo(72)
    assert not should_replace_tempo(181)


def test_q2_inserts_title_do_mode_tempo_and_keeps_custom_tempo():
    text = """\
@title "Litanie"
@do G4
@mode minor
@tempo 72
@sectie a
L: Heer ||
S: so ||
A: mi ||
T: do ||
B: do ||
"""
    out = apply_q2_q3(text)
    assert '@title "Litanie"' in out
    assert "@do G4" in out
    assert "@mode minor" in out
    assert "@tempo 72" in out
    assert out.index("@title") < out.index("@sectie")
    assert out.index("@tempo") < out.index("@sectie")


def test_q2_replaces_130_with_131_or_181_from_filename():
    text = """\
@do F4
@mode major
@tempo 130
@sectie a
L: Heer ||
S: fa ||
A: re ||
T: la- ||
B: re ||
"""
    out = apply_q2_q3(
        text, source_path="stichier-heer-ik-roep-toon-1-groningen.mvsa"
    )
    assert "@tempo 181" in out
    assert '@title "Heer ik roep (Toon 1)"' in out

    out2 = apply_q2_q3(text, source_path="alleluia-toon-8.mvsa")
    assert "@tempo 131" in out2


def test_q2_keeps_oct_when_present():
    text = """\
@do F4
@mode major
@oct S=0 A=0 T=-1 B=-2
@sectie a
L: Heer ||
S: fa ||
A: re ||
T: la- ||
B: re ||
"""
    out = apply_q2_q3(text)
    assert "@oct S=0 A=0 T=-1 B=-2" in out
    assert out.index("@tempo") < out.index("@oct")


def test_q3_maat_comments_per_system_and_strips_old():
    text = """\
@do F4
@mode major
@sectie a
# maat 99
#maat 5
L: a_ | b_ ||
S: fa | so ||
A: re | re ||
T: la- | so- ||
B: re | re ||

@sectie b
L: c_ ||
S: mi ||
A: do ||
T: so- ||
B: do ||
"""
    out = apply_q2_q3(text)
    assert "# maat" not in out
    assert "#maat 99" not in out
    assert "#maat 5" not in out
    assert "#maat 1" in out
    # First system: 2 measures → second system starts at 3
    assert "#maat 3" in out
    assert out.index("#maat 1") < out.index("L: a_")
    assert out.index("@sectie a") < out.index("#maat 1")
    assert out.index("#maat 1") < out.index("@sectie b")
    assert out.index("@sectie b") < out.index("#maat 3")


def test_kuiser_pipeline_q2_q3_then_validate():
    result = kuiser_mvsa_text(
        _MIN,
        align=False,
        source_path="tropaar-voorbeeld-toon-4-hemelum.mvsa",
    )
    assert "@tempo 181" in result.text
    assert "#maat 1" in result.text
    assert '@title "' in result.text
    assert "(Toon 4)" in result.text
    errs = [d for d in validate_mvsa_text(result.text) if d.severity == "error"]
    assert not errs


def test_kuiser_existing_fixtures_still_ok():
    """Minimal fixtures gain Q2/Q3 headers but remain valid."""
    result = kuiser_mvsa_text(_MIN, align=False)
    assert "@tempo 131" in result.text
    assert re.search(r"#maat 1\nL:", result.text)
    errs = [d for d in validate_mvsa_text(result.text) if d.severity == "error"]
    assert not errs
