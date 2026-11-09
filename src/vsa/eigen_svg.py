"""Eigen partituur-SVG uit Score-IR (``mvsa svg --engine eigen``).

Drie beelden van dezelfde Score-IR:

- ``notes`` — partituur zonder VSA-strepen
- ``vsa-notes`` — dezelfde partituur mét sopraan-VSA
- ``vsa`` — kale VSA: lettergrepen en strepen, geen notenbalk

OSMD en MuseScore blijven de andere engines. Dit bestand is geen
standaardproduct.
"""

from __future__ import annotations

import base64
import html
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .bravura_glyphs import GLYPHS, STAFF_UNITS
from .music import Pitch
from .mvsa_normalize import format_ehm
from .pitch_resolver import _SCALE_INTERVALS, pitch_to_degree_and_chrom
from .svg_glyphs import SVGGlyphRenderer

EIGEN_VIEWS: tuple[str, ...] = ("notes", "vsa-notes", "vsa")
# Regelbreedte in tekening-eenheden (ongeveer CSS-pixels). Een langere
# regel breekt af, ook midden in een maat. None: alleen @nieuw-systeem.
DEFAULT_SYSTEM_WIDTH = 760.0
FONT_FAMILY = "Source Sans 3"
# Zelfde maten als MuseScore-Style (checklist S7, leesbaarheid L2).
LYRIC_PT = 13.0
CUE_PT = 12.0
LYRIC_WEIGHT = "400"
_PT = 96.0 / 72.0
SP = 12.0
LYRIC_FONT = LYRIC_PT * _PT
# Klein wit tussen lettergrepen: MuseScore-nabewerking houdt ~0,45 spatium,
# plus ruimte voor het koppelteken. Geen tijd-raster dat de maat oprekt.
LYRIC_GAP = 10.0
MEASURE_GLUE = 4.0
# MuseScore beamWidth is 0,5 spatium. De balk was 2,4 px; dit zit daar tegenaan.
BEAM_WIDTH = 6.0
BEAM_SHIFT = 9.0
# Bravura: één staff space = 250 font-eenheden.
GLYPH_SCALE = SP / STAFF_UNITS

_NAV_LABEL = {
    "segno": "Segno",
    "fine": "Fine",
    "to_coda": "To Coda",
    "coda": "Coda",
    "ds_al_fine": "D.S. al Fine",
    "dc_al_fine": "D.C. al Fine",
    "ds_al_coda": "D.S. al Coda",
    "dc_al_coda": "D.C. al Coda",
}


class EigenSvgError(Exception):
    """Eigen SVG-export mislukt."""


def normalize_eigen_view(name: str | None) -> str:
    if name is None or not str(name).strip():
        return "notes"
    key = str(name).strip().lower()
    if key not in EIGEN_VIEWS:
        known = ", ".join(EIGEN_VIEWS)
        raise EigenSvgError(f"onbekend beeld {name!r} (verwacht: {known})")
    return key


def _half_width(name: str) -> float:
    _d, x0, _y0, x1, _y1 = GLYPHS[name]
    return (x1 - x0) * GLYPH_SCALE / 2.0


def _paint_glyph(
    name: str,
    x: float,
    y: float,
    css: str,
    *,
    center: bool = False,
) -> str:
    """Zet een Bravura-contour op (x, y). Zonder center ligt font-oorsprong (0, 0) daar."""
    d, x0, y0, x1, y1 = GLYPHS[name]
    if center:
        ox = x - (x0 + x1) / 2.0 * GLYPH_SCALE
        oy = y + (y0 + y1) / 2.0 * GLYPH_SCALE
    else:
        ox = x
        oy = y
    return (
        f'<path class="{css}" d="{d}" fill="black" fill-rule="nonzero" '
        f'transform="translate({ox:.2f},{oy:.2f}) scale({GLYPH_SCALE:.5f},{-GLYPH_SCALE:.5f})"/>'
    )


def _head_name(ev: Ev) -> str:
    if ev.breve:
        return "noteheadDoubleWhole"
    if _whole(ev.elm):
        return "noteheadWhole"
    if _note_open(ev.elm):
        return "noteheadHalf"
    return "noteheadBlack"


def _ehm_glyph(token: str) -> str:
    """``/2`` en ``\\\\2`` uit format_ehm → gestapelde strepen die de VSA-tekenaar kent."""
    prefix = ""
    body = token
    if body[:1] in {"#", "b"}:
        prefix = body[0]
        body = body[1:]
    if body in {"-", "~"}:
        base = "-" if body == "-" else "~"
    elif body.startswith("/"):
        n = int(body[1:]) if len(body) > 1 else 1
        base = "/" * n
    elif body.startswith("\\"):
        n = int(body[1:]) if len(body) > 1 else 1
        base = "\\" * n
    else:
        base = body
    return prefix + base


def _token_moves(token: str) -> bool:
    """Een kale ``-`` of ``~`` is geen zichtbare VSA-streep."""
    body = token[1:] if token[:1] in {"#", "b"} else token
    return body not in {"-", "~", ""}


def _shows_length(elm: str) -> bool:
    """``~`` en ``-`` zijn een gewone tel. ``_``, ``__`` en ``.`` zijn een teken."""
    return elm not in {"", "~", "-"}


def soprano_vsa_plan(
    doc: dict[str, Any],
) -> tuple[list[tuple[int, int, str, str]], list[tuple[int, int, str]]]:
    """Zichtbare sopraan-VSA en onderstrepingen.

    Een liggende ``-`` komt alleen in beeld binnen een melisma dat ook een
    stijgende of dalende streep heeft (``-&/`` of ``-&\\``). Een
    onderstreping staat op de nootpositie waar de bron een lengteteken heeft.
    Bij «lu_&~&~&_» zijn dat dus de eerste en de laatste noot.
    """
    ctx = doc.get("pitchContext") or {}
    do = _parse_do(str(ctx.get("do") or "F4"))
    mode = str(ctx.get("mode") or "major")
    intervals = _SCALE_INTERVALS.get(mode, _SCALE_INTERVALS["major"])
    prev: int | None = None
    marks: list[tuple[int, int, str, str]] = []
    underlines: list[tuple[int, int, str]] = []
    for measure_i, measure in enumerate(doc.get("measures") or []):
        events = _events_for_voice(list((measure.get("voices") or {}).get("S") or []), "S")
        pitched: list[tuple[Ev, str, str]] = []
        for ev in events:
            if ev.step is None or ev.octave is None:
                continue
            pitch = Pitch(step=ev.step, octave=ev.octave, alter=ev.alter)
            degree, _chrom = pitch_to_degree_and_chrom(do, pitch, intervals)
            token = "-" if prev is None else format_ehm(prev, pitch, do, intervals)
            prev = degree
            pitched.append((ev, token, _ehm_glyph(token)))
            if not ev.spacer and not ev.rest and _shows_length(ev.elm):
                underlines.append((measure_i, ev.index, ev.elm))
        group: list[tuple[Ev, str, str]] = []
        groups: list[list[tuple[Ev, str, str]]] = []
        for item in pitched:
            if item[0].lyric_index is not None and group:
                groups.append(group)
                group = []
            group.append(item)
        if group:
            groups.append(group)
        for grouped in groups:
            if any(_token_moves(token) for _ev, token, _glyph in grouped):
                for ev, token, glyph in grouped:
                    marks.append((measure_i, ev.index, token, glyph))
    return marks, underlines


