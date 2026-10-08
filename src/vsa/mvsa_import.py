"""Import MusicXML / MSCZ into .mvsa (draft-v0).

Primary path: parse SATB MusicXML (as emitted by ``mvsa musicxml``).
``.mscz`` is converted to ``.mxl`` via MuseScore CLI, then normalized to
four-part Coria/SATB (same explode as ``mscz mxl``) before parsing.

Lossy by design: layout and MuseScore-only details are dropped. Success =
pitch / duration / lyrics-equivalent roundtrip where the source was our MXL.

Imported LSATB systems are soft-wrapped to about
:data:`DEFAULT_SYSTEM_SOFT_WIDTH` characters so the result stays readable
in an editor (one long measure may exceed the width alone).

By default the result is run through :func:`vsa.mvsa_kuiser.kuiser_mvsa_text`
(canonieke schrijfvorm / normaalvorm: standaard-lengte als ``~``, maatstrepen
sync, kolomuitlijning). Pass ``align=False`` (CLI ``--no-align``) to skip.

With ``--pitch vsa``, each stem line gets a check-only absolute pitch
**eindanker** glued to the last bar of every system (e.g. ``||a4``), so
later edits can be caught by ``mvsa validate`` (``MVSA-BAR-ANKER``).
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
from .mvsa_kuiser import MvsaKuiserError, kuiser_mvsa_text
from .mvsa_normalize import (
    OCTAVE_STYLES,
    PITCH_FORMS,
    canonicalize_pitch_form,
    format_abc_scientific,
    format_doremi,
    format_ehm,
    pitch_to_degree_and_chrom,
)
from .mvsa_validate import MvsaValidationError
from .pitch_resolver import _SCALE_INTERVALS, parse_pitch_string

# MusicXML part id → stem letter (matches mvsa_musicxml.PARTS)
_PART_VOICE = {"P1": "S", "P2": "A", "P3": "T", "P4": "B"}

# Soft wrap for imported LSATB systems (full line incl. ``L: `` prefix).
DEFAULT_SYSTEM_SOFT_WIDTH = 80

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
    system_soft_width: int = DEFAULT_SYSTEM_SOFT_WIDTH,
) -> str:
    """Read ``.mxl`` / ``.musicxml`` / ``.mscz`` and return mvsa text."""
    pitch = canonicalize_pitch_form(pitch)
    if pitch not in PITCH_FORMS:
        raise MvsaImportError(
            f"onbekende --pitch {pitch!r}; kies uit "
            f"doremi, a-g (of abc), vsa"
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
    if system_soft_width < 1:
        raise MvsaImportError(
            f"system_soft_width moet ≥ 1 zijn; kreeg {system_soft_width}"
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
            # MuseScore partituur is often SA/TB; explode to P1–P4 like mscz mxl.
            from .musicxml_playback_normalize import normalize_playback_musicxml

            xml = normalize_playback_musicxml(xml, apply_timing=True)
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
            system_soft_width=system_soft_width,
        )
        if align:
            # Canonieke normaalvorm (syntax/semantics): ~ op L, bars sync, kolommen.
            try:
                text = kuiser_mvsa_text(
                    text, pitch="preserve", octave_style=octave_style, align=True
                ).text
            except (MvsaKuiserError, MvsaValidationError) as exc:
                raise MvsaImportError(
                    f"import-normaalvorm (kuiser) mislukt: {exc}"
                ) from exc
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
    system_soft_width: int = DEFAULT_SYSTEM_SOFT_WIDTH,
) -> None:
    text = import_score_to_mvsa(
        path,
        pitch=pitch,
        octave_style=octave_style,
        align=align,
        section_id=section_id,
        musescore=musescore,
        system_soft_width=system_soft_width,
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
                if _find(note_el, "chord") is not None:
                    # Chord tone shares onset with previous note; not a new slot.
                    continue
                if _find(note_el, "grace") is not None:
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
    system_soft_width: int = DEFAULT_SYSTEM_SOFT_WIDTH,
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
    # Carry last written pitch per stem so same-height holds become ``-``.
    last_pitch: dict[str, Pitch | None] = {v: None for v in "SATB"}

    for mi in range(n_meas):
        s_notes = score.parts["S"][mi]
        positions = _group_positions(s_notes)
        l_segs.append(_format_l_measure(positions))
        for letter in "SATB":
            v_notes = score.parts[letter][mi]
            v_positions = _group_positions(v_notes, mirror_of=positions)
            seg, last_pitch[letter] = _format_voice_measure(
                v_positions,
                pitch_form=pitch_form,
                do=do_p,
                intervals=intervals,
                writing_oct=writing_oct[letter],
                last_pitch=last_pitch[letter],
            )
            voice_segs[letter].append(seg)

    ranges = _pack_system_ranges(
        l_segs,
        voice_segs,
        soft_width=system_soft_width,
        pitch_form=pitch_form,
        score=score,
    )
    for si, (start, end) in enumerate(ranges):
        is_last = si == len(ranges) - 1
        chunk_l = l_segs[start:end]
        chunk_v = {letter: voice_segs[letter][start:end] for letter in "SATB"}
        n = end - start
        if n <= 0:
            continue
        if is_last:
            bars = ["|"] * (n - 1) + ["||"]
        else:
            bars = ["|"] * n
        lines.append(f"L: {_join_measure_segs(chunk_l, bars)}")
        for letter in "SATB":
            voice_bars = _bars_with_system_eindanker(
                bars,
                pitch_form=pitch_form,
                end_pitch=_last_sounding_in_range(score, letter, start, end),
            )
            lines.append(
                f"{letter}: {_join_measure_segs(chunk_v[letter], voice_bars)}"
            )
        if not is_last:
            lines.append("")
    lines.append("")
    return "\n".join(lines)


def _last_sounding_in_range(
    score: _Score, letter: str, start: int, end: int
) -> Pitch | None:
    """Last pitched note in measures ``[start, end)`` for one stem (or None)."""
    last: Pitch | None = None
    for mi in range(start, end):
        for note in score.parts.get(letter, [])[mi]:
            if note.pitch is not None:
                last = note.pitch
    return last


def _bars_with_system_eindanker(
    bars: list[str],
    *,
    pitch_form: str,
    end_pitch: Pitch | None,
) -> list[str]:
    """Glue absolute pitch onto the last bar when importing as ``vsa``.

    Lyrics lines keep bare bars; stem lines get e.g. ``||a4`` / ``|f#4`` so
    ``mvsa validate`` can catch pitch drift after edits (``MVSA-BAR-ANKER``).
    """
    if pitch_form != "vsa" or not bars or end_pitch is None:
        return bars
    out = list(bars)
    out[-1] = f"{out[-1]}{format_abc_scientific(end_pitch)}"
    return out


def _join_measure_segs(segs: list[str], bars: list[str]) -> str:
    parts: list[str] = []
    for i, seg in enumerate(segs):
        parts.append(seg)
        if i < len(bars):
            parts.append(f" {bars[i]}")
            if i + 1 < len(segs):
                parts.append(" ")
    return "".join(parts).rstrip()


def _system_content_width(
    l_segs: list[str],
    voice_segs: dict[str, list[str]],
    start: int,
    end: int,
    *,
    final_system: bool,
    pitch_form: str = "doremi",
    score: _Score | None = None,
) -> int:
    """Max length of ``L:/S:/A:/T:/B:`` lines for measures ``[start, end)``."""
    n = end - start
    if n <= 0:
        return 0
    if final_system:
        bars = ["|"] * (n - 1) + ["||"]
    else:
        bars = ["|"] * n
    widths = [len(f"L: {_join_measure_segs(l_segs[start:end], bars)}")]
    for letter in "SATB":
        ep = (
            _last_sounding_in_range(score, letter, start, end)
            if score is not None
            else None
        )
        voice_bars = _bars_with_system_eindanker(
            bars, pitch_form=pitch_form, end_pitch=ep
        )
        joined = _join_measure_segs(voice_segs[letter][start:end], voice_bars)
        widths.append(len(f"{letter}: {joined}"))
    return max(widths)


def _pack_system_ranges(
    l_segs: list[str],
    voice_segs: dict[str, list[str]],
    *,
    soft_width: int = DEFAULT_SYSTEM_SOFT_WIDTH,
    pitch_form: str = "doremi",
    score: _Score | None = None,
) -> list[tuple[int, int]]:
    """Pack measure indices into ``[start, end)`` ranges under soft_width.

    A single measure that alone exceeds ``soft_width`` still gets its own
    system. Intermediate systems are sized as non-final (trailing ``|``);
    the last packed range is measured as final (``||``) when it is the
    whole piece, but packing decisions use non-final width so adding a
    measure later does not under-estimate.
    """
    n = len(l_segs)
    if n == 0:
        return []
    ranges: list[tuple[int, int]] = []
    start = 0
    for i in range(n):
        trial_end = i + 1
        # While packing, treat the trial as a non-final system (ends with |).
        # The true last system may end with || (one char longer) — acceptable.
        width = _system_content_width(
            l_segs,
            voice_segs,
            start,
            trial_end,
            final_system=False,
            pitch_form=pitch_form,
            score=score,
        )
        if start < i and width > soft_width:
            ranges.append((start, i))
            start = i
    ranges.append((start, n))
    return ranges


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

    When ``mirror_of`` is set (for A/T/B), emit one position per S position with
    the same slot count. If the voice has lyrics, consume by lyric/melisma
    groups so a shorter collapsed melisma (M5a) does not steal the next
    syllable; pad with the last pitch held (re-export collapses pads again).
    Without lyrics, fall back to index-aligned chunks of S's sizes.
    """
    if mirror_of is not None:
        out: list[_Position] = []
        i = 0
        hold_pitch: Pitch | None = None
        hold_dur = Duration("quarter", 0)
        by_lyrics = any(n.lyrics for n in notes)
        for pos in mirror_of:
            n = len(pos.notes)
            if by_lyrics:
                chunk: list[_Note] = []
                if i < len(notes):
                    chunk.append(notes[i])
                    i += 1
                    while i < len(notes) and not notes[i].lyrics:
                        chunk.append(notes[i])
                        i += 1
            else:
                chunk = list(notes[i : i + n])
                i += n
            if chunk and chunk[-1].pitch is not None:
                hold_pitch = chunk[-1].pitch
                hold_dur = chunk[-1].duration
            if len(chunk) > n:
                chunk = chunk[:n]
                if chunk and chunk[-1].pitch is not None:
                    hold_pitch = chunk[-1].pitch
                    hold_dur = chunk[-1].duration
            elif len(chunk) < n:
                fill = hold_pitch if hold_pitch is not None else Pitch("C", 4, 0.0)
                while len(chunk) < n:
                    chunk.append(
                        _Note(
                            pitch=fill,
                            duration=hold_dur,
                            lyrics=[],
                        )
                    )
                if hold_pitch is None:
                    hold_pitch = fill
            out.append(_Position(notes=chunk, recite=pos.recite))
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
        lyric_text = n0.lyrics[0].text if n0.lyrics else ""
        multi_syllable = _lyric_looks_multi_syllable(lyric_text)
        recite = bool(n0.is_breve) or multi_syllable
        if multi_syllable and len(group) > 1:
            # Recite underlay on the visible note; lyric-less followers are often
            # failed expand/spacers — keep one slot (same pitch/duur as n0).
            group = [n0]
        positions.append(_Position(notes=group, recite=recite))
        i = j
    return positions


