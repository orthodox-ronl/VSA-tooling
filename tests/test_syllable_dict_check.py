"""Dictionary-check op VSA-body."""

from pathlib import Path

from vsa.parser import Parser
from vsa.syllabify import hyphenate_dutch_word
from vsa.syllable_dict_check import (
    CODE_LANG_SKIPPED,
    CODE_MISMATCH,
    CODE_TAAL_MISMATCH,
    CODE_UNKNOWN,
    append_canonical_form,
    apply_replacements_to_text,
    find_dictionary_syllable_issues,
    find_dictionary_syllable_issues_from_cores,
    prompt_dictionary_fixes,
    replace_sung_token_in_text,
    set_canonical_form,
)
from vsa.syllable_dictionary import (
    apply_syllable_dictionary_from_config,
    clear_syllable_dictionary_cache,
    load_syllable_dictionary,
    set_lyrics_lang,
    set_syllable_dictionary_path,
    syllable_lemma,
)
from vsa.validation_runner import validate_file


class _Tty:
    def __init__(self, data: str) -> None:
        self._data = data
        self._pos = 0

    def isatty(self) -> bool:
        return True

    def readline(self) -> str:
        if self._pos >= len(self._data):
            return ""
        end = self._data.find("\n", self._pos)
        if end < 0:
            chunk = self._data[self._pos :]
            self._pos = len(self._data)
            return chunk
        chunk = self._data[self._pos : end + 1]
        self._pos = end + 1
        return chunk


def test_hyphenate_prefers_dictionary() -> None:
    assert hyphenate_dutch_word("eeuwig") == "eeu-wig"
    assert hyphenate_dutch_word("eeuwi-ge") == "eeu-wi-ge"
    assert hyphenate_dutch_word("apostel") == "a-pos-tel"


def test_mismatch_when_surface_differs_from_dictionary() -> None:
    doc = Parser("eeuwi-ge Licht").parse()
    findings = find_dictionary_syllable_issues(doc, source_text="eeuwi-ge Licht")
    assert any(f.code == CODE_MISMATCH and f.expected == "eeu-wi-ge" for f in findings)


def test_unknown_multisyllable_is_reported() -> None:
    doc = Parser("xyzzyxabcde").parse()
    # force a fake multi-syllable look: use hyphens already
    doc = Parser("xyz-zy-xab").parse()
    findings = find_dictionary_syllable_issues(doc, source_text="xyz-zy-xab")
    assert any(f.code == CODE_UNKNOWN for f in findings)


def test_ksl_lang_skips_latin_and_flags_cyrillic(tmp_path: Path) -> None:
    ksl = tmp_path / "syllable_dictionary.ksl.txt"
    ksl.write_text("# leeg\n", encoding="utf-8")
    apply_syllable_dictionary_from_config(cli_path=ksl, lang="ksl")
    clear_syllable_dictionary_cache()
    try:
        findings = find_dictionary_syllable_issues_from_cores(
            ["Heer", "Гос-по-ди"],
            lyrics_lang="ksl",
        )
        assert any(f.code == CODE_LANG_SKIPPED for f in findings)
        assert not any(f.surface == "Heer" for f in findings)
        assert any(
            f.code == CODE_UNKNOWN and f.surface == "Гос-по-ди" for f in findings
        )
        # Geen NL-Pyphen-voorstel: suggestie = surface.
        hit = next(f for f in findings if f.surface == "Гос-по-ди")
        assert "Гос-по-ди" in hit.message_nl
    finally:
        set_lyrics_lang("nl")
        set_syllable_dictionary_path(None)
        clear_syllable_dictionary_cache()


def test_nl_lang_skips_cyrillic() -> None:
    findings = find_dictionary_syllable_issues_from_cores(
        ["Господи", "xyz-zy-xab"],
        lyrics_lang="nl",
    )
    assert not any("Господи" in f.surface for f in findings)
    assert any(f.code == CODE_UNKNOWN and f.surface == "xyz-zy-xab" for f in findings)


