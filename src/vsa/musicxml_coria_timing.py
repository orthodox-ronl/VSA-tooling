"""Coria-playback timing transforms on MusicXML (port uit VSA-demo).

Na dubbele maatstreep (``light-light``): extra maat met whole-rest + lyric
``[PAUZE]``; cue-directions (``P:``/``D:``/``K:``) van de volgende koormaat
erboven. Gebogen cesuur: kwart-rust erna, zonder lyric.

Op het MVSA→playback-pad gebeurt ``[PAUZE]`` al in ``mvsa_musicxml`` (ook vóór
mid-flow ``@tekst``). Deze module blijft de MSCZ→MXL-transform (light-light).
"""

from __future__ import annotations

import copy
import re
from xml.etree import ElementTree as ET

CUE_RE = re.compile(r"^\s*[PDK]\s*[:;]", re.I)
PAUSE_LYRIC = "[PAUZE]"

_NS_STRIP = re.compile(r"^\{[^}]+\}")


def local(tag: str) -> str:
    return _NS_STRIP.sub("", tag)


def apply_coria_timing(xml: str) -> str:
    """Insert ``[PAUZE]`` after double bars and caesura quarter rests."""
    root = ET.fromstring(xml)
    parts = _music_parts(root)
    if not parts:
        return xml
    div = _divisions_of(root)
    insert_pause_measures(parts, whole_dur=4 * div)
    insert_caesura_quarter_rests(parts, quarter=div)
    _renumber_measures(root)
    return _serialize(root)


def insert_pause_measures(parts: list[ET.Element], whole_dur: int) -> int:
    """Na elke dubbele streep: whole-rest + ``[PAUZE]``; cue van de volgende maat."""
    if not parts:
        return 0
    soprano = _children(parts[0], "measure")
    insert_after = [
        i for i in range(len(soprano) - 1) if _has_double_bar(soprano[i])
    ]
    n = 0
    for i in reversed(insert_after):
        next_measures = [_children(p, "measure")[i + 1] for p in parts]
        cues = _steal_cue_directions(next_measures[0])
        for extra in next_measures[1:]:
            _steal_cue_directions(extra)
        number = f"{next_measures[0].get('number', i + 2)}p"
        for part, nxt in zip(parts, next_measures):
            pause = _make_pause_measure(number, rest_dur=whole_dur, cues=cues)
            part.insert(list(part).index(nxt), pause)
        n += 1
    return n


def insert_caesura_quarter_rests(parts: list[ET.Element], quarter: int) -> int:
    """Gebogen cesuur: 1 kwart rust op hetzelfde moment in alle parts, geen lyric."""
    if not parts:
        return 0
    n = 0
    n_meas = len(_children(parts[0], "measure"))
    for mi in range(n_meas):
        group = [_children(p, "measure")[mi] for p in parts]
        cuts: set[int] = set()
        for m in group:
            t = 0
            for note in _children(m, "note"):
                if _is_chord(note):
                    continue
                t += _note_duration(note)
                if _note_has_caesura(note):
                    cuts.add(t)
        for t_cut in sorted(cuts, reverse=True):
            for m in group:
                if _insert_rest_after_time(m, t_cut, quarter):
                    n += 1
    return n


def _music_parts(root: ET.Element) -> list[ET.Element]:
    return [el for el in root if local(el.tag) == "part"]


def _child(el: ET.Element, name: str) -> ET.Element | None:
    for c in el:
        if local(c.tag) == name:
            return c
    return None


def _children(el: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in el if local(c.tag) == name]


def _text(el: ET.Element | None) -> str:
    return (el.text or "").strip() if el is not None else ""


def _is_chord(note: ET.Element) -> bool:
    return any(local(c.tag) == "chord" for c in note)


def _note_duration(note: ET.Element) -> int:
    d = _child(note, "duration")
    if d is not None and _text(d).isdigit():
        return int(_text(d))
    return 0


def _note_has_caesura(note: ET.Element) -> bool:
    return any(local(el.tag) == "caesura" for el in note.iter())


def _has_double_bar(measure: ET.Element) -> bool:
    for bar in _children(measure, "barline"):
        if _text(_child(bar, "bar-style")) == "light-light":
            return True
    return False


def _direction_is_cue(direction: ET.Element) -> bool:
    words = " ".join(
        (el.text or "") for el in direction.iter() if local(el.tag) == "words"
    )
    return bool(CUE_RE.search(words.strip()))


def _steal_cue_directions(measure: ET.Element) -> list[ET.Element]:
    stolen: list[ET.Element] = []
    for el in list(measure):
        if local(el.tag) == "direction" and _direction_is_cue(el):
            measure.remove(el)
            stolen.append(el)
    return stolen


def _divisions_of(root: ET.Element) -> int:
    for part in _music_parts(root):
        for measure in _children(part, "measure"):
            attrs = _child(measure, "attributes")
            if attrs is None:
                continue
            div = _child(attrs, "divisions")
            if div is not None and _text(div).isdigit():
                return int(_text(div))
    return 4


