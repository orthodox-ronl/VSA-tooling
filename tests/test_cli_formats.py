"""Smoke tests for top-level mvsa / mxl / mscz entry points."""

from __future__ import annotations

import pytest

from vsa.cli_md import main as md_main
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
    assert "kuiser" in out
    assert (
        "{validate,mxl,mscz,pdf,svg,mp3,ogg,wav,score-ir,"
        "normalize,transpose,kuiser,text,import,products}"
    ) in out
    assert "pdf" in out
    assert "svg" in out


def test_mxl_help_lists_matrix_actions(capsys):
    with pytest.raises(SystemExit) as exc:
        mxl_main(["-h"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "mvsa" in out
    assert "{mvsa,mscz,validate,normalize}" in out
    assert "mscz" in out


def test_mscz_help_lists_matrix_actions(capsys):
    with pytest.raises(SystemExit) as exc:
        mscz_main(["-h"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "mvsa" in out
    assert "mp3" in out
    assert "score-ir" in out
    assert "mxl" in out
    assert "svg" in out
    assert "pdf" in out
    assert "normalize" in out
    assert "compare" in out
    assert "products" in out


def test_md_help_lists_products(capsys):
    with pytest.raises(SystemExit) as exc:
        md_main(["-h"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "{pdf,svg,text}" in out
    assert "pdf" in out
    assert "svg" in out
    assert "text" in out


def test_mvsa_validate_alias_works():
    assert mvsa_main(["validate", "examples/mvsa/alleluia-toon-8.mvsa"]) == 0


def test_mvsa_validate_success_prints_single_ok(capsys):
    assert mvsa_main(["validate", "examples/mvsa/alleluia-toon-8.mvsa"]) == 0
    out = capsys.readouterr().out.strip()
    assert out == "OK"
    assert ": OK" not in out

def test_vsa_rejects_nested_mvsa(capsys):
    from vsa.cli import main as vsa_main

    with pytest.raises(SystemExit) as exc:
        vsa_main(["mvsa", "validate", "examples/mvsa/alleluia-toon-8.mvsa"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "invalid choice: 'mvsa'" in err
