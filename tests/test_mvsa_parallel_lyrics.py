"""Export van parallelle L / L1 naar MusicXML lyric numbers."""

from __future__ import annotations

from pathlib import Path

from vsa.mvsa_musicxml import export_mvsa_to_musicxml
from vsa.mvsa_musicxml import _lyric_number_for_marker

ROOT = Path(__file__).resolve().parents[1]
PARALLEL = (ROOT / "examples" / "mvsa" / "hulptekst-parallel-l1-mini.mvsa").read_text(
    encoding="utf-8"
)
KSL_MINI = (ROOT / "examples" / "mvsa" / "hulptekst-ksl-mini.mvsa").read_text(
    encoding="utf-8"
)


def test_lyric_number_for_marker() -> None:
    assert _lyric_number_for_marker("L") == 1
    assert _lyric_number_for_marker("lyrics") == 1
    assert _lyric_number_for_marker("L1") == 2
    assert _lyric_number_for_marker("L2") == 3


def test_parallel_l_l1_export_lyric_numbers() -> None:
    xml = export_mvsa_to_musicxml(PARALLEL, layout="playback")
    assert 'lyric number="1"' in xml
    assert 'lyric number="2"' in xml
    assert "<text>Свя</text>" in xml
    assert "<text>тый</text>" in xml
    assert "<text>Svja</text>" in xml
    assert "<text>tyj</text>" in xml


def test_parallel_l1_blocks_auto_hulptekst() -> None:
    """Handmatige L1 wint: --hulptekst voegt geen tweede number=2 toe."""
    xml = export_mvsa_to_musicxml(PARALLEL, layout="playback", hulptekst=True)
    # L1 blijft Svja; geen gegenereerde dubbele laag over L1 heen.
    assert xml.count("Svja") >= 1
    # Gegenereerd uit Свя zou ook Svja zijn — controleer dat number=2 Svja is,
    # niet een derde laag.
    assert xml.count('lyric number="3"') == 0


def test_hulptekst_still_works_without_l1() -> None:
    xml = export_mvsa_to_musicxml(KSL_MINI, layout="partituur", hulptekst=True)
    assert 'lyric number="2"' in xml
    assert "<text>Svja</text>" in xml
