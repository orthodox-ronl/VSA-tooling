"""Tests for destination-street ``mvsa import`` / ``mscz import``."""

from __future__ import annotations

from pathlib import Path

import pytest

from vsa.cli_mscz import main as mscz_main
from vsa.cli_mvsa import main as mvsa_main
from vsa.cli_mxl import main as mxl_main

_REPO = Path(__file__).resolve().parents[1]
_MXL = _REPO / "examples" / "importer" / "tweede-antifoon-zondag-hemelum.mxl"


def test_mvsa_import_rejects_wrong_extension(tmp_path: Path, capsys) -> None:
    bad = tmp_path / "x.vsa"
    bad.write_text("title: t\n---\na4.\n", encoding="utf-8")
    assert mvsa_main(["import", str(bad)]) == 1
    err = capsys.readouterr().err
    assert "niet is toegestaan" in err
    assert ".mscz" in err


def test_mscz_import_rejects_wrong_extension(tmp_path: Path, capsys) -> None:
    bad = tmp_path / "x.vsa"
    bad.write_text("title: t\n---\na4.\n", encoding="utf-8")
    assert mscz_main(["import", str(bad)]) == 1
    err = capsys.readouterr().err
    assert "niet is toegestaan" in err
    assert ".mvsa" in err


@pytest.mark.skipif(not _MXL.is_file(), reason="example .mxl ontbreekt")
def test_mvsa_import_mxl_parity_with_mxl_mvsa(tmp_path: Path) -> None:
    out_a = tmp_path / "via-import.mvsa"
    out_b = tmp_path / "via-mxl-mvsa.mvsa"
    assert mvsa_main(["import", str(_MXL), "-o", str(out_a)]) == 0
    assert mxl_main(["mvsa", str(_MXL), "-o", str(out_b)]) == 0
    assert out_a.read_text(encoding="utf-8") == out_b.read_text(encoding="utf-8")


@pytest.mark.skipif(not _MXL.is_file(), reason="example .mxl ontbreekt")
def test_mscz_import_mxl_writes_mscz(tmp_path: Path) -> None:
    """Parity path mxl→mscz without asserting MuseScore binary identity."""
    from vsa.musescore_cli import find_musescore

    if find_musescore() is None:
        pytest.skip("MuseScore niet geïnstalleerd")
    out = tmp_path / "from-import.mscz"
    assert mscz_main(["import", str(_MXL), "-o", str(out)]) == 0
    assert out.is_file()
    assert out.stat().st_size > 0
