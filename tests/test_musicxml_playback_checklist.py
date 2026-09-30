"""Tests for playback checklist + normalize + recite expand."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from vsa.musicxml_playback_checklist import (
    coria_importer_violations,
    validate_playback_musicxml,
)
from vsa.musicxml_playback_normalize import normalize_playback_musicxml
from vsa.musicxml_recite_expand import expand_recite_notes
from vsa.mvsa_musicxml import export_mvsa_to_musicxml

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
INTOCHT_SCHETS = EXAMPLES / "mvsa" / "test-kleine-intocht-zondag-hemelum.mvsa"

_BAD_SATB = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC
  "-//Recordare//DTD MusicXML 3.1 Partwise//EN"
  "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="2.0">
  <defaults><scaling><millimeters>7</millimeters><tenths>40</tenths></scaling></defaults>
  <part-list>
    <part-group type="start" number="1"/>
    <score-part id="P1"><part-name>Soprano</part-name></score-part>
    <score-part id="P2"><part-name>Soprano</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>4</duration>
        <type>whole</type>
        <beam number="1">begin</beam>
        <stem>up</stem>
      </note>
    </measure>
  </part>
</score-partwise>
"""

_LICENSE_AS_SOURCE = """\
<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <identification>
    <source>CC BY-SA 4.0 - zie colofon</source>
    <rights></rights>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>Soprano</part-name>
      <score-instrument id="P1-I1">
        <instrument-name></instrument-name>
        <instrument-sound>keyboard.piano.grand</instrument-sound>
      </score-instrument>
      <midi-device id="P1-I1" port="1"/>
      <midi-instrument id="P1-I1">
        <midi-channel>1</midi-channel>
        <midi-program>1</midi-program>
        <volume>78.7402</volume>
        <pan>0</pan>
      </midi-instrument>
    </score-part>
    <score-part id="P2">
      <part-name>Alto</part-name>
      <score-instrument id="P2-I1">
        <instrument-name></instrument-name>
        <instrument-sound>keyboard.piano.grand</instrument-sound>
      </score-instrument>
      <midi-device id="P2-I1" port="1"/>
      <midi-instrument id="P2-I1">
        <midi-channel>2</midi-channel>
        <midi-program>1</midi-program>
        <volume>78.7402</volume>
        <pan>0</pan>
      </midi-instrument>
    </score-part>
    <score-part id="P3">
      <part-name>Tenor</part-name>
      <score-instrument id="P3-I1">
        <instrument-name></instrument-name>
        <instrument-sound>keyboard.piano.grand</instrument-sound>
      </score-instrument>
      <midi-device id="P3-I1" port="1"/>
      <midi-instrument id="P3-I1">
        <midi-channel>3</midi-channel>
        <midi-program>1</midi-program>
        <volume>78.7402</volume>
        <pan>0</pan>
      </midi-instrument>
    </score-part>
    <score-part id="P4">
      <part-name>Bass</part-name>
      <score-instrument id="P4-I1">
        <instrument-name></instrument-name>
        <instrument-sound>keyboard.piano.grand</instrument-sound>
      </score-instrument>
      <midi-device id="P4-I1" port="1"/>
      <midi-instrument id="P4-I1">
        <midi-channel>4</midi-channel>
        <midi-program>1</midi-program>
        <volume>78.7402</volume>
        <pan>0</pan>
      </midi-instrument>
    </score-part>
  </part-list>
  <part id="P1"><measure number="1"><note><rest/><duration>4</duration><type>whole</type></note></measure></part>
  <part id="P2"><measure number="1"><note><rest/><duration>4</duration><type>whole</type></note></measure></part>
  <part id="P3"><measure number="1"><note><rest/><duration>4</duration><type>whole</type></note></measure></part>
  <part id="P4"><measure number="1"><note><rest/><duration>4</duration><type>whole</type></note></measure></part>
</score-partwise>
"""


def test_mvsa_export_passes_satb_checklist():
    text = INTOCHT_SCHETS.read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(text, section_id="schets-a-bladcijfer")
    findings = validate_playback_musicxml(xml, profile="satb")
    assert findings == [], findings


def test_bad_mxl_fails_m2_m4_m8():
    findings = validate_playback_musicxml(_BAD_SATB, profile="satb")
    codes = {f.code for f in findings}
    assert "M2" in codes
    assert "M4" in codes
    assert "M8" in codes or "M9" in codes


