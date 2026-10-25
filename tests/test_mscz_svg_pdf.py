"""CLI: mscz svg / mscz pdf; mvsa svg|pdf weigeren .mscz."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from vsa.cli_mscz import main as mscz_main
from vsa.cli_mvsa import main as mvsa_main


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


def test_mscz_svg_writes_sibling(tmp_path: Path, capsys) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04fake")
    with patch("vsa.mvsa_mscz.export_mscz_to_svg", side_effect=_fake_svg):
        assert mscz_main(["svg", str(bron)]) == 0
    out = tmp_path / "lied.mscz.svg"
    assert out.is_file()
    assert "Geschreven:" in capsys.readouterr().out


def test_mscz_pdf_writes_output(tmp_path: Path, capsys) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04fake")
    pdf = tmp_path / "out.pdf"
    with patch("vsa.mvsa_mscz.export_mscz_to_pdf", side_effect=_fake_pdf):
        assert mscz_main(["pdf", str(bron), "-o", str(pdf)]) == 0
    assert pdf.is_file()
    assert "Geschreven:" in capsys.readouterr().out


def test_mvsa_svg_rejects_mscz(tmp_path: Path, capsys) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04fake")
    assert mvsa_main(["svg", str(bron)]) == 1
    err = capsys.readouterr().err
    assert "weigert .mscz" in err
    assert "mscz svg" in err


def test_mvsa_pdf_rejects_mscz(tmp_path: Path, capsys) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04fake")
    assert mvsa_main(["pdf", str(bron)]) == 1
    err = capsys.readouterr().err
    assert "weigert .mscz" in err
    assert "mscz pdf" in err
