"""``vsa mvsa`` valideert zijn eigen uitvoer en faalt dan zichtbaar."""

from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

import pytest

from vsa import cli_vsa_mvsa
from vsa.cli_vsa_mvsa import run_vsa_mvsa

BAD = "@do F4\n@mode major\n\n@sectie demo\nL: (ver-hoor_) mij_ |\nS: g  /  |\nA: e  /  |\nT: c  /  |\nB: c  /  |\n"
GOOD = BAD.replace("(ver-hoor_)", "(ver-hoor)_")


def _run(monkeypatch, tmp_path: Path, text: str) -> int:
    out = tmp_path / "x.vsa.mvsa"
    out.write_text(text, encoding="utf-8")

    def fake(*_a, **_k):
        return SimpleNamespace(
            text=text,
            output_path=out,
            warnings=[],
            phrase_ids=["1"],
            resolved=SimpleNamespace(canonical_id="t", formula_id="t"),
        )

    monkeypatch.setattr(cli_vsa_mvsa, "convert_vsa_to_mvsa", fake)
    args = argparse.Namespace(
        path=str(tmp_path / "x.vsa"),
        template=None,
        output=str(out),
        melody="S",
        library=None,
        list_templates=False,
        tempo=None,
    )
    return run_vsa_mvsa(args)


def test_invalid_output_fails(monkeypatch, tmp_path: Path, capsys) -> None:
    assert _run(monkeypatch, tmp_path, BAD) == 1
    err = capsys.readouterr().err
    assert "MVSA-RECITE-INTERIOR-ELM" in err
    assert "ongeldig" in err


def test_valid_output_passes(monkeypatch, tmp_path: Path, capsys) -> None:
    assert _run(monkeypatch, tmp_path, GOOD) == 0
