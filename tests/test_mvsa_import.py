"""Tests for score → mvsa import (roundtrip via MusicXML)."""

from __future__ import annotations

import re
from pathlib import Path

from vsa.musicxml_package import write_musicxml_output
from vsa.musicxml_playback_normalize import normalize_playback_musicxml
from vsa.mvsa_import import (
    DEFAULT_SYSTEM_SOFT_WIDTH,
    do_from_fifths,
    import_score_to_mvsa,
    join_import_syllables,
    parse_musicxml_satb,
    read_mscz_key_fifths,
    score_to_mvsa,
)
from vsa.mvsa_musicxml import export_mvsa_to_musicxml
from vsa.mvsa_validate import validate_mvsa_text

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "mvsa"
# Schets-secties (schets3-oct-doremi, …) staan in het test-fixture.
ALLELUIA = EXAMPLES / "test-alleluia-toon-8.mvsa"


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
    section = "schets3-oct-doremi"
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
    section = "schets3-oct-doremi"
    before = export_mvsa_to_musicxml(text, section_id=section)
    mxl = tmp_path / "schets2.mxl"
    write_musicxml_output(mxl, before)

    imported = import_score_to_mvsa(mxl, pitch="abc", octave_style="@oct")
    diags = validate_mvsa_text(imported)
    assert not [d for d in diags if d.severity == "error"], diags
    after = export_mvsa_to_musicxml(imported)
    assert _all_pitches(before) == _all_pitches(after)


def test_sa_tb_normalize_then_import_keeps_lyric_slots():
    """MuseScore-achtige SA/TB: na explode geen melisma-explosie op laatste lettergreep."""
    xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <work><work-title>Proef</work-title></work>
  <part-list>
    <score-part id="P1"><part-name></part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>2</divisions>
        <key><fifths>-1</fifths></key>
        <staves>2</staves>
        <clef number="1"><sign>G</sign><line>2</line></clef>
        <clef number="2"><sign>F</sign><line>4</line></clef>
      </attributes>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>2</duration><voice>1</voice><type>quarter</type>
        <staff>1</staff>
        <lyric number="1"><syllabic>single</syllabic><text>Wij</text></lyric>
      </note>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>1</duration><voice>1</voice><type>eighth</type>
        <staff>1</staff>
        <lyric number="1"><syllabic>single</syllabic><text>die</text></lyric>
      </note>
      <note>
        <pitch><step>G</step><octave>4</octave></pitch>
        <duration>1</duration><voice>1</voice><type>eighth</type>
        <staff>1</staff>
        <lyric number="1"><syllabic>single</syllabic><text>de</text></lyric>
      </note>
      <note>
        <pitch><step>F</step><octave>4</octave></pitch>
        <duration>1</duration><voice>1</voice><type>eighth</type>
        <staff>1</staff>
        <lyric number="1"><syllabic>begin</syllabic><text>Che</text></lyric>
      </note>
      <note>
        <pitch><step>G</step><octave>4</octave></pitch>
        <duration>1</duration><voice>1</voice><type>eighth</type>
        <staff>1</staff>
      </note>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>2</duration><voice>1</voice><type>quarter</type>
        <staff>1</staff>
        <lyric number="1"><syllabic>end</syllabic><text>ru</text></lyric>
      </note>
      <backup><duration>8</duration></backup>
      <note>
        <pitch><step>F</step><octave>4</octave></pitch>
        <duration>2</duration><voice>2</voice><type>quarter</type>
        <staff>1</staff>
      </note>
      <note>
        <pitch><step>F</step><octave>4</octave></pitch>
        <duration>1</duration><voice>2</voice><type>eighth</type>
        <staff>1</staff>
      </note>
      <note>
        <pitch><step>E</step><octave>4</octave></pitch>
        <duration>1</duration><voice>2</voice><type>eighth</type>
        <staff>1</staff>
      </note>
      <note>
        <pitch><step>D</step><octave>4</octave></pitch>
        <duration>1</duration><voice>2</voice><type>eighth</type>
        <staff>1</staff>
      </note>
      <note>
        <pitch><step>E</step><octave>4</octave></pitch>
        <duration>1</duration><voice>2</voice><type>eighth</type>
        <staff>1</staff>
      </note>
      <note>
        <pitch><step>F</step><octave>4</octave></pitch>
        <duration>2</duration><voice>2</voice><type>quarter</type>
        <staff>1</staff>
      </note>
      <backup><duration>8</duration></backup>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>8</duration><voice>5</voice><type>whole</type>
        <staff>2</staff>
      </note>
      <backup><duration>8</duration></backup>
      <note>
        <pitch><step>F</step><octave>3</octave></pitch>
        <duration>8</duration><voice>6</voice><type>whole</type>
        <staff>2</staff>
      </note>
    </measure>
  </part>
