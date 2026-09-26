"""Tests for mvsa normalize (pitch-form rewrite)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from vsa.mvsa_musicxml import export_mvsa_to_musicxml
from vsa.mvsa_normalize import normalize_mvsa_text
from vsa.mvsa_validate import validate_mvsa_text
from vsa.pitch_resolver import ehm_to_motion

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "mvsa"
ALLELUIA = EXAMPLES / "alleluia-toon-8.canonieke.mvsa"


def _part_pitches(xml: str, part_id: str) -> list[tuple[str, str, str]]:
    marker = f'<part id="{part_id}">'
    body = xml.split(marker)[1].split("</part>")[0]
    return re.findall(
        r"<step>(\w)</step>(?:<alter>(-?\d)</alter>)?<octave>(\d)</octave>",
        body,
    )


def _all_pitches(xml: str) -> dict[str, list[tuple[str, str, str]]]:
    return {pid: _part_pitches(xml, pid) for pid in ("P1", "P2", "P3", "P4")}


def test_ehm_digit_forms():
    assert ehm_to_motion("/3") == (3, 0.0)
    assert ehm_to_motion("\\2") == (-2, 0.0)
    assert ehm_to_motion("//") == (2, 0.0)


def test_normalize_abc_pitch_equivalent_schets2():
    text = ALLELUIA.read_text(encoding="utf-8")
    section = "schets2-oct-doremi"
    before = export_mvsa_to_musicxml(text, section_id=section)
    normalized = normalize_mvsa_text(text, pitch="abc", octave_style="@oct")
    diags = validate_mvsa_text(normalized)
    assert not [d for d in diags if d.severity == "error"]
    after = export_mvsa_to_musicxml(normalized, section_id=section)
    assert _all_pitches(before) == _all_pitches(after)


def test_normalize_doremi_abc_doremi_roundtrip():
    text = ALLELUIA.read_text(encoding="utf-8")
    section = "schets2-oct-doremi"
    before = export_mvsa_to_musicxml(text, section_id=section)
    mid = normalize_mvsa_text(text, pitch="abc", octave_style="@oct")
    back = normalize_mvsa_text(mid, pitch="doremi", octave_style="@oct")
    after = export_mvsa_to_musicxml(back, section_id=section)
    assert _all_pitches(before) == _all_pitches(after)


def test_normalize_vsa_pitch_equivalent_schets2():
    text = ALLELUIA.read_text(encoding="utf-8")
    section = "schets2-oct-doremi"
    before = export_mvsa_to_musicxml(text, section_id=section)
    normalized = normalize_mvsa_text(text, pitch="vsa", octave_style="@oct")
    diags = validate_mvsa_text(normalized)
    assert not [d for d in diags if d.severity == "error"]
    after = export_mvsa_to_musicxml(normalized, section_id=section)
    assert _all_pitches(before) == _all_pitches(after)


def test_export_alleluia_ehm_section():
    text = ALLELUIA.read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(text, section_id="schets5-ehm")
    assert _part_pitches(xml, "P1")[0] == ("B", "-1", "4")
