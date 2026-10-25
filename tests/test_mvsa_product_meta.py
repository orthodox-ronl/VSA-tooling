"""mvsa mxl/svg/pdf/score-ir mergen products-meta (stap 2)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from vsa.cli_mvsa import main as mvsa_main
from vsa.products_meta import meta_path_for, sha256_file


def _fake_mxl(_src: Path, dest: Path, **_kwargs: object) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("<score/>", encoding="utf-8")


def _fake_score_ir(_src: Path, dest: Path, **_kwargs: object) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("{}", encoding="utf-8")


def _fake_from_ir(_src: Path, dest: Path, **_kwargs: object) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("<score/>", encoding="utf-8")


def _fake_svg(_src: Path, dest: Path, **_kwargs: object) -> list[Path]:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("<svg/>", encoding="utf-8")
    return [dest]


def _fake_pdf(_src: Path, dest: Path, **_kwargs: object) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"%PDF-1.4 fake")
    return dest


def test_mvsa_subs_merge_meta_keys(tmp_path: Path) -> None:
    bron = tmp_path / "lied.mvsa"
    bron.write_text("title: t\n---\nL  | a\nS  | a\n", encoding="utf-8")

    with patch("vsa.mvsa_musicxml.export_mvsa_path", side_effect=_fake_mxl):
        assert mvsa_main(["mxl", str(bron)]) == 0
    data = json.loads(meta_path_for(bron).read_text(encoding="utf-8"))
    assert set(data["products"]) == {"mxl"}
    assert data["products"]["mxl"]["sha256"] == sha256_file(tmp_path / "lied.mvsa.mxl")

    with (
        patch("vsa.score_ir.export_mvsa_path_to_score_ir", side_effect=_fake_score_ir),
        patch(
            "vsa.score_ir_musicxml.export_score_ir_path_to_musicxml",
            side_effect=_fake_from_ir,
        ),
    ):
        assert mvsa_main(["score-ir", str(bron), "--musicxml"]) == 0
    data = json.loads(meta_path_for(bron).read_text(encoding="utf-8"))
    assert set(data["products"]) >= {"mxl", "score-ir", "from-ir"}

    with patch("vsa.mvsa_mscz.export_mvsa_to_svg", side_effect=_fake_svg):
        assert mvsa_main(["svg", str(bron)]) == 0
    data = json.loads(meta_path_for(bron).read_text(encoding="utf-8"))
    assert "svg" in data["products"]

    with patch("vsa.mvsa_mscz.export_mvsa_to_pdf", side_effect=_fake_pdf):
        assert mvsa_main(["pdf", str(bron)]) == 0
    data = json.loads(meta_path_for(bron).read_text(encoding="utf-8"))
    assert set(data["products"]) >= {"mxl", "score-ir", "from-ir", "svg", "pdf"}
    for key in ("mxl", "score-ir", "from-ir", "svg", "pdf"):
        assert isinstance(data["products"][key].get("generated_at"), str)