def soprano_vsa_tokens(doc: dict[str, Any]) -> list[tuple[int, str, str]]:
    """Zichtbare VSA-strepen van de sopraan, in leesvolgorde."""
    marks, _underlines = soprano_vsa_plan(doc)
    return [(index, token, glyph) for _measure_i, index, token, glyph in marks]


def _parse_do(raw: str) -> Pitch:
    text = raw.strip()
    step = text[0].upper()
    rest = text[1:]
    alter = 0.0
    if rest.startswith("#"):
        alter = 1.0
        rest = rest[1:]
    elif rest.startswith("b"):
        alter = -1.0
        rest = rest[1:]
    octave = int(rest) if rest else 4
    return Pitch(step=step, octave=octave, alter=alter)

_ELM_QUARTERS: dict[str, float] = {
    "~": 1.0,
    "-": 1.0,
    "-.": 1.5,
    "~.": 1.5,
    "~..": 1.75,
    "_": 2.0,
    "_.": 3.0,
    "_..": 3.5,
    "__": 4.0,
    "__.": 6.0,
    "__..": 7.0,
    ".": 0.5,
    "..": 0.25,
}

_STEPS = "CDEFGAB"
_STEM_UP = frozenset({"S", "T"})
_STAFF_OF = {"S": "treble", "A": "treble", "T": "bass", "B": "bass"}


@dataclass
class Ev:
    voice: str
    index: int
    start: float
    end: float
    step: str | None
    octave: int | None
    alter: float
    elm: str
    lyric_index: int | None
    spacer: bool
    breve: bool
    stemless: bool
    slur_start: bool
    slur_stop: bool
    extend: bool
    rest: bool


def _q(value: float) -> float:
    return round(value, 4)


def _diatonic(step: str, octave: int) -> int:
    return octave * 7 + _STEPS.index(step)


def _elm_quarters(elm: str) -> float:
    try:
        return _ELM_QUARTERS[elm]
    except KeyError as exc:
        raise ValueError(f"Score-IR-SVG-spike: onbekende ELM {elm!r}") from exc


def _lyric_text(lyric: dict[str, Any]) -> str:
    return "".join(str(s.get("text", "")) for s in lyric.get("syllables") or [])


def _layer_text(lyric: dict[str, Any], number: str) -> str:
    layers = lyric.get("layers") or {}
    parts = layers.get(number) or layers.get(int(number) if number.isdigit() else number) or []
    return "".join(str(part) for part in parts)


def _text_width(text: str, pt: float = LYRIC_PT) -> float:
    px = pt * _PT
    return max(12.0, len(text) * px * 0.50)


def _f_major(doc: dict[str, Any]) -> bool:
    ctx = doc.get("pitchContext") or {}
    do = str(ctx.get("do") or "")
    return do.upper().startswith("F") and ctx.get("mode") == "major"


def _events_for_voice(raw: list[dict[str, Any]], voice: str) -> list[Ev]:
    out: list[Ev] = []
    cursor = 0.0
    for index, ev in enumerate(raw):
        if isinstance(ev.get("sourceIndex"), int):
            index = ev["sourceIndex"]
        elm = str((ev.get("duration") or {}).get("elm") or "~")
        dur = _elm_quarters(elm)
        pitch = ev.get("pitch")
        step: str | None = None
        octave: int | None = None
        alter = 0.0
        rest = bool(ev.get("rest")) or pitch is None or pitch == "hold"
        if isinstance(pitch, dict):
            rest = False
            step = str(pitch.get("step") or "C")
            octave = int(pitch.get("octave") or 4)
            alter = float(pitch.get("alter") or 0)
        printed = ev.get("print") or {}
        melisma = ev.get("melisma") or {}
        out.append(
            Ev(
                voice=voice,
                index=index,
                start=_q(cursor),
                end=_q(cursor + dur),
                step=step,
                octave=octave,
                alter=alter,
                elm=elm,
                lyric_index=ev.get("lyricIndex") if isinstance(ev.get("lyricIndex"), int) else None,
                spacer=bool(printed.get("spacer")),
                breve=bool(printed.get("breveHead")),
                stemless=bool(printed.get("stemless")),
                slur_start=bool(melisma.get("slurStart")),
                slur_stop=bool(melisma.get("slurStop")),
                extend=bool(melisma.get("extend")),
                rest=rest,
            )
        )
        cursor += dur
    return out


def _pitch_y(staff_bottom: float, bottom_diatonic: int, step: str, octave: int) -> tuple[float, int]:
    pos = _diatonic(step, octave) - bottom_diatonic
    return staff_bottom - pos * (SP / 2.0), pos


def _ledger_positions(pos: int) -> list[int]:
    lines: list[int] = []
    if pos <= -2:
        k = -2
        while k >= pos:
            lines.append(k)
            k -= 2
    if pos >= 10:
        k = 10
        while k <= pos:
            lines.append(k)
            k += 2
    return lines


def _note_open(elm: str) -> bool:
    return elm.startswith("_")


def _whole(elm: str) -> bool:
    return elm.startswith("__")


def _dots(elm: str) -> int:
    # ``.`` / ``..`` zijn achtste en zestiende, geen stip.
    if set(elm) <= {"."}:
        return 0
    return elm.count(".")


class _Svg:
    def __init__(self) -> None:
        self.parts: list[str] = []

    def add(self, fragment: str) -> None:
        self.parts.append(fragment)


def _lyric_width(ev: Ev, lyrics: list[dict[str, Any]]) -> float:
    if ev.lyric_index is None or not 0 <= ev.lyric_index < len(lyrics):
        return 0.0
    return _text_width(_lyric_text(lyrics[ev.lyric_index]))


def _column_gap(starters: list[Ev]) -> float:
    """Kleinste hartafstand van nootkoppen. Achtsten blijven zoals ze goed stonden."""
    sounding = [ev for ev in starters if not ev.rest and not ev.spacer]
    if not sounding:
        return 0.0
    if any(_whole(ev.elm) or ev.breve or _note_open(ev.elm) for ev in sounding):
        return 26.0
    if all(_elm_quarters(ev.elm) <= 0.5 for ev in sounding):
        return 18.0
    return 22.0


def _layout_times(voices: dict[str, list[Ev]], lyrics: list[dict[str, Any]], x0: float) -> dict[float, float]:
    """Hart van de noot per starttijd. Lettergrepen krijgen een klein gat, geen maat-rek."""
    starts = sorted({ev.start for evs in voices.values() for ev in evs})
    x_at: dict[float, float] = {}
    prev_x: float | None = None
    prev_right: float | None = None
    for t0 in starts:
        starters = [ev for evs in voices.values() for ev in evs if ev.start == t0]
        lyric_w = max((_lyric_width(ev, lyrics) for ev in starters), default=0.0)
        if prev_x is None:
            x = x0 + max(10.0, lyric_w / 2.0)
        else:
            x = prev_x + _column_gap(starters)
            if lyric_w and prev_right is not None:
                x = max(x, prev_right + LYRIC_GAP + lyric_w / 2.0)
        x_at[t0] = x
        prev_x = x
        if lyric_w:
            prev_right = x + lyric_w / 2.0
    return x_at


