"""Export .mvsa to multi-part SATB MusicXML (draft-v0).

Layouts (canonieke checklists):

- ``playback`` — vier parts Soprano/Alto/Tenor/Bass (Coria / ``.mxl``);
  elke part met canonieke piano-MIDI (checklist M8).
- ``partituur`` — twee parts SA + TB, **twee voices** per balk (S/T stok
  omhoog, A/B stok omlaag), **lege** part-namen (tussenbestand / bron voor
  MuseScore-``.mscz``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from xml.sax.saxutils import escape

from .duration_model import elm_to_duration
from .music import Duration, Pitch
from .musicxml_package import write_musicxml_output
from .mvsa_parse import (
    HEIGHT_DEGREE_RE,
    HEIGHT_EHM_RE,
    HEIGHT_NOTE_RE,
    LPosition,
    StickyContext,
    VoicePosition,
    parse_mvsa,
)
from .mvsa_validate import is_lyrics_stem
from .mvsa_validate import MvsaValidationError
from .mvsa_validate import resolve_stem_map_key
from .mvsa_validate import split_directive_assignments
from .syllabify import display_lyric_text
from .pitch_resolver import (
    PitchResolver,
    degree_to_pitch,
    key_fifths,
    parse_pitch_string,
    pitch_in_do_octave,
)

MvsaLayout = Literal["playback", "partituur"]

PARTS = (
    {"id": "P1", "name": "Soprano", "abbr": "S", "clef": ("G", "2"), "voice": "S"},
    {"id": "P2", "name": "Alto", "abbr": "A", "clef": ("G", "2"), "voice": "A"},
    {"id": "P3", "name": "Tenor", "abbr": "T", "clef": ("F", "4"), "voice": "T"},
    {"id": "P4", "name": "Bass", "abbr": "B", "clef": ("F", "4"), "voice": "B"},
)

# Canonieke playback-MIDI (checklist M8): piano op elke stempartij.
_PLAYBACK_MIDI_SOUND = "keyboard.piano.grand"
_PLAYBACK_MIDI_PROGRAM = "1"
_PLAYBACK_MIDI_VOLUME = "78.7402"
_PLAYBACK_MIDI_PAN = "0"

# Partituur: twee balken; part-name leeg (geen stem-indicaties op het blad).
PARTITUUR_PARTS = (
    {"id": "P1", "clef": ("G", "2"), "upper": "S", "lower": "A"},
    {"id": "P2", "clef": ("F", "4"), "upper": "T", "lower": "B"},
)

# Prefix accidental, name, then either oct[+acc] or acc[+oct]
_DEGREE_RE = HEIGHT_DEGREE_RE
_NOTE_RE = HEIGHT_NOTE_RE
_EHM_RE = HEIGHT_EHM_RE

ALTER_ACCIDENTAL = {
    1.0: "sharp",
    -1.0: "flat",
    2.0: "double-sharp",
    -2.0: "double-flat",
}

_DEGREE_INDEX = {"do": 0, "re": 1, "mi": 2, "fa": 3, "sol": 4, "la": 5, "ti": 6}


@dataclass
class LyricSyllable:
    text: str
    syllabic: str = "single"
    number: int = 1
    extend: bool = False  # MusicXML <extend/> (melisma-lijn na lettergreep)


@dataclass
class NoteEvent:
    pitch: Pitch
    duration: Duration
    lyrics: list[LyricSyllable] = field(default_factory=list)
    recite: bool = False
    spacer: bool = False  # onzichtbare kop, zichtbare lyric (partituur-recite)
    duration_divisions: int | None = None  # override MusicXML <duration>
    stemless: bool = False  # stokloos (||O||-midden of spacer)
    breve_head: bool = False  # print als ||O||; metrisch = duration (niet type=breve)
    slur_start: bool = False  # melisma-boog start (S2) — alleen bij toonwissels
    slur_stop: bool = False  # melisma-boog eind
    tie_start: bool = False  # same-pitch hold-keten (I2)
    tie_stop: bool = False


# Partituur-print: recite met ≥6 lettergrepen → 1-(n-2)-1 (randnoten + ||O||).
# Midden: stokloos met breve-kop; metrisch = randduur (geen MusicXML type=breve —
# MuseScore rekt die anders tot 8/4 en blaas maten op).
RECITE_PRINT_COLLAPSE_MIN = 6

# Cue-spacer (legacy / peiling): minimale onzichtbare maat. Partituur/MSCZ
# gebruikt voor mid-flow ``@tekst`` géén spacermaat en géén mid-systeem-HBox.
CUE_GAP_DURATION_DIVS = 1
CUE_GAP_NOTE_TYPE = "16th"
PAUSE_LYRIC = "[PAUZE]"
PAUSE_DURATION_DIVS = 16  # whole @ divisions=4

# Extra Coria-parts voor hulptekst (volume 0; geen dubbel geluid by default).
_HULPTEKST_VOLUME = "0"

_CLEF_BY_SATB = {
    "S": ("G", "2"),
    "A": ("G", "2"),
    "T": ("F", "4"),
    "B": ("F", "4"),
}


def _pairing_taal(taal: str | None) -> str | None:
    """Complementaire laag-label: ksl↔nl (Coria-partnamen)."""
    if taal is None:
        return None
    low = taal.lower()
    if low == "ksl":
        return "nl"
    if low == "nl":
        return "ksl"
    return None


def _part_display_name(base: str, label: str | None) -> str:
    if label:
        return f"{base} ({label})"
    return base


def _part_display_abbr(base: str, label: str | None, *, hulp: bool = False) -> str:
    if label:
        return f"{base}-{label}"
    return f"{base}h" if hulp else base


def _clef_for_voice(voice_id: str) -> tuple[str, str]:
    if re.fullmatch(r"[SATB]\d*", voice_id):
        return _CLEF_BY_SATB[voice_id[0].upper()]
    return ("G", "2")


def _satb_display_name(voice_id: str) -> str:
    """Vriendelijke SATB-naam; anders de stemidentifier zelf."""
    if re.fullmatch(r"[SATB]\d*", voice_id):
        return next(p["name"] for p in PARTS if p["voice"] == voice_id[0])
    return voice_id


def _satb_abbr(voice_id: str) -> str:
    if re.fullmatch(r"[SATB]\d*", voice_id):
        return voice_id[0]
    return voice_id[:4]


def _infer_label_from_lyric_text(text: str) -> str | None:
    from .transliterate import detect_direction

    direction = detect_direction(text)
    if direction == "ksl_to_latin":
        return "ksl"
    if direction == "nl_to_cyrillic":
        return "nl"
    return None


def _infer_bron_taal_from_events(
    voice_measures: dict[str, list[list[NoteEvent]]],
) -> str | None:
    """Eerste lyric number=1 met herkenbaar schrift → ``ksl`` of ``nl``."""
    for measures in voice_measures.values():
        for measure in measures:
            for ev in measure:
                for ly in ev.lyrics:
                    if ly.number != 1 or not ly.text or ly.text == PAUSE_LYRIC:
                        continue
                    found = _infer_label_from_lyric_text(ly.text)
                    if found:
                        return found
    return None


def _lyric_numbers_present(
    voice_measures: dict[str, list[list[NoteEvent]]],
) -> list[int]:
    nums: set[int] = set()
    for measures in voice_measures.values():
        for measure in measures:
            for ev in measure:
                for ly in ev.lyrics:
                    nums.add(ly.number)
    return sorted(nums) if nums else [1]


def _resolve_layer_labels(
    systems: list,
    voice_measures: dict[str, list[list[NoteEvent]]],
    lyric_numbers: list[int],
) -> list[str | None]:
    """Eén Coria-label per lyric-number, uit ``@taal`` of schrift-gok."""
    markers: list[str] = []
    ctx = None
    for system in systems:
        markers = [m for m in system.markers if is_lyrics_stem(m)]
        ctx = getattr(system, "context", None)
        if markers:
            break
    labels: list[str | None] = []
    for i, num in enumerate(lyric_numbers):
        label: str | None = None
        if ctx is not None and i < len(markers):
            label = ctx.taal_for(markers[i])
        if label is None and i == 0:
            label = (ctx.taal_for("L") if ctx is not None else None) or (
                _infer_bron_taal_from_events(voice_measures)
            )
        if label is None and i == 1:
            base = labels[0] if labels else None
            label = (ctx.taal_for("L1") if ctx is not None else None) or _pairing_taal(
                base
            )
        labels.append(label)
    return labels


def _ordered_voice_ids(
    voice_measures: dict[str, list[list[NoteEvent]]],
    systems: list,
) -> list[str]:
    """Stemvolgorde uit het eerste systeem; val terug op keys zonder ``h``-suffix."""
    for system in systems:
        voices = [m for m in system.markers if not is_lyrics_stem(m)]
        if voices:
            # Playback gebruikt volle ids; partituur-legacy kan letters zijn.
            if any(v in voice_measures for v in voices):
                return list(voices)
            letters = []
            for v in voices:
                letter = v[0]
                if letter not in letters and letter in voice_measures:
                    letters.append(letter)
            if letters:
                return letters
    return [v for v in voice_measures if not re.search(r"h\d*$", v) and "h" not in v[1:]]


def _build_playback_part_list(
    voice_ids: list[str],
    layer_labels: list[str | None],
    *,
    with_extra_layers: bool,
) -> tuple[list[dict], list[dict] | None]:
    """Coria part-list: ``Sop (aap)``, ``Zeep (noot)``, …"""
    primary_label = layer_labels[0] if layer_labels else None
    primary = [
        {
            "id": f"P{i + 1}",
            "name": _part_display_name(_satb_display_name(v), primary_label),
            "abbr": _part_display_abbr(_satb_abbr(v), primary_label),
            "clef": _clef_for_voice(v),
            "voice": v,
        }
        for i, v in enumerate(voice_ids)
    ]
    if not with_extra_layers or len(layer_labels) < 2:
        return primary, None
    extra: list[dict] = []
    pid = len(primary) + 1
    for li, label in enumerate(layer_labels[1:], start=2):
        for v in voice_ids:
            extra.append(
                {
                    "id": f"P{pid}",
                    "name": _part_display_name(
                        _satb_display_name(v), label
                    )
                    if label
                    else f"{_satb_display_name(v)} (hulptekst)",
                    "abbr": _part_display_abbr(
                        _satb_abbr(v), label, hulp=True
                    ),
                    "clef": _clef_for_voice(v),
                    "voice": f"{v}h{li}",
                }
            )
            pid += 1
    return primary, extra


def _clone_notes_for_lyric_number(
    measures: list[list[NoteEvent]], number: int
) -> list[list[NoteEvent]]:
    cloned: list[list[NoteEvent]] = []
    for measure in measures:
        cm: list[NoteEvent] = []
        for ev in measure:
            layer = [ly for ly in ev.lyrics if ly.number == number]
            cm.append(
                NoteEvent(
                    pitch=ev.pitch,
                    duration=ev.duration,
                    lyrics=[
                        LyricSyllable(
                            text=ly.text,
                            syllabic=ly.syllabic,
                            number=1,
                            extend=ly.extend,
                        )
                        for ly in layer
                    ],
                    recite=ev.recite,
                    spacer=ev.spacer,
                    duration_divisions=ev.duration_divisions,
                    stemless=ev.stemless,
                    breve_head=ev.breve_head,
                    slur_start=ev.slur_start,
                    slur_stop=ev.slur_stop,
                    tie_start=ev.tie_start,
                    tie_stop=ev.tie_stop,
                )
            )
        cloned.append(cm)
    return cloned


def _attach_hulptekst_parts(
    voice_measures: dict[str, list[list[NoteEvent]]],
    voice_ids: list[str],
    lyric_numbers: list[int],
) -> dict[str, list[list[NoteEvent]]]:
    """Kloon stemmen per lyric-number > 1 naar ``{voice}h{n}``."""
    out = {k: v for k, v in voice_measures.items()}
    # Primaire laag: strip andere lyric-numbers op de bronstemmen (Coria toont één tekst).
    primary_num = lyric_numbers[0] if lyric_numbers else 1
    for voice in voice_ids:
        if voice in out:
            out[voice] = _clone_notes_for_lyric_number(out[voice], primary_num)
    for num in lyric_numbers[1:]:
        for voice in voice_ids:
            src = voice_measures.get(voice, [])
            out[f"{voice}h{num}"] = _clone_notes_for_lyric_number(src, num)
    return out


class MvsaExportError(Exception):
    def __init__(self, message: str, *, line: int = 0) -> None:
        self.line = line
        super().__init__(message)


def _direction_from_sticky_taal(taal: str | None):
    """Sticky ``@taal`` → transliterator-richting; ``None`` = auto per lettergreep."""
    if taal is None:
        return None
    low = taal.lower()
    if low == "ksl":
        return "ksl_to_latin"
    if low == "nl":
        return "nl_to_cyrillic"
    return None


def _apply_hulptekst_to_notes(
    notes: list[NoteEvent],
    *,
    direction: str | None,
) -> None:
    """Voeg lyric number 2 toe; skip als number 2 al bestaat (handmatige L1)."""
    from .transliterate import render_syllable

    for ev in notes:
        if any(ly.number == 2 for ly in ev.lyrics):
            continue
        extras: list[LyricSyllable] = []
        for ly in list(ev.lyrics):
            if ly.number != 1:
                continue
            if not ly.text or ly.text == PAUSE_LYRIC:
                continue
            rendered = render_syllable(ly.text, direction=direction)
            if rendered == ly.text:
                continue
            extras.append(
                LyricSyllable(
                    text=rendered,
                    syllabic=ly.syllabic,
                    number=2,
                    extend=ly.extend,
                )
            )
        ev.lyrics.extend(extras)


def _apply_hulptekst_lyric_layer(
    voice_measures: dict[str, list[list[NoteEvent]]],
) -> None:
    """Fallback zonder sticky ``@taal`` (auto per lettergreep)."""
    for measures in voice_measures.values():
        for measure in measures:
            _apply_hulptekst_to_notes(measure, direction=None)



def export_mvsa_to_musicxml(
    text: str,
    *,
    title: str = "mvsa",
    section_id: str | None = None,
    layout: MvsaLayout = "playback",
    source_path: Path | None = None,
    bibliotheek_id: str | None = None,
    hulptekst: bool = False,
    hulptekst_as_parts: bool = False,
) -> str:
    """Validate + export. Raises MvsaValidationError or MvsaExportError.

    *hulptekst*: tweede lyric-laag (``number=\"2\"``) via
    :mod:`vsa.transliterate` (ksl→Latijn / nl→Cyrillisch per lettergreep).
    *hulptekst_as_parts*: alleen zinvol bij ``layout=\"playback\"`` — extra
    SATB-parts met alleen hulptekst (volume 0; speler kan solo zetten).
    """
    if layout not in ("playback", "partituur"):
        raise MvsaExportError(f"onbekende layout {layout!r}")
    if hulptekst_as_parts and not hulptekst:
        hulptekst = True
    if hulptekst_as_parts and layout != "playback":
        raise MvsaExportError(
            "hulptekst_as_parts is alleen voor layout=playback (Coria)"
        )
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

        sections = sections_for_layout(doc, layout=layout)

    voice_measures: dict[str, list[list[NoteEvent]]] = {
        p["voice"]: [] for p in PARTS
    }
    bar_styles: list[str] = []
    measure_left_styles: list[str | None] = []
    measure_staff_texts: list[list[str]] = []
    measure_new_system: list[bool] = []
    # BPM per maatindex; None = geen tempo-wissel (vorige blijft).
    measure_tempos: list[int | None] = []
    # Speelblok-id → (eerste_maatindex, laatste_maatindex) in bladvorm.
    blok_measure_range: dict[str, tuple[int, int]] = {}
    score_started = False
    systems_flat: list = []
    for section in sections:
        section_start = len(bar_styles)
        for system in section.systems:
            systems_flat.append(system)
            events_by_voice = _system_to_events(
                system, layout=layout, hulptekst=hulptekst
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
                    # Alleen ``@mscz-newline`` forceert een MuseScore-systeembreuk.
                    wants_break = bool(getattr(system, "mscz_newline", False))
                    measure_new_system.append(wants_break and score_started)
                    sys_tempo = getattr(system, "tempo", None)
                    measure_tempos.append(
                        int(sys_tempo) if sys_tempo is not None else None
                    )
                else:
                    measure_staff_texts.append([])
                    measure_new_system.append(False)
                    measure_tempos.append(None)
            if system.measures:
                score_started = True
        if (
            layout == "partituur"
            and section.origin == "blok"
            and section.id
            and len(bar_styles) > section_start
        ):
            blok_measure_range[section.id] = (section_start, len(bar_styles) - 1)

    from .mvsa_speelplan import plan_partituur_navigation

    nav = plan_partituur_navigation(doc) if layout == "partituur" else None
    ending_start: list[str | None] = [None] * len(bar_styles)
    ending_stop: list[str | None] = [None] * len(bar_styles)
    repeat_times: list[int | None] = [None] * len(bar_styles)
    nav_marks: list[list[str]] = [[] for _ in bar_styles]
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
    # expand / identity: geen extra tekens; expand schrijft het plan uit via
    # sections_for_layout.
    # Wrap lange ``@tekst`` (``...`` → nieuwe regel) vóór breedte-schatting.
    for i, texts in enumerate(measure_staff_texts):
        if texts:
            measure_staff_texts[i] = [wrap_tekst_at_ellipsis(t) for t in texts]

    measure_widths: list[int | None] = [None] * len(measure_staff_texts)
    if layout == "partituur":
        _prepare_partituur_tekst_frames(
            bar_styles,
            measure_staff_texts,
            measure_new_system,
            measure_widths,
        )
        # Witruimte vóór mid-flow @tekst: dubbele maatstreep + SystemText.
        # Geen MusicXML-spacermaat (lege balklijnen) en geen mid-systeem-HBox
        # (MuseScore tekent dan een accolade middenin het systeem).
        measure_cue_gap = [False] * len(measure_staff_texts)
        measure_pauze = [False] * len(measure_staff_texts)
    else:
        measure_cue_gap = [False] * max(
            len(measure_staff_texts),
            max((len(ms) for ms in voice_measures.values()), default=0),
        )
        measure_pauze = _insert_playback_pauze_measures(
            voice_measures,
            bar_styles,
            measure_staff_texts,
            measure_left_styles,
            measure_tempos,
        )

    from .bibliotheek_id import resolve_bibliotheek_id

    ctx = sections[0].systems[0].context if sections and sections[0].systems else StickyContext()
    effective_title = doc.title if doc.title else title
    tempo = getattr(doc, "tempo", None)
    meta = {
        "composer": getattr(doc, "composer", None),
        "copyright": getattr(doc, "copyright", None),
        "bron": getattr(doc, "bron", None),
        "ondertitel": getattr(doc, "ondertitel", None),
        "tekstdichter": getattr(doc, "tekstdichter", None),
        "arrangeur": getattr(doc, "arrangeur", None),
        "vertaler": getattr(doc, "vertaler", None),
        "toon": getattr(doc, "toon", None),
        "tempo": str(tempo) if tempo is not None else None,
        "bibliotheek_id": resolve_bibliotheek_id(bibliotheek_id, source_path),
    }
    # Starttempo op maat 1 als geen @tempo vóór het eerste systeem.
    if measure_tempos and measure_tempos[0] is None:
        measure_tempos[0] = _parse_tempo_bpm(meta)
    if layout == "partituur":
        return _emit_score_partituur(
            voice_measures,
            title=effective_title,
            context=ctx,
            bar_styles=bar_styles,
            measure_left_styles=measure_left_styles,
            measure_staff_texts=measure_staff_texts,
            measure_new_system=measure_new_system,
            measure_cue_gap=measure_cue_gap,
            measure_widths=measure_widths,
            measure_ending_start=ending_start,
            measure_ending_stop=ending_stop,
            measure_repeat_times=repeat_times,
            measure_nav_marks=nav_marks,
            measure_tempos=measure_tempos,
            meta=meta,
        )

    extra_parts: list[dict[str, str]] | None = None
    playback_parts: list[dict] | None = None
    if layout == "playback":
        voice_ids = _ordered_voice_ids(voice_measures, systems_flat)
        # Geen lege SATB-placeholders meenemen als het stuk andere ids heeft.
        if voice_ids and not all(
            re.fullmatch(r"[SATB]\d*", v) for v in voice_ids
        ):
            voice_measures = {
                k: v for k, v in voice_measures.items() if k in voice_ids
            }
        lyric_nums = _lyric_numbers_present(voice_measures)
        layer_labels = _resolve_layer_labels(
            systems_flat, voice_measures, lyric_nums
        )
        if hulptekst_as_parts:
            if len(lyric_nums) < 2:
                # Genereer-laag ontbreekt → toch labels voor bron only.
                pass
            playback_parts, extra_parts = _build_playback_part_list(
                voice_ids,
                layer_labels,
                with_extra_layers=len(lyric_nums) > 1,
            )
            if len(lyric_nums) > 1:
                voice_measures = _attach_hulptekst_parts(
                    voice_measures, voice_ids, lyric_nums
                )
        else:
            # Gewone Coria: stemnamen = identifiers (SATB → Soprano…).
            playback_parts, _ = _build_playback_part_list(
                voice_ids, [None], with_extra_layers=False
            )

    xml = _emit_score_playback(
        voice_measures,
        title=effective_title,
        context=ctx,
        bar_styles=bar_styles,
        measure_left_styles=measure_left_styles,
        measure_staff_texts=measure_staff_texts,
        measure_new_system=measure_new_system,
        measure_cue_gap=measure_cue_gap,
        measure_pauze=measure_pauze,
        measure_tempos=measure_tempos,
        meta=meta,
        parts=playback_parts,
        extra_parts=extra_parts,
    )
    from .musicxml_coria_timing import finalize_coria_musicxml

    # Timing al in emit ([PAUZE]); hier alleen sanitize + accidentals + geen DOCTYPE.
    return finalize_coria_musicxml(xml, apply_timing=False)


def export_mvsa_path(
    path: Path,
    out: Path,
    *,
    section_id: str | None = None,
    layout: MvsaLayout = "playback",
    bibliotheek_id: str | None = None,
    hulptekst: bool = False,
    hulptekst_as_parts: bool = False,
) -> None:
    text = path.read_text(encoding="utf-8-sig")
    xml = export_mvsa_to_musicxml(
        text,
        title=path.stem,
        section_id=section_id,
        layout=layout,
        source_path=path,
        bibliotheek_id=bibliotheek_id,
        hulptekst=hulptekst,
        hulptekst_as_parts=hulptekst_as_parts,
    )
    write_musicxml_output(out, xml)


def _lyric_number_for_marker(marker: str, *, index: int = 0) -> int:
    """Map lyrics-stem naar MusicXML ``lyric number``.

    ``L`` / ``lyrics`` → 1; ``L1`` → 2; ``L2`` → 3; enz.
    Andere lyrics-ids (``Lap``, ``Lus``, …): volgorde in het systeem (1-based).
    """
    low = marker.lower()
    if low in {"l", "lyrics"}:
        return 1
    m = re.fullmatch(r"l(\d+)", low)
    if m:
        return int(m.group(1)) + 1
    return index + 1


def _add_lyric_layer_to_notes(
    notes: list[NoteEvent],
    lpos: LPosition,
    *,
    opens_hyphen: bool,
    number: int,
) -> None:
    """Voeg één parallelle lyrics-laag toe aan bestaande noten (zelfde positie)."""
    if not notes:
        return
    if lpos.recite:
        syllables = list(lpos.syllables) if lpos.syllables else []
        n = len(syllables)
        for i, note in enumerate(notes):
            if i >= n:
                break
            syl_text = syllables[i]
            if not syl_text:
                continue
            opens = i + 1 < n and i < len(lpos.links) and lpos.links[i]
            continues = (i == 0 and lpos.continues_word) or (
                i > 0 and i - 1 < len(lpos.links) and lpos.links[i - 1]
            )
            if continues and opens:
                syl = "middle"
            elif continues:
                syl = "end"
            elif opens:
                syl = "begin"
            else:
                syl = "single"
            note.lyrics.append(
                LyricSyllable(text=syl_text, syllabic=syl, number=number)
            )
        return

    if not lpos.syllables:
        return
    n = len(notes)
    primary_syl = _syllabic_for_position(lpos, opens_hyphen=opens_hyphen)
    if len(lpos.syllables) == 1:
        syl = primary_syl
        if n > 1 and syl == "single":
            syl = "begin"
        text = lpos.syllables[0]
        extend = n > 1
    else:
        text = _join_lyric_text(lpos.syllables, lpos.links)
        syl = primary_syl if primary_syl != "single" else "begin"
        extend = n > 1
    notes[0].lyrics.append(
        LyricSyllable(text=text, syllabic=syl, number=number, extend=extend)
    )


def _system_to_events(
    system,
    *,
    layout: MvsaLayout = "playback",
    hulptekst: bool = False,
) -> dict[str, list[list[NoteEvent]]]:
    ctx: StickyContext = system.context
    lyric_markers = [m for m in system.markers if is_lyrics_stem(m)]
    if not lyric_markers:
        raise MvsaExportError("geen lyrics-regel in systeem", line=system.start_line)
    primary_lyric = lyric_markers[0]
    parallel_lyrics = lyric_markers[1:]
    hulp_direction = (
        _direction_from_sticky_taal(ctx.taal_for(primary_lyric))
        if hulptekst
        else None
    )

    voice_markers = [m for m in system.markers if not is_lyrics_stem(m)]
    if layout == "partituur":
        non_satb = [m for m in voice_markers if not re.fullmatch(r"[SATB]\d*", m)]
        if non_satb:
            raise MvsaExportError(
                "partituur-export ondersteunt alleen stem-ids S/A/T/B "
                f"(eventueel met cijfer), niet {non_satb}",
                line=system.start_line,
            )

    # Playback: volle stemidentifier als key. Partituur: SATB-letter (SA/TB-balken).
    def _vkey(vm: str) -> str:
        return vm if layout == "playback" else vm[0]

    resolvers: dict[str, PitchResolver] = {}
    line_ehms = getattr(system, "line_ehms", {}) or {}
    for m in voice_markers:
        key = _vkey(m)
        resolvers[key] = _voice_resolver(ctx, m)
        if ctx.start:
            _apply_start(resolvers[key], ctx.start, m)
        line_ehm = line_ehms.get(m)
        if line_ehm is not None:
            _apply_line_ehm(resolvers[key], line_ehm)

    result: dict[str, list[list[NoteEvent]]] = {_vkey(m): [] for m in voice_markers}
    if layout == "partituur":
        for p in PARTS:
            result.setdefault(p["voice"], [])

    primary_number = _lyric_number_for_marker(primary_lyric, index=0)

    for bundle in system.measures:
        l_positions = bundle.lyrics.get(primary_lyric, [])
        measure_events: dict[str, list[NoteEvent]] = {
            _vkey(m): [] for m in voice_markers
        }

        for vi, lpos in enumerate(l_positions):
            next_continues = (
                vi + 1 < len(l_positions) and l_positions[vi + 1].continues_word
            )
            extra_layers: list[tuple[int, LPosition]] = []
            for pi, pm in enumerate(parallel_lyrics, start=1):
                pl_list = bundle.lyrics.get(pm, [])
                if vi >= len(pl_list):
                    raise MvsaExportError(
                        f"{pm}: minder L-posities dan {primary_lyric}",
                        line=system.line_nos.get(pm, system.start_line),
                    )
                extra_layers.append(
                    (_lyric_number_for_marker(pm, index=pi), pl_list[vi])
                )
            for vm in voice_markers:
                key = _vkey(vm)
                vpositions = bundle.voices.get(vm, [])
                if vi >= len(vpositions):
                    raise MvsaExportError(
                        f"{vm}: minder hoogte-stukken dan L-posities",
                        line=system.line_nos.get(vm, system.start_line),
                    )
                vpos = vpositions[vi]
                notes = _position_to_notes(
                    lpos,
                    vpos,
                    resolvers[key],
                    ctx,
                    vm,
                    opens_hyphen=next_continues,
                    layout=layout,
                    line=system.line_nos.get(vm, system.start_line),
                    marker=vm,
                    lyric_number=primary_number,
                    extra_lyric_layers=extra_layers,
                )
                if hulptekst:
                    _apply_hulptekst_to_notes(notes, direction=hulp_direction)
                measure_events[key].extend(notes)

        for key, evs in measure_events.items():
            result[key].append(evs)

    if layout == "partituur":
        for p in PARTS:
            if p["voice"] not in result:
                result[p["voice"]] = [[] for _ in system.measures]
    return result


def writing_do_pitch(ctx: StickyContext, marker: str) -> Pitch:
    """``@do`` shifted by ``@oct`` for this voice (schrijf-do)."""
    do_p = parse_pitch_string(ctx.do)
    shift = ctx.oct_for(marker)
    if shift == 0:
        return do_p
    return Pitch(step=do_p.step, octave=do_p.octave + shift, alter=do_p.alter)


def _voice_resolver(ctx: StickyContext, marker: str) -> PitchResolver:
    """PitchResolver whose do is the stem's schrijf-do (``@do`` + ``@oct``)."""
    do_p = writing_do_pitch(ctx, marker)
    return PitchResolver.from_metadata({"do": str(do_p), "mode": ctx.mode})


def _expand_start_ehm(ehm: str) -> list[str]:
    """Normalize identifier/@start EHM to PitchResolver.apply_start_marker args."""
    raw = ehm.strip()
    if re.fullmatch(r"\\+\d+", raw) or re.fullmatch(r"/+\d+", raw):
        ch = raw[0]
        n = int(raw.lstrip("\\/"))
        raw = ch * n
    if raw in ("", "-"):
        return []
    return [raw]


def _apply_line_ehm(resolver: PitchResolver, ehm: str) -> None:
    """Apply beginanker from a stemregelidentifier (overrides prior @start)."""
    resolver.apply_start_marker(_expand_start_ehm(ehm))


def _apply_start(resolver: PitchResolver, start_rest: str, marker: str) -> None:
    """Parse ``@start S=- A=\\3`` / ``@start Sop=-`` for this voice."""
    mapping: dict[str, str] = {}
    for part in split_directive_assignments(start_rest):
        if "=" not in part:
            continue
        key, _, val = part.partition("=")
        mapping[key.strip()] = val.strip()
    found = resolve_stem_map_key(mapping, marker)
    if found is not None:
        resolver.apply_start_marker(_expand_start_ehm(mapping[found]))
    else:
        resolver.apply_start_marker([])


def _join_lyric_text(syllables: list[str], links: list[bool]) -> str:
    if not syllables:
        return ""
    out = syllables[0]
    for i, syl in enumerate(syllables[1:]):
        sep = "-" if (i < len(links) and links[i]) else " "
        out += sep + syl
    return out


def _syllabic_for_position(
    lpos: LPosition,
    *,
    opens_hyphen: bool,
) -> str:
    """Single MusicXML syllabic for the primary lyric of a non-recite position."""
    if lpos.continues_word and opens_hyphen:
        return "middle"
    if lpos.continues_word:
        return "end"
    if opens_hyphen:
        return "begin"
    return "single"


def _position_to_notes(
    lpos: LPosition,
    vpos: VoicePosition,
    resolver: PitchResolver,
    ctx: StickyContext,
    letter: str,
    *,
    opens_hyphen: bool = False,
    layout: MvsaLayout = "playback",
    line: int = 0,
    marker: str = "",
    lyric_number: int = 1,
    extra_lyric_layers: list[tuple[int, LPosition]] | None = None,
) -> list[NoteEvent]:
    elms = list(lpos.elms) if lpos.elms else ["~"]
    slots = list(vpos.slots) if vpos.slots else ["-"]
    extra_lyric_layers = list(extra_lyric_layers or [])

    if lpos.recite:
        pitch = _resolve_slot(
            slots[0] if slots else "-",
            resolver,
            ctx,
            letter,
            line=line,
            marker=marker,
        )
        # Playback/Coria (M10): één noot per lettergreep.
        # Partituur (R2): bij ≥6 lettergrepen 1-(n-2)-1 met ||O||-midden.
        if lpos.elms:
            base_dur = elm_to_duration(lpos.elms[0])
        else:
            base_dur = elm_to_duration("~")  # kwart per lettergreep / rantrand
        syllables = list(lpos.syllables) if lpos.syllables else [""]
        n = len(syllables)
        out_notes: list[NoteEvent] = []
        for i, syl_text in enumerate(syllables):
            opens = i + 1 < n and i < len(lpos.links) and lpos.links[i]
            continues = (i == 0 and lpos.continues_word) or (
                i > 0 and i - 1 < len(lpos.links) and lpos.links[i - 1]
            )
            if continues and opens:
                syl = "middle"
            elif continues:
                syl = "end"
            elif opens:
                syl = "begin"
            else:
                syl = "single"
            lyrics: list[LyricSyllable] = []
            if syl_text:
                lyrics.append(
                    LyricSyllable(
                        text=syl_text, syllabic=syl, number=lyric_number
                    )
                )
            out_notes.append(
                NoteEvent(
                    pitch=pitch,
                    duration=base_dur,
                    lyrics=lyrics,
                    recite=True,
                )
            )
        for num, plpos in extra_lyric_layers:
            _add_lyric_layer_to_notes(
                out_notes, plpos, opens_hyphen=opens_hyphen, number=num
            )
        if layout == "partituur" and n >= RECITE_PRINT_COLLAPSE_MIN:
            return _collapse_recite_for_partituur(out_notes, edge_dur=base_dur)
        return out_notes

    n = max(len(elms), len(slots))
    while len(elms) < n:
        elms.append("~")
    while len(slots) < n:
        slots.append("-")

    notes: list[NoteEvent] = []
    last_pitch: Pitch | None = None
    primary_syl = _syllabic_for_position(lpos, opens_hyphen=opens_hyphen)

    for si, (elm, slot) in enumerate(zip(elms, slots)):
        pitch = _resolve_slot(
            slot,
            resolver,
            ctx,
            letter,
            last_pitch=last_pitch,
            line=line,
            marker=marker,
        )
        last_pitch = pitch
        dur = elm_to_duration(elm)
        lyrics: list[LyricSyllable] = []
        if si == 0 and lpos.syllables:
            if len(lpos.syllables) == 1:
                syl = primary_syl
                if n > 1 and syl == "single":
                    syl = "begin"
                lyrics.append(
                    LyricSyllable(
                        text=lpos.syllables[0],
                        syllabic=syl,
                        number=lyric_number,
                        extend=n > 1,
                    )
                )
            else:
                text = _join_lyric_text(lpos.syllables, lpos.links)
                syl = primary_syl if primary_syl != "single" else "begin"
                lyrics.append(
                    LyricSyllable(
                        text=text,
                        syllabic=syl,
                        number=lyric_number,
                        extend=n > 1,
                    )
                )
        notes.append(
            NoteEvent(
                pitch=pitch,
                duration=dur,
                lyrics=lyrics,
                slur_start=(n > 1 and si == 0),
                slur_stop=(n > 1 and si == n - 1),
            )
        )
    for num, plpos in extra_lyric_layers:
        _add_lyric_layer_to_notes(
            notes, plpos, opens_hyphen=opens_hyphen, number=num
        )
    # Same-pitch melisma (S13/R7 / M5a). Partituur: I1 ongestipte pack + ties.
    # Playback/Coria: gestipte ELM's behouden; same-pitch → één noot zolang
    # representeerbaar (≤ 28). Langer → I2-tie-keten (MuseScore speelt
    # type/duration-mismatch als heraangeslagen kwarten).
    return _collapse_same_pitch_melisma(
        notes, allow_dotted=(layout == "playback")
    )


def _pitch_equal(a: Pitch, b: Pitch) -> bool:
    return a.step == b.step and a.octave == b.octave and a.alter == b.alter


def _note_divs(ev: NoteEvent) -> int:
    if ev.duration_divisions is not None:
        return ev.duration_divisions
    return ev.duration.divisions_value


_DIVS_TO_DURATION: dict[int, Duration] = {
    1: Duration(note_type="16th", dots=0),
    2: Duration(note_type="eighth", dots=0),
    3: Duration(note_type="eighth", dots=1),
    4: Duration(note_type="quarter", dots=0),
    6: Duration(note_type="quarter", dots=1),
    7: Duration(note_type="quarter", dots=2),  # double-dotted quarter
    8: Duration(note_type="half", dots=0),
    12: Duration(note_type="half", dots=1),
    14: Duration(note_type="half", dots=2),  # double-dotted half
    16: Duration(note_type="whole", dots=0),
    24: Duration(note_type="whole", dots=1),
    28: Duration(note_type="whole", dots=2),  # _.&-&_. same-pitch (7 quarters)
    # Geen 32→breve: MuseScore zet durationType=breve en rekt de maat (corrupt).
}

# Melisma-collapse partituur/MSCZ: alleen ongestipt (MuseScore dropte dots
# bij senza-misura-import → stem-len mismatch → “corrupt score”).
_COLLAPSE_SAFE_DIVS = frozenset({1, 2, 4, 8, 16})
_PACK_ORDER = (16, 8, 4, 2, 1)
# Playback/Coria: gestipte standaardduuren ok (geen MuseScore-import).
_PACK_ORDER_DOTTED = (28, 24, 16, 14, 12, 8, 7, 6, 4, 3, 2, 1)


def _duration_from_divs(divs: int) -> tuple[Duration, int | None]:
    """Map divisions → (Duration, optional duration_divisions override).

    Nooit MusicXML ``type=breve``: MuseScore gebruikt dat als maatbreedte
    (vaak 8/4) en stemmen lopen uit sync. Wel tot dubbelgepunt whole (28).
    """
    if divs in _DIVS_TO_DURATION:
        return _DIVS_TO_DURATION[divs], None
    for note_type, base in (
        ("whole", 16),
        ("half", 8),
        ("quarter", 4),
        ("eighth", 2),
        ("16th", 1),
    ):
        if divs == base:
            return Duration(note_type=note_type, dots=0), None
        if divs == base + base // 2:
            return Duration(note_type=note_type, dots=1), None
        if base >= 4 and divs == base + base // 2 + base // 4:
            return Duration(note_type=note_type, dots=2), None
    return Duration(note_type="quarter", dots=0), divs


def _pack_safe_divs(total: int, *, allow_dotted: bool = False) -> list[int]:
    """Split ``total`` into standaardduuren ≤ dotted-whole.

    Partituur (``allow_dotted=False``): alleen ongestipt ≤ whole (I1+I2).
    Playback: gestipte waarden toegestaan.
    """
    if total <= 0:
        return []
    parts: list[int] = []
    remaining = total
    order = _PACK_ORDER_DOTTED if allow_dotted else _PACK_ORDER
    for size in order:
        while remaining >= size:
            parts.append(size)
            remaining -= size
    return parts


def _pack_same_pitch_run(
    run: list[NoteEvent], *, allow_dotted: bool = False
) -> list[NoteEvent]:
    """One same-pitch melisma run → one note or a tie-chain (I2)."""
    first = run[0]
    total = sum(_note_divs(n) for n in run)

    if allow_dotted:
        # Coria stript ``<tie>``: prefer one sounding note when representable.
        # Keep intentional dotted ELM slots (``_.``) when the run is already one note.
        if len(run) == 1:
            return list(run)
        dur, div_override = _duration_from_divs(total)
        if div_override is None:
            # ≤ double-dotted whole: één MusicXML-duur, type en duration matchen.
            return [
                NoteEvent(
                    pitch=first.pitch,
                    duration=dur,
                    lyrics=list(first.lyrics),
                    recite=first.recite,
                    spacer=first.spacer,
                    duration_divisions=None,
                    stemless=first.stemless,
                )
            ]
        # Langer dan één standaardduur (bijv. 8 kwarten = 32): nooit
        # ``type=quarter`` + ``duration=32`` — MuseScore heraanslaat elke
        # kwart. Fall through naar I2-tie-keten (ongestipt ≤ whole).
        # Coria kan bij tie-joins heraanslaan; beter dan per-kwart chops.

    parts = _pack_safe_divs(total, allow_dotted=False)
    if not parts:
        return [
            NoteEvent(
                pitch=first.pitch,
                duration=first.duration,
                lyrics=list(first.lyrics),
                recite=first.recite,
                spacer=first.spacer,
                duration_divisions=first.duration_divisions,
                stemless=first.stemless,
            )
        ]
    out: list[NoteEvent] = []
    for i, divs in enumerate(parts):
        dur, div_override = _duration_from_divs(divs)
        lyrics = list(first.lyrics) if i == 0 else []
        out.append(
            NoteEvent(
                pitch=first.pitch,
                duration=dur,
                lyrics=lyrics,
                recite=first.recite,
                spacer=first.spacer,
                duration_divisions=div_override,
                stemless=first.stemless,
                tie_start=(i < len(parts) - 1),
                tie_stop=(i > 0),
            )
        )
    return out


def _collapse_same_pitch_melisma(
    notes: list[NoteEvent], *, allow_dotted: bool = False
) -> list[NoteEvent]:
    """Same-pitch melisma → collapse and/or tie-keten (S13/R7).

    *allow_dotted* (playback/Coria): behoud gestipte ELM's; same-pitch → één
    noot zolang de som ≤ dubbelgepunt whole (28). Langer → I2-tie-keten
    (geen ``type``/``duration``-mismatch; MuseScore heraanslaat anders).
    Partituur/MSCZ (default): **I1** ongestipt ≤ whole; **I2** tie-keten.

    Slur alleen bij toonwissels binnen het melisma; pure hold → ties
    (partituur, of playback bij overflow) of één noot (playback ≤ 28).
    """
    if len(notes) <= 1:
        return notes

    runs: list[list[NoteEvent]] = []
    for note in notes:
        if runs and _pitch_equal(runs[-1][-1].pitch, note.pitch):
            runs[-1].append(note)
        else:
            runs.append([note])

    packed: list[NoteEvent] = []
    for run in runs:
        packed.extend(_pack_same_pitch_run(run, allow_dotted=allow_dotted))

    n = len(packed)
    if n == 1:
        only = packed[0]
        lyrics = [
            LyricSyllable(
                text=ly.text,
                syllabic=ly.syllabic if ly.syllabic != "begin" else "single",
                number=ly.number,
                extend=False,
            )
            for ly in only.lyrics
        ]
        return [
            NoteEvent(
                pitch=only.pitch,
                duration=only.duration,
                lyrics=lyrics,
                recite=only.recite,
                spacer=only.spacer,
                duration_divisions=only.duration_divisions,
                stemless=only.stemless,
                tie_start=only.tie_start,
                tie_stop=only.tie_stop,
            )
        ]

    use_slur = any(
        not _pitch_equal(packed[i].pitch, packed[i + 1].pitch)
        for i in range(n - 1)
    )
    out: list[NoteEvent] = []
    for i, note in enumerate(packed):
        lyrics = list(note.lyrics)
        if i == 0 and lyrics:
            lyrics = [
                LyricSyllable(
                    text=ly.text,
                    syllabic="begin" if ly.syllabic == "single" else ly.syllabic,
                    number=ly.number,
                    extend=True,
                )
                for ly in lyrics
            ]
        elif i > 0:
            lyrics = []
        out.append(
            NoteEvent(
                pitch=note.pitch,
                duration=note.duration,
                lyrics=lyrics,
                recite=note.recite,
                spacer=note.spacer,
                duration_divisions=note.duration_divisions,
                stemless=note.stemless,
                slur_start=(use_slur and i == 0),
                slur_stop=(use_slur and i == n - 1),
                tie_start=note.tie_start,
                tie_stop=note.tie_stop,
            )
        )
    return out


def _collapse_recite_for_partituur(
    notes: list[NoteEvent],
    *,
    edge_dur: Duration,
) -> list[NoteEvent]:
    """Printmodel 1-(n-2)-1 met spacers (model A) voor ``n ≥ RECITE_PRINT_COLLAPSE_MIN``.

    Eerste en laatste lettergreep: zichtbare randnoot (``edge_dur``).
    Midden: één stokloze breve (``||O||``) met de **eerste** midden-lettergreep
    gecentreerd; overige midden-lettergrepen elk op een spacer-noot (onzichtbare
    kop, **zichtbare** lyric — geen ``print-object=no`` op de hele noot).
    Elke slot duurt ``edge_dur``, zodat de speelduur = ``n ×`` rand = Coria.
    Geen melisma-extender onder de recite-body.
    """
    n = len(notes)
    if n < RECITE_PRINT_COLLAPSE_MIN:
        return notes
    first = notes[0]
    last = notes[-1]
    middle = notes[1:-1]
    # Midden: stokloos + breve-kop in MSCZ; metrisch = edge (geen type=breve).
    out: list[NoteEvent] = [
        NoteEvent(
            pitch=first.pitch,
            duration=edge_dur,
            lyrics=list(first.lyrics),
            recite=True,
        ),
        NoteEvent(
            pitch=middle[0].pitch,
            duration=edge_dur,
            lyrics=list(middle[0].lyrics),
            recite=True,
            stemless=True,
            breve_head=True,
        ),
    ]
    for body in middle[1:]:
        out.append(
            NoteEvent(
                pitch=body.pitch,
                duration=edge_dur,
                lyrics=list(body.lyrics),
                recite=True,
                spacer=True,
                stemless=True,
            )
        )
    out.append(
        NoteEvent(
            pitch=last.pitch,
            duration=edge_dur,
            lyrics=list(last.lyrics),
            recite=True,
        )
    )
    return out


def _apply_volta_ab_ac(
    volta,
    blok_measure_range: dict[str, tuple[int, int]],
    measure_left_styles: list[str | None],
    bar_styles: list[str],
    ending_start: list[str | None],
    ending_stop: list[str | None],
) -> None:
    """Zet forward/backward-repeat + endings voor ``VoltaAbAc`` op maat-arrays."""
    ra = blok_measure_range.get(volta.a)
    rb = blok_measure_range.get(volta.b)
    rc = blok_measure_range.get(volta.c)
    if ra is None or rb is None or rc is None:
        return
    a0, _a1 = ra
    b0, b1 = rb
    c0, c1 = rc
    measure_left_styles[a0] = "repeat-start"
    ending_start[b0] = volta.first_ending_numbers
    ending_stop[b1] = volta.first_ending_numbers
    bar_styles[b1] = "repeat-end"
    ending_start[c0] = volta.second_ending_number
    ending_stop[c1] = volta.second_ending_number


def _apply_repeat_nav(
    repeat,
    blok_measure_range: dict[str, tuple[int, int]],
    measure_left_styles: list[str | None],
    bar_styles: list[str],
    repeat_times: list[int | None],
) -> None:
    """``|: start … end :|`` met optioneel ``times`` > 2."""
    rs = blok_measure_range.get(repeat.start_id)
    re_ = blok_measure_range.get(repeat.end_id)
    if rs is None or re_ is None:
        return
    measure_left_styles[rs[0]] = "repeat-start"
    bar_styles[re_[1]] = "repeat-end"
    if repeat.times > 2:
        repeat_times[re_[1]] = repeat.times


def _apply_ds_al_fine(
    ds,
    blok_measure_range: dict[str, tuple[int, int]],
    nav_marks: list[list[str]],
) -> None:
    """Segno/Fine + D.S. of D.C. al Fine op maat-nav-marks."""
    rs = blok_measure_range.get(ds.segno_id)
    rf = blok_measure_range.get(ds.fine_id)
    rd = blok_measure_range.get(ds.ds_after_id)
    if rs is None or rf is None or rd is None:
        return
    if not ds.use_da_capo:
        nav_marks[rs[0]].append("segno")
    nav_marks[rf[1]].append("fine")
    jump = "dc_al_fine" if ds.use_da_capo else "ds_al_fine"
    nav_marks[rd[1]].append(jump)


def _apply_ds_al_coda(
    coda,
    blok_measure_range: dict[str, tuple[int, int]],
    nav_marks: list[list[str]],
) -> None:
    """Segno / To Coda / Coda + D.S. of D.C. al Coda op maat-nav-marks."""
    rs = blok_measure_range.get(coda.segno_id)
    rt = blok_measure_range.get(coda.to_coda_id)
    rd = blok_measure_range.get(coda.ds_after_id)
    rc = blok_measure_range.get(coda.coda_id)
    if rs is None or rt is None or rd is None or rc is None:
        return
    if not coda.use_da_capo:
        nav_marks[rs[0]].append("segno")
    nav_marks[rt[1]].append("to_coda")
    jump = "dc_al_coda" if coda.use_da_capo else "ds_al_coda"
    nav_marks[rd[1]].append(jump)
    nav_marks[rc[0]].append("coda")


def _emit_nav_marks(out: list[str], marks: list[str]) -> None:
    """MusicXML-directions voor segno / Fine / Coda / D.S.|D.C. jumps."""
    for mark in marks:
        if mark == "segno":
            out.append(
                '<direction placement="above">'
                "<direction-type><segno/></direction-type>"
                '<sound segno="segno"/>'
                "</direction>"
            )
        elif mark == "fine":
            out.append(
                '<direction placement="above">'
                '<direction-type><words font-weight="bold">Fine</words>'
                "</direction-type>"
                '<sound fine="yes"/>'
                "</direction>"
            )
        elif mark == "ds_al_fine":
            out.append(
                '<direction placement="above">'
                '<direction-type><words font-weight="bold">D.S. al Fine</words>'
                "</direction-type>"
                '<sound dalsegno="segno"/>'
                "</direction>"
            )
        elif mark == "dc_al_fine":
            out.append(
                '<direction placement="above">'
                '<direction-type><words font-weight="bold">D.C. al Fine</words>'
                "</direction-type>"
                '<sound dacapo="yes"/>'
                "</direction>"
            )
        elif mark == "to_coda":
            out.append(
                '<direction placement="above">'
                '<direction-type><words font-weight="bold">To Coda</words>'
                "</direction-type>"
                '<sound tocoda="coda"/>'
                "</direction>"
            )
        elif mark == "coda":
            out.append(
                '<direction placement="above">'
                "<direction-type><coda/></direction-type>"
                '<sound coda="coda"/>'
                "</direction>"
            )
        elif mark == "ds_al_coda":
            out.append(
                '<direction placement="above">'
                '<direction-type><words font-weight="bold">D.S. al Coda</words>'
                "</direction-type>"
                '<sound dalsegno="segno"/>'
                "</direction>"
            )
        elif mark == "dc_al_coda":
            out.append(
                '<direction placement="above">'
                '<direction-type><words font-weight="bold">D.C. al Coda</words>'
                "</direction-type>"
                '<sound dacapo="yes"/>'
                "</direction>"
            )


def _mvsa_bar_to_style(token: str) -> str:
    """MVSA-maatstreep → interne bar-code voor MusicXML-export.

    Codes:
    - ``regular`` / ``light-light`` / ``none`` — alleen streepstijl
    - ``repeat-start`` — ``|:`` (forward-repeat als *linker* streep van de volgende maat)
    - ``repeat-end`` — ``:|`` (backward-repeat rechts)
    - ``repeat-end-section`` — ``:||`` (sectie-einde + backward-repeat)
    """
    t = (token or "|").strip()
    if t == "|:":
        return "repeat-start"
    if t == ":|":
        return "repeat-end"
    if t == ":||":
        return "repeat-end-section"
    if t == "||":
        return "light-light"
    return "regular"


def _is_section_end_bar(style: str) -> bool:
    """``||`` / ``:||`` (en afgeleide pauzestrepen) — dubbele streep / Coria-pauze."""
    return style in ("light-light", "repeat-end-section")


def _right_bar_style(mi: int, n_measures: int, bar_styles: list[str]) -> str:
    """Sectie-``||`` → ``light-light``; cue-spacer → ``none``; slot = ``light-heavy``."""
    raw = bar_styles[mi] if 0 <= mi < len(bar_styles) else "regular"
    if raw == "repeat-start":
        # Start-herhaling hoort links op de *volgende* maat; rechts hier gewoon.
        raw = "regular"
    elif raw == "repeat-end":
        return "light-heavy"
    elif raw == "repeat-end-section":
        return "light-light"
    if raw in ("light-light", "none"):
        return raw
    if mi == n_measures - 1:
        return "light-heavy"
    return raw


def _emit_measure_barlines(
    out: list[str],
    mi: int,
    n_measures: int,
    bar_styles: list[str],
    *,
    left_style: str | None = None,
    pauzes: list[bool] | None = None,
    ending_start: str | None = None,
    ending_stop: str | None = None,
    repeat_times: int | None = None,
) -> None:
    """Linker forward-repeat (na ``|:``) + rechter streep (eventueel backward).

    Linker streep komt van ``start_bar`` (leidende ``|:`` zonder lege maat) of
    van de vorige maat die op ``|:`` eindigde. Pauzematen tussen ``|:`` en de
    koormaat worden overgeslagen. Optioneel MusicXML-``<ending>`` (volta).
    """
    need_forward = left_style == "repeat-start"
    if not need_forward:
        j = mi - 1
        while j >= 0 and pauzes and j < len(pauzes) and pauzes[j]:
            j -= 1
        prev = bar_styles[j] if j >= 0 and j < len(bar_styles) else None
        need_forward = prev == "repeat-start"
    left_bits: list[str] = []
    if need_forward:
        left_bits.append("<bar-style>heavy-light</bar-style>")
        left_bits.append('<repeat direction="forward"/>')
    if ending_start:
        left_bits.append(f'<ending number="{ending_start}" type="start"/>')
    if left_bits:
        out.append(f'<barline location="left">{"".join(left_bits)}</barline>')
    raw = bar_styles[mi] if 0 <= mi < len(bar_styles) else "regular"
    style = _right_bar_style(mi, n_measures, bar_styles)
    right_bits: list[str] = [f"<bar-style>{style}</bar-style>"]
    if raw in ("repeat-end", "repeat-end-section"):
        if repeat_times and repeat_times > 2:
            right_bits.append(
                f'<repeat direction="backward" times="{repeat_times}"/>'
            )
        else:
            right_bits.append('<repeat direction="backward"/>')
    if ending_stop:
        right_bits.append(f'<ending number="{ending_stop}" type="stop"/>')
    out.append(f'<barline location="right">{"".join(right_bits)}</barline>')


def _resolve_slot(
    token: str,
    resolver: PitchResolver,
    ctx: StickyContext,
    letter: str,
    *,
    last_pitch: Pitch | None = None,
    line: int = 0,
    marker: str = "",
) -> Pitch:
    tok = token.strip()
    if tok in ("-", "~"):
        if last_pitch is not None:
            return last_pitch
        return resolver.current_pitch

    note_m = _NOTE_RE.fullmatch(tok)
    deg_m = _DEGREE_RE.fullmatch(tok)
    if note_m and not deg_m:
        step = note_m.group(1).upper()
        alter_s = note_m.group(2) or ""
        oct_s = note_m.group(3)
        suffix = note_m.group(4) or ""
        alter = 0.0
        if alter_s == "bb":
            alter = -2.0
        elif alter_s == "b":
            alter = -1.0
        elif alter_s == "#":
            alter = 1.0
        oct_delta = 0
        if suffix in ("-", "+"):
            oct_delta = -1 if suffix == "-" else 1
        elif suffix:
            oct_delta = int(suffix)
        if oct_s is not None:
            pitch = Pitch(step=step, octave=int(oct_s) + oct_delta, alter=alter)
        else:
            # a–g zonder cijfer: do-octaaf [schrijf-do, +12) — ``c`` bij F4 = C5.
            pitch = pitch_in_do_octave(
                resolver._do, step, alter, oct_delta=oct_delta
            )
        resolver.set_absolute_pitch(pitch)
        return pitch

    if deg_m:
        prefix_acc = deg_m.group(1) or ""
        name = deg_m.group(2).lower()
        # Branch A: oct then optional acc  |  Branch B: acc then optional oct
        oct_a, acc_a = deg_m.group(3), deg_m.group(4)
        acc_b, oct_b = deg_m.group(5), deg_m.group(6)
        if acc_b is not None or (oct_b is not None and oct_a is None and acc_a is None):
            oct_off = oct_b or ""
            trail_acc = acc_b or ""
        else:
            oct_off = oct_a or ""
            trail_acc = acc_a or ""
        chrom = prefix_acc or trail_acc
        if name == "so":
            name = "sol"
        if name == "si":
            name = "ti"
        idx = _DEGREE_INDEX[name]
        # resolver._do is already schrijf-do (@do + @oct); suffix is extra only
        shift = 0
        if oct_off in ("-", "+"):
            shift = -1 if oct_off == "-" else 1
        elif oct_off:
            shift = int(oct_off)
        if chrom == "#":
            chrom_alter = 1.0
        elif chrom == "b":
            chrom_alter = -1.0
        else:
            chrom_alter = 0.0
        base = degree_to_pitch(resolver._do, idx + 7 * shift, resolver._intervals)
        pitch = (
            Pitch(step=base.step, octave=base.octave, alter=base.alter + chrom_alter)
            if chrom_alter
            else base
        )
        resolver._degree = idx + 7 * shift
        resolver._last_sounding = pitch
        return pitch

    if _EHM_RE.fullmatch(tok):
        return resolver.resolve_ehm(tok)

    try:
        pitch = parse_pitch_string(tok[0].upper() + tok[1:] if tok[0].islower() else tok)
        resolver.set_absolute_pitch(pitch)
        return pitch
    except ValueError as exc:
        where = f"{marker}: " if marker else ""
        raise MvsaExportError(
            f"{where}onbekende hoogte-token {tok!r}",
            line=line,
        ) from exc


def wrap_tekst_at_ellipsis(text: str) -> str:
    """Lange cue: vanaf eerste ``...`` een nieuwe regel (``...`` op regel 2)."""
    idx = text.find("...")
    if idx <= 0:
        return text
    before = text[:idx].rstrip()
    after = text[idx:].lstrip()
    if not before:
        return text
    return f"{before}\n{after}"


def estimate_cue_width_tenths(texts: list[str]) -> int:
    """MusicXML measure ``width`` in tenths — ruim genoeg voor de cue-regels."""
    lines: list[str] = []
    for t in texts:
        lines.extend(t.splitlines() or [t])
    max_len = max((len(line) for line in lines), default=0)
    return max(80, max_len * 14)


def _prepare_partituur_tekst_frames(
    bar_styles: list[str],
    measure_staff_texts: list[list[str]],
    measure_new_system: list[bool],
    measure_widths: list[int | None],
) -> None:
    """Mid-flow ``@tekst``: vorige maat dubbele streep; maatbreedte voor de cue.

    Herhalingen (``:|``) blijven ``repeat-end`` (light-heavy + backward).
    Geen HBox/spacermaat: MuseScore tekent daar mid-systeem-accolades of
    lege balklijnen. Scheiding = ``‖`` + SystemText (+ optioneel ``@mscz-newline``).
    """
    n = len(measure_staff_texts)
    while len(bar_styles) < n:
        bar_styles.append("regular")
    while len(measure_new_system) < n:
        measure_new_system.append(False)
    while len(measure_widths) < n:
        measure_widths.append(None)

    for i in range(n):
        texts = measure_staff_texts[i]
        if not texts:
            continue
        measure_widths[i] = estimate_cue_width_tenths(texts)
        starts_system = i == 0 or measure_new_system[i]
        if starts_system:
            continue
        if i > 0:
            prev = bar_styles[i - 1]
            if prev not in (
                "repeat-start",
                "repeat-end",
                "repeat-end-section",
                "light-light",
                "none",
            ):
                bar_styles[i - 1] = "light-light"


def _emit_staff_text_directions(out: list[str], texts: list[str]) -> None:
    """Staff-tekst boven de balk; newlines in ``words`` voor wrap bij ``...``."""
    for text in texts:
        out.append('<direction placement="above">')
        out.append("<direction-type>")
        # Escape per regel; behoud echte newlines in de XML-tekstnode.
        escaped = escape(text)
        out.append(f'<words justify="left" default-x="0">{escaped}</words>')
        out.append("</direction-type>")
        out.append("</direction>")


# Zelfde default als eenstemmige VSA (``tempo="130"`` / ``muziek.tempo``).
DEFAULT_TEMPO_BPM = 130


def _parse_tempo_bpm(meta: dict[str, str | None] | None) -> int:
    """BPM uit document-meta ``tempo`` (``@tempo``); default ``DEFAULT_TEMPO_BPM``."""
    raw = ((meta or {}).get("tempo") or "").strip()
    if not raw:
        return DEFAULT_TEMPO_BPM
    try:
        bpm = int(raw)
    except ValueError:
        return DEFAULT_TEMPO_BPM
    if bpm < 1 or bpm > 999:
        return DEFAULT_TEMPO_BPM
    return bpm


def _emit_tempo_direction(out: list[str], bpm: int) -> None:
    """Playback-``sound tempo`` (kwart = BPM); metronoom onzichtbaar op blad/PDF.

    ``print-object="no"`` houdt de markering weg uit MuseScore-partituur en
    PDF; afspelen (audio/Coria) gebruikt nog steeds ``sound tempo``.
    """
    out.append('<direction placement="above" print-object="no">')
    out.append("<direction-type>")
    out.append('<metronome parentheses="no">')
    out.append("<beat-unit>quarter</beat-unit>")
    out.append(f"<per-minute>{bpm}</per-minute>")
    out.append("</metronome>")
    out.append("</direction-type>")
    out.append(f'<sound tempo="{bpm}"/>')
    out.append("</direction>")


def _insert_playback_pauze_measures(
    voice_measures: dict[str, list[list[NoteEvent]]],
    bar_styles: list[str],
    measure_staff_texts: list[list[str]],
    measure_left_styles: list[str | None] | None = None,
    measure_tempos: list[int | None] | None = None,
) -> list[bool]:
    """``[PAUZE]``-maten voor Coria: na sectie-einde én vóór mid-flow ``@tekst``.

    - Na ``||`` / ``:||`` (``light-light`` / ``repeat-end-section``).
    - Vóór een koormaat met ``@tekst`` als die niet de eerste maat is en de
      vorige maat nog geen sectie-eindestreep had (geen dubbele pauze).
    Cue-teksten van de volgende koormaat verhuizen naar de pauzemaat.
    Tempo-wissels blijven op de koormaat (pauzemaat krijgt ``None``).
    """
    n = max(
        len(bar_styles),
        len(measure_staff_texts),
        max((len(ms) for ms in voice_measures.values()), default=0),
    )
    while len(bar_styles) < n:
        bar_styles.append("regular")
    while len(measure_staff_texts) < n:
        measure_staff_texts.append([])
    if measure_left_styles is not None:
        while len(measure_left_styles) < n:
            measure_left_styles.append(None)
    if measure_tempos is not None:
        while len(measure_tempos) < n:
            measure_tempos.append(None)
    for measures in voice_measures.values():
        while len(measures) < n:
            measures.append([])

    insert_after: set[int] = {
        i for i in range(n - 1) if _is_section_end_bar(bar_styles[i])
    }
    # Mid-flow @tekst: pauze vóór die koormaat (= insert na i-1), tenzij
    # sectie-einde die pauze al triggert.
    for i in range(1, n):
        if not measure_staff_texts[i]:
            continue
        if _is_section_end_bar(bar_styles[i - 1]):
            continue
        insert_after.add(i - 1)

    pauze = [False] * n
    for i in sorted(insert_after, reverse=True):
        # Cue van de volgende koormaat → op de pauzemaat.
        cues = list(measure_staff_texts[i + 1])
        measure_staff_texts[i + 1] = []
        for measures in voice_measures.values():
            measures.insert(i + 1, [])
        bar_styles.insert(i + 1, "light-light")
        measure_staff_texts.insert(i + 1, cues)
        if measure_left_styles is not None:
            measure_left_styles.insert(i + 1, None)
        if measure_tempos is not None:
            measure_tempos.insert(i + 1, None)
        pauze.insert(i + 1, True)
    return pauze


def _emit_cue_gap_rest(out: list[str], *, voice: int | None = None) -> None:
    """Onzichtbare minimale rust voor een cue-spacermaat."""
    voice_xml = f"<voice>{voice}</voice>" if voice is not None else ""
    out.append(
        f'<note print-object="no"><rest/><duration>{CUE_GAP_DURATION_DIVS}</duration>'
        f"{voice_xml}<type>{CUE_GAP_NOTE_TYPE}</type></note>"
    )


def _emit_pauze_rest(out: list[str], *, with_lyric: bool) -> None:
    """Whole-rest + optioneel ``[PAUZE]``-lyric (Coria-playback)."""
    lyric_xml = ""
    if with_lyric:
        lyric_xml = (
            f'<lyric number="1"><syllabic>single</syllabic>'
            f"<text>{PAUSE_LYRIC}</text></lyric>"
        )
    out.append(
        f"<note><rest/><duration>{PAUSE_DURATION_DIVS}</duration>"
        f"<type>whole</type>{lyric_xml}</note>"
    )


def _emit_identification(out: list[str], meta: dict[str, str | None] | None) -> None:
    """MusicXML ``<identification>``: creators, rights, source, toon."""
    if not meta:
        return
    creators: list[tuple[str, str]] = []
    for key, mxml_type in (
        ("composer", "composer"),
        ("tekstdichter", "lyricist"),
        ("arrangeur", "arranger"),
        ("vertaler", "translator"),
    ):
        value = (meta.get(key) or "").strip()
        if value:
            creators.append((mxml_type, value))
    rights = (meta.get("copyright") or "").strip()
    bib = (meta.get("bibliotheek_id") or "").strip()
    if bib:
        rights = (
            f"{rights}\nBibliotheek-id: {bib}".strip()
            if rights
            else f"Bibliotheek-id: {bib}"
        )
    source = (meta.get("bron") or "").strip()
    toon = (meta.get("toon") or "").strip()
    if not creators and not rights and not source and not toon:
        return
    out.append("<identification>")
    for mxml_type, value in creators:
        out.append(f'<creator type="{mxml_type}">{escape(value)}</creator>')
    if rights:
        out.append(f"<rights>{escape(rights)}</rights>")
    if source:
        out.append(f"<source>{escape(source)}</source>")
    if toon:
        out.append("<miscellaneous>")
        out.append(
            f'<miscellaneous-field name="tone">{escape(toon)}</miscellaneous-field>'
        )
        out.append("</miscellaneous>")
    out.append("</identification>")


def _emit_work_and_movement(
    out: list[str], title: str, meta: dict[str, str | None] | None
) -> None:
    out.append(f"<work><work-title>{escape(title)}</work-title></work>")
    ondertitel = ((meta or {}).get("ondertitel") or "").strip()
    if ondertitel:
        out.append(f"<movement-title>{escape(ondertitel)}</movement-title>")


def _emit_playback_piano_midi(
    out: list[str],
    part_id: str,
    channel: int,
    *,
    volume: str = _PLAYBACK_MIDI_VOLUME,
) -> None:
    """Canonieke piano-MIDI voor één Coria/playback-part (checklist M8)."""
    instrument_id = f"{part_id}-I1"
    out.append(f'<score-instrument id="{instrument_id}">')
    out.append("<instrument-name></instrument-name>")
    out.append(f"<instrument-sound>{_PLAYBACK_MIDI_SOUND}</instrument-sound>")
    out.append("</score-instrument>")
    out.append(f'<midi-device id="{instrument_id}" port="1"/>')
    out.append(f'<midi-instrument id="{instrument_id}">')
    out.append(f"<midi-channel>{channel}</midi-channel>")
    out.append(f"<midi-program>{_PLAYBACK_MIDI_PROGRAM}</midi-program>")
    out.append(f"<volume>{volume}</volume>")
    out.append(f"<pan>{_PLAYBACK_MIDI_PAN}</pan>")
    out.append("</midi-instrument>")


def _emit_score_playback(
    voice_measures: dict[str, list[list[NoteEvent]]],
    *,
    title: str,
    context: StickyContext,
    bar_styles: list[str] | None = None,
    measure_left_styles: list[str | None] | None = None,
    measure_staff_texts: list[list[str]] | None = None,
    measure_new_system: list[bool] | None = None,
    measure_cue_gap: list[bool] | None = None,
    measure_pauze: list[bool] | None = None,
    measure_tempos: list[int | None] | None = None,
    meta: dict[str, str | None] | None = None,
    parts: list[dict] | None = None,
    extra_parts: list[dict] | None = None,
) -> str:
    do_p = parse_pitch_string(context.do)
    fifths = key_fifths(do_p, context.mode)
    n_measures = max((len(ms) for ms in voice_measures.values()), default=0)
    styles = list(bar_styles or [])
    left_styles = list(measure_left_styles or [])
    staff_texts = list(measure_staff_texts or [])
    new_systems = list(measure_new_system or [])
    cue_gaps = list(measure_cue_gap or [])
    pauzes = list(measure_pauze or [])
    tempos = list(measure_tempos or [])
    while len(left_styles) < n_measures:
        left_styles.append(None)
    while len(staff_texts) < n_measures:
        staff_texts.append([])
    while len(new_systems) < n_measures:
        new_systems.append(False)
    while len(cue_gaps) < n_measures:
        cue_gaps.append(False)
    while len(pauzes) < n_measures:
        pauzes.append(False)
    while len(tempos) < n_measures:
        tempos.append(None)

    emit_parts: list[dict] = list(parts) if parts is not None else list(PARTS)
    if extra_parts:
        emit_parts = emit_parts + list(extra_parts)
    if tempos and tempos[0] is None:
        tempos[0] = _parse_tempo_bpm(meta)

    out: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN"',
        '  "http://www.musicxml.org/dtds/partwise.dtd">',
        '<score-partwise version="3.1">',
    ]
    _emit_work_and_movement(out, title, meta)
    _emit_identification(out, meta)
    out.append("<part-list>")
    for channel, part in enumerate(emit_parts, start=1):
        out.append(f'<score-part id="{part["id"]}">')
        out.append(f"<part-name>{part['name']}</part-name>")
        out.append(f"<part-abbreviation>{part['abbr']}</part-abbreviation>")
        vol = (
            _HULPTEKST_VOLUME
            if re.search(r"h\d+$", str(part.get("voice", "")))
            else _PLAYBACK_MIDI_VOLUME
        )
        _emit_playback_piano_midi(out, part["id"], channel, volume=vol)
        out.append("</score-part>")
    out.append("</part-list>")

    for part_idx, part in enumerate(emit_parts):
        voice = part["voice"]
        measures = list(voice_measures.get(voice, []))
        while len(measures) < n_measures:
            measures.append([])
        out.append(f'<part id="{part["id"]}">')
        for mi in range(n_measures):
            events = measures[mi]
            out.append(f'<measure number="{mi + 1}">')
            if mi == 0:
                clef_sign, clef_line = part["clef"]
                out.append("<attributes>")
                out.append("<divisions>4</divisions>")
                out.append(f"<key><fifths>{fifths}</fifths></key>")
                out.append("<time><senza-misura/></time>")
                out.append(
                    f"<clef><sign>{clef_sign}</sign><line>{clef_line}</line></clef>"
                )
                out.append("</attributes>")
            # Tempo alleen op de bovenste part (wijzigt afspeelsnelheid).
            if part_idx == 0 and tempos[mi] is not None:
                _emit_tempo_direction(out, tempos[mi])
            # Staff-tekst alleen op de bovenste balk (Soprano).
            if part["voice"] == "S":
                if new_systems[mi]:
                    out.append('<print new-system="yes"/>')
                if staff_texts[mi]:
                    _emit_staff_text_directions(out, staff_texts[mi])
            if pauzes[mi]:
                # Lyric op alle parts (Coria toont het niet onder rust; wel voor
                # toekomstige eigen player / inspectie).
                _emit_pauze_rest(out, with_lyric=True)
            elif cue_gaps[mi]:
                _emit_cue_gap_rest(out)
            elif not events:
                out.append(
                    '<note><rest/><duration>16</duration><type>whole</type></note>'
                )
            else:
                for ev in events:
                    _emit_note(out, ev, fifths=fifths)
            _emit_measure_barlines(
                out,
                mi,
                n_measures,
                styles,
                left_style=left_styles[mi],
                pauzes=pauzes,
            )
            out.append("</measure>")
        out.append("</part>")
    out.append("</score-partwise>")
    return "\n".join(out)


