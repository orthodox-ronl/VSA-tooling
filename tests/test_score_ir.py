"""Score-IR export (partituur profile)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vsa.score_ir import (
    SCORE_IR_FORMAT,
    SCORE_IR_PROFILE,
    SCORE_IR_VERSION,
    export_mvsa_path_to_score_ir,
    export_mvsa_to_score_ir,
)

ROOT = Path(__file__).resolve().parents[1]
VREDE = ROOT / "examples" / "mvsa" / "1a-vredeslitanie.mvsa"


def test_export_vredeslitanie_shape() -> None:
    text = VREDE.read_text(encoding="utf-8")
    doc = export_mvsa_to_score_ir(text)
    assert doc["format"] == SCORE_IR_FORMAT
    assert doc["version"] == SCORE_IR_VERSION
    assert doc["profile"] == SCORE_IR_PROFILE
    assert doc["pitchContext"]["do"] == "F4"
    assert doc["meta"]["title"]
    assert len(doc["measures"]) >= 2

    m1 = doc["measures"][0]
    assert m1["id"] == "m1"
    assert m1["cues"], "eerste maat hoort @tekst-cue te hebben"
    assert m1["cues"][0]["kind"] == "tekst"
    assert "Gezegend" in m1["cues"][0]["text"]
    assert m1["cues"][0]["anchor"] == "measure-start"
    assert m1["lyrics"], "lyrics op maat 1"
    for letter in ("S", "A", "T", "B"):
        assert letter in m1["voices"]
        assert m1["voices"][letter], f"stem {letter} leeg op m1"
        ev0 = m1["voices"][letter][0]
        assert "pitch" in ev0 and "step" in ev0["pitch"]
        assert ev0["duration"]["elm"]


def test_export_path_writes_json(tmp_path: Path) -> None:
    out = tmp_path / "out.score-ir.json"
    export_mvsa_path_to_score_ir(VREDE, out)
    raw = json.loads(out.read_text(encoding="utf-8"))
    assert raw["format"] == SCORE_IR_FORMAT
    assert raw["measures"][0]["cues"]


def test_unknown_section_raises() -> None:
    from vsa.mvsa_musicxml import MvsaExportError

    text = VREDE.read_text(encoding="utf-8")
    with pytest.raises(MvsaExportError, match="sectie"):
        export_mvsa_to_score_ir(text, section_id="bestaat-niet")