</score-partwise>
"""
    cleaned = normalize_playback_musicxml(xml, apply_timing=False)
    score = parse_musicxml_satb(cleaned)
    text = score_to_mvsa(score, pitch_form="abc", system_soft_width=80)
    l_line = next(line for line in text.splitlines() if line.startswith("L:"))
    s_line = next(line for line in text.splitlines() if line.startswith("S:"))
    a_line = next(line for line in text.splitlines() if line.startswith("A:"))
    first_l = l_line.split("|", 1)[0]
    first_s = s_line.split("|", 1)[0]
    first_a = a_line.split("|", 1)[0]
    assert "Wij~" in first_l  # canonieke standaard-lengte als ``~``
    assert "Che.&." in first_l
    assert "-ru~" in first_l
    # "ru" is one quarter — not a long melisma tail of filler notes.
    after_ru = first_l.split("-ru", 1)[1]
    assert after_ru.startswith("~")
    assert "&" not in after_ru.split()[0]
    # Same height as previous position → ``-`` (niet opnieuw ``a4``).
    assert re.search(r"a4\s+-\s+g4\s+f4&g4\s+a4", first_s)
    assert "f4" in first_a
    assert "c4&c4&c4&c4" not in first_a
    diags = validate_mvsa_text(text)
    assert not [d for d in diags if d.severity == "error"], diags


def test_repeated_pitch_with_lyrics_collapses_to_recite():
    """Same-pitch notes each with a lyric → one recite; holds only for melisma."""
    xml = _satb_score_xml(
        {
            "P1": """\
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>0</fifths></key></attributes>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>a</text></lyric>
      </note>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>b</text></lyric>
      </note>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>c</text></lyric>
      </note>
      <note>
        <pitch><step>B</step><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>d</text></lyric>
      </note>
    </measure>
    <measure number="2">
      <note>
        <pitch><step>B</step><octave>4</octave></pitch>
        <duration>2</duration><type>half</type>
        <lyric number="1"><syllabic>single</syllabic><text>e</text></lyric>
      </note>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>f</text></lyric>
      </note>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>begin</syllabic><text>g</text></lyric>
      </note>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
      </note>
    </measure>""",
            "P2": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>F</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>F</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>F</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
    </measure>
    <measure number="2">
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>2</duration><type>half</type></note>
      <note><pitch><step>F</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>F</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>F</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
    </measure>""",
            "P3": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
    </measure>
    <measure number="2">
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>2</duration><type>half</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
    </measure>""",
            "P4": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>F</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>F</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>F</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>F</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
    </measure>
    <measure number="2">
      <note><pitch><step>F</step><octave>3</octave></pitch><duration>2</duration><type>half</type></note>
      <note><pitch><step>F</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>F</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>F</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
    </measure>""",
        }
    )
    score = parse_musicxml_satb(xml)
    text = score_to_mvsa(score, pitch_form="abc", system_soft_width=200)
    l_line = next(ln for ln in text.splitlines() if ln.startswith("L:"))
    s_line = next(ln for ln in text.splitlines() if ln.startswith("S:"))
    # maat1: three same-pitch lyrics → one recite; then d on b4
    assert "(a b c)" in l_line
    assert re.search(r"a4\s+b4", s_line)
    assert not re.search(r"a4\s+-\s+-", s_line)
    # maat2: pair f + g stays separate (drempel ≥3); g + lyric-less → melisma
    assert "(f g)" not in l_line
    assert "-&-" in s_line.replace(" ", "") or re.search(r"-\s*&\s*-", s_line)
    diags = validate_mvsa_text(text)
    assert not [d for d in diags if d.severity == "error"], (diags, text)


def test_join_import_syllables_repairs_musescore_word_boundaries():
    """Syllabic-aware join + targeted MuseScore hacks."""
    assert join_import_syllables(
        ["Wij", "heb", "ben", "het", "wa", "re"],
        ["single", "begin", "middle", "middle", "end", "single"],
    ) == "Wij heb-ben het wa-re"
    assert join_import_syllables(
        ["Ver", "vuld zij on-ze mond", "met"]
    ) == "Ver-vuld zij on-ze mond met"
    assert join_import_syllables(
        ["he", "mel", "se", "Geest"],
        ["begin", "middle", "end", "single"],
    ) == "he-mel-se-Geest"
    # MuseScore often puts ``Geest`` as chain ``end`` (N≥4 bigrams + merge).
    assert join_import_syllables(
        ["he", "mel", "se", "Geest"],
        ["begin", "middle", "middle", "end"],
    ) == "he-mel-se-Geest"
    # Same result when MuseScore marks all as single.
    assert join_import_syllables(
        ["he", "mel", "se", "Geest"],
        ["single", "single", "single", "single"],
    ) == "he-mel-se-Geest"
    # Underlay string with spaces: glue ``aan``+``bid-den``.
    assert join_import_syllables(
        ["aan bid-den de on-deel-ba-re"], ["single"]
    ) == "aan-bid-den de on-deel-ba-re"
    # Closed-class: ``ons``+``heeft`` / ``Gij``+``hebt`` must not glue.
    assert join_import_syllables(
        ["ons", "heeft"], ["single", "single"]
    ) == "ons heeft"
    assert join_import_syllables(
        ["Gij", "hebt"], ["single", "single"]
    ) == "Gij hebt"
    # Pending single prepends into begin…end (``aan-bid-den``).
    assert join_import_syllables(
        ["aan", "bid", "den"],
        ["single", "begin", "end"],
    ) == "aan-bid-den"
    # Or extends into an already-hyphenated MuseScore token.
    assert join_import_syllables(
        ["aan", "bid-den"], ["single", "single"]
    ) == "aan-bid-den"
    # Trailing attach yields to a better next word (``ge-loof``).
    assert join_import_syllables(
        ["wa", "re", "ge", "loof"],
        ["begin", "end", "single", "single"],
    ) == "wa-re ge-loof"
    # Short capital compounds (allowlist); not ``Licht-aan``.
    assert join_import_syllables(
        ["Be", "waar", "ons", "in"],
        ["single", "single", "single", "single"],
    ) == "Be-waar ons in"
    assert join_import_syllables(
        ["Ont", "ferm"], ["single", "single"]
    ) == "Ont-ferm"
    assert join_import_syllables(
        ["Licht", "aan"], ["single", "single"]
    ) == "Licht aan"


