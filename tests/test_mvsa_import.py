"""Tests for score → mvsa import (roundtrip via MusicXML)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from vsa.mvsa_import import import_score_to_mvsa
from vsa.mvsa_musicxml import export_mvsa_to_musicxml
from vsa.mvsa_validate import validate_mvsa_text
from vsa.musicxml_package import write_musicxml_output

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


def test_roundtrip_mvsa_mxl_mvsa_pitch_doremi(tmp_path: Path):
    text = ALLELUIA.read_text(encoding="utf-8")
    section = "schets2-oct-doremi"
    before = export_mvsa_to_musicxml(text, section_id=section)
    mxl = tmp_path / "schets2.mxl"
    write_musicxml_output(mxl, before)

    imported = import_score_to_mvsa(mxl, pitch="doremi", octave_style="@oct")
    diags = validate_mvsa_text(imported)
    assert not [d for d in diags if d.severity == "error"], diags

    after = export_mvsa_to_musicxml(imported)
    assert _all_pitches(before) == _all_pitches(after)


def test_roundtrip_mvsa_mxl_mvsa_pitch_abc(tmp_path: Path):
    text = ALLELUIA.read_text(encoding="utf-8")
    section = "schets2-oct-doremi"
    before = export_mvsa_to_musicxml(text, section_id=section)
    mxl = tmp_path / "schets2.mxl"
    write_musicxml_output(mxl, before)

    imported = import_score_to_mvsa(mxl, pitch="abc", octave_style="@oct")
    diags = validate_mvsa_text(imported)
    assert not [d for d in diags if d.severity == "error"], diags
    after = export_mvsa_to_musicxml(imported)
    assert _all_pitches(before) == _all_pitches(after)
