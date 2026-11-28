"""Render a vsa-template YAML to MusicXML or MuseScore native (.mscx/.mscz).

Usage:
  python scripts/render_vsa_template_musicxml.py <template.yaml> [out.musicxml|.mxl|.mscx|.mscz]
  python scripts/render_vsa_template_musicxml.py --all
"""

from __future__ import annotations

import argparse
import math
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import yaml

REPO = Path(__file__).resolve().parents[1]
LIBRARY = REPO / "docs" / "specification-vsa-templates" / "library"

DEGREE_ORDER = ("do", "re", "mi", "fa", "sol", "la", "ti")
# Semitones above tonic for major / natural minor (ti = leading in major, flat-7 in minor)
MAJOR_ST = (0, 2, 4, 5, 7, 9, 11)
MINOR_ST = (0, 2, 3, 5, 7, 8, 10)  # natural minor

ELM_DIV = {
    "~": (4, "quarter", 0),
    "-": (4, "quarter", 0),
    "-.": (6, "quarter", 1),
    "~.": (6, "quarter", 1),
    "_": (8, "half", 0),
    "_.": (12, "half", 1),
    "__": (16, "whole", 0),
    ".": (2, "eighth", 0),
    "..": (1, "16th", 0),
}

DO_RE = re.compile(r"^([A-G])(#|b)?([0-9])$")
PITCH_RE = re.compile(r"^(#|b)?(do|re|mi|fa|sol|la|ti)([+-][1-3])?$")

STEP_TO_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def parse_do(do: str) -> tuple[int, int]:
    """Return (pitch_class 0-11, octave) for scientific pitch."""
    m = DO_RE.match(do)
    if not m:
        raise ValueError(f"bad do: {do}")
    step, alter, octv = m.group(1), m.group(2), int(m.group(3))
    pc = STEP_TO_PC[step]
    if alter == "#":
        pc = (pc + 1) % 12
    elif alter == "b":
        pc = (pc - 1) % 12
    return pc, octv


def pc_to_step_alter(pc: int) -> tuple[str, int]:
    """Prefer flats for black keys (chant key signatures)."""
    table = {
        0: ("C", 0),
        1: ("D", -1),
        2: ("D", 0),
        3: ("E", -1),
        4: ("E", 0),
        5: ("F", 0),
        6: ("G", -1),
        7: ("G", 0),
        8: ("A", -1),
        9: ("A", 0),
        10: ("B", -1),
        11: ("B", 0),
    }
    return table[pc % 12]


