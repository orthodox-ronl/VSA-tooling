"""Officiële ``vsa mvsa`` / ``convert_vsa_to_mvsa`` (T1–T7)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vsa.cli_vsa_mvsa import run_vsa_mvsa
from vsa.template_library import (
    DEFAULT_OCT_LINE,
    DEFAULT_TEMPO_TROPAAR_KONDAK,
    DEFAULT_TEMPLATE_ID,
    TemplateLibraryError,
    infer_template_id,
    list_templates_for_soort_toon,
    load_resolved_template,
    resolve_template_id,
    select_template_id,
)
from vsa.template_instance import TemplateInstanceError
from vsa.vsa_mvsa import (
    _tempo_from_meta,
    clean_emit_frontmatter,
    convert_vsa_to_mvsa,
    emit_sections_enabled,
    find_fitting_alternate_templates,
    format_alternate_template_hint,
    section_id_for_phrase_index,
)
from vsa.template_library import load_resolved_template

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "docs" / "specification-vsa-templates" / "library"
ELIA = LIBRARY / "tropaar-toon-4-hemelum" / "examples" / "corpus" / "T4-06-profeet-elia.vsa"
T2_VSA = LIBRARY / "tropaar-toon-2-groningen" / "examples" / "corpus" / "T2-groningen-zondag.vsa"
K5_VSA = LIBRARY / "kondak-toon-5-groningen" / "examples" / "corpus" / "K5-groningen-zondag.vsa"
K8_HEMELUM_VSA = (
    LIBRARY
    / "kondak-toon-8-hemelum"
    / "examples"
    / "corpus"
    / "K8-hemelum-gestorvenen.vsa"
)


def test_tempo_ignores_vsa_frontmatter() -> None:
    assert DEFAULT_TEMPO_TROPAAR_KONDAK == 180
    assert _tempo_from_meta({"tempo": 132}) == 180
    assert _tempo_from_meta({}) == 180


def test_clean_emit_frontmatter_drops_playback_keeps_template() -> None:
    fm = clean_emit_frontmatter(
        {
            "do": "F4",
            "mode": "major",
            "tempo": 132,
            "titel": "Kondak test",
            "toon": 5,
            "soort": "kondak",
            "taal": "nl",
            "bron": {"uitgangspunt": "Koormap Groningen"},
            "gelegenheid": [{"naam": "Zondag", "type": "zondag"}],
            "zoektekst": "abc",
        },
        template_id="kondak-toon-5-groningen",
        template_opgegeven="kondak-toon-5",
    )
    assert fm.startswith("---")
    assert "titel: Kondak test" in fm
    assert "soort: kondak" in fm
    assert "toon: 5" in fm
    assert "zoektekst: abc" in fm
    assert "bron:" in fm
    assert "gelegenheid:" in fm
    assert "template: kondak-toon-5-groningen" in fm
    assert "template_opgegeven: kondak-toon-5" in fm
    assert "do:" not in fm
    assert "mode:" not in fm
    assert "tempo:" not in fm
    # soort direct boven toon; template na toon
    body = fm.split("---", 2)[1]
    assert body.index("soort:") < body.index("toon:") < body.index("template:")
    assert abs(body.index("soort:") - body.index("toon:")) < 40


def test_clean_emit_frontmatter_maps_legacy_title_genre_tone() -> None:
    fm = clean_emit_frontmatter(
        {"title": "X", "genre": "tropaar", "tone": 4},
        template_id="tropaar-toon-4-hemelum",
    )
    assert "titel: X" in fm
    assert "soort: tropaar" in fm
    assert "toon: 4" in fm


def test_clean_emit_frontmatter_omits_opgegeven_when_same() -> None:
    fm = clean_emit_frontmatter(
        {"titel": "x"},
        template_id="kondak-toon-5-groningen",
        template_opgegeven="kondak-toon-5-groningen",
    )
    assert "template: kondak-toon-5-groningen" in fm
    assert "template_opgegeven" not in fm


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
    assert resolve_template_id("hemelum-tropaar-toon-4") == "tropaar-toon-4-hemelum"
    assert resolve_template_id("tropaar-toon-4") == "tropaar-toon-4-hemelum"
    assert resolve_template_id("groningen-tropaar-toon-4") == (
        "tropaar-toon-4-groningen"
    )
    assert resolve_template_id("kondak-toon-8") == "kondak-toon-8-groningen"


def test_list_templates_for_soort_toon() -> None:
    assert list_templates_for_soort_toon("kondak", 8) == [
        "kondak-toon-8-groningen",
        "kondak-toon-8-hemelum",
    ]
    # Alleen Groningen bestaat → één kandidaat (ook bij gevraagde hemelum-bron).
    assert list_templates_for_soort_toon("kondak", 5) == [
        "kondak-toon-5-groningen"
    ]
    # kondak-toon-4-* zijn aliassen → tropaar-toon-4-*.
    assert list_templates_for_soort_toon("kondak", 4) == [
        "tropaar-toon-4-groningen",
        "tropaar-toon-4-hemelum",
    ]


def test_select_template_id_unique_and_bron() -> None:
    assert (
        select_template_id(
            soort="kondak",
            toon=8,
            bron="hemelum",
            path="kondak-zaterdag-gestorvenen-toon-8-hemelum.vsa",
        )
        == "kondak-toon-8-hemelum"
    )
    assert select_template_id(soort="kondak", toon=5) == "kondak-toon-5-groningen"
    assert (
        select_template_id(
            path="kondak-icoon-moeder-gods-vladimir-toon-8-liturgikon.vsa",
            soort="kondak",
            toon=8,
        )
        == "kondak-toon-8-hemelum"
    )
    assert (
        select_template_id(
            soort="tropaar",
            toon=4,
            path="tropaar-nikolaas-van-myra-toon-4-hemelum.mvsa",
        )
        == "tropaar-toon-4-hemelum"
    )


def test_select_template_id_ambiguous_without_hint() -> None:
    with pytest.raises(TemplateLibraryError, match="meerdere templates"):
        select_template_id(soort="kondak", toon=8)


def test_select_template_id_missing() -> None:
    with pytest.raises(TemplateLibraryError, match="geen template"):
        select_template_id(soort="stichier", toon=1)


def test_select_template_id_from_existing_mvsa(tmp_path: Path) -> None:
    out = tmp_path / "x.mvsa"
    # template_opgegeven (alias) wint; moet bij soort/toon-kandidaten horen.
    out.write_text(
        "---\n"
        "template: kondak-toon-8-hemelum\n"
        "template_opgegeven: kondak-toon-8-liturgikon\n"
        "---\n\n@title x\n",
        encoding="utf-8",
    )
    assert (
        select_template_id(soort="kondak", toon=8, output=out)
        == "kondak-toon-8-liturgikon"
    )


def test_infer_template_id_compat_wrapper() -> None:
    assert infer_template_id(soort="kondak", toon=5) == "kondak-toon-5-groningen"


def test_load_same_as_tropaar_toon_2() -> None:
    resolved = load_resolved_template("tropaar-toon-2-groningen")
    assert resolved.canonical_id == "tropaar-toon-2-groningen"
    assert resolved.formula_id == "kondak-toon-2-groningen"
    assert "phrases" in resolved.doc
    assert resolved.doc["id"] == "tropaar-toon-2-groningen"


@pytest.mark.skipif(not ELIA.is_file(), reason="corpus Elia ontbreekt")
def test_convert_elia_default_template_oct_a0(tmp_path: Path) -> None:
    out = tmp_path / "elia.mvsa"
    result = convert_vsa_to_mvsa(ELIA, output=out, write=True)
    assert result.output_path == out
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert DEFAULT_OCT_LINE in text
    assert result.resolved.canonical_id == "tropaar-toon-4-hemelum"
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
        T2_VSA, template="tropaar-toon-2-groningen", output=out, write=True
    )
    assert result.resolved.formula_id == "kondak-toon-2-groningen"
    assert result.phrase_ids[-1] == "laatste"
    assert "formule kondak-toon-2-groningen" in result.text or "kondak-toon-2-groningen" in result.text


@pytest.mark.skipif(not K8_HEMELUM_VSA.is_file(), reason="corpus kondak-8-hemelum ontbreekt")
def test_alternate_template_suggestion_on_pitch_mismatch() -> None:
    """T4: Groningen faalt op Hemelum-VSA → suggestie kondak-toon-8-hemelum."""
    text = K8_HEMELUM_VSA.read_text(encoding="utf-8")
    failed = load_resolved_template("kondak-toon-8-groningen")
    fitting = find_fitting_alternate_templates(
        text,
        failed=failed,
        soort="kondak",
        toon=8,
        source_name=K8_HEMELUM_VSA.name,
    )
    assert "kondak-toon-8-hemelum" in fitting
    hint = format_alternate_template_hint(
        failed_id="kondak-toon-8-groningen",
        fitting=fitting,
        source=K8_HEMELUM_VSA,
    )
    assert "kondak-toon-8-hemelum" in hint
    assert "--template kondak-toon-8-hemelum" in hint
    with pytest.raises(TemplateInstanceError) as ei:
        convert_vsa_to_mvsa(
            K8_HEMELUM_VSA, template="kondak-toon-8-groningen", write=False
        )
    assert "kondak-toon-8-hemelum" in (ei.value.hint_nl or "")
    assert "--template" in (ei.value.hint_nl or "")


@pytest.mark.skipif(not K5_VSA.is_file(), reason="corpus kondak-5 ontbreekt")
def test_convert_emit_no_speelplan_blok_has_secties(tmp_path: Path) -> None:
    """T6/emit-vorm: geen @speelplan/@blok; wel secties + VSA-commentaar."""
    out = tmp_path / "k5.mvsa"
    result = convert_vsa_to_mvsa(
        K5_VSA, template="kondak-toon-5-groningen", output=out, write=True
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
    # Gekuiste FM: geen do/mode/tempo; wel template-formule-id (T1/T6).
    fm = text.split("---", 2)[1]
    assert "do:" not in fm
    assert "tempo:" not in fm
    assert "titel:" in fm
    assert "template:" in fm


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
            "template": "tropaar-toon-4-hemelum",
            "output": None,
            "melody": "S",
            "tempo": None,
        },
    )()
    assert run_vsa_mvsa(ns) == 0
    assert src.with_suffix(".mvsa").is_file()