def _l_duration_suffix(elms: list[str]) -> str:
    """ELM-suffix for one L-positie (canonieke vorm: standaard-kwart als ``~``)."""
    if not elms:
        return ""
    if len(elms) == 1:
        return elms[0]
    return "&".join(elms)


def _format_l_measure(positions: list[_Position]) -> str:
    parts: list[str] = []
    for idx, pos in enumerate(positions):
        n0 = pos.notes[0]
        lyric = n0.lyrics[0] if n0.lyrics else None
        raw = lyric.text if lyric else ""
        syllabic = lyric.syllabic if lyric else "single"

        if pos.recite:
            text = _clean_recite_lyric_text(raw)
            body = f"({text})" if text else "()"
            # Explicit non-breve duration after ) if present
            if not n0.is_breve:
                body += _l_duration_suffix([_duration_to_elm(n0.duration)])
            parts.append(body)
            continue

        text = _clean_import_lyric_text(raw)
        elms = [_duration_to_elm(n.duration) for n in pos.notes]
        # Lyric-less / extender-only slot: bare ``~`` is not an L-position —
        # use empty recite ``()~`` so sync-telling matches the stem.
        if not text:
            parts.append("()" + _l_duration_suffix(elms))
            continue
        # First syllable / text
        prefix = f"-{text}" if syllabic in ("end", "middle") and text else text
        parts.append(prefix + _l_duration_suffix(elms))
    return " ".join(parts)


