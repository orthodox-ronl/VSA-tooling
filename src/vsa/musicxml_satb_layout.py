"""Convert MusicXML between Coria-playback (4 parts) and partituur (2 staves).

Used so ``mxl mscz`` / ``mscz mxl`` landen op de canonieke checklists.
Playback (vier parts) krijgt altijd piano-MIDI op elke stempartij (M8).
"""

from __future__ import annotations

import copy
import re
from xml.etree import ElementTree as ET

_NS_STRIP = re.compile(r"^\{[^}]+\}")

_PLAYBACK_MIDI_SOUND = "keyboard.piano.grand"
_PLAYBACK_MIDI_PROGRAM = "1"
_PLAYBACK_MIDI_VOLUME = "78.7402"
_PLAYBACK_MIDI_PAN = "0"
_MIDI_CHILD_TAGS = frozenset({"score-instrument", "midi-device", "midi-instrument"})
_PLAYBACK_PART_NAMES = {
    "P1": ("Soprano", "S"),
    "P2": ("Alto", "A"),
    "P3": ("Tenor", "T"),
    "P4": ("Bass", "B"),
}
_PLAYBACK_CHANNELS = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}


def local(tag: str) -> str:
    return _NS_STRIP.sub("", tag)


def ensure_partituur_musicxml(xml: str) -> str:
    """Return MusicXML with two empty-named SA/TB parts (twee voices per balk).

    Already-partituur scores (≤2 parts, empty names) are returned with names
    cleared. Four-part SATB is merged into SA + TB with voice 1 (stok omhoog)
    and voice 2 (stok omlaag).
    """
    root = ET.fromstring(xml)
    score_parts = _score_parts(root)
    if len(score_parts) <= 2:
        _clear_part_names(root)
        return _serialize(root)

    by_id = {pid: el for pid, el in _iter_parts(root)}
    if not {"P1", "P2", "P3", "P4"}.issubset(by_id):
        # Unknown multi-part layout: clear names and leave structure.
        _clear_part_names(root)
        return _serialize(root)

    title = _work_title(root)
    n_meas = max(len(list(by_id[p].findall("measure"))) for p in by_id)
    new_root = ET.Element("score-partwise", version=root.get("version") or "3.1")
    work = ET.SubElement(new_root, "work")
    ET.SubElement(work, "work-title").text = title
    part_list = ET.SubElement(new_root, "part-list")
    pg = ET.SubElement(part_list, "part-group", type="start", number="1")
    ET.SubElement(pg, "group-symbol").text = "bracket"
    for pid in ("P1", "P2"):
        sp = ET.SubElement(part_list, "score-part", id=pid)
        ET.SubElement(sp, "part-name")
        ET.SubElement(sp, "part-abbreviation")
    ET.SubElement(part_list, "part-group", type="stop", number="1")

    for pid, upper_id, lower_id, clef in (
        ("P1", "P1", "P2", ("G", "2")),
        ("P2", "P3", "P4", ("F", "4")),
    ):
        part_el = ET.SubElement(new_root, "part", id=pid)
        upper_meas = list(by_id[upper_id].findall("measure"))
        lower_meas = list(by_id[lower_id].findall("measure"))
        for mi in range(n_meas):
            um = upper_meas[mi] if mi < len(upper_meas) else None
            lm = lower_meas[mi] if mi < len(lower_meas) else None
            meas = ET.SubElement(part_el, "measure", number=str(mi + 1))
            if mi == 0:
                src_m = um if um is not None else lm
                attrs = ET.SubElement(meas, "attributes")
                ET.SubElement(attrs, "divisions").text = _divisions(src_m) or "4"
                key = ET.SubElement(attrs, "key")
                ET.SubElement(key, "fifths").text = _fifths(src_m) or "0"
                time = ET.SubElement(attrs, "time")
                ET.SubElement(time, "senza-misura")
                clef_el = ET.SubElement(attrs, "clef")
                ET.SubElement(clef_el, "sign").text = clef[0]
                ET.SubElement(clef_el, "line").text = clef[1]
            _merge_measure_notes(meas, um, lm, lyrics=(pid == "P1"))
            _copy_barlines(
                meas,
                um if um is not None else lm,
                is_last=(mi == n_meas - 1),
            )

    return _serialize(new_root)