def resolve_degree(degree: str, do: str, mode: str) -> tuple[str, int, int]:
    """Return (step, alter, octave) for a ladder degree."""
    m = PITCH_RE.match(degree)
    if not m:
        raise ValueError(f"bad degree: {degree}")
    chrom, name, oct_off = m.group(1), m.group(2), m.group(3)
    do_pc, do_oct = parse_do(do)
    idx = DEGREE_ORDER.index(name)
    st = (MAJOR_ST if mode == "major" else MINOR_ST)[idx]
    if chrom == "#":
        st += 1
    elif chrom == "b":
        st -= 1
    abs_semi = do_pc + st
    abs_pc = abs_semi % 12
    octv = do_oct + (abs_semi // 12)
    if oct_off:
        octv += int(oct_off)

    # Spell from degree name + accidental when chromatic; else prefer flats.
    natural_st = (MAJOR_ST if mode == "major" else MINOR_ST)[idx]
    natural_pc = (do_pc + natural_st) % 12
    nat_step, nat_alter = pc_to_step_alter(natural_pc)
    if chrom == "#":
        # Raise the natural spelling by a semitone (G → G#)
        step = nat_step
        alter = nat_alter + 1
        if alter == 2:  # rare; simplify
            step, alter = pc_to_step_alter(abs_pc)
    elif chrom == "b":
        step = nat_step
        alter = nat_alter - 1
        if alter == -2:
            step, alter = pc_to_step_alter(abs_pc)
    else:
        step, alter = pc_to_step_alter(abs_pc)
    return step, alter, octv


def fifths_for(do: str, mode: str) -> int:
    """Rough key signature fifths count."""
    # Major: number of sharps/flats from C
    major_fifths = {
        "C": 0,
        "G": 1,
        "D": 2,
        "A": 3,
        "E": 4,
        "B": 5,
        "F#": 6,
        "F": -1,
        "Bb": -2,
        "Eb": -3,
        "Ab": -4,
        "Db": -5,
        "Gb": -6,
    }
    m = DO_RE.match(do)
    assert m
    name = m.group(1) + (m.group(2) or "")
    # Normalize b/#
    name = name.replace("b", "b").replace("#", "#")
    if mode == "minor":
        # relative major is +3 semitones → use relative major fifths
        # D minor → F major (-1), etc.
        rel = {
            "A": "C",
            "E": "G",
            "B": "D",
            "F#": "A",
            "C#": "E",
            "G#": "B",
            "D": "F",
            "G": "Bb",
            "C": "Eb",
            "F": "Ab",
            "Bb": "Db",
            "Eb": "Gb",
        }
        name = rel.get(name, name)
    return major_fifths.get(name, 0)


def load_resolved(path: Path, library: Path) -> dict:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError(f"not a mapping: {path}")
    if "same_as" in doc:
        target_id = doc["same_as"]
        matches = list(library.glob(f"*/template.yaml"))
        for cand in matches:
            other = yaml.safe_load(cand.read_text(encoding="utf-8"))
            if isinstance(other, dict) and other.get("id") == target_id:
                # Keep alias id/genre/tone for title; melodic body from target
                merged = dict(other)
                merged["id"] = doc.get("id", other["id"])
                for k in ("genre", "tone", "source", "pitches_status"):
                    if k in doc:
                        merged[k] = doc[k]
                merged["_resolved_from"] = target_id
                return merged
        raise FileNotFoundError(f"same_as target not found: {target_id}")
    return doc


def phrase_order(doc: dict) -> list[dict]:
    phrases = {p["id"]: p for p in doc["phrases"]}
    if "sequence" in doc:
        ids = list(doc["sequence"])
    elif "cycle" in doc:
        ids = list(doc["cycle"])
        if "final" in doc:
            ids.append(doc["final"])
        # Also include library-only phrases (e.g. 1a) after cycle+final
        for p in doc["phrases"]:
            if p["id"] not in ids:
                ids.append(p["id"])
    else:
        ids = [p["id"] for p in doc["phrases"]]
    return [phrases[i] for i in ids]


def pitch_xml(step: str, alter: int, octave: int) -> str:
    alt = f"<alter>{alter}</alter>" if alter else ""
    return f"<pitch><step>{step}</step>{alt}<octave>{octave}</octave></pitch>"


# MuseScore 4 imports new-system; it skips <system-layout>. Measure width is
# best-effort. Trailing HBox after the last measure cannot be expressed in
# MusicXML (measure-distance creates an HBox *before* a measure).
LAST_MEASURE_WIDTH_TENTHS = "500"
LAST_SYSTEM_RIGHT_MARGIN_TENTHS = "420"

PARTS = (
    {
        "id": "P1",
        "name": "S\nA",
        "clef_sign": "G",
        "clef_line": "2",
        "v1": "S",
        "v2": "A",
        "upper": True,
    },
    {
        "id": "P2",
        "name": "T\nB",
        "clef_sign": "F",
        "clef_line": "4",
        "v1": "T",
        "v2": "B",
        "upper": False,
    },
)

# Coria/playback: one part per stem so T (etc.) can be soloed.
# Lyrics on every part: Coria shows text per muted/solo voice.
# Geen geforceerde stem-richting: speler kiest naar midden van de balk.
INSTANCE_PARTS = (
    {
        "id": "P1",
        "name": "Soprano",
        "abbr": "S",
        "clef_sign": "G",
        "clef_line": "2",
        "voice": "S",
        "lyrics": True,
    },
    {
        "id": "P2",
        "name": "Alto",
        "abbr": "A",
        "clef_sign": "G",
        "clef_line": "2",
        "voice": "A",
        "lyrics": True,
    },
    {
        "id": "P3",
        "name": "Tenor",
        "abbr": "T",
        "clef_sign": "F",
        "clef_line": "4",
        "voice": "T",
        "lyrics": True,
    },
    {
        "id": "P4",
        "name": "Bass",
        "abbr": "B",
        "clef_sign": "F",
        "clef_line": "4",
        "voice": "B",
        "lyrics": True,
    },
)

ALTER_ACCIDENTAL_MUSICXML = {
    1: "sharp",
    -1: "flat",
    2: "double-sharp",
    -2: "double-flat",
}

# Circle-of-fifths order: sharps FCGDAEB, flats BEADGCF.
_SHARP_ORDER = ("F", "C", "G", "D", "A", "E", "B")


def key_alter_for_step(step: str, fifths: int) -> int:
    """Alter implied by key signature for a diatonic step (0 if none)."""
    if fifths > 0:
        return 1 if step in _SHARP_ORDER[:fifths] else 0
    if fifths < 0:
        flat_order = tuple(reversed(_SHARP_ORDER))
        return -1 if step in flat_order[:(-fifths)] else 0
    return 0


def emit_note(
    out: list[str],
    pitch: tuple[str, int, int],
    dur: int,
    ntype: str,
    dots: int,
    voice: int,
    stem: str | None,
    *,
    optional: bool = False,
    recite: bool = False,
    lyric: str | None = None,
    syllabic: str = "single",
    lyric_extend: bool = False,
    lyric_extend_type: str | None = None,
    slur: str | None = None,
    slur_number: int = 1,
    fifths: int = 0,
    musicxml_hyphens_from_syllabic: bool = False,
) -> None:
    step, alter, octv = pitch
    alt = f"<alter>{alter}</alter>" if alter else ""
    # Alleen zichtbare accidental als die afwijkt van de toonsoort (Coria/F-dur:
    # Bb zonder mol; F# wél met kruis).
    accidental = ""
    if alter != key_alter_for_step(step, fifths) and alter in ALTER_ACCIDENTAL_MUSICXML:
        accidental = f"<accidental>{ALTER_ACCIDENTAL_MUSICXML[alter]}</accidental>"
    dots_xml = "".join("<dot/>" for _ in range(dots))
    lyric_xml = ""
    if lyric:
        # Coria/MuseScore tekenen zelf een streepje bij syllabic begin/middle.
        # Dubbele streepjes als de tekst óók op '-' eindigt.
        text = str(lyric)
        if musicxml_hyphens_from_syllabic and syllabic in {"begin", "middle"}:
            text = text.rstrip("-")
        ext = ""
        et = lyric_extend_type or ("start" if lyric_extend else None)
        if et:
            ext = f'<extend type="{et}"/>'
        lyric_xml = (
            f'<lyric number="1"><syllabic>{escape(syllabic)}</syllabic>'
            f"<text>{escape(text)}</text>{ext}</lyric>"
        )
    if optional:
        nh = '<notehead parentheses="yes">normal</notehead>'
    elif recite:
        # MusicXML: half duration, breve notehead (blad-||O||).
        nh = "<notehead>breve</notehead>"
    else:
        nh = ""
    notations = ""
    if slur:
        notations = (
            f'<notations><slur type="{slur}" number="{slur_number}" '
            f'placement="above"/></notations>'
        )
    if recite:
        stem_xml = "<stem>none</stem>"
    elif stem:
        stem_xml = f"<stem>{stem}</stem>"
    else:
        # Geen <stem>: speler/MuseScore kiest richting (naar midden balk).
        stem_xml = ""
    out.append(
        f"<note><pitch><step>{step}</step>{alt}<octave>{octv}</octave></pitch>"
        f"<duration>{dur}</duration><voice>{voice}</voice>"
        f"<type>{ntype}</type>{dots_xml}{accidental}{stem_xml}"
        f"{nh}{notations}{lyric_xml}</note>"
    )


STAFF_FONT = "DejaVu Sans Condensed"
STAFF_FONT_PT = "12"
# Lyrics: same face as staff text. Size matches staff (12pt, not spatium-
# dependent) so choir text stays readable; tweak LYRIC_FONT_PT if a frase
# wraps onto an extra system.
LYRIC_FONT = STAFF_FONT
LYRIC_FONT_PT = "12"
# Uitgewerkt zangstuk (instance): één maat per strofe (geen binnen-strofe-maatstrepen).
# Template-layout blijft strakker (formuleblad).
INSTANCE_MAX_QUARTERS_PER_MEASURE = 8
INSTANCE_MIN_LAST_CHUNK_QUARTERS = 3.0
# Instance spacing: leesbare lyrics (niet tegen elkaar / overlappend).
INSTANCE_MIN_NOTE_DISTANCE = "0.60"
INSTANCE_LYRICS_MIN_DISTANCE = "0.60"
INSTANCE_MEASURE_SPACING = "1.35"
INSTANCE_MIN_MEASURE_WIDTH = "5"
# Ruimte cadens → volgende recite (ná de maatstreep van de vorige strofe).
INSTANCE_PHRASE_GAP = (2, "eighth")
# Recite-collapse alleen vanaf zoveel syllaben (anders aparte noten).
RECITE_COLLAPSE_MIN_SYLLABLES = 3
# MuseScore Division=480 → quarter = 480 ticks (lyric melisma extender).
MSCX_DIVISION = 480
DUR_TICKS = {
    "16th": MSCX_DIVISION // 4,
    "eighth": MSCX_DIVISION // 2,
    "quarter": MSCX_DIVISION,
    "half": MSCX_DIVISION * 2,
    "whole": MSCX_DIVISION * 4,
    "breve": MSCX_DIVISION * 8,
    "longa": MSCX_DIVISION * 16,
}
DUR_FRAC = {
    "16th": (1, 16),
    "eighth": (1, 8),
    "quarter": (1, 4),
    "half": (1, 2),
    "whole": (1, 1),
    "breve": (2, 1),
    "longa": (4, 1),
}
FRAME_FONT_PT = "14"
TITLE_FONT_PT = "18"
# Titel-VBox (spatium). Visuele titel→systeem ≈ VBox + frameSystemDistance.
TITLE_VBOX_HEIGHT_SP = 3.0
# Stafafruimte SA↔TB; systeemmafruimte en titel→systeem = ratio × stafafruimte.
# Formuleblad: leesbaar maar niet te veel wit; instance blijft compact.
STAFF_DISTANCE_SP = 6.0
VERTICAL_GAP_RATIO = 1.55
INSTANCE_STAFF_DISTANCE_SP = 5.0
INSTANCE_VERTICAL_GAP_RATIO = 1.5
# Met setting 1,5×staff maten we ~7/6 i.p.v. 9/6; schaal systemDistance bij.
SYSTEM_DISTANCE_CALIBRATION = 9 / 7
# Cycle after last measure: empty spacer HBox + text HBox (approx. centered).
# If the last frase leaves too little room, fall back to a VBox below.
CYCLE_SPACER_HBOX_WIDTH = "14"
CYCLE_TEXT_HBOX_WIDTH = "36"
# Last-frase length (quarters) above this → VBox instead of trailing HBoxes.
CYCLE_HBOX_MAX_LAST_QUARTERS = 16
# Reciteertoon: breve (||O||) on the page; playback/spacing = half (2 beats).
RECITE_PLAY_DIV = ELM_DIV["_"]  # (8, "half", 0)
# Formulelabels: frase-id en anker-afkorting op dezelfde hoogte.
FRASE_ID_Y = "-4.5"
MAPPING_TEXT_Y = "-4.5"
# Frase-anker arrow sits below anker-label.
# Anchors never share an event with role: recite in the library templates.
ANCHOR_ARROW_Y = "-1.3"
# Bij e.st. op eerste klinkende noot: frase-id links, anker rechts (zelfde y).
# MuseScore koppelt StaffText op onzichtbare spacers door naar de volgende
# zichtbare noot — daarom horizontale offsets i.p.v. alleen een spacer.
FRASE_ID_X_BESIDE_ANCHOR = "-9"
ANCHOR_LABEL_X_BESIDE_FRASE = "4"
# Extra onzichtbare spacer-noot (hele) schuift de klinkende noten naar rechts
# zodat er onder de labels lucht is.
PHRASE_LEAD_SPACER_NTYPE = "whole"
PHRASE_LEAD_SPACER_DUR = 16
# Formuleblad: bij voorkeur twee frasen per systeem.
TEMPLATE_PHRASES_PER_SYSTEM = 2
# Ruimte boven de balk voor labels (spatium).
TEMPLATE_STAFF_UPPER_BORDER_SP = 6.5
_TEMPLATE_PAGE_INCH_PER_SYSTEM = 2.6
_TEMPLATE_PAGE_TITLE_INCH = 1.5
# YAML stores e.st. without spaces; the score shows "e. st.".
ANCHOR_LABELS = {
    "e.st.": "e. st.",
    "l.st.": "l. st.",
    "vl.st.": "vl. st.",
    "l.lgr.": "l. lgr.",
}


def words_direction(
    text: str,
    *,
    placement: str = "above",
    enclosure: str | None = None,
    font_size: str | None = None,
) -> str:
    size = font_size or STAFF_FONT_PT
    attrs = [f'font-family="{STAFF_FONT}"', f'font-size="{size}"']
    if enclosure:
        attrs.append(f'enclosure="{enclosure}"')
    attr = " " + " ".join(attrs)
    return (
        f'<direction placement="{placement}"><direction-type>'
        f"<words{attr}>{escape(text)}</words>"
        "</direction-type></direction>"
    )


def last_system_print() -> str:
    return (
        '<print new-system="yes">'
        "<system-layout><system-margins>"
        "<left-margin>0</left-margin>"
        f"<right-margin>{LAST_SYSTEM_RIGHT_MARGIN_TENTHS}</right-margin>"
        "</system-margins></system-layout>"
        "</print>"
    )


def resolve_phrase_events(phrase: dict, do: str, mode: str) -> tuple[list[dict], int]:
    from vsa.template_instance import flatten_phrase_events

    events: list[dict] = []
    total = 0
    for event in flatten_phrase_events(phrase["events"]):
        is_recite = event.get("role") == "recite"
        if is_recite:
            # Blad: breve (||O||). MuseScore: half + headType breve → 2 tellen.
            dur, ntype, dots = RECITE_PLAY_DIV
        else:
            dur, ntype, dots = ELM_DIV[event["duration"]]
        pitches = event["pitches"]
        events.append(
            {
                "pitches": {
                    v: resolve_degree(pitches[v], do, mode) for v in ("S", "A", "T", "B")
                },
                "dur": dur,
                "ntype": ntype,
                "dots": dots,
                "optional": bool(event.get("optional")),
                "recite": is_recite,
                "anchor": event.get("anchor"),
                "lyric": event.get("lyric"),
            }
        )
        total += dur
    return events, total


def emit_part_voices(
    out: list[str],
    events: list[dict],
    *,
    v1: str,
    v2: str,
    anchors: bool,
) -> None:
    """Voice 1 notes (with optional staff text), backup, then voice 2 — MuseScore pattern."""
    for ev in events:
        if anchors and ev.get("anchor"):
            out.append(words_direction(str(ev["anchor"])))
        emit_note(
            out,
            ev["pitches"][v1],
            ev["dur"],
            ev["ntype"],
            ev["dots"],
            1,
            "up",
            optional=ev["optional"],
            recite=ev["recite"],
            lyric=ev.get("lyric") if v1 == "S" else None,
        )
    total = sum(ev["dur"] for ev in events)
    out.append(f"<backup><duration>{total}</duration></backup>")
    for ev in events:
        emit_note(
            out,
            ev["pitches"][v2],
            ev["dur"],
            ev["ntype"],
            ev["dots"],
            2,
            "down",
            optional=ev["optional"],
            recite=ev["recite"],
        )


def cycle_label(doc: dict) -> str | None:
    if "cycle" in doc and "final" in doc:
        body = ", ".join(str(x) for x in doc["cycle"])
        return f"||: {body} :|| {doc['final']}"
    if "sequence" in doc:
        return "sequence: " + ", ".join(str(x) for x in doc["sequence"])
    return None


def cycle_repeat_flags(doc: dict, phrase_id: str) -> tuple[bool, int | None]:
    """Return (start_repeat, end_repeat_count) for cycle-form templates."""
    if "cycle" not in doc or "final" not in doc:
        return False, None
    ids = [str(x) for x in doc["cycle"]]
    if not ids:
        return False, None
    start = phrase_id == ids[0]
    end_count = len(ids) if phrase_id == ids[-1] else None
    return start, end_count


def _score_header(title: str) -> list[str]:
    return [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
        '"http://www.musicxml.org/dtds/partwise.dtd">',
        '<score-partwise version="4.0">',
        f"<work><work-title>{escape(title)}</work-title></work>",
        "<identification><encoding>"
        "<software>render_vsa_template_musicxml.py</software>"
        '<supports element="print" attribute="new-system" type="yes"/>'
        "</encoding></identification>",
        "<part-list>",
        '<part-group type="start" number="1"><group-symbol>bracket</group-symbol></part-group>',
        '<score-part id="P1">'
        f"<part-name>{escape(PARTS[0]['name'])}</part-name>"
        f"<part-abbreviation>{escape(PARTS[0]['name'])}</part-abbreviation>"
        "</score-part>",
        '<score-part id="P2">'
        f"<part-name>{escape(PARTS[1]['name'])}</part-name>"
        f"<part-abbreviation>{escape(PARTS[1]['name'])}</part-abbreviation>"
        "</score-part>",
        '<part-group type="stop" number="1"/>',
        "</part-list>",
    ]


def render_template_musicxml(doc: dict) -> str:
    do = doc["do"]
    mode = doc.get("mode", "major")
    fifths = fifths_for(do, mode)
    title = f"{doc.get('id', 'template')} (formule uit YAML)"
    if doc.get("_resolved_from"):
        title += f" ← {doc['_resolved_from']}"

    phrases = phrase_order(doc)
    resolved: list[tuple[str, list[dict], int]] = []
    for phrase in phrases:
        events, total = resolve_phrase_events(phrase, do, mode)
        resolved.append((str(phrase["id"]), events, total))
    label = cycle_label(doc)
    n_phr = len(resolved)

    out: list[str] = _score_header(title)

    for part in PARTS:
        out.append(f'<part id="{part["id"]}">')
        for mi, (pid, events, _total) in enumerate(resolved, start=1):
            is_first = mi == 1
            is_last = mi == n_phr
            width = f' width="{LAST_MEASURE_WIDTH_TENTHS}"' if is_last and n_phr > 1 else ""
            out.append(f'<measure number="{mi}"{width}>')
            if is_last and n_phr > 1:
                out.append(last_system_print())
            if is_first:
                out.append("<attributes>")
                out.append("<divisions>4</divisions>")
                out.append(f"<key><fifths>{fifths}</fifths></key>")
                out.append("<time><senza-misura/></time>")
                out.append(
                    f'<clef><sign>{part["clef_sign"]}</sign>'
                    f'<line>{part["clef_line"]}</line></clef>'
                )
                out.append("</attributes>")
            start_rep, end_rep = cycle_repeat_flags(doc, pid)
            if start_rep:
                out.append(
                    '<barline location="left"><repeat direction="forward"/></barline>'
                )
            if part["upper"]:
                out.append(
                    words_direction(pid, enclosure="rectangle")
                )
            emit_part_voices(
                out,
                events,
                v1=part["v1"],
                v2=part["v2"],
                anchors=part["upper"],
            )
            if is_last and label and not part["upper"]:
                # MusicXML fallback: MuseScore Style/VBox do not round-trip.
                out.append(
                    words_direction(label, placement="below", font_size=FRAME_FONT_PT)
                )
            if is_last:
                out.append(
                    '<barline location="right"><bar-style>light-heavy</bar-style></barline>'
                )
            elif end_rep is not None:
                out.append(
                    '<barline location="right"><bar-style>light-heavy</bar-style>'
                    '<repeat direction="backward"/></barline>'
                )
            else:
                out.append(
                    '<barline location="right"><bar-style>light-light</bar-style></barline>'
                )
            out.append("</measure>")
        out.append("</part>")

    out.append("</score-partwise>")
    return "\n".join(out)


def render_elia_r1_musicxml() -> str:
    """Pad-B proof for Elia line 1: S from VSA, A/T/B from tropaar-toon-4-hemelum slots."""
    # (lyric, dur_div, S, A, T, B) with scientific pitches already resolved for do=F4
    notes = [
        ("Gij", 4, ("A", 0, 4), ("F", 0, 4), ("C", 0, 4), ("F", 0, 3)),
        ("waart", 4, ("A", 0, 4), ("F", 0, 4), ("C", 0, 4), ("F", 0, 3)),
        ("een", 4, ("A", 0, 4), ("F", 0, 4), ("C", 0, 4), ("F", 0, 3)),
        ("En", 8, ("A", 0, 4), ("F", 0, 4), ("C", 0, 4), ("D", 0, 3)),
        ("gel", 4, ("A", 0, 4), ("F", 0, 4), ("C", 0, 4), ("D", 0, 3)),
        ("in", 4, ("B", -1, 4), ("G", 0, 4), ("G", 0, 3), ("G", 0, 2)),
        ("het", 4, ("B", -1, 4), ("G", 0, 4), ("G", 0, 3), ("G", 0, 2)),
        ("vlees", 8, ("A", 0, 4), ("F", 0, 4), ("F", 0, 3), ("F", 0, 3)),
    ]
    type_map = {4: ("quarter", 0), 8: ("half", 0)}
    events = [
        {
            "pitches": {"S": s, "A": a, "T": t, "B": b},
            "dur": dur,
            "ntype": type_map[dur][0],
            "dots": type_map[dur][1],
            "optional": False,
            "recite": False,
            "anchor": None,
            "lyric": lyric,
        }
        for lyric, dur, s, a, t, b in notes
    ]

    out: list[str] = _score_header("Elia regel 1 — instance (provisional)")
    for part in PARTS:
        out.append(f'<part id="{part["id"]}">')
        out.append('<measure number="1">')
        out.append("<attributes>")
        out.append("<divisions>4</divisions>")
        out.append("<key><fifths>-1</fifths></key>")
        out.append("<time><senza-misura/></time>")
        out.append(
            f'<clef><sign>{part["clef_sign"]}</sign>'
            f'<line>{part["clef_line"]}</line></clef>'
        )
        out.append("</attributes>")
        emit_part_voices(
            out,
            events,
            v1=part["v1"],
            v2=part["v2"],
            anchors=False,
        )
        out.append(
            '<barline location="right"><bar-style>light-heavy</bar-style></barline>'
        )
        out.append("</measure></part>")
    out.append("</score-partwise>")
    return "\n".join(out)


# --- MuseScore native (.mscx / .mscz) ---------------------------------------
# Style + VBox do not survive MusicXML. Open the MSCX in MuseScore.

STEP_MIDI = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
STEP_TPC = {"C": 14, "D": 16, "E": 18, "F": 13, "G": 15, "A": 17, "B": 19}
DUR_QUARTERS = {
    "quarter": 1.0,
    "half": 2.0,
    "whole": 4.0,
    "breve": 8.0,
    "longa": 16.0,
    "eighth": 0.5,
    "16th": 0.25,
}
ALTER_ACCIDENTAL = {
    1: "accidentalSharp",
    -1: "accidentalFlat",
    2: "accidentalDoubleSharp",
    -2: "accidentalDoubleFlat",
}

_MSCZ_CONTAINER = """\
<?xml version="1.0" encoding="UTF-8"?>
<container>
  <rootfiles>
    <rootfile full-path="score.mscx"/>
  </rootfiles>
</container>
"""

# A4 in inches (MuseScore Style page* units).
_PAGE_WIDTH_IN = 8.27
_PAGE_HEIGHT_A4_IN = 11.69
_PAGE_MARGIN_IN = 0.590551
def _page_style(*, layout: str = "template", n_systems: int = 1) -> str:
    """Page size/margins. Template grows with frase-count for single-SVG export."""
    if layout == "template":
        height = max(
            _PAGE_HEIGHT_A4_IN,
            _TEMPLATE_PAGE_TITLE_INCH
            + max(1, n_systems) * _TEMPLATE_PAGE_INCH_PER_SYSTEM,
        )
    else:
        height = _PAGE_HEIGHT_A4_IN
    printable = _PAGE_WIDTH_IN - 2 * _PAGE_MARGIN_IN
    m = f"{_PAGE_MARGIN_IN:g}"
    return (
        f"<pageWidth>{_PAGE_WIDTH_IN:g}</pageWidth>"
        f"<pageHeight>{height:.2f}</pageHeight>"
        f"<pagePrintableWidth>{printable:.4f}</pagePrintableWidth>"
        f"<pageEvenLeftMargin>{m}</pageEvenLeftMargin>"
        f"<pageOddLeftMargin>{m}</pageOddLeftMargin>"
        f"<pageEvenTopMargin>{m}</pageEvenTopMargin>"
        f"<pageEvenBottomMargin>{m}</pageEvenBottomMargin>"
        f"<pageOddTopMargin>{m}</pageOddTopMargin>"
        f"<pageOddBottomMargin>{m}</pageOddBottomMargin>"
        "<pageTwosided>0</pageTwosided>"
    )


def midi_and_tpc(step: str, alter: int, octave: int) -> tuple[int, int]:
    midi = (octave + 1) * 12 + STEP_MIDI[step] + alter
    tpc = STEP_TPC[step] + 7 * alter
    return midi, tpc


def events_quarters(events: list[dict]) -> float:
    q = 0.0
    for ev in events:
        unit = DUR_QUARTERS[ev["ntype"]]
        if ev.get("dots") == 1:
            unit *= 1.5
        elif ev.get("dots") == 2:
            unit *= 1.75
        q += unit
    return q


def events_len_attr(events: list[dict]) -> str:
    q = events_quarters(events)
    if abs(q - round(q)) < 1e-9:
        return f"{int(round(q))}/4"
    return f"{int(round(q * 2))}/8"


def score_title(doc: dict) -> str:
    genre = str(doc.get("genre", "")).capitalize() or "Template"
    tone = doc.get("tone")
    if tone:
        return f"{genre}melodie (Toon {tone})"
    return str(doc.get("id", "vsa-template"))


def _phrase_lead_spacer_event() -> dict:
    """Onzichtbare spacer-noot: ruimte voor frase-id naast e.st. op de eerste noot."""
    return {
        "pitches": {
            "S": ("C", 0, 4),
            "A": ("C", 0, 4),
            "T": ("C", 0, 3),
            "B": ("C", 0, 3),
        },
        "dur": PHRASE_LEAD_SPACER_DUR,
        "ntype": PHRASE_LEAD_SPACER_NTYPE,
        "dots": 0,
        "optional": False,
        "recite": False,
        "spacer": True,
        "anchor": None,
    }


def _with_phrase_lead_spacer(events: list[dict]) -> list[dict]:
    """Voeg voorspacer toe als de eerste noot een anker heeft (e.st. e.d.)."""
    if events and events[0].get("anchor"):
        return [_phrase_lead_spacer_event(), *events]
    return events


def _anchor_label(anchor: str) -> str:
    key = anchor.replace(" ", "")
    return ANCHOR_LABELS.get(key, anchor)


def _mscx_staff_text(
    text: str,
    *,
    rectangle: bool = False,
    x: str = "0",
    y: str = MAPPING_TEXT_Y,
    align: str | None = None,
) -> str:
    frame = "<frameType>1</frameType>" if rectangle else ""
    align_xml = f"<align>{escape(align)}</align>" if align else ""
    inner = (
        f'<font size="{STAFF_FONT_PT}"/><font face="{STAFF_FONT}"/>{escape(text)}'
    )
    return (
        "<StaffText>"
        f"<family>{STAFF_FONT}</family>"
        f"<size>{STAFF_FONT_PT}</size>"
        "<placement>above</placement>"
        "<autoplace>0</autoplace>"
        f"{align_xml}"
        f'<offset x="{x}" y="{y}"/>'
        f"{frame}"
        f"<text>{inner}</text>"
        "</StaffText>"
    )


def _mscx_anchor_staff_texts(anchor: str, *, x: str = "0") -> list[str]:
    """Abbreviation at formulelabel height; arrow below, pointing at the note."""
    return [
        _mscx_staff_text(_anchor_label(anchor), x=x),
        _mscx_staff_text(
            "↓", x=x, y=ANCHOR_ARROW_Y, align="center,baseline"
        ),
    ]


def _mscx_note(
    pitch: tuple[str, int, int],
    *,
    optional: bool = False,
    recite: bool = False,
    spacer: bool = False,
) -> str:
    step, alter, octv = pitch
    midi, tpc = midi_and_tpc(step, alter, octv)
    bits: list[str] = []
    if optional:
        bits.append("<parentheses>both</parentheses>")
    if spacer:
        bits.append("<visible>0</visible>")
        bits.append("<play>0</play>")
    if alter in ALTER_ACCIDENTAL and not spacer:
        bits.append(
            f"<Accidental><subtype>{ALTER_ACCIDENTAL[alter]}</subtype></Accidental>"
        )
    bits.append(f"<pitch>{midi}</pitch>")
    bits.append(f"<tpc>{tpc}</tpc>")
    if recite:
        # ||O|| notehead: half duration + headType breve (2 beats playback).
        bits.append("<headType>breve</headType>")
    if optional:
        bits.append("<hideGeneratedParentheses>1</hideGeneratedParentheses>")
    return "<Note>" + "".join(bits) + "</Note>"


def _event_ticks(ev: dict) -> int:
    ticks = DUR_TICKS[ev["ntype"]]
    if ev.get("dots") == 1:
        ticks = ticks * 3 // 2
    elif ev.get("dots") == 2:
        ticks = ticks * 7 // 4
    return ticks


def _event_frac(ev: dict) -> tuple[int, int]:
    num, den = DUR_FRAC[ev["ntype"]]
    if ev.get("dots") == 1:
        num, den = num * 3, den * 2
    elif ev.get("dots") == 2:
        num, den = num * 7, den * 4
    return num, den


def _add_frac(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
    n = a[0] * b[1] + b[0] * a[1]
    d = a[1] * b[1]
    g = math.gcd(n, d)
    return n // g, d // g


def _frac_str(frac: tuple[int, int]) -> str:
    return f"{frac[0]}/{frac[1]}"


def prepare_instance_events(events: list[dict]) -> list[dict]:
    """Hyphens tussen lettergrepen; melisma ticks + slur-span op VSA-&-noten."""
    out = [dict(ev) for ev in events]
    i = 0
    while i < len(out):
        if out[i].get("rest"):
            i += 1
            continue
        lyric = out[i].get("lyric")
        syllabic = out[i].get("syllabic") or "single"
        if lyric:
            j = i + 1
            while j < len(out) and not out[j].get("lyric"):
                j += 1
            if j > i + 1:
                # Recite/spacer-gap: geen slur/extender; ticks blijven staan.
                gap = out[i + 1 : j]
                if out[i].get("recite") or any(
                    e.get("rest") or e.get("spacer") for e in gap
                ):
                    i = j
                    continue
                # Melisma: streepje op de lettergreep + extender + slur.
                out[i]["lyric"] = str(lyric).rstrip("-") + "-"
                span = (0, 1)
                for k in range(i, j - 1):
                    span = _add_frac(span, _event_frac(out[k]))
                ticks = sum(_event_ticks(out[k]) for k in range(i + 1, j))
                out[i]["lyric_ticks"] = ticks
                out[i]["lyric_extend"] = True
                out[i]["slur_next"] = _frac_str(span)
                out[j - 1]["slur_prev"] = _frac_str(span)
                i = j
                continue
            if syllabic in {"begin", "middle"}:
                out[i]["lyric"] = str(lyric).rstrip("-") + "-"
        i += 1
    return out


def split_events_for_layout(
    events: list[dict],
    *,
    max_quarters: float = INSTANCE_MAX_QUARTERS_PER_MEASURE,
    min_last_quarters: float = INSTANCE_MIN_LAST_CHUNK_QUARTERS,
) -> list[list[dict]]:
    """Splits een lange frase in layout-maten (geen knip in een melisma).

    Kleine rest-chunk aan het eind wordt bij de vorige gevoegd zodat er geen
    wees-maat van 1–2 tellen ontstaat.
    """
    if not events:
        return []
    chunks: list[list[dict]] = []
    current: list[dict] = []
    quarters = 0.0

    def in_melisma_tail(ev: dict) -> bool:
        return bool(ev.get("slur_prev")) or (
            not ev.get("lyric") and (ev.get("syllabic") in {"middle", "end"})
        )

    for ev in events:
        eq = events_quarters([ev])
        if (
            current
            and quarters + eq > max_quarters
            and not in_melisma_tail(ev)
            and not current[-1].get("slur_next")
            and not current[-1].get("keep_with_next")
        ):
            chunks.append(current)
            current = []
            quarters = 0.0
        current.append(ev)
        quarters += eq
    if current:
        chunks.append(current)
    if (
        len(chunks) >= 2
        and events_quarters(chunks[-1]) < min_last_quarters
    ):
        chunks[-2].extend(chunks[-1])
        chunks.pop()
    return chunks


def _mscx_slur_start(frac: str) -> str:
    return (
        f'<Spanner type="Slur"><Slur/>'
        f"<next><location><fractions>{frac}</fractions></location></next>"
        "</Spanner>"
    )


def _mscx_slur_end(frac: str) -> str:
    return (
        '<Spanner type="Slur">'
        f"<prev><location><fractions>-{frac}</fractions></location></prev>"
        "</Spanner>"
    )


def _mscx_chord(
    pitches: tuple[str, int, int] | list[tuple[str, int, int]],
    ntype: str,
    dots: int,
    *,
    optional: bool = False,
    recite: bool = False,
    lyric: str | None = None,
    syllabic: str = "single",
    lyric_ticks: int = 0,
    lyric_align: str | None = None,
    slur_next: str | None = None,
    slur_prev: str | None = None,
    spacer: bool = False,
) -> list[str]:
    pitch_list = [pitches] if isinstance(pitches, tuple) else list(pitches)
    lines: list[str] = []
    dots_xml = ""
    if dots and not recite and not spacer:
        dots_xml = f"<dots>{dots}</dots>"
    stem_xml = ""
    if recite or spacer:
        stem_xml = "<noStem>1</noStem>"
    notes_xml = "".join(
        _mscx_note(p, optional=optional, recite=recite, spacer=spacer)
        for p in pitch_list
    )
    paren = ""
    if optional:
        idxs = "".join(
            f"<NoteIdx>{i}</NoteIdx>" for i in range(len(pitch_list))
        )
        paren = f"<NoteParenGroup><Notes>{idxs}</Notes></NoteParenGroup>"
    slur_xml = ""
    if slur_next:
        slur_xml += _mscx_slur_start(slur_next)
    if slur_prev:
        slur_xml += _mscx_slur_end(slur_prev)
    lyrics_xml = ""
    if lyric:
        syl = {"single": "0", "begin": "1", "end": "2", "middle": "3"}.get(
            syllabic, "0"
        )
        ticks_xml = ""
        if lyric_ticks:
            ticks_xml = f"<ticks>{lyric_ticks}</ticks><ticks_f>0</ticks_f>"
        # MuseScore 4.7+: horizontale plaatsing = <position>, niet <align>
        # (align is text-interne uitlijning; position knoopt aan de nootkop).
        pos_xml = ""
        align_xml = ""
        if lyric_align:
            horiz = lyric_align.split(",", 1)[0].strip()
            pos_xml = f"<position>{escape(horiz)}</position>"
            align_xml = f"<align>{escape(lyric_align)}</align>"
        lyrics_xml = (
            f"<Lyrics><syllabic>{syl}</syllabic>"
            f"{ticks_xml}"
            f"{pos_xml}"
            f"{align_xml}"
            f"<family>{LYRIC_FONT}</family>"
            f"<size>{LYRIC_FONT_PT}</size>"
            f"<text>{escape(lyric)}</text></Lyrics>"
        )
    lines.append(
        f"<Chord>{dots_xml}<durationType>{ntype}</durationType>"
        f"{stem_xml}{slur_xml}{lyrics_xml}{notes_xml}{paren}</Chord>"
    )
    return lines


def _mscx_end_barline(*, subtype: str = "normal", visible: bool = True) -> str:
    """Eind-maatstreep in de voice (MuseScore 4 leest géén Measure/endBarLineVisible)."""
    bits = [f"<subtype>{subtype}</subtype>"]
    if not visible:
        bits.append("<visible>0</visible>")
    return "<BarLine>" + "".join(bits) + "</BarLine>"


def _mscx_voice(
    events: list[dict],
    voice_keys: str | tuple[str, ...],
    *,
    frase_id: str | None = None,
    anchors: bool = False,
    keysig: bool = False,
    fifths: int = 0,
    time_sig: tuple[int, int] | None = None,
    with_lyrics: bool = False,
    end_barline: str | None = None,
    end_barline_visible: bool = True,
) -> list[str]:
    keys = (voice_keys,) if isinstance(voice_keys, str) else voice_keys
    lines = ["<voice>"]
    if keysig:
        # Clefs come from Part Staff defaultConcertClef / defaultTransposingClef
        # (and Instrument <clef>). A measure <Clef> would draw a second clef.
        lines.append(f"<KeySig><concertKey>{fifths}</concertKey></KeySig>")
    if time_sig is not None:
        sig_n, sig_d = time_sig
        # visible=0 + style genCourtesyTimesig=0: geen getallen / courtesy
        # aan het eind van de balk; Measure len blijft kloppen (geen +/-).
        lines.append(
            "<TimeSig><visible>0</visible>"
            "<isCourtesy>0</isCourtesy>"
            f"<sigN>{sig_n}</sigN><sigD>{sig_d}</sigD></TimeSig>"
        )
    # Eerste klinkende event (na optionele lead-spacer): frase-id + e.st. naast elkaar.
    first_sounding_i = 0
    while first_sounding_i < len(events) and (
        events[first_sounding_i].get("spacer") or events[first_sounding_i].get("rest")
    ):
        first_sounding_i += 1
    pair_frase_with_anchor = bool(
        frase_id
        and anchors
        and first_sounding_i < len(events)
        and events[first_sounding_i].get("anchor")
    )
    if frase_id is not None and not pair_frase_with_anchor:
        lines.append(_mscx_staff_text(frase_id, rectangle=True, y=FRASE_ID_Y))
    for ei, ev in enumerate(events):
        if anchors and ev.get("anchor"):
            if pair_frase_with_anchor and ei == first_sounding_i:
                lines.append(
                    _mscx_staff_text(
                        frase_id,
                        rectangle=True,
                        x=FRASE_ID_X_BESIDE_ANCHOR,
                        y=FRASE_ID_Y,
                    )
                )
                lines.extend(
                    _mscx_anchor_staff_texts(
                        str(ev["anchor"]), x=ANCHOR_LABEL_X_BESIDE_FRASE
                    )
                )
            else:
                lines.extend(_mscx_anchor_staff_texts(str(ev["anchor"])))
        if ev.get("rest"):
            vis = ""
            if ev.get("visible") is False:
                vis = "<visible>0</visible>"
            dots_xml = f"<dots>{ev['dots']}</dots>" if ev.get("dots") else ""
            lines.append(
                f"<Rest>{vis}{dots_xml}"
                f"<durationType>{ev['ntype']}</durationType></Rest>"
            )
            continue
        pitch_list = [ev["pitches"][k] for k in keys]
        lines.extend(
            _mscx_chord(
                pitch_list,
                ev["ntype"],
                ev["dots"],
                optional=ev["optional"],
                recite=ev["recite"],
                lyric=ev.get("lyric") if with_lyrics else None,
                syllabic=ev.get("syllabic") or "single",
                lyric_ticks=int(ev.get("lyric_ticks") or 0) if with_lyrics else 0,
                lyric_align=ev.get("lyric_align") if with_lyrics else None,
                slur_next=ev.get("slur_next"),
                slur_prev=ev.get("slur_prev"),
                spacer=bool(ev.get("spacer")),
            )
        )
    if end_barline is not None:
        lines.append(
            _mscx_end_barline(
                subtype=end_barline, visible=end_barline_visible
            )
        )
    lines.append("</voice>")
    return lines


def _vertical_layout_gaps(*, layout: str = "template") -> tuple[str, str, str]:
    """staffDistance, systemDistance, frameSystemDistance (spatium strings).

    Doel: systeemmafruimte en titel→systeem = gap-ratio × stafafruimte
    op het scherm. Titelgat ≈ ``TITLE_VBOX_HEIGHT_SP`` + ``frameSystemDistance``.
    ``systemDistance`` × ``SYSTEM_DISTANCE_CALIBRATION`` (historisch: gemeten
    7/6 i.p.v. 9/6 bij naïeve 1,5×-setting).
    """
    if layout == "instance":
        staff = INSTANCE_STAFF_DISTANCE_SP
        ratio = INSTANCE_VERTICAL_GAP_RATIO
    else:
        staff = STAFF_DISTANCE_SP
        ratio = VERTICAL_GAP_RATIO
    target = staff * ratio
    system = round(target * SYSTEM_DISTANCE_CALIBRATION, 2)
    frame = round(target - TITLE_VBOX_HEIGHT_SP, 2)
    if frame < 0:
        raise ValueError(
            f"TITLE_VBOX_HEIGHT_SP ({TITLE_VBOX_HEIGHT_SP}) ≥ "
            f"target gap ({target}); verklein de VBox of verhoog de ratio"
        )
    return f"{staff:g}", f"{system:g}", f"{frame:g}"


def _mscx_style_block(*, layout: str = "template", n_systems: int = 1) -> str:
    """MuseScore layout/fonts — always emitted; MuseScore save may strip it.

    ``layout="template"``: formuleblad.
    ``layout="instance"``: zangstuk uit VSA+template.

    Verticaal: geen page-fill (`enableVerticalSpread=0`, `maxPageFillSpread=0`).
    Systeemmafruimte en titel→eerste-systeem via ``_vertical_layout_gaps``;
    min=max zodat de pagina niet wordt uitgevuld.
    """
    staff_dist, min_sys, frame_sys = _vertical_layout_gaps(layout=layout)
    max_sys = min_sys
    akk_dist = staff_dist
    if layout == "instance":
        min_note = INSTANCE_MIN_NOTE_DISTANCE
        lyrics_min = INSTANCE_LYRICS_MIN_DISTANCE
        fill_limit = "0"
        border = "2.0"
        lyrics_bottom = "1.0"
        courtesy = (
            "<genCourtesyTimesig>0</genCourtesyTimesig>"
            "<genCourtesyKeysig>0</genCourtesyKeysig>"
            f"<measureSpacing>{INSTANCE_MEASURE_SPACING}</measureSpacing>"
            f"<minMeasureWidth>{INSTANCE_MIN_MEASURE_WIDTH}</minMeasureWidth>"
        )
    else:
        min_note = "0.5"
        lyrics_min = "0.25"
        fill_limit = "1"
        border = f"{TEMPLATE_STAFF_UPPER_BORDER_SP:g}"
        lyrics_bottom = "1.0"
        courtesy = ""
    return (
        "<Style>"
        f"{_page_style(layout=layout, n_systems=n_systems)}"
        "<enableVerticalSpread>0</enableVerticalSpread>"
        "<maxPageFillSpread>0</maxPageFillSpread>"
        f"<minSystemSpread>{min_sys}</minSystemSpread>"
        f"<maxSystemSpread>{max_sys}</maxSystemSpread>"
        f"<minStaffSpread>{staff_dist}</minStaffSpread>"
        f"<maxStaffSpread>{staff_dist}</maxStaffSpread>"
        f"<staffDistance>{staff_dist}</staffDistance>"
        f"<akkoladeDistance>{akk_dist}</akkoladeDistance>"
        f"<maxAkkoladeDistance>{akk_dist}</maxAkkoladeDistance>"
        f"<minSystemDistance>{min_sys}</minSystemDistance>"
        f"<maxSystemDistance>{max_sys}</maxSystemDistance>"
        f"<staffUpperBorder>{border}</staffUpperBorder>"
        f"<staffLowerBorder>{border if layout == 'instance' else '3'}</staffLowerBorder>"
        f"<frameSystemDistance>{frame_sys}</frameSystemDistance>"
        f"<systemFrameDistance>{frame_sys}</systemFrameDistance>"
        f"<lyricsMinBottomDistance>{lyrics_bottom}</lyricsMinBottomDistance>"
        "<lyricsMinTopDistance>0.5</lyricsMinTopDistance>"
        "<enableIndentationOnFirstSystem>0</enableIndentationOnFirstSystem>"
        "<firstSystemIndentationValue>0</firstSystemIndentationValue>"
        f"<lastSystemFillLimit>{fill_limit}</lastSystemFillLimit>"
        # Formuleblad: geen S/A/T/B-namen, geen maatnummers (botsen met [1]/[2]).
        "<firstSystemInstNameVisibility>0</firstSystemInstNameVisibility>"
        "<subsSystemInstNameVisibility>0</subsSystemInstNameVisibility>"
        f"<showMeasureNumber>{0 if layout != 'instance' else 1}</showMeasureNumber>"
        "<showMeasureNumberOne>0</showMeasureNumberOne>"
        f"{courtesy}"
        f'<staffTextPosAbove x="0" y="{MAPPING_TEXT_Y}"/>'
        f"<staffFontFace>{STAFF_FONT}</staffFontFace>"
        f"<staffFontSize>{STAFF_FONT_PT}</staffFontSize>"
        "<staffFontSpatiumDependent>0</staffFontSpatiumDependent>"
        f"<frameFontFace>{STAFF_FONT}</frameFontFace>"
        f"<frameFontSize>{FRAME_FONT_PT}</frameFontSize>"
        "<frameFontSpatiumDependent>0</frameFontSpatiumDependent>"
        f"<lyricsOddFontFace>{LYRIC_FONT}</lyricsOddFontFace>"
        f"<lyricsOddFontSize>{LYRIC_FONT_PT}</lyricsOddFontSize>"
        "<lyricsOddFontSpatiumDependent>0</lyricsOddFontSpatiumDependent>"
        f"<lyricsEvenFontFace>{LYRIC_FONT}</lyricsEvenFontFace>"
        f"<lyricsEvenFontSize>{LYRIC_FONT_PT}</lyricsEvenFontSize>"
        "<lyricsEvenFontSpatiumDependent>0</lyricsEvenFontSpatiumDependent>"
        f"<lyricsMinDistance>{lyrics_min}</lyricsMinDistance>"
        f"<minNoteDistance>{min_note}</minNoteDistance>"
        "</Style>"
    )


def _mscx_cycle_text(label: str) -> str:
    inner = (
        f'<font size="{FRAME_FONT_PT}"/><font face="{STAFF_FONT}"/>'
        f"{escape(label)}"
    )
    return (
        "<Text>"
        "<style>frame</style>"
        "<align>center,center</align>"
        f"<family>{STAFF_FONT}</family>"
        f"<size>{FRAME_FONT_PT}</size>"
        f"<text>{inner}</text>"
        "</Text>"
    )


def _mscx_append_cycle_frames(
    out: list[str],
    label: str | None,
    *,
    last_quarters: int,
    alone_on_system: bool,
) -> None:
    """After last measure: spacer HBox + cycle HBox, or VBox if too little room."""
    if not label:
        return
    use_hbox = alone_on_system and last_quarters <= CYCLE_HBOX_MAX_LAST_QUARTERS
    if use_hbox:
        out.append(f"<HBox><width>{CYCLE_SPACER_HBOX_WIDTH}</width></HBox>")
        out.append(
            f"<HBox><width>{CYCLE_TEXT_HBOX_WIDTH}</width>"
            f"{_mscx_cycle_text(label)}"
            "</HBox>"
        )
    else:
        out.append(
            "<VBox>"
            "<height>4</height>"
            f"{_mscx_cycle_text(label)}"
            "</VBox>"
        )


def resolve_phrase_id_sequence(
    doc: dict, phrase_ids: list[str]
) -> list[tuple[str, list[dict]]]:
    phrases = {str(p["id"]): p for p in doc["phrases"]}
    do = doc["do"]
    mode = doc.get("mode", "major")
    resolved: list[tuple[str, list[dict]]] = []
    for pid in phrase_ids:
        if pid not in phrases:
            raise KeyError(f"unknown phrase id {pid!r}")
        events, _total = resolve_phrase_events(phrases[pid], do, mode)
        resolved.append((pid, events))
    return resolved


def render_mscx(
    doc: dict,
    resolved: list[tuple[str, list[dict]]],
    *,
    title: str,
    cycle_label_text: str | None = None,
    cycle_repeats: bool = False,
    system_break_each: bool = False,
    layout: str = "template",
    mapping_labels: bool | None = None,
) -> str:
    """MuseScore 4 native score: Style + trailing HBox/VBox + SATB parts.

    ``mapping_labels``: frase-ids, ankers, cycle-frames. Default: aan voor
    template, uit voor instance (VSA+template).
    """
    if mapping_labels is None:
        mapping_labels = layout != "instance"
    fifths = fifths_for(doc["do"], doc.get("mode", "major"))
    n_phr = len(resolved)

    out: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<museScore version="4.70">',
        "<programVersion>4.7.4</programVersion>",
        "<Score>",
        "<Division>480</Division>",
        _mscx_style_block(
            layout=layout,
            n_systems=max(
                1,
                math.ceil(n_phr / TEMPLATE_PHRASES_PER_SYSTEM)
                if layout == "template"
                else n_phr,
            ),
        ),
        f'<metaTag name="workTitle">{escape(title)}</metaTag>',
        '<metaTag name="platform">Microsoft Windows</metaTag>',
        '<Part id="1">',
        "<Staff>",
        '<StaffType group="pitched"><name>stdNormal</name></StaffType>',
        '<bracket type="0" span="2" col="0" visible="1"/>',
        # Instance: maatsoort bestaat (geen +/-) maar wordt niet getekend.
        f"<showTimeSig>{1 if mapping_labels else 0}</showTimeSig>",
        "</Staff>",
        "<trackName>Women</trackName>",
        '<Instrument id="women">',
        # Formuleblad/instance: geen S/A/T/B-naam links van de balk.
        "<longName></longName><shortName></shortName>",
        "<trackName>Women</trackName>",
        "<instrumentId>voice.female</instrumentId>",
        "</Instrument>",
        "</Part>",
        '<Part id="2">',
        "<Staff>",
        '<StaffType group="pitched"><name>stdNormal</name></StaffType>',
        # MuseScore 4 draws the staff clef from these defaults (not only
        # Instrument <clef>). F = bass clef for TB.
        "<defaultConcertClef>F</defaultConcertClef>",
        "<defaultTransposingClef>F</defaultTransposingClef>",
        f"<showTimeSig>{1 if mapping_labels else 0}</showTimeSig>",
        "</Staff>",
        "<trackName>Men</trackName>",
        '<Instrument id="men">',
        "<longName></longName><shortName></shortName>",
        "<trackName>Men</trackName>",
        "<instrumentId>voice.male</instrumentId>",
        "<clef>F</clef>",
        "</Instrument>",
        "</Part>",
    ]

    for staff_i, part in enumerate(PARTS, start=1):
        out.append(f'<Staff id="{staff_i}">')
        if staff_i == 1:
            inner_title = (
                f'<font size="{TITLE_FONT_PT}"/><font face="{STAFF_FONT}"/>'
                f"{escape(title)}"
            )
            out.append(
                "<VBox>"
                f"<height>{TITLE_VBOX_HEIGHT_SP:g}</height>"
                "<Text>"
                "<style>title</style>"
                f"<family>{STAFF_FONT}</family>"
                f"<size>{TITLE_FONT_PT}</size>"
                f"<text>{inner_title}</text>"
                "</Text>"
                "</VBox>"
            )
        last_quarters = 0
        # Cycle-HBox: formuleblad mag trailing frames naast de laatste frase.
        alone_on_system = system_break_each or (layout == "template" and n_phr > 1)
        # Instance: layout-maten binnen strofe; zichtbare maatstreep alleen
        # aan strofe-eind. Template: een maat per frase.
        measure_jobs: list[
            tuple[str | None, list[dict], bool, bool, bool, bool]
        ] = []
        for pi, (pid, events) in enumerate(resolved):
            is_last_phrase = pi == n_phr - 1
            chunk_events = (
                _with_phrase_lead_spacer(events)
                if layout == "template" and mapping_labels
                else events
            )
            if is_last_phrase:
                last_quarters = int(round(events_quarters(chunk_events)))
            # Instance: één maat per strofe — geen binnen-strofe-maatstrepen
            # (recite-tekst + slotnoot + cadens horen visueel bij elkaar).
            chunks = [chunk_events]
            for ci, chunk in enumerate(chunks):
                measure_jobs.append(
                    (
                        pid,
                        chunk,
                        pi == 0 and ci == 0,
                        ci == 0,
                        ci == len(chunks) - 1,
                        is_last_phrase and ci == len(chunks) - 1,
                    )
                )

        for mi, job in enumerate(measure_jobs, start=1):
            pid, events, is_first, phrase_start, stanza_end, piece_end = job
            start_rep, end_rep = False, None
            if cycle_repeats and phrase_start:
                start_rep, _ = cycle_repeat_flags(doc, pid or "")
            if cycle_repeats and stanza_end:
                _, end_rep = cycle_repeat_flags(doc, pid or "")

            len_attr = events_len_attr(events)
            out.append(f'<Measure len="{len_attr}">')
            if layout == "instance":
                out.append("<stretch>0.85</stretch>")
            if start_rep:
                out.append("<startRepeat/>")
            # Formuleblad: bij voorkeur twee frasen per systeem.
            if (
                staff_i == 1
                and not piece_end
                and stanza_end
                and layout == "template"
                and n_phr > 1
                and mi % TEMPLATE_PHRASES_PER_SYSTEM == 0
            ):
                out.append(
                    "<LayoutBreak><subtype>line</subtype></LayoutBreak>"
                )
            if end_rep is not None:
                out.append(f"<endRepeat>{end_rep}</endRepeat>")
            # MuseScore 4: maatstreep-zichtbaarheid via <BarLine> in de voice,
            # niet via Measure/endBarLineVisible (wordt genegeerd).
            if piece_end:
                bar_subtype, bar_visible = "end", True
            elif layout == "instance" and not stanza_end:
                bar_subtype, bar_visible = "normal", False
            else:
                bar_subtype, bar_visible = "normal", True
            if layout == "instance":
                sig_n, sig_d = (int(x) for x in len_attr.split("/"))
                measure_time_sig: tuple[int, int] | None = (sig_n, sig_d)
            elif is_first:
                measure_time_sig = (4, 4)
            else:
                measure_time_sig = None
            # Bij cycle-endRepeat laat MuseScore de herhaal-maatstreep tekenen.
            emit_bar = end_rep is None
            if layout == "instance":
                chord_keys = ("S", "A") if staff_i == 1 else ("T", "B")
                out.extend(
                    _mscx_voice(
                        events,
                        chord_keys,
                        frase_id=(
                            pid
                            if mapping_labels
                            and staff_i == 1
                            and phrase_start
                            and pid is not None
                            else None
                        ),
                        anchors=mapping_labels and staff_i == 1,
                        keysig=is_first,
                        fifths=fifths,
                        time_sig=measure_time_sig,
                        with_lyrics=staff_i == 1,
                        end_barline=bar_subtype if emit_bar else None,
                        end_barline_visible=bar_visible,
                    )
                )
            else:
                out.extend(
                    _mscx_voice(
                        events,
                        part["v1"],
                        frase_id=(
                            pid
                            if mapping_labels
                            and staff_i == 1
                            and pid is not None
                            else None
                        ),
                        anchors=mapping_labels and staff_i == 1,
                        keysig=is_first,
                        fifths=fifths,
                        time_sig=measure_time_sig,
                        with_lyrics=staff_i == 1,
                        end_barline=bar_subtype if emit_bar else None,
                        end_barline_visible=bar_visible,
                    )
                )
                out.extend(
                    _mscx_voice(
                        events,
                        part["v2"],
                    )
                )
            out.append("</Measure>")
        if staff_i == 1 and mapping_labels:
            _mscx_append_cycle_frames(
                out,
                cycle_label_text,
                last_quarters=last_quarters,
                alone_on_system=alone_on_system,
            )
        out.append("</Staff>")

    out.append("</Score>")
    out.append("</museScore>")
    return "\n".join(out)


def render_template_mscx(doc: dict) -> str:
    """Abstract template (3 frasen + cycle-repeat barlines)."""
    phrase_ids = [str(p["id"]) for p in phrase_order(doc)]
    resolved = resolve_phrase_id_sequence(doc, phrase_ids)
    return render_mscx(
        doc,
        resolved,
        title=score_title(doc),
        cycle_label_text=cycle_label(doc),
        cycle_repeats=True,
    )


def render_expanded_mscx(
    doc: dict,
    phrase_ids: list[str],
    *,
    title: str,
    cycle_label_text: str | None = None,
) -> str:
    """Uitgevouwen formule: één maat per toegewezen template-frase (geen repeats)."""
    resolved = resolve_phrase_id_sequence(doc, phrase_ids)
    label = cycle_label_text if cycle_label_text is not None else ", ".join(phrase_ids)
    return render_mscx(
        doc,
        resolved,
        title=title,
        cycle_label_text=label,
        cycle_repeats=False,
    )


def mapped_notes_to_events(notes: list, do: str, mode: str) -> list[dict]:
    """Mapped notes → MSCX/MXL event dicts (S uit VSA, A/T/B uit template).

    H5: één ``dur``/``ntype``/``dots`` per event uit de VSA-noot — A/T/B
    krijgen hetzelfde ritme (geen aparte template-ELM op instance).
    """
    events: list[dict] = []
    for note in notes:
        template_event = note.template_event
        s_pitch = note.s_pitch
        role = template_event.get("role")
        events.append(
            {
                "pitches": {
                    "S": (s_pitch.step, int(s_pitch.alter), s_pitch.octave),
                    "A": resolve_degree(template_event["pitches"]["A"], do, mode),
                    "T": resolve_degree(template_event["pitches"]["T"], do, mode),
                    "B": resolve_degree(template_event["pitches"]["B"], do, mode),
                },
                "dur": note.duration.divisions_value,
                "ntype": note.duration.note_type,
                "dots": note.duration.dots,
                "optional": False,
                # Voor print-collapse; Coria-pad zet dit later uit of negeert het.
                "recite": role == "recite",
                "role": role,
                "anchor": template_event.get("anchor") if note.show_anchor else None,
                "lyric": note.lyric or None,
                "syllabic": note.syllabic,
            }
        )
    return events


def _join_recite_lyrics(notes: list[dict]) -> str:
    """Lettergrepen → leesbare tekst: streepjes binnen woorden, spaties ertussen."""
    parts: list[str] = []
    for e in notes:
        raw = e.get("lyric")
        if not raw:
            continue
        text = str(raw).rstrip("-")
        syl = e.get("syllabic") or "single"
        if parts and not parts[-1].endswith("-"):
            parts.append(" ")
        parts.append(text)
        if syl in ("begin", "middle"):
            parts.append("-")
    return "".join(parts)


def _invisible_rest(dur: int, ntype: str) -> dict:
    return {
        "pitches": {"S": ("C", 0, 4), "A": ("C", 0, 4), "T": ("C", 0, 3), "B": ("C", 0, 3)},
        "dur": dur,
        "ntype": ntype,
        "dots": 0,
        "optional": False,
        "recite": False,
        "rest": True,
        "visible": False,
    }


def _recite_body_spacer(note: dict, *, ntype: str, dur: int, dots: int) -> dict:
    """Onzichtbare stille noot met lyric: ruimte tussen recite-lettergrepen.

    Geen rust: MuseScore toont lyrics op verborgen rusten niet betrouwbaar.
    Extra systeemruimte valt tussen deze lettergrepen, niet als gap ná de tekst.
    """
    spacer = dict(note)
    spacer["dur"] = dur
    spacer["ntype"] = ntype
    spacer["dots"] = dots
    spacer["recite"] = False
    spacer["spacer"] = True
    spacer["keep_with_next"] = True
    for key in (
        "lyric_ticks",
        "lyric_extend",
        "slur_next",
        "slur_prev",
        "lyric_align",
        "rest",
        "visible",
    ):
        spacer.pop(key, None)
    return spacer


def collapse_recite_for_print(events: list[dict]) -> list[dict]:
    """Ongemarkeerde recite (≥3) → ||O|| + laatste lettergreep als kwart.

    Alleen ``role=recite`` (ongemarkeerde VSA-syllaben). Elke VSA-scope
    (``{/en}``, ``{moe__}``, ``{Ni__}``, …) blijft een eigen noot met VSA-duur —
    nooit breve, nooit opgeslokt.

    Printmodel:

    - eerste body-lettergreep op de ``||O||``, **gecentreerd** op de nootkop;
    - overige body-lettergrepen elk op een onzichtbare spacer-noot (naar rechts);
    - laatste recite-syllabe = kwart; daarna template-cadens ongewijzigd.
    - geen melisma-extender onder de recitaltekst.

    Alleen MSCZ/print (niet Coria-MXL).
    """
    if not events:
        return []
    out: list[dict] = []
    i = 0
    q_dur, q_type, q_dots = ELM_DIV["~"]
    while i < len(events):
        if not events[i].get("recite"):
            ev = dict(events[i])
            ev["recite"] = False
            out.append(ev)
            i += 1
            continue
        j = i
        while j < len(events) and events[j].get("recite"):
            j += 1
        run = [dict(e) for e in events[i:j]]
        if len(run) < RECITE_COLLAPSE_MIN_SYLLABLES:
            for note in run:
                ev = dict(note)
                ev["recite"] = False
                out.append(ev)
            i = j
            continue
        body, last = run[:-1], run[-1]
        first, rest = body[0], body[1:]
        breve = dict(first)
        dur, ntype, _dots = RECITE_PLAY_DIV  # altijd half, geen punt
        breve["dur"] = dur
        breve["ntype"] = ntype
        breve["dots"] = 0
        breve["recite"] = True
        breve["keep_with_next"] = True
        # Eerste lettergreep gecentreerd op de nootkop (MuseScore-default).
        for key in (
            "lyric_align",
            "lyric_ticks",
            "lyric_extend",
            "slur_next",
            "slur_prev",
        ):
            breve.pop(key, None)
        last_ev = dict(last)
        last_ev["recite"] = False
        last_ev["dur"] = q_dur
        last_ev["ntype"] = q_type
        last_ev["dots"] = q_dots
        for key in (
            "lyric_ticks",
            "lyric_extend",
            "slur_next",
            "slur_prev",
            "lyric_align",
        ):
            last_ev.pop(key, None)
        out.append(breve)
        out.extend(
            _recite_body_spacer(note, ntype=q_type, dur=q_dur, dots=q_dots)
            for note in rest
        )
        out.append(last_ev)
        i = j
    return out


def render_instance_mscx(
    doc: dict,
    mapped: list[tuple[str, list]],
    *,
    title: str,
) -> str:
    """Uitgeschreven tropaar: VSA-S + template A/T/B; instance-layout.

    Één maat per strofe. Recite (≥3 ongemarkeerd): ||O|| met eerste
    lettergreep gecentreerd; overige body-lettergrepen op spacer-noten;
    slotlettergreep als kwart; VSA-scopes blijven eigen noten met hun duur.
    """
    do = doc["do"]
    mode = doc.get("mode", "major")
    resolved: list[tuple[str | None, list[dict]]] = []
    last_i = len(mapped) - 1
    gap_dur, gap_type = INSTANCE_PHRASE_GAP
    for i, (pid, notes) in enumerate(mapped):
        events = prepare_instance_events(
            collapse_recite_for_print(mapped_notes_to_events(notes, do, mode))
        )
        if i < last_i:
            events.append(_invisible_rest(gap_dur, gap_type))
        resolved.append((pid, events))
    return render_mscx(
        doc,
        resolved,
        title=title,
        cycle_label_text=None,
        cycle_repeats=False,
        system_break_each=False,
        layout="instance",
        mapping_labels=False,
    )


def _instance_score_header(title: str) -> list[str]:
    """Vier aparte score-parts (S/A/T/B) voor Coria-solo per stem.

    Geen DOCTYPE: sommige players (o.a. Coria) falen op DTD-fetch/validatie.
    """
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<score-partwise version="4.0">',
        f"<work><work-title>{escape(title)}</work-title></work>",
        "<identification><encoding>"
        "<software>render_vsa_template_musicxml.py</software>"
        "</encoding></identification>",
        "<part-list>",
        '<part-group type="start" number="1">'
        "<group-symbol>bracket</group-symbol></part-group>",
    ]
    for part in INSTANCE_PARTS:
        out.append(
            f'<score-part id="{part["id"]}">'
            f"<part-name>{escape(part['name'])}</part-name>"
            f"<part-abbreviation>{escape(part['abbr'])}</part-abbreviation>"
            "</score-part>"
        )
    out.append('<part-group type="stop" number="1"/>')
    out.append("</part-list>")
    return out