def _lyric_looks_multi_syllable(text: str) -> bool:
    """True when one MusicXML lyric encodes multiple syllables (recite underlay).

    Signals: whitespace between parts, or a soft hyphen between word characters
    (``die-tot``, ``ko-nink-rijk``). Lone extender ``-`` is not multi-syllable.
    """
    t = (text or "").strip()
    if not t or t == "-":
        return False
    if any(ch.isspace() for ch in t):
        return True
    # Soft hyphen between letters/digits (not a leading syllabic ``-li``).
    for i, ch in enumerate(t):
        if ch != "-" or i == 0 or i + 1 >= len(t):
            continue
        left, right = t[i - 1], t[i + 1]
        if (left.isalnum() or left in "',.") and (
            right.isalnum() or right in "',."
        ):
            return True
    return False


def _clean_recite_lyric_text(text: str) -> str:
    """Keep spaces/hyphens inside recite ``( … )``; trim extender-only / ELM ``.``."""
    t = (text or "").strip()
    if not t or t == "-":
        return ""
    # Sentence-final ``.`` before ``)`` is fine as punctuation; trailing-only
    # period that was meant as duration is rare inside multi-syllable underlay.
    # Collapse runs of whitespace for stable tokens.
    t = " ".join(t.split())
    return t


def _clean_import_lyric_text(text: str) -> str:
    """Normalize single-syllable MusicXML lyric text for non-recite L-tokens.

    - Lone ``-`` (melisma extender) → empty (emitted as ``()…``).
    - Trailing ``.`` is an ELM character in mvsa; strip sentence-final ``.``.
    - Soft hyphens / spaces should already have been routed to recite; if they
      remain, collapse so the L-parser does not invent extra positions.
      Trailing comma alone (``gen,``) is kept.
    """
    t = (text or "").strip()
    if not t or t == "-":
        return ""
    # Avoid ``ren._`` parsing as syllable ``ren`` + ELM ``.`` (dropping ``_``).
    while t.endswith(".") and len(t) > 1:
        t = t[:-1].rstrip()
    if not t or t == "-":
        return ""
    trailing_comma = t.endswith(",")
    t = t.replace("-", "")
    t = "".join(t.split())
    # Letters / apostrophe only — comma/colon mid-token would split L-positions.
    t = "".join(ch for ch in t if ch.isalpha() or ch == "'")
    if trailing_comma and t:
        t += ","
    if not t:
        return ""
    return t


def _format_voice_measure(
    positions: list[_Position],
    *,
    pitch_form: str,
    do: Pitch,
    intervals: list[int],
    writing_oct: int,
    last_pitch: Pitch | None = None,
) -> tuple[str, Pitch | None]:
    """Format one measure of stem tokens; same height as previous → ``-``.

    ``last_pitch`` carries across measures so holds stay readable. Returns
    ``(segment, new_last_pitch)``.
    """
    tokens: list[str] = []
    prev_degree: int | None = None
    for pos in positions:
        slots: list[str] = []
        for note in pos.notes:
            if note.pitch is None:
                slots.append("-")
                continue
            if last_pitch is not None and note.pitch == last_pitch:
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
    return " ".join(tokens), last_pitch


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
