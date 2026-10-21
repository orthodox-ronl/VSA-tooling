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
from .mvsa_musicxml import LyricSyllable, NoteEvent, _emit_score_partituur
from .mvsa_parse import StickyContext
from .score_ir import SCORE_IR_FORMAT, SCORE_IR_PROFILE

_IR_BAR_TO_STYLE: dict[str, str] = {
    "single": "regular",
    "light-light": "light-light",
    "light-heavy": "light-heavy",
    "heavy-light": "heavy-light",
    "heavy-heavy": "heavy-heavy",
    "none": "none",
    "regular": "regular",
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
        cues = [
            str(c.get("text", ""))
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
    return _emit_score_partituur(
        voice_measures,
        title=title,
        context=ctx,
        bar_styles=bar_styles,
        measure_left_styles=measure_left_styles,
        measure_staff_texts=measure_staff_texts,
        meta=meta,
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
