"""Tests for ``vsa text`` / plain lyric export (VSA, MVSA, MusicXML, MSCZ)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from vsa.cli import main
from vsa.musescore_cli import MuseScoreNotFoundError, find_musescore
from vsa.text_export import (
    plain_text_from_mscz,
    plain_text_from_musicxml,
    plain_text_from_mvsa,
    plain_text_from_path,
    plain_text_from_vsa,
)

_ANTIFOON_SNIPPET = """\
---
do: F4
mode: major
---

[:] Juich {/voor} {/God}, ge{\\he}{/le} {/aar__}{\\de_},
   {\\\\&/breng} {/lof} {\\aan} {\\Zijn} {/heer_}lijk{\\heid_}. [:]
"""

_MVSA_MINIMAL = """\
@title "Test"
@do F4
@mode major

L: Heilig God, ||
S: do re ||
A: do re ||
T: do re ||
B: do re ||
"""

_FIXTURE_MXL = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "specification-vsa-templates"
    / "library"
    / "tropaar-toon-4"
    / "examples"
    / "corpus"
    / "T4-01-johannes-voorloper.mxl"
)

MUSESCORE = find_musescore()


def test_vsa_plain_joins_scopes_and_strips_melisma_markup() -> None:
    text = plain_text_from_vsa(_ANTIFOON_SNIPPET)
    assert "Juich voor God" in text
    assert "gehele aarde" in text.replace(",", "")
    assert "{/" not in text
    assert "\\" not in text


def test_vsa_cli_text(tmp_path, capsys) -> None:
    path = tmp_path / "voorbeeld.vsa"
    path.write_text(_ANTIFOON_SNIPPET, encoding="utf-8")
    assert main(["text", str(path)]) == 0
    out = capsys.readouterr().out
    assert "Juich voor God" in out


def test_mvsa_plain_joins_measures() -> None:
    text = plain_text_from_mvsa(_MVSA_MINIMAL)
    assert "Heilig" in text
    assert "God" in text


def test_mvsa_recite_group_does_not_glue_next_word() -> None:
    """``(hei-li-ge) Sterke`` mag niet ``heiligeSterke`` worden."""
    src = """\
@do G4
@mode major

L: (hei-li-ge) Ster~&~&~-ke_. ||
S: f#4          a4&b4&c5  b4   ||
A: d#4          f#4&g4&a4 g4   ||
T: b3           d4&-&-    d4   ||
B: b2           d3&-&-    g3   ||
"""
    text = plain_text_from_mvsa(src)
    assert "heilige Sterke" in text
    assert "heiligeSterke" not in text


def test_vsa_bare_ehm_not_in_plain_text() -> None:
    src = """\
---
do: F4
mode: major
---
God_, // om aan de wereld te schenken
"""
    text = plain_text_from_vsa(src)
    assert "//" not in text
    assert "God" in text
    assert "om aan de wereld" in text


def test_hard_hyphen_equals_becomes_visible_dash() -> None:
    vsa = """\
---
do: F4
mode: major
---
het mede=eeuwige woord
"""
    assert "mede-eeuwige" in plain_text_from_vsa(vsa)

    mvsa = """\
@do F4
@mode major

L: mede=eeu-wi-ge ||
S: do re mi fa ||
A: do re mi fa ||
T: do re mi fa ||
B: do re mi fa ||
"""
    text = plain_text_from_mvsa(mvsa)
    assert "mede-eeuwige" in text
    assert "=" not in text


_MUSICXML_SYLLABICS = """\
<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list>
    <score-part id="P1"><part-name>S</part-name></score-part>
    <score-part id="P2"><part-name>A</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <note>
        <pitch><step>F</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1">
          <syllabic>begin</syllabic>
          <text>Hei</text>
        </lyric>
      </note>
      <note>
        <pitch><step>G</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1">
          <syllabic>middle</syllabic>
          <text>li</text>
        </lyric>
      </note>
      <note>
        <pitch><step>A</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1">
          <syllabic>end</syllabic>
          <text>ge</text>
        </lyric>
      </note>
      <note>
        <pitch><step>B</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1">
          <syllabic>single</syllabic>
          <text>God</text>
        </lyric>
      </note>
    </measure>
    <measure number="2">
      <note>
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1">
          <syllabic>begin</syllabic>
          <text>Heer</text>
        </lyric>
      </note>
      <note>
        <pitch><step>D</step><octave>5</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1">
          <syllabic>end</syllabic>
          <text>lijk</text>
        </lyric>
      </note>
    </measure>
  </part>
  <part id="P2">
    <measure number="1">
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1">
          <syllabic>begin</syllabic>
          <text>Hei</text>
        </lyric>
      </note>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1">
          <syllabic>middle</syllabic>
          <text>li</text>
        </lyric>
      </note>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1">
          <syllabic>end</syllabic>
          <text>ge</text>
        </lyric>
      </note>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1">
          <syllabic>single</syllabic>
          <text>God</text>
        </lyric>
      </note>
    </measure>
    <measure number="2">
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1">
          <syllabic>begin</syllabic>
          <text>Heer</text>
        </lyric>
      </note>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1">
          <syllabic>end</syllabic>
          <text>lijk</text>
        </lyric>
      </note>
    </measure>
  </part>
