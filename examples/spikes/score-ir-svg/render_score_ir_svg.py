"""Spike: Score-IR (partituur) → eigen SVG.

Eén systeem, twee balken. Bewust klein: geen OSMD, geen MuseScore, geen
product-CLI. Contracten die deze tekening laat zien:

- S4  stok S/T omhoog, A/B omlaag
- S8  recite 1–(n−2)–1: randnoten, stokloze ||O||, spacers alleen als tekst
- S13 melisma: lyric + extender; bij toonwissel een slur alleen over die noten
- VSA-hoogtestrepen van de sopraanlijn (echte beweging, geen losse overlay)

Het SVG heeft een viewBox en width="100%" zodat het in een venster meeschaalt.
"""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vsa.music import Pitch
from vsa.mvsa_normalize import format_ehm
from vsa.pitch_resolver import _SCALE_INTERVALS, pitch_to_degree_and_chrom
from vsa.svg_glyphs import SVGGlyphRenderer

_GLYPH_SPEC = importlib.util.spec_from_file_location(
    "score_ir_svg_bravura_glyphs",
    Path(__file__).with_name("bravura_glyphs.py"),
)
assert _GLYPH_SPEC and _GLYPH_SPEC.loader
_bravura = importlib.util.module_from_spec(_GLYPH_SPEC)
sys.modules[_GLYPH_SPEC.name] = _bravura
_GLYPH_SPEC.loader.exec_module(_bravura)
GLYPHS: dict[str, tuple[str, float, float, float, float]] = _bravura.GLYPHS
STAFF_UNITS = _bravura.STAFF_UNITS

SP = 12.0
PX_QUARTER = 36.0
LYRIC_FONT = 18.0
# Bravura: één staff space = 250 font-eenheden.
GLYPH_SCALE = SP / STAFF_UNITS


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


def soprano_vsa_tokens(doc: dict[str, Any]) -> list[tuple[int, str, str]]:
    """Echte VSA-beweging van de sopraan: (event-index, mvsa-token, glyph).

    Eerste noot en elke gelijkblijvende toon krijgen een liggende streep (``-``).
    """
    ctx = doc.get("pitchContext") or {}
    do = _parse_do(str(ctx.get("do") or "F4"))
    mode = str(ctx.get("mode") or "major")
    intervals = _SCALE_INTERVALS.get(mode, _SCALE_INTERVALS["major"])
    prev: int | None = None
    out: list[tuple[int, str, str]] = []
    for measure in doc.get("measures") or []:
        events = _events_for_voice(list((measure.get("voices") or {}).get("S") or []), "S")
        for ev in events:
            if ev.step is None or ev.octave is None:
                continue
            pitch = Pitch(step=ev.step, octave=ev.octave, alter=ev.alter)
            degree, _chrom = pitch_to_degree_and_chrom(do, pitch, intervals)
            token = "-" if prev is None else format_ehm(prev, pitch, do, intervals)
            prev = degree
            out.append((ev.index, token, _ehm_glyph(token)))
    return out


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


def _text_width(text: str) -> float:
    return max(12.0, len(text) * LYRIC_FONT * 0.52)


def _f_major(doc: dict[str, Any]) -> bool:
    ctx = doc.get("pitchContext") or {}
    do = str(ctx.get("do") or "")
    return do.upper().startswith("F") and ctx.get("mode") == "major"


def _events_for_voice(raw: list[dict[str, Any]], voice: str) -> list[Ev]:
    out: list[Ev] = []
    cursor = 0.0
    for index, ev in enumerate(raw):
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


