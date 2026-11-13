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
    default_vsa_mvsa_output,
    emit_mapped_document,
    emit_sections_enabled,
    find_fitting_alternate_templates,
    find_fitting_phrase_separator_fix,
    format_alternate_template_hint,
    format_phrase_separator_hint,
    section_id_for_phrase_index,
    split_notes_by_source_line,
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
        select_template_id(soort="stichier", toon=3)


def test_select_template_id_formule_overrides_soort() -> None:
    """Liturgische soort ≠ melodieformule (T1 formule:)."""
    assert (
        select_template_id(soort="kondak", toon=6, formule="stichier")
        == "stichier-toon-6-groningen"
    )
    assert (
        select_template_id(
            soort="kondak",
            toon=6,
            formule="stichier-toon-6-groningen",
        )
        == "stichier-toon-6-groningen"
    )
    # Zonder formule: kondak/tropaar toon 6 (Groningen).
    assert select_template_id(soort="kondak", toon=6) == "kondak-toon-6-groningen"


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


def test_select_template_id_path_bron_zero_hits_falls_back_to_meta() -> None:
    """T1: leaf ``asten`` (geen …-asten-formule) → ``bron: Hemelum``."""
    path = (
        Path("catalogus")
        / "tropaar"
        / "silouan-de-athoniet-toon-4"
        / "asten"
        / "tropaar-silouan-de-athoniet-toon-4-asten.vsa"
    )
    assert (
        select_template_id(
            soort="tropaar",
            toon=4,
            bron="Koorinstructie Hemelum",
            path=path,
            output=path.with_name(path.name + ".mvsa"),
        )
        == "tropaar-toon-4-hemelum"
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


@pytest.mark.skipif(not T2_VSA.is_file(), reason="corpus toon 2 ontbreekt")
def test_html_comment_not_in_mvsa_l_lines(tmp_path: Path) -> None:
    """HTML-comment in VSA mag niet in L-lyrics belanden (lyrics/zoektekst).

    Mag wél als ``#``-spiegel van de VSA-body (``include_vsa_comment``).
    Regressie: Verzamel-VSA-notities ooit als eerste L-syllaben.
    """
    marker = "Verzamel-VSA-REGRESSIE-frasescheider-XYZ"
    src_text = T2_VSA.read_text(encoding="utf-8")
    # Zelfde plek als typische stichier-notities: vóór de eerste muziekregel.
    injected = src_text.replace(
        "\n\n\n[/:]",
        f"\n\n<!--\n  {marker}\n  Template: stichier-toon-1-groningen.\n-->\n\n[/:]",
        1,
    )
    assert marker in injected
    src = tmp_path / "t2-with-comment.vsa"
    src.write_text(injected, encoding="utf-8")
    result = convert_vsa_to_mvsa(
        src, template="tropaar-toon-2-groningen", write=False
    )
    l_lines = [
        ln for ln in result.text.splitlines() if ln.lstrip().startswith("L:")
    ]
    assert l_lines
    for ln in l_lines:
        assert "Verzamel" not in ln
        assert "REGRESSIE" not in ln
        assert "frasescheider" not in ln
        assert "XYZ" not in ln
        assert "stichier-toon-1" not in ln
    # Spiegel als #-comment mag; lyrics-export leest die niet.
    assert any(marker in ln for ln in result.text.splitlines() if ln.lstrip().startswith("#"))


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


_T1_FM = """\
---
titel: Test tropaar toon 1
soort: tropaar
toon: 1
do: F4
mode: major
---
"""

# Zelfde melodie als hemelum «Heer red Uw volk», maar zonder ** vóór slot.
_T1_MISSING_SEP_BODY = r"""
[:] Heer red Uw {/&/volk_&_} {\\en} ze{/gen} {/Uw} {/erf_}{deel_}, *
{\schenk} de orthodoxe {\chris_}te{\nen_} *
de over{/win_}{/ning_} {\\o}{/ver} {/Uw} {/vij_}an{den_}
{\en} bescherm uw gemeente {/door_} {Uw_} {\kruis_}. [//:]
"""

# Korte vorm: verkeerde pijl op door (\ i.p.v. /) — géén ontbrekende *.
_T1_WRONG_PITCH_BODY = r"""
[:] Heer, red Uw {/&/volk_&_} {\\en} ze{/gen} {/Uw} {/erf_}{deel_}; *
{\en} bescherm Uw Gemeente {\door_} {Uw_} {\Kruis_}. [:]
"""


def test_phrase_separator_fix_for_missing_star_before_final(tmp_path: Path) -> None:
    """T4: ontbrekende ** vóór slotfrase → Hint met werkende regel."""
    src = tmp_path / "heer-red.vsa"
    src.write_text(_T1_FM + _T1_MISSING_SEP_BODY, encoding="utf-8")
    tpl = load_resolved_template("tropaar-toon-1-groningen")
    fix = find_fitting_phrase_separator_fix(
        frontmatter=_T1_FM,
        body=_T1_MISSING_SEP_BODY,
        template=tpl.doc,
        source_name=src.name,
    )
    assert fix is not None
    assert any(m == "**" for m in fix.edits.values())
    hint = format_phrase_separator_hint(fix)
    assert "frasescheiding" in hint
    assert "**" in hint
    with pytest.raises(TemplateInstanceError) as ei:
        convert_vsa_to_mvsa(src, template="tropaar-toon-1-groningen", write=False)
    assert "frasescheiding" in (ei.value.hint_nl or "")
    assert "**" in (ei.value.hint_nl or "")
    # Controle: met de voorgestelde edit mapte het écht.
    from vsa.vsa_stanzas import apply_phrase_separators

    fixed_body = apply_phrase_separators(_T1_MISSING_SEP_BODY, fix.edits)
    fixed = tmp_path / "heer-red-fixed.vsa"
    fixed.write_text(_T1_FM + fixed_body, encoding="utf-8")
    result = convert_vsa_to_mvsa(
        fixed, template="tropaar-toon-1-groningen", write=False
    )
    assert len(result.phrase_ids) == 4


def test_phrase_separator_no_false_hint_on_wrong_pitch_mark(tmp_path: Path) -> None:
    """T4: verkeerde EHM (\\ vs /) → géén valse frasescheidings-Hint."""
    src = tmp_path / "kort.vsa"
    src.write_text(_T1_FM + _T1_WRONG_PITCH_BODY, encoding="utf-8")
    tpl = load_resolved_template("tropaar-toon-1-groningen")
    fix = find_fitting_phrase_separator_fix(
        frontmatter=_T1_FM,
        body=_T1_WRONG_PITCH_BODY,
        template=tpl.doc,
        source_name=src.name,
    )
    assert fix is None
    with pytest.raises(TemplateInstanceError) as ei:
        convert_vsa_to_mvsa(src, template="tropaar-toon-1-groningen", write=False)
    assert "frasescheiding" not in (ei.value.hint_nl or "")


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


def test_default_vsa_mvsa_output_uses_stem_brontype_doeltype() -> None:
    assert default_vsa_mvsa_output(Path("lied.vsa")) == Path("lied.vsa.mvsa")
    nested = Path("catalogus") / "x" / "default" / "lied.vsa"
    assert default_vsa_mvsa_output(nested) == nested.with_name("lied.vsa.mvsa")


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
    assert src.with_name(f"{src.name}.mvsa").is_file()


def test_split_notes_by_source_line_print_wrap() -> None:
    """T6: ingesprongen VSA-vervolgregel → aparte maat-chunk."""
    from vsa.music import Duration, Pitch
    from vsa.template_instance import MappedNote

    q = Duration(note_type="quarter")
    f4 = Pitch(step="F", octave=4, alter=0.0)

    def mn(lyric: str, line: int) -> MappedNote:
        return MappedNote(
            lyric=lyric,
            duration=q,
            s_pitch=f4,
            template_event={"role": "recite", "pitches": {"S": "fa"}},
            source_line=line,
        )

    notes = [mn("Die", 30), mn("macht", 30), mn("de", 31), mn("rust", 31)]
    chunks = split_notes_by_source_line(notes)
    assert len(chunks) == 2
    assert [n.lyric for n in chunks[0]] == ["Die", "macht"]
    assert [n.lyric for n in chunks[1]] == ["de", "rust"]
    # Zonder bronregels: één chunk (handmatige MappedNote / oude tests).
    assert len(split_notes_by_source_line([mn("x", 0), mn("y", 0)])) == 1


def test_emit_mapped_document_print_wrap_two_measures() -> None:
    """T6: één frase over twee bronregels → twee LSATB-systemen, zelfde sectie."""
    from vsa.music import Duration, Pitch
    from vsa.template_instance import MappedNote

    q = Duration(note_type="quarter")
    f4 = Pitch(step="F", octave=4, alter=0.0)

    def mn(lyric: str, line: int) -> MappedNote:
        return MappedNote(
            lyric=lyric,
            duration=q,
            s_pitch=f4,
            template_event={"role": "open", "pitches": {"S": "fa", "A": "re", "T": "do", "B": "do"}},
            source_line=line,
        )

    mapped = [
        ("1", [mn("kort", 10)]),
        ("laatste", [mn("lang", 20), mn("deel", 20), mn("wrap", 21), mn("eind", 21)]),
    ]
    text, _ = emit_mapped_document(
        mapped,
        do="F4",
        mode="major",
        title="wrap-test",
        source_path="wrap.vsa",
        template_path="t.yaml",
        cycle_len=1,
        with_sections=True,
    )
    l_lines = [ln for ln in text.splitlines() if ln.startswith("L:")]
    assert len(l_lines) == 3  # frase 1 + twee wrap-maten
    assert "@sectie laatste" in text
    # Wrap-maten staan ná @sectie laatste; geen extra sectiekop ertussen.
    last_sec = text.index("@sectie laatste")
    assert text.count("@sectie laatste") == 1
    assert text[last_sec:].count("\nL:") == 2


BIB_WRAP_VSA = (
    Path(__file__).resolve().parents[2]
    / "bibliotheek"
    / "content-source"
    / "catalogus"
    / "tropaar"
    / "zaterdag-gestorvenen-toon-2"
    / "hemelum"
    / "tropaar-zaterdag-gestorvenen-toon-2-hemelum.vsa"
)


@pytest.mark.skipif(not BIB_WRAP_VSA.is_file(), reason="bibliotheek-voorbeeld ontbreekt")
def test_convert_print_wrap_last_phrase_two_measures(tmp_path: Path) -> None:
    """Corpus: laatste frase met indent-wrap → twee maten onder @sectie laatste."""
    out = tmp_path / "wrap.mvsa"
    result = convert_vsa_to_mvsa(
        BIB_WRAP_VSA,
        template="tropaar-toon-2-groningen",
        output=out,
        write=True,
    )
    assert result.phrase_ids[-1] == "laatste"
    after = result.text.split("@sectie laatste", 1)[1]
    assert after.count("\nL:") == 2
    assert "gaan" in after
    assert "rust" in after or "le_" in after
