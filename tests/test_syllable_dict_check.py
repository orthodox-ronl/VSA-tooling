"""Dictionary-check op VSA-body."""

from pathlib import Path

from vsa.parser import Parser
from vsa.syllabify import hyphenate_dutch_word
from vsa.syllable_dict_check import (
    CODE_MISMATCH,
    CODE_UNKNOWN,
    append_canonical_form,
    apply_replacements_to_text,
    find_dictionary_syllable_issues,
    prompt_dictionary_fixes,
    replace_sung_token_in_text,
    set_canonical_form,
)
from vsa.syllable_dictionary import (
    clear_syllable_dictionary_cache,
    load_syllable_dictionary,
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


def test_validate_file_dictionary_mismatch_is_error(tmp_path: Path) -> None:
    path = tmp_path / "bad.vsa"
    # Foute deling zit ín scopes → syllabify kan geen soft `-` bijzetten.
    path.write_text("{eeuwi}{ge}\n", encoding="utf-8")
    result = validate_file(path)
    hits = [m for m in result.messages if m.code == CODE_MISMATCH]
    assert hits
    assert hits[0].severity == "error"
    assert not result.ok
    assert "{eeuwi}{ge}" in path.read_text(encoding="utf-8")


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


def test_set_canonical_form_replaces_lemma(tmp_path: Path, monkeypatch) -> None:
    data = tmp_path / "syllable_dictionary.nl.txt"
    data.write_text("ou-de-vorm\n", encoding="utf-8")
    import vsa.syllable_dictionary as dict_mod
    import vsa.syllable_dict_check as check_mod

    monkeypatch.setattr(dict_mod, "dictionary_file_path", lambda: data)
    monkeypatch.setattr(check_mod, "dictionary_file_path", lambda: data)
    clear_syllable_dictionary_cache()
    written = set_canonical_form("ou-de=vorm", allow_replace=True)
    assert written == "ou-de=vorm"
    assert "ou-de-vorm" not in data.read_text(encoding="utf-8")
    assert "ou-de=vorm" in data.read_text(encoding="utf-8")
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
