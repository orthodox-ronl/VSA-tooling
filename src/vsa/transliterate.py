"""Bidirectionele hulptekst: kerkslavisch ↔ Latijn / Nederlands ↔ Cyrillisch.

Parochieschema (``scheme=\"parochie\"``): uitspraakweergave voor meezingen,
geen wetenschappelijke ISO-transcriptie. Roundtrip letter-voor-letter is
geen doel.
"""

from __future__ import annotations

from typing import Literal

Direction = Literal["ksl_to_latin", "nl_to_cyrillic"]
Scheme = Literal["parochie"]

# Cyrillisch (incl. kerkslavische archaïsmen) → Latijn (NL-parochiegebruik).
# Langere keys eerst bij lookup via gesorteerde keys.
_KSL_TO_LATIN: dict[str, str] = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "jo",
    "ж": "zj",
    "з": "z",
    "и": "i",
    "й": "j",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "oe",
    "ф": "f",
    "х": "ch",
    "ц": "ts",
    "ч": "tsj",
    "ш": "sj",
    "щ": "sjtsj",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "joe",
    "я": "ja",
    "ѣ": "ie",
    "і": "i",
    "ї": "ji",
    "ѳ": "f",
    "ѵ": "i",
    "ѧ": "ja",
    "ѫ": "oe",
    "ѭ": "joe",
    "ѩ": "ja",
    "ѹ": "oe",
    "ѡ": "o",
    "ѥ": "je",
    "ѯ": "ks",
    "ѱ": "ps",
    "ѻ": "o",
    "ѽ": "o",
    "ѿ": "ot",
    "ҁ": "",
    "҂": "",
}

# Nederlands (Latijn) → Cyrillisch: digraphen eerst (langste match).
_NL_TO_CYR_DIGRAPHS: tuple[tuple[str, str], ...] = (
    ("sch", "сх"),
    ("ch", "х"),
    ("ng", "нг"),
    ("nk", "нк"),
    ("aa", "а"),
    ("ee", "е"),
    ("oo", "о"),
    ("uu", "ю"),
    ("oe", "у"),
    ("ie", "и"),
    ("ei", "ей"),
    ("ij", "ей"),
    ("ui", "ёй"),
    ("ou", "ау"),
    ("au", "ау"),
    ("eu", "ёй"),
    ("th", "т"),
    ("qu", "кв"),
)

_NL_TO_CYR_SINGLE: dict[str, str] = {
    "a": "а",
    "b": "б",
    "c": "к",
    "d": "д",
    "e": "е",
    "f": "ф",
    "g": "х",
    "h": "х",
    "i": "и",
    "j": "й",
    "k": "к",
    "l": "л",
    "m": "м",
    "n": "н",
    "o": "о",
    "p": "п",
    "q": "к",
    "r": "р",
    "s": "с",
    "t": "т",
    "u": "у",
    "v": "в",
    "w": "в",
    "x": "кс",
    "y": "й",
    "z": "з",
}

_CYR_RE = None  # lazy


def _is_cyrillic_char(ch: str) -> bool:
    o = ord(ch)
    return (
        0x0400 <= o <= 0x04FF
        or 0x0500 <= o <= 0x052F
        or 0x2DE0 <= o <= 0x2DFF
        or 0xA640 <= o <= 0xA69F
    )


def has_cyrillic(text: str) -> bool:
    return any(_is_cyrillic_char(c) for c in text)


def has_latin_letter(text: str) -> bool:
    return any("a" <= c.lower() <= "z" for c in text)


def detect_direction(text: str) -> Direction | None:
    """Richting uit schrift van de token; ``None`` als niet te bepalen."""
    cyr = has_cyrillic(text)
    lat = has_latin_letter(text)
    if cyr and not lat:
        return "ksl_to_latin"
    if lat and not cyr:
        return "nl_to_cyrillic"
    if cyr:
        return "ksl_to_latin"
    return None


def _case_like(src: str, mapped: str) -> str:
    if not mapped:
        return mapped
    if src.isupper():
        return mapped.upper()
    if src[0].isupper():
        return mapped[0].upper() + mapped[1:]
    return mapped


def _ksl_char_to_latin(ch: str) -> str:
    lower = ch.lower()
    mapped = _KSL_TO_LATIN.get(lower)
    if mapped is None:
        return ch
    return _case_like(ch, mapped)


def render_ksl_to_latin(text: str) -> str:
    return "".join(_ksl_char_to_latin(c) for c in text)


def render_nl_to_cyrillic(text: str) -> str:
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if not ch.isalpha():
            out.append(ch)
            i += 1
            continue
        lower = text[i:].lower()
        matched = False
        for digraph, repl in _NL_TO_CYR_DIGRAPHS:
            if lower.startswith(digraph):
                chunk = text[i : i + len(digraph)]
                out.append(_case_like(chunk, repl))
                i += len(digraph)
                matched = True
                break
        if matched:
            continue
        single = _NL_TO_CYR_SINGLE.get(ch.lower())
        if single is None:
            out.append(ch)
        else:
            out.append(_case_like(ch, single))
        i += 1
    return "".join(out)


def render_syllable(
    text: str,
    *,
    direction: Direction | None = None,
    scheme: Scheme = "parochie",
) -> str:
    """Zet één lettergreep/token om; onbekende richting → ongewijzigd."""
    if scheme != "parochie":
        raise ValueError(f"onbekend schema {scheme!r}")
    if not text:
        return text
    dir_ = direction or detect_direction(text)
    if dir_ is None:
        return text
    if dir_ == "ksl_to_latin":
        return render_ksl_to_latin(text)
    return render_nl_to_cyrillic(text)


def render_syllables(
    syllables: list[str],
    *,
    direction: Direction | None = None,
    scheme: Scheme = "parochie",
) -> list[str]:
    """Zelfde lengte als *syllables*; 1:1 mapping per token."""
    return [
        render_syllable(s, direction=direction, scheme=scheme) for s in syllables
    ]


__all__ = [
    "Direction",
    "Scheme",
    "detect_direction",
    "has_cyrillic",
    "has_latin_letter",
    "render_ksl_to_latin",
    "render_nl_to_cyrillic",
    "render_syllable",
    "render_syllables",
]