def _content_right(voices: dict[str, list[Ev]], lyrics: list[dict[str, Any]], x_at: dict[float, float]) -> float:
    right = max(x_at.values(), default=0.0)
    for evs in voices.values():
        for ev in evs:
            cx = x_at.get(ev.start)
            if cx is None:
                continue
            hang = max(12.0, _lyric_width(ev, lyrics) / 2.0 + 3.0)
            right = max(right, cx + hang)
    return right


def _cx(x_at: dict[float, float], ev: Ev) -> float:
    return x_at[ev.start]


def _font_css() -> str:
    """Source Sans 3 in het SVG, zodat de plaat niet van een geïnstalleerd font afhangt."""
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "scripts" / "osmd-svg" / "fonts" / "source-sans-3-400.woff2",
        Path.cwd() / "scripts" / "osmd-svg" / "fonts" / "source-sans-3-400.woff2",
    ]
    font = next((p for p in candidates if p.is_file()), None)
    if font is None:
        return ""
    payload = base64.b64encode(font.read_bytes()).decode("ascii")
    return (
        "<defs><style><![CDATA["
        "@font-face{"
        f"font-family:'{FONT_FAMILY}';"
        "font-style:normal;"
        "font-weight:400;"
        f"src:url(data:font/woff2;base64,{payload}) format('woff2');"
        "}"
        "]]></style></defs>"
    )


def _voice_map(measure: dict[str, Any]) -> dict[str, list[Ev]]:
    return {
        letter: _events_for_voice(list((measure.get("voices") or {}).get(letter) or []), letter)
        for letter in ("S", "A", "T", "B")
    }


def _bar_tail(style: str) -> float:
    if style in {"repeat-end", "repeat-end-section", "light-heavy", "light-light", "heavy-heavy"}:
        return 18.0
    return 0.0


def _measure_end(measure: dict[str, Any], x: float) -> tuple[dict[str, list[Ev]], dict[float, float], float, float]:
    """Stemmen, x per tijd, x van de eerste noot, x van de rechterstreep."""
    lyrics = list(measure.get("lyrics") or [])
    voices = _voice_map(measure)
    left_style = str((measure.get("bar") or {}).get("left") or "")
    origin = x + (36.0 if left_style in {"repeat-start", "heavy-light", "heavy-heavy"} else 0.0)
    x_at = _layout_times(voices, lyrics, origin)
    right_style = str((measure.get("bar") or {}).get("right") or "")
    end_x = _content_right(voices, lyrics, x_at) + _bar_tail(right_style)
    if not measure.get("_continuation"):
        cue_w = max((_text_width(line, CUE_PT) for line in _cue_lines(measure)), default=0.0)
        if cue_w:
            end_x = max(end_x, origin + cue_w + 14.0)
    return voices, x_at, origin, end_x


def _slice_voice(raw: list[dict[str, Any]], t0: float, t1: float) -> list[dict[str, Any]]:
    cursor = 0.0
    kept: list[dict[str, Any]] = []
    for index, ev in enumerate(raw):
        elm = str((ev.get("duration") or {}).get("elm") or "~")
        start = _q(cursor)
        if t0 - 1e-4 <= start < t1 - 1e-4:
            copy = dict(ev)
            copy["sourceIndex"] = index
            kept.append(copy)
        cursor += _elm_quarters(elm)
    return kept


def _slice_measure(measure: dict[str, Any], t0: float, t1: float, *, first: bool, last: bool) -> dict[str, Any]:
    sl: dict[str, Any] = {
        "id": measure.get("id"),
        "lyrics": list(measure.get("lyrics") or []),
        "voices": {
            letter: _slice_voice(list(events), t0, t1)
            for letter, events in (measure.get("voices") or {}).items()
        },
        "bar": {
            "left": (measure.get("bar") or {}).get("left") if first else None,
            "right": (measure.get("bar") or {}).get("right") if last else None,
        },
    }
    if first:
        if measure.get("cues"):
            sl["cues"] = measure["cues"]
        if measure.get("navigation"):
            sl["navigation"] = measure["navigation"]
        if measure.get("newSystem"):
            sl["newSystem"] = True
    else:
        sl["_continuation"] = True
    ending = dict(measure.get("ending") or {})
    if not first:
        ending.pop("start", None)
    if not last:
        ending.pop("stop", None)
    if ending:
        sl["ending"] = ending
    return sl


def _cut_times(measure: dict[str, Any], budget: float) -> list[tuple[float, float]]:
    """Knippunten zodat elk stuk binnen ``budget`` blijft. Liever op een lettergreep."""
    voices = _voice_map(measure)
    lyrics = list(measure.get("lyrics") or [])
    x_at = _layout_times(voices, lyrics, 0.0)
    sop = voices.get("S") or []
    if not sop:
        return [(0.0, 1.0e9)]
    total = max((ev.end for evs in voices.values() for ev in evs), default=0.0)
    if _content_right(voices, lyrics, x_at) <= budget:
        return [(0.0, total + 1.0)]
    cuts: list[tuple[float, float]] = []
    t0 = 0.0
    guard = 0
    while t0 < total - 1e-4 and guard < 64:
        guard += 1
        x0 = x_at.get(_q(t0), 0.0)
        best: float | None = None
        overflow: float | None = None
        for ev in sop:
            if ev.start <= t0 + 1e-4:
                continue
            x = x_at.get(ev.start, x0)
            if x - x0 <= budget:
                if ev.lyric_index is not None:
                    best = ev.start
            else:
                overflow = ev.start
                break
        if overflow is None:
            cuts.append((t0, total + 1.0))
            break
        cut = best if best is not None and best > t0 + 1e-4 else overflow
        if cut <= t0 + 1e-4:
            cut = overflow
        cuts.append((t0, cut))
        t0 = cut
    if not cuts or cuts[-1][1] <= total:
        cuts.append((t0, total + 1.0))
    return cuts


def _systems(
    measures: list[dict[str, Any]],
    *,
    system_width: float | None,
    show_music: bool,
    f_major: bool,
) -> list[list[tuple[int, dict[str, Any]]]]:
    prefix = 36.0 + (54.0 if show_music else 8.0)
    if show_music and f_major:
        prefix += 22.0
    groups: list[list[tuple[int, dict[str, Any]]]] = []
    current: list[tuple[int, dict[str, Any]]] = []
    used = prefix

    def flush() -> None:
        nonlocal current, used
        if current:
            groups.append(current)
            current = []
            used = prefix

    for index, measure in enumerate(measures):
        if system_width is None:
            slices = [measure]
        else:
            budget = max(180.0, system_width - prefix)
            spans = _cut_times(measure, budget)
            if len(spans) == 1:
                slices = [measure]
            else:
                slices = [
                    _slice_measure(measure, t0, t1, first=si == 0, last=si == len(spans) - 1)
                    for si, (t0, t1) in enumerate(spans)
                ]
        for si, sl in enumerate(slices):
            if measure.get("newSystem") and si == 0 and current:
                flush()
            if si > 0 and current:
                flush()
            span = _measure_end(sl, 0.0)[3] + MEASURE_GLUE
            if current and system_width is not None and used + span > system_width:
                flush()
            current.append((index, sl))
            used += span
    flush()
    return groups or [[]]


