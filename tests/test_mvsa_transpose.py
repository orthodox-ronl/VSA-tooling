"""Tests for mvsa transpose (tonica / @do shift; mode unchanged)."""

from __future__ import annotations

import re
from pathlib import Path

from vsa.cli_mvsa import main as mvsa_main
from vsa.music import Pitch
from vsa.mvsa_musicxml import export_mvsa_to_musicxml
from vsa.mvsa_transpose import (
    format_do_pitch,
    parse_transpose_target,
    transpose_mvsa_text,
    transpose_pitch,
)
from vsa.mvsa_validate import validate_mvsa_text
from vsa.pitch_resolver import _pitch_to_midi, parse_pitch_string

ROOT = Path(__file__).resolve().parents[1]
ALLELUIA = ROOT / "examples" / "bug-cases" / "alleluia-9b-toon-3-vokn.mvsa"


def _part_pitches(xml: str, part_id: str) -> list[tuple[str, str, str]]:
    marker = f'<part id="{part_id}">'
    body = xml.split(marker)[1].split("</part>")[0]
    return re.findall(
        r"<step>(\w)</step>(?:<alter>(-?\d)</alter>)?<octave>(\d)</octave>",
        body,
    )


def _midi_from_triple(step: str, alter: str, octave: str) -> int:
    a = float(alter) if alter else 0.0
    return _pitch_to_midi(Pitch(step=step, octave=int(octave), alter=a))


def test_transpose_pitch_eb_to_f():
    eb = parse_pitch_string("Eb4")
    f = parse_pitch_string("F4")
    out = transpose_pitch(eb, semitones=2, letter_shift=1)
    assert out == f
    bb = parse_pitch_string("Bb4")
    assert transpose_pitch(bb, semitones=2, letter_shift=1) == parse_pitch_string(
        "C5"
    )


def test_parse_transpose_target_octave_optional():
    ref = parse_pitch_string("Eb4")
    assert parse_transpose_target("F4", reference_do=ref) == parse_pitch_string("F4")
    assert parse_transpose_target("F", reference_do=ref) == parse_pitch_string("F4")
    assert format_do_pitch(parse_pitch_string("Eb4")) == "Eb4"


def test_transpose_alleluia_eb_to_f_sounding_plus_two():
    text = ALLELUIA.read_text(encoding="utf-8")
    assert "@do Eb4" in text
    before_xml = export_mvsa_to_musicxml(text)
    before = {
        pid: [_midi_from_triple(*t) for t in _part_pitches(before_xml, pid)]
        for pid in ("P1", "P2", "P3", "P4")
    }

    out = transpose_mvsa_text(text, to="F4", pitch="ag-vsa", align=False)
    diags = validate_mvsa_text(out)
    assert not [d for d in diags if d.severity == "error"], (diags, out)
    assert re.search(r"^@do\s+F4\b", out, re.M)
    assert "@mode major" in out
    assert "@do Eb4" not in out

    after_xml = export_mvsa_to_musicxml(out)
    after = {
        pid: [_midi_from_triple(*t) for t in _part_pitches(after_xml, pid)]
        for pid in ("P1", "P2", "P3", "P4")
    }
    for pid in before:
        assert len(before[pid]) == len(after[pid]), pid
        for b, a in zip(before[pid], after[pid], strict=True):
            assert a == b + 2, (pid, b, a)


def test_transpose_alleluia_to_f_without_octave():
    text = ALLELUIA.read_text(encoding="utf-8")
    out = transpose_mvsa_text(text, to="F", pitch="ag-vsa", align=False)
    assert re.search(r"^@do\s+F4\b", out, re.M)


def test_cli_transpose_alleluia(tmp_path: Path):
    out = tmp_path / "alleluia.in-F.mvsa"
    code = mvsa_main(
        [
            "transpose",
            str(ALLELUIA),
            "--to",
            "F4",
            "-o",
            str(out),
            "--no-align",
        ]
    )
    assert code == 0
    assert out.is_file()
    body = out.read_text(encoding="utf-8")
    assert re.search(r"^@do\s+F4\b", body, re.M)
    diags = validate_mvsa_text(body)
    assert not [d for d in diags if d.severity == "error"]
