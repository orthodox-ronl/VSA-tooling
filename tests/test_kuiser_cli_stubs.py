"""Straat-kuiser stubs: ontbrekende spec → exit 2 + hub-verwijzing."""

from __future__ import annotations

from vsa.cli import main as vsa_main
from vsa.cli_mscz import main as mscz_main
from vsa.cli_mxl import main as mxl_main
from vsa.kuiser_cli import kuiser_spec_missing_message


def test_kuiser_spec_missing_message_mentions_hub():
    msg = kuiser_spec_missing_message("mscz")
    assert "kuiser.md" in msg
    assert "mscz" in msg


def test_vsa_kuiser_missing_path(capsys):
    code = vsa_main(["kuiser", "x-does-not-exist.vsa"])
    err = capsys.readouterr().err
    assert code == 1
    assert "niet gevonden" in err.lower() or "Pad" in err


def test_mscz_kuiser_stub(capsys):
    code = mscz_main(["kuiser", "x.mscz"])
    out = capsys.readouterr().out
    assert code == 2
    assert "geen kuiser-spec" in out
    assert "kuiser.md" in out


def test_mxl_kuiser_stub(capsys):
    code = mxl_main(["kuiser", "x.mxl"])
    out = capsys.readouterr().out
    assert code == 2
    assert "geen kuiser-spec" in out
    assert "kuiser.md" in out
