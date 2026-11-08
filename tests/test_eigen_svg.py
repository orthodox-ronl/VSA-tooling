"""Eigen partituur-SVG: drie beelden uit Score-IR, naast OSMD en MuseScore."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from vsa.cli_mvsa import main as mvsa_main
from vsa.eigen_svg import EigenSvgError, normalize_eigen_view, render_score_ir_svg
from vsa.score_ir import export_mvsa_to_score_ir

ROOT = Path(__file__).resolve().parents[1]
ALLELUIA = ROOT / "examples" / "bug-cases" / "corib" / "alleluia-toon-8.mvsa"
TOON2 = ROOT / "examples" / "bug-cases" / "corib" / "alleluia-toon-2.mvsa"
LITANIE = ROOT / "examples" / "mvsa" / "1a-vredeslitanie.mvsa"
TRISAGION = ROOT / "examples" / "bug-cases" / "trisagion-8a-hemelum.mvsa"
SLAV = ROOT / "examples" / "mvsa" / "trisagion-8a-slav-hemelum.mvsa"


def _doc(path: Path, **kwargs) -> dict:
    return export_mvsa_to_score_ir(
        path.read_text(encoding="utf-8"),
        title=path.stem,
        source_path=path,
        **kwargs,
    )


def _cy(svg: str, voice: str, index: int) -> float:
    match = re.search(
        rf'data-voice="{voice}"[^>]*data-index="{index}"[^>]*data-cy="([0-9.]+)"',
        svg,
    )
    assert match, f"geen noot {voice} index {index}"
    return float(match.group(1))


def test_normalize_eigen_view() -> None:
    assert normalize_eigen_view(None) == "notes"
    assert normalize_eigen_view("VSA-NOTES") == "vsa-notes"
    with pytest.raises(EigenSvgError):
        normalize_eigen_view("osmd")


def test_alleluia_three_views() -> None:
    doc = _doc(ALLELUIA)
    notes = render_score_ir_svg(doc, view="notes")
    both = render_score_ir_svg(doc, view="vsa-notes")
    bare = render_score_ir_svg(doc, view="vsa")

    # S4 stok, S8 spacer/breve, S13 extender, L2 Source Sans 3 (13/12 pt).
    assert 'data-view="notes"' in notes
    assert "vsa-mark" not in notes
    assert "vsa-underline" not in notes
    assert "melisma-extend" in notes
    assert 'class="staff"' in notes
    assert "Source Sans 3" in notes
    assert 'font-size="13pt"' in notes
    assert 'font-size="12pt"' in notes
    assert 'font-weight="400"' in notes
    assert 'font-weight="700"' not in notes
    assert "woff2" in notes
    assert "DejaVu" not in notes
    # Laatste 'le' (C5) zit boven de alt-G.
    assert _cy(notes, "S", 9) < _cy(notes, "A", 0)
    assert 'data-step="C" data-octave="5"' in notes
    assert "stem-up" in notes and "stem-down" in notes
    assert 'data-kind="spacer"' in notes
    assert 'data-kind="breve"' in notes
    assert 'class="brace"' in notes

    assert re.findall(r'data-ehm="([^"]+)"', both) == [
        "/",
        r"\2",
        r"\2",
        "/",
        "/",
        "/",
        "\\",
    ]
    assert re.findall(r'data-elm="([^"]+)"', both) == ["_", "_", "_", "__"]
    assert "melisma-extend" in both

    assert 'class="staff"' not in bare
    assert 'class="clef"' not in bare
    assert "notehead" not in bare
    assert "vsa-mark" in bare
    assert "melisma-extend" not in bare


def test_toon2_keeps_the_stay_inside_the_melisma() -> None:
    both = render_score_ir_svg(_doc(TOON2), view="vsa-notes")
    tokens = re.findall(r'data-ehm="([^"]+)"', both)
    assert tokens[0] == "-"
    assert tokens.count("-") == 1


def test_litanie_systems_repeats_and_cues() -> None:
    doc = _doc(LITANIE)
    assert [m.get("newSystem") for m in doc["measures"]] == [
        None,
        None,
        True,
        None,
        True,
        None,
    ]
    svg = render_score_ir_svg(doc, view="notes")
    assert svg.count('class="system"') == 3
    assert 'data-style="repeat-start"' in svg
    assert 'data-style="repeat-end"' in svg
    assert 'data-style="light-light"' in svg
    assert re.findall(r'class="measure-number"[^>]*>(\d+)', svg) == ["1", "3", "5"]
    cues = re.findall(r'class="cue" x="([0-9.]+)"[^>]*>([^<]+)', svg)
    laat = next(x for x, text in cues if text.startswith("P: Laat ons"))
    gezegend = next(x for x, text in cues if text.startswith("P: Gezegend"))
    assert float(laat) > float(gezegend) + 120


def test_trisagion_splits_on_nieuw_systeem() -> None:
    svg = render_score_ir_svg(_doc(TRISAGION), view="vsa")
    assert svg.count('class="system"') == 4
    assert 'class="staff"' not in svg
    assert "vsa-mark" in svg


def test_translit_is_a_second_lyric_line() -> None:
    plain = render_score_ir_svg(_doc(SLAV), view="notes")
    translit = render_score_ir_svg(
        _doc(SLAV, translit=True, translit_modus="nls"),
        view="notes",
    )
    assert "lyric-translit" not in plain
    assert "Svja" in translit
    assert "lyric-translit" in translit


def test_navigation_words() -> None:
    text = """\
