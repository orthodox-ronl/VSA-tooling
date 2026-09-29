"""Tests for audio export (format resolution + MuseScore path)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from vsa.audio_export import (
    DEFAULT_AUDIO_FORMAT,
    AudioExportError,
    export_musicxml_to_audio,
    export_to_audio,
    normalize_audio_format,
    resolve_audio_output_path,
)
from vsa.config import load_config
from vsa.musescore_cli import MuseScoreNotFoundError, find_musescore
from vsa.musicxml_package import write_musicxml_output

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
OEFEN = EXAMPLES / "docs-walkthroughs" / "coria-oefenlink" / "oefenmelodie.vsa"
ALLELUIA = EXAMPLES / "mvsa" / "test-alleluia-toon-8.mvsa"
MUSESCORE = find_musescore()

_MINIMAL_MUSICXML = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC
  "-//Recordare//DTD MusicXML 3.1 Partwise//EN"
  "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1">
      <part-name>Music</part-name>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>4</duration>
        <type>whole</type>
      </note>
    </measure>
  </part>
</score-partwise>
"""


def test_normalize_audio_format_default():
    assert normalize_audio_format(None) == DEFAULT_AUDIO_FORMAT
    assert normalize_audio_format("") == "mp3"
    assert normalize_audio_format("MP3") == "mp3"
    assert normalize_audio_format(".ogg") == "ogg"


def test_normalize_audio_format_rejects_unknown():
    with pytest.raises(AudioExportError, match="Onbekend audioformaat"):
        normalize_audio_format("flac")


def test_resolve_audio_output_path_adds_suffix(tmp_path: Path):
    assert resolve_audio_output_path(tmp_path / "a").suffix == ".mp3"
    assert resolve_audio_output_path(tmp_path / "a", format_name="ogg").suffix == ".ogg"
    assert resolve_audio_output_path(tmp_path / "a.wav").name == "a.wav"
    assert resolve_audio_output_path(tmp_path / "a.WAV").name == "a.WAV"


def test_config_loads_audio_format(tmp_path: Path):
    config_file = tmp_path / "vsa.toml"
    config_file.write_text('[audio]\nformat = "ogg"\n', encoding="utf-8")
    config = load_config(config_file)
    assert config.audio.format == "ogg"


def test_config_rejects_invalid_audio_format(tmp_path: Path):
    config_file = tmp_path / "vsa.toml"
    config_file.write_text('[audio]\nformat = "flac"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="audio.format"):
        load_config(config_file)


def test_export_musicxml_without_musescore_raises(tmp_path: Path):
    mxl = tmp_path / "score.mxl"
    write_musicxml_output(mxl, _MINIMAL_MUSICXML)
    out = tmp_path / "out.mp3"
    with patch(
        "vsa.audio_export.convert_with_musescore",
        side_effect=MuseScoreNotFoundError("x"),
    ):
        with pytest.raises(AudioExportError, match="x"):
            export_musicxml_to_audio(mxl, out)


def test_export_rejects_unknown_suffix(tmp_path: Path):
    src = tmp_path / "x.pdf"
    src.write_bytes(b"%PDF")
    with pytest.raises(AudioExportError, match="verwacht"):
        export_to_audio(src, tmp_path / "out.mp3")


@pytest.mark.skipif(MUSESCORE is None, reason="MuseScore niet geïnstalleerd")
def test_export_minimal_mxl_to_mp3(tmp_path: Path):
    mxl = tmp_path / "score.mxl"
    write_musicxml_output(mxl, _MINIMAL_MUSICXML)
    out = tmp_path / "score.mp3"
    written = export_musicxml_to_audio(mxl, out)
    assert written == out
    assert out.is_file()
    assert out.stat().st_size > 100


@pytest.mark.skipif(MUSESCORE is None, reason="MuseScore niet geïnstalleerd")
def test_export_vsa_to_mp3(tmp_path: Path):
    assert OEFEN.is_file()
    out = tmp_path / "oefenmelodie.mp3"
    keep = tmp_path / "oefenmelodie.mxl"
    written = export_to_audio(OEFEN, out, keep_mxl=keep)
    assert written == out
    assert out.is_file()
    assert out.stat().st_size > 500
    assert keep.is_file()


@pytest.mark.skipif(MUSESCORE is None, reason="MuseScore niet geïnstalleerd")
def test_export_mvsa_section_to_mp3(tmp_path: Path):
    assert ALLELUIA.is_file()
    out = tmp_path / "alleluia.mp3"
    written = export_to_audio(
        ALLELUIA,
        out,
        section_id="schets3-oct-doremi",
    )
    assert written == out
    assert out.is_file()
    assert out.stat().st_size > 500
