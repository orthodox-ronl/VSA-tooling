"""Export .mvsa to multi-part SATB MusicXML (draft-v0)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

from .duration_model import elm_to_duration
from .music import Duration, Pitch
from .musicxml_package import write_musicxml_output
from .mvsa_parse import (
    LPosition,
    StickyContext,
    VoicePosition,
    parse_mvsa,
)
from .mvsa_validate import MvsaValidationError
from .pitch_resolver import (
    PitchResolver,
    degree_to_pitch,
    key_fifths,
    parse_pitch_string,
)

PARTS = (
    {"id": "P1", "name": "Soprano", "abbr": "S", "clef": ("G", "2"), "voice": "S"},
    {"id": "P2", "name": "Alto", "abbr": "A", "clef": ("G", "2"), "voice": "A"},
    {"id": "P3", "name": "Tenor", "abbr": "T", "clef": ("F", "4"), "voice": "T"},
    {"id": "P4", "name": "Bass", "abbr": "B", "clef": ("F", "4"), "voice": "B"},
)

# Prefix accidental, name, then either oct[+acc] or acc[+oct]
_DEGREE_RE = re.compile(
    r"^(#|b)?(do|re|mi|fa|sol|so|la|si|ti)"
    r"(?:([+-]\d*)(#|b)?|(#|b)([+-]\d*)?)?$",
    re.IGNORECASE,
)
_NOTE_RE = re.compile(
    r"^([a-gA-G])(bb|b|#)?(\d+)?([+-]\d*)?$",
)
_EHM_RE = re.compile(r"^[+#b♯♭]*[/\\~\-]+$")

ALTER_ACCIDENTAL = {
    1.0: "sharp",
    -1.0: "flat",
    2.0: "double-sharp",
    -2.0: "double-flat",
}

_DEGREE_INDEX = {"do": 0, "re": 1, "mi": 2, "fa": 3, "sol": 4, "la": 5, "ti": 6}

# Reciteertoon on the page: breve (||O||); playback/spacing uses breve divisions.
_RECITE_DURATION = Duration(note_type="breve", dots=0)


@dataclass
class LyricSyllable:
    text: str
    syllabic: str = "single"
    number: int = 1


@dataclass
class NoteEvent:
    pitch: Pitch
    duration: Duration
    lyrics: list[LyricSyllable] = field(default_factory=list)
    recite: bool = False


class MvsaExportError(Exception):
    def __init__(self, message: str, *, line: int = 0) -> None:
        self.line = line
        super().__init__(message)


def export_mvsa_to_musicxml(
    text: str,
    *,
    title: str = "mvsa",
    section_id: str | None = None,
) -> str:
    """Validate + export. Raises MvsaValidationError or MvsaExportError."""
    doc = parse_mvsa(text)
    errors = [d for d in doc.diagnostics if d.severity == "error"]
    if errors:
        raise MvsaValidationError(errors)

    sections = doc.sections
    if section_id is not None:
        sections = [s for s in sections if s.id == section_id]
        if not sections:
            raise MvsaExportError(f"sectie {section_id!r} niet gevonden")

    voice_measures: dict[str, list[list[NoteEvent]]] = {
        p["voice"]: [] for p in PARTS
    }
    for section in sections:
        for system in section.systems:
            events_by_voice = _system_to_events(system)
            for voice, measures in events_by_voice.items():
                voice_measures[voice].extend(measures)

    ctx = sections[0].systems[0].context if sections and sections[0].systems else StickyContext()
    return _emit_score(voice_measures, title=title, context=ctx)


def export_mvsa_path(
    path: Path,
    out: Path,
    *,
    section_id: str | None = None,
) -> None:
    text = path.read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(
        text, title=path.stem, section_id=section_id
    )
    write_musicxml_output(out, xml)


def _system_to_events(system) -> dict[str, list[list[NoteEvent]]]:
    ctx: StickyContext = system.context
    lyric_marker = next((m for m in system.markers if m == "L" or m.startswith("L")), None)
    if lyric_marker is None:
        raise MvsaExportError("geen lyrics-regel L in systeem", line=system.start_line)

    voice_markers = [m for m in system.markers if m[0] in "SATB"]
    resolvers: dict[str, PitchResolver] = {}
    for m in voice_markers:
        letter = m[0]
        resolvers[letter] = PitchResolver.from_metadata(
            {"do": ctx.do, "mode": ctx.mode}
        )
        if ctx.start:
            _apply_start(resolvers[letter], ctx.start, letter)

    result: dict[str, list[list[NoteEvent]]] = {m[0]: [] for m in voice_markers}
    for p in PARTS:
        result.setdefault(p["voice"], [])

    for bundle in system.measures:
        l_positions = bundle.lyrics.get(lyric_marker, [])
        measure_events: dict[str, list[NoteEvent]] = {m[0]: [] for m in voice_markers}

        for vi, lpos in enumerate(l_positions):
            next_continues = (
                vi + 1 < len(l_positions) and l_positions[vi + 1].continues_word
            )
            for vm in voice_markers:
                letter = vm[0]
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
                    resolvers[letter],
                    ctx,
                    letter,
                    opens_hyphen=next_continues,
                )
                measure_events[letter].extend(notes)

        for letter, evs in measure_events.items():
            result[letter].append(evs)

    for p in PARTS:
        if p["voice"] not in result:
            result[p["voice"]] = [[] for _ in system.measures]
    return result


def _apply_start(resolver: PitchResolver, start_rest: str, letter: str) -> None:
    """Parse ``@start S=- A=\\3 T=\\6 B=\\8`` for this voice."""
    for part in start_rest.split():
        if "=" not in part:
            continue
        key, _, val = part.partition("=")
        if key.strip().upper().startswith(letter):
            ehm = val.strip()
            if re.fullmatch(r"\\+\d+", ehm) or re.fullmatch(r"/+\d+", ehm):
                ch = ehm[0]
                n = int(ehm.lstrip("\\/"))
                ehm = ch * n
            resolver.apply_start_marker([ehm] if ehm not in ("", "-") else [])
            if ehm == "-":
                resolver.apply_start_marker([])
            return
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
) -> list[NoteEvent]:
    elms = list(lpos.elms) if lpos.elms else ["~"]
    slots = list(vpos.slots) if vpos.slots else ["-"]

    if lpos.recite:
        pitch = _resolve_slot(slots[0] if slots else "-", resolver, ctx, letter)
        # No ELM after ')' → breve (recite default). Explicit ELM → that duration.
        if lpos.elms:
            dur = elm_to_duration(lpos.elms[0])
        else:
            dur = _RECITE_DURATION
        lyrics: list[LyricSyllable] = []
        if lpos.syllables:
            text = _join_lyric_text(lpos.syllables, lpos.links)
            syl = "single"
            if lpos.continues_word:
                syl = "end"
            lyrics.append(LyricSyllable(text=text, syllabic=syl, number=1))
        return [
            NoteEvent(pitch=pitch, duration=dur, lyrics=lyrics, recite=True)
        ]

    n = max(len(elms), len(slots))
    while len(elms) < n:
        elms.append("~")
    while len(slots) < n:
        slots.append("-")

    notes: list[NoteEvent] = []
    last_pitch: Pitch | None = None
    primary_syl = _syllabic_for_position(lpos, opens_hyphen=opens_hyphen)

    for si, (elm, slot) in enumerate(zip(elms, slots)):
        pitch = _resolve_slot(slot, resolver, ctx, letter, last_pitch=last_pitch)
        last_pitch = pitch
        dur = elm_to_duration(elm)
        lyrics: list[LyricSyllable] = []
        if si == 0 and lpos.syllables:
            if len(lpos.syllables) == 1:
                syl = primary_syl
                if n > 1 and syl == "single":
                    syl = "begin"
                lyrics.append(
                    LyricSyllable(text=lpos.syllables[0], syllabic=syl)
                )
            else:
                text = _join_lyric_text(lpos.syllables, lpos.links)
                syl = primary_syl if primary_syl != "single" else "begin"
                lyrics.append(LyricSyllable(text=text, syllabic=syl))
        notes.append(NoteEvent(pitch=pitch, duration=dur, lyrics=lyrics))
    return notes


def _resolve_slot(
    token: str,
    resolver: PitchResolver,
    ctx: StickyContext,
    letter: str,
    *,
    last_pitch: Pitch | None = None,
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
            octave = int(oct_s) + oct_delta
        else:
            # a–g without digit: do-octaaf (+ @oct + suffix)
            do_p = parse_pitch_string(ctx.do)
            octave = do_p.octave + ctx.oct_for(letter) + oct_delta
        pitch = Pitch(step=step, octave=octave, alter=alter)
        resolver._last_sounding = pitch
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
        shift = ctx.oct_for(letter)
        if oct_off in ("-", "+"):
            shift += -1 if oct_off == "-" else 1
        elif oct_off:
            shift += int(oct_off)
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

    if _EHM_RE.match(tok) or set(tok) <= set("\\/#b+-~"):
        return resolver.resolve_ehm(tok)

    try:
        pitch = parse_pitch_string(tok[0].upper() + tok[1:] if tok[0].islower() else tok)
        resolver._last_sounding = pitch
        return pitch
    except ValueError as exc:
        raise MvsaExportError(f"onbekende hoogte-token {tok!r}") from exc


def _emit_score(
    voice_measures: dict[str, list[list[NoteEvent]]],
    *,
    title: str,
    context: StickyContext,
) -> str:
    do_p = parse_pitch_string(context.do)
    fifths = key_fifths(do_p, context.mode)
    n_measures = max((len(ms) for ms in voice_measures.values()), default=0)

    out: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN"',
        '  "http://www.musicxml.org/dtds/partwise.dtd">',
        '<score-partwise version="3.1">',
        f"<work><work-title>{escape(title)}</work-title></work>",
        "<part-list>",
    ]
    for part in PARTS:
        out.append(f'<score-part id="{part["id"]}">')
        out.append(f"<part-name>{part['name']}</part-name>")
        out.append(f"<part-abbreviation>{part['abbr']}</part-abbreviation>")
        out.append("</score-part>")
    out.append("</part-list>")

    for part in PARTS:
        voice = part["voice"]
        measures = voice_measures.get(voice, [])
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
            if not events:
                out.append(
                    '<note><rest/><duration>16</duration><type>whole</type></note>'
                )
            else:
                for ev in events:
                    _emit_note(out, ev, fifths=fifths)
            style = "light-heavy" if mi == n_measures - 1 else "regular"
            out.append(
                f'<barline location="right"><bar-style>{style}</bar-style></barline>'
            )
            out.append("</measure>")
        out.append("</part>")
    out.append("</score-partwise>")
    return "\n".join(out)


def _emit_note(out: list[str], ev: NoteEvent, *, fifths: int) -> None:
    p = ev.pitch
    d = ev.duration
    alt = f"<alter>{int(p.alter)}</alter>" if p.alter else ""
    accidental = ""
    if p.alter in ALTER_ACCIDENTAL and p.alter != _key_alter(p.step, fifths):
        accidental = f"<accidental>{ALTER_ACCIDENTAL[p.alter]}</accidental>"
    dots = "".join("<dot/>" for _ in range(d.dots))
    lyric_xml = ""
    for ly in ev.lyrics:
        lyric_xml += (
            f'<lyric number="{ly.number}">'
            f"<syllabic>{escape(ly.syllabic)}</syllabic>"
            f"<text>{escape(ly.text)}</text></lyric>"
        )
    out.append("<note>")
    out.append(
        f"<pitch><step>{p.step}</step>{alt}<octave>{p.octave}</octave></pitch>"
    )
    out.append(f"<duration>{d.divisions_value}</duration>")
    out.append(f"<type>{d.note_type}</type>{dots}{accidental}{lyric_xml}")
    out.append("</note>")


def _key_alter(step: str, fifths: int) -> float:
    sharp_order = ("F", "C", "G", "D", "A", "E", "B")
    if fifths > 0:
        return 1.0 if step in sharp_order[:fifths] else 0.0
    if fifths < 0:
        flat_order = tuple(reversed(sharp_order))
        return -1.0 if step in flat_order[:(-fifths)] else 0.0
    return 0.0
