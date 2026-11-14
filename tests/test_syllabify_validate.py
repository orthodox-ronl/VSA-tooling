"""Validate: ontbrekende soft lettergreepstreepjes (Pyphen, zonder dictionary)."""

from pathlib import Path

from vsa.monosyllable_exceptions import (
    clear_monosyllable_exceptions_cache,
    is_monosyllable_exception,
    load_monosyllable_exceptions,
)
from vsa.parser import Parser
from vsa.syllabify_validate import (
    CODE,
    find_missing_syllable_hyphens,
    format_missing_hyphen_message,
)
from vsa.syllable_dict_check import CODE_MISMATCH
from vsa.syllable_dictionary import clear_syllable_dictionary_cache
from vsa.validation_runner import validate_file


def test_unknown_to_dictionary_uses_pyphen_missing_path(monkeypatch) -> None:
    """Zonder dictionary-treffer blijft de oude Pyphen-missing-check."""
    clear_syllable_dictionary_cache()
    import vsa.syllable_dictionary as dict_mod

    monkeypatch.setattr(dict_mod, "load_syllable_dictionary", lambda: {})
    text = "Uw kwinkeleer Licht"
    doc = Parser(text).parse()
    findings = find_missing_syllable_hyphens(doc, source_text=text)
    assert findings
    message, hint = format_missing_hyphen_message(findings[0])
    assert "monosyllable_exceptions.nl.txt" in hint
    assert "vsa syllabify" in hint


def test_already_hyphenated_word_is_silent() -> None:
    text = "Uw eeu-wig Licht"
    doc = Parser(text).parse()
    findings = find_missing_syllable_hyphens(doc, source_text=text)
    assert not any(f.word.casefold() == "eeuwig" for f in findings)


def test_scope_text_is_not_checked() -> None:
    text = "{/onbederfelijke_}"
    doc = Parser(text).parse()
    findings = find_missing_syllable_hyphens(doc, source_text=text)
    assert findings == []


def test_exception_suppresses_pyphen_missing(tmp_path: Path, monkeypatch) -> None:
    clear_monosyllable_exceptions_cache()
    clear_syllable_dictionary_cache()
    import vsa.syllable_dictionary as dict_mod
    import vsa.monosyllable_exceptions as mod

    monkeypatch.setattr(dict_mod, "load_syllable_dictionary", lambda: {})
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "monosyllable_exceptions.nl.txt").write_text(
        "kwinkeleer\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        mod,
        "exceptions_file_path",
        lambda: data_dir / "monosyllable_exceptions.nl.txt",
    )
    clear_monosyllable_exceptions_cache()
    assert is_monosyllable_exception("Kwinkeleer")
    text = "Uw kwinkeleer Licht"
    doc = Parser(text).parse()
    findings = find_missing_syllable_hyphens(doc, source_text=text)
    assert not any(f.word.casefold() == "kwinkeleer" for f in findings)
    clear_monosyllable_exceptions_cache()


def test_validate_file_dictionary_mismatch_for_eeuwig(tmp_path: Path) -> None:
    path = tmp_path / "eeuwig.vsa"
    path.write_text("Uw eeuwig Licht\n", encoding="utf-8")
    result = validate_file(path)
    hits = [m for m in result.messages if m.code == CODE_MISMATCH]
    assert hits
    assert hits[0].severity == "error"
    assert "eeu-wig" in hits[0].message_nl
    assert not result.ok


def test_bundled_exceptions_file_loads() -> None:
    clear_monosyllable_exceptions_cache()
    words = load_monosyllable_exceptions()
    assert isinstance(words, frozenset)