def ensure_playback_musicxml(xml: str) -> str:
    """Return four-part Soprano/Alto/Tenor/Bass MusicXML for Coria.

    Two-staff partituur (chords or voice1+2) is exploded. Already-four-part
    SATB is returned with canonical part names.
    """
    root = ET.fromstring(xml)
    score_parts = _score_parts(root)
    by_id = {pid: el for pid, el in _iter_parts(root)}

    if len(score_parts) >= 4 and {"P1", "P2", "P3", "P4"}.issubset(by_id):
        _normalize_playback_part_list(root)
        return _serialize(root)

    if len(score_parts) == 2 and {"P1", "P2"}.issubset(by_id):
        return _explode_partituur_to_playback(root, by_id)

    # Fallback: rename whatever we have; keep structure.
    _normalize_playback_part_list(root)
    return _serialize(root)


def _explode_partituur_to_playback(
    root: ET.Element, by_id: dict[str, ET.Element]
) -> str:
    title = _work_title(root)
    n_meas = max(len(list(by_id[p].findall("measure"))) for p in ("P1", "P2"))
    new_root = ET.Element("score-partwise", version=root.get("version") or "3.1")
    work = ET.SubElement(new_root, "work")
    ET.SubElement(work, "work-title").text = title
    part_list = ET.SubElement(new_root, "part-list")
    for pid, name, abbr in (
        ("P1", "Soprano", "S"),
        ("P2", "Alto", "A"),
        ("P3", "Tenor", "T"),
        ("P4", "Bass", "B"),
    ):
        sp = ET.SubElement(part_list, "score-part", id=pid)
        ET.SubElement(sp, "part-name").text = name
        ET.SubElement(sp, "part-abbreviation").text = abbr
        _set_piano_midi(sp, pid)

    voice_streams: dict[str, list[list[ET.Element]]] = {
        "S": [],
        "A": [],
        "T": [],
        "B": [],
    }
    clefs = {"S": ("G", "2"), "A": ("G", "2"), "T": ("F", "4"), "B": ("F", "4")}
    p1_meas = list(by_id["P1"].findall("measure"))
    p2_meas = list(by_id["P2"].findall("measure"))
    for mi in range(n_meas):
        sa = _split_staff_measure(p1_meas[mi] if mi < len(p1_meas) else None)
        tb = _split_staff_measure(p2_meas[mi] if mi < len(p2_meas) else None)
        voice_streams["S"].append(sa[0])
        voice_streams["A"].append(sa[1])
        voice_streams["T"].append(tb[0])
        voice_streams["B"].append(tb[1])

    for voice, pid in (("S", "P1"), ("A", "P2"), ("T", "P3"), ("B", "P4")):
        part_el = ET.SubElement(new_root, "part", id=pid)
        for mi in range(n_meas):
            meas = ET.SubElement(part_el, "measure", number=str(mi + 1))
            src_staff = p1_meas[mi] if mi < len(p1_meas) else (
                p2_meas[mi] if mi < len(p2_meas) else None
            )
            if mi == 0:
                src = p1_meas[0] if p1_meas else None
                attrs = ET.SubElement(meas, "attributes")
                ET.SubElement(attrs, "divisions").text = _divisions(src) or "4"
                key = ET.SubElement(attrs, "key")
                ET.SubElement(key, "fifths").text = _fifths(src) or "0"
                time = ET.SubElement(attrs, "time")
                ET.SubElement(time, "senza-misura")
                clef_el = ET.SubElement(attrs, "clef")
                ET.SubElement(clef_el, "sign").text = clefs[voice][0]
                ET.SubElement(clef_el, "line").text = clefs[voice][1]
            # Cue/directions alleen op sopraan (zoals MVSA-export).
            if voice == "S" and src_staff is not None:
                for el in src_staff:
                    if local(el.tag) == "direction":
                        meas.append(copy.deepcopy(el))
            notes = voice_streams[voice][mi]
            if not notes:
                rest = ET.SubElement(meas, "note")
                ET.SubElement(rest, "rest")
                ET.SubElement(rest, "duration").text = "16"
                ET.SubElement(rest, "type").text = "whole"
            else:
                soprano = voice_streams["S"][mi]
                for idx, note in enumerate(notes):
                    n = copy.deepcopy(note)
                    for ch in list(n):
                        if local(ch.tag) == "chord":
                            n.remove(ch)
                    if voice != "S":
                        _ensure_lyrics_from(n, soprano, idx)
                    meas.append(n)
            _copy_barlines(meas, src_staff, is_last=(mi == n_meas - 1))

    return _serialize(new_root)