def test_auto_lang_checks_cyrillic_and_latin(tmp_path: Path, monkeypatch) -> None:
    """auto: Latijn én Cyrillisch in één bron → beide dictionaries."""
    data = tmp_path / "data"
    data.mkdir()
    (data / "syllable_dictionary.nl.txt").write_text(
        "heer\n", encoding="utf-8"
    )
    (data / "syllable_dictionary.ksl.txt").write_text("# leeg\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    apply_syllable_dictionary_from_config(lang="auto")
    clear_syllable_dictionary_cache()
    try:
        findings = find_dictionary_syllable_issues_from_cores(
            ["xyz-zy-xab", "Гос-по-ди"],
            lyrics_lang="auto",
        )
        assert any(
            f.code == CODE_UNKNOWN and f.surface == "xyz-zy-xab" for f in findings
        )
        assert any("(nl" in f.message_nl for f in findings if f.surface == "xyz-zy-xab")
        assert any(
            f.code == CODE_UNKNOWN and f.surface == "Гос-по-ди" for f in findings
        )
        assert any("(ksl" in f.message_nl for f in findings if f.surface == "Гос-по-ди")
        assert not any(f.code == CODE_LANG_SKIPPED for f in findings)
    finally:
        set_lyrics_lang("nl")
        set_syllable_dictionary_path(None)
        clear_syllable_dictionary_cache()


def test_force_nl_emits_lang_skipped_for_cyrillic() -> None:
    findings = find_dictionary_syllable_issues_from_cores(
        ["Господи", "xyz-zy-xab"],
        lyrics_lang="nl",
    )
    assert any(f.code == CODE_LANG_SKIPPED for f in findings)
    assert "ksl" in next(f for f in findings if f.code == CODE_LANG_SKIPPED).message_nl
    assert not any("Господи" in f.surface for f in findings)
    assert any(f.code == CODE_UNKNOWN and f.surface == "xyz-zy-xab" for f in findings)


def test_frontmatter_taal_mismatch_warning() -> None:
    source = "---\ntaal: nl\n---\nГос-по-ди Heer\n"
    findings = find_dictionary_syllable_issues_from_cores(
        ["Гос-по-ди", "Heer"],
        source_text=source,
        lyrics_lang="auto",
    )
    assert any(f.code == CODE_TAAL_MISMATCH for f in findings)
    hit = next(f for f in findings if f.code == CODE_TAAL_MISMATCH)
    assert "ksl" in hit.message_nl


def test_validate_file_dictionary_mismatch_is_error(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "bad.vsa"
    path.write_text("eeuwi-ge\n", encoding="utf-8")
    import vsa.validation_runner as runner

    monkeypatch.setattr(
        runner, "_auto_repair_vsa_soft_hyphens", lambda path, text, result: text
    )
    result = validate_file(path)
    hits = [m for m in result.messages if m.code == CODE_MISMATCH]
    assert hits
    assert hits[0].severity == "error"
    assert not result.ok
    assert "eeuwi-ge" in path.read_text(encoding="utf-8")


def test_validate_auto_repairs_scope_letter_redistribution(tmp_path: Path) -> None:
    """Scopes met verkeerde lettergrenzen → herverdeel tot dictionary-vorm."""
    path = tmp_path / "scopes.vsa"
    path.write_text("{eeuwi}{ge}\n", encoding="utf-8")
    result = validate_file(path)
    text = path.read_text(encoding="utf-8")
    assert "{eeu}wi{ge}" in text
    assert not any(
        m.code == CODE_MISMATCH and m.severity == "error" for m in result.messages
    )
    assert any(m.code == "VSA-SYLLABIFY-APPLIED" for m in result.messages)


def test_append_and_prompt_unknown_accept(tmp_path: Path, monkeypatch) -> None:
    clear_syllable_dictionary_cache()
    data = tmp_path / "syllable_dictionary.nl.txt"
    data.write_text("# test\n", encoding="utf-8")
    import vsa.syllable_dictionary as dict_mod
    import vsa.syllable_dict_check as check_mod

    monkeypatch.setattr(dict_mod, "dictionary_file_path", lambda: data)
    monkeypatch.setattr(check_mod, "dictionary_file_path", lambda: data)
    clear_syllable_dictionary_cache()

    written = append_canonical_form("nieuw-woord-xyz")
    assert written == "nieuw-woord-xyz"
    assert syllable_lemma("nieuwwoordxyz") in dict_mod.load_syllable_dictionary()

    finding = next(
        f
        for f in find_dictionary_syllable_issues(
            Parser("ander-woord-xyz").parse(), source_text="ander-woord-xyz"
        )
        if f.code == CODE_UNKNOWN
    )
    from io import StringIO

    session = prompt_dictionary_fixes(
        [finding], stdin=_Tty("\n"), stdout=StringIO()
    )
    assert "ander-woord-xyz" in session.added_or_updated
    clear_syllable_dictionary_cache()


def test_replace_scope_bridged_eeuwen() -> None:
    """Spatie/Enter op MISMATCH herschrijft scope-brug eeuw|en naar eeu|wen."""
    from vsa.syllable_dict_check import apply_replacements_to_source, _locate

    source = (
        "---\n"
        "zoektekst: eeuwen\n"
        "---\n"
        "\n"
        "in de eeu-wen der {\\eeuw}{\\en}.\n"
    )
    line, col = _locate(source, "eeuw-en")
    row = source.splitlines()[line - 1]
    assert col > row.index("der")
    assert "eeuw" in row[col - 1 :]
    out = apply_replacements_to_source(source, [("eeuw-en", "eeu-wen")])
    assert "{\\eeu}{\\wen}" in out
    assert "{\\eeuw}{\\en}" not in out


def test_replace_mvsa_recite_bridged_gezegend() -> None:
    """Enter op MISMATCH: ``(… gez)-e_-gend_`` → ``(… ge)-ze_-gend_``."""
    from vsa.syllable_dict_check import (
        apply_replacements_to_source,
        find_mvsa_dictionary_syllable_issues,
    )

    src = """\
@title "t"
@do F4
@mode major
@oct S=0

L: (De Naam des He-ren zij gez)-e_-gend_ [//.] |
S: a4                          -   -          |
"""
    out = apply_replacements_to_source(src, [("gez-e-gend", "ge-ze-gend")])
    assert "gez)-e_" not in out
    assert "ge)-ze_" in out or "(De Naam des He-ren zij ge)-ze_" in out
    assert "[//.]" in out
    again = find_mvsa_dictionary_syllable_issues(out)
    assert not any(
        f.surface.replace("=", "-").casefold().startswith("gez-e")
        for f in again
    )


def test_replace_mvsa_elm_bridged_eeuwigheid() -> None:
    """``eeuw_-ig-heid_`` → ``eeu_-wig-heid_`` over ELM-posities."""
    from vsa.syllable_dict_check import apply_replacements_to_source

    src = """\
@title "t"
@do F4
@mode major
@oct S=0

L: in eeuw_-ig-heid_ [//.] |
S: -  g4 a4  -   -          |
"""
    out = apply_replacements_to_source(
        src, [("eeuw-ig-heid", "eeu-wig-heid")]
    )
    assert "eeuw_" not in out or "eeu_" in out
    assert "eeu_" in out
    assert "-wig" in out or "wig" in out
    assert "[//.]" in out


def test_replace_mvsa_recite_bridged_eeuwen() -> None:
    """``eeuw)-en`` → ``eeu)-wen`` over recite-einde."""
    from vsa.syllable_dict_check import apply_replacements_to_source

    src = """\
@title "t"
@do F4
@mode major
@oct S=0

L: (Nu en al-tijd en in de eeu-wen de eeuw)-en, a_-men_ |
S:  a4                                      \\   /   -   |
"""
    out = apply_replacements_to_source(src, [("eeuw-en", "eeu-wen")])
    assert "eeuw)-en" not in out
    assert "eeu)-wen" in out or "eeu)-wen," in out


def test_replace_scope_bridged_inserts_hard_hyphen() -> None:
    """Enter op MISMATCH zet hard ``=`` tussen scopes (mede=eeuwige)."""
    from vsa.parser import Parser
    from vsa.syllable_dict_check import (
        CODE_MISMATCH,
        apply_replacements_to_source,
        find_dictionary_syllable_issues,
    )

    src = r"het me{\de}{/eeu_}wi{\ge} woord"
    # Oppervlakte via scopegrenzen = alleen soft ``-``.
    findings = find_dictionary_syllable_issues(
        Parser(src).parse(), source_text=src
    )
    hit = next(f for f in findings if f.code == CODE_MISMATCH)
    assert hit.surface == "me-de-eeu-wi-ge"
    assert hit.expected == "me-de=eeu-wi-ge"
    out = apply_replacements_to_source(src, [(hit.surface, hit.expected)])
    assert r"me{\de}={/eeu_}wi{\ge}" in out
    again = find_dictionary_syllable_issues(
        Parser(out).parse(), source_text=out
    )
    assert not any(
        f.code == CODE_MISMATCH and f.surface.startswith("me-de") for f in again
    )


def test_replace_scope_plus_text_eeuwigheid() -> None:
    """``{/eeuw}igheid`` → ``{/eeu}wig-heid`` bij dictionary-correctie."""
    from vsa.syllable_dict_check import replace_sung_token_in_text

    src = r"God is {/van} {/eeuw}igheid {\on}"
    out = replace_sung_token_in_text(src, "eeuw-igheid", "eeu-wig-heid")
    assert r"{/eeu}wig-heid" in out
    assert r"{/eeuw}igheid" not in out


def test_replace_sung_token_preserves_case() -> None:
    text = "Uw Eeuwig Licht eeuwig."
    out = replace_sung_token_in_text(text, "eeuwig", "eeu-wig")
    assert "Eeu-wig" in out
    assert "eeu-wig" in out


def test_replacements_skip_zoektekst_frontmatter() -> None:
    from vsa.syllable_dict_check import apply_replacements_to_source

    source = (
        "---\n"
        "zoektekst: |-\n"
        "  Gij werd verheerlijkt op de berg\n"
        "---\n"
        "\n"
        "Gij werd verheerlijkt op de berg\n"
    )
    out = apply_replacements_to_source(
        source, [("verheerlijkt", "ver-heer-lijkt")]
    )
    fm, body = out.split("---\n", 2)[1], out.split("---\n", 2)[2]
    assert "verheerlijkt" in fm
    assert "ver-heer-lijkt" not in fm
    assert "ver-heer-lijkt" in body


def test_locate_ignores_zoektekst_frontmatter() -> None:
    """Positie-melding mag nooit op YAML-zoektekst wijzen."""
    from vsa.syllable_dict_check import _locate

    source = (
        "---\n"
        "zoektekst: |-\n"
        "  de rechtvaardige zal blijven\n"
        "---\n"
        "\n"
        "<!-- commentaar met rechtvaardige erin -->\n"
        "{\\recht}{\\vaar_}di-ge\n"
    )
    line, _col = _locate(source, "recht-vaar-di-ge")
    # Frontmatter = regels 1–5; zoektekst-regel ~3 mag nooit winnen.
    assert line > 5
    assert line != 3
    rows = source.splitlines()
    assert not rows[line - 1].lstrip().startswith("<!--")


def test_locate_never_points_at_html_comment() -> None:
    """Synthetic kern (scope-brug) mag niet op ``<!--`` landen."""
    from vsa.syllable_dict_check import _locate

    source = (
        "---\n"
        "zoektekst: x\n"
        "---\n"
        "\n"
        "<!--\n"
        "  commentaar stro-fes hier\n"
        "-->\n"
        "\n"
        "tot_ {\\U_}{\\roep_}\n"
    )
    line, column = _locate(source, "U-roep")
    rows = source.splitlines()
    assert 1 <= line <= len(rows)
    assert not rows[line - 1].lstrip().startswith("<!--")
    assert "U" in rows[line - 1] or "roep" in rows[line - 1]
    assert column >= 1


def test_locate_mvsa_hyphen_chain_with_space_not_on_title() -> None:
    """MVSA ``Aan_ -U_`` (spatie tussen posities) → L-regel, niet ``@title``."""
    from vsa.syllable_dict_check import _locate

    source = (
        '@oct "G"\n'
        '@title "Vragende Litanie (16)"\n'
        "\n"
        "S:  a4_   a_   |\n"
        "L:  Aan_ -U_.&-&_   o_, Heer__  |\n"
    )
    line, column = _locate(source, "Aan-U")
    rows = source.splitlines()
    assert rows[line - 1].lstrip().startswith("L:")
    assert "Aan" in rows[line - 1]
    assert not rows[line - 1].lstrip().startswith("@")
    assert column >= 1


def test_prompt_prints_source_id_once(tmp_path: Path, monkeypatch) -> None:
    from io import StringIO

    clear_syllable_dictionary_cache()
    data = tmp_path / "syllable_dictionary.nl.txt"
    data.write_text("eeu-wig\n", encoding="utf-8")
    import vsa.syllable_dictionary as dict_mod
    import vsa.syllable_dict_check as check_mod

    monkeypatch.setattr(dict_mod, "dictionary_file_path", lambda: data)
    monkeypatch.setattr(check_mod, "dictionary_file_path", lambda: data)
    clear_syllable_dictionary_cache()

    finding = next(
        f
        for f in find_dictionary_syllable_issues(
            Parser("eeuwig\n").parse(), source_text="eeuwig\n"
        )
        if f.code == CODE_MISMATCH
    )
    out = StringIO()
    prompt_dictionary_fixes(
        [finding, finding],
        stdin=_Tty("s\ns\n"),
        stdout=out,
        source_id="tropaar/transfiguratie-toon-7/hemelum",
    )
    text = out.getvalue()
    assert text.count("--- tropaar/transfiguratie-toon-7/hemelum ---") == 1
    # Zonder source_path: catalogus-id in de locatieregel (niet kale :regel:kolom:).
    assert "tropaar/transfiguratie-toon-7/hemelum:" in text
    assert not text.lstrip().startswith(":")


def test_format_clickable_location_fallback_never_bare() -> None:
    from vsa.syllable_dict_check import format_clickable_location

    bare = format_clickable_location(None, 56, 8)
    assert bare == "?:56:8:"
    with_id = format_clickable_location(
        None, 56, 8, fallback="soort/variant/uv"
    )
    assert with_id == "soort/variant/uv:56:8:"


def test_prompt_mismatch_enter_queues_source_replace(
    tmp_path: Path, monkeypatch
) -> None:
    from io import StringIO

    clear_syllable_dictionary_cache()
    data = tmp_path / "syllable_dictionary.nl.txt"
    data.write_text("eeu-wig\n", encoding="utf-8")
    import vsa.syllable_dictionary as dict_mod
    import vsa.syllable_dict_check as check_mod

    monkeypatch.setattr(dict_mod, "dictionary_file_path", lambda: data)
    monkeypatch.setattr(check_mod, "dictionary_file_path", lambda: data)
    clear_syllable_dictionary_cache()

    finding = next(
        f
        for f in find_dictionary_syllable_issues(
            Parser("Uw eeuwig Licht").parse(), source_text="Uw eeuwig Licht"
        )
        if f.code == CODE_MISMATCH
    )
    session = prompt_dictionary_fixes(
        [finding], stdin=_Tty("\n"), stdout=StringIO()
    )
    assert session.replacements == [("eeuwig", "eeu-wig")]
    assert apply_replacements_to_text("Uw eeuwig Licht", session.replacements) == (
        "Uw eeu-wig Licht"
    )


def test_prompt_unknown_hyphenated_accepts_surface(
    tmp_path: Path, monkeypatch
) -> None:
    from io import StringIO

    clear_syllable_dictionary_cache()
    data = tmp_path / "syllable_dictionary.nl.txt"
    data.write_text("# test\n", encoding="utf-8")
    import vsa.syllable_dictionary as dict_mod
    import vsa.syllable_dict_check as check_mod

    monkeypatch.setattr(dict_mod, "dictionary_file_path", lambda: data)
    monkeypatch.setattr(check_mod, "dictionary_file_path", lambda: data)
    clear_syllable_dictionary_cache()

    surface = "eeu-wig-heids-waar-de"
    finding = next(
        f
        for f in find_dictionary_syllable_issues(
            Parser(surface).parse(), source_text=surface
        )
        if f.code == CODE_UNKNOWN
    )
    session = prompt_dictionary_fixes(
        [finding], stdin=_Tty("\n"), stdout=StringIO()
    )
    assert session.added_or_updated == [surface]
    assert load_syllable_dictionary()[syllable_lemma(surface)] == surface


def test_prompt_accepts_space_as_default(tmp_path: Path, monkeypatch) -> None:
    from io import StringIO

    from vsa.syllable_dict_check import format_clickable_location

    clear_syllable_dictionary_cache()
    data = tmp_path / "syllable_dictionary.nl.txt"
    data.write_text("eeu-wig\n", encoding="utf-8")
    import vsa.syllable_dictionary as dict_mod
    import vsa.syllable_dict_check as check_mod

    monkeypatch.setattr(dict_mod, "dictionary_file_path", lambda: data)
    monkeypatch.setattr(check_mod, "dictionary_file_path", lambda: data)
    clear_syllable_dictionary_cache()

    finding = next(
        f
        for f in find_dictionary_syllable_issues(
            Parser("Uw eeuwig Licht").parse(), source_text="Uw eeuwig Licht"
        )
        if f.code == CODE_MISMATCH
    )
    finding = finding.__class__(
        code=finding.code,
        surface=finding.surface,
        expected=finding.expected,
        line=3,
        column=7,
        message_nl=finding.message_nl,
        hint_nl=finding.hint_nl,
    )
    out = StringIO()
    src = tmp_path / "content-source" / "lied.vsa"
    src.parent.mkdir(parents=True)
    src.write_text("x\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    session = prompt_dictionary_fixes(
        [finding],
        stdin=_Tty(" \n"),
        stdout=out,
        source_path=src,
    )
    assert not session.aborted
    assert session.replacements == [("eeuwig", "eeu-wig")]
    loc = format_clickable_location(src, 3, 7, cwd=tmp_path)
    assert loc in out.getvalue()
    assert loc.startswith("content-source")
    assert loc.endswith(":3:7:")
    text = out.getvalue()
    assert text.index(loc) < text.index(finding.message_nl)


def test_prompt_plus_accepts_current_form(tmp_path: Path, monkeypatch) -> None:
    from io import StringIO

    clear_syllable_dictionary_cache()
    data = tmp_path / "syllable_dictionary.nl.txt"
    data.write_text("eeu-wig\n", encoding="utf-8")
    import vsa.syllable_dictionary as dict_mod
    import vsa.syllable_dict_check as check_mod

    monkeypatch.setattr(dict_mod, "dictionary_file_path", lambda: data)
    monkeypatch.setattr(check_mod, "dictionary_file_path", lambda: data)
    clear_syllable_dictionary_cache()

    data.write_text("eeu-wi-ge\n", encoding="utf-8")
    clear_syllable_dictionary_cache()
    finding = next(
        f
        for f in find_dictionary_syllable_issues(
            Parser("eeuwi-ge").parse(), source_text="eeuwi-ge"
        )
        if f.code == CODE_MISMATCH
    )
    session = prompt_dictionary_fixes(
        [finding], stdin=_Tty("+\n"), stdout=StringIO()
    )
    assert "eeuwi-ge" in session.added_or_updated
    text = data.read_text(encoding="utf-8")
    assert "eeu-wi-ge" in text
    assert "+eeuwi-ge" in text


def test_prompt_tab_skips_and_esc_aborts(tmp_path: Path, monkeypatch) -> None:
    from io import StringIO

    clear_syllable_dictionary_cache()
    data = tmp_path / "syllable_dictionary.nl.txt"
    data.write_text("eeu-wig\n", encoding="utf-8")
    import vsa.syllable_dictionary as dict_mod
    import vsa.syllable_dict_check as check_mod

    monkeypatch.setattr(dict_mod, "dictionary_file_path", lambda: data)
    monkeypatch.setattr(check_mod, "dictionary_file_path", lambda: data)
    clear_syllable_dictionary_cache()

    findings = [
        f
        for f in find_dictionary_syllable_issues(
            Parser("eeuwig xyz-zy-xab").parse(),
            source_text="eeuwig xyz-zy-xab",
        )
        if f.code in {CODE_MISMATCH, CODE_UNKNOWN}
    ]
    assert len(findings) >= 2
    out = StringIO()
    session = prompt_dictionary_fixes(
        findings, stdin=_Tty("\t\nq\n"), stdout=out
    )
    # Eerste Tab = overslaan; tweede Esc/q = abort → geen replacements.
    assert session.aborted
    assert session.replacements == []
    assert "afgebroken" in out.getvalue().casefold()
    assert "[Esc]" in out.getvalue()


def test_locate_accounts_for_yaml_frontmatter() -> None:
    from vsa.syllable_dict_check import _locate

    source = (
        "---\n"
        "zoektekst: |-\n"
        "  eeuwig Licht\n"
        "---\n"
        "\n"
        "Uw eeuwig Licht\n"
    )
    line, column = _locate(source, "eeuwig")
    # Frontmatter is 4 regels (--- / zoektekst /   eeuwig / ---), dan lege
    # regel, dan bodyregel 6: "Uw eeuwig Licht".
    assert line == 6
    assert column == 4


def test_locate_remaps_hash_comment_line_shift() -> None:
    """``#``-regels mogen regelnummers niet laten wijzen naar ``@oct`` e.d."""
    from vsa.syllable_dict_check import _locate

    # Spiegel van alleluia-toon-4-znameni-vokn.mvsa: twee #-regels vóór L:
    # verschuiven de L-regel in gestripte tekst, niet in de bron.
    source = (
        "---\n"
        "zoektekst: >-\n"
        "  Alleluja\n"
        "---\n"
        "\n"
        "# titelcommentaar\n"
        "\n"
        "@title \"Alleluia\"\n"
        "\n"
        "# drie mollen\n"
        "@do Eb4\n"
        "\n"
        "@oct S=0 A=0 T=-1 B=-1\n"
        "\n"
        "L:  Al-le-(lu-ja, Al-le-lu-ja)\n"
        "S:  G   /  /\n"
    )
    lines = source.splitlines()
    # Bronregel met lu-ja (1-based): L-regel.
    expected_line = next(
        i for i, row in enumerate(lines, start=1) if row.startswith("L:")
    )
    oct_line = next(
        i for i, row in enumerate(lines, start=1) if row.startswith("@oct")
    )
    line, column = _locate(source, "lu-ja")
    assert line == expected_line
    assert line != oct_line
    # Kolom op de L-regel: start van «lu-ja» na «Al-le-(».
    assert lines[line - 1][column - 1 : column - 1 + len("lu-ja")] == "lu-ja"


def test_at_directives_excluded_from_dictionary_cores() -> None:
    """``@``-regels tellen niet als lyrics voor validate dictionary-check."""
    from vsa.syllable_dict_check import (
        CODE_UNKNOWN,
        find_dictionary_syllable_issues,
        iter_vsa_lyric_word_cores,
    )

    body = (
        '@title "Proef"\n'
        "@mode major\n"
        "@oct S=0 A=0 T=-1 B=-1\n"
        "on-be-kend-woord-xyz\n"
    )
    document = Parser(body).parse()
    lemmas = {syllable_lemma(c) for c in iter_vsa_lyric_word_cores(document)}
    assert lemmas.isdisjoint({"title", "mode", "major", "s0", "t1"})
    findings = find_dictionary_syllable_issues(document, source_text=body)
    assert not any(
        syllable_lemma(f.surface) in {"title", "mode", "major", "s0", "t1"}
        for f in findings
    )
    unknown = [f for f in findings if f.code == CODE_UNKNOWN]
    assert len(unknown) == 1
    assert unknown[0].line == 4
    assert "on-be-kend-woord-xyz" in unknown[0].surface


def test_kondak_copy_no_at_directive_dict_noise(tmp_path: Path) -> None:
    import shutil

    src = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "formule-tekst"
        / "vsa-bestanden"
        / "kondak-h-apostel-thaddeos-toon-4.vsa"
    )
    if not src.is_file():
        return
    dst = tmp_path / src.name
    shutil.copyfile(src, dst)
    result = validate_file(dst)
    noise = ("title", "mode", "major", "S=0", "T=-1")
    hits = [
        m
        for m in result.messages
        if "SYLLABLE-DICT" in m.code and any(n in m.message_nl for n in noise)
    ]
    assert not hits, [m.message_nl for m in hits]


def test_vsa_scope_boundaries_count_as_syllable_breaks() -> None:
    """Scopegrenzen = zing-deling; geen MISMATCH op ver{/heer}{\\lijkt}."""
    from vsa.syllable_dict_check import (
        bare_sung_text,
        find_dictionary_syllable_issues,
        iter_vsa_lyric_word_cores,
    )

    body = (
        "Gij werd ver{/&\\heer}{\\lijkt} op de berg, o Chris{/tus} {/God_}, *\n"
        "en aan Uw Leer-lin-gen toon-de Gij Uw {\\heer_}lijk{heid_}. *\n"
        "Doe ook voor {/&\\ons}, {\\zon}daars, Uw eeu-wig {/Licht} {/stra_}{len_}: **\n"
        "Gij die ons het {\\Licht_} {\\&\\schenkt~&~}, {/e_}re zij {\\U__}."
    )
    document = Parser(body).parse()
    cores = iter_vsa_lyric_word_cores(document)
    by_lemma = {syllable_lemma(c): c for c in cores}
    assert by_lemma["verheerlijkt"] == "ver-heer-lijkt"
    assert by_lemma["christus"] == "Chris-tus"
    assert by_lemma["heerlijkheid"] == "heer-lijk-heid"
    assert by_lemma["zondaars"] == "zon-daars"
    assert by_lemma["stralen"] == "stra-len"
    assert by_lemma["ere"] == "e-re"
    # Geen dubbele streepjes aan scopegrenzen in de kale tekst.
    bare = bare_sung_text(document)
    assert "--" not in bare
    findings = find_dictionary_syllable_issues(document, source_text=body)
    bad = [
        f
        for f in findings
        if f.code == CODE_MISMATCH
        and syllable_lemma(f.surface)
        in {
            "verheerlijkt",
            "christus",
            "heerlijkheid",
            "zondaars",
            "stralen",
            "ere",
        }
    ]
    assert bad == []


def test_mvsa_lyrics_ignore_title_directive() -> None:
    from vsa.syllable_dict_check import (
        find_mvsa_dictionary_syllable_issues,
        iter_mvsa_lyric_word_cores,
    )

    source = """\
@title "tropaar-voorbeeld-title-woord"
@do F4
@mode major
@sectie a
L: (Gij werd ver-heer-lijkt) |
S: g                        |
"""
    cores = iter_mvsa_lyric_word_cores(source)
    lemmas = {syllable_lemma(c) for c in cores}
    assert "title" not in lemmas
    assert "tropaarvoorbeeldtitlewoord" not in lemmas
    assert "gij" in lemmas
    assert "verheerlijkt" in lemmas
    findings = find_mvsa_dictionary_syllable_issues(source)
    assert not any(
        syllable_lemma(f.surface) in {"title", "tropaarvoorbeeldtitlewoord"}
        for f in findings
    )


def test_mvsa_recite_paren_keeps_word_for_dictionary(
    tmp_path: Path, monkeypatch
) -> None:
    """``Al-le-(lu-ja`` = ``Al-le-lu-ja`` voor de woordenlijst (haakje weg)."""
    from vsa.syllable_dict_check import (
        CODE_UNKNOWN,
        find_mvsa_dictionary_syllable_issues,
        iter_mvsa_lyric_word_cores,
    )

    data = tmp_path / "syllable_dictionary.nl.txt"
    data.write_text("al-le-lu-ja\n", encoding="utf-8")
    import vsa.syllable_dictionary as dict_mod
    import vsa.syllable_dict_check as check_mod

    monkeypatch.setattr(dict_mod, "dictionary_file_path", lambda: data)
    monkeypatch.setattr(check_mod, "dictionary_file_path", lambda: data)
    clear_syllable_dictionary_cache()

    # Zelfde patroon als alleluia-toon-4-znameni-vokn.mvsa: ``-`` vóór ``(``
    # is parser-ELM, orthografisch soft ``-`` het woord in.
    source = """\
@do Eb4
@mode major
L:  Al-le-(lu-ja, Al-le-lu-ja) |
S:  G   /  /                   |
"""
    cores = iter_mvsa_lyric_word_cores(source)
    assert cores == ["Al-le-lu-ja", "Al-le-lu-ja"]
    findings = find_mvsa_dictionary_syllable_issues(source)
    assert not any(
        f.code == CODE_UNKNOWN and syllable_lemma(f.surface) == "luja"
        for f in findings
    )
    assert not any(syllable_lemma(f.surface) == "alle" for f in findings)


def test_set_canonical_form_adds_plus_alt(tmp_path: Path, monkeypatch) -> None:
    data = tmp_path / "syllable_dictionary.nl.txt"
    data.write_text("ou-de-vorm\n", encoding="utf-8")
    import vsa.syllable_dictionary as dict_mod
    import vsa.syllable_dict_check as check_mod

    monkeypatch.setattr(dict_mod, "dictionary_file_path", lambda: data)
    monkeypatch.setattr(check_mod, "dictionary_file_path", lambda: data)
    clear_syllable_dictionary_cache()
    written = set_canonical_form("ou-de=vorm", allow_replace=True)
    assert written == "ou-de=vorm"
    text = data.read_text(encoding="utf-8")
    # Primaire blijft; nieuwe vorm wordt ``+``-alternatief.
    assert "ou-de-vorm\n" in text
    assert "+ou-de=vorm" in text
    clear_syllable_dictionary_cache()


def test_set_canonical_form_keeps_alphabetical_order(
    tmp_path: Path, monkeypatch
) -> None:
    data = tmp_path / "syllable_dictionary.nl.txt"
    data.write_text("# kop\nzee-man\naan-tal\n", encoding="utf-8")
    import vsa.syllable_dictionary as dict_mod
    import vsa.syllable_dict_check as check_mod

    monkeypatch.setattr(dict_mod, "dictionary_file_path", lambda: data)
    monkeypatch.setattr(check_mod, "dictionary_file_path", lambda: data)
    clear_syllable_dictionary_cache()
    append_canonical_form("mid-den")
    text = data.read_text(encoding="utf-8")
    assert text.startswith("# kop\n")
    entries = [
        ln.strip()
        for ln in text.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    assert entries == ["aan-tal", "mid-den", "zee-man"]
    clear_syllable_dictionary_cache()


def test_mvsa_replace_shrinks_hyphen_chain_and_voice_holds() -> None:
    """``ge-nee-st`` → ``ge-neest``: L krimpt; extra stem-``-`` verdwijnt."""
    from vsa.mvsa_align import _voice_tokens
    from vsa.mvsa_parse import parse_l_positions
    from vsa.mvsa_validate import _split_bars
    from vsa.syllable_dict_check import apply_replacements_to_source

    src = (
        "@oct S=0\n"
        "L: Hij ge_-nee_-st_ al |\n"
        "S: a4  /   -    /   -  |\n"
        "A: f4  -   -    -   -  |\n"
    )
    out = apply_replacements_to_source(src, [("ge-nee-st", "ge-neest")])
    l_line = next(ln for ln in out.splitlines() if ln.lstrip().startswith("L:"))
    s_line = next(ln for ln in out.splitlines() if ln.lstrip().startswith("S:"))
    l_body = l_line.split(":", 1)[1]
    s_body = s_line.split(":", 1)[1]
    positions = parse_l_positions(_split_bars(l_body).segments[0])
    s_toks = _voice_tokens(_split_bars(s_body).segments[0])
    assert [p.syllables for p in positions] == [["Hij"], ["ge"], ["neest"], ["al"]]
    assert len(s_toks) == len(positions)
    cores = ["".join(p.syllables) for p in positions]
    assert any("neest" in c for c in cores)
    assert "nee" not in cores
    assert "st" not in cores


def test_prompt_unknown_typed_form_queues_replacement(
    tmp_path: Path, monkeypatch
) -> None:
    from io import StringIO

    clear_syllable_dictionary_cache()
    data = tmp_path / "syllable_dictionary.nl.txt"
    data.write_text("# test\n", encoding="utf-8")
    import vsa.syllable_dictionary as dict_mod
    import vsa.syllable_dict_check as check_mod

    monkeypatch.setattr(dict_mod, "dictionary_file_path", lambda: data)
    monkeypatch.setattr(check_mod, "dictionary_file_path", lambda: data)
    clear_syllable_dictionary_cache()

    surface = "xyzzyxab"
    finding = next(
        f
        for f in find_dictionary_syllable_issues(
            Parser(surface).parse(), source_text=surface
        )
        if f.code == CODE_UNKNOWN
    )
    session = prompt_dictionary_fixes(
        [finding], stdin=_Tty("xyz-zy-xab\n"), stdout=StringIO()
    )
    assert session.added_or_updated == ["xyz-zy-xab"]
    assert session.replacements == [(surface, "xyz-zy-xab")]
    clear_syllable_dictionary_cache()


def test_regeleinde_na_leesteken_is_woordgrens() -> None:
    """``{/mij_},⏎{/ver}{hoor_}`` is NIET één woord ``mij-,-ver-hoor``."""
    from vsa.syllable_dict_check import bare_sung_text, iter_vsa_lyric_word_cores

    body = (
        "[:] Heer ik roep tot U ver{\\hoor_} {/mij_},\n"
        "{/ver}{hoor_} {\\mij} o {/Heer_.},\n"
    )
    document = Parser(body).parse()
    bare = bare_sung_text(document)
    assert "mij-, ver-hoor" in bare
    cores = iter_vsa_lyric_word_cores(document)
    assert cores.count("ver-hoor") == 2 and not any("," in c for c in cores), cores
