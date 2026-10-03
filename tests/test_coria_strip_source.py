"""Coria sanitize must strip identification/source (source+encoding crash)."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from vsa.musicxml_coria_timing import (
    finalize_coria_musicxml,
    strip_coria_identification_source,
)
from vsa.musicxml_playback_checklist import validate_playback_musicxml


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


SAMPLE = """\
<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <identification>
    <rights>CC BY-SA 4.0</rights>
    <source>Hemelum (koorinstructie)</source>
    <encoding>
      <software>test</software>
    </encoding>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>Vocal</part-name>
      <score-instrument id="P1-I1">
        <instrument-name>Voice</instrument-name>
        <instrument-sound>keyboard.piano.grand</instrument-sound>
      </score-instrument>
      <midi-instrument id="P1-I1">
        <midi-channel>1</midi-channel>
        <midi-program>1</midi-program>
      </midi-instrument>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>4</divisions>
        <key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
      </note>
    </measure>
  </part>
</score-partwise>
"""


def test_strip_moves_source_to_misc_bron() -> None:
    root = ET.fromstring(SAMPLE)
    assert strip_coria_identification_source(root) == 1
    ident = next(c for c in root if _local(c.tag) == "identification")
    assert not any(_local(c.tag) == "source" for c in ident)
    bron = [
        c
        for misc in ident
        if _local(misc.tag) == "miscellaneous"
        for c in misc
        if _local(c.tag) == "miscellaneous-field" and c.get("name") == "bron"
    ]
    assert len(bron) == 1
    assert bron[0].text == "Hemelum (koorinstructie)"


def test_finalize_strips_source_and_checklist_ok_mono() -> None:
    out = finalize_coria_musicxml(SAMPLE, apply_timing=False)
    root = ET.fromstring(out)
    ident = next(c for c in root if _local(c.tag) == "identification")
    assert not any(_local(c.tag) == "source" for c in ident)
    findings = validate_playback_musicxml(out, profile="mono")
    meta = [f for f in findings if f.code == "META"]
    assert not any("source" in f.message and "encoding" in f.message for f in meta)


def test_checklist_flags_source_plus_encoding() -> None:
    findings = validate_playback_musicxml(SAMPLE, profile="mono")
    assert any(
        f.code == "META" and "source" in f.message and "encoding" in f.message
        for f in findings
    )
