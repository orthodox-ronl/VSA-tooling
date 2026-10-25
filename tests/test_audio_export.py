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
from vsa.audio_trim import (
    encode_trimmed_audio,
    find_ffmpeg,
    last_audible_end_seconds,
    wav_duration_seconds,
    write_silent_padded_pcm16_fixture,
)
from vsa.config import load_config
from vsa.musescore_cli import MuseScoreNotFoundError, find_musescore
from vsa.musicxml_package import write_musicxml_output

FFMPEG = find_ffmpeg()

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


def test_last_audible_end_ignores_trailing_silence(tmp_path: Path):
    wav = tmp_path / "tone_then_silence.wav"
    write_silent_padded_pcm16_fixture(
        wav, tone_ms=100, silence_ms=800, rate=8000
    )
    end = last_audible_end_seconds(wav, threshold=0.01)
    dur = wav_duration_seconds(wav)
    assert 0.09 <= end <= 0.12
    assert dur == pytest.approx(0.9, abs=0.02)


@pytest.mark.skipif(FFMPEG is None, reason="ffmpeg niet geïnstalleerd")
def test_encode_trimmed_audio_cuts_trailing_silence(tmp_path: Path):
    src = tmp_path / "padded.wav"
    write_silent_padded_pcm16_fixture(
        src, tone_ms=100, silence_ms=800, rate=8000
    )
    out = tmp_path / "trimmed.wav"
    encode_trimmed_audio(src, out, pad_ms=10, threshold=0.01)
    dur = wav_duration_seconds(out)
    end = last_audible_end_seconds(out, threshold=0.01)
    assert dur == pytest.approx(0.11, abs=0.03)
    assert dur - end <= 0.05


@pytest.mark.skipif(
    MUSESCORE is None or FFMPEG is None,
    reason="MuseScore of ffmpeg niet geïnstalleerd",
)
def test_export_minimal_mxl_to_mp3(tmp_path: Path):
    mxl = tmp_path / "score.mxl"
    write_musicxml_output(mxl, _MINIMAL_MUSICXML)
    out = tmp_path / "score.mp3"
    written = export_musicxml_to_audio(mxl, out)
    assert written == out
    assert out.is_file()
    assert out.stat().st_size > 100


@pytest.mark.skipif(
    MUSESCORE is None or FFMPEG is None,
    reason="MuseScore of ffmpeg niet geïnstalleerd",
)
def test_export_minimal_mxl_wav_has_short_trailing_silence(tmp_path: Path):
    """Checklist A5: hoogstens ~50 ms stilte na laatste hoorbare sample."""
    mxl = tmp_path / "score.mxl"
    write_musicxml_output(mxl, _MINIMAL_MUSICXML)
    out = tmp_path / "score.wav"
    export_musicxml_to_audio(mxl, out, format_name="wav")
    dur = wav_duration_seconds(out)
    end = last_audible_end_seconds(out, threshold=0.01)
    assert dur > 0.5
    assert dur - end <= 0.05


@pytest.mark.skipif(
    MUSESCORE is None or FFMPEG is None,
    reason="MuseScore of ffmpeg niet geïnstalleerd",
)
def test_export_vsa_to_mp3(tmp_path: Path):
    assert OEFEN.is_file()
    out = tmp_path / "oefenmelodie.mp3"
    keep = tmp_path / "oefenmelodie.mxl"
    written = export_to_audio(OEFEN, out, keep_mxl=keep)
    assert written == out
    assert out.is_file()
    assert out.stat().st_size > 500
    assert keep.is_file()


@pytest.mark.skipif(
    MUSESCORE is None or FFMPEG is None,
    reason="MuseScore of ffmpeg niet geïnstalleerd",
)
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