def _emit_score_partituur(
    voice_measures: dict[str, list[list[NoteEvent]]],
    *,
    title: str,
    context: StickyContext,
    bar_styles: list[str] | None = None,
    measure_left_styles: list[str | None] | None = None,
    measure_staff_texts: list[list[str]] | None = None,
    measure_new_system: list[bool] | None = None,
    measure_cue_gap: list[bool] | None = None,
    measure_widths: list[int | None] | None = None,
    measure_ending_start: list[str | None] | None = None,
    measure_ending_stop: list[str | None] | None = None,
    measure_repeat_times: list[int | None] | None = None,
    measure_nav_marks: list[list[str]] | None = None,
    measure_tempos: list[int | None] | None = None,
    meta: dict[str, str | None] | None = None,
) -> str:
    """Twee balken SA/TB: voice 1 (S/T) stok omhoog, voice 2 (A/B) stok omlaag."""
    do_p = parse_pitch_string(context.do)
    fifths = key_fifths(do_p, context.mode)
    n_measures = max((len(ms) for ms in voice_measures.values()), default=0)
    styles = list(bar_styles or [])
    left_styles = list(measure_left_styles or [])
    staff_texts = list(measure_staff_texts or [])
    new_systems = list(measure_new_system or [])
    cue_gaps = list(measure_cue_gap or [])
    widths = list(measure_widths or [])
    end_starts = list(measure_ending_start or [])
    end_stops = list(measure_ending_stop or [])
    rep_times = list(measure_repeat_times or [])
    navs = list(measure_nav_marks or [])
    tempos = list(measure_tempos or [])
    while len(left_styles) < n_measures:
        left_styles.append(None)
    while len(staff_texts) < n_measures:
        staff_texts.append([])
    while len(new_systems) < n_measures:
        new_systems.append(False)
    while len(cue_gaps) < n_measures:
        cue_gaps.append(False)
    while len(widths) < n_measures:
        widths.append(None)
    while len(end_starts) < n_measures:
        end_starts.append(None)
    while len(end_stops) < n_measures:
        end_stops.append(None)
    while len(rep_times) < n_measures:
        rep_times.append(None)
    while len(navs) < n_measures:
        navs.append([])
    while len(tempos) < n_measures:
        tempos.append(None)
    if tempos and tempos[0] is None:
        tempos[0] = _parse_tempo_bpm(meta)

    out: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN"',
        '  "http://www.musicxml.org/dtds/partwise.dtd">',
        '<score-partwise version="3.1">',
    ]
    _emit_work_and_movement(out, title, meta)
    _emit_identification(out, meta)
    out.append("<part-list>")
    out.append(
        '<part-group type="start" number="1">'
        "<group-symbol>bracket</group-symbol></part-group>"
    )
    for part in PARTITUUR_PARTS:
        out.append(f'<score-part id="{part["id"]}">')
        out.append("<part-name></part-name>")
        out.append("<part-abbreviation></part-abbreviation>")
        out.append("</score-part>")
    out.append('<part-group type="stop" number="1"/>')
    out.append("</part-list>")

    for part in PARTITUUR_PARTS:
        upper_ms = list(voice_measures.get(part["upper"], []))
        lower_ms = list(voice_measures.get(part["lower"], []))
        while len(upper_ms) < n_measures:
            upper_ms.append([])
        while len(lower_ms) < n_measures:
            lower_ms.append([])
        with_lyrics = part["upper"] == "S"
        top_staff = part["upper"] == "S"
        out.append(f'<part id="{part["id"]}">')
        for mi in range(n_measures):
            upper = upper_ms[mi]
            lower = lower_ms[mi]
            wattr = f' width="{widths[mi]}"' if widths[mi] else ""
            out.append(f'<measure number="{mi + 1}"{wattr}>')
            if mi == 0:
                clef_sign, clef_line = part["clef"]
                out.append("<attributes>")
                out.append("<divisions>4</divisions>")
                out.append(f"<key><fifths>{fifths}</fifths></key>")
                out.append("<time><senza-misura/></time>")
                out.append(
                    f"<clef><sign>{clef_sign}</sign><line>{clef_line}</line></clef>"
                )
                out.append("</attributes>")
            if top_staff and tempos[mi] is not None:
                _emit_tempo_direction(out, tempos[mi])
            if top_staff:
                if new_systems[mi]:
                    out.append('<print new-system="yes"/>')
                if navs[mi]:
                    _emit_nav_marks(out, navs[mi])
                if staff_texts[mi]:
                    _emit_staff_text_directions(out, staff_texts[mi])
            if cue_gaps[mi]:
                _emit_cue_gap_rest(out, voice=1)
            elif not upper and not lower:
                out.append(
                    '<note><rest/><duration>16</duration>'
                    "<type>whole</type><voice>1</voice></note>"
                )
            else:
                _emit_staff_voices(
                    out,
                    upper,
                    lower,
                    fifths=fifths,
                    with_lyrics=with_lyrics,
                )
            _emit_measure_barlines(
                out,
                mi,
                n_measures,
                styles,
                left_style=left_styles[mi],
                ending_start=end_starts[mi],
                ending_stop=end_stops[mi],
                repeat_times=rep_times[mi],
            )
            out.append("</measure>")
        out.append("</part>")
    out.append("</score-partwise>")
    return "\n".join(out)