def render_score_ir_svg(
    doc: dict[str, Any],
    *,
    view: str = "notes",
    lyric_pt: float | None = None,
    cue_pt: float | None = None,
    system_width: float | None = DEFAULT_SYSTEM_WIDTH,
) -> str:
    """Teken Score-IR. ``view`` is ``notes``, ``vsa-notes`` of ``vsa``.

    ``system_width`` is de regelbreedte. ``None`` breekt alleen op
    ``@nieuw-systeem``.
    """
    global LYRIC_PT, CUE_PT, LYRIC_FONT
    if doc.get("format") != "score-ir":
        raise EigenSvgError("verwacht format score-ir")
    chosen = normalize_eigen_view(view)
    saved = (LYRIC_PT, CUE_PT, LYRIC_FONT)
    if lyric_pt is not None:
        LYRIC_PT = float(lyric_pt)
        LYRIC_FONT = LYRIC_PT * _PT
    if cue_pt is not None:
        CUE_PT = float(cue_pt)
    try:
        return _render_score_ir_svg(doc, chosen, system_width=system_width)
    finally:
        LYRIC_PT, CUE_PT, LYRIC_FONT = saved


def _render_score_ir_svg(
    doc: dict[str, Any],
    chosen: str,
    *,
    system_width: float | None,
) -> str:
    marks, underlines = soprano_vsa_plan(doc)
    chunks: list[str] = []
    width = 240.0
    y = 0.0
    gap = 22.0
    show_music = chosen != "vsa"
    groups = _systems(
        list(doc.get("measures") or []),
        system_width=system_width,
        show_music=show_music,
        f_major=_f_major(doc),
    )
    for group in groups:
        system_w, system_h, body = _render_system(
            doc,
            indexed=group,
            view=chosen,
            vsa_marks=marks,
            vsa_underlines=underlines,
        )
        chunks.append(f'<g class="system" transform="translate(0,{y:.1f})">{body}</g>')
        width = max(width, system_w)
        y += system_h + gap
    height = max(y - gap, 80.0)
    title = html.escape(str((doc.get("meta") or {}).get("title") or "partituur"))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" '
        f'width="{width:.0f}" height="{height:.0f}" '
        f'preserveAspectRatio="xMinYMin meet" role="img" data-view="{chosen}">\n'
        f"<title>{title}</title>\n"
        f"{_font_css()}\n"
        f'<rect class="page" x="0" y="0" width="{width:.1f}" height="{height:.1f}" fill="white"/>\n'
        + "\n".join(chunks)
        + "\n</svg>\n"
    )


def _render_system(
    doc: dict[str, Any],
    *,
    indexed: list[tuple[int, dict[str, Any]]],
    view: str,
    vsa_marks: list[tuple[int, int, str, str]],
    vsa_underlines: list[tuple[int, int, str]],
) -> tuple[float, float, str]:
    """Eén systeem. Kale VSA slaat de notenbalk over."""
    show_music = view != "vsa"
    show_vsa = view != "notes"
    f_major = _f_major(doc)
    svg = _Svg()
    glyphs = SVGGlyphRenderer(unit=max(6.0, LYRIC_PT * 0.40))

    if show_music:
        treble_bottom = 76.0
        lyric_y = treble_bottom + 70.0
        bass_bottom = lyric_y + 56.0 + 4.0 * SP
        height = bass_bottom + 2.0 * SP + 16.0
    else:
        treble_bottom = 48.0
        lyric_y = 72.0
        bass_bottom = lyric_y
        height = lyric_y + 40.0
    staff_bottom = {"treble": treble_bottom, "bass": bass_bottom}
    bottom_dia = {"treble": _diatonic("E", 4), "bass": _diatonic("G", 2)}

    measures = [measure for _index, measure in indexed]
    measure_ids = [index for index, _measure in indexed]
    left = 36.0 if show_music else 16.0
    x = left + (54.0 if show_music else 8.0)
    if show_music and f_major:
        x += 22.0
    end_x = x

    prepared: list[tuple[dict[str, Any], dict[str, list[Ev]], dict[float, float], float, float]] = []
    for measure in measures:
        voices, x_at, origin, end_x = _measure_end(measure, x)
        prepared.append((measure, voices, x_at, origin, end_x))
        x = end_x + MEASURE_GLUE

    width = max(end_x + 24.0, 240.0)
    if show_music:
        _draw_brace(svg, left - 4.0, treble_bottom - 4 * SP, bass_bottom)
        for staff, bottom in staff_bottom.items():
            for line in range(5):
                y = bottom - line * SP
                svg.add(
                    f'<line class="staff" data-staff="{staff}" x1="{left:.1f}" y1="{y:.1f}" '
                    f'x2="{end_x:.1f}" y2="{y:.1f}" stroke="black" stroke-width="1"/>'
                )
        _draw_clefs_and_signature(svg, left, treble_bottom, bass_bottom, f_major)
        if measures and not measures[0].get("_continuation"):
            number = measure_ids[0] + 1
            svg.add(
                f'<text class="measure-number" data-number="{number}" x="8" y="{treble_bottom - 2 * SP:.1f}" '
                f'font-family="{FONT_FAMILY}, sans-serif" font-size="12pt" font-weight="400">{number}</text>'
            )

    volta_boxes: list[tuple[dict[str, Any], float, float]] = []
    ink_top = 12.0
    for local_i, (measure, voices, x_at, measure_x, bar_x) in enumerate(prepared):
        measure_i = measure_ids[local_i]
        lyrics = list(measure.get("lyrics") or [])
        note_centers: dict[tuple[str, int], tuple[float, float]] = {}
        lyric_centers: dict[int, float] = {}
        left_style = str((measure.get("bar") or {}).get("left") or "")
        if show_music and left_style:
            _draw_barline(svg, left_style, measure_x - 34.0, treble_bottom, bass_bottom, staff_bottom)
        for letter, evs in voices.items():
            for ev in evs:
                cx = _cx(x_at, ev)
                if show_music and not ev.rest and ev.step is not None and ev.octave is not None:
                    cy, pos = _pitch_y(staff_bottom[_STAFF_OF[letter]], bottom_dia[_STAFF_OF[letter]], ev.step, ev.octave)
                    note_centers[(letter, ev.index)] = (cx, cy)
                    _draw_note(svg, ev, cx, cy, pos, f_major, lyric_y, draw_stem=False)
                elif not show_music and letter == "S":
                    note_centers[(letter, ev.index)] = (cx, lyric_y)
                if letter == "S" and ev.lyric_index is not None:
                    lyric_centers[ev.lyric_index] = cx
        if show_music:
            tips, stem_top = _draw_stems_and_beams(svg, voices, note_centers, lyric_y)
            slur_top = _draw_slurs(svg, voices, note_centers, tips)
            ink_top = min(ink_top, stem_top, slur_top, _cue_top(measure, treble_bottom))
            if (measure.get("ending") or {}).get("start"):
                ink_top = min(ink_top, treble_bottom - 4 * SP - 32.0)
            right_style = str((measure.get("bar") or {}).get("right") or "")
            if right_style:
                _draw_barline(
                    svg,
                    right_style,
                    bar_x,
                    treble_bottom,
                    bass_bottom,
                    staff_bottom,
                )
            _draw_navigation(svg, measure, measure_x, treble_bottom)
            volta_boxes.append((measure, measure_x, bar_x))
        _draw_cues(
            svg,
            measure,
            measure_x,
            treble_bottom if show_music else lyric_y + 4 * SP,
        )
        _draw_lyrics(
            svg,
            lyrics,
            lyric_centers,
            voices,
            note_centers,
            lyric_y,
            glyphs,
            vsa_marks,
            vsa_underlines,
            measure_i,
            show_vsa=show_vsa,
            show_extend=show_music,
        )

    if show_music:
        _draw_voltas(svg, volta_boxes, treble_bottom)
    body = "\n".join(svg.parts)
    pad = max(0.0, 4.0 - ink_top)
    if pad > 0.4:
        body = f'<g class="headroom" transform="translate(0,{pad:.1f})">{body}</g>'
        height += pad
    return width, height, body


