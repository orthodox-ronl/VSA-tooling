"""Canonieke syllable-dictionary (startset)."""

from pathlib import Path

from vsa.syllable_dictionary import (
    allowed_syllable_forms,
    canonical_syllable_form,
    clear_syllable_dictionary_cache,
    is_allowed_syllable_form,
    load_syllable_dictionary,
    parse_syllable_dictionary_text,
    set_syllable_dictionary_path,
    syllable_lemma,
)
from vsa.syllabify import hyphenate_dutch_word
from vsa.syllable_dict_check import CODE_MISMATCH, find_dictionary_syllable_issues_from_cores


def setup_function() -> None:
    clear_syllable_dictionary_cache()


def test_lemma_strips_hyphens_and_hard_equals() -> None:
    assert syllable_lemma("me-de=eeu-wi-ge") == "medeeeuwige"
    assert syllable_lemma("Eeu-wig") == "eeuwig"


def test_known_corrections_in_dictionary() -> None:
    d = load_syllable_dictionary()
    assert d[syllable_lemma("apostel")] == "a-pos-tel"
    assert d[syllable_lemma("eeuwige")] == "eeu-wi-ge"
    assert d[syllable_lemma("medeeeuwige")] == "me-de=eeu-wi-ge"
    assert d[syllable_lemma("drieeenheid")] == "drie=een-heid"
    assert d[syllable_lemma("eniggeboren")] == "e-nig=ge-bo-ren"
    assert d[syllable_lemma("hiërarch")] == "hiër-arch"
    assert d[syllable_lemma("overwinning")] == "o-ver-win-ning"
    assert canonical_syllable_form("eeuwi-ge") == "eeu-wi-ge"
    assert "eeuwi-ge" not in d.values()
    assert "ge-stand-doen" not in d.values()
    assert "hoor-mij-oheer" not in d.values()


def test_dictionary_lemmas_unique() -> None:
    d = load_syllable_dictionary()
    assert len(d) >= 700
    assert len(d) == len(set(d.values()))


def test_plus_alt_forms_parse_and_validate(tmp_path: Path) -> None:
    from vsa.syllable_dictionary import apply_syllable_dictionary_from_config

    data = tmp_path / "dict.txt"
    data.write_text(
        "# test\nal-le-lu-ia\n+al-le-lu-i-a\na-men\n",
        encoding="utf-8",
    )
    apply_syllable_dictionary_from_config(cli_path=data, lang="nl")
    clear_syllable_dictionary_cache()
    try:
        assert canonical_syllable_form("alleluia") == "al-le-lu-ia"
        assert allowed_syllable_forms("alleluia") == frozenset(
            {"al-le-lu-ia", "al-le-lu-i-a"}
        )
        assert is_allowed_syllable_form("al-le-lu-i-a")
        assert is_allowed_syllable_form("al-le-lu-ia")
        assert not is_allowed_syllable_form("al-le-lui-a")

        findings = find_dictionary_syllable_issues_from_cores(
            ["al-le-lu-ia", "al-le-lu-i-a", "al-le-lui-a"],
            lyrics_lang="nl",
        )
        assert not any(f.surface == "al-le-lu-ia" for f in findings)
        assert not any(f.surface == "al-le-lu-i-a" for f in findings)
        assert any(
            f.code == CODE_MISMATCH and f.surface == "al-le-lui-a" for f in findings
        )

        assert hyphenate_dutch_word("al-le-lu-i-a") == "al-le-lu-i-a"
        assert hyphenate_dutch_word("Alleluia") == "Al-le-lu-ia"
    finally:
        set_syllable_dictionary_path(None)
        clear_syllable_dictionary_cache()


def test_plus_alt_rejects_wrong_lemma() -> None:
    try:
        parse_syllable_dictionary_text("a-men\n+al-le-lu-ia\n")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "open groep" in str(exc) or "hoort bij" in str(exc)


def test_commentaar_boven_woord_blijft_bij_sorteren(tmp_path):
    from vsa.syllable_dict_check import rewrite_dictionary_sorted

    p = tmp_path / "d.txt"
    p.write_text(
        "# kop\n\nzon-der\n# let op: eigennaam\n# tweede regel\nbe-gin\n"
        "# bij de alt\n+beg-in\n",
        encoding="utf-8",
    )
    rewrite_dictionary_sorted(p)
    assert p.read_text(encoding="utf-8") == (
        "# kop\n\n"
        "# let op: eigennaam\n# tweede regel\n# bij de alt\nbe-gin\n+beg-in\n"
        "zon-der\n"
    )
    rewrite_dictionary_sorted(p)  # idempotent
    assert p.read_text(encoding="utf-8").count("# let op") == 1
