"""Import MusicXML / MSCZ into .mvsa (draft-v0).

Primary path: parse SATB MusicXML (as emitted by ``mvsa musicxml``).
``.mscz`` is converted to ``.mxl`` via MuseScore CLI first.

Lossy by design: layout and MuseScore-only details are dropped. Success =
pitch / duration / lyrics-equivalent roundtrip where the source was our MXL.
"""

from __future__ import annotations

import os
import tempfile
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

from .music import Duration, Pitch
from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError, convert_with_musescore
from .mvsa_align import align_mvsa_text
from .mvsa_normalize import (
    OCTAVE_STYLES,
    PITCH_FORMS,
    format_abc_scientific,
    format_doremi,
    format_ehm,
    pitch_to_degree_and_chrom,
)
from .pitch_resolver import _SCALE_INTERVALS, parse_pitch_string

# MusicXML part id → stem letter (matches mvsa_musicxml.PARTS)
_PART_VOICE = {"P1": "S", "P2": "A", "P3": "T", "P4": "B"}

# Reverse of duration_model default (prefer ~ for quarter)
_DURATION_TO_ELM: dict[tuple[str, int], str] = {
    ("quarter", 0): "~",
    ("quarter", 1): "-.",
    ("half", 0): "_",
    ("half", 1): "_.",
    ("whole", 0): "__",
    ("eighth", 0): ".",
    ("16th", 0): "..",
}

# Major key: fifths → tonic step (+ optional alter as accidental string)
_FIFTHS_TO_TONIC: dict[int, str] = {
    0: "C",
    1: "G",
    2: "D",
    3: "A",
    4: "E",
    5: "B",
    6: "F#",
    -1: "F",
    -2: "Bb",
    -3: "Eb",
    -4: "Ab",
    -5: "Db",
    -6: "Gb",
}


class MvsaImportError(Exception):
    """Score → mvsa import failed."""


@dataclass
class _Lyric:
    text: str
    syllabic: str = "single"


@dataclass
class _Note:
    pitch: Pitch | None  # None = rest
    duration: Duration
    lyrics: list[_Lyric] = field(default_factory=list)
    is_breve: bool = False


@dataclass
class _Score:
    title: str
    do: str
    mode: str
    # voice letter -> list of measures; each measure = list of notes
    parts: dict[str, list[list[_Note]]]


def import_score_to_mvsa(
    path: Path,
    *,
    pitch: str = "doremi",
    octave_style: str = "@oct",
    align: bool = True,
    section_id: str = "import",
    musescore: Path | None = None,
) -> str:
    """Read ``.mxl`` / ``.musicxml`` / ``.mscz`` and return mvsa text."""
    if pitch not in PITCH_FORMS:
        raise MvsaImportError(
            f"onbekende --pitch {pitch!r}; kies uit {', '.join(PITCH_FORMS)}"
        )
    if octave_style not in OCTAVE_STYLES:
        raise MvsaImportError(
            f"onbekende --octave-style {octave_style!r}; "
            f"kies uit {', '.join(OCTAVE_STYLES)}"
        )
    if octave_style == "marker":
        raise MvsaImportError(
            "octave-style 'marker' is nog niet geïmplementeerd; gebruik @oct"
        )

    path = Path(path)
    suffix = path.suffix.lower()
    tmp_mxl: Path | None = None
    try:
        if suffix == ".mscz":
            fd, name = tempfile.mkstemp(suffix=".mxl", prefix="mvsa-import-")
            os.close(fd)
            tmp_mxl = Path(name)
            try:
                convert_with_musescore(path, tmp_mxl, musescore=musescore)
            except (MuseScoreNotFoundError, MuseScoreConvertError) as exc:
                raise MvsaImportError(str(exc)) from exc
            xml = read_musicxml_file(tmp_mxl)
        elif suffix in {".mxl", ".musicxml", ".xml"}:
            xml = read_musicxml_file(path)
        else:
            raise MvsaImportError(
                f"verwacht .mxl, .musicxml, .xml of .mscz; kreeg {suffix!r}"
            )

        score = parse_musicxml_satb(xml)
        text = score_to_mvsa(
            score,
            pitch_form=pitch,
            section_id=section_id,
        )
        if align:
            text = align_mvsa_text(text)
        return text
    finally:
        if tmp_mxl is not None:
            tmp_mxl.unlink(missing_ok=True)


