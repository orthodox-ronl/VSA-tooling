"""``.vsa`` playback-export: syllabify + Coria-finalize."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

import pytest

from vsa.street_products import products_vsa_one
from vsa.vsa_musicxml_export import export_vsa_to_musicxml

_REPO = Path(__file__).resolve().parents[1]
_VALID = _REPO / "examples" / "minimal" / "valid-demo.vsa"


def _score_xml_from_mxl(mxl: Path) -> str:
    with zipfile.ZipFile(mxl) as zf:
        return zf.read("score.xml").decode("utf-8")


@pytest.mark.skipif(not _VALID.is_file(), reason="valid-demo.vsa ontbreekt")
def test_export_finalize_strips_doctype(tmp_path: Path) -> None:
    dest = tmp_path / _VALID.name
    dest.write_text(_VALID.read_text(encoding="utf-8"), encoding="utf-8")
    out = tmp_path / "out.mxl"
    export_vsa_to_musicxml(dest, out)
    xml = _score_xml_from_mxl(out)
    assert "<!DOCTYPE" not in xml
    assert "<score-partwise" in xml


@pytest.mark.skipif(not _VALID.is_file(), reason="valid-demo.vsa ontbreekt")
def test_export_syllabify_adds_junction_lyric(tmp_path: Path) -> None:
    dest = tmp_path / _VALID.name
    dest.write_text(_VALID.read_text(encoding="utf-8"), encoding="utf-8")
    plain = tmp_path / "plain.mxl"
    syl = tmp_path / "syl.mxl"
    export_vsa_to_musicxml(dest, plain, syllabify=False)
    export_vsa_to_musicxml(dest, syl, syllabify=True)
    plain_texts = re.findall(
        r"<text[^>]*>([^<]*)</text>", _score_xml_from_mxl(plain)
    )
    syl_texts = re.findall(r"<text[^>]*>([^<]*)</text>", _score_xml_from_mxl(syl))
    assert "Hei" in plain_texts
    assert "Hei-" in syl_texts
    # Canonieke bron ongewijzigd
    assert dest.read_text(encoding="utf-8") == _VALID.read_text(encoding="utf-8")


@pytest.mark.skipif(not _VALID.is_file(), reason="valid-demo.vsa ontbreekt")
def test_vsa_products_mxl_is_coria_finalized(tmp_path: Path) -> None:
    """Coria-finalize op mxl-product; overige universele exports gemockt."""
    from unittest.mock import patch

    dest = tmp_path / _VALID.name
    dest.write_text(_VALID.read_text(encoding="utf-8"), encoding="utf-8")

    def _ir(_b: Path, out: Path, **_k: object) -> None:
        out.write_text("{}", encoding="utf-8")

    def _from(_s: Path, d: Path, **_k: object) -> None:
        d.write_text("<score/>", encoding="utf-8")

    def _mscz(_b: Path, out: Path, **_k: object) -> Path:
        out.write_bytes(b"PK")
        return out

    def _pdf(_b: Path, out: Path, **_k: object) -> Path:
        out.write_bytes(b"%PDF")
        return out

    def _mp3(_b: Path, out: Path, **_k: object) -> Path:
        out.write_bytes(b"ID3")
        return out

    def _lyr(_b: Path, out: Path | None = None, **_k: object) -> Path:
        p = Path(out) if out else _b.with_name(_b.name + ".lyrics.txt")
        p.write_text("x\n", encoding="utf-8")
        return p

    with (
        patch(
            "vsa.street_product_export.export_bron_to_score_ir",
            side_effect=_ir,
        ),
        patch(
            "vsa.score_ir_musicxml.export_score_ir_path_to_musicxml",
            side_effect=_from,
        ),
        patch(
            "vsa.street_product_export.export_bron_to_mscz_product",
            side_effect=_mscz,
        ),
        patch(
            "vsa.street_product_export.export_bron_to_partituur_pdf",
            side_effect=_pdf,
        ),
        patch("vsa.audio_export.export_to_audio", side_effect=_mp3),
        patch(
            "vsa.street_product_export.write_lyrics_product",
            side_effect=_lyr,
        ),
    ):
        assert products_vsa_one(dest) == 0
    mxl = tmp_path / f"{dest.name}.mxl"
    assert mxl.is_file()
    xml = _score_xml_from_mxl(mxl)
    assert "<!DOCTYPE" not in xml
    texts = re.findall(r"<text[^>]*>([^<]*)</text>", xml)
    assert "Hei-" in texts
