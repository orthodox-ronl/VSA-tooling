"""Tests voor mvsa → vsa (E1–E6), default stem S."""

from __future__ import annotations

from pathlib import Path

import pytest

from vsa.cli_mvsa import main as mvsa_main
from vsa.derived_path import derived_output_path
from vsa.input_paths import collect_cli_sources, is_nested_derived_source
from vsa.mvsa_vsa import (
    MvsaVsaError,
    convert_mvsa_to_vsa,
    convert_mvsa_to_vsa_text,
    default_mvsa_vsa_output,
    degree_delta_to_ehm,
    start_marker_for_degree,
)
from vsa.yaml_frontmatter import parse_vsa_frontmatter
from vsa.zoektekst import check_zoektekst

_REPO = Path(__file__).resolve().parents[1]
_FIXTURE = _REPO / "tests" / "fixtures" / "mvsa_vsa_mini.mvsa"
_UW = _REPO / "tests" / "fixtures" / "uw_heilig_kruis.mvsa"


def test_degree_delta_to_ehm_basics() -> None:
    assert degree_delta_to_ehm(0) == "-"
    assert degree_delta_to_ehm(1) == "/"
    assert degree_delta_to_ehm(2) == "//"
    assert degree_delta_to_ehm(-1) == "\\"
    assert degree_delta_to_ehm(1, 1.0) == "#/"
    assert start_marker_for_degree(0) == "[:]"
    assert start_marker_for_degree(-1) == "[\\:]"


def test_default_output_paths() -> None:
    src = Path("lied.mvsa")
    # Enkele stem (default of --voice x): altijd .mvsa.vsa
    assert default_mvsa_vsa_output(src) == Path("lied.mvsa.vsa")
    # Alleen --voice all zet voice_label → .mvsa.{stem}.vsa
    assert default_mvsa_vsa_output(src, voice_label="S") == Path("lied.mvsa.s.vsa")
    assert default_mvsa_vsa_output(src, voice_label="A") == Path("lied.mvsa.a.vsa")
    assert default_mvsa_vsa_output(src, voice_label="t") == Path("lied.mvsa.t.vsa")
    assert derived_output_path(src, ".vsa") == Path("lied.mvsa.vsa")


