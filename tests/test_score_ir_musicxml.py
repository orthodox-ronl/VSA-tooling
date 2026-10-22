"""Score-IR → partituur MusicXML (OSMD-brug)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vsa.score_ir import export_mvsa_to_score_ir
from vsa.score_ir_musicxml import (
    ScoreIrMusicxmlError,
    export_score_ir_path_to_musicxml,
    score_ir_to_musicxml,
)

ROOT = Path(__file__).resolve().parents[1]
VREDE = ROOT / "examples" / "mvsa" / "1a-vredeslitanie.mvsa"


def test_score_ir_to_musicxml_has_cues_and_parts() -> None:
    doc = export_mvsa_to_score_ir(VREDE.read_text(encoding="utf-8"))
    xml = score_ir_to_musicxml(doc)
    assert 'score-partwise version="3.1"' in xml
    assert 'part id="P1"' in xml
    assert 'part id="P2"' in xml
    assert "Gezegend" in xml
    assert "<words" in xml
    assert "<lyric" in xml


def test_export_path_roundtrip(tmp_path: Path) -> None:
    from vsa.score_ir import export_mvsa_path_to_score_ir

    ir = tmp_path / "x.score-ir.json"
    mxl = tmp_path / "x.musicxml"
    export_mvsa_path_to_score_ir(VREDE, ir)
    export_score_ir_path_to_musicxml(ir, mxl)
    text = mxl.read_text(encoding="utf-8")
    assert "Gezegend" in text


def test_rejects_wrong_format() -> None:
    with pytest.raises(ScoreIrMusicxmlError, match="format"):
        score_ir_to_musicxml({"format": "nope", "profile": "partituur"})
