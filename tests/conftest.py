"""Pytest: canonieke syllable-dictionary uit tests/fixtures (niet package-stub)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vsa.syllable_dictionary import (
    clear_syllable_dictionary_cache,
    set_lyrics_lang,
    set_syllable_dictionary_path,
)

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "syllable_dictionary.nl.txt"


@pytest.fixture(autouse=True)
def _syllable_dictionary_fixture():
    # Expliciet nl + fixture-pad, zodat ``auto``-resolve de testlijst niet
    # overschrijft met een lege package/sibling-detectie.
    set_lyrics_lang("nl")
    set_syllable_dictionary_path(_FIXTURE)
    clear_syllable_dictionary_cache()
    yield
    set_lyrics_lang("auto")
    set_syllable_dictionary_path(None)
    clear_syllable_dictionary_cache()
