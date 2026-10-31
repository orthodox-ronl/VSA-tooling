"""Tests for mvsa svg --engine osmd (Score-IR → headless OSMD)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from vsa.mvsa_mscz import MvsaMsczError, export_mvsa_to_svg
from vsa.osmd_svg import (
    OsmdSvgError,
    find_osmd_render_script,
    normalize_svg_engine,
)

ROOT = Path(__file__).resolve().parents[1]
VREDE = ROOT / "examples" / "mvsa" / "1a-vredeslitanie.mvsa"


def test_normalize_svg_engine() -> None:
    assert normalize_svg_engine(None) == "musescore"
    assert normalize_svg_engine("OSMD") == "osmd"
    with pytest.raises(OsmdSvgError, match="onbekende"):
        normalize_svg_engine("lilypond")


def test_find_osmd_render_script_in_repo() -> None:
    script = find_osmd_render_script()
    assert script.name == "render.mjs"
    assert script.is_file()
    assert script.parent.name == "osmd-svg"


def test_export_osmd_engine_rejects_keep_mscz(tmp_path: Path) -> None:
    out = tmp_path / "x.svg"
    with pytest.raises(MvsaMsczError, match="keep-mscz"):
        export_mvsa_to_svg(
            VREDE,
            out,
            engine="osmd",
            keep_mscz=tmp_path / "x.mscz",
        )


def test_export_osmd_engine_calls_renderer(tmp_path: Path) -> None:
    out = tmp_path / "vrede.svg"
    keep = tmp_path / "vrede.from-ir.musicxml"

    def _fake_render(musicxml: Path, dest: Path, **_kwargs) -> Path:
        assert musicxml.is_file()
        assert musicxml.read_text(encoding="utf-8").lstrip().startswith("<?xml")
        dest.write_text(
            '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>\n',
            encoding="utf-8",
        )
        return dest

    with patch("vsa.osmd_svg.render_musicxml_to_svg", side_effect=_fake_render):
        written = export_mvsa_to_svg(
            VREDE,
            out,
            engine="osmd",
            keep_mxl=keep,
        )
    assert written == [out]
    assert out.is_file()
    assert keep.is_file()
    assert "score-partwise" in keep.read_text(encoding="utf-8") or "<score-" in keep.read_text(
        encoding="utf-8"
    )