def _split_staff_measure(
    meas: ET.Element | None,
) -> tuple[list[ET.Element], list[ET.Element]]:
    """Split one staff measure into (upper, lower) — voice 1/2 or legacy chords."""
    if meas is None:
        return [], []
    notes = [n for n in meas if local(n.tag) == "note"]
    if any(_voice_num(n) is not None for n in notes):
        upper = [n for n in notes if (_voice_num(n) or 1) == 1]
        lower = [n for n in notes if (_voice_num(n) or 1) != 1]
        return upper, lower
    upper: list[ET.Element] = []
    lower: list[ET.Element] = []
    i = 0
    while i < len(notes):
        n = notes[i]
        if _is_rest(n):
            upper.append(n)
            lower.append(n)
            i += 1
            continue
        if i + 1 < len(notes) and _has_chord(notes[i + 1]):
            upper.append(n)
            lower.append(notes[i + 1])
            i += 2
        else:
            upper.append(n)
            lower.append(copy.deepcopy(n))
            i += 1
    return upper, lower


def _ensure_lyrics_from(
    note: ET.Element, soprano_notes: list[ET.Element], index: int
) -> None:
    if any(local(c.tag) == "lyric" for c in note):
        return
    if index < 0 or index >= len(soprano_notes):
        return
    for child in soprano_notes[index]:
        if local(child.tag) == "lyric":
            note.append(copy.deepcopy(child))


def _merge_measure_notes(
    dest: ET.Element,
    upper_m: ET.Element | None,
    lower_m: ET.Element | None,
    *,
    lyrics: bool,
) -> None:
    """Merge two playback parts into one staff: voice 1 up, backup, voice 2 down."""
    u_notes = (
        [n for n in upper_m if local(n.tag) == "note"] if upper_m is not None else []
    )
    l_notes = (
        [n for n in lower_m if local(n.tag) == "note"] if lower_m is not None else []
    )
    u_clean = [_strip_chord_voice(n) for n in u_notes]
    l_clean = [_strip_chord_voice(n) for n in l_notes]
    if not u_clean and not l_clean:
        rest = ET.SubElement(dest, "note")
        ET.SubElement(rest, "rest")
        ET.SubElement(rest, "duration").text = "16"
        ET.SubElement(rest, "type").text = "whole"
        ET.SubElement(rest, "voice").text = "1"
        return

    total_u = 0
    for n in u_clean:
        if not lyrics:
            for child in list(n):
                if local(child.tag) == "lyric":
                    n.remove(child)
        _set_voice_stem(n, voice=1, stem="up")
        dest.append(n)
        dur = _note_duration(n)
        if dur is not None:
            total_u += int(dur)

    if u_clean and l_clean:
        backup = ET.SubElement(dest, "backup")
        ET.SubElement(backup, "duration").text = str(total_u or 16)

    for n in l_clean:
        for child in list(n):
            if local(child.tag) == "lyric":
                n.remove(child)
        _set_voice_stem(n, voice=2, stem="down")
        dest.append(n)


def _set_voice_stem(note: ET.Element, *, voice: int, stem: str) -> None:
    had_none_stem = any(
        local(c.tag) == "stem" and (c.text or "") == "none" for c in note
    )
    had_notehead = any(local(c.tag) == "notehead" for c in note)
    for child in list(note):
        tag = local(child.tag)
        if tag in {"voice", "stem", "chord"}:
            note.remove(child)
    v = ET.Element("voice")
    v.text = str(voice)
    note.append(v)
    stem_el = ET.Element("stem")
    stem_el.text = "none" if (had_none_stem or had_notehead) else stem
    note.append(stem_el)


def _strip_chord_voice(note: ET.Element) -> ET.Element:
    n = copy.deepcopy(note)
    for child in list(n):
        if local(child.tag) in {"chord", "backup"}:
            n.remove(child)
    return n


def _voice_num(note: ET.Element) -> int | None:
    for c in note:
        if local(c.tag) == "voice" and c.text and c.text.isdigit():
            return int(c.text)
    return None


def _is_rest(note: ET.Element) -> bool:
    return any(local(c.tag) == "rest" for c in note)


def _has_chord(note: ET.Element) -> bool:
    return any(local(c.tag) == "chord" for c in note)


def _note_duration(note: ET.Element) -> str | None:
    for c in note:
        if local(c.tag) == "duration":
            return c.text
    return None


def _score_parts(root: ET.Element) -> list[str]:
    pl = next((c for c in root if local(c.tag) == "part-list"), None)
    if pl is None:
        return []
    return [
        el.get("id") or ""
        for el in pl
        if local(el.tag) == "score-part"
    ]


def _iter_parts(root: ET.Element):
    for el in root:
        if local(el.tag) == "part":
            yield el.get("id") or "", el


def _clear_part_names(root: ET.Element) -> None:
    pl = next((c for c in root if local(c.tag) == "part-list"), None)
    if pl is None:
        return
    for sp in pl:
        if local(sp.tag) != "score-part":
            continue
        for child in list(sp):
            if local(child.tag) in {"part-name", "part-abbreviation"}:
                child.text = ""


