"""Unit-tests voor bidirectionele hulptekst (parochieschema)."""

from __future__ import annotations

import pytest

from vsa.transliterate import (
    detect_direction,
    render_ksl_to_latin,
    render_nl_to_cyrillic,
    render_syllable,
    render_syllables,
)


@pytest.mark.parametrize(
    ("src", "expected"),
    [
        ("Свя", "Svja"),
        ("тый", "tyj"),
        ("Бо", "Bo"),
        ("же", "zje"),
        ("Креп", "Krep"),
        ("кый", "kyj"),
        ("Без", "Bez"),
        ("смерт'", "smert'"),
        ("ный", "nyj"),
        ("По", "Po"),
        ("ми", "mi"),
        ("луй", "loej"),
        ("нас", "nas"),
        ("Господи", "Gospodi"),
    ],
)
def test_ksl_to_latin_corpus(src: str, expected: str) -> None:
    assert render_ksl_to_latin(src) == expected


@pytest.mark.parametrize(
    ("src", "expected"),
    [
        ("Heer", "Хер"),  # ee → één е (klank)
        ("ont", "онт"),
        ("ferm", "ферм"),
        ("Amen", "Амен"),
        ("Aan", "Ан"),  # aa → а
        ("U", "У"),
        ("schoen", "схун"),
        ("choral", "хорал"),
    ],
)
def test_nl_to_cyrillic_corpus(src: str, expected: str) -> None:
    assert render_nl_to_cyrillic(src) == expected


def test_render_syllables_preserves_length() -> None:
    src = ["Свя", "тый", "Бо", "же"]
    out = render_syllables(src, direction="ksl_to_latin")
    assert len(out) == len(src)
    assert out == ["Svja", "tyj", "Bo", "zje"]


def test_auto_detect_direction() -> None:
    assert detect_direction("Свя") == "ksl_to_latin"
    assert detect_direction("Heer") == "nl_to_cyrillic"
    assert detect_direction("...") is None
    assert render_syllable("Свя") == "Svja"
    assert render_syllable("Heer") == "Хер"
    assert render_syllable("...") == "..."


def test_unknown_scheme_raises() -> None:
    with pytest.raises(ValueError, match="schema"):
        render_syllable("а", scheme="iso")  # type: ignore[arg-type]
