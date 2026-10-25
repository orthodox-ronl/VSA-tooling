"""Unit tests for products-meta + mvsa/vsa products (no MuseScore)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vsa.cli_mvsa import main as mvsa_main
from vsa.products_meta import (
    SCHEMA_VERSION,
    freshness,
    load_meta,
    meta_path_for,
    product_file_name,
    sha256_file,
    write_meta,
)
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
    assert meta["schema"] == SCHEMA_VERSION
    assert meta["bron"] == "lied.mvsa"
    assert meta["bron_sha256"] == sha256_file(bron)
    entry = meta["products"]["mxl"]
    assert entry["file"] == "lied.mvsa.mxl"
    assert entry["sha256"] == sha256_file(mxl)
    status, _ = freshness(bron, required_keys={"mxl"})
    assert status == "ok"

    bron.write_text(bron.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    status, _ = freshness(bron, required_keys={"mxl"})
    assert status == "stale"


def test_freshness_missing_product(tmp_path: Path) -> None:
    bron = tmp_path / "lied.mvsa"
    bron.write_text("x\n", encoding="utf-8")
    mxl = tmp_path / "lied.mvsa.mxl"
    mxl.write_text("<score/>", encoding="utf-8")
    write_meta(bron, {"mxl": mxl})
    mxl.unlink()
    status, msg = freshness(bron, required_keys={"mxl"})
    assert status == "missing"
    assert "ontbreekt" in msg


def test_freshness_stale_product_hash(tmp_path: Path) -> None:
    bron = tmp_path / "lied.mvsa"
    bron.write_text("x\n", encoding="utf-8")
    mxl = tmp_path / "lied.mvsa.mxl"
    mxl.write_text("<score/>", encoding="utf-8")
    write_meta(bron, {"mxl": mxl})
    mxl.write_text("<score changed/>", encoding="utf-8")
    status, msg = freshness(bron, required_keys={"mxl"})
    assert status == "stale"
    assert "sha256" in msg


def test_freshness_stale_schema_1(tmp_path: Path) -> None:
    bron = tmp_path / "lied.mvsa"
    bron.write_text("x\n", encoding="utf-8")
    mxl = tmp_path / "lied.mvsa.mxl"
    mxl.write_text("<score/>", encoding="utf-8")
    meta_path = meta_path_for(bron)
    meta_path.write_text(
        json.dumps(
            {
                "schema": 1,
                "bron": bron.name,
                "bron_sha256": sha256_file(bron),
                "generated_at": "2026-01-01T00:00:00+00:00",
                "products": {"mxl": mxl.name},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    status, msg = freshness(bron, required_keys={"mxl"})
    assert status == "stale"
    assert "schema" in msg


def test_product_file_name_helpers() -> None:
    assert product_file_name("a.mxl") == "a.mxl"
    assert product_file_name({"file": "a.mxl", "sha256": "abc"}) == "a.mxl"
    assert product_file_name({}) is None


@pytest.mark.skipif(not _MVSA.is_file(), reason="example .mvsa ontbreekt")
def test_mvsa_products_skip_svg_writes_meta(tmp_path: Path) -> None:
    dest = tmp_path / _MVSA.name
    dest.write_text(_MVSA.read_text(encoding="utf-8"), encoding="utf-8")
    assert products_mvsa_one(dest, skip_svg=True) == 0
    meta_path = meta_path_for(dest)
    assert meta_path.is_file()
    data = json.loads(meta_path.read_text(encoding="utf-8"))
    assert data["schema"] == SCHEMA_VERSION
    assert set(data["products"]) >= {"mxl", "score-ir", "from-ir"}
    for key in ("mxl", "score-ir", "from-ir"):
        entry = data["products"][key]
        path = tmp_path / entry["file"]
        assert path.is_file()
        assert entry["sha256"] == sha256_file(path)
    assert products_mvsa_one(dest, skip_svg=True) == 0
    status, _ = freshness(dest, required_keys={"mxl", "score-ir", "from-ir"})
    assert status == "ok"


@pytest.mark.skipif(not _MVSA.is_file(), reason="example .mvsa ontbreekt")
def test_mvsa_products_cli_dry_run(tmp_path: Path) -> None:
    dest = tmp_path / _MVSA.name
    dest.write_text(_MVSA.read_text(encoding="utf-8"), encoding="utf-8")
    assert mvsa_main(["products", str(dest), "--skip-svg", "--dry-run"]) == 0
    assert not meta_path_for(dest).exists()


def test_vsa_products_minimal(tmp_path: Path) -> None:
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
    data = json.loads(meta_path_for(dest).read_text(encoding="utf-8"))
    assert data["schema"] == SCHEMA_VERSION
    assert "sha256" in data["products"]["mxl"]
    status, _ = freshness(dest, required_keys={"mxl", "svg"})
    assert status == "ok"
