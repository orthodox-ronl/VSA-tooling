"""Score-IR (partituur) export from ``.mvsa``.

Draft contract: ``docs/plans/partituur-ir.md``. Layout profile is always
``partituur`` (SA+TB intent); oefen-profiel comes later.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .bibliotheek_id import resolve_bibliotheek_id
from .music import Duration, Pitch
from .mvsa_musicxml import (
    PARTS,
    MvsaExportError,
    NoteEvent,
    _mvsa_bar_to_style,
    _system_to_events,
    wrap_tekst_at_ellipsis,
)
from .mvsa_parse import StickyContext, parse_mvsa
from .mvsa_validate import MvsaValidationError

SCORE_IR_FORMAT = "score-ir"
SCORE_IR_VERSION = "0.1"
SCORE_IR_PROFILE = "partituur"

# Reverse of duration_model default (same keys as mvsa_import._DURATION_TO_ELM).
_DURATION_TO_ELM: dict[tuple[str, int], str] = {
    ("quarter", 0): "~",
    ("quarter", 1): "~.",
    ("half", 0): "_",
    ("half", 1): "_.",
    ("whole", 0): "__",
    ("eighth", 0): ".",
    ("16th", 0): "..",
}

_BAR_STYLE_TO_IR: dict[str, str] = {
    "regular": "single",
    "light-light": "light-light",
    "light-heavy": "light-heavy",
    "heavy-light": "heavy-light",
    "heavy-heavy": "heavy-heavy",
    "none": "none",
}


def _duration_to_elm(dur: Duration) -> str:
    return _DURATION_TO_ELM.get((dur.note_type, dur.dots), "~")


def _pitch_to_ir(pitch: Pitch) -> dict[str, Any]:
    out: dict[str, Any] = {"step": pitch.step, "octave": pitch.octave}
    if pitch.alter:
        out["alter"] = pitch.alter
    return out


def _bar_token_to_ir(style: str | None) -> str | None:
    if style is None:
        return None
    return _BAR_STYLE_TO_IR.get(style, style)


def _serialize_voice_event(
    ev: NoteEvent,
    *,
    lyric_index: int | None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "pitch": _pitch_to_ir(ev.pitch),
        "duration": {"elm": _duration_to_elm(ev.duration)},
    }
    if lyric_index is not None:
        event["lyricIndex"] = lyric_index
    melisma: dict[str, Any] = {}
    if any(ly.extend for ly in ev.lyrics):
        melisma["extend"] = True
    if ev.slur_start or ev.slur_stop:
        melisma["slur"] = True
    if ev.tie_start or ev.tie_stop:
        melisma["tie"] = True
    if melisma:
        event["melisma"] = melisma
    if ev.recite:
        event["recite"] = True
    marks: dict[str, Any] = {}
    if ev.caesura:
        marks["caesura"] = True
        if ev.caesura_elm:
            marks["caesuraElm"] = ev.caesura_elm
    if ev.breath:
        marks["breath"] = True
    if ev.fermata:
        marks["fermata"] = True
    if ev.dynamics:
        marks["dynamics"] = ev.dynamics
    if ev.wedge_start:
        marks["wedgeStart"] = ev.wedge_start
    if ev.wedge_stop:
        marks["wedgeStop"] = True
    if ev.direction_words:
        marks["words"] = ev.direction_words
    if marks:
        event["marks"] = marks
    return event


def _lyric_pos_from_event(ev: NoteEvent) -> dict[str, Any] | None:
    primary = [ly for ly in ev.lyrics if ly.number == 1]
    if not primary:
        return None
    syllables = [
        {"text": ly.text, "syllabic": ly.syllabic} for ly in primary
    ]
    layers: dict[str, list[str]] = {
        "1": [ly.text for ly in primary],
    }
    layer2 = [ly for ly in ev.lyrics if ly.number == 2]
    if layer2:
        layers["2"] = [ly.text for ly in layer2]
    pos: dict[str, Any] = {"syllables": syllables, "layers": layers}
    if ev.recite:
        pos["recite"] = True
    return pos


def _measure_from_voices(
    *,
    measure_id: str,
    bar_right: str | None,
    bar_left: str | None,
    cues_text: list[str],
    voice_events: dict[str, list[NoteEvent]],
) -> dict[str, Any]:
    # Shared lyrics from soprano (same L-line on all singing voices).
    lyrics: list[dict[str, Any]] = []
    lyric_index_by_s_event: list[int | None] = []
    for ev in voice_events.get("S", []):
        pos = _lyric_pos_from_event(ev)
        if pos is not None:
            lyric_index_by_s_event.append(len(lyrics))
            lyrics.append(pos)
        else:
            lyric_index_by_s_event.append(None)

    voices_out: dict[str, list[dict[str, Any]]] = {}
    for letter in ("S", "A", "T", "B"):
        events = voice_events.get(letter, [])
        serialized: list[dict[str, Any]] = []
        for i, ev in enumerate(events):
            # lyricIndex only on the event that carries layer-1 text; index
            # aligned to the shared lyrics list built from S.
            li: int | None = None
            if _lyric_pos_from_event(ev) is not None and i < len(
                lyric_index_by_s_event
            ):
                li = lyric_index_by_s_event[i]
            serialized.append(_serialize_voice_event(ev, lyric_index=li))
        voices_out[letter] = serialized

    bar: dict[str, Any] = {}
    left = _bar_token_to_ir(bar_left)
    right = _bar_token_to_ir(bar_right) or "single"
    if left:
        bar["left"] = left
    bar["right"] = right

    cues = [
        {"kind": "tekst", "text": t, "anchor": "measure-start"}
        for t in cues_text
        if t
    ]
    return {
        "id": measure_id,
        "bar": bar,
        "cues": cues,
        "lyrics": lyrics,
        "voices": voices_out,
    }


def export_mvsa_to_score_ir(
    text: str,
    *,
    title: str = "mvsa",
    section_id: str | None = None,
    source_path: Path | None = None,
    bibliotheek_id: str | None = None,
) -> dict[str, Any]:
    """Validate + build Score-IR document (profile ``partituur``).

    Raises :class:`MvsaValidationError` or :class:`MvsaExportError`.
    """
    doc = parse_mvsa(text)
    errors = [d for d in doc.diagnostics if d.severity == "error"]
    if errors:
        raise MvsaValidationError(errors)

    sections = doc.sections
    if section_id is not None:
        sections = [s for s in sections if s.id == section_id]
        if not sections:
            raise MvsaExportError(f"sectie {section_id!r} niet gevonden")
    else:
        from .mvsa_speelplan import sections_for_layout

        sections = sections_for_layout(doc, layout="partituur")

    voice_measures: dict[str, list[list[NoteEvent]]] = {
        p["voice"]: [] for p in PARTS
    }
    bar_styles: list[str] = []
    measure_left_styles: list[str | None] = []
    measure_staff_texts: list[list[str]] = []
    pitch_carry: dict[str, Pitch] = {}
    for section in sections:
        for system in section.systems:
            events_by_voice, pitch_carry = _system_to_events(
                system,
                layout="partituur",
                hulptekst=False,
                pitch_carry=pitch_carry,
            )
            for voice, measures in events_by_voice.items():
                voice_measures.setdefault(voice, [])
                voice_measures[voice].extend(measures)
            for mi, bundle in enumerate(system.measures):
                bar_styles.append(_mvsa_bar_to_style(bundle.final_bar))
                left = None
                if mi == 0 and bundle.start_bar:
                    left = _mvsa_bar_to_style(bundle.start_bar)
                measure_left_styles.append(left)
                if mi == 0:
                    texts = list(getattr(system, "staff_texts", None) or [])
                    measure_staff_texts.append(texts)
                else:
                    measure_staff_texts.append([])

    for i, texts in enumerate(measure_staff_texts):
        if texts:
            measure_staff_texts[i] = [wrap_tekst_at_ellipsis(t) for t in texts]

    n = len(bar_styles)
    measures_out: list[dict[str, Any]] = []
    for mi in range(n):
        voice_slice = {
            letter: list(voice_measures.get(letter, [[]])[mi])
            if mi < len(voice_measures.get(letter, []))
            else []
            for letter in ("S", "A", "T", "B")
        }
        measures_out.append(
            _measure_from_voices(
                measure_id=f"m{mi + 1}",
                bar_right=bar_styles[mi] if mi < len(bar_styles) else None,
                bar_left=(
                    measure_left_styles[mi]
                    if mi < len(measure_left_styles)
                    else None
                ),
                cues_text=(
                    measure_staff_texts[mi]
                    if mi < len(measure_staff_texts)
                    else []
                ),
                voice_events=voice_slice,
            )
        )

    ctx: StickyContext = (
        sections[0].systems[0].context
        if sections and sections[0].systems
        else StickyContext()
    )
    effective_title = doc.title if doc.title else title
    meta: dict[str, Any] = {"title": effective_title}
    bib = resolve_bibliotheek_id(bibliotheek_id, source_path)
    if bib:
        meta["bibliotheekId"] = bib
    if getattr(doc, "bron", None):
        meta["sourceLabel"] = doc.bron

    return {
        "format": SCORE_IR_FORMAT,
        "version": SCORE_IR_VERSION,
        "profile": SCORE_IR_PROFILE,
        "meta": meta,
        "pitchContext": {
            "do": ctx.do,
            "mode": ctx.mode,
            "octaves": dict(ctx.oct) if ctx.oct else {},
        },
        "measures": measures_out,
    }


def export_mvsa_to_score_ir_json(
    text: str,
    *,
    title: str = "mvsa",
    section_id: str | None = None,
    source_path: Path | None = None,
    bibliotheek_id: str | None = None,
    indent: int = 2,
) -> str:
    doc = export_mvsa_to_score_ir(
        text,
        title=title,
        section_id=section_id,
        source_path=source_path,
        bibliotheek_id=bibliotheek_id,
    )
    return json.dumps(doc, ensure_ascii=False, indent=indent) + "\n"


def export_mvsa_path_to_score_ir(
    path: Path,
    out: Path,
    *,
    section_id: str | None = None,
    bibliotheek_id: str | None = None,
) -> None:
    path = Path(path)
    if path.suffix.lower() != ".mvsa":
        raise MvsaExportError(
            f"score-ir verwacht .mvsa, kreeg {path.name}"
        )
    text = path.read_text(encoding="utf-8")
    payload = export_mvsa_to_score_ir_json(
        text,
        title=path.stem,
        section_id=section_id,
        source_path=path,
        bibliotheek_id=bibliotheek_id,
    )
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(payload, encoding="utf-8", newline="\n")
