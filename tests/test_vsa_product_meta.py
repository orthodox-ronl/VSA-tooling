"""vsa musicxml / svg mergen products-meta (stap 3)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from vsa.cli import main as vsa_main
from vsa.products_meta import meta_path_for, sha256_file


def _fake_export_mxl(
    input_path: Path,
    output_path: Path,
    cli_overrides: dict,
    *,
    syllabify: bool = False,
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("<score/>", encoding="utf-8")
    return 0


def test_vsa_musicxml_merges_mxl_meta(tmp_path: Path) -> None:
    bron = tmp_path / "lied.vsa"
    bron.write_text("L | a\n", encoding="utf-8")
    out = tmp_path / "lied.vsa.mxl"
    with patch("vsa.cli._export_vsa_to_musicxml", side_effect=_fake_export_mxl):
        assert vsa_main(["musicxml", str(bron), str(out)]) == 0
    data = json.loads(meta_path_for(bron).read_text(encoding="utf-8"))
    assert set(data["products"]) == {"mxl"}
    assert data["products"]["mxl"]["sha256"] == sha256_file(out)
    assert isinstance(data["products"]["mxl"]["generated_at"], str)


def test_vsa_svg_merges_svg_meta(tmp_path: Path) -> None:
    examples = list((Path(__file__).resolve().parents[1] / "examples").rglob("*.vsa"))
    if not examples:
        pytest.skip("geen .vsa-examples")
    src = examples[0]
    bron = tmp_path / src.name
    bron.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    assert vsa_main(["svg", str(bron)]) == 0
    svg = tmp_path / f"{bron.name}.svg"
    assert svg.is_file()
    data = json.loads(meta_path_for(bron).read_text(encoding="utf-8"))
    assert "svg" in data["products"]
    assert data["products"]["svg"]["sha256"] == sha256_file(svg)


def test_vsa_musicxml_then_svg_merge(tmp_path: Path) -> None:
    examples = list((Path(__file__).resolve().parents[1] / "examples").rglob("*.vsa"))
    if not examples:
        pytest.skip("geen .vsa-examples")
    src = examples[0]
    bron = tmp_path / src.name
    bron.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    mxl = tmp_path / f"{bron.name}.mxl"
    with patch("vsa.cli._export_vsa_to_musicxml", side_effect=_fake_export_mxl):
        assert vsa_main(["musicxml", str(bron), str(mxl)]) == 0
    assert vsa_main(["svg", str(bron)]) == 0
    data = json.loads(meta_path_for(bron).read_text(encoding="utf-8"))
    assert set(data["products"]) == {"mxl", "svg"}
