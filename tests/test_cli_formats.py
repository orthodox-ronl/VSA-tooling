"""Smoke tests for top-level mvsa / mxl / mscz entry points."""

from __future__ import annotations

import pytest

from vsa.cli_mscz import main as mscz_main
from vsa.cli_mvsa import main as mvsa_main
from vsa.cli_mxl import main as mxl_main


def test_mvsa_help_lists_subcommands(capsys):
    with pytest.raises(SystemExit) as exc:
        mvsa_main(["-h"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "validate" in out
    assert "normalize" in out
    assert "import" in out


def test_mxl_help_lists_matrix_actions(capsys):
    with pytest.raises(SystemExit) as exc:
        mxl_main(["-h"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "import" in out
    assert "mscz" in out


def test_mscz_help_lists_matrix_actions(capsys):
    with pytest.raises(SystemExit) as exc:
        mscz_main(["-h"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "import" in out
    assert "mxl" in out


def test_mvsa_validate_alias_works():
    assert mvsa_main(["validate", "examples/mvsa/alleluia-toon-8.canonieke.mvsa"]) == 0