def emit_instance_voice(
    out: list[str],
    events: list[dict],
    *,
    voice_key: str,
    with_lyrics: bool,
    fifths: int = 0,
    stem: str | None = None,
) -> None:
    """Één MusicXML-stem; lyrics + slurs. Geen lege lyric-extends (breekt Coria)."""
    slur_number = 0
    active_slur: int | None = None
    for ev in events:
        slur = None
        number = 1
        if ev.get("slur_next"):
            slur_number += 1
            active_slur = slur_number
            slur = "start"
            number = active_slur
        elif ev.get("slur_prev"):
            slur = "stop"
            number = active_slur or 1
            active_slur = None
        lyric = ev.get("lyric") if with_lyrics else None
        extend_type = None
        if with_lyrics and lyric and ev.get("lyric_extend"):
            extend_type = "start"
        emit_note(
            out,
            ev["pitches"][voice_key],
            ev["dur"],
            ev["ntype"],
            ev["dots"],
            1,
            stem,
            optional=ev["optional"],
            recite=False,
            lyric=lyric,
            syllabic=ev.get("syllabic") or "single",
            lyric_extend_type=extend_type,
            slur=slur,
            slur_number=number,
            fifths=fifths,
            musicxml_hyphens_from_syllabic=True,
        )


def render_instance_musicxml(
    doc: dict,
    mapped: list[tuple[str, list]],
    *,
    title: str,
) -> str:
    """Coria/playback MusicXML: vier parts; één maat per strofe; slurs/lyrics.

    Geen recite-collapse: elke syllabe blijft een noot (solo-oefenen).
    """
    do = doc["do"]
    mode = doc.get("mode", "major")
    fifths = fifths_for(do, mode)
    measures: list[list[dict]] = []
    for _pid, notes in mapped:
        # Coria: alle syllaben als quarters; geen breve-printmodel.
        raw = mapped_notes_to_events(notes, do, mode)
        for ev in raw:
            ev["recite"] = False
        events = prepare_instance_events(raw)
        measures.append(events)

    out: list[str] = _instance_score_header(title)
    for part in INSTANCE_PARTS:
        out.append(f'<part id="{part["id"]}">')
        for mi, events in enumerate(measures, start=1):
            is_first = mi == 1
            is_last = mi == len(measures)
            out.append(f'<measure number="{mi}">')
            if is_first:
                out.append("<attributes>")
                out.append("<divisions>4</divisions>")
                out.append(f"<key><fifths>{fifths}</fifths></key>")
                out.append("<time><senza-misura/></time>")
                out.append(
                    f'<clef><sign>{part["clef_sign"]}</sign>'
                    f'<line>{part["clef_line"]}</line></clef>'
                )
                out.append("</attributes>")
            emit_instance_voice(
                out,
                events,
                voice_key=part["voice"],
                with_lyrics=bool(part["lyrics"]),
                fifths=fifths,
                stem=None,
            )
            if is_last:
                out.append(
                    '<barline location="right">'
                    "<bar-style>light-heavy</bar-style></barline>"
                )
            else:
                out.append(
                    '<barline location="right">'
                    "<bar-style>regular</bar-style></barline>"
                )
            out.append("</measure>")
        out.append("</part>")
    out.append("</score-partwise>")
    return "\n".join(out)