def _emit_staff_voices(
    out: list[str],
    upper: list[NoteEvent],
    lower: list[NoteEvent],
    *,
    fifths: int,
    with_lyrics: bool,
) -> None:
    """Voice 1 (stok omhoog) → backup → voice 2 (stok omlaag)."""
    for ev in upper:
        _emit_single_note(
            out,
            ev,
            fifths=fifths,
            chord=False,
            with_lyrics=with_lyrics,
            voice=1,
            stem="up",
        )
    total_u = sum(_note_divs(ev) for ev in upper)
    if upper and lower:
        out.append(f"<backup><duration>{total_u}</duration></backup>")
    elif not upper and lower:
        # Alleen lower: write as voice 2 without backup.
        pass
    for ev in lower:
        _emit_single_note(
            out,
            ev,
            fifths=fifths,
            chord=False,
            with_lyrics=False,
            voice=2,
            stem="down",
        )


def _emit_note(out: list[str], ev: NoteEvent, *, fifths: int) -> None:
    _emit_single_note(
        out, ev, fifths=fifths, chord=False, with_lyrics=True, voice=1, stem="up"
    )


def _emit_chord(
    out: list[str],
    primary: NoteEvent,
    secondary: NoteEvent | None,
    *,
    fifths: int,
    with_lyrics: bool,
) -> None:
    """Legacy chord emit — prefer ``_emit_staff_voices`` for partituur."""
    _emit_staff_voices(
        out,
        [primary],
        [secondary] if secondary is not None else [],
        fifths=fifths,
        with_lyrics=with_lyrics,
    )