def _make_rest_note(
    duration: int, *, type_name: str, lyric: str | None = None
) -> ET.Element:
    note = ET.Element("note")
    ET.SubElement(note, "rest")
    ET.SubElement(note, "duration").text = str(duration)
    ET.SubElement(note, "voice").text = "1"
    ET.SubElement(note, "type").text = type_name
    if lyric:
        ly = ET.SubElement(note, "lyric", number="1")
        ET.SubElement(ly, "syllabic").text = "single"
        ET.SubElement(ly, "text").text = lyric
    return note


def _make_pause_measure(
    number: str, *, rest_dur: int, cues: list[ET.Element]
) -> ET.Element:
    measure = ET.Element("measure", number=number)
    for cue in cues:
        measure.append(copy.deepcopy(cue))
    measure.append(_make_rest_note(rest_dur, type_name="whole", lyric=PAUSE_LYRIC))
    bar = ET.SubElement(measure, "barline", location="right")
    ET.SubElement(bar, "bar-style").text = "light-light"
    return measure


def _insert_rest_after_time(measure: ET.Element, t_cut: int, duration: int) -> bool:
    t = 0
    for el in list(measure):
        if local(el.tag) != "note" or _is_chord(el):
            continue
        t += _note_duration(el)
        if t == t_cut:
            rest = _make_rest_note(duration, type_name="quarter")
            measure.insert(list(measure).index(el) + 1, rest)
            return True
    return False


def _renumber_measures(root: ET.Element) -> None:
    for part in _music_parts(root):
        for i, measure in enumerate(_children(part, "measure"), start=1):
            measure.set("number", str(i))


def _serialize(root: ET.Element) -> str:
    """Serialize zonder DOCTYPE (Coria faalt op DTD-fetch)."""
    body = ET.tostring(root, encoding="unicode")
    if body.startswith("<?xml"):
        return body
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + body


_DOCTYPE_RE = re.compile(r"<!DOCTYPE[^>]*(?:\[.*?\])?\s*>", re.I | re.S)

_NOTE_MARKUP = frozenset({"beam", "stem", "notations", "accidental"})
_LAYOUT_ATTR_PREFIXES = ("default-", "relative-")
_LAYOUT_ATTRS = frozenset({"width", "print-object", "color"})
CORIA_FORBIDDEN_TAGS = frozenset(
    {"beam", "stem", "notations", "part-group", "movement-title", "supports", "tie"}
)
_STEPS = "CDEFGAB"
_SHARP_ORDER = "FCGDAEB"
_FLAT_ORDER = "BEADGCF"
_ALTER_TO_ACCIDENTAL = {
    -2: "double-flat",
    -1: "flat",
    0: "natural",
    1: "sharp",
    2: "double-sharp",
}


def strip_doctype(xml: str) -> str:
    """Verwijder MusicXML-DOCTYPE (Coria DTD-fetch)."""
    return _DOCTYPE_RE.sub("", xml, count=1).lstrip()


_LICENSE_IN_TEXT = re.compile(
    r"(?i)\b(CC\s*BY|creativecommons|colofon|all\s+rights\s+reserved)\b"
)


def _misc_field(ident: ET.Element, name: str) -> ET.Element | None:
    misc = _child(ident, "miscellaneous")
    if misc is None:
        return None
    for field in _children(misc, "miscellaneous-field"):
        if field.get("name") == name:
            return field
    return None


def _set_misc_field(ident: ET.Element, name: str, value: str) -> None:
    misc = _child(ident, "miscellaneous")
    if misc is None:
        misc = ET.SubElement(ident, "miscellaneous")
    field = _misc_field(ident, name)
    if field is None:
        field = ET.SubElement(misc, "miscellaneous-field", name=name)
    field.text = value


def strip_coria_identification_source(root: ET.Element) -> int:
    """Verwijder ``identification/source`` (Coria faalt op source+encoding).

    Bewaar de tekst in ``miscellaneous-field name="bron"`` als die nog leeg is.
    Returns aantal verwijderde ``<source>``-elementen.
    """
    n = 0
    ident = _child(root, "identification")
    if ident is None:
        return 0
    source_el = _child(ident, "source")
    if source_el is None:
        return 0
    text = _text(source_el)
    if text and not _text(_misc_field(ident, "bron")):
        _set_misc_field(ident, "bron", text)
    ident.remove(source_el)
    return 1


