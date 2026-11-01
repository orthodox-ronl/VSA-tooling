"""Bidirectionele hulptekst: kerkslavisch ↔ Latijn / Nederlands ↔ Cyrillisch.

Parochieschema (``scheme=\"parochie\"``): uitspraakweergave voor meezingen,
geen wetenschappelijke ISO-transcriptie. Roundtrip letter-voor-letter is
geen doel.

Bevroren keuzes (expert-review + K&K): zie
``docs/plans/transliteraties-keuzes.md``.
"""

from __future__ import annotations

from typing import Literal

Direction = Literal["ksl_to_latin", "nl_to_cyrillic"]
Scheme = Literal["parochie"]

# Cyrillisch → Latijn: basisletters (``е``/``ь``/``ий`` via context in renderer).
_KSL_TO_LATIN: dict[str, str] = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
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

# Medeklinkers waar ``е`` als gewone ``e`` blijft (geen ``je``).
_KSL_E_PLAIN_AFTER = frozenset("цгжшщч")
# Medeklinkers waar ``е`` als ``je`` (nynje, Djevo, …). Geen ``м``/``т``:
# ``Мене``/``Мне`` via overrides; ``Христе`` blijft Christe; ``смерт`` geen smjert.
_KSL_E_JE_AFTER = frozenset("ндл")

# Vaste overrides (lowercase key → canonieke Latijnse vorm, bron-hoofdletter later).
_KSL_OVERRIDES: dict[str, str] = {
    "ныне": "nynje",
    "дево": "djevo",
    "марие": "marieje",
    "трисвятое": "trisvjatoje",
    "воскресе": "voskresje",
    "господь": "gospod'",
    "крепкий": "krepkiej",
    "божий": "bozjiej",
    "аминь": "amin'",
    "иисусе": "iesusje",
    "иисус": "iesus",
    "иисуса": "iesusa",
    "иисусу": "iesusoe",
    "иисусом": "iesusom",
    "величаем": "velitjajem",
    "единую": "jedinoejoe",
    "небеси": "njebesi",
    "царствие": "tsarstvieje",
    "мое": "moje",
    "мене": "menje",
    "мне": "mnje",
}