def _emit_single_note(
    out: list[str],
    ev: NoteEvent,
    *,
    fifths: int,
    chord: bool,
    with_lyrics: bool,
    voice: int = 1,
    stem: str = "up",
) -> None:
    p = ev.pitch
    d = ev.duration
    alt = f"<alter>{int(p.alter)}</alter>" if p.alter else ""
    accidental = ""
    if p.alter in ALTER_ACCIDENTAL and p.alter != _key_alter(p.step, fifths):
        accidental = f"<accidental>{ALTER_ACCIDENTAL[p.alter]}</accidental>"
    dots = "".join("<dot/>" for _ in range(d.dots))
    lyric_xml = ""
    if with_lyrics:
        for ly in ev.lyrics:
            extend_xml = "<extend/>" if ly.extend else ""
            lyric_xml += (
                f'<lyric number="{ly.number}">'
                f"<syllabic>{escape(ly.syllabic)}</syllabic>"
                f"<text>{escape(display_lyric_text(ly.text))}</text>{extend_xml}</lyric>"
            )
    out.append("<note>")
    if chord:
        out.append("<chord/>")
    out.append(
        f"<pitch><step>{p.step}</step>{alt}<octave>{p.octave}</octave></pitch>"
    )
    divs = (
        ev.duration_divisions
        if ev.duration_divisions is not None
        else d.divisions_value
    )
    out.append(f"<duration>{divs}</duration>")
    if ev.tie_start:
        out.append('<tie type="start"/>')
    if ev.tie_stop:
        out.append('<tie type="stop"/>')
    out.append(f"<voice>{voice}</voice>")
    out.append(f"<type>{d.note_type}</type>{dots}{accidental}")
    if ev.spacer:
        # Onzichtbare kop, wél lyrics (``print-object=no`` op <note> verbergt
        # lyrics in MuseScore-PDF — zie templates: visible=0 + play=0 in MSCZ).
        out.append("<stem>none</stem>")
        out.append("<notehead>none</notehead>")
    elif ev.stemless or ev.breve_head:
        # ||O||-midden: stokloos; breve-kop zet MSCZ-postprocess (headType).
        out.append("<stem>none</stem>")
    else:
        out.append(f"<stem>{stem}</stem>")
    if lyric_xml:
        out.append(lyric_xml)
    needs_notations = (
        not chord
        and (ev.slur_start or ev.slur_stop or ev.tie_start or ev.tie_stop)
    )
    if needs_notations:
        out.append("<notations>")
        if ev.slur_start:
            placement = "above" if stem == "up" else "below"
            out.append(
                f'<slur type="start" number="{voice}" placement="{placement}"/>'
            )
        if ev.slur_stop:
            out.append(f'<slur type="stop" number="{voice}"/>')
        if ev.tie_start:
            out.append('<tied type="start"/>')
        if ev.tie_stop:
            out.append('<tied type="stop"/>')
        out.append("</notations>")
    out.append("</note>")


def _key_alter(step: str, fifths: int) -> float:
    sharp_order = ("F", "C", "G", "D", "A", "E", "B")
    if fifths > 0:
        return 1.0 if step in sharp_order[:fifths] else 0.0
    if fifths < 0:
        flat_order = tuple(reversed(sharp_order))
        return -1.0 if step in flat_order[:(-fifths)] else 0.0
    return 0.0
