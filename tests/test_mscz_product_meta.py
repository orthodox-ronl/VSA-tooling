"""mscz mxl/svg/pdf mergen products-meta (stap 1)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from vsa.cli_mscz import main as mscz_main
from vsa.products_meta import meta_path_for, sha256_file


def _fake_mxl(_src: Path, dest: Path, **_kwargs: object) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("<score/>", encoding="utf-8")


def _fake_svg(_src: Path, dest: Path, **_kwargs: object) -> list[Path]:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("<svg/>", encoding="utf-8")
    return [dest]


def _fake_bladreeks(_src: Path, dest: Path, **_kwargs: object) -> list[Path]:
    dest = Path(dest)
    pages = [
        dest.parent / f"{dest.stem}-1.svg",
        dest.parent / f"{dest.stem}-2.svg",
    ]
    for page in pages:
        page.write_text("<svg/>", encoding="utf-8")
    return pages


def _fake_pdf(_src: Path, dest: Path, **_kwargs: object) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"%PDF-1.4 fake")
    return dest


def test_mscz_mxl_writes_and_merges_meta(tmp_path: Path) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04fake")
    with patch(
        "vsa.musicxml_playback_normalize.export_mscz_to_playback_mxl",
        side_effect=_fake_mxl,
    ):
        assert mscz_main(["mxl", str(bron)]) == 0
    meta_path = meta_path_for(bron)
    assert meta_path.is_file()
    data = json.loads(meta_path.read_text(encoding="utf-8"))
    assert data["schema"] == 2
    assert "generated_at" in data["products"]["mxl"]
    assert data["products"]["mxl"]["sha256"] == sha256_file(tmp_path / "lied.mscz.mxl")

    with patch("vsa.mvsa_mscz.export_mscz_to_pdf", side_effect=_fake_pdf):
        assert mscz_main(["pdf", str(bron)]) == 0
    data = json.loads(meta_path.read_text(encoding="utf-8"))
    assert set(data["products"]) == {"mxl", "pdf"}
    assert data["products"]["mxl"]["sha256"] == sha256_file(tmp_path / "lied.mscz.mxl")
    assert data["products"]["pdf"]["file"] == "lied.mscz.pdf"


def test_mscz_svg_meta_single_tall_not_bladreeks(tmp_path: Path) -> None:
    """Product-meta heeft altijd één key ``svg`` (tall); geen ``svg-N``-bladreeks."""
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04fake")
    with patch("vsa.mvsa_mscz.export_mscz_to_svg", side_effect=_fake_svg):
        assert mscz_main(["svg", str(bron)]) == 0
    data = json.loads(meta_path_for(bron).read_text(encoding="utf-8"))
    assert set(data["products"]) == {"svg"}
    assert data["products"]["svg"]["file"] == "lied.mscz.svg"

    # Ook als de exporter per ongeluk meerdere pagina's teruggeeft: meta = één svg.
    with patch("vsa.mvsa_mscz.export_mscz_to_svg", side_effect=_fake_bladreeks):
        assert mscz_main(["svg", str(bron)]) == 0
    data = json.loads(meta_path_for(bron).read_text(encoding="utf-8"))
    assert set(data["products"]) == {"svg"}
    assert not any(k.startswith("svg-") for k in data["products"])
    assert data["products"]["svg"]["file"] == "lied.mscz-1.svg"


def test_mscz_pdf_skips_meta_when_not_sibling(tmp_path: Path, capsys) -> None:
    bron = tmp_path / "bron" / "lied.mscz"
    bron.parent.mkdir()
    bron.write_bytes(b"PK\x03\x04fake")
    elsewhere = tmp_path / "out" / "x.pdf"
    elsewhere.parent.mkdir()
    with patch("vsa.mvsa_mscz.export_mscz_to_pdf", side_effect=_fake_pdf):
        assert mscz_main(["pdf", str(bron), "-o", str(elsewhere)]) == 0
    assert not meta_path_for(bron).exists()
    assert "products-meta key 'pdf' overgeslagen" in capsys.readouterr().err