def _draw_clefs_and_signature(
    svg: _Svg,
    left: float,
    treble_bottom: float,
    bass_bottom: float,
    f_major: bool,
) -> None:
    # G-sleutel: font-oorsprong op de g-lijn. F-sleutel: oorsprong op de f-lijn.
    g_y, _gpos = _pitch_y(treble_bottom, _diatonic("E", 4), "G", 4)
    f_y, _fpos = _pitch_y(bass_bottom, _diatonic("G", 2), "F", 3)
    svg.add(_paint_glyph("gClef", left + 2.0, g_y, "clef", center=False).replace(
        'class="clef"', 'class="clef" data-staff="treble"', 1
    ))
    svg.add(_paint_glyph("fClef", left + 2.0, f_y, "clef", center=False).replace(
        'class="clef"', 'class="clef" data-staff="bass"', 1
    ))
    if not f_major:
        return
    # F-groot: één mol op de b-lijn. Toon B met alter -1 krijgt dan geen tweede mol.
    for staff, bottom, dia, step, octave in (
        ("treble", treble_bottom, _diatonic("E", 4), "B", 4),
        ("bass", bass_bottom, _diatonic("G", 2), "B", 2),
    ):
        y, _pos = _pitch_y(bottom, dia, step, octave)
        # Rechterrand van de mol vlak voor de eerste nootkolom.
        _d, _x0, _y0, x1, _y1 = GLYPHS["accidentalFlat"]
        ox = left + 46.0 - x1 * GLYPH_SCALE
        svg.add(_paint_glyph("accidentalFlat", ox, y, "key-signature").replace(
            'class="key-signature"', f'class="key-signature" data-staff="{staff}"', 1
        ))


def _stem_end(cy: float, voice: str, lyric_y: float) -> float:
    """Stok stopt vóór de tekst, zodat slur en lettergreep vrij blijven."""
    reach = 3.0 * SP
    short = 2.0 * SP
    if voice in _STEM_UP:
        y2 = cy - reach
        if _STAFF_OF[voice] == "bass":
            # Niet door de lettergreep, ook als de noot dicht onder de tekst staat.
            y2 = max(y2, lyric_y + 12.0)
            return min(y2, cy - 8.0)
        return min(y2, cy - short)
    y2 = cy + reach
    if _STAFF_OF[voice] == "treble":
        y2 = min(y2, lyric_y - 28.0)
        return max(y2, cy + 8.0)
    return max(y2, cy + short)


def _draw_note(
    svg: _Svg,
    ev: Ev,
    cx: float,
    cy: float,
    pos: int,
    f_major: bool,
    lyric_y: float,
    *,
    draw_stem: bool = True,
) -> None:
    kind = "spacer" if ev.spacer else "breve" if ev.breve else "whole" if _whole(ev.elm) else "note"
    stem_dir = "up" if ev.voice in _STEM_UP else "down"
    svg.add(
        f'<g class="note voice-{ev.voice} {kind}" data-voice="{ev.voice}" '
        f'data-kind="{kind}" data-index="{ev.index}" '
        + (
            f'data-step="{ev.step}" data-octave="{ev.octave}" data-cy="{cy:.1f}" '
            if ev.step is not None and ev.octave is not None
            else ""
        )
        + (
            f'data-lyric-index="{ev.lyric_index}" '
            if ev.lyric_index is not None
            else ""
        )
        + ">"
    )
    if ev.spacer or ev.rest:
        svg.add("</g>")
        return
    for line_pos in _ledger_positions(pos):
        y = cy + (pos - line_pos) * (SP / 2.0)
        svg.add(
            f'<line class="ledger" x1="{cx - 11:.1f}" y1="{y:.1f}" x2="{cx + 11:.1f}" y2="{y:.1f}" '
            f'stroke="black" stroke-width="1"/>'
        )
    head = _head_name(ev)
    svg.add(_paint_glyph(head, cx, cy, "notehead breve-head" if ev.breve else "notehead", center=True))
    rx = _half_width(head)
    if draw_stem and not ev.breve and not ev.stemless and not _whole(ev.elm):
        y2 = _stem_end(cy, ev.voice, lyric_y)
        if stem_dir == "up":
            x = cx + rx - 0.8
            svg.add(
                f'<line class="stem stem-up voice-{ev.voice}" data-voice="{ev.voice}" '
                f'x1="{x:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="black" stroke-width="1.35"/>'
            )
        else:
            x = cx - rx + 0.8
            svg.add(
                f'<line class="stem stem-down voice-{ev.voice}" data-voice="{ev.voice}" '
                f'x1="{x:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="black" stroke-width="1.35"/>'
            )
    dot_y = cy - (SP / 4.0 if pos % 2 == 0 else 0.0)
    for dot in range(_dots(ev.elm)):
        dx = cx + rx + 7.0 + dot * 8.0
        svg.add(_paint_glyph("augmentationDot", dx, dot_y, "dot", center=True))
    if ev.alter and not (f_major and ev.step == "B" and ev.alter < 0):
        name = "accidentalSharp" if ev.alter > 0 else "accidentalFlat"
        _d, _x0, _y0, x1, _y1 = GLYPHS[name]
        right = cx - rx - 3.0
        svg.add(_paint_glyph(name, right - x1 * GLYPH_SCALE, cy, "accidental"))
    svg.add("</g>")


def _stem_x(ev: Ev, cx: float) -> float:
    rx = _half_width(_head_name(ev))
    if ev.voice in _STEM_UP:
        return cx + rx - 0.8
    return cx - rx + 0.8


def _short_level(ev: Ev) -> int:
    """1 = achtste, 2 = zestiende, 3 = korter. 0 = geen vlag of balk."""
    if ev.rest or ev.spacer or ev.stemless or ev.breve or _whole(ev.elm) or _note_open(ev.elm):
        return 0
    quarters = _elm_quarters(ev.elm)
    if quarters <= 0.125:
        return 3
    if quarters <= 0.25:
        return 2
    if quarters <= 0.5:
        return 1
    return 0


