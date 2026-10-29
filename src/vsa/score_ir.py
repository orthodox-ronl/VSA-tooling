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
    _apply_ds_al_coda,
    _apply_ds_al_fine,
    _apply_repeat_nav,
    _apply_volta_ab_ac,
    _collapse_same_pitch_melisma,
    _collect_l_jump_nav_marks,
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
    # Speelplan-bladvorm (zelfde tokens als mvsa_musicxml / from-ir).
    "repeat-start": "repeat-start",
    "repeat-end": "repeat-end",
    "repeat-end-section": "repeat-end-section",
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
    # Rusten (pitch=None): zelfde model als mvsa_musicxml._emit_single_note.
    if ev.pitch is None:
        event: dict[str, Any] = {
            "rest": True,
            "duration": {"elm": _duration_to_elm(ev.duration)},
        }
    else:
        event = {
            "pitch": _pitch_to_ir(ev.pitch),
            "duration": {"elm": _duration_to_elm(ev.duration)},
        }
    if lyric_index is not None:
        event["lyricIndex"] = lyric_index
    melisma: dict[str, Any] = {}
    if any(ly.extend for ly in ev.lyrics):
        melisma["extend"] = True
    if ev.slur_start:
        melisma["slurStart"] = True
    if ev.slur_stop:
        melisma["slurStop"] = True
    if ev.tie_start:
        melisma["tieStart"] = True
    if ev.tie_stop:
        melisma["tieStop"] = True
    if melisma:
        event["melisma"] = melisma
    if ev.recite:
        event["recite"] = True
    print_opts: dict[str, Any] = {}
    if ev.spacer:
        print_opts["spacer"] = True
    if ev.stemless:
        print_opts["stemless"] = True
    if ev.breve_head:
        print_opts["breveHead"] = True
    if print_opts:
        event["print"] = print_opts
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
    ending_start: str | None = None,
    ending_stop: str | None = None,
    repeat_times: int | None = None,
    navigation: list[str] | None = None,
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
    out: dict[str, Any] = {
        "id": measure_id,
        "bar": bar,
        "cues": cues,
        "lyrics": lyrics,
        "voices": voices_out,
    }
    ending: dict[str, str] = {}
    if ending_start:
        ending["start"] = ending_start
    if ending_stop:
        ending["stop"] = ending_stop
    if ending:
        out["ending"] = ending
    if repeat_times is not None and repeat_times > 2:
        out["repeatTimes"] = repeat_times
    if navigation:
        out["navigation"] = list(navigation)
    return out


def export_mvsa_to_score_ir(
    text: str,
    *,
    title: str = "mvsa",
    section_id: str | None = None,
    source_path: Path | None = None,
    bibliotheek_id: str | None = None,
    allow_import_sync_errors: bool = False,
) -> dict[str, Any]:
    """Validate + build Score-IR document (profile ``partituur``).

    Raises :class:`MvsaValidationError` or :class:`MvsaExportError`.

    ``allow_import_sync_errors``: voor tijdelijke VSA→MXL→MVSA-brug
    (score-ir uit ``.vsa``); ``MVSA-SYNC`` mag dan als waarschuwing
    door — de import-schets is bewust niet catalogus-schoon.
    """
    doc = parse_mvsa(text)
    errors = [d for d in doc.diagnostics if d.severity == "error"]
    if allow_import_sync_errors:
        soft = [d for d in errors if d.code == "MVSA-SYNC"]
        errors = [d for d in errors if d.code != "MVSA-SYNC"]
        for d in soft:
            print(
                f"score-ir: negeer import-{d.code}: {d.message}",
                flush=True,
            )
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

    from .mvsa_speelplan import plan_partituur_navigation

    voice_measures: dict[str, list[list[NoteEvent]]] = {
        p["voice"]: [] for p in PARTS
    }
    bar_styles: list[str] = []
    measure_left_styles: list[str | None] = []
    measure_staff_texts: list[list[str]] = []
    blok_measure_range: dict[str, tuple[int, int]] = {}
    pitch_carry: dict[str, Pitch] = {}
    for section in sections:
        section_start = len(bar_styles)
        for system in section.systems:
            events_by_voice, pitch_carry = _system_to_events(
                system,
                layout="partituur",
                translit=False,
                pitch_carry=pitch_carry,
            )
            for voice, measures in events_by_voice.items():
                voice_measures.setdefault(voice, [])
                # S13 eindvorm voor OSMD: gestipte same-pitch (niet I1-ties).
                # S8-spacers/breve blijven intact via pack-guard.
                collapsed = [
                    _collapse_same_pitch_melisma(m, allow_dotted=True)
                    for m in measures
                ]
                voice_measures[voice].extend(collapsed)
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
        if (
            section.origin == "blok"
            and section.id
            and len(bar_styles) > section_start
        ):
            blok_measure_range[section.id] = (section_start, len(bar_styles) - 1)

    # Zelfde speelplan-bladvorm als partituur-MusicXML (volta / herhaal / D.S.).
    ending_start: list[str | None] = [None] * len(bar_styles)
    ending_stop: list[str | None] = [None] * len(bar_styles)
    repeat_times: list[int | None] = [None] * len(bar_styles)
    nav_marks: list[list[str]] = [[] for _ in bar_styles]
    if section_id is None:
        nav = plan_partituur_navigation(doc)
        if nav is not None and nav.kind == "volta_ab_ac" and nav.volta is not None:
            _apply_volta_ab_ac(
                nav.volta,
                blok_measure_range,
                measure_left_styles,
                bar_styles,
                ending_start,
                ending_stop,
            )
        elif nav is not None and nav.kind == "repeat" and nav.repeat is not None:
            _apply_repeat_nav(
                nav.repeat,
                blok_measure_range,
                measure_left_styles,
                bar_styles,
                repeat_times,
            )
        elif nav is not None and nav.kind == "ds_al_fine" and nav.ds is not None:
            _apply_ds_al_fine(nav.ds, blok_measure_range, nav_marks)
        elif nav is not None and nav.kind == "ds_al_coda" and nav.coda is not None:
            _apply_ds_al_coda(nav.coda, blok_measure_range, nav_marks)
        _collect_l_jump_nav_marks(voice_measures.get("S", []), nav_marks)

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
                ending_start=(
                    ending_start[mi] if mi < len(ending_start) else None
                ),
                ending_stop=ending_stop[mi] if mi < len(ending_stop) else None,
                repeat_times=(
                    repeat_times[mi] if mi < len(repeat_times) else None
                ),
                navigation=nav_marks[mi] if mi < len(nav_marks) else None,
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
    if getattr(doc, "tempo", None) is not None:
        meta["tempo"] = str(doc.tempo)

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
    allow_import_sync_errors: bool = False,
) -> str:
    doc = export_mvsa_to_score_ir(
        text,
        title=title,
        section_id=section_id,
        source_path=source_path,
        bibliotheek_id=bibliotheek_id,
        allow_import_sync_errors=allow_import_sync_errors,
    )
    return json.dumps(doc, ensure_ascii=False, indent=indent) + "\n"


def export_mvsa_path_to_score_ir(
    path: Path,
    out: Path,
    *,
    section_id: str | None = None,
    bibliotheek_id: str | None = None,
    allow_import_sync_errors: bool = False,
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
        allow_import_sync_errors=allow_import_sync_errors,
    )
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(payload, encoding="utf-8", newline="\n")