</score-partwise>
"""


def test_musicxml_joins_syllabics_across_measures() -> None:
    text = plain_text_from_musicxml(_MUSICXML_SYLLABICS)
    assert text == "Heilige God Heerlijk"


def test_musicxml_does_not_duplicate_satb_lyrics() -> None:
    """P2 heeft dezelfde lyrics; tekst mag niet twee keer voorkomen."""
    text = plain_text_from_musicxml(_MUSICXML_SYLLABICS)
    assert text.count("Heilige") == 1
    assert text.count("God") == 1


def test_musicxml_empty_score_returns_empty_string() -> None:
    xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list>
    <score-part id="P1"><part-name>S</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <note>
        <pitch><step>F</step><octave>4</octave></pitch>
        <duration>1</duration>
        <type>quarter</type>
      </note>
    </measure>
  </part>
</score-partwise>
"""
    assert plain_text_from_musicxml(xml) == ""


def test_musicxml_prefers_voice_1_within_part() -> None:
    xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list>
    <score-part id="P1"><part-name>SA</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <note>
        <pitch><step>F</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>1</voice>
        <type>quarter</type>
        <lyric number="1">
          <syllabic>single</syllabic>
          <text>Lead</text>
        </lyric>
      </note>
      <backup><duration>1</duration></backup>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>1</duration>
        <voice>2</voice>
        <type>quarter</type>
        <lyric number="1">
          <syllabic>single</syllabic>
          <text>Dup</text>
        </lyric>
      </note>
    </measure>
  </part>
</score-partwise>
"""
    assert plain_text_from_musicxml(xml) == "Lead"


def test_musicxml_skips_lyric_number_2() -> None:
    xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list>
    <score-part id="P1"><part-name>S</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <note>
        <pitch><step>F</step><octave>4</octave></pitch>
        <duration>1</duration>
        <type>quarter</type>
        <lyric number="1">
          <syllabic>single</syllabic>
          <text>Eerste</text>
        </lyric>
        <lyric number="2">
          <syllabic>single</syllabic>
          <text>Tweede</text>
        </lyric>
      </note>
    </measure>
  </part>
</score-partwise>
"""
    assert plain_text_from_musicxml(xml) == "Eerste"


def test_musicxml_fixture_corpus_mxl_not_duplicated() -> None:
    assert _FIXTURE_MXL.is_file()
    text = plain_text_from_path(_FIXTURE_MXL)
    assert "Profeet" in text or "profeet" in text.lower()
    # Corpus heeft lyrics op P1–P4; eerste part wint → geen verdubbeling.
    assert text.lower().count("profeet") == 1


def test_cli_text_musicxml_and_output_file(tmp_path, capsys) -> None:
    path = tmp_path / "lied.musicxml"
    path.write_text(_MUSICXML_SYLLABICS, encoding="utf-8")
    out = tmp_path / "lied.lyrics.txt"
    assert main(["text", str(path), "-o", str(out)]) == 0
    assert out.read_text(encoding="utf-8").strip() == "Heilige God Heerlijk"
    assert "Geschreven:" in capsys.readouterr().out


def test_cli_text_rejects_unknown_suffix(tmp_path, capsys) -> None:
    path = tmp_path / "lied.txt"
    path.write_text("x", encoding="utf-8")
    assert main(["text", str(path)]) == 1
    err = capsys.readouterr().err
    assert ".vsa" in err or "verwacht" in err


def test_plain_text_from_mscz_without_musescore_raises(tmp_path: Path) -> None:
    fake = tmp_path / "lied.mscz"
    fake.write_bytes(b"PK\x03\x04fake")
    with patch(
        "vsa.musescore_cli.convert_with_musescore",
        side_effect=MuseScoreNotFoundError("x"),
    ):
        with pytest.raises(MuseScoreNotFoundError):
            plain_text_from_mscz(fake)


@pytest.mark.skipif(MUSESCORE is None, reason="MuseScore niet geïnstalleerd")
def test_mscz_text_via_temp_mxl_optional(tmp_path: Path) -> None:
    """Optioneel pad: .mscz → temp-mxl → plaintext (geen .mvsa-sibling)."""
    from vsa.mvsa_mscz import export_mvsa_to_mscz

    mvsa = Path(__file__).resolve().parents[1] / "examples" / "mvsa" / "test-alleluia-toon-8.mvsa"
    if not mvsa.is_file():
        pytest.skip("geen alleluia-fixture")
    mscz = tmp_path / "alleluia.mscz"
    try:
        export_mvsa_to_mscz(mvsa, mscz, section_id="schets3-oct-doremi")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"mscz-export mislukt: {exc}")
    text = plain_text_from_path(mscz)
    assert text
    assert not any(tmp_path.glob("*.mvsa"))
