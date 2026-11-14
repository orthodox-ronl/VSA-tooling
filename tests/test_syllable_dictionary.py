"""Canonieke syllable-dictionary (startset)."""

from vsa.syllable_dictionary import (
    canonical_syllable_form,
    clear_syllable_dictionary_cache,
    load_syllable_dictionary,
    syllable_lemma,
)


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