def test_normalize_clears_importer_violations():
    cleaned = normalize_playback_musicxml(_BAD_SATB, apply_timing=False)
    root = ET.fromstring(cleaned.split("?>", 1)[-1].lstrip())
    # After normalize: no beam/stem/part-group; version 3.1
    assert coria_importer_violations(root) == []
    assert "DOCTYPE" not in cleaned.upper()
    assert _child_local(root, "defaults") is None


def _child_local(root: ET.Element, name: str) -> ET.Element | None:
    from vsa.musicxml_satb_layout import local

    for c in root:
        if local(c.tag) == name:
            return c
    return None


def test_one_part_two_staff_musescore_explodes_to_satb():
    """MuseScore SA/TB often: 1 score-part, staff 1/2, voices 1/2 + 5/6."""
    xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <defaults><scaling><millimeters>7</millimeters><tenths>40</tenths></scaling></defaults>
  <identification>
    <rights>CC BY-SA 4.0</rights>
  </identification>
  <work><work-title>Proef</work-title></work>
  <part-list>
    <score-part id="P1"><part-name></part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <staves>2</staves>
        <clef number="1"><sign>G</sign><line>2</line></clef>
        <clef number="2"><sign>F</sign><line>4</line></clef>
      </attributes>
      <note>
        <pitch><step>G</step><octave>4</octave></pitch>
        <duration>4</duration><voice>1</voice><type>whole</type>
        <staff>1</staff>
        <lyric number="1"><syllabic>single</syllabic><text>Heer</text></lyric>
      </note>
      <backup><duration>4</duration></backup>
      <note>
        <pitch><step>E</step><octave>4</octave></pitch>
        <duration>4</duration><voice>2</voice><type>whole</type>
        <staff>1</staff>
      </note>
      <backup><duration>4</duration></backup>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>4</duration><voice>5</voice><type>whole</type>
        <staff>2</staff>
      </note>
      <backup><duration>4</duration></backup>
      <note>
        <pitch><step>C</step><octave>3</octave></pitch>
        <duration>4</duration><voice>6</voice><type>whole</type>
        <staff>2</staff>
      </note>
    </measure>
  </part>
</score-partwise>
"""
    cleaned = normalize_playback_musicxml(xml, apply_timing=False)
    findings = validate_playback_musicxml(cleaned, profile="satb")
    assert findings == [], findings
    root = ET.fromstring(cleaned.split("?>", 1)[-1].lstrip())
    from vsa.musicxml_satb_layout import local

    parts = [el for el in root if local(el.tag) == "part"]
    assert [p.get("id") for p in parts] == ["P1", "P2", "P3", "P4"]
    assert _child_local(root, "defaults") is None


def test_meta_source_looks_like_license():
    findings = validate_playback_musicxml(_LICENSE_AS_SOURCE, profile="satb")
    assert any(f.code == "META" for f in findings)


def test_expand_recite_feathered_breve():
    xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <part-list><score-part id="P1"><part-name>S</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note>
        <pitch><step>G</step><octave>4</octave></pitch>
        <duration>4</duration>
        <type>breve</type>
        <notehead>breve</notehead>
        <lyric number="1"><syllabic>single</syllabic><text>Heer ontferm</text></lyric>
      </note>
    </measure>
  </part>
</score-partwise>
"""
    root = ET.fromstring(xml)
    n = expand_recite_notes(root)
    assert n == 1
    notes = root.findall(".//note")
    assert len(notes) >= 2
    assert all(n.findtext("type") == "quarter" for n in notes)


def test_bibliotheek_id_prefers_content_source(tmp_path: Path):
    from vsa.bibliotheek_id import bibliotheek_id_from_path

    # Simulate repo root named bibliotheek + content-source/bibliotheek/...
    nested = (
        tmp_path
        / "bibliotheek"
        / "content-source"
        / "bibliotheek"
        / "9-alleluia"
        / "9a-toon-1"
        / "groningen"
        / "score.mvsa"
    )
    nested.parent.mkdir(parents=True)
    nested.write_text("x", encoding="utf-8")
    assert (
        bibliotheek_id_from_path(nested)
        == "9-alleluia/9a-toon-1/groningen"
    )


def test_export_respects_explicit_bibliotheek_id():
    text = INTOCHT_SCHETS.read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(
        text,
        section_id="schets-a-bladcijfer",
        bibliotheek_id="custom/id/here",
    )
    assert "Bibliotheek-id: custom/id/here" in xml