def sanitize_coria_importer(root: ET.Element) -> None:
    """Strip visuele MusicXML die Coria's vertaler laat crashen (VSA-demo-port)."""
    root.set("version", "3.1")
    # Engraving-only layout block (checklist M9).
    for el in list(root):
        if local(el.tag) == "defaults":
            root.remove(el)
    # Geen strip van movement-title: MVSA zet ``@ondertitel`` daar (cues zitten
    # in ``<direction>``, niet in movement-title zoals Capella soms deed).
    ident = _child(root, "identification")
    if ident is not None:
        enc = _child(ident, "encoding")
        if enc is not None:
            for el in list(enc):
                if local(el.tag) == "supports":
                    enc.remove(el)
        # Coria: ``<source>`` + ``<encoding>`` → "translation failed".
        # Bronvermelding blijft in miscellaneous-field ``bron``.
        strip_coria_identification_source(root)
        _ensure_bron_misc_when_rights_is_license(root, ident)
    for el in list(root.iter()):
        for attr in list(el.attrib):
            if attr.startswith(_LAYOUT_ATTR_PREFIXES) or attr in _LAYOUT_ATTRS:
                del el.attrib[attr]
        if local(el.tag) != "note":
            continue
        for child_el in list(el):
            ctag = local(child_el.tag)
            if ctag in _NOTE_MARKUP or ctag == "tie":
                el.remove(child_el)
                continue
            if ctag != "lyric":
                continue
            # Lyric ``<extend/>`` behouden (checklist M5); demo stripte die voor NWC.
    plist = _child(root, "part-list")
    if plist is not None:
        for el in list(plist):
            if local(el.tag) == "part-group":
                plist.remove(el)


def _ensure_bron_misc_when_rights_is_license(
    root: ET.Element, ident: ET.Element
) -> None:
    """Checklist META: rights met licentie eist bron in misc-field ``bron``.

    Geen ``identification/source``: Coria faalt op source+encoding.
    """
    if _text(_misc_field(ident, "bron")):
        return
    rights_el = _child(ident, "rights")
    rights = _text(rights_el)
    if not rights or not _LICENSE_IN_TEXT.search(rights):
        return
    title = ""
    for el in root.iter():
        if local(el.tag) == "work-title" and (el.text or "").strip():
            title = (el.text or "").strip()
            break
    _set_misc_field(ident, "bron", title or "partituur")


def _key_alters(fifths: int) -> dict[str, int]:
    alters = {step: 0 for step in _STEPS}
    if fifths > 0:
        for step in _SHARP_ORDER[:fifths]:
            alters[step] = 1
    elif fifths < 0:
        for step in _FLAT_ORDER[:-fifths]:
            alters[step] = -1
    return alters


def _note_sounding_alter(note: ET.Element) -> int | None:
    pitch = _child(note, "pitch")
    if pitch is None:
        return None
    alter_el = _child(pitch, "alter")
    if alter_el is None or not _text(alter_el):
        return 0
    try:
        return int(float(_text(alter_el)))
    except ValueError:
        return None


def _insert_accidental(note: ET.Element, name: str) -> None:
    acc = ET.Element("accidental")
    acc.text = name
    type_el = _child(note, "type")
    if type_el is not None:
        note.insert(list(note).index(type_el) + 1, acc)
    else:
        note.append(acc)


def apply_playback_accidentals(root: ET.Element) -> int:
    """Zet ``<accidental>`` waar klinkende toon afwijkt van voortekening/maat."""
    n = 0
    for part in _music_parts(root):
        fifths = 0
        for measure in _children(part, "measure"):
            attrs = _child(measure, "attributes")
            if attrs is not None:
                key = _child(attrs, "key")
                if key is not None:
                    raw = _text(_child(key, "fifths"))
                    if raw.lstrip("-").isdigit():
                        fifths = int(raw)
            implied_key = _key_alters(fifths)
            state: dict[tuple[str, str], int] = {}
            for note in _children(measure, "note"):
                sounding = _note_sounding_alter(note)
                pitch = _child(note, "pitch")
                if sounding is None or pitch is None:
                    continue
                step = _text(_child(pitch, "step"))
                octave = _text(_child(pitch, "octave"))
                if step not in implied_key:
                    continue
                current = state.get((step, octave), implied_key[step])
                if sounding == current:
                    continue
                name = _ALTER_TO_ACCIDENTAL.get(sounding)
                if name is None:
                    continue
                _insert_accidental(note, name)
                state[(step, octave)] = sounding
                n += 1
    return n


def finalize_coria_musicxml(xml: str, *, apply_timing: bool = True) -> str:
    """Coria-klare MusicXML: geen DOCTYPE, timing optioneel, sanitize, accidentals."""
    cleaned = strip_doctype(xml)
    # ET wil geen XML-declaratie-problemen; strip eventuele losse declaratie ok.
    root = ET.fromstring(cleaned)
    if apply_timing:
        parts = _music_parts(root)
        if parts:
            div = _divisions_of(root)
            insert_pause_measures(parts, whole_dur=4 * div)
            insert_caesura_quarter_rests(parts, quarter=div)
            _renumber_measures(root)
    sanitize_coria_importer(root)
    apply_playback_accidentals(root)
    return _serialize(root)