def import_score_path(
    path: Path,
    out: Path,
    *,
    pitch: str = "doremi",
    octave_style: str = "@oct",
    align: bool = True,
    section_id: str = "import",
    musescore: Path | None = None,
) -> None:
    text = import_score_to_mvsa(
        path,
        pitch=pitch,
        octave_style=octave_style,
        align=align,
        section_id=section_id,
        musescore=musescore,
    )
    out = Path(out)
    if out.suffix.lower() != ".mvsa":
        out = out.with_suffix(".mvsa")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\n")


def read_musicxml_file(path: Path) -> str:
    """Return uncompressed MusicXML text from ``.mxl`` or plain XML."""
    path = Path(path)
    if path.suffix.lower() == ".mxl":
        with zipfile.ZipFile(path) as archive:
            # Prefer score.xml; else first .xml that is not container
            names = archive.namelist()
            candidate = None
            for name in names:
                lower = name.lower()
                if lower.endswith("score.xml") or lower.endswith("score.musicxml"):
                    candidate = name
                    break
            if candidate is None:
                for name in names:
                    if name.lower().endswith((".xml", ".musicxml")) and "container" not in name.lower():
                        candidate = name
                        break
            if candidate is None:
                raise MvsaImportError(f"geen MusicXML in {path}")
            return archive.read(candidate).decode("utf-8")
    return path.read_text(encoding="utf-8")


def parse_musicxml_satb(xml: str) -> _Score:
    root = ET.fromstring(xml)
    title = "import"
    work_title = _find(root, "work", "work-title")
    if work_title is not None and (work_title.text or "").strip():
        title = work_title.text.strip()

    parts: dict[str, list[list[_Note]]] = {}
    do_str = "F4"
    mode = "major"
    for part_el in _findall(root, "part"):
        part_id = part_el.get("id") or ""
        voice = _PART_VOICE.get(part_id)
        if voice is None:
            # Try part-abbreviation via part-list
            continue
        measures: list[list[_Note]] = []
        for meas in _findall(part_el, "measure"):
            attrs = _find(meas, "attributes")
            if attrs is not None:
                fifths_el = _find(attrs, "key", "fifths")
                if fifths_el is not None and fifths_el.text is not None:
                    try:
                        fifths = int(fifths_el.text)
                        tonic = _FIFTHS_TO_TONIC.get(fifths, "F")
                        do_str = f"{tonic}4"
                    except ValueError:
                        pass
            notes: list[_Note] = []
            for note_el in _findall(meas, "note"):
                if _find(note_el, "rest") is not None:
                    # Skip filler rests (empty measures from export)
                    continue
                pitch_el = _find(note_el, "pitch")
                if pitch_el is None:
                    continue
                step = (_find_text(pitch_el, "step") or "C").upper()
                oct_s = _find_text(pitch_el, "octave") or "4"
                alter_s = _find_text(pitch_el, "alter")
                alter = float(alter_s) if alter_s else 0.0
                pitch = Pitch(step=step, octave=int(oct_s), alter=alter)
                type_s = _find_text(note_el, "type") or "quarter"
                dots = len(_findall(note_el, "dot"))
                dur = Duration(note_type=type_s, dots=dots)
                lyrics: list[_Lyric] = []
                for ly in _findall(note_el, "lyric"):
                    text = _find_text(ly, "text") or ""
                    syllabic = _find_text(ly, "syllabic") or "single"
                    lyrics.append(_Lyric(text=text, syllabic=syllabic))
                notes.append(
                    _Note(
                        pitch=pitch,
                        duration=dur,
                        lyrics=lyrics,
                        is_breve=(type_s == "breve"),
                    )
                )
            measures.append(notes)
        parts[voice] = measures

    if "S" not in parts:
        raise MvsaImportError("geen sopraan-part (P1) in MusicXML")
    for letter in ("A", "T", "B"):
        if letter not in parts:
            # Pad missing voices with empty measures matching S
            parts[letter] = [[] for _ in parts["S"]]

    n = len(parts["S"])
    for letter, measures in parts.items():
        while len(measures) < n:
            measures.append([])
        if len(measures) > n:
            parts[letter] = measures[:n]

    return _Score(title=title, do=do_str, mode=mode, parts=parts)


