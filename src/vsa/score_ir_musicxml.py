"""Score-IR → partituur MusicXML (OSMD / schermbrug).

Draft: ``docs/plans/partituur-ir.md``. Hergebruikt
:func:`vsa.mvsa_musicxml._emit_score_partituur`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .duration_model import UnknownELM, elm_to_duration
from .music import Pitch
from .mvsa_musicxml import (
    LyricSyllable,
    NoteEvent,
    _emit_score_partituur,
    estimate_cue_width_tenths,
    wrap_tekst_at_ellipsis,
)
from .mvsa_parse import StickyContext
from .score_ir import SCORE_IR_FORMAT, SCORE_IR_PROFILE

# Zelfde defaults als MuseScore-partituur (``mscz_partituur``).
_OSMD_CUE_FONT = "Source Sans 3"
_OSMD_CUE_FONT_SIZE = "12"

_IR_BAR_TO_STYLE: dict[str, str] = {
    "single": "regular",
    "light-light": "light-light",
    "light-heavy": "light-heavy",
    "heavy-light": "heavy-light",
    "heavy-heavy": "heavy-heavy",
    "none": "none",
    "regular": "regular",
    # Doorgeven aan ``_emit_measure_barlines`` (niet platslaan naar regular).
    "repeat-start": "repeat-start",
    "repeat-end": "repeat-end",
    "repeat-end-section": "repeat-end-section",
}


class ScoreIrMusicxmlError(ValueError):
    """Score-IR document cannot be converted to MusicXML."""


def _require_score_ir(doc: dict[str, Any]) -> None:
    if doc.get("format") != SCORE_IR_FORMAT:
        raise ScoreIrMusicxmlError(
            f"verwacht format {SCORE_IR_FORMAT!r}, kreeg {doc.get('format')!r}"
        )
    if doc.get("profile") != SCORE_IR_PROFILE:
        raise ScoreIrMusicxmlError(
            f"alleen profile {SCORE_IR_PROFILE!r} ondersteund, "
            f"kreeg {doc.get('profile')!r}"
        )


def _pitch_from_ir(raw: Any) -> Pitch:
    if not isinstance(raw, dict) or "step" not in raw or "octave" not in raw:
        raise ScoreIrMusicxmlError(f"ongeldige pitch: {raw!r}")
    return Pitch(
        step=str(raw["step"]),
        octave=int(raw["octave"]),
        alter=float(raw.get("alter") or 0.0),
    )


def _duration_from_ir(raw: Any):
    if not isinstance(raw, dict) or "elm" not in raw:
        raise ScoreIrMusicxmlError(f"ongeldige duration: {raw!r}")
    try:
        return elm_to_duration(str(raw["elm"]))
    except UnknownELM as exc:
        raise ScoreIrMusicxmlError(str(exc)) from exc


def _screen_cue_text(text: str) -> str:
    """Cue voor OSMD: wrap op ``...`` (uitgangspunt voor maatbreedte).

    ``score-osmd.js`` zet na layout terug naar één regel als die nóg in de
    (al berekende) maatbreedte past; anders blijft de wrap staan.
    """
    flat = " ".join(str(text).split())
    return wrap_tekst_at_ellipsis(flat)


def _lyrics_for_index(
    measure: dict[str, Any], lyric_index: int | None
) -> list[LyricSyllable]:
    if lyric_index is None:
        return []
    lyrics = measure.get("lyrics") or []
    if lyric_index < 0 or lyric_index >= len(lyrics):
        return []
    pos = lyrics[lyric_index]
    syllables = pos.get("syllables") or []
    out: list[LyricSyllable] = []
    for syl in syllables:
        out.append(
            LyricSyllable(
                text=str(syl.get("text", "")),
                syllabic=str(syl.get("syllabic", "single")),
                number=1,
            )
        )
    return out


def _event_to_note(
    ev: dict[str, Any],
    *,
    measure: dict[str, Any],
) -> NoteEvent:
    pitch = _pitch_from_ir(ev.get("pitch"))
    duration = _duration_from_ir(ev.get("duration"))
    li = ev.get("lyricIndex")
    lyrics = _lyrics_for_index(measure, li if isinstance(li, int) else None)
    melisma = ev.get("melisma") or {}
    if lyrics and melisma.get("extend"):
        lyrics[0].extend = True
    marks = ev.get("marks") or {}
    return NoteEvent(
        pitch=pitch,
        duration=duration,
        lyrics=lyrics,
        recite=bool(ev.get("recite")),
        slur_start=bool(melisma.get("slur")),
        slur_stop=bool(melisma.get("slur")),
        tie_start=bool(melisma.get("tie")),
        tie_stop=bool(melisma.get("tie")),
        caesura=bool(marks.get("caesura")),
        caesura_elm=marks.get("caesuraElm"),
        breath=bool(marks.get("breath")),
        fermata=bool(marks.get("fermata")),
        dynamics=marks.get("dynamics"),
        wedge_start=marks.get("wedgeStart"),
        wedge_stop=bool(marks.get("wedgeStop")),
        direction_words=marks.get("words"),
    )


def score_ir_to_musicxml(doc: dict[str, Any]) -> str:
    """Convert a Score-IR document (partituur) to MusicXML 3.1 partituur."""
    _require_score_ir(doc)
    measures = doc.get("measures") or []
    if not isinstance(measures, list):
        raise ScoreIrMusicxmlError("measures moet een lijst zijn")

    voice_measures: dict[str, list[list[NoteEvent]]] = {
        letter: [] for letter in ("S", "A", "T", "B")
    }
    bar_styles: list[str] = []
    measure_left_styles: list[str | None] = []
    measure_staff_texts: list[list[str]] = []
    measure_ending_start: list[str | None] = []
    measure_ending_stop: list[str | None] = []
    measure_repeat_times: list[int | None] = []
    measure_nav_marks: list[list[str]] = []

    for measure in measures:
        if not isinstance(measure, dict):
            raise ScoreIrMusicxmlError("maat moet een object zijn")
        bar = measure.get("bar") or {}
        right = _IR_BAR_TO_STYLE.get(str(bar.get("right") or "single"), "regular")
        left_raw = bar.get("left")
        left = (
            _IR_BAR_TO_STYLE.get(str(left_raw), str(left_raw))
            if left_raw
            else None
        )
        bar_styles.append(right)
        measure_left_styles.append(left)
        ending = measure.get("ending") or {}
        measure_ending_start.append(
            str(ending["start"]) if isinstance(ending, dict) and ending.get("start") else None
        )
        measure_ending_stop.append(
            str(ending["stop"]) if isinstance(ending, dict) and ending.get("stop") else None
        )
        rt = measure.get("repeatTimes")
        measure_repeat_times.append(int(rt) if isinstance(rt, int) else None)
        nav_raw = measure.get("navigation") or []
        measure_nav_marks.append(
            [str(m) for m in nav_raw] if isinstance(nav_raw, list) else []
        )
        cues = [
            _screen_cue_text(c.get("text", ""))
            for c in (measure.get("cues") or [])
            if isinstance(c, dict) and c.get("text")
        ]
        measure_staff_texts.append(cues)
        voices = measure.get("voices") or {}
        for letter in ("S", "A", "T", "B"):
            events_raw = voices.get(letter) or []
            notes = [
                _event_to_note(ev, measure=measure)
                for ev in events_raw
                if isinstance(ev, dict)
            ]
            voice_measures[letter].append(notes)

    pc = doc.get("pitchContext") or {}
    ctx = StickyContext(
        do=str(pc.get("do") or "F4"),
        mode=str(pc.get("mode") or "major"),
        oct={str(k): int(v) for k, v in (pc.get("octaves") or {}).items()},
    )
    meta_in = doc.get("meta") or {}
    title = str(meta_in.get("title") or "score-ir")
    meta = {
        "bron": meta_in.get("sourceLabel"),
        "bibliotheek_id": meta_in.get("bibliotheekId"),
    }
    # MusicXML width: licht voor MuseScore. Geen osmdWidthFactor: cues mogen
    # op scherm over maten heen (score-osmd.js); verbreden per cue tilt de
    # layout en duwt buur-cues omhoog.
    measure_widths: list[int | None] = []
    measure_osmd_factors: list[float | None] = []
    for texts in measure_staff_texts:
        if not texts:
            measure_widths.append(None)
            measure_osmd_factors.append(None)
            continue
        base = estimate_cue_width_tenths(texts)
        measure_widths.append(max(base, 120))
        measure_osmd_factors.append(None)
    # Geen geforceerde new-system na herhaal/sectie: dat zet vaak één maat
    # alleen op een regel. Cue-plaatsing t.o.v. de sleutel doet score-osmd.js
    # na render (OSMD negeert default-x grotendeels).
    measure_new_system = [False] * len(measures)
    return _emit_score_partituur(
        voice_measures,
        title=title,
        context=ctx,
        bar_styles=bar_styles,
        measure_left_styles=measure_left_styles,
        measure_staff_texts=measure_staff_texts,
        measure_new_system=measure_new_system,
        measure_widths=measure_widths,
        measure_ending_start=measure_ending_start,
        measure_ending_stop=measure_ending_stop,
        measure_repeat_times=measure_repeat_times,
        measure_nav_marks=measure_nav_marks,
        meta=meta,
        staff_text_osmd=True,
        tempo_sound_only=True,
        osmd_cue_font=_OSMD_CUE_FONT,
        osmd_cue_font_size=_OSMD_CUE_FONT_SIZE,
        measure_osmd_width_factors=measure_osmd_factors,
    )


def score_ir_json_to_musicxml(text: str) -> str:
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ScoreIrMusicxmlError(f"ongeldige JSON: {exc}") from exc
    if not isinstance(doc, dict):
        raise ScoreIrMusicxmlError("Score-IR root moet een object zijn")
    return score_ir_to_musicxml(doc)


def export_score_ir_path_to_musicxml(path: Path, out: Path) -> None:
    path = Path(path)
    out = Path(out)
    xml = score_ir_json_to_musicxml(path.read_text(encoding="utf-8"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(xml, encoding="utf-8", newline="\n")
