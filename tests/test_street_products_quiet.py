"""--quiet dempt voortgang op stdout; fouten blijven zichtbaar."""

from __future__ import annotations

from pathlib import Path

from vsa.street_products import products_mscz_one


def test_quiet_dry_run_no_stdout(tmp_path: Path, capsys) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04")
    # force+dry-run: plan loggen zonder MuseScore
    assert products_mscz_one(bron, force=True, dry_run=True, quiet=True) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "mxl" not in captured.out


def test_verbose_dry_run_lists_plan(tmp_path: Path, capsys) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04")
    assert products_mscz_one(bron, force=True, dry_run=True, quiet=False) == 0
    out = capsys.readouterr().out
    assert "mxl" in out
    assert "lied.mscz" in out
