"""Fase 7e: normalize aanwezig per straat-CLI (help), geen vsa-normalize."""

from __future__ import annotations

import pytest

from vsa.cli import main as vsa_main
from vsa.cli_mscz import main as mscz_main
from vsa.cli_mvsa import main as mvsa_main
from vsa.cli_mxl import main as mxl_main


def test_mvsa_help_exposes_normalize(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        mvsa_main(["-h"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "normalize" in out
    assert "mvsa normalize" in out or "normalize PATH" in out


def test_mxl_help_exposes_normalize(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        mxl_main(["-h"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "normalize" in out
    assert "{mvsa,mscz,validate,normalize}" in out


def test_mscz_help_exposes_normalize(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        mscz_main(["-h"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "normalize" in out
    assert "normalize" in out.split("{", 1)[-1].split("}", 1)[0]


def test_vsa_has_no_normalize_subcommand(capsys) -> None:
    """Check: geen aparte ``vsa normalize`` (canonieke .vsa = validate/spec)."""
    with pytest.raises(SystemExit) as exc:
        vsa_main(["normalize", "-h"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "invalid choice" in err or "unrecognized" in err.lower()


def test_normalize_subhelp_mvsa_mxl_mscz() -> None:
    for main, args in (
        (mvsa_main, ["normalize", "-h"]),
        (mxl_main, ["normalize", "-h"]),
        (mscz_main, ["normalize", "-h"]),
    ):
        with pytest.raises(SystemExit) as exc:
            main(args)
        assert exc.value.code == 0