@pytest.mark.skipif(not _FIXTURE.is_file(), reason="fixture ontbreekt")
def test_convert_mini_s_default(tmp_path: Path) -> None:
    bron = tmp_path / _FIXTURE.name
    bron.write_text(_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    out = convert_mvsa_to_vsa(bron, voice="S")
    assert out == tmp_path / "mvsa_vsa_mini.mvsa.vsa"
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    fm, body = parse_vsa_frontmatter(text)
    assert fm["herkomst"]["generator"] == "mvsa-vsa"
    assert fm["herkomst"]["bron"] == bron.name
    assert fm["herkomst"]["stem"] == "S"
    assert fm.get("soort") == "tropaar"
    assert fm.get("do") == "G4"
    assert "*" in body
    assert body.strip().startswith("[")
    assert body.rstrip().endswith("[:]")
    # Twee maten → twee strofen
    assert body.count("*") >= 1


@pytest.mark.skipif(not _FIXTURE.is_file(), reason="fixture ontbreekt")
def test_convert_unknown_voice_errors() -> None:
    text = _FIXTURE.read_text(encoding="utf-8")
    with pytest.raises(MvsaVsaError, match="komt niet voor"):
        convert_mvsa_to_vsa_text(text, source_name="x.mvsa", voice="cantus")


@pytest.mark.skipif(not _FIXTURE.is_file(), reason="fixture ontbreekt")
def test_cli_mvsa_vsa_writes_sibling(tmp_path: Path) -> None:
    bron = tmp_path / _FIXTURE.name
    bron.write_text(_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    assert mvsa_main(["vsa", str(bron)]) == 0
    out = tmp_path / "mvsa_vsa_mini.mvsa.vsa"
    assert out.is_file()
    assert "herkomst" in out.read_text(encoding="utf-8")


@pytest.mark.skipif(not _UW.is_file(), reason="uw_heilig fixture ontbreekt")
def test_uw_heilig_kruis_s_emit_basics() -> None:
    text = convert_mvsa_to_vsa_text(
        _UW.read_text(encoding="utf-8"),
        source_name="uw_heilig_kruis.mvsa",
    )
    fm, body = parse_vsa_frontmatter(text)
    assert fm["titel"] == "Uw Heilig Kruis"
    assert fm["herkomst"]["stem"] == "S"
    assert fm["do"] == "G4"
    assert fm["tempo"] == 150
    # Twee maten → één * tussen strofen
    assert body.count("*") == 1
    assert body.lstrip().startswith("[\\:]")
    assert "Uw" in body
    # Stay na frasegrens: kale Uw, geen {-Uw}
    assert "{-Uw}" not in body
    assert "{//en} Uw" in body or "{//en}Uw" in body
    # Melisma bie met duur-ELMs
    assert "bie_&_" in body
    # Melisma ver zonder ~ in tekst
    assert "{/&/ver}" in body
    # Zoektekst: literal block, frase per regel, geen lege regels
    assert "zoektekst: |" in text
    zt = str(fm["zoektekst"])
    assert "\n\n" not in zt
    assert zt.count("\n") >= 1  # minstens twee frasen
    assert "heilig" in zt.lower()
    assert not any(ln.strip() == "" for ln in zt.splitlines())
    assert check_zoektekst(text, kind="vsa", require=True) == []
    assert "\n\n" not in body


@pytest.mark.skipif(not _UW.is_file(), reason="uw_heilig fixture ontbreekt")
def test_uw_heilig_voice_a_still_mvsa_vsa(tmp_path: Path) -> None:
    bron = tmp_path / _UW.name
    bron.write_text(_UW.read_text(encoding="utf-8"), encoding="utf-8")
    out = convert_mvsa_to_vsa(bron, voice="A")
    assert out.name == "uw_heilig_kruis.mvsa.vsa"
    fm, _body = parse_vsa_frontmatter(out.read_text(encoding="utf-8"))
    assert fm["herkomst"]["stem"] == "A"


@pytest.mark.skipif(not _UW.is_file(), reason="uw_heilig fixture ontbreekt")
def test_cli_voice_all_writes_per_stem_including_s(tmp_path: Path) -> None:
    bron = tmp_path / _UW.name
    bron.write_text(_UW.read_text(encoding="utf-8"), encoding="utf-8")
    assert mvsa_main(["vsa", str(bron), "--voice", "all"]) == 0
    names = sorted(p.name for p in tmp_path.glob("*.vsa"))
    assert "uw_heilig_kruis.mvsa.s.vsa" in names
    assert "uw_heilig_kruis.mvsa.a.vsa" in names
    assert "uw_heilig_kruis.mvsa.t.vsa" in names
    assert "uw_heilig_kruis.mvsa.b.vsa" in names
    assert "uw_heilig_kruis.mvsa.vsa" not in names
    fm, _ = parse_vsa_frontmatter(
        (tmp_path / "uw_heilig_kruis.mvsa.s.vsa").read_text(encoding="utf-8")
    )
    assert fm["herkomst"]["stem"] == "S"


@pytest.mark.skipif(not _FIXTURE.is_file(), reason="fixture ontbreekt")
def test_batch_skips_nested_mvsa(tmp_path: Path) -> None:
    bare = tmp_path / "lied.mvsa"
    nested = tmp_path / "lied.mscz.mvsa"
    bare.write_text(_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    nested.write_text(_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    assert is_nested_derived_source(nested)
    files = collect_cli_sources(tmp_path, suffixes=(".mvsa",))
    assert bare in files
    assert nested not in files
    # Expliciet pad mag wel
    assert collect_cli_sources(nested, suffixes=(".mvsa",)) == [nested]