def score_to_mvsa(
    score: _Score,
    *,
    pitch_form: str,
    section_id: str = "import",
) -> str:
    do_p = parse_pitch_string(score.do)
    intervals = _SCALE_INTERVALS[score.mode]
    writing_oct = _infer_writing_octaves(score, do_p, intervals)

    lines: list[str] = [
        f"# Imported: {score.title}",
        f"@do {score.do}",
        f"@mode {score.mode}",
    ]
    if any(v != 0 for v in writing_oct.values()):
        assign = " ".join(f"{k}={writing_oct[k]}" for k in ("S", "A", "T", "B"))
        lines.append(f"@oct {assign}")
    lines.append("")
    lines.append(f"@sectie {section_id}")

    n_meas = len(score.parts["S"])
    l_segs: list[str] = []
    voice_segs: dict[str, list[str]] = {v: [] for v in "SATB"}

    for mi in range(n_meas):
        s_notes = score.parts["S"][mi]
        positions = _group_positions(s_notes)
        l_segs.append(_format_l_measure(positions))
        for letter in "SATB":
            v_notes = score.parts[letter][mi]
            v_positions = _group_positions(v_notes, mirror_of=positions)
            voice_segs[letter].append(
                _format_voice_measure(
                    v_positions,
                    pitch_form=pitch_form,
                    do=do_p,
                    intervals=intervals,
                    writing_oct=writing_oct[letter],
                )
            )

    bars = ["|"] * (n_meas - 1) + ["||"] if n_meas else ["||"]

    def join_segs(segs: list[str]) -> str:
        parts: list[str] = []
        for i, seg in enumerate(segs):
            parts.append(seg)
            if i < len(bars):
                parts.append(f" {bars[i]}")
                if i + 1 < len(segs):
                    parts.append(" ")
        return "".join(parts).rstrip()

    lines.append(f"L: {join_segs(l_segs)}")
    for letter in "SATB":
        lines.append(f"{letter}: {join_segs(voice_segs[letter])}")
    lines.append("")
    return "\n".join(lines)


# --- position grouping / formatting -----------------------------------------


@dataclass
class _Position:
    notes: list[_Note]
    recite: bool = False


def _group_positions(
    notes: list[_Note],
    *,
    mirror_of: list[_Position] | None = None,
) -> list[_Position]:
    """Group notes into L-length positions (lyric starts / melisma).

    When ``mirror_of`` is set (for A/T/B), use the same group sizes as S.
    """
    if mirror_of is not None:
        out: list[_Position] = []
        i = 0
        for pos in mirror_of:
            n = len(pos.notes)
            chunk = notes[i : i + n]
            if len(chunk) < n:
                # Pad with last pitch held
                while len(chunk) < n and chunk:
                    chunk.append(
                        _Note(
                            pitch=chunk[-1].pitch,
                            duration=chunk[-1].duration,
                            lyrics=[],
                        )
                    )
                while len(chunk) < n:
                    chunk.append(
                        _Note(
                            pitch=Pitch("C", 4, 0.0),
                            duration=Duration("quarter", 0),
                            lyrics=[],
                        )
                    )
            out.append(_Position(notes=chunk, recite=pos.recite))
            i += n
        return out

    positions: list[_Position] = []
    i = 0
    while i < len(notes):
        n0 = notes[i]
        group = [n0]
        j = i + 1
        # Melisma: following notes without lyrics belong to this position
        while j < len(notes) and not notes[j].lyrics:
            group.append(notes[j])
            j += 1
        recite = n0.is_breve or (
            bool(n0.lyrics) and n0.is_breve
        )
        # Also treat breve as recite even without lyric
        if n0.is_breve:
            recite = True
        positions.append(_Position(notes=group, recite=recite))
        i = j
    return positions


