"""Universele street-products: gates, mscz audio, products-keys (mocks)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from vsa.cli import main as vsa_main
from vsa.cli_mscz import main as mscz_main
from vsa.cli_mvsa import main as mvsa_main
from vsa.products_meta import meta_path_for
from vsa.street_products import UNIVERSAL_PRODUCT_KEYS, products_mscz_one
import json


def _touch(path: Path, content: bytes | str = b"x") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)
    return path


def _fake_mxl(_bron: Path, out: Path, **_kw: object) -> Path:
    return _touch(out, "<score/>")


def _fake_score_ir(_bron: Path, out: Path, **_kw: object) -> None:
    _touch(out, "{}")


def _fake_from_ir(_src: Path, dest: Path, **_kw: object) -> None:
    _touch(dest, "<score/>")


def _fake_mscz(_bron: Path, out: Path, **_kw: object) -> Path:
    return _touch(out, b"PK\x03\x04")


def _fake_pdf(_bron: Path, out: Path, **_kw: object) -> Path:
    return _touch(out, b"%PDF-1.4")


def _fake_mp3(_bron: Path, out: Path, **_kw: object) -> Path:
    return _touch(out, b"ID3")


def _fake_lyrics(_bron: Path, out: Path | None = None, **_kw: object) -> Path:
    dest = Path(out) if out is not None else _bron.with_name(_bron.name + ".lyrics.txt")
    return _touch(dest, "woord\n")


def _fake_svg(_bron: Path, dest: Path, **_kw: object) -> list[Path]:
    dest = Path(dest)
    _touch(dest, "<svg/>")
    return [dest]


def _universal_patches(*, with_svg: bool = True):
    patches = [
        patch(
            "vsa.street_product_export.export_bron_to_mxl",
            side_effect=_fake_mxl,
        ),
        patch(
            "vsa.street_product_export.export_bron_to_score_ir",
            side_effect=_fake_score_ir,
        ),
        patch(
            "vsa.score_ir_musicxml.export_score_ir_path_to_musicxml",
            side_effect=_fake_from_ir,
        ),
        patch(
            "vsa.street_product_export.export_bron_to_mscz_product",
            side_effect=_fake_mscz,
        ),
        patch(
            "vsa.street_product_export.export_bron_to_partituur_pdf",
            side_effect=_fake_pdf,
        ),
        patch("vsa.audio_export.export_to_audio", side_effect=_fake_mp3),
        patch(
            "vsa.street_product_export.write_lyrics_product",
            side_effect=_fake_lyrics,
        ),
    ]
    if with_svg:
        patches.append(
            patch("vsa.mvsa_mscz.export_mscz_to_svg", side_effect=_fake_svg)
        )
    return patches


def test_mscz_products_writes_universal_keys(tmp_path: Path) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04fake")
    with (
        patch(
            "vsa.street_product_export.export_bron_to_mxl",
            side_effect=_fake_mxl,
        ),
        patch(
            "vsa.street_product_export.export_bron_to_score_ir",
            side_effect=_fake_score_ir,
        ),
        patch(
            "vsa.score_ir_musicxml.export_score_ir_path_to_musicxml",
            side_effect=_fake_from_ir,
        ),
        patch(
            "vsa.street_product_export.export_bron_to_mscz_product",
            side_effect=_fake_mscz,
        ),
        patch(
            "vsa.street_product_export.export_bron_to_partituur_pdf",
            side_effect=_fake_pdf,
        ),
        patch("vsa.audio_export.export_to_audio", side_effect=_fake_mp3),
        patch(
            "vsa.street_product_export.write_lyrics_product",
            side_effect=_fake_lyrics,
        ),
        patch("vsa.mvsa_mscz.export_mscz_to_svg", side_effect=_fake_svg),
    ):
        assert products_mscz_one(bron, force=True) == 0
    data = json.loads(meta_path_for(bron).read_text(encoding="utf-8"))
    keys = set(data["products"])
    assert set(UNIVERSAL_PRODUCT_KEYS).issubset(keys)
    assert "svg" in keys


def test_mscz_mp3_writes_sibling(tmp_path: Path, capsys) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04fake")
    with patch("vsa.audio_export.export_to_audio", side_effect=_fake_mp3):
        assert mscz_main(["mp3", str(bron)]) == 0
    assert (tmp_path / "lied.mscz.mp3").is_file()
    assert "Geschreven:" in capsys.readouterr().out


def test_mvsa_mp3_rejects_mscz(tmp_path: Path, capsys) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04fake")
    assert mvsa_main(["mp3", str(bron)]) == 1
    err = capsys.readouterr().err
    assert "weigert .mscz" in err
    assert "mscz mp3" in err


def test_mvsa_mxl_rejects_mscz(tmp_path: Path, capsys) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04fake")
    assert mvsa_main(["mxl", str(bron)]) == 1
    err = capsys.readouterr().err
    assert "weigert .mscz" in err
    assert "mscz mxl" in err


def test_vsa_audio_rejects_mscz(tmp_path: Path, capsys) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04fake")
    assert vsa_main(["audio", str(bron), str(tmp_path / "out.mp3")]) == 1
    err = capsys.readouterr().err
    assert "weigert .mscz" in err
    assert "mscz mp3" in err


def test_vsa_text_rejects_mscz(tmp_path: Path, capsys) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04fake")
    assert vsa_main(["text", str(bron)]) == 1
    err = capsys.readouterr().err
    assert "weigert .mscz" in err
    assert "mscz text" in err


def test_mscz_help_lists_audio(capsys) -> None:
    import pytest

    with pytest.raises(SystemExit) as exc:
        mscz_main(["-h"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "mp3" in out
    assert "score-ir" in out
