"""Tests for Coria timing transforms (pause + caesura)."""

from __future__ import annotations

from vsa.musicxml_coria_timing import apply_coria_timing


def test_apply_coria_timing_inserts_pauze_and_moves_cue():
    xml = """\
<?xml version="1.0"?>
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1"><part-name>Soprano</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>4</divisions></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch>
        <duration>16</duration><type>whole</type></note>
      <barline location="right"><bar-style>light-light</bar-style></barline>
    </measure>
    <measure number="2">
      <direction placement="above">
        <direction-type><words>P: volgende</words></direction-type>
      </direction>
      <note><pitch><step>D</step><octave>4</octave></pitch>
        <duration>16</duration><type>whole</type></note>
      <barline location="right"><bar-style>light-heavy</bar-style></barline>
    </measure>
  </part>
</score-partwise>
"""
    out = apply_coria_timing(xml)
    assert "[PAUZE]" in out
    assert out.index("P: volgende") < out.index("[PAUZE]")
    assert out.count("<measure ") == 3


def test_apply_coria_timing_caesura_adds_quarter_rest():
    xml = """\
<?xml version="1.0"?>
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1"><part-name>Soprano</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>4</divisions></attributes>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>4</duration><type>quarter</type>
        <notations><articulations><caesura/></articulations></notations>
      </note>
      <note>
        <pitch><step>D</step><octave>4</octave></pitch>
        <duration>4</duration><type>quarter</type>
      </note>
    </measure>
  </part>
</score-partwise>
"""
    out = apply_coria_timing(xml)
    assert "<rest" in out
    assert out.count("<type>quarter</type>") >= 3  # 2 notes + 1 rest
