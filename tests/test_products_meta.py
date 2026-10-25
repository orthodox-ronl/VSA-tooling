"""Unit tests for products-meta + mvsa/vsa products (no MuseScore)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

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
from vsa.street_products import (
    _assign_svg_products,
    products_mscz_one,
    products_mvsa_one,
    products_vsa_one,
)
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
    assert isinstance(entry["generated_at"], str) and entry["generated_at"]
    assert isinstance(meta["generated_at"], str) and meta["generated_at"]
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


def test_write_meta_sets_product_generated_at(tmp_path: Path) -> None:
    bron = tmp_path / "lied.mvsa"
    bron.write_text("x\n", encoding="utf-8")
    mxl = tmp_path / "lied.mvsa.mxl"
    mxl.write_text("<score/>", encoding="utf-8")
    stamp = "2026-03-15T12:00:00+00:00"
    write_meta(bron, {"mxl": mxl}, generated_at=stamp)
    meta = load_meta(bron)
    assert meta is not None
    assert meta["generated_at"] == stamp
    assert meta["products"]["mxl"]["generated_at"] == stamp


def test_write_meta_merge_keeps_other_keys(tmp_path: Path) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04fake")
    mxl = tmp_path / "lied.mscz.mxl"
    svg = tmp_path / "lied.mscz.svg"
    mxl.write_text("<score/>", encoding="utf-8")
    svg.write_text("<svg/>", encoding="utf-8")
    write_meta(
        bron,
        {"mxl": mxl, "svg": svg},
        generated_at="2026-01-01T00:00:00+00:00",
    )

    svg.write_text("<svg changed/>", encoding="utf-8")
    later = "2026-02-01T00:00:00+00:00"
    write_meta(bron, {"svg": svg}, merge=True, generated_at=later)
    meta = load_meta(bron)
    assert meta is not None
    assert set(meta["products"]) == {"mxl", "svg"}
    assert meta["generated_at"] == later
    assert meta["products"]["mxl"]["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert meta["products"]["mxl"]["sha256"] == sha256_file(mxl)
    assert meta["products"]["svg"]["generated_at"] == later
    assert meta["products"]["svg"]["sha256"] == sha256_file(svg)
    status, _ = freshness(bron, required_keys={"mxl", "svg"})
    assert status == "ok"


def test_write_meta_merge_drops_old_keys_when_bron_stale(tmp_path: Path) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04v1")
    mxl = tmp_path / "lied.mscz.mxl"
    svg = tmp_path / "lied.mscz.svg"
    mxl.write_text("<score/>", encoding="utf-8")
    svg.write_text("<svg/>", encoding="utf-8")
    write_meta(bron, {"mxl": mxl, "svg": svg})

    bron.write_bytes(b"PK\x03\x04v2-changed")
    svg.write_text("<svg new/>", encoding="utf-8")
    write_meta(
        bron,
        {"svg": svg},
        merge=True,
        generated_at="2026-03-01T00:00:00+00:00",
    )
    meta = load_meta(bron)
    assert meta is not None
    assert set(meta["products"]) == {"svg"}
    assert meta["bron_sha256"] == sha256_file(bron)
    assert meta["products"]["svg"]["generated_at"] == "2026-03-01T00:00:00+00:00"


def test_write_meta_replace_drops_unlisted_keys(tmp_path: Path) -> None:
    bron = tmp_path / "lied.mvsa"
    bron.write_text("x\n", encoding="utf-8")
    mxl = tmp_path / "lied.mvsa.mxl"
    svg = tmp_path / "lied.mvsa.svg"
    mxl.write_text("<score/>", encoding="utf-8")
    svg.write_text("<svg/>", encoding="utf-8")
    write_meta(bron, {"mxl": mxl, "svg": svg})
    write_meta(bron, {"mxl": mxl}, merge=False)
    meta = load_meta(bron)
    assert meta is not None
    assert set(meta["products"]) == {"mxl"}


def test_freshness_ok_without_legacy_product_generated_at(tmp_path: Path) -> None:
    """Schema-2 zonder product-generated_at blijft leesbaar (pre-7b sidecars)."""
    bron = tmp_path / "lied.mvsa"
    bron.write_text("x\n", encoding="utf-8")
    mxl = tmp_path / "lied.mvsa.mxl"
    mxl.write_text("<score/>", encoding="utf-8")
    meta_path_for(bron).write_text(
        json.dumps(
            {
                "schema": SCHEMA_VERSION,
                "bron": bron.name,
                "bron_sha256": sha256_file(bron),
                "generated_at": "2026-01-01T00:00:00+00:00",
                "products": {
                    "mxl": {"file": mxl.name, "sha256": sha256_file(mxl)},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    status, _ = freshness(bron, required_keys={"mxl"})
    assert status == "ok"


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
        assert isinstance(entry.get("generated_at"), str) and entry["generated_at"]
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


def test_assign_svg_products_bladreeks_drops_seed_svg(tmp_path: Path) -> None:
    seed = tmp_path / "lied.mscz.svg"
    p1 = tmp_path / "lied.mscz-1.svg"
    p2 = tmp_path / "lied.mscz-2.svg"
    products: dict[str, Path] = {"mxl": tmp_path / "lied.mscz.mxl", "svg": seed}
    _assign_svg_products(products, [p1, p2])
    assert "svg" not in products
    assert products["svg-1"] == p1
    assert products["svg-2"] == p2


def test_assign_svg_products_single_keeps_svg(tmp_path: Path) -> None:
    seed = tmp_path / "lied.mscz.svg"
    written = tmp_path / "lied.mscz.svg"
    products: dict[str, Path] = {"svg": seed}
    _assign_svg_products(products, [written])
    assert products == {"svg": written}


def _fake_write_mxl(_src: Path, dest: Path, **_kwargs: object) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("<score/>", encoding="utf-8")


def _fake_bladreeks_svg(_src: Path, dest: Path, **_kwargs: object) -> list[Path]:
    dest = Path(dest)
    pages = [
        dest.parent / f"{dest.stem}-1.svg",
        dest.parent / f"{dest.stem}-2.svg",
    ]
    for page in pages:
        page.write_text("<svg/>", encoding="utf-8")
    assert not dest.exists()
    return pages


def _fake_single_svg(_src: Path, dest: Path, **_kwargs: object) -> list[Path]:
    dest = Path(dest)
    dest.write_text("<svg/>", encoding="utf-8")
    return [dest]


def test_mscz_products_bladreeks_meta_no_dead_svg(tmp_path: Path) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04fake")
    with (
        patch(
            "vsa.musicxml_playback_normalize.export_mscz_to_playback_mxl",
            side_effect=_fake_write_mxl,
        ),
        patch("vsa.mvsa_mscz.export_mscz_to_svg", side_effect=_fake_bladreeks_svg),
    ):
        assert products_mscz_one(bron, force=True) == 0
    data = json.loads(meta_path_for(bron).read_text(encoding="utf-8"))
    assert data["schema"] == SCHEMA_VERSION
    keys = set(data["products"])
    assert keys == {"mxl", "svg-1", "svg-2"}
    assert "svg" not in keys
    for key in ("mxl", "svg-1", "svg-2"):
        entry = data["products"][key]
        path = tmp_path / entry["file"]
        assert path.is_file()
        assert entry["sha256"] == sha256_file(path)


def test_mscz_products_single_svg_meta_key(tmp_path: Path) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04fake")
    with (
        patch(
            "vsa.musicxml_playback_normalize.export_mscz_to_playback_mxl",
            side_effect=_fake_write_mxl,
        ),
        patch("vsa.mvsa_mscz.export_mscz_to_svg", side_effect=_fake_single_svg),
    ):
        assert products_mscz_one(bron, force=True) == 0
    data = json.loads(meta_path_for(bron).read_text(encoding="utf-8"))
    assert set(data["products"]) == {"mxl", "svg"}
    assert data["products"]["svg"]["file"] == "lied.mscz.svg"


def test_mvsa_products_bladreeks_meta_no_dead_svg(tmp_path: Path) -> None:
    bron = tmp_path / "lied.mvsa"
    bron.write_text("title: t\n---\nL  | a\nS  | a\n", encoding="utf-8")

    def _fake_score_ir(_src: Path, dest: Path, **_kwargs: object) -> None:
        dest.write_text("{}", encoding="utf-8")

    def _fake_from_ir(_src: Path, dest: Path, **_kwargs: object) -> None:
        dest.write_text("<score/>", encoding="utf-8")

    with (
        patch("vsa.mvsa_musicxml.export_mvsa_path", side_effect=_fake_write_mxl),
        patch(
            "vsa.score_ir.export_mvsa_path_to_score_ir",
            side_effect=_fake_score_ir,
        ),
        patch(
            "vsa.score_ir_musicxml.export_score_ir_path_to_musicxml",
            side_effect=_fake_from_ir,
        ),
        patch("vsa.mvsa_mscz.export_mvsa_to_svg", side_effect=_fake_bladreeks_svg),
    ):
        assert products_mvsa_one(bron, force=True) == 0
    data = json.loads(meta_path_for(bron).read_text(encoding="utf-8"))
    assert data["schema"] == SCHEMA_VERSION
    keys = set(data["products"])
    assert keys == {"mxl", "score-ir", "from-ir", "svg-1", "svg-2"}
    assert "svg" not in keys
