"""Integratietests: hulptekst lyric number 2 en Coria-dubbelparts."""

from __future__ import annotations

from pathlib import Path

import pytest

from vsa.mvsa_musicxml import MvsaExportError, export_mvsa_to_musicxml

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "mvsa"

KSL_MINI = (EXAMPLES / "hulptekst-ksl-mini.mvsa").read_text(encoding="utf-8")
NL_MINI = (EXAMPLES / "hulptekst-nl-mini.mvsa").read_text(encoding="utf-8")


def test_ksl_partituur_lyric_number_2() -> None:
    xml = export_mvsa_to_musicxml(
        KSL_MINI, layout="partituur", hulptekst=True
    )
    assert 'lyric number="1"' in xml
    assert 'lyric number="2"' in xml
    assert "<text>Свя</text>" in xml or "<text>Свя" in xml
    assert "<text>Svja</text>" in xml
    assert "<text>Bo</text>" in xml
    assert "<text>zje</text>" in xml


def test_nl_playback_lyric_number_2() -> None:
    xml = export_mvsa_to_musicxml(NL_MINI, layout="playback", hulptekst=True)
    assert 'lyric number="2"' in xml
    assert "<text>Хер</text>" in xml
    assert "<text>онт</text>" in xml
    assert "<text>ферм</text>" in xml
    assert "<text>У</text>" in xml


def test_hulptekst_as_parts_playback() -> None:
    xml = export_mvsa_to_musicxml(
        KSL_MINI, layout="playback", hulptekst_as_parts=True
    )
    assert 'id="P5"' in xml
    assert "Soprano (hulptekst)" in xml
    assert "<volume>0</volume>" in xml
    # Bronparts behouden lyric 1 + 2; hulptekst-parts hebben Svja als number 1.
    assert xml.count("Svja") >= 2


def test_hulptekst_as_parts_rejects_partituur() -> None:
    with pytest.raises(MvsaExportError, match="playback"):
        export_mvsa_to_musicxml(
            KSL_MINI, layout="partituur", hulptekst_as_parts=True
        )


def test_without_flag_no_lyric_2() -> None:
    xml = export_mvsa_to_musicxml(KSL_MINI, layout="playback")
    assert 'lyric number="2"' not in xml
