"""Migratiestap 7: tooling-API voor lyric-tokens vervangt ``nl_hyphen.py`` van bibliotheek.

De 32 uitzonderingen uit ``nl_hyphen.HYPHEN_EXCEPTIONS`` staan in het woordenboek
(``data/syllable_dictionary.nl.txt``); deze test legt vast dat de tooling-API voor elk
dezelfde splitsing geeft. Besluit eigenaar (2026-11-20): ``eeuwen`` is ``eeu-wen``.
"""

from __future__ import annotations

import pytest

from vsa.syllabify import hyphenate_token_parts, split_syllabic

# woord -> verwachte splitsing (was HYPHEN_EXCEPTIONS in bibliotheek/scripts/nl_hyphen.py)
FORMER_EXCEPTIONS = {
    "altijd": "al-tijd",
    "eeuwen": "eeu-wen",  # besluit 2026-11-20 (was eeuw-en)
    "aanbidden": "aan-bid-den",
    "aanschouwen": "aan-schou-wen",
    "aarde": "aar-de",
    "allerlei": "al-ler-lei",
    "barmhartigheid": "barm-har-tig-heid",
    "barmhartigen": "barm-har-ti-gen",
    "dorsten": "dors-ten",
    "gedenk": "ge-denk",
    "gekomen": "ge-ko-men",
    "geschieden": "ge-schie-den",
    "heilige": "hei-li-ge",
    "hemelse": "he-mel-se",
    "hongeren": "hon-ge-ren",
    "kinderen": "kin-de-ren",
    "koninkrijk": "ko-nink-rijk",
    "lasterlijk": "las-ter-lijk",
    "nedervallen": "ne-der-val-len",
    "opgestaan": "op-ge-staan",
    "treurenden": "treu-ren-den",
    "vader": "va-der",
    "verheugt": "ver-heugt",
    "vervolgd": "ver-volgd",
    "vredestichters": "vre-de-stich-ters",
    "wanneer": "wan-neer",
    "wonderbaar": "won-der-baar",
    "worden": "wor-den",
    "zachtmoedigen": "zacht-moe-di-gen",
    "zalig": "za-lig",
    "zingen": "zin-gen",
    "zullen": "zul-len",
}


@pytest.mark.parametrize("word,expected", sorted(FORMER_EXCEPTIONS.items()))
def test_former_exception_gets_same_split_from_tooling(word: str, expected: str) -> None:
    assert hyphenate_token_parts(word) == expected.split("-")


def test_token_keeps_punctuation_and_case() -> None:
    assert hyphenate_token_parts("Heilige,") == ["Hei", "li", "ge,"]
    assert hyphenate_token_parts("(Vader") == ["(Va", "der"]
    assert hyphenate_token_parts("ZINGEN") == ["ZIN", "GEN"]


def test_unknown_word_is_not_guessed() -> None:
    """Onbekende woorden blijven heel; de schrijver beslist (geen naive regels meer)."""
    assert hyphenate_token_parts("onbekendwoordje") == ["onbekendwoordje"]


def test_empty_and_blank_tokens() -> None:
    assert hyphenate_token_parts("") == []
    assert hyphenate_token_parts("  ") == []


@pytest.mark.parametrize(
    "orig,i,n,expected",
    [
        ("single", 0, 1, "single"),
        ("", 0, 3, "begin"),
        ("", 1, 3, "middle"),
        ("", 2, 3, "end"),
        ("begin", 0, 2, "begin"),
        ("begin", 1, 2, "middle"),
        ("middle", 1, 3, "middle"),
        ("end", 2, 3, "end"),
        ("end", 0, 3, "middle"),
    ],
)
def test_split_syllabic(orig: str, i: int, n: int, expected: str) -> None:
    assert split_syllabic(orig, i, n) == expected
