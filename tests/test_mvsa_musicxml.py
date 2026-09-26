"""Tests for mvsa → MusicXML export."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from vsa.mvsa_musicxml import (
    MvsaExportError,
    _resolve_slot,
    export_mvsa_to_musicxml,
)
from vsa.mvsa_parse import StickyContext, parse_l_positions, parse_mvsa
from vsa.mvsa_validate import MvsaValidationError
from vsa.pitch_resolver import PitchResolver

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "mvsa"
INTOCHT = EXAMPLES / "kleine-intocht-zondag-hemelum.canonieke.mvsa"
ALLELUIA = EXAMPLES / "alleluia-toon-8.canonieke.mvsa"


def _part_pitches(xml: str, part_id: str) -> list[tuple[str, str, str]]:
    marker = f'<part id="{part_id}">'
    body = xml.split(marker)[1].split("</part>")[0]
    return re.findall(
        r"<step>(\w)</step>(?:<alter>(-?\d)</alter>)?<octave>(\d)</octave>",
        body,
    )


def _part_lyrics(xml: str, part_id: str) -> list[tuple[str, str]]:
    marker = f'<part id="{part_id}">'
    body = xml.split(marker)[1].split("</part>")[0]
    return re.findall(r"<syllabic>(\w+)</syllabic><text>([^<]*)</text>", body)


def test_parse_l_recite_parens_and_melisma():
    pos = parse_l_positions("(Al-le-lu-ia,) al-le lu_&-&-&_ i_")
    assert pos[0].recite is True
    assert pos[0].syllables == ["Al", "le", "lu", "ia,"]
    assert pos[0].elms == []
    assert any(len(p.elms) == 4 for p in pos)


def test_parse_l_hyphen_after_recite_is_word_link():
    alone = parse_l_positions("(Al-le-lu-ia, Al-le-lu-ia, Al)-")
    assert len(alone) == 1
    assert alone[0].recite is True
    assert alone[0].elms == []  # bare '-' after ) is not ELM

    dangling_in = parse_l_positions("(Al-le-lu-ia, Al-le-lu-ia, Al-)")
    assert dangling_in[0].elms == []
    assert dangling_in[0].syllables[-1] == "Al"

    cont = parse_l_positions("(Al-le-lu-ia, Al-le-lu-ia, Al)-le-lu_&-&-&_ i_ a__")
    assert cont[0].recite is True
    assert cont[0].syllables[-1] == "Al"
    assert cont[1].syllables == ["le"]
    assert cont[1].continues_word is True
    assert cont[2].syllables == ["lu"]
    assert cont[2].continues_word is True
    assert cont[2].elms == ["_", "-", "-", "_"]


def test_parse_l_recite_optional_elm():
    pos = parse_l_positions("(Zoon van God)_")
    assert pos[0].recite is True
    assert pos[0].syllables == ["Zoon", "van", "God"]
    assert pos[0].elms == ["_"]
    assert pos[0].links == [False, False]


def test_parse_l_punct_after_elm_and_hyphen_continue():
    pos = parse_l_positions("Komt_, Chris_-tus_,")
    assert pos[0].syllables == ["Komt,"]
    assert pos[1].syllables == ["Chris"]
    assert pos[2].syllables == ["tus,"]
    assert pos[2].continues_word is True


def test_parse_l_recite_spaces_between_words():
    pos = parse_l_positions("(laat ons aan-bid-den voor)")
    assert len(pos) == 1
    assert pos[0].recite is True
    assert pos[0].syllables == ["laat", "ons", "aan", "bid", "den", "voor"]
    assert pos[0].links == [False, False, True, True, False]


def test_resolve_scientific_ignores_oct():
    ctx = StickyContext(do="F4", mode="major", oct={"B": -1})
    resolver = PitchResolver.from_metadata({"do": "F4", "mode": "major"})
    p = _resolve_slot("g3", resolver, ctx, "B")
    assert (p.step, p.octave, p.alter) == ("G", 3, 0.0)


def test_resolve_degree_octave_then_sharp():
    ctx = StickyContext(do="F4", mode="major")
    resolver = PitchResolver.from_metadata({"do": "F4", "mode": "major"})
    p = _resolve_slot("so-#", resolver, ctx, "T")
    assert (p.step, p.octave, p.alter) == ("C", 4, 1.0)


def test_resolve_degree_sharp_then_octave():
    ctx = StickyContext(do="F4", mode="major")
    resolver = PitchResolver.from_metadata({"do": "F4", "mode": "major"})
    p = _resolve_slot("so#-", resolver, ctx, "T")
    assert (p.step, p.octave, p.alter) == ("C", 4, 1.0)


def test_resolve_letter_do_octave():
    ctx = StickyContext(do="F4", mode="major", oct={"B": -1})
    resolver = PitchResolver.from_metadata({"do": "F4", "mode": "major"})
    p = _resolve_slot("g", resolver, ctx, "B")
    assert (p.step, p.octave, p.alter) == ("G", 3, 0.0)


def test_resolve_hold_dash():
    ctx = StickyContext(do="G4", mode="major")
    resolver = PitchResolver.from_metadata({"do": "G4", "mode": "major"})
    first = _resolve_slot("d4", resolver, ctx, "T")
    held = _resolve_slot("-", resolver, ctx, "T", last_pitch=first)
    assert held == first


def test_export_rejects_invalid():
    with pytest.raises(MvsaValidationError):
        export_mvsa_to_musicxml("@sectie x\nL: a_ |\nS: do |\n")


def test_export_intocht_schets_a():
    text = INTOCHT.read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(text, section_id="schets-a-bladcijfer")
    assert xml.count("<part id=") == 4
    assert '<part id="P1">' in xml
    s = _part_pitches(xml, "P1")
    b = _part_pitches(xml, "P4")
    assert s[0] == ("B", "-1", "4")  # bb4
    assert b[0] == ("G", "", "3")  # g3
    assert xml.split('<part id="P1">')[1].split("</part>")[0].count("<measure") == 4
    lyrics = _part_lyrics(xml, "P1")
    assert ("single", "Komt,") in lyrics
    assert ("begin", "Chris") in lyrics
    assert ("end", "tus,") in lyrics
    assert ("single", "Zoon van God") in lyrics
    assert any(
        t.startswith("laat ons aan-bid-den") and "voor" in t
        for _, t in lyrics
    )
    body = xml.split('<part id="P1">')[1].split("</part>")[0]
    assert 'lyric number="2"' not in body
    assert "<type>breve</type>" in xml
    # (Zoon van God)_ → half, not breve
    assert body.count("<type>half</type>") >= 1


def test_export_alleluia_so_sharp():
    text = ALLELUIA.read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(text, section_id="schets1-doremi")
    tenor = _part_pitches(xml, "P3")
    assert tenor[-1] == ("C", "1", "4")  # so-#


def test_export_unknown_section():
    text = INTOCHT.read_text(encoding="utf-8")
    with pytest.raises(MvsaExportError, match="sectie"):
        export_mvsa_to_musicxml(text, section_id="bestaat-niet")


def test_parse_sticky_oct():
    doc = parse_mvsa(
        "@do G4\n@mode major\n@oct T=-1 B=-1\n"
        "@sectie x\nL: a_ ||\nS: g4 ||\nA: e4 ||\nT: d ||\nB: g ||\n"
    )
    assert doc.sections[0].systems[0].context.oct == {"T": -1, "B": -1}
