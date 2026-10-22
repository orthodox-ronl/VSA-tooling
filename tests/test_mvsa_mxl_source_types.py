"""mvsa mxl accepteert .mvsa/.mscz/.mxl; geen UTF-8-crash op binaire bronnen."""

from __future__ import annotations

from pathlib import Path

import pytest

from vsa.cli import main
from vsa.mvsa_musicxml import MvsaExportError, export_mvsa_path
from vsa.mvsa_validate import collect_mvsa_files


def test_collect_mvsa_files_ignores_mscz(tmp_path: Path) -> None:
    mscz = tmp_path / "lied.mscz"
    mscz.write_bytes(b"PK\x03\x04binary")
    assert collect_mvsa_files(mscz) == []
    mvsa = tmp_path / "lied.mvsa"
    mvsa.write_text("@do=F4\n", encoding="utf-8")
    assert collect_mvsa_files(mvsa) == [mvsa]


def test_export_mvsa_path_rejects_mscz(tmp_path: Path) -> None:
    mscz = tmp_path / "lied.mscz"
    mscz.write_bytes(b"PK\x03\x04\xba\x00not-text")
    out = tmp_path / "out.mxl"
    with pytest.raises(MvsaExportError, match=r"verwacht \.mvsa"):
        export_mvsa_path(mscz, out)


def test_mvsa_mxl_rejects_unknown_suffix_clearly(capsys, tmp_path: Path) -> None:
    junk = tmp_path / "lied.pdf"
    junk.write_bytes(b"%PDF-1.4\xba")
    code = main(["mvsa", "mxl", str(junk)])
    err = capsys.readouterr().err
    assert code == 1
    assert "utf-8" not in err.lower()
    assert "Verwacht bestand met extensie" in err
    assert ".mvsa" in err
    assert "lied.pdf" in err


def test_mvsa_validate_mscz_no_utf8_crash(capsys, tmp_path: Path) -> None:
    mscz = tmp_path / "lied.mscz"
    mscz.write_bytes(b"PK\x03\x04\xba\x00")
    code = main(["mvsa", "validate", str(mscz)])
    err = capsys.readouterr().err
    assert code == 1
    assert "utf-8" not in err.lower()
    assert "Geen .mvsa gevonden" in err


def test_mvsa_mscz_rejects_mscz_source(capsys, tmp_path: Path) -> None:
    mscz = tmp_path / "lied.mscz"
    mscz.write_bytes(b"PK\x03\x04\xba")
    code = main(["mvsa", "mscz", str(mscz)])
    err = capsys.readouterr().err
    assert code == 1
    assert "utf-8" not in err.lower()
    assert "Verwacht bestand met extensie" in err
    assert ".mvsa" in err
    assert "lied.mscz" in err
