"""Coria sanitize must strip identification/source (source+encoding crash)."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from vsa.musicxml_coria_timing import (
    CORIA_FORBIDDEN_TAGS,
    finalize_coria_musicxml,
    reorder_identification_encoding_before_misc,
    sanitize_coria_importer,
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

MISC_BEFORE_ENCODING = """\
<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <identification>
    <creator type="composer">Traditioneel</creator>
    <rights>CC BY-SA 4.0</rights>
    <miscellaneous>
      <miscellaneous-field name="bron">koormap Hemelum</miscellaneous-field>
      <miscellaneous-field name="vsa-generator">mvsa-products</miscellaneous-field>
    </miscellaneous>
    <encoding>
      <encoding-date>2026-10-04</encoding-date>
      <software>mvsa-products</software>
    </encoding>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>Soprano</part-name>
      <score-instrument id="P1-I1">
        <instrument-name></instrument-name>
        <instrument-sound>keyboard.piano.grand</instrument-sound>
      </score-instrument>
      <midi-instrument id="P1-I1">
        <midi-channel>1</midi-channel>
        <midi-program>1</midi-program>
        <volume>78.7402</volume>
        <pan>0</pan>
      </midi-instrument>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>4</divisions>
        <key><fifths>-1</fifths></key>
        <time><senza-misura/></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>4</duration>
        <voice>1</voice>
        <type>quarter</type>
        <notehead>none</notehead>
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


def test_checklist_flags_misc_before_encoding() -> None:
    findings = validate_playback_musicxml(MISC_BEFORE_ENCODING, profile="mono")
    assert any(
        f.code == "META"
        and "miscellaneous" in f.message
        and "encoding" in f.message
        for f in findings
    )
    assert any(
        f.code == "M4" and "notehead" in f.message for f in findings
    )


def test_sanitize_reorders_encoding_before_misc_and_strips_notehead() -> None:
    root = ET.fromstring(MISC_BEFORE_ENCODING)
    sanitize_coria_importer(root)
    ident = next(c for c in root if _local(c.tag) == "identification")
    tags = [_local(c.tag) for c in ident]
    assert tags.index("encoding") < tags.index("miscellaneous")
    assert not any(_local(el.tag) == "notehead" for el in root.iter())


def test_reorder_helper_and_forbidden_includes_notehead() -> None:
    assert "notehead" in CORIA_FORBIDDEN_TAGS
    root = ET.fromstring(MISC_BEFORE_ENCODING)
    ident = next(c for c in root if _local(c.tag) == "identification")
    assert reorder_identification_encoding_before_misc(ident) is True
    tags = [_local(c.tag) for c in ident]
    assert tags.index("encoding") < tags.index("miscellaneous")
    assert reorder_identification_encoding_before_misc(ident) is False


def test_finalize_misc_before_encoding_passes_checklist_mono() -> None:
    out = finalize_coria_musicxml(MISC_BEFORE_ENCODING, apply_timing=False)
    findings = validate_playback_musicxml(out, profile="mono")
    meta = [f for f in findings if f.code == "META"]
    assert not any("miscellaneous" in f.message and "vóór" in f.message for f in meta)
    assert not any(f.code == "M4" and "notehead" in f.message for f in findings)