def _beam_groups(evs: list[Ev]) -> list[list[Ev]]:
    """Achtsten en korter, aaneengesloten, binnen dezelfde kwarttel."""
    groups: list[list[Ev]] = []
    current: list[Ev] = []
    beat: int | None = None
    for ev in evs:
        level = _short_level(ev)
        gap = current and abs(ev.start - current[-1].end) > 0.02
        if level == 0 or gap:
            if len(current) >= 2:
                groups.append(current)
            current = []
            beat = None
            if level == 0:
                continue
        ev_beat = math.floor(ev.start + 1e-4)
        if current and ev_beat != beat:
            if len(current) >= 2:
                groups.append(current)
            current = []
        if not current:
            beat = ev_beat
        current.append(ev)
    if len(current) >= 2:
        groups.append(current)
    return groups


def _draw_stem_line(svg: _Svg, ev: Ev, x: float, y1: float, y2: float) -> None:
    direction = "up" if ev.voice in _STEM_UP else "down"
    svg.add(
        f'<line class="stem stem-{direction} voice-{ev.voice}" data-voice="{ev.voice}" '
        f'data-index="{ev.index}" x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" '
        f'stroke="black" stroke-width="1.35"/>'
    )


def _draw_flag(svg: _Svg, ev: Ev, x: float, y: float) -> None:
    level = _short_level(ev)
    if level <= 0:
        return
    up = ev.voice in _STEM_UP
    if level >= 2:
        name = "flag16thUp" if up else "flag16thDown"
    else:
        name = "flag8thUp" if up else "flag8thDown"
    svg.add(_paint_glyph(name, x, y, "flag", center=False))


def _draw_stems_and_beams(
    svg: _Svg,
    voices: dict[str, list[Ev]],
    centers: dict[tuple[str, int], tuple[float, float]],
    lyric_y: float,
) -> tuple[dict[tuple[str, int], float], float]:
    """Stokken, balken en vlaggen. Geeft de stokpunt per noot en de hoogste inkt."""
    tips: dict[tuple[str, int], float] = {}
    ink_top = 10_000.0
    for letter, evs in voices.items():
        drawable = [
            ev
            for ev in evs
            if (letter, ev.index) in centers
            and not ev.spacer
            and not ev.rest
            and not ev.breve
            and not ev.stemless
            and not _whole(ev.elm)
        ]
        groups = _beam_groups(drawable)
        beamed = {ev.index for group in groups for ev in group}
        up = letter in _STEM_UP
        for ev in drawable:
            if ev.index in beamed:
                continue
            cx, cy = centers[(letter, ev.index)]
            x = _stem_x(ev, cx)
            y2 = _stem_end(cy, letter, lyric_y)
            _draw_stem_line(svg, ev, x, cy, y2)
            _draw_flag(svg, ev, x, y2)
            tips[(letter, ev.index)] = y2
            ink_top = min(ink_top, y2, cy)
        for group in groups:
            xs: list[float] = []
            preferred: list[float] = []
            for ev in group:
                cx, cy = centers[(letter, ev.index)]
                xs.append(_stem_x(ev, cx))
                preferred.append(_stem_end(cy, letter, lyric_y))
            x0 = xs[0]
            span = xs[-1] - x0
            cys = [centers[(letter, ev.index)][1] for ev in group]
            slope = 0.0
            if abs(span) > 1:
                slope = max(-0.18, min(0.18, (cys[-1] - cys[0]) / span))
            if up:
                y0 = min(tip - slope * (x - x0) for tip, x in zip(preferred, xs))
            else:
                y0 = max(tip - slope * (x - x0) for tip, x in zip(preferred, xs))

            def beam_y(x: float, shift: float = 0.0) -> float:
                return y0 + slope * (x - x0) + shift

            for ev, x, cy in zip(group, xs, cys):
                tip = beam_y(x)
                _draw_stem_line(svg, ev, x, cy, tip)
                tips[(letter, ev.index)] = tip
                ink_top = min(ink_top, tip)
            _beam_segments(svg, group, xs, beam_y, level=1, shift=0.0, voice=letter)
            if any(_short_level(ev) >= 2 for ev in group):
                shift = BEAM_SHIFT if up else -BEAM_SHIFT
                _beam_segments(svg, group, xs, beam_y, level=2, shift=shift, voice=letter)
                if shift < 0:
                    ink_top = min(ink_top, beam_y(xs[0], shift), beam_y(xs[-1], shift))
    return tips, ink_top


def _beam_segments(
    svg: _Svg,
    group: list[Ev],
    xs: list[float],
    beam_y,
    *,
    level: int,
    shift: float,
    voice: str,
) -> None:
    """Eén balklaag. Een losse korte noot krijgt een stompje naar de buur."""
    n = len(group)
    i = 0
    while i < n:
        if _short_level(group[i]) < level:
            i += 1
            continue
        j = i
        while j + 1 < n and _short_level(group[j + 1]) >= level:
            j += 1
        if j > i:
            x1, x2 = xs[i], xs[j]
            svg.add(
                f'<line class="beam" data-voice="{voice}" data-level="{level}" x1="{x1:.1f}" y1="{beam_y(x1, shift):.1f}" '
                f'x2="{x2:.1f}" y2="{beam_y(x2, shift):.1f}" stroke="black" stroke-width="{BEAM_WIDTH:.1f}" '
                f'stroke-linecap="butt"/>'
            )
        else:
            neighbor = xs[i + 1] if i + 1 < n else xs[i - 1]
            step = 12.0 if neighbor > xs[i] else -12.0
            x1 = xs[i]
            x2 = xs[i] + step
            svg.add(
                f'<line class="beam" data-voice="{voice}" data-level="{level}" x1="{x1:.1f}" y1="{beam_y(x1, shift):.1f}" '
                f'x2="{x2:.1f}" y2="{beam_y(x2, shift):.1f}" stroke="black" stroke-width="{BEAM_WIDTH:.1f}" '
                f'stroke-linecap="butt"/>'
            )
        i = j + 1


def _slur_anchor(
    letter: str,
    index: int,
    centers: dict[tuple[str, int], tuple[float, float]],
    tips: dict[tuple[str, int], float],
    *,
    up: bool,
) -> tuple[float, float] | None:
    """Stokpunt, of net boven/onder de nootkop als er geen stok is."""
    center = centers.get((letter, index))
    if center is None:
        return None
    cx, cy = center
    tip = tips.get((letter, index))
    clearance = 3.0
    if tip is None:
        return cx, cy - SP * 0.7 if up else cy + SP * 0.7
    return cx, tip - clearance if up else tip + clearance


def _one_slur(x1: float, y1: float, x2: float, y2: float, *, up: bool) -> tuple[str, float]:
    """Eén kwadratische boog. De top blijft laag, zodat het systeem niet groeit."""
    span = abs(x2 - x1)
    peak = min(9.0, max(4.0, span * 0.08))
    # Op t=0,5 ligt de kromme halverwege het controlepunt en de koorde.
    lift = peak * 2.0
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0 + (-lift if up else lift)
    path = f"M {x1:.1f} {y1:.1f} Q {cx:.1f} {cy:.1f} {x2:.1f} {y2:.1f}"
    top = min(y1, y2, cy) if up else min(y1, y2)
    return path, top


