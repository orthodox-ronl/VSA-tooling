"""Unit-tests voor bidirectionele hulptekst (parochieschema, bevroren keuzes)."""

from __future__ import annotations

import pytest

from vsa.transliterate import (
    BOGORODITSE_LATIN_LINES,
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
        ("тый", "tiej"),
        ("Бо", "Bo"),
        ("же", "zje"),
        ("Креп", "Krep"),
        ("кый", "kiej"),
        ("Крепкий", "Krepkiej"),
        ("Божий", "Bozjiej"),
        ("Без", "Bez"),
        ("смертный", "smertniej"),
        ("ный", "niej"),
        ("По", "Po"),
        ("ми", "mi"),
        ("луй", "loej"),
        ("нас", "nas"),
        ("Господи", "Gospodi"),
        ("Господь", "Gospod'"),
        ("Аминь", "Amin'"),
        ("Иисусе", "Iesusje"),
        ("ныне", "nynje"),
        ("Дево", "Djevo"),
        ("Марие", "Marieje"),
        ("Трисвятое", "Trisvjatoje"),
        ("воскресе", "voskresje"),
        ("Богородице", "Bogoroditse"),
        ("Царице", "Tsaritse"),
        ("Пресвятая", "Presvjataja"),
        ("Небеси", "Njebesi"),
        ("Мое", "Moje"),
        ("Мене", "Menje"),
        ("Мне", "Mnje"),
        ("Христе", "Christe"),
        ("Величаем", "Velitjajem"),
        ("Единую", "Jedinoejoe"),
        ("Царствие", "Tsarstvieje"),
        ("Старец", "Starets"),
    ],
)
def test_ksl_to_latin_corpus(src: str, expected: str) -> None:
    assert render_ksl_to_latin(src) == expected


@pytest.mark.parametrize(
    ("src", "expected"),
    [
        ("Heer", "Хиир"),
        ("ont", "онт"),
        ("ferm", "ферм"),
        ("Amen", "Аминь"),
        ("Aan", "Ан"),
        ("U", "У"),
        ("schoen", "схун"),
        ("choral", "хорал"),
        ("en", "эн"),
        ("den", "дэн"),
        ("Eer", "Ир"),
        ("eeuwen", "эувен"),
        ("Eeuwen", "Эувен"),
        ("Geest", "Хейст"),
        ("vergeef", "верхейф"),
        ("Christus", "Христус"),
        ("Alleluia", "Аллелуиа"),
        ("God", "Ход"),
        ("Glorie", "Хлори"),
        ("huis", "хёйс"),  # ui middenin → ёй
        ("uit", "аут"),  # ui woordbegin → ау
        ("Heilige", "Хейлихе"),
    ],
)
def test_nl_to_cyrillic_corpus(src: str, expected: str) -> None:
    assert render_nl_to_cyrillic(src) == expected


def test_render_syllables_preserves_length() -> None:
    src = ["Свя", "тый", "Бо", "же"]
    out = render_syllables(src, direction="ksl_to_latin")
    assert len(out) == len(src)
    assert out == ["Svja", "tiej", "Bo", "zje"]


def test_auto_detect_direction() -> None:
    assert detect_direction("Свя") == "ksl_to_latin"
    assert detect_direction("Heer") == "nl_to_cyrillic"
    assert detect_direction("...") is None
    assert render_syllable("Свя") == "Svja"
    assert render_syllable("Heer") == "Хиир"
    assert render_syllable("...") == "..."


def test_uppercase_cyrillic_digraph_titlecase() -> None:
    """Één hoofdletter mag digraph niet volledig uppercasen (Х→Ch, niet CH)."""
    assert render_ksl_to_latin("Христе") == "Christe"
    assert render_ksl_to_latin("Царю") == "Tsarjoe"
    assert render_ksl_to_latin("Утешителю").startswith("Oe")


def test_source_case_followed_on_overrides() -> None:
    assert render_ksl_to_latin("ДЕВО") == "DJEVO"
    assert render_nl_to_cyrillic("HEER") == "ХИИР"


def test_bogoroditse_latin_lines() -> None:
    assert BOGORODITSE_LATIN_LINES[0] == "Bogoroditse Djevo radoejsja"
    assert "Gospod'" in BOGORODITSE_LATIN_LINES[1]
    assert BOGORODITSE_LATIN_LINES[1].startswith("Blagodatnaja Marieje")


def test_unknown_scheme_raises() -> None:
    with pytest.raises(ValueError, match="schema"):
        render_syllable("а", scheme="iso")  # type: ignore[arg-type]