def test_pair_of_same_pitch_lyrics_does_not_collapse_to_recite():
    """Exactly two same-pitch syllables (e.g. we/gen) stay separate positions."""
    xml = _satb_score_xml(
        {
            "P1": """\
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>-1</fifths></key></attributes>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>2</duration><type>half</type>
        <lyric number="1"><syllabic>middle</syllabic><text>we</text></lyric>
      </note>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>2</duration><type>half</type>
        <lyric number="1"><syllabic>end</syllabic><text>gen</text></lyric>
      </note>
    </measure>""",
            "P2": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>2</duration><type>half</type></note>
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>2</duration><type>half</type></note>
    </measure>""",
            "P3": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>2</duration><type>half</type></note>
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>2</duration><type>half</type></note>
    </measure>""",
            "P4": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>G</step><octave>3</octave></pitch><duration>2</duration><type>half</type></note>
      <note><pitch><step>G</step><octave>3</octave></pitch><duration>2</duration><type>half</type></note>
    </measure>""",
        }
    )
    score = parse_musicxml_satb(xml)
    text = score_to_mvsa(score, pitch_form="abc")
    l_line = next(ln for ln in text.splitlines() if ln.startswith("L:"))
    assert "(we" not in l_line
    assert "(we-gen)" not in l_line
    assert "we" in l_line and "gen" in l_line
    diags = validate_mvsa_text(text)
    assert not [d for d in diags if d.severity == "error"], (diags, text)


def test_simple_flanks_absorb_into_multi_syllable_underlay_recite():
    """Ver + underlay + met on one pitch → one recite (MuseScore underlay)."""
    xml = _satb_score_xml(
        {
            "P1": """\
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>-1</fifths></key></attributes>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>Ver</text></lyric>
      </note>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic>
          <text>vuld zij on-ze mond</text></lyric>
      </note>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>met</text></lyric>
      </note>
      <note>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>Uw</text></lyric>
      </note>
    </measure>""",
            "P2": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
    </measure>""",
            "P3": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
    </measure>""",
            "P4": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>G</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>G</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>G</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>G</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
    </measure>""",
        }
    )
    score = parse_musicxml_satb(xml)
    text = score_to_mvsa(score, pitch_form="abc")
    l_line = next(ln for ln in text.splitlines() if ln.startswith("L:"))
    first = l_line.split("|", 1)[0]
    assert "Ver~" not in first
    assert "met~" not in first
    assert "(Ver-vuld zij on-ze mond met)" in first
    assert "Uw~" in first or "Uw" in first
    s_line = next(ln for ln in text.splitlines() if ln.startswith("S:"))
    assert re.search(r"Bb4\s+c5", s_line)
    diags = validate_mvsa_text(text)
    assert not [d for d in diags if d.severity == "error"], (diags, text)


def test_same_pitch_syllabic_run_collapses_like_musescore_recite():
    """MuseScore-style expanded recite (same pitch + syllabic) → one ``( … )``."""
    # Mimics wij-hebben opening: six Bb quarters then half Licht / aan / schouwd.
    s_notes = """\
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>-1</fifths></key></attributes>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>Wij</text></lyric>
      </note>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>begin</syllabic><text>heb</text></lyric>
      </note>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>middle</syllabic><text>ben</text></lyric>
      </note>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>middle</syllabic><text>het</text></lyric>
      </note>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>end</syllabic><text>wa</text></lyric>
      </note>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>re</text></lyric>
      </note>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>2</duration><type>half</type>
        <lyric number="1"><syllabic>single</syllabic><text>Licht</text></lyric>
      </note>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>2</duration><type>half</type>
        <lyric number="1"><syllabic>begin</syllabic><text>aan</text></lyric>
      </note>
      <note>
        <pitch><step>B</step><alter>-1</alter><octave>4</octave></pitch>
        <duration>2</duration><type>half</type>
        <lyric number="1"><syllabic>end</syllabic><text>schouwd</text></lyric>
      </note>
    </measure>"""

    def held(step: str, oct_: str, alter: str | None = None) -> str:
        alt = f"<alter>{alter}</alter>" if alter else ""
        notes = []
        for _ in range(6):
            notes.append(
                f"<note><pitch><step>{step}</step>{alt}"
                f"<octave>{oct_}</octave></pitch>"
                f"<duration>1</duration><type>quarter</type></note>"
            )
        notes.append(
            f"<note><pitch><step>{step}</step>{alt}"
            f"<octave>{oct_}</octave></pitch>"
            f"<duration>2</duration><type>half</type></note>"
        )
        # aan / schouwd counterparts (pitch steps for A/T/B ignored for sync)
        notes.append(
            f"<note><pitch><step>{step}</step>{alt}"
            f"<octave>{oct_}</octave></pitch>"
            f"<duration>2</duration><type>half</type></note>"
        )
        notes.append(
            f"<note><pitch><step>{step}</step>{alt}"
            f"<octave>{oct_}</octave></pitch>"
            f"<duration>2</duration><type>half</type></note>"
        )
        return (
            '<measure number="1">'
            "<attributes><divisions>1</divisions></attributes>"
            + "".join(notes)
            + "</measure>"
        )

    xml = _satb_score_xml(
        {
            "P1": s_notes,
            "P2": held("G", "4"),
            "P3": held("D", "4"),
            "P4": held("G", "3"),
        }
    )
    score = parse_musicxml_satb(xml)
    text = score_to_mvsa(score, pitch_form="abc", system_soft_width=200)
    l_line = next(ln for ln in text.splitlines() if ln.startswith("L:"))
    s_line = next(ln for ln in text.splitlines() if ln.startswith("S:"))
    first_l = l_line.split("|", 1)[0]
    first_s = s_line.split("|", 1)[0]
    # Six Bb lyric notes → one recite with repaired word boundaries.
    assert "(Wij heb-ben het wa-re)" in first_l
    assert "heb-ben-het-wa" not in first_l
    assert "Licht_" in first_l
    assert "aan_" in first_l
    assert "-schouwd_" in first_l or "schouwd_" in first_l
    assert "Wij~" not in first_l
    assert "heb~" not in first_l
    assert re.search(r"Bb4\s+-\s+a4\s+Bb4", first_s) or re.search(
        r"Bb4\s+a4\s+Bb4", first_s
    )
    diags = validate_mvsa_text(text)
    assert not [d for d in diags if d.severity == "error"], (diags, text)