def _layout_times(voices: dict[str, list[Ev]], lyrics: list[dict[str, Any]], x0: float) -> dict[float, float]:
    times = {0.0}
    for evs in voices.values():
        for ev in evs:
            times.add(ev.start)
            times.add(ev.end)
    ordered = sorted(times)
    x_at = {ordered[0]: x0}
    x = x0
    for t0, t1 in zip(ordered, ordered[1:]):
        starters = [
            ev
            for evs in voices.values()
            for ev in evs
            if ev.start == _q(t0)
        ]
        active = [
            ev
            for evs in voices.values()
            for ev in evs
            if ev.start <= _q(t0) and ev.end > _q(t0)
        ]
        lyric_w = 0.0
        for ev in starters:
            if ev.lyric_index is not None and 0 <= ev.lyric_index < len(lyrics):
                lyric_w = max(lyric_w, _text_width(_lyric_text(lyrics[ev.lyric_index])) + 16.0)
        all_spacer = bool(active) and all(ev.spacer for ev in active)
        if all_spacer:
            width = max(lyric_w, 24.0)
        else:
            width = max((t1 - t0) * PX_QUARTER, lyric_w, 28.0)
            if any(ev.breve for ev in starters):
                width = max(width, 36.0)
        x += width
        x_at[_q(t1)] = x
    return x_at


def _cx(x_at: dict[float, float], ev: Ev, lyrics: list[dict[str, Any]]) -> float:
    lyric_w = 16.0
    if ev.lyric_index is not None and 0 <= ev.lyric_index < len(lyrics):
        lyric_w = _text_width(_lyric_text(lyrics[ev.lyric_index]))
    return x_at[ev.start] + max(14.0, lyric_w / 2.0)


def render_score_ir_svg(doc: dict[str, Any]) -> str:
    """Teken partituur-Score-IR als één SVG-systeem."""
    if doc.get("format") != "score-ir":
        raise ValueError("verwacht format score-ir")
    f_major = _f_major(doc)
    svg = _Svg()
    glyphs = SVGGlyphRenderer(unit=14.0)

    treble_bottom = 100.0
    lyric_y = treble_bottom + 108.0
    bass_bottom = lyric_y + 72.0 + 4.0 * SP
    height = bass_bottom + 3.0 * SP + 36.0
    staff_bottom = {"treble": treble_bottom, "bass": bass_bottom}
    bottom_dia = {"treble": _diatonic("E", 4), "bass": _diatonic("G", 2)}

    measures = doc.get("measures") or []
    left = 36.0
    x = left + 54.0
    if f_major:
        x += 22.0
    note_centers: dict[tuple[str, int], tuple[float, float]] = {}
    lyric_centers: dict[int, float] = {}
    end_x = x

    prepared: list[tuple[dict[str, Any], dict[str, list[Ev]], dict[float, float]]] = []
    for measure in measures:
        lyrics = list(measure.get("lyrics") or [])
        voices = {
            letter: _events_for_voice(list((measure.get("voices") or {}).get(letter) or []), letter)
            for letter in ("S", "A", "T", "B")
        }
        x_at = _layout_times(voices, lyrics, x)
        prepared.append((measure, voices, x_at))
        end_x = max(x_at.values(), default=x) + 28.0
        x = end_x + 8.0

    width = max(end_x + 24.0, 240.0)
    svg.add(
        f'<rect class="page" x="0" y="0" width="{width:.1f}" height="{height:.1f}" fill="white"/>'
    )
    svg.add(
        f'<path class="brace" d="M {left - 10:.1f} {treble_bottom - 4 * SP:.1f} '
        f'Q {left - 22:.1f} {(treble_bottom + bass_bottom - 4 * SP) / 2:.1f} '
        f'{left - 10:.1f} {bass_bottom:.1f}" fill="none" stroke="black" stroke-width="1.6"/>'
    )

    for staff, bottom in staff_bottom.items():
        for line in range(5):
            y = bottom - line * SP
            svg.add(
                f'<line class="staff" data-staff="{staff}" x1="{left:.1f}" y1="{y:.1f}" '
                f'x2="{end_x:.1f}" y2="{y:.1f}" stroke="black" stroke-width="1"/>'
            )

    _draw_clefs_and_signature(svg, left, treble_bottom, bass_bottom, f_major)

    for measure, voices, x_at in prepared:
        lyrics = list(measure.get("lyrics") or [])
        for letter, evs in voices.items():
            for ev in evs:
                cx = _cx(x_at, ev, lyrics)
                cy = 0.0
                if not ev.rest and ev.step is not None and ev.octave is not None:
                    cy, pos = _pitch_y(staff_bottom[_STAFF_OF[letter]], bottom_dia[_STAFF_OF[letter]], ev.step, ev.octave)
                    note_centers[(letter, ev.index)] = (cx, cy)
                    _draw_note(svg, ev, cx, cy, pos, f_major, lyric_y)
                if letter == "S" and ev.lyric_index is not None:
                    lyric_centers[ev.lyric_index] = cx
        _draw_slurs(svg, voices, note_centers, lyric_y)
        bar_x = max(x_at.values(), default=end_x)
        _draw_barline(svg, measure, bar_x, treble_bottom, bass_bottom)
        _draw_lyrics(svg, lyrics, lyric_centers, voices, note_centers, lyric_y, glyphs, doc)

    title = html.escape(str((doc.get("meta") or {}).get("title") or "partituur"))
    body = "\n".join(svg.parts)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" '
        f'width="100%" preserveAspectRatio="xMinYMin meet" role="img">\n'
        f"<title>{title}</title>\n"
        f"{body}\n</svg>\n"
    )


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
            y2 = max(y2, lyric_y + 14.0)
        return min(y2, cy - short)
    y2 = cy + reach
    if _STAFF_OF[voice] == "treble":
        y2 = min(y2, lyric_y - 46.0)
    return max(y2, cy + short)


