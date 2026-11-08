"""Spike: Score-IR (partituur) → eigen SVG.

Eén systeem, twee balken. Bewust klein: geen OSMD, geen MuseScore, geen
product-CLI. Contracten die deze tekening laat zien:

- S4  stok S/T omhoog, A/B omlaag
- S8  recite 1–(n−2)–1: randnoten, stokloze ||O||, spacers alleen als tekst
- S13 melisma: lyric + extender; bij toonwissel een slur alleen over die noten
- één VSA-hoogteaccent (EHM ``/``) via een spike-overlay, geen Score-IR-veld

Het SVG heeft een viewBox en width="100%" zodat het in een venster meeschaalt.
"""

from __future__ import annotations

import argparse
import html
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vsa.svg_glyphs import SVGGlyphRenderer

SP = 12.0
PX_QUARTER = 36.0
LYRIC_FONT = 18.0
NOTE_RX = 6.2
NOTE_RY = 4.6

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


def render_score_ir_svg(doc: dict[str, Any], accent: dict[str, Any] | None = None) -> str:
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
        _draw_lyrics(svg, lyrics, lyric_centers, voices, note_centers, lyric_y, glyphs, accent, measure)

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
    treble_y = treble_bottom - 1.15 * SP
    bass_y = bass_bottom - 2.55 * SP
    svg.add(
        f'<text class="clef" data-staff="treble" x="{left + 8:.1f}" y="{treble_y:.1f}" '
        f'font-family="Noto Music, serif" font-size="38">&#119070;</text>'
    )
    svg.add(
        f'<text class="clef" data-staff="bass" x="{left + 8:.1f}" y="{bass_y:.1f}" '
        f'font-family="Noto Music, serif" font-size="34">&#119074;</text>'
    )
    if not f_major:
        return
    # F-groot: één mol op de b-lijn. Toon B met alter -1 krijgt dan geen tweede mol.
    for staff, bottom, dia, step, octave in (
        ("treble", treble_bottom, _diatonic("E", 4), "B", 4),
        ("bass", bass_bottom, _diatonic("G", 2), "B", 2),
    ):
        y, _pos = _pitch_y(bottom, dia, step, octave)
        svg.add(
            f'<text class="key-signature" data-staff="{staff}" x="{left + 40:.1f}" y="{y + 5:.1f}" '
            f'font-family="DejaVu Sans, Liberation Sans, sans-serif" font-size="20">&#9837;</text>'
        )


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
    if ev.breve:
        _draw_breve(svg, cx, cy)
    else:
        fill = "none" if _note_open(ev.elm) else "black"
        rx = NOTE_RX + 1.8 if _whole(ev.elm) else NOTE_RX
        svg.add(
            f'<ellipse class="notehead" cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{NOTE_RY:.1f}" '
            f'fill="{fill}" stroke="black" stroke-width="1.4" transform="rotate(-20 {cx:.1f} {cy:.1f})"/>'
        )
        if not ev.stemless and not _whole(ev.elm):
            y2 = _stem_end(cy, ev.voice, lyric_y)
            if stem_dir == "up":
                x = cx + rx - 0.6
                svg.add(
                    f'<line class="stem stem-up voice-{ev.voice}" data-voice="{ev.voice}" '
                    f'x1="{x:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="black" stroke-width="1.3"/>'
                )
            else:
                x = cx - rx + 0.6
                svg.add(
                    f'<line class="stem stem-down voice-{ev.voice}" data-voice="{ev.voice}" '
                    f'x1="{x:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y2:.1f}" stroke="black" stroke-width="1.3"/>'
                )
        for dot in range(_dots(ev.elm)):
            dx = cx + rx + 8.0 + dot * 7.0
            svg.add(f'<circle class="dot" cx="{dx:.1f}" cy="{cy - 3:.1f}" r="2.1" fill="black"/>')
    if ev.alter and not (f_major and ev.step == "B" and ev.alter < 0):
        symbol = "&#9839;" if ev.alter > 0 else "&#9837;" if ev.alter < 0 else "&#9838;"
        svg.add(
            f'<text class="accidental" data-voice="{ev.voice}" x="{cx - 16:.1f}" y="{cy + 5:.1f}" '
            f'text-anchor="end" font-family="DejaVu Sans, sans-serif" font-size="16">{symbol}</text>'
        )
    svg.add("</g>")


def _draw_breve(svg: _Svg, cx: float, cy: float) -> None:
    """Stokloze ||O|| (S8): twee strepen en een open kop, geen gewone nootstok."""
    h = SP * 1.55
    gap = SP * 0.85
    svg.add(
        f'<line class="breve-bar" x1="{cx - gap:.1f}" y1="{cy - h:.1f}" x2="{cx - gap:.1f}" y2="{cy + h:.1f}" '
        f'stroke="black" stroke-width="1.6"/>'
    )
    svg.add(
        f'<line class="breve-bar" x1="{cx + gap:.1f}" y1="{cy - h:.1f}" x2="{cx + gap:.1f}" y2="{cy + h:.1f}" '
        f'stroke="black" stroke-width="1.6"/>'
    )
    svg.add(
        f'<ellipse class="breve-head" cx="{cx:.1f}" cy="{cy:.1f}" rx="5.4" ry="4.2" '
        f'fill="none" stroke="black" stroke-width="1.4"/>'
    )


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
    accent: dict[str, Any] | None,
    measure: dict[str, Any],
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
                end_x = note_centers[("S", stop.index)][0] + NOTE_RX
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
    if not accent:
        return
    if int(accent.get("measure", 0)) != _measure_ordinal(measure):
        return
    lyric_index = accent.get("lyricIndex")
    ehm = str(accent.get("ehm") or "")
    if not isinstance(lyric_index, int) or lyric_index not in centers or not ehm:
        return
    width = max(_text_width(_lyric_text(lyrics[lyric_index])), 44.0)
    x = centers[lyric_index] - width / 2.0
    y = lyric_y - 22.0
    for fragment in glyphs.render_height_modifier([ehm], x, y, width):
        svg.add(fragment.replace('class="vsa-glyph ', 'class="vsa-accent vsa-glyph ', 1))


def _measure_ordinal(measure: dict[str, Any]) -> int:
    raw = str(measure.get("id") or "")
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits:
        return max(0, int(digits) - 1)
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Spike: Score-IR naar eigen partituur-SVG")
    parser.add_argument("score_ir", type=Path, help="Score-IR JSON, of .mvsa met --from-mvsa")
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--accent", type=Path, help="Spike-overlay: één VSA-accent, geen Score-IR-veld")
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
    accent = json.loads(args.accent.read_text(encoding="utf-8")) if args.accent else None
    svg = render_score_ir_svg(doc, accent)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