# Nederlands → Cyrillisch: digraphen (langste match eerst).
_NL_TO_CYR_DIGRAPHS: tuple[tuple[str, str], ...] = (
    ("eeuwen", "эувен"),  # vaste uitzondering vóór ``ee``
    ("sch", "сх"),
    ("ch", "х"),
    ("ng", "нг"),
    ("nk", "нк"),
    ("aa", "а"),
    ("ee", "ей"),
    ("oo", "о"),
    ("uu", "ю"),
    ("oe", "у"),
    ("ie", "и"),
    ("ei", "ей"),
    ("ij", "ей"),
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

# Hele-woord overrides (lowercase → Cyrillisch; case via ``_case_like``).
_NL_OVERRIDES: dict[str, str] = {
    "heer": "хиир",
    "amen": "аминь",
    "amin": "аминь",
    "amin'": "аминь",
    "christus": "христус",
    "alleluia": "аллелуиа",
    "eeuwen": "эувен",
    "eer": "ир",
    "en": "эн",
    "den": "дэн",
    "god": "ход",
    "glorie": "хлори",
    "geest": "хейст",
    "vergeef": "верхейф",
}


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
    # Één hoofdletter (Cyrillisch of Latijn) mag digraphen niet volledig
    # uppercasen (Х→CH, Ц→TS); alleen bij hele woorden in HOOFDLETTERS.
    if len(src) > 1 and src.isupper():
        return mapped.upper()
    if src[:1].isupper():
        return mapped[:1].upper() + mapped[1:]
    return mapped


def _strip_stress(text: str) -> str:
    """Verwijder kombinerende accenten (kerkslavische klemtoontekens)."""
    return "".join(c for c in text if not (0x0300 <= ord(c) <= 0x036F))


def _lookup_override(text: str, table: dict[str, str]) -> str | None:
    key = _strip_stress(text).casefold()
    # Normaliseer typografische apostrof → toetsenbord-'.
    key = key.replace("\u2019", "'").replace("\u02bc", "'")
    mapped = table.get(key)
    if mapped is None:
        return None
    return _case_like(text, mapped)


def _is_cyr_vowel(ch: str) -> bool:
    return ch.lower() in "аеёиоуыэюяѣіїѧѫѹѡѥ"


def _ksl_e_to_latin(prev: str | None, *, word_initial: bool, word_final: bool) -> str:
    """``е`` → ``je`` of ``e`` volgens bevroren expert-keuzes."""
    if word_initial:
        return "je"
    if prev is None:
        return "je"
    p = prev.lower()
    if p in _KSL_E_PLAIN_AFTER:
        return "e"
    if _is_cyr_vowel(p) or p in "'ьъ":
        return "je"
    if p in _KSL_E_JE_AFTER:
        return "je"
    # Woord-einde: ``je`` na klinker / н д л; anders ``e`` (Christe, niet Christje).
    # ``воскресе`` e.d. via override → …sje.
    if word_final and (_is_cyr_vowel(p) or p in _KSL_E_JE_AFTER or p in "'ьъ"):
        return "je"
    return "e"


def render_ksl_to_latin(text: str) -> str:
    hit = _lookup_override(text, _KSL_OVERRIDES)
    if hit is not None:
        return hit

    raw = _strip_stress(text)
    # Digraph ``пре`` aan woordbegin / na niet-letter → ``pre`` (geen prje).
    out: list[str] = []
    i = 0
    n = len(raw)
    prev_cyr: str | None = None
    while i < n:
        ch = raw[i]
        lower = ch.lower()

        # ``ий`` / ``ый`` → ``iej`` (Krepkiej, Bozjiej, …).
        if i + 1 < n and lower in "иы" and raw[i + 1].lower() == "й":
            chunk = raw[i : i + 2]
            out.append(_case_like(chunk, "iej"))
            prev_cyr = raw[i + 1]
            i += 2
            continue

        # ``пре`` zonder ``je`` (Пресвятая, …).
        if lower == "п" and raw[i : i + 3].casefold() == "пре":
            if prev_cyr is None or not _is_cyrillic_char(prev_cyr):
                chunk = raw[i : i + 3]
                out.append(_case_like(chunk, "pre"))
                prev_cyr = raw[i + 2]
                i += 3
                continue

        # ``ец`` → ``ets`` (е niet als je).
        if lower == "е" and i + 1 < n and raw[i + 1].lower() == "ц":
            out.append(_case_like(ch, "e"))
            prev_cyr = ch
            i += 1
            continue

        if lower == "е":
            word_initial = prev_cyr is None or not _is_cyrillic_char(prev_cyr)
            # word_final: rest is geen Cyrillische letter meer.
            rest = raw[i + 1 :]
            word_final = not any(_is_cyrillic_char(c) for c in rest)
            mapped = _ksl_e_to_latin(
                prev_cyr, word_initial=word_initial, word_final=word_final
            )
            out.append(_case_like(ch, mapped))
            prev_cyr = ch
            i += 1
            continue

        if lower == "ь":
            out.append("'")
            prev_cyr = ch
            i += 1
            continue

        if lower in _KSL_TO_LATIN:
            out.append(_case_like(ch, _KSL_TO_LATIN[lower]))
            prev_cyr = ch
            i += 1
            continue

        out.append(ch)
        if _is_cyrillic_char(ch):
            prev_cyr = ch
        elif ch.isalpha():
            prev_cyr = ch
        i += 1
    return "".join(out)


def render_nl_to_cyrillic(text: str) -> str:
    hit = _lookup_override(text, _NL_OVERRIDES)
    if hit is not None:
        return hit

    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if not ch.isalpha() and ch not in "'\u2019":
            out.append(ch)
            i += 1
            continue
        lower = text[i:].casefold()

        # ``ui``: woordbegin → ``ау``, anders ``ёй``.
        if lower.startswith("ui"):
            at_start = i == 0 or not text[i - 1].isalpha()
            repl = "ау" if at_start else "ёй"
            chunk = text[i : i + 2]
            out.append(_case_like(chunk, repl))
            i += 2
            continue

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


# Bogoroditse-frase (canonieke Latijnse hulptekst, regels).
BOGORODITSE_LATIN_LINES: tuple[str, ...] = (
    "Bogoroditse Djevo radoejsja",
    "Blagodatnaja Marieje Gospod' s Tobojoe",
    "Blagoslovenna Ty v zjenach",
    "I blagosloven Plod tjreva Tvojego",
    "Jako Spasa rodila jesi doesj nasjiech",
)


__all__ = [
    "BOGORODITSE_LATIN_LINES",
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