def _draw_note(svg: _Svg, ev: Ev, cx: float, cy: float, pos: int, f_major: bool, lyric_y: float) -> None:
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
    if not ev.breve and not ev.stemless and not _whole(ev.elm):
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


def _draw_slurs(
    svg: _Svg,
    voices: dict[str, list[Ev]],
    centers: dict[tuple[str, int], tuple[float, float]],
    lyric_y: float,
) -> None:
    for letter, evs in voices.items():
        starts = [ev.index for ev in evs if ev.slur_start]
        stops = [ev.index for ev in evs if ev.slur_stop]
        for start, stop in zip(starts, stops):
            if stop <= start:
                continue
            pts = [centers[(letter, i)] for i in range(start, stop + 1) if (letter, i) in centers]
            if len(pts) < 2:
                continue
            x1 = pts[0][0]
            x2 = pts[-1][0]
            ys = [y for _x, y in pts]
            # S boven de stokken, A onder de altkoppen (boven de tekst),
            # T vlak boven de tenorkoppen, B onder de baskoppen.
            # Zo snijdt de slur de nootkoppen van die stem niet.
            if letter == "S":
                tip = min(_stem_end(y, "S", lyric_y) for y in ys)
                base = tip - 8.0
                arch = -14.0
            elif letter == "A":
                tip = max(_stem_end(y, "A", lyric_y) for y in ys)
                base = tip + 8.0
                arch = 8.0
            elif letter == "T":
                tip = min(_stem_end(y, "T", lyric_y) for y in ys)
                base = tip - 8.0
                arch = -8.0
            else:
                tip = max(_stem_end(y, "B", lyric_y) for y in ys)
                base = tip + 8.0
                arch = 10.0
            y1 = y2 = base
            cx = (x1 + x2) / 2.0
            cy = base + arch
            svg.add(
                f'<path class="melisma-slur" data-voice="{letter}" data-from="{start}" data-to="{stop}" '
                f'd="M {x1:.1f} {y1:.1f} Q {cx:.1f} {cy:.1f} {x2:.1f} {y2:.1f}" '
                f'fill="none" stroke="black" stroke-width="1.3"/>'
            )


def _draw_barline(svg: _Svg, measure: dict[str, Any], x: float, treble_bottom: float, bass_bottom: float) -> None:
    right = str((measure.get("bar") or {}).get("right") or "single")
    y1 = treble_bottom - 4 * SP
    y2 = bass_bottom
    svg.add(
        f'<line class="barline" data-style="{html.escape(right)}" x1="{x:.1f}" y1="{y1:.1f}" '
        f'x2="{x:.1f}" y2="{y2:.1f}" stroke="black" stroke-width="1.2"/>'
    )
    if right in {"light-light", "light-heavy", "heavy-light", "heavy-heavy", "repeat-end", "repeat-end-section"}:
        svg.add(
            f'<line class="barline barline-double" x1="{x + 5:.1f}" y1="{y1:.1f}" x2="{x + 5:.1f}" y2="{y2:.1f}" '
            f'stroke="black" stroke-width="1.2"/>'
        )