def _draw_slurs(
    svg: _Svg,
    voices: dict[str, list[Ev]],
    centers: dict[tuple[str, int], tuple[float, float]],
    tips: dict[tuple[str, int], float],
) -> float:
    """Van de eerste stok naar de laatste stok. Eén boog, geen knik per noot."""
    ink_top = 10_000.0
    for letter, evs in voices.items():
        starts = [ev.index for ev in evs if ev.slur_start]
        stops = [ev.index for ev in evs if ev.slur_stop]
        up = letter in _STEM_UP
        for start, stop in zip(starts, stops):
            if stop <= start:
                continue
            present = [
                i
                for i in range(start, stop + 1)
                if (letter, i) in centers
            ]
            if len(present) < 2:
                continue
            a = _slur_anchor(letter, present[0], centers, tips, up=up)
            b = _slur_anchor(letter, present[-1], centers, tips, up=up)
            if a is None or b is None:
                continue
            path, top = _one_slur(a[0], a[1], b[0], b[1], up=up)
            svg.add(
                f'<path class="melisma-slur" data-voice="{letter}" data-from="{start}" data-to="{stop}" '
                f'd="{path}" fill="none" stroke="black" stroke-width="1.3"/>'
            )
            ink_top = min(ink_top, top)
    return ink_top


def _draw_brace(svg: _Svg, x_right: float, y_top: float, y_bottom: float) -> None:
    """Bravura-accolade, opgerekt over de twee balken.

    Het teken is één balk hoog. De breedte blijft ongeveer 16 px, anders
    wordt de streep een haarlijn als je hem over de tekst heen trekt.
    """
    d, x0, y0, x1, y1 = GLYPHS["brace"]
    target_h = max(1.0, y_bottom - y_top)
    sy = target_h / (y1 - y0)
    sx = 16.0 / max(1.0, x1 - x0)
    ox = x_right - x1 * sx
    oy = y_top + y1 * sy
    svg.add(
        f'<path class="brace" d="{d}" fill="black" fill-rule="nonzero" '
        f'transform="translate({ox:.2f},{oy:.2f}) scale({sx:.5f},{-sy:.5f})"/>'
    )


def _bar_strokes(style: str) -> list[tuple[float, float]]:
    """Afstand vanaf het anker, en lijndikte. Enkele streep is één dunne lijn."""
    thin, thick, gap = 1.35, 3.8, 5.2
    if style in {"repeat-end", "repeat-end-section", "light-heavy"}:
        return [(0.0, thin), (gap, thick)]
    if style in {"repeat-start", "heavy-light"}:
        return [(0.0, thick), (gap, thin)]
    if style == "light-light":
        return [(0.0, thin), (gap, thin)]
    if style == "heavy-heavy":
        return [(0.0, thick), (gap, thick)]
    return [(0.0, thin)]


def _draw_barline(
    svg: _Svg,
    style: str,
    x: float,
    treble_bottom: float,
    bass_bottom: float,
    staff_bottom: dict[str, float],
) -> None:
    y1 = treble_bottom - 4 * SP
    y2 = bass_bottom
    for offset, stroke in _bar_strokes(style):
        bx = x + offset
        svg.add(
            f'<line class="barline" data-style="{html.escape(style)}" x1="{bx:.1f}" y1="{y1:.1f}" '
            f'x2="{bx:.1f}" y2="{y2:.1f}" stroke="black" stroke-width="{stroke:.2f}"/>'
        )
    if style in {"repeat-start", "heavy-light"}:
        dot_x = x + 5.2 + 12.0
    elif style in {"repeat-end", "repeat-end-section"}:
        dot_x = x - 12.0
    else:
        return
    for bottom in staff_bottom.values():
        mid = bottom - 2 * SP
        svg.add(_paint_glyph("repeatDots", dot_x, mid, "repeat-dots", center=True))


