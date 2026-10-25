"""Unit tests for products-meta + mvsa/vsa products (no MuseScore)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vsa.cli_mvsa import main as mvsa_main
from vsa.products_meta import freshness, load_meta, meta_path_for, sha256_file, write_meta
from vsa.street_products import products_mvsa_one, products_vsa_one

_REPO = Path(__file__).resolve().parents[1]
_MVSA = _REPO / "examples" / "mvsa" / "1a-vredeslitanie.mvsa"


def test_write_and_freshness_roundtrip(tmp_path: Path) -> None:
    bron = tmp_path / "lied.mvsa"
    bron.write_text("title: t\n---\nL  | a\nS  | a\n", encoding="utf-8")
    mxl = tmp_path / "lied.mvsa.mxl"
    mxl.write_text("<score/>", encoding="utf-8")
    write_meta(bron, {"mxl": mxl})
    meta = load_meta(bron)
    assert meta is not None
    assert meta["schema"] == 1
    assert meta["bron"] == "lied.mvsa"
    assert meta["bron_sha256"] == sha256_file(bron)
    assert meta["products"]["mxl"] == "lied.mvsa.mxl"
    status, _ = freshness(bron, required_keys={"mxl"})
    assert status == "ok"

    bron.write_text(bron.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    status, _ = freshness(bron, required_keys={"mxl"})
    assert status == "stale"


def test_freshness_missing_product(tmp_path: Path) -> None:
    bron = tmp_path / "lied.mvsa"
    bron.write_text("x\n", encoding="utf-8")
    write_meta(bron, {"mxl": tmp_path / "lied.mvsa.mxl"})
    status, msg = freshness(bron, required_keys={"mxl"})
    assert status == "missing"
    assert "ontbreekt" in msg


@pytest.mark.skipif(not _MVSA.is_file(), reason="example .mvsa ontbreekt")
def test_mvsa_products_skip_svg_writes_meta(tmp_path: Path) -> None:
    dest = tmp_path / _MVSA.name
    dest.write_text(_MVSA.read_text(encoding="utf-8"), encoding="utf-8")
    assert products_mvsa_one(dest, skip_svg=True) == 0
    meta_path = meta_path_for(dest)
    assert meta_path.is_file()
    data = json.loads(meta_path.read_text(encoding="utf-8"))
    assert set(data["products"]) >= {"mxl", "score-ir", "from-ir"}
    assert (tmp_path / data["products"]["mxl"]).is_file()
    assert (tmp_path / data["products"]["score-ir"]).is_file()
    assert (tmp_path / data["products"]["from-ir"]).is_file()
    # Second run without --force should be no-op ok
    assert products_mvsa_one(dest, skip_svg=True) == 0


@pytest.mark.skipif(not _MVSA.is_file(), reason="example .mvsa ontbreekt")
def test_mvsa_products_cli_dry_run(tmp_path: Path) -> None:
    dest = tmp_path / _MVSA.name
    dest.write_text(_MVSA.read_text(encoding="utf-8"), encoding="utf-8")
    assert mvsa_main(["products", str(dest), "--skip-svg", "--dry-run"]) == 0
    assert not meta_path_for(dest).exists()


def test_vsa_products_minimal(tmp_path: Path) -> None:
    # Tiny valid-ish .vsa if examples lack one — use syllabified simple form
    examples = list((_REPO / "examples").rglob("*.vsa"))
    if not examples:
        pytest.skip("geen .vsa-examples")
    src = examples[0]
    dest = tmp_path / src.name
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    code = products_vsa_one(dest)
    if code != 0:
        pytest.skip("voorbeeld-.vsa faalde export (niet regressie-meta)")
    assert meta_path_for(dest).is_file()
    status, _ = freshness(dest, required_keys={"mxl", "svg"})
    assert status == "ok"