def _draw_lyrics(
    svg: _Svg,
    lyrics: list[dict[str, Any]],
    centers: dict[int, float],
    voices: dict[str, list[Ev]],
    note_centers: dict[tuple[str, int], tuple[float, float]],
    lyric_y: float,
    glyphs: SVGGlyphRenderer,
    doc: dict[str, Any],
) -> None:
    sop = voices.get("S") or []
    for index, lyric in enumerate(lyrics):
        if index not in centers:
            continue
        text = _lyric_text(lyric)
        cx = centers[index]
        kind = "lyric"
        ev = next((e for e in sop if e.lyric_index == index), None)
        if ev is not None and ev.spacer:
            kind = "lyric spacer-lyric"
        svg.add(
            f'<text class="{kind}" data-lyric-index="{index}" x="{cx:.1f}" y="{lyric_y:.1f}" '
            f'text-anchor="middle" font-family="DejaVu Sans, Liberation Sans, sans-serif" '
            f'font-size="{LYRIC_FONT:.0f}">{html.escape(text)}</text>'
        )
        if ev is not None and ev.extend:
            stop = next((e for e in sop if e.slur_stop and e.index > ev.index), None)
            end_x = cx + _text_width(text)
            if stop is not None and ("S", stop.index) in note_centers:
                end_x = note_centers[("S", stop.index)][0] + _half_width("noteheadHalf")
            y = lyric_y - 6.0
            svg.add(
                f'<line class="melisma-extend" data-lyric-index="{index}" '
                f'x1="{cx + _text_width(text) / 2 + 4:.1f}" y1="{y:.1f}" x2="{end_x:.1f}" y2="{y:.1f}" '
                f'stroke="black" stroke-width="1.1"/>'
            )
    for index, lyric in enumerate(lyrics[:-1]):
        syll = str((lyric.get("syllables") or [{}])[0].get("syllabic") or "")
        nxt = str((lyrics[index + 1].get("syllables") or [{}])[0].get("syllabic") or "")
        if syll in {"begin", "middle"} and nxt in {"middle", "end"} and index in centers and index + 1 in centers:
            hx = (centers[index] + centers[index + 1]) / 2.0
            svg.add(
                f'<text class="hyphen" x="{hx:.1f}" y="{lyric_y:.1f}" text-anchor="middle" '
                f'font-family="DejaVu Sans, sans-serif" font-size="{LYRIC_FONT:.0f}">-</text>'
            )
    _draw_soprano_vsa(svg, glyphs, doc, note_centers, lyric_y)


def _draw_soprano_vsa(
    svg: _Svg,
    glyphs: SVGGlyphRenderer,
    doc: dict[str, Any],
    note_centers: dict[tuple[str, int], tuple[float, float]],
    lyric_y: float,
) -> None:
    """Hoogtestrepen van de sopraan, boven de lettergrepen. Dat is de VSA van dit stuk."""
    width = 36.0
    y = lyric_y - 30.0
    for index, token, glyph in soprano_vsa_tokens(doc):
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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Spike: Score-IR naar eigen partituur-SVG")
    parser.add_argument("score_ir", type=Path, help="Score-IR JSON, of .mvsa met --from-mvsa")
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument(
        "--from-mvsa",
        action="store_true",
        help="Lees .mvsa en maak eerst Score-IR (alleen om het voorbeeld te verversen)",
    )
    args = parser.parse_args(argv)
    if args.from_mvsa:
        from vsa.score_ir import export_mvsa_to_score_ir

        doc = export_mvsa_to_score_ir(
            args.score_ir.read_text(encoding="utf-8"),
            title=args.score_ir.stem,
        )
    else:
        doc = json.loads(args.score_ir.read_text(encoding="utf-8"))
    svg = render_score_ir_svg(doc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
