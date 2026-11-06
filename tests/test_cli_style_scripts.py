"""Tests voor scripts/cli_style.py (repo-scripts console-rollen)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import cli_style as cs  # noqa: E402


def test_format_count_aligns() -> None:
    assert cs.format_count(12, "stale-mxl") == " 12  stale-mxl"
    assert cs.format_count(3, "missing-pdf") == "  3  missing-pdf"


def test_count_and_refuse(capsys: pytest.CaptureFixture[str], monkeypatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    cs.count(12, "ok-items", role="ok")
    cs.refuse("WEIGERT  doel bestaat al")
    out = capsys.readouterr().out
    assert " 12  ok-items" in out
    assert "WEIGERT  doel bestaat al" in out


def test_detail_gate(capsys: pytest.CaptureFixture[str]) -> None:
    cs.set_verbose(False)
    cs.detail("stil")
    assert capsys.readouterr().out == ""
    cs.set_verbose(True)
    try:
        cs.detail("luid")
        assert "luid" in capsys.readouterr().out
    finally:
        cs.set_verbose(False)