def test_word_split_across_barline_between_two_recites():
    """One word (wa-re) in two recites separated by a barline → ``)-`` link."""

    def voice_meas(
        number: int,
        step: str,
        oct_: str,
        *,
        lyric: str = "",
        alter: str | None = None,
        attrs: bool = False,
    ) -> str:
        alt = f"<alter>{alter}</alter>" if alter else ""
        key = (
            "<attributes><divisions>1</divisions>"
            "<key><fifths>-1</fifths></key></attributes>\n      "
            if attrs
            else ""
        )
        ly = (
            f'<lyric number="1"><syllabic>single</syllabic>'
            f"<text>{lyric}</text></lyric>"
            if lyric
            else ""
        )
        return f"""\
    <measure number="{number}">
      {key}<note>
        <pitch><step>{step}</step>{alt}<octave>{oct_}</octave></pitch>
        <duration>4</duration><type>whole</type>
        {ly}
      </note>
    </measure>"""

    # Measure 1: multi-syllable underlay ending mid-word ``wa``;
    # measure 2: ``re`` as its own underlay/recite on same pitch.
    xml = _satb_score_xml(
        {
            "P1": voice_meas(
                1, "B", "4", lyric="foo wa", alter="-1", attrs=True
            )
            + "\n"
            # Space → multi-syllable underlay → second recite (not a bare syllable).
            + voice_meas(2, "B", "4", lyric="re meer", alter="-1"),
            "P2": voice_meas(1, "G", "4", lyric="", attrs=True)
            + "\n"
            + voice_meas(2, "G", "4", lyric=""),
            "P3": voice_meas(1, "D", "4", lyric="", attrs=True)
            + "\n"
            + voice_meas(2, "D", "4", lyric=""),
            "P4": voice_meas(1, "G", "3", lyric="", attrs=True)
            + "\n"
            + voice_meas(2, "G", "3", lyric=""),
        }
    )
    score = parse_musicxml_satb(xml)
    text = score_to_mvsa(score, pitch_form="abc", system_soft_width=200)
    l_line = next(ln for ln in text.splitlines() if ln.startswith("L:"))
    # Canonical: woordstreepje after first recite (ELM allowed before ``-``),
    # then second recite starting with the continuation syllable.
    compact = l_line.replace(" ", "")
    assert re.search(r"\(foowa\)[_.]*-\|\(re", compact)
    assert "(foo wa)" in l_line
    assert "(re" in l_line
    assert "wa-re" not in l_line  # not one recite across the bar
    diags = validate_mvsa_text(text)
    assert not [d for d in diags if d.severity == "error"], (diags, text)


def test_import_soft_wraps_systems():
    """Korte maten worden over meerdere LSATB-systemen verdeeld (~80 tekens)."""
    # Four identical short SATB measures → one system would exceed soft_width=35.
    parts = []
    for pid, step, oct_ in (
        ("P1", "G", "4"),
        ("P2", "E", "4"),
        ("P3", "C", "4"),
        ("P4", "C", "3"),
    ):
        body = []
        for n in range(1, 5):
            lyric = (
                '<lyric number="1"><syllabic>single</syllabic><text>Heer</text></lyric>'
                if pid == "P1"
                else ""
            )
            body.append(
                f"""\
    <measure number="{n}">
      <attributes><divisions>1</divisions><key><fifths>0</fifths></key></attributes>
      <note>
        <pitch><step>{step}</step><octave>{oct_}</octave></pitch>
        <duration>4</duration><type>whole</type>
        {lyric}
      </note>
    </measure>"""
            )
        parts.append(
            f'<part id="{pid}">\n' + "\n".join(body) + "\n  </part>"
        )
    xml = f"""\
<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <work><work-title>Wrap</work-title></work>
  <part-list>
    <score-part id="P1"><part-name>S</part-name></score-part>
    <score-part id="P2"><part-name>A</part-name></score-part>
    <score-part id="P3"><part-name>T</part-name></score-part>
    <score-part id="P4"><part-name>B</part-name></score-part>
  </part-list>
  {"".join(parts)}
</score-partwise>
"""
    score = parse_musicxml_satb(xml)
    text = score_to_mvsa(score, pitch_form="abc", system_soft_width=35)
    l_lines = [ln for ln in text.splitlines() if ln.startswith("L:")]
    assert len(l_lines) >= 2, (
        f"verwacht meerdere LSATB-systemen bij soft_width=35; kreeg {l_lines!r}"
    )
    assert l_lines[-1].rstrip().endswith("||")
    for ln in l_lines[:-1]:
        assert ln.rstrip().endswith("|")
        assert not ln.rstrip().endswith("||")
    diags = validate_mvsa_text(text)
    assert not [d for d in diags if d.severity == "error"], diags