@do F4
@mode major
@sectie x
L: [segno]a_ | b_[fine] | c_[dsalfine] ||
S: do | re | mi ||
A: do | re | mi ||
T: do | re | mi ||
B: do | re | mi ||
"""
    doc = export_mvsa_to_score_ir(text, title="segno")
    svg = render_score_ir_svg(doc, view="notes")
    assert ">Segno<" in svg
    assert ">Fine<" in svg
    assert ">D.S. al Fine<" in svg


def test_cli_eigen_writes_sibling_and_skips_product_meta(tmp_path: Path) -> None:
    src = tmp_path / "alleluia.mvsa"
    src.write_text(ALLELUIA.read_text(encoding="utf-8"), encoding="utf-8")
    code = mvsa_main(["svg", str(src), "--engine", "eigen", "--view", "vsa-notes"])
    assert code == 0
    out = tmp_path / "alleluia.mvsa.eigen-vsa-notes.svg"
    assert out.is_file()
    assert 'data-view="vsa-notes"' in out.read_text(encoding="utf-8")
    assert not (tmp_path / "alleluia.mvsa.products-meta.json").exists()
    assert not (tmp_path / "alleluia.mvsa.svg").exists()


def test_cli_rejects_view_on_other_engines(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = tmp_path / "lied.mvsa"
    src.write_text(ALLELUIA.read_text(encoding="utf-8"), encoding="utf-8")
    code = mvsa_main(["svg", str(src), "--engine", "osmd", "--view", "vsa"])
    assert code == 1
    assert "--view" in capsys.readouterr().err


def test_cli_rejects_musescore_style(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = tmp_path / "lied.mvsa"
    src.write_text(ALLELUIA.read_text(encoding="utf-8"), encoding="utf-8")
    code = mvsa_main(
        ["svg", str(src), "--engine", "eigen", "--min-system-distance", "9"]
    )
    assert code == 1
    assert "MuseScore-Style" in capsys.readouterr().err


def test_cli_rejects_a_different_lyric_font(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = tmp_path / "lied.mvsa"
    src.write_text(ALLELUIA.read_text(encoding="utf-8"), encoding="utf-8")
    code = mvsa_main(
        ["svg", str(src), "--engine", "eigen", "--lyrics-font", "DejaVu Sans"]
    )
    assert code == 1
    assert "Source Sans 3" in capsys.readouterr().err
