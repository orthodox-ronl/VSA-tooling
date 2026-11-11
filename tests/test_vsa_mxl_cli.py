"""vsa mxl: uniforme path [-o]-vorm; straat-puur .vsa."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from vsa.cli import main as vsa_main


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


def test_vsa_mxl_sibling_default(tmp_path: Path, capsys) -> None:
    bron = tmp_path / "lied.vsa"
    bron.write_text("{tekst}", encoding="utf-8")
    with patch("vsa.cli._export_vsa_to_musicxml", side_effect=_fake_export_mxl):
        assert vsa_main(["mxl", str(bron)]) == 0
    assert (tmp_path / "lied.vsa.mxl").is_file()
    assert "Geschreven:" in capsys.readouterr().out


def test_vsa_musicxml_alias_same_shape(tmp_path: Path) -> None:
    bron = tmp_path / "lied.vsa"
    bron.write_text("{tekst}", encoding="utf-8")
    out = tmp_path / "out.mxl"
    with patch("vsa.cli._export_vsa_to_musicxml", side_effect=_fake_export_mxl):
        assert vsa_main(["musicxml", str(bron), "-o", str(out)]) == 0
    assert out.is_file()


def test_vsa_mxl_rejects_mvsa_with_hint(capsys, tmp_path: Path) -> None:
    mvsa = tmp_path / "lied.mvsa"
    mvsa.write_text("@do=F4\n", encoding="utf-8")
    code = vsa_main(["mxl", str(mvsa)])
    err = capsys.readouterr().err
    assert code == 1
    assert "weigert .mvsa" in err
    assert "mvsa mxl" in err


def test_vsa_mxl_rejects_mscz_with_hint(capsys, tmp_path: Path) -> None:
    mscz = tmp_path / "lied.mscz"
    mscz.write_bytes(b"PK\x03\x04")
    code = vsa_main(["mxl", str(mscz)])
    err = capsys.readouterr().err
    assert code == 1
    assert "weigert .mscz" in err
    assert "mscz mxl" in err


def test_vsa_mxl_rejects_o_on_directory(capsys, tmp_path: Path) -> None:
    a = tmp_path / "a.vsa"
    b = tmp_path / "b.vsa"
    a.write_text("{tekst}", encoding="utf-8")
    b.write_text("{tekst}", encoding="utf-8")
    with patch("vsa.cli._export_vsa_to_musicxml", side_effect=_fake_export_mxl):
        code = vsa_main(["mxl", str(tmp_path), "-o", str(tmp_path / "out.mxl")])
    err = capsys.readouterr().err
    assert code == 1
    assert "-o/--output" in err