def test_clean_lyric_hyphen_and_trailing_period():
    from vsa.mvsa_import import (
        _clean_import_lyric_text,
        _clean_recite_lyric_text,
        _lyric_looks_multi_syllable,
    )

    assert _clean_import_lyric_text("-") == ""
    assert _clean_import_lyric_text("  -  ") == ""
    assert _clean_import_lyric_text("ren.") == "ren"
    assert _clean_import_lyric_text("nen,") == "nen,"
    assert _clean_import_lyric_text("Wij") == "Wij"
    # Single-syllable cleaner still collapses hyphens if called directly.
    assert _clean_import_lyric_text("ko-nink-rijk") == "koninkrijk"

    assert _lyric_looks_multi_syllable("-") is False
    assert _lyric_looks_multi_syllable("Wij") is False
    assert _lyric_looks_multi_syllable("gen,") is False
    assert _lyric_looks_multi_syllable("ko-nink-rijk") is True
    assert _lyric_looks_multi_syllable("ons, die-tot U zin-gen: al") is True
    assert (
        _clean_recite_lyric_text("ons,  die-tot   U zin-gen: al")
        == "ons, die-tot U zin-gen: al"
    )


def test_multi_syllable_lyric_on_one_note_becomes_recite():
    """Multi-lettergreep underlay on one note → mvsa recite ``( … )``."""
    xml = _satb_score_xml(
        {
            "P1": """\
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>0</fifths></key></attributes>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic>
          <text>ons, die-tot U zin-gen: al</text></lyric>
      </note>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>le</text></lyric>
      </note>
      <note>
        <pitch><step>G</step><octave>4</octave></pitch>
        <duration>2</duration><type>half</type>
        <lyric number="1"><syllabic>single</syllabic><text>ja</text></lyric>
      </note>
    </measure>""",
            "P2": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>F</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>F</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>E</step><octave>4</octave></pitch><duration>2</duration><type>half</type></note>
    </measure>""",
            "P3": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>2</duration><type>half</type></note>
    </measure>""",
            "P4": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>F</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>F</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>C</step><octave>3</octave></pitch><duration>2</duration><type>half</type></note>
    </measure>""",
        }
    )
    score = parse_musicxml_satb(xml)
    text = score_to_mvsa(score, pitch_form="abc")
    l_line = next(ln for ln in text.splitlines() if ln.startswith("L:"))
    first = l_line.split("|", 1)[0]
    # Underlay repaired; same-pitch flank ``le`` absorbed; ``ja`` may link.
    assert "ons," in first
    assert "die-tot" in first or "die tot" in first
    assert "al" in first
    assert "onsdietotUzingenal" not in first
    assert "ja_" in first
    diags = validate_mvsa_text(text)
    assert not [d for d in diags if d.severity == "error"], (diags, text)


def test_default_soft_width_constant():
    assert DEFAULT_SYSTEM_SOFT_WIDTH == 80


def test_vsa_import_glues_absolute_eindanker_on_last_system_bar():
    """``--pitch vsa``: absolute toonhoogte als eindanker op laatste maatstreep."""

    def meas(step: str, oct_: str, *, lyric: str, number: int) -> str:
        attrs = (
            "<attributes><divisions>1</divisions>"
            "<key><fifths>0</fifths></key></attributes>\n      "
            if number == 1
            else ""
        )
        return f"""\
    <measure number="{number}">
      {attrs}<note>
        <pitch><step>{step}</step><octave>{oct_}</octave></pitch>
        <duration>4</duration><type>whole</type>
        <lyric number="1"><syllabic>single</syllabic><text>{lyric}</text></lyric>
      </note>
    </measure>"""

    # Two short measures → soft-width forces two systems; each stem ends with anker.
    xml = _satb_score_xml(
        {
            "P1": meas("G", "4", lyric="een", number=1)
            + "\n"
            + meas("A", "4", lyric="twee", number=2),
            "P2": meas("E", "4", lyric="", number=1)
            + "\n"
            + meas("F", "4", lyric="", number=2),
            "P3": meas("C", "4", lyric="", number=1)
            + "\n"
            + meas("D", "4", lyric="", number=2),
            "P4": meas("C", "3", lyric="", number=1)
            + "\n"
            + meas("D", "3", lyric="", number=2),
        }
    )
    score = parse_musicxml_satb(xml)
    # Soft width klein genoeg → één maat per systeem; elk systeem krijgt eindanker.
    text = score_to_mvsa(score, pitch_form="vsa", system_soft_width=12)
    s_lines = [ln for ln in text.splitlines() if ln.startswith("S:")]
    assert len(s_lines) == 2, text
    assert s_lines[0].rstrip().endswith("|g4"), s_lines[0]
    assert s_lines[1].rstrip().endswith("||a4"), s_lines[1]
    a_lines = [ln for ln in text.splitlines() if ln.startswith("A:")]
    assert a_lines[0].rstrip().endswith("|e4"), a_lines[0]
    assert a_lines[1].rstrip().endswith("||f4"), a_lines[1]
    l_lines = [ln for ln in text.splitlines() if ln.startswith("L:")]
    assert len(l_lines) == 2
    for ln in l_lines:
        assert not re.search(r"\|[a-gA-G#b]+\d", ln), ln

    # doremi / abc: geen eindankers
    for form in ("doremi", "abc"):
        other = score_to_mvsa(score, pitch_form=form, system_soft_width=12)
        for ln in other.splitlines():
            if ln.startswith(("S:", "A:", "T:", "B:")):
                assert not re.search(r"\|[a-gA-G#b]+\d", ln), (form, ln)

    diags = validate_mvsa_text(text)
    assert not [d for d in diags if d.severity == "error"], (diags, text)


def test_roundtrip_mvsa_mxl_mvsa_pitch_vsa(tmp_path: Path):
    text = ALLELUIA.read_text(encoding="utf-8")
    section = "schets3-oct-doremi"
    before = export_mvsa_to_musicxml(text, section_id=section)
    mxl = tmp_path / "schets2.mxl"
    write_musicxml_output(mxl, before)

    imported = import_score_to_mvsa(mxl, pitch="vsa", octave_style="@oct")
    diags = validate_mvsa_text(imported)
    assert not [d for d in diags if d.severity == "error"], diags
    # Elke stemregel eindigt met absolute eindanker (laatste systeem).
    for letter in "SATB":
        last = [ln for ln in imported.splitlines() if ln.startswith(f"{letter}:")][-1]
        assert re.search(r"\|\|[a-gA-G#b]+\d\s*$", last), last

    after = export_mvsa_to_musicxml(imported)
    assert _all_pitches(before) == _all_pitches(after)


def _satb_score_xml(measure_body_by_part: dict[str, str], *, title: str = "Proef") -> str:
    """Build minimal SATB MusicXML from per-part measure inner XML."""
    part_list = "\n".join(
        f'    <score-part id="{pid}"><part-name>{name}</part-name></score-part>'
        for pid, name in (("P1", "S"), ("P2", "A"), ("P3", "T"), ("P4", "B"))
    )
    parts = []
    for pid in ("P1", "P2", "P3", "P4"):
        parts.append(
            f'  <part id="{pid}">\n{measure_body_by_part[pid]}\n  </part>'
        )
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <work><work-title>{title}</work-title></work>
  <part-list>
{part_list}
  </part-list>
{chr(10).join(parts)}
</score-partwise>
"""


def test_soft_hyphen_lyric_becomes_recite_one_l_position():
    """Soft-hyphen multi-lettergreep on one note → recite, still one L-positie."""
    def meas(step: str, oct_: str, *, lyric: str = "") -> str:
        ly = (
            f'<lyric number="1"><syllabic>single</syllabic>'
            f"<text>{lyric}</text></lyric>"
            if lyric
            else ""
        )
        return f"""\
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>0</fifths></key></attributes>
      <note>
        <pitch><step>{step}</step><octave>{oct_}</octave></pitch>
        <duration>4</duration><type>whole</type>
        {ly}
      </note>
    </measure>"""

    xml = _satb_score_xml(
        {
            "P1": meas("G", "4", lyric="ko-nink-rijk"),
            "P2": meas("E", "4"),
            "P3": meas("C", "4"),
            "P4": meas("C", "3"),
        }
    )
    score = parse_musicxml_satb(xml)
    text = score_to_mvsa(score, pitch_form="abc")
    l_line = next(ln for ln in text.splitlines() if ln.startswith("L:"))
    assert "(ko-nink-rijk)__" in l_line.replace(" ", "") or "(ko-nink-rijk)__" in l_line
    assert "koninkrijk__" not in l_line.replace(" ", "")
    diags = validate_mvsa_text(text)
    assert not [d for d in diags if d.severity == "error"], diags


def test_hyphen_extender_and_trailing_period_lyrics_validate():
    """Extender ``-`` → ``()…``; trailing ``.`` stripped so ELM blijft syncen."""
    xml = _satb_score_xml(
        {
            "P1": """\
    <measure number="1">
      <attributes><divisions>2</divisions><key><fifths>0</fifths></key></attributes>
      <note>
        <pitch><step>E</step><octave>4</octave></pitch>
        <duration>4</duration><type>half</type>
        <lyric number="1"><syllabic>end</syllabic><text>ren.</text></lyric>
      </note>
      <note>
        <pitch><step>E</step><octave>4</octave></pitch>
        <duration>2</duration><type>quarter</type>
        <lyric number="1"><syllabic>begin</syllabic><text>Al</text></lyric>
      </note>
      <note>
        <pitch><step>F</step><octave>4</octave></pitch>
        <duration>1</duration><type>eighth</type>
        <lyric number="1"><syllabic>end</syllabic><text>le</text></lyric>
      </note>
      <note>
        <pitch><step>G</step><octave>4</octave></pitch>
        <duration>1</duration><type>eighth</type>
        <lyric number="1"><syllabic>single</syllabic><text>-</text></lyric>
      </note>
    </measure>""",
            "P2": """\
    <measure number="1">
      <attributes><divisions>2</divisions></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration><type>half</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>2</duration><type>quarter</type></note>
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>1</duration><type>eighth</type></note>
      <note><pitch><step>E</step><octave>4</octave></pitch><duration>1</duration><type>eighth</type></note>
    </measure>""",
            "P3": """\
    <measure number="1">
      <attributes><divisions>2</divisions></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration><type>half</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>2</duration><type>quarter</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>eighth</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>eighth</type></note>
    </measure>""",
            "P4": """\
    <measure number="1">
      <attributes><divisions>2</divisions></attributes>
      <note><pitch><step>C</step><octave>3</octave></pitch><duration>4</duration><type>half</type></note>
      <note><pitch><step>C</step><octave>3</octave></pitch><duration>2</duration><type>quarter</type></note>
      <note><pitch><step>C</step><octave>3</octave></pitch><duration>1</duration><type>eighth</type></note>
      <note><pitch><step>C</step><octave>3</octave></pitch><duration>1</duration><type>eighth</type></note>
    </measure>""",
        }
    )
    score = parse_musicxml_satb(xml)
    text = score_to_mvsa(score, pitch_form="abc")
    l_line = next(ln for ln in text.splitlines() if ln.startswith("L:"))
    first = l_line.split("|", 1)[0]
    assert "-ren_" in first or "ren_" in first.replace(" ", "")
    assert "()." in first.replace(" ", "") or "()." in first
    # No bare extender hyphen left as syllable text.
    assert " -." not in first and not first.rstrip().endswith(" -.")
    diags = validate_mvsa_text(text)
    assert not [d for d in diags if d.severity == "error"], (diags, text)


def test_lyricless_leading_notes_emit_empty_recite():
    """Notes without lyrics → empty recite ``()~``, not bare ``~``."""
    xml = _satb_score_xml(
        {
            "P1": """\
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>0</fifths></key></attributes>
      <note>
        <pitch><step>G</step><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
      </note>
      <note>
        <pitch><step>F</step><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>ons</text></lyric>
      </note>
      <note>
        <pitch><step>E</step><octave>4</octave></pitch>
        <duration>2</duration><type>half</type>
        <lyric number="1"><syllabic>single</syllabic><text>nu</text></lyric>
      </note>
    </measure>""",
            "P2": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>E</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>2</duration><type>half</type></note>
    </measure>""",
            "P3": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>B</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>2</duration><type>half</type></note>
    </measure>""",
            "P4": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>G</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>G</step><octave>3</octave></pitch><duration>1</duration><type>quarter</type></note>
      <note><pitch><step>C</step><octave>3</octave></pitch><duration>2</duration><type>half</type></note>
    </measure>""",
        }
    )
    score = parse_musicxml_satb(xml)
    text = score_to_mvsa(score, pitch_form="abc")
    l_line = next(ln for ln in text.splitlines() if ln.startswith("L:"))
    first = l_line.split("|", 1)[0]
    assert "()~" in first
    assert "ons~" in first and "nu_" in first
    assert re.search(r"(^| )~ ons", first) is None
    diags = validate_mvsa_text(text)
    assert not [d for d in diags if d.severity == "error"], (diags, text)


def test_import_writes_canonical_default_tilde():
    """Canonieke normaalvorm: standaard-kwart op L als ``~`` (ook lone)."""
    from vsa.mvsa_import import _l_duration_suffix

    assert _l_duration_suffix(["~"]) == "~"
    assert _l_duration_suffix(["_"]) == "_"
    assert _l_duration_suffix(["~", "~"]) == "~&~"
    assert _l_duration_suffix([".", "."]) == ".&."


def test_chord_tones_do_not_create_extra_slots():
    """``<chord/>`` notes share onset — not a new melisma slot."""
    xml = _satb_score_xml(
        {
            "P1": """\
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>0</fifths></key></attributes>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>4</duration><type>whole</type>
        <lyric number="1"><syllabic>single</syllabic><text>Heer</text></lyric>
      </note>
      <note>
        <chord/>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>4</duration><type>whole</type>
      </note>
    </measure>""",
            "P2": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>F</step><octave>4</octave></pitch><duration>4</duration><type>whole</type></note>
    </measure>""",
            "P3": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration><type>whole</type></note>
    </measure>""",
            "P4": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>F</step><octave>3</octave></pitch><duration>4</duration><type>whole</type></note>
    </measure>""",
        }
    )
    score = parse_musicxml_satb(xml)
    assert len(score.parts["S"][0]) == 1
    text = score_to_mvsa(score, pitch_form="abc")
    s_line = next(ln for ln in text.splitlines() if ln.startswith("S:"))
    assert "&" not in s_line.split("|", 1)[0]
    diags = validate_mvsa_text(text)
    assert not [d for d in diags if d.severity == "error"], diags


def test_single_long_measure_stays_one_system():
    """Eén maat langer dan soft_width blijft één LSATB-systeem."""
    # Lange lettergrepen in één maat → L-regel > soft_width; toch één systeem.
    lyrics = [
        "Alleluia",
        "cherubijnen",
        "geheimnisvol",
        "uitbeelden",
        "levenschenkende",
        "Drieeenheid",
    ]
    notes_s = []
    notes_other = []
    for syl in lyrics:
        notes_s.append(
            f"""\
      <note>
        <pitch><step>G</step><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>{syl}</text></lyric>
      </note>"""
        )
        notes_other.append(
            """\
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration><type>quarter</type>
      </note>"""
        )
    meas = (
        '    <measure number="1">\n'
        "      <attributes><divisions>1</divisions>"
        "<key><fifths>0</fifths></key></attributes>\n"
        "{body}\n"
        "    </measure>"
    )
    xml = _satb_score_xml(
        {
            "P1": meas.format(body="\n".join(notes_s)),
            "P2": meas.format(body="\n".join(notes_other)),
            "P3": meas.format(body="\n".join(notes_other)),
            "P4": meas.format(
                body="\n".join(
                    n.replace("<octave>4</octave>", "<octave>3</octave>")
                    for n in notes_other
                )
            ),
        }
    )
    score = parse_musicxml_satb(xml)
    text = score_to_mvsa(score, pitch_form="abc", system_soft_width=40)
    l_lines = [ln for ln in text.splitlines() if ln.startswith("L:")]
    assert len(l_lines) == 1
    assert len(l_lines[0]) > 40
    assert l_lines[0].rstrip().endswith("||")
    diags = validate_mvsa_text(text)
    assert not [d for d in diags if d.severity == "error"], diags


def test_import_without_align_stays_valid(tmp_path: Path):
    """Default align mag; zonder align moet sync-telling sowieso kloppen."""
    text = ALLELUIA.read_text(encoding="utf-8")
    mxl_xml = export_mvsa_to_musicxml(text, section_id="schets3-oct-doremi")
    mxl = tmp_path / "alleluia.mxl"
    write_musicxml_output(mxl, mxl_xml)
    imported = import_score_to_mvsa(mxl, pitch="abc", align=False)
    diags = validate_mvsa_text(imported)
    assert not [d for d in diags if d.severity == "error"], diags
    assert sum(1 for ln in imported.splitlines() if ln.startswith("L:")) >= 1


def test_import_default_runs_kuiser_normaalvorm(tmp_path: Path):
    """Default import: kuiser-normaalvorm (canonieke ``~`` + kolomalign)."""
    from vsa.mvsa_kuiser import kuiser_mvsa_text

    text = ALLELUIA.read_text(encoding="utf-8")
    mxl_xml = export_mvsa_to_musicxml(text, section_id="schets3-oct-doremi")
    mxl = tmp_path / "alleluia.mxl"
    write_musicxml_output(mxl, mxl_xml)
    imported = import_score_to_mvsa(mxl, pitch="abc", align=True)
    again = kuiser_mvsa_text(imported, pitch="preserve", align=True).text
    assert imported == again  # idempotent normaalvorm
    l_line = next(ln for ln in imported.splitlines() if ln.startswith("L:"))
    assert "~" in l_line
    diags = validate_mvsa_text(imported)
    assert not [d for d in diags if d.severity == "error"], diags


def test_do_from_fifths_circle():
    assert do_from_fifths(0) == "C4"
    assert do_from_fifths(-1) == "F4"
    assert do_from_fifths(1) == "G4"
    assert do_from_fifths(-2) == "Bb4"


def test_musicxml_fifths_sets_at_do():
    xml = _satb_score_xml(
        {
            "P1": """\
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>-1</fifths></key></attributes>
      <note>
        <pitch><step>F</step><octave>4</octave></pitch>
        <duration>4</duration><type>whole</type>
        <lyric number="1"><syllabic>single</syllabic><text>Heer</text></lyric>
      </note>
    </measure>""",
            "P2": """\
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>-1</fifths></key></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration><type>whole</type></note>
    </measure>""",
            "P3": """\
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>-1</fifths></key></attributes>
      <note><pitch><step>A</step><octave>3</octave></pitch><duration>4</duration><type>whole</type></note>
    </measure>""",
            "P4": """\
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>-1</fifths></key></attributes>
      <note><pitch><step>F</step><octave>3</octave></pitch><duration>4</duration><type>whole</type></note>
    </measure>""",
        }
    )
    score = parse_musicxml_satb(xml)
    assert score.do == "F4"
    text = score_to_mvsa(score, pitch_form="abc")
    assert "@do F4" in text


def test_import_do_cli_overrides_fifths(tmp_path: Path):
    xml = _satb_score_xml(
        {
            "P1": """\
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>0</fifths></key></attributes>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>4</duration><type>whole</type>
        <lyric number="1"><syllabic>single</syllabic><text>Heer</text></lyric>
      </note>
    </measure>""",
            "P2": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>G</step><octave>3</octave></pitch><duration>4</duration><type>whole</type></note>
    </measure>""",
            "P3": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>E</step><octave>3</octave></pitch><duration>4</duration><type>whole</type></note>
    </measure>""",
            "P4": """\
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>C</step><octave>3</octave></pitch><duration>4</duration><type>whole</type></note>
    </measure>""",
        }
    )
    mxl = tmp_path / "c-major.mxl"
    write_musicxml_output(mxl, xml)
    imported = import_score_to_mvsa(mxl, pitch="abc", do="F4")
    assert "@do F4" in imported
    assert "@do C4" not in imported


def test_read_mscz_key_fifths_from_template_and_wij_hebben():
    template = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "specification-vsa-templates"
        / "library"
        / "tropaar-toon-4"
        / "examples"
        / "corpus"
        / "T4-01-johannes-voorloper.mscz"
    )
    wij = EXAMPLES / "wij-hebben" / "wij-hebben-het-ware-licht-default-hemelum.mscz"
    assert template.is_file()
    assert wij.is_file()
    assert read_mscz_key_fifths(template) == -1
    assert do_from_fifths(read_mscz_key_fifths(template)) == "F4"
    # Hemelum-bron heeft geen KeySig in de .mscx → None (geen gok).
    assert read_mscz_key_fifths(wij) is None