def _format_l_measure(positions: list[_Position]) -> str:
    parts: list[str] = []
    for idx, pos in enumerate(positions):
        n0 = pos.notes[0]
        lyric = n0.lyrics[0] if n0.lyrics else None
        text = lyric.text if lyric else ""
        syllabic = lyric.syllabic if lyric else "single"

        if pos.recite:
            body = f"({text})" if text else "()"
            # Explicit non-breve duration after ) if present
            if not n0.is_breve:
                elm = _duration_to_elm(n0.duration)
                body += elm
            parts.append(body)
            continue

        elms = [_duration_to_elm(n.duration) for n in pos.notes]
        # First syllable / text
        if syllabic in ("end", "middle") and text:
            token = f"-{text}{elms[0]}"
        else:
            token = f"{text}{elms[0]}" if text else elms[0]
        if len(elms) > 1:
            token += "&" + "&".join(elms[1:])
        parts.append(token)
    return " ".join(parts)


def _format_voice_measure(
    positions: list[_Position],
    *,
    pitch_form: str,
    do: Pitch,
    intervals: list[int],
    writing_oct: int,
) -> str:
    tokens: list[str] = []
    prev_degree: int | None = None
    last_pitch: Pitch | None = None
    for pos in positions:
        slots: list[str] = []
        for note in pos.notes:
            if note.pitch is None:
                slots.append("-")
                continue
            if last_pitch is not None and note.pitch == last_pitch and pitch_form == "vsa":
                slots.append("-")
            elif pitch_form == "abc":
                slots.append(format_abc_scientific(note.pitch))
                deg, _ = pitch_to_degree_and_chrom(do, note.pitch, intervals)
                prev_degree = deg
            elif pitch_form == "doremi":
                slots.append(format_doremi(note.pitch, do, intervals, writing_oct))
                deg, _ = pitch_to_degree_and_chrom(do, note.pitch, intervals)
                prev_degree = deg
            else:  # vsa
                if prev_degree is None:
                    slots.append(format_doremi(note.pitch, do, intervals, writing_oct))
                else:
                    slots.append(format_ehm(prev_degree, note.pitch, do, intervals))
                deg, _ = pitch_to_degree_and_chrom(do, note.pitch, intervals)
                prev_degree = deg
            last_pitch = note.pitch
        tokens.append("&".join(slots))
    return " ".join(tokens)


def _duration_to_elm(dur: Duration) -> str:
    key = (dur.note_type, dur.dots)
    if key in _DURATION_TO_ELM:
        return _DURATION_TO_ELM[key]
    if dur.note_type == "breve":
        return ""  # recite default
    return "~"


def _infer_writing_octaves(
    score: _Score, do: Pitch, intervals: list[int]
) -> dict[str, int]:
    result: dict[str, int] = {}
    for letter in "SATB":
        degrees: list[int] = []
        for meas in score.parts.get(letter, []):
            for note in meas:
                if note.pitch is None:
                    continue
                try:
                    deg, _ = pitch_to_degree_and_chrom(do, note.pitch, intervals)
                    degrees.append(deg // 7)
                except Exception:
                    continue
        if degrees:
            result[letter] = Counter(degrees).most_common(1)[0][0]
        else:
            result[letter] = 0
    return result


# --- XML helpers ------------------------------------------------------------


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _findall(parent: ET.Element, *path: str) -> list[ET.Element]:
    """Find direct/nested children by local names (namespace-tolerant)."""
    if not path:
        return []
    current = [parent]
    for name in path:
        nxt: list[ET.Element] = []
        for el in current:
            for child in el:
                if _local(child.tag) == name:
                    nxt.append(child)
        current = nxt
    return current


def _find(parent: ET.Element, *path: str) -> ET.Element | None:
    found = _findall(parent, *path)
    return found[0] if found else None


def _find_text(parent: ET.Element, *path: str) -> str | None:
    el = _find(parent, *path)
    if el is None or el.text is None:
        return None
    return el.text.strip()