def _cue_lines(measure: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for cue in measure.get("cues") or []:
        for line in str(cue.get("text") or "").splitlines():
            text = line.strip()
            if text:
                lines.append(text)
    return lines


def _cue_top(measure: dict[str, Any], treble_bottom: float) -> float:
    """Bovenkant van de hoogste priesterregel, of ver onder de rand als er geen is."""
    lines = _cue_lines(measure)
    if not lines:
        return 10_000.0
    step = CUE_PT * _PT + 2.0
    baseline = treble_bottom - 4 * SP - 8.0 - step * (len(lines) - 1)
    return baseline - CUE_PT * _PT * 0.8


def _draw_cues(svg: _Svg, measure: dict[str, Any], x: float, treble_bottom: float) -> None:
    lines = _cue_lines(measure)
    step = CUE_PT * _PT + 2.0
    y = treble_bottom - 4 * SP - 8.0 - step * (len(lines) - 1)
    face = f'font-family="{FONT_FAMILY}, sans-serif" font-size="{CUE_PT:.0f}pt" font-weight="{LYRIC_WEIGHT}"'
    for text in lines:
        svg.add(
            f'<text class="cue" x="{x:.1f}" y="{y:.1f}" {face}>{html.escape(text)}</text>'
        )
        y += step


def _draw_navigation(
    svg: _Svg,
    measure: dict[str, Any],
    x: float,
    treble_bottom: float,
) -> None:
    labels = [
        _NAV_LABEL.get(str(key), str(key))
        for key in (measure.get("navigation") or [])
    ]
    if not labels:
        return
    y = treble_bottom - 4 * SP - 40.0
    face = f'font-family="{FONT_FAMILY}, sans-serif" font-size="12pt" font-weight="{LYRIC_WEIGHT}"'
    svg.add(
        f'<text class="nav-mark" x="{x:.1f}" y="{y:.1f}" {face}>{html.escape("  ".join(labels))}</text>'
    )


def _draw_voltas(
    svg: _Svg,
    boxes: list[tuple[dict[str, Any], float, float]],
    treble_bottom: float,
) -> None:
    """Haak boven de sopraan-alt-balk, over de maten van het slot."""
    y = treble_bottom - 4 * SP - 16.0
    index = 0
    while index < len(boxes):
        measure, left, right = boxes[index]
        ending = measure.get("ending") or {}
        if not ending.get("start") and not ending.get("stop"):
            index += 1
            continue
        number = str(ending.get("start") or "")
        last = index
        while last + 1 < len(boxes):
            this = boxes[last][0].get("ending") or {}
            nxt = boxes[last + 1][0].get("ending") or {}
            if this.get("stop") or not nxt:
                break
            if nxt.get("start") and nxt.get("start") != number:
                break
            last += 1
            if (boxes[last][0].get("ending") or {}).get("stop"):
                break
        x2 = boxes[last][2]
        hook = 9.0
        svg.add(
            f'<path class="volta" data-number="{html.escape(number)}" '
            f'd="M {left:.1f} {y + hook:.1f} V {y:.1f} H {x2:.1f} V {y + hook:.1f}" '
            f'fill="none" stroke="black" stroke-width="1.1"/>'
        )
        if number:
            face = f'font-family="{FONT_FAMILY}, sans-serif" font-size="12pt" font-weight="{LYRIC_WEIGHT}"'
            svg.add(
                f'<text class="volta-number" x="{left + 4:.1f}" y="{y - 3:.1f}" {face}>'
                f'{html.escape(number)}</text>'
            )
        index = last + 1


def _draw_lyrics(
    svg: _Svg,
    lyrics: list[dict[str, Any]],
    centers: dict[int, float],
    voices: dict[str, list[Ev]],
    note_centers: dict[tuple[str, int], tuple[float, float]],
    lyric_y: float,
    glyphs: SVGGlyphRenderer,
    vsa_marks: list[tuple[int, int, str, str]],
    vsa_underlines: list[tuple[int, int, str]],
    measure_i: int,
    *,
    show_vsa: bool,
    show_extend: bool,
) -> None:
    face = (
        f'font-family="{FONT_FAMILY}, sans-serif" font-size="{LYRIC_PT:.0f}pt" '
        f'font-weight="{LYRIC_WEIGHT}"'
    )
    sop = voices.get("S") or []
    for index, lyric in enumerate(lyrics):
        if index not in centers:
            continue
        text = _lyric_text(lyric)
        cx = centers[index]
        ev = next((e for e in sop if e.lyric_index == index), None)
        kind = "lyric spacer-lyric" if ev is not None and ev.spacer else "lyric"
        svg.add(
            f'<text class="{kind}" data-lyric-index="{index}" x="{cx:.1f}" y="{lyric_y:.1f}" '
            f'text-anchor="middle" {face}>{html.escape(text)}</text>'
        )
        second = _layer_text(lyric, "2")
        if second:
            svg.add(
                f'<text class="lyric-translit" data-lyric-index="{index}" x="{cx:.1f}" '
                f'y="{lyric_y + 18:.1f}" text-anchor="middle" {face}>{html.escape(second)}</text>'
            )
    for index, lyric in enumerate(lyrics[:-1]):
        syll = str((lyric.get("syllables") or [{}])[0].get("syllabic") or "")
        nxt = str((lyrics[index + 1].get("syllables") or [{}])[0].get("syllabic") or "")
        if syll in {"begin", "middle"} and nxt in {"middle", "end"} and index in centers and index + 1 in centers:
            hx = (centers[index] + centers[index + 1]) / 2.0
            svg.add(
                f'<text class="hyphen" x="{hx:.1f}" y="{lyric_y:.1f}" text-anchor="middle" {face}>-</text>'
            )
        elif (
            syll in {"begin", "middle"}
            and nxt in {"middle", "end"}
            and index in centers
            and index + 1 not in centers
        ):
            hx = centers[index] + _text_width(_lyric_text(lyric)) / 2.0 + 8.0
            svg.add(
                f'<text class="hyphen" x="{hx:.1f}" y="{lyric_y:.1f}" text-anchor="middle" {face}>-</text>'
            )
    if show_extend:
        _draw_extenders(svg, sop, lyrics, note_centers, lyric_y)
    if show_vsa:
        _draw_soprano_vsa(svg, glyphs, note_centers, lyric_y, vsa_marks, vsa_underlines, measure_i)


def _draw_extenders(
    svg: _Svg,
    sop: list[Ev],
    lyrics: list[dict[str, Any]],
    note_centers: dict[tuple[str, int], tuple[float, float]],
    lyric_y: float,
) -> None:
    """S13: streep onder de lettergreep tot de laatste noot van die greep."""
    index = 0
    while index < len(sop):
        start = sop[index]
        if start.lyric_index is None:
            index += 1
            continue
        group = [start]
        nxt = index + 1
        while nxt < len(sop) and sop[nxt].lyric_index is None:
            group.append(sop[nxt])
            nxt += 1
        index = nxt
        if not any(event.extend for event in group) or len(group) < 2:
            continue
        first = note_centers.get(("S", group[0].index))
        last = note_centers.get(("S", group[-1].index))
        if first is None or last is None or last[0] <= first[0] + 8:
            continue
        lyric = lyrics[start.lyric_index] if start.lyric_index < len(lyrics) else {}
        x1 = first[0] + _text_width(_lyric_text(lyric)) / 2.0 + 4.0
        x2 = last[0] + 6.0
        if x2 <= x1:
            continue
        y = lyric_y - 5.0
        svg.add(
            f'<line class="melisma-extend" data-index="{group[0].index}" '
            f'x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" '
            f'stroke="black" stroke-width="1"/>'
        )


def _draw_soprano_vsa(
    svg: _Svg,
    glyphs: SVGGlyphRenderer,
    note_centers: dict[tuple[str, int], tuple[float, float]],
    lyric_y: float,
    vsa_marks: list[tuple[int, int, str, str]],
    vsa_underlines: list[tuple[int, int, str]],
    measure_i: int,
) -> None:
    """Hoogtestrepen boven de noot, onderstreping eronder. Alleen de sopraan."""
    width = 16.0
    # Zelfde verhouding als de kale VSA: accent op één em boven de regel
    # (offset −20 bij corps 20), onderstreping op een kwart em eronder.
    em = LYRIC_PT * _PT
    y = lyric_y - em
    for mark_measure, index, token, glyph in vsa_marks:
        if mark_measure != measure_i:
            continue
        center = note_centers.get(("S", index))
        if center is None:
            continue
        x = center[0] - width / 2.0
        svg.add(
            f'<g class="vsa-mark" data-voice="S" data-index="{index}" '
            f'data-ehm="{html.escape(token, quote=True)}">'
        )
        for fragment in glyphs.render_height_modifier([glyph], x, y, width):
            svg.add(fragment)
        svg.add("</g>")
    for mark_measure, index, elm in vsa_underlines:
        if mark_measure != measure_i:
            continue
        center = note_centers.get(("S", index))
        if center is None:
            continue
        x = center[0] - width / 2.0
        svg.add(
            f'<g class="vsa-underline" data-voice="S" data-index="{index}" '
            f'data-elm="{html.escape(elm, quote=True)}">'
        )
        for fragment in glyphs.render_length_modifier([elm], x, lyric_y + em * 0.25, width):
            svg.add(fragment)
        svg.add("</g>")


def eigen_svg_suffix(
    view: str,
    *,
    translit: bool = False,
    translit_modus: str | None = None,
) -> str:
    """Bestandsstuk naast ``lied.mvsa``: ``.eigen-notes.svg`` enzovoort."""
    chosen = normalize_eigen_view(view)
    extra = ""
    if translit:
        from .derived_path import translit_svg_doel_suffix

        extra = translit_svg_doel_suffix(translit_modus).removesuffix(".svg")
    return f".eigen-{chosen}{extra}.svg"


def export_mvsa_to_eigen_svg(
    path: Path,
    out: Path,
    *,
    view: str = "notes",
    section_id: str | None = None,
    bibliotheek_id: str | None = None,
    translit: bool = False,
    translit_modus: str | None = None,
    lyric_pt: float | None = None,
    cue_pt: float | None = None,
    system_width: float | None = DEFAULT_SYSTEM_WIDTH,
) -> Path:
    """``.mvsa`` → Score-IR → eigen SVG. Schrijft ``out`` en geeft dat pad terug."""
    from .atomic_io import write_text
    from .score_ir import export_mvsa_to_score_ir

    path = Path(path)
    text = path.read_text(encoding="utf-8")
    doc = export_mvsa_to_score_ir(
        text,
        title=path.stem,
        section_id=section_id,
        source_path=path,
        bibliotheek_id=bibliotheek_id,
        translit=translit,
        translit_modus=translit_modus,
    )
    svg = render_score_ir_svg(
        doc,
        view=view,
        lyric_pt=lyric_pt,
        cue_pt=cue_pt,
        system_width=system_width,
    )
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_text(out, svg, encoding="utf-8", newline="\n")
    return out