def _set_playback_part_names(root: ET.Element) -> None:
    """Backward-compatible alias: names + canonieke piano-MIDI."""
    _normalize_playback_part_list(root)


def _normalize_playback_part_list(root: ET.Element) -> None:
    """Zet Soprano…Bass-namen én piano-MIDI op P1–P4 (checklist M8)."""
    pl = next((c for c in root if local(c.tag) == "part-list"), None)
    if pl is None:
        return
    for sp in pl:
        if local(sp.tag) != "score-part":
            continue
        pid = sp.get("id") or ""
        if pid not in _PLAYBACK_PART_NAMES:
            continue
        name, abbr = _PLAYBACK_PART_NAMES[pid]
        pn = next((c for c in sp if local(c.tag) == "part-name"), None)
        pa = next((c for c in sp if local(c.tag) == "part-abbreviation"), None)
        if pn is None:
            pn = ET.SubElement(sp, "part-name")
        if pa is None:
            pa = ET.SubElement(sp, "part-abbreviation")
        pn.text = name
        pa.text = abbr
        _set_piano_midi(sp, pid)


def _set_piano_midi(score_part: ET.Element, part_id: str) -> None:
    """Replace instrumentatie op één score-part door canonieke piano."""
    for child in list(score_part):
        if local(child.tag) in _MIDI_CHILD_TAGS:
            score_part.remove(child)
    instrument_id = f"{part_id}-I1"
    channel = _PLAYBACK_CHANNELS.get(part_id, 1)
    score_instrument = ET.SubElement(
        score_part, "score-instrument", id=instrument_id
    )
    ET.SubElement(score_instrument, "instrument-name")
    ET.SubElement(score_instrument, "instrument-sound").text = _PLAYBACK_MIDI_SOUND
    ET.SubElement(score_part, "midi-device", id=instrument_id, port="1")
    midi_instrument = ET.SubElement(
        score_part, "midi-instrument", id=instrument_id
    )
    ET.SubElement(midi_instrument, "midi-channel").text = str(channel)
    ET.SubElement(midi_instrument, "midi-program").text = _PLAYBACK_MIDI_PROGRAM
    ET.SubElement(midi_instrument, "volume").text = _PLAYBACK_MIDI_VOLUME
    ET.SubElement(midi_instrument, "pan").text = _PLAYBACK_MIDI_PAN


def _work_title(root: ET.Element) -> str:
    for el in root.iter():
        if local(el.tag) == "work-title" and (el.text or "").strip():
            return el.text.strip()
    return "score"


def _bar_style_of(meas: ET.Element | None) -> str:
    if meas is None:
        return "regular"
    for bar in meas:
        if local(bar.tag) != "barline":
            continue
        if bar.get("location", "right") not in (None, "right"):
            continue
        for child in bar:
            if local(child.tag) == "bar-style" and (child.text or "").strip():
                return child.text.strip()
    return "regular"


def _copy_barlines(
    dest: ET.Element,
    src: ET.Element | None,
    *,
    is_last: bool = False,
) -> None:
    """Kopieer linker/rechter ``<barline>`` inclusief ``<repeat>`` (Coria-playback)."""
    barlines: list[ET.Element] = []
    if src is not None:
        barlines = [el for el in src if local(el.tag) == "barline"]
    if not barlines:
        style = "light-heavy" if is_last else "regular"
        bl = ET.SubElement(dest, "barline", location="right")
        ET.SubElement(bl, "bar-style").text = style
        return
    for bl in barlines:
        dest.append(copy.deepcopy(bl))
    if is_last:
        # Zorg dat de laatste maat een slotstreep houdt als bron alleen ``regular`` had.
        right = next(
            (
                b
                for b in dest
                if local(b.tag) == "barline"
                and b.get("location", "right") in (None, "right")
            ),
            None,
        )
        if right is not None and _bar_style_of(dest) == "regular":
            style_el = next(
                (c for c in right if local(c.tag) == "bar-style"),
                None,
            )
            if style_el is None:
                style_el = ET.SubElement(right, "bar-style")
            style_el.text = "light-heavy"


def _divisions(meas: ET.Element | None) -> str | None:
    if meas is None:
        return None
    for el in meas.iter():
        if local(el.tag) == "divisions" and el.text:
            return el.text
    return None


def _fifths(meas: ET.Element | None) -> str | None:
    if meas is None:
        return None
    for el in meas.iter():
        if local(el.tag) == "fifths" and el.text is not None:
            return el.text
    return None


def _serialize(root: ET.Element) -> str:
    # ElementTree does not keep DOCTYPE; fine for MuseScore / our importer.
    xml = ET.tostring(root, encoding="unicode")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml
