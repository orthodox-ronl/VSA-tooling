"""Officiële ``vsa mvsa`` / ``convert_vsa_to_mvsa`` (T1–T7)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vsa.cli_vsa_mvsa import run_vsa_mvsa
from vsa.template_library import (
    DEFAULT_OCT_LINE,
    DEFAULT_TEMPO_TROPAAR_KONDAK,
    DEFAULT_TEMPLATE_ID,
    load_resolved_template,
    resolve_template_id,
)
from vsa.vsa_mvsa import (
    _tempo_from_meta,
    clean_emit_frontmatter,
    convert_vsa_to_mvsa,
    emit_sections_enabled,
    section_id_for_phrase_index,
)

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "docs" / "specification-vsa-templates" / "library"
ELIA = LIBRARY / "tropaar-toon-4" / "examples" / "corpus" / "T4-06-profeet-elia.vsa"
T2_VSA = LIBRARY / "tropaar-toon-2" / "examples" / "corpus" / "T2-groningen-zondag.vsa"
K5_VSA = LIBRARY / "kondak-toon-5" / "examples" / "corpus" / "K5-groningen-zondag.vsa"


def test_tempo_ignores_vsa_frontmatter() -> None:
    assert DEFAULT_TEMPO_TROPAAR_KONDAK == 180
    assert _tempo_from_meta({"tempo": 132}) == 180
    assert _tempo_from_meta({}) == 180


def test_clean_emit_frontmatter_drops_playback() -> None:
    fm = clean_emit_frontmatter(
        {
            "do": "F4",
            "mode": "major",
            "tempo": 132,
            "template": "kondak-toon-5",
            "titel": "Kondak test",
            "toon": 5,
            "taal": "nl",
            "zoektekst": "abc",
        }
    )
    assert fm.startswith("---")
    assert "titel: Kondak test" in fm
    assert "toon: 5" in fm
    assert "zoektekst: abc" in fm
    assert "do:" not in fm
    assert "mode:" not in fm
    assert "tempo:" not in fm
    assert "template:" not in fm


def test_section_id_for_phrase_index_cycle() -> None:
    ids = ["1", "2", "3", "1", "2", "3", "1", "laatste"]
    assert section_id_for_phrase_index(0, ids, cycle_len=3) == "cyclus-1"
    assert section_id_for_phrase_index(2, ids, cycle_len=3) == "cyclus-1"
    assert section_id_for_phrase_index(3, ids, cycle_len=3) == "herhaling"
    assert section_id_for_phrase_index(6, ids, cycle_len=3) == "herhaling"
    assert section_id_for_phrase_index(7, ids, cycle_len=3) == "laatste"


def test_emit_sections_disabled_for_tone_3() -> None:
    assert emit_sections_enabled({"tone": 3}) is False
    assert emit_sections_enabled({"tone": 5}) is True


def test_resolve_default_and_alias() -> None:
    assert resolve_template_id(None) == DEFAULT_TEMPLATE_ID
    assert resolve_template_id("hemelum-tropaar-toon-4") == "tropaar-toon-4"
    assert resolve_template_id("groningen-tropaar-toon-4") == (
        "groningen-tropaar-toon-4"
    )


def test_load_same_as_tropaar_toon_2() -> None:
    resolved = load_resolved_template("tropaar-toon-2")
    assert resolved.canonical_id == "tropaar-toon-2"
    assert resolved.formula_id == "kondak-toon-2"
    assert "phrases" in resolved.doc
    assert resolved.doc["id"] == "tropaar-toon-2"


@pytest.mark.skipif(not ELIA.is_file(), reason="corpus Elia ontbreekt")
def test_convert_elia_default_template_oct_a0(tmp_path: Path) -> None:
    out = tmp_path / "elia.mvsa"
    result = convert_vsa_to_mvsa(ELIA, output=out, write=True)
    assert result.output_path == out
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert DEFAULT_OCT_LINE in text
    assert result.resolved.canonical_id == "tropaar-toon-4"
    # Alt schrijft f (F4), niet f+ (F5 bij A=0).
    a_lines = [ln for ln in text.splitlines() if ln.startswith("A:")]
    assert a_lines
    assert not any(
        ln.split("|", 1)[0].startswith("A: f+")
        or " f+ " in ln.split("|", 1)[0]
        for ln in a_lines
    )


@pytest.mark.skipif(not T2_VSA.is_file(), reason="corpus toon 2 ontbreekt")
def test_convert_tropaar_toon_2_via_same_as(tmp_path: Path) -> None:
    out = tmp_path / "t2.mvsa"
    result = convert_vsa_to_mvsa(
        T2_VSA, template="tropaar-toon-2", output=out, write=True
    )
    assert result.resolved.formula_id == "kondak-toon-2"
    assert result.phrase_ids[-1] == "laatste"
    assert "formule kondak-toon-2" in result.text or "kondak-toon-2" in result.text


@pytest.mark.skipif(not K5_VSA.is_file(), reason="corpus kondak-5 ontbreekt")
def test_convert_emit_no_speelplan_blok_has_secties(tmp_path: Path) -> None:
    """T6/emit-vorm: geen @speelplan/@blok; wel secties + VSA-commentaar."""
    out = tmp_path / "k5.mvsa"
    result = convert_vsa_to_mvsa(
        K5_VSA, template="kondak-toon-5", output=out, write=True
    )
    text = result.text
    assert "@speelplan" not in text
    assert "@blok" not in text
    assert "@sectie cyclus-1" in text
    assert "@sectie herhaling" in text
    assert "@sectie laatste" in text
    assert "# === oorspronkelijke VSA (commentaar) ===" in text
    assert "# template:" in text
    assert "WAARSCHUWING:" in text
    assert "@tempo 180" in text
    assert text.index("@sectie cyclus-1") < text.index("@sectie herhaling")
    assert text.index("@sectie herhaling") < text.index("@sectie laatste")
    # Gekuiste FM: geen do/mode/tempo in YAML-kop.
    fm = text.split("---", 2)[1]
    assert "do:" not in fm
    assert "tempo:" not in fm
    assert "titel:" in fm


def test_cli_list_templates() -> None:
    ns = type("NS", (), {"list_templates": True, "library": None, "path": None})()
    assert run_vsa_mvsa(ns) == 0


@pytest.mark.skipif(not ELIA.is_file(), reason="corpus Elia ontbreekt")
def test_cli_writes_sibling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "x.vsa"
    src.write_text(ELIA.read_text(encoding="utf-8"), encoding="utf-8")
    ns = type(
        "NS",
        (),
        {
            "list_templates": False,
            "library": None,
            "path": str(src),
            "template": "tropaar-toon-4",
            "output": None,
            "melody": "S",
            "tempo": None,
        },
    )()
    assert run_vsa_mvsa(ns) == 0
    assert src.with_suffix(".mvsa").is_file()