def _score_style_mss(mscx: str) -> str:
    """MuseScore 4 leest layout bij voorkeur uit ``score_style.mss`` in de MSCZ."""
    start = mscx.find("<Style>")
    end = mscx.find("</Style>")
    if start < 0 or end < 0:
        raise ValueError("MSCZ zonder <Style>-blok")
    style = mscx[start : end + len("</Style>")]
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<museScore version="4.70">\n'
        f"{style}\n"
        "</museScore>\n"
    )


def write_mscx_output(path: Path, mscx: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".mscz":
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("META-INF/container.xml", _MSCZ_CONTAINER)
            archive.writestr("score.mscx", mscx)
            # MS4: Style in MSCX alleen is niet genoeg; score_style.mss is leidend.
            archive.writestr("score_style.mss", _score_style_mss(mscx))
    else:
        path.write_text(mscx, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("template", nargs="?", type=Path)
    parser.add_argument("output", nargs="?", type=Path)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--elia-r1", type=Path, help="Write Elia R1 instance MusicXML")
    args = parser.parse_args()

    sys.path.insert(0, str(REPO / "src"))
    from vsa.musicxml_package import write_musicxml_output

    if args.elia_r1:
        write_musicxml_output(args.elia_r1, render_elia_r1_musicxml())
        print(f"wrote {args.elia_r1}")
        return 0

    if args.all:
        for yaml_path in sorted(LIBRARY.glob("*/template.yaml")):
            doc_raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if isinstance(doc_raw, dict) and "same_as" in doc_raw:
                print(f"skip alias {yaml_path.parent.name} (same_as)")
                continue
            doc = load_resolved(yaml_path, LIBRARY)
            out_mxl = yaml_path.with_name("template.mxl")
            out_mscz = yaml_path.with_name("template.mscz")
            write_musicxml_output(out_mxl, render_template_musicxml(doc))
            write_mscx_output(out_mscz, render_template_mscx(doc))
            print(f"wrote {out_mxl.relative_to(REPO)}")
            print(f"wrote {out_mscz.relative_to(REPO)}")
        return 0

    if not args.template:
        parser.error("template path or --all required")
    doc = load_resolved(args.template, LIBRARY)
    out = args.output or args.template.with_name("template.mxl")
    suffix = out.suffix.lower()
    if suffix in {".mscx", ".mscz"}:
        write_mscx_output(out, render_template_mscx(doc))
    else:
        write_musicxml_output(out, render_template_musicxml(doc))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
