"""MusicXML visible accidentals and hersteltekens (natural)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from vsa.block_parser import DEFAULT_METADATA
from vsa.musicxml_renderer import (
    MUSICXML_PROFILE_ENGRAVING,
    MusicXMLRenderer,
    _key_alter_for_step,
    _visible_accidental,
)
from vsa.parser import Parser


def _notes(xml: str) -> list[ET.Element]:
    root = ET.fromstring(xml.split("?>", 1)[-1].split("dtd\">", 1)[-1])
    return list(root.iter("note"))


def _render(body: str, *, do: str = "C4", mode: str = "major") -> str:
    meta = dict(DEFAULT_METADATA)
    meta.update(
        {
            "do": do,
            "mode": mode,
            "musicxml-profile": MUSICXML_PROFILE_ENGRAVING,
        }
    )
    return MusicXMLRenderer(metadata=meta).render(Parser(body).parse())


def test_key_alter_for_step_f_major() -> None:
    assert _key_alter_for_step("B", -1) == -1
    assert _key_alter_for_step("F", -1) == 0
    assert _key_alter_for_step("F", 1) == 1


def test_visible_accidental_natural_after_sharp() -> None:
    state: dict[str, int] = {}
    assert _visible_accidental("C", 1.0, 0, state) == "sharp"
    assert state["C"] == 1
    assert _visible_accidental("C", 1.0, 0, state) is None  # already active
    assert _visible_accidental("D", 0.0, 0, state) is None
    assert _visible_accidental("C", 0.0, 0, state) == "natural"
    assert state["C"] == 0


def test_export_sharp_then_return_emits_natural() -> None:
    """{#-}{/}{\\} → C# then D then C natural: herstelteken on last C."""
    xml = _render(r"[:] {#-Cis}{/Re}{\Do} [:]")
    notes = _notes(xml)
    assert len(notes) == 3

    cis, re, do_ = notes
    assert cis.findtext("pitch/step") == "C"
    assert cis.findtext("pitch/alter") == "1"
    assert cis.findtext("accidental") == "sharp"

    assert re.findtext("pitch/step") == "D"
    assert re.find("accidental") is None

    assert do_.findtext("pitch/step") == "C"
    assert do_.find("pitch/alter") is None
    assert do_.findtext("accidental") == "natural"


def test_export_same_tone_hold_no_repeat_accidental() -> None:
    r"""{+\go}{ri}{/os}: sharp once on C; ri keeps Cis without second sharp."""
    xml = _render(r"[/:] {+\go}{ri}{/os} [/:]")
    notes = _notes(xml)
    # start marker sets degree; first sounding may be recite-less — scopes only
    assert [n.findtext("lyric/text") for n in notes] == ["go", "ri", "os"]

    go, ri, os_ = notes
    assert go.findtext("pitch/step") == "C"
    assert go.findtext("pitch/alter") == "1"
    assert go.findtext("accidental") == "sharp"

    assert ri.findtext("pitch/step") == "C"
    assert ri.findtext("pitch/alter") == "1"
    assert ri.find("accidental") is None

    assert os_.findtext("pitch/step") == "D"
    assert os_.find("accidental") is None


def test_export_flat_then_natural_on_same_step() -> None:
    xml = _render(r"[:] {b-Des}{/Re}{\Do} [:]")
    notes = _notes(xml)
    assert notes[0].findtext("accidental") == "flat"
    assert notes[2].findtext("accidental") == "natural"


def test_new_measure_resets_accidental_state() -> None:
    """After a barline, a fresh sharp is written again; no leftover natural."""
    xml = _render("[:] {#-A} // {#-B} [:]")
    notes = _notes(xml)
    assert len(notes) == 2
    assert notes[0].findtext("accidental") == "sharp"
    assert notes[1].findtext("accidental") == "sharp"
