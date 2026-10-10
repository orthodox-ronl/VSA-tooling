"""Import MusicXML / MSCZ into .mvsa (draft-v0).

Primary path: parse SATB MusicXML (as emitted by ``mvsa musicxml``).
``.mscz`` is converted to ``.mxl`` via MuseScore CLI, then normalized to
four-part Coria/SATB (same explode as ``mscz mxl``) before parsing.

Lossy by design: layout and MuseScore-only details are dropped. Success =
pitch / duration / lyrics-equivalent roundtrip where the source was our MXL.

Same-pitch runs (≥3 simple lyrics, same duration) collapse to one recite
``( … )``; flanks around a multi-syllable underlay on the same pitch/duur
are absorbed into that recite.

``@do`` comes from CLI ``--do``, else MSCZ ``KeySig/concertKey``, else
MusicXML ``fifths``, else ``F4``.

Syllable/word boundaries follow MusicXML ``syllabic`` groups (``single``
never glues to another ``single``; ``begin``…``end`` is re-hyphenated with
Pyphen; long MuseScore chains use longest in-group matches). Spaces inside
an ``end`` lyric stay as word breaks; a second ``begin`` counts as ``middle``
(``Ja-cob``). False compounds (``dag-gaan``, ``steun-van``) stay spaced.
Recite underlay is repaired lightly (``we der ke`` → ``we-der-ke``) without
re-gluing whole words. Cross-position woordstreepjes when the right side is
``middle``/``end`` (or a recite), plus short proper-name begins. A word
split by a barline between two recites gets a canonical ``)-`` link.

Imported LSATB systems are soft-wrapped to about
:data:`DEFAULT_SYSTEM_SOFT_WIDTH` characters so the result stays readable
in an editor (one long measure may exceed the width alone).

By default the result is run through :func:`vsa.mvsa_kuiser.kuiser_mvsa_text`
(canonieke schrijfvorm / normaalvorm: lone standaard-``~`` op L weggelaten,
``~`` wél bij ``&``-melisma en na ``)``; maatstrepen sync, kolomuitlijning).
Pass ``align=False`` (CLI ``--no-align``) to skip.

With ``--pitch vsa``, each stem line gets a check-only absolute pitch
**eindanker** glued to the last bar of every system (e.g. ``||a4``), so
later edits can be caught by ``mvsa validate`` (``MVSA-BAR-ANKER``).
"""

from __future__ import annotations

import os
import re
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
from .syllabify import dehyphenate_dutch_word, hyphenate_dutch_word

# MusicXML part id → stem letter (matches mvsa_musicxml.PARTS)
_PART_VOICE = {"P1": "S", "P2": "A", "P3": "T", "P4": "B"}

# Soft wrap for imported LSATB systems (full line incl. ``L: `` prefix).
DEFAULT_SYSTEM_SOFT_WIDTH = 80

# Shown after ``# Imported: …`` on every import output (mvsa/mxl/mscz import).
IMPORT_SKETCH_WARNING_BANNER = """\
#  ##########################################################################  #
#  #                                                                        #  #
#  #   WAARSCHUWING:                                                        #  #
#  #                                                                        #  #
#  #   DIT BESTAND IS GEÏMPORTEERD UIT EEN PARTITUUR EN IS EEN SCHETS.      #  #
#  #   CONTROLEER VÓÓR OPNAME IN DE CATALOGUS TEN MINSTE:                   #  #
#  #   - woordstreepjes (te veel / te weinig / valse koppelingen)           #  #
#  #   - lettergreepgrenzen in recite ( ... )                               #  #
#  #   - uitlijning A/T/B t.o.v. L/S (verschoven of ontbrekende -)          #  #
#  #   - ritme & / duren / maatstrepen t.o.v. de bronpartituur              #  #
#  #   - ontbrekende metadata (bijv. @tempo) die niet meekwam bij import    #  #
#  #                                                                        #  #
#  ##########################################################################  #\
"""

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

# Major key: circle-of-fifths index → tonic spelling for ``@do …4``.
# Same index as MusicXML ``<fifths>`` and MuseScore ``<concertKey>``.
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

_MSCZ_CONCERT_KEY_RE = re.compile(
    r"<KeySig>\s*<concertKey>\s*(-?\d+)\s*</concertKey>",
    re.IGNORECASE,
)


def do_from_fifths(fifths: int) -> str:
    """Map key-signature fifths (0=C, -1=F, 1=G, …) to ``@do`` pitch, octave 4."""
    tonic = _FIFTHS_TO_TONIC.get(fifths)
    if tonic is None:
        raise MvsaImportError(
            f"onbekende toonsoort (fifths/concertKey={fifths}); "
            "gebruik --do (bijv. F4)"
        )
    return f"{tonic}4"


def read_mscz_key_fifths(path: Path) -> int | None:
    """Return MuseScore ``KeySig/concertKey`` from ``.mscz``, or None if absent."""
    path = Path(path)
    try:
        with zipfile.ZipFile(path) as archive:
            mscx_name = next(
                (
                    name
                    for name in archive.namelist()
                    if name.lower().endswith(".mscx")
                ),
                None,
            )
            if mscx_name is None:
                return None
            text = archive.read(mscx_name).decode("utf-8")
    except (OSError, zipfile.BadZipFile) as exc:
        raise MvsaImportError(f"kan .mscz niet lezen: {exc}") from exc
    match = _MSCZ_CONCERT_KEY_RE.search(text)
    if match is None:
        return None
    return int(match.group(1))


def _format_do_pitch(pitch: Pitch) -> str:
    """Canonical ``@do`` spelling (``F4``, ``Bb4``, ``C#5``)."""
    step = pitch.step.upper()
    alter = pitch.alter
    if alter == -2.0:
        body = f"{step}bb"
    elif alter == -1.0:
        body = "Bb" if step == "B" else f"{step}b"
    elif alter == 1.0:
        body = f"{step}#"
    elif alter == 2.0:
        body = f"{step}##"
    elif alter == 0.0:
        body = step
    else:
        body = step
    return f"{body}{pitch.octave}"


def _normalize_do_arg(do: str) -> str:
    """Validate CLI ``--do`` and return canonical ``@do`` spelling."""
    try:
        pitch = parse_pitch_string(do)
    except ValueError as exc:
        raise MvsaImportError(f"ongeldige --do {do!r}: {exc}") from exc
    return _format_do_pitch(pitch)


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
    do: str | None = None,
) -> str:
    """Read ``.mxl`` / ``.musicxml`` / ``.mscz`` and return mvsa text.

    ``@do`` resolution (first wins):

    1. Explicit ``do`` / CLI ``--do`` (e.g. ``F4``).
    2. For ``.mscz``: MuseScore ``KeySig/concertKey`` (sharps/flats count).
    3. MusicXML ``<key><fifths>`` from the converted/score XML.
    4. Fallback ``F4`` when no key signature is present.
    """
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
    do_override = _normalize_do_arg(do) if do is not None else None

    path = Path(path)
    suffix = path.suffix.lower()
    tmp_mxl: Path | None = None
    mscz_fifths: int | None = None
    try:
        if suffix == ".mscz":
            mscz_fifths = read_mscz_key_fifths(path)
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
        if do_override is not None:
            score.do = do_override
        elif mscz_fifths is not None:
            score.do = do_from_fifths(mscz_fifths)
        text = score_to_mvsa(
            score,
            pitch_form=pitch,
            section_id=section_id,
            system_soft_width=system_soft_width,
        )
        if align:
            # Canonieke normaalvorm: lone ~ weg, bars sync, kolommen.
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
    do: str | None = None,
) -> None:
    text = import_score_to_mvsa(
        path,
        pitch=pitch,
        octave_style=octave_style,
        align=align,
        section_id=section_id,
        musescore=musescore,
        system_soft_width=system_soft_width,
        do=do,
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
                        do_str = do_from_fifths(int(fifths_el.text))
                    except (ValueError, MvsaImportError):
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
        *IMPORT_SKETCH_WARNING_BANNER.splitlines(),
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

    s_positions_per_meas = [
        _group_positions(score.parts["S"][mi]) for mi in range(n_meas)
    ]
    _apply_cross_measure_word_links(s_positions_per_meas)

    for mi in range(n_meas):
        positions = s_positions_per_meas[mi]
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
    # How many source notes this position consumed (may exceed len(notes)
    # after same-pitch recite collapse or multi-syllable trim).
    source_count: int = 0
    # Total MusicXML duration (divisions at 4 per quarter) of the source span.
    # Kept after recite collapse / multi-syllable trim so A/T/B can mirror by time.
    duration_units: int = 0
    # Word continues after this position (barline / next position): emit ``)-``
    # after a recite, or rely on ``leading_word_hyphen`` on the next syllable.
    word_continues_after: bool = False
    # This syllable continues a word from the previous position/measure.
    leading_word_hyphen: bool = False
    # MusicXML syllabic of the primary lyric (single/begin/middle/end).
    syllabic: str = "single"


def _position_source_count(pos: _Position) -> int:
    return pos.source_count if pos.source_count > 0 else len(pos.notes)


def _note_duration_units(note: _Note) -> int:
    return note.duration.divisions_value


def _position_duration_units(pos: _Position) -> int:
    if pos.duration_units > 0:
        return pos.duration_units
    total = sum(_note_duration_units(n) for n in pos.notes)
    if total > 0:
        return total
    # Last resort: assume one quarter per source note.
    return _position_source_count(pos) * 4


def _fit_mirror_chunk(
    chunk: list[_Note],
    n_slots: int,
    hold_pitch: Pitch | None,
    hold_dur: Duration,
) -> tuple[list[_Note], Pitch | None, Duration]:
    """Truncate or pad ``chunk`` to ``n_slots``; update hold pitch/duration."""
    if chunk and chunk[-1].pitch is not None:
        hold_pitch = chunk[-1].pitch
        hold_dur = chunk[-1].duration
    if len(chunk) > n_slots:
        chunk = chunk[:n_slots]
        if chunk and chunk[-1].pitch is not None:
            hold_pitch = chunk[-1].pitch
            hold_dur = chunk[-1].duration
    elif len(chunk) < n_slots:
        fill = hold_pitch if hold_pitch is not None else Pitch("C", 4, 0.0)
        while len(chunk) < n_slots:
            chunk.append(_Note(pitch=fill, duration=hold_dur, lyrics=[]))
        if hold_pitch is None:
            hold_pitch = fill
    return chunk, hold_pitch, hold_dur


def _mirror_positions_by_duration(
    notes: list[_Note],
    mirror_of: list[_Position],
) -> list[_Position]:
    """Align A/T/B to S positions by duration, not note index or lyrics.

    A long note that covers several S slots is split/padded into those slots.
    A lyric-less spacer after a long note is not stolen into the previous
    melisma (MSCZ imports often leave such spacers when underlay is incomplete).
    Leftover duration from a partially consumed note feeds the next position.
    """
    out: list[_Position] = []
    i = 0
    rem_pitch: Pitch | None = None
    rem_units = 0
    rem_dur = Duration("quarter", 0)
    hold_pitch: Pitch | None = None
    hold_dur = Duration("quarter", 0)

    for pos in mirror_of:
        n_slots = len(pos.notes)
        n_src = _position_source_count(pos)
        need = _position_duration_units(pos)
        chunk: list[_Note] = []
        got = 0

        while got < need:
            if rem_units > 0:
                take = min(rem_units, need - got)
                chunk.append(
                    _Note(pitch=rem_pitch, duration=rem_dur, lyrics=[])
                )
                if rem_pitch is not None:
                    hold_pitch = rem_pitch
                    hold_dur = rem_dur
                rem_units -= take
                if rem_units == 0:
                    rem_pitch = None
                got += take
                continue
            if i >= len(notes):
                break
            note = notes[i]
            i += 1
            units = _note_duration_units(note)
            if note.pitch is not None:
                hold_pitch = note.pitch
                hold_dur = note.duration
            if got + units <= need:
                chunk.append(note)
                got += units
            else:
                take = need - got
                chunk.append(
                    _Note(pitch=note.pitch, duration=note.duration, lyrics=[])
                )
                rem_pitch = note.pitch
                rem_units = units - take
                rem_dur = note.duration
                got = need

        chunk, hold_pitch, hold_dur = _fit_mirror_chunk(
            chunk, n_slots, hold_pitch, hold_dur
        )
        out.append(
            _Position(
                notes=chunk,
                recite=pos.recite,
                source_count=n_src,
                duration_units=need,
            )
        )
    return out


def _group_positions(
    notes: list[_Note],
    *,
    mirror_of: list[_Position] | None = None,
) -> list[_Position]:
    """Group notes into L-length positions (lyric starts / melisma).

    When ``mirror_of`` is set (for A/T/B), emit one position per S position with
    the same slot count, consuming the voice by **duration** against each S
    position (long notes split/padded; leftover duration carries to the next
    position). Lyric text on A/T/B does not drive slot boundaries — S/L does.
    """
    if mirror_of is not None:
        return _mirror_positions_by_duration(notes, mirror_of)

    positions: list[_Position] = []
    i = 0
    while i < len(notes):
        # ≥3 same-pitch simple lyrics (same duration) → one recite.
        # Pairs like ``we``/``gen`` stay separate; see coalesce for underlay.
        run = _same_pitch_simple_lyric_run(notes, i)
        if len(run) >= 3:
            items = [
                (
                    n.lyrics[0].text if n.lyrics else "",
                    (n.lyrics[0].syllabic if n.lyrics else "single"),
                )
                for n in run
            ]
            combined = join_import_lyrics(items)
            collapsed = _Note(
                pitch=run[0].pitch,
                duration=run[0].duration,
                lyrics=[_Lyric(text=combined, syllabic="single")],
                is_breve=True,
            )
            j = i + len(run)
            # Lyric-less same-pitch followers (ties / spacers) stay in the
            # source span so A/T/B mirror stays aligned; not shown on S.
            while (
                j < len(notes)
                and not notes[j].lyrics
                and notes[j].pitch == run[0].pitch
            ):
                j += 1
            span = notes[i:j]
            positions.append(
                _Position(
                    notes=[collapsed],
                    recite=True,
                    source_count=j - i,
                    duration_units=sum(_note_duration_units(n) for n in span),
                    syllabic="single",
                )
            )
            i = j
            continue

        n0 = notes[i]
        group = [n0]
        j = i + 1
        # Melisma: following notes without lyrics belong to this position
        while j < len(notes) and not notes[j].lyrics:
            group.append(notes[j])
            j += 1
        lyric_text = n0.lyrics[0].text if n0.lyrics else ""
        syllabic = n0.lyrics[0].syllabic if n0.lyrics else "single"
        multi_syllable = _lyric_looks_multi_syllable(lyric_text)
        recite = bool(n0.is_breve) or multi_syllable
        source_len = len(group)
        duration_units = sum(_note_duration_units(n) for n in group)
        if multi_syllable and len(group) > 1:
            # Recite underlay on the visible note; lyric-less followers are often
            # failed expand/spacers — keep one slot (same pitch/duur as n0).
            group = [n0]
        if multi_syllable:
            repaired = join_import_lyrics([(lyric_text, "single")])
            group = [
                _Note(
                    pitch=n0.pitch,
                    duration=n0.duration,
                    lyrics=[_Lyric(text=repaired or lyric_text, syllabic="single")],
                    is_breve=n0.is_breve,
                )
            ]
        positions.append(
            _Position(
                notes=group,
                recite=recite,
                source_count=source_len,
                duration_units=duration_units,
                syllabic=syllabic,
            )
        )
        i = j
    positions = _coalesce_same_pitch_lyric_positions(positions)
    positions = _merge_fragment_lyric_positions(positions)
    _apply_word_links_in_sequence(positions)
    return positions


# Minimum simple-lyric same-pitch notes before collapsing to recite alone.
_MIN_SIMPLE_RECITE_RUN = 3


def _position_pitch(pos: _Position) -> Pitch | None:
    return pos.notes[0].pitch if pos.notes else None


def _position_duration(pos: _Position) -> Duration | None:
    return pos.notes[0].duration if pos.notes else None


def _position_lyric_fragment(pos: _Position) -> str:
    """Lyric text for coalesce (recite body without ``()``, or single syllable)."""
    if not pos.notes:
        return ""
    n0 = pos.notes[0]
    if not n0.lyrics:
        return ""
    raw = n0.lyrics[0].text or ""
    if pos.recite:
        return _clean_recite_lyric_text(raw)
    return _clean_import_lyric_text(raw) or raw.strip()


def _merge_positions_to_recite(run: list[_Position]) -> _Position:
    """Merge adjacent same-pitch lyric positions into one breve recite."""
    items: list[tuple[str, str]] = []
    for p in run:
        frag = _position_lyric_fragment(p)
        if frag:
            items.append((frag, p.syllabic or "single"))
    combined = join_import_lyrics(items)
    pitch = _position_pitch(run[0])
    dur = _position_duration(run[0]) or Duration("quarter", 0)
    collapsed = _Note(
        pitch=pitch,
        duration=dur,
        lyrics=[_Lyric(text=combined, syllabic="single")],
        is_breve=True,
    )
    return _Position(
        notes=[collapsed],
        recite=True,
        source_count=sum(_position_source_count(p) for p in run),
        duration_units=sum(_position_duration_units(p) for p in run),
        syllabic="single",
    )


def _coalesce_same_pitch_lyric_positions(
    positions: list[_Position],
) -> list[_Position]:
    """Join neighbors that belong to the same recite underlay.

    MuseScore often encodes ``Ver`` + ``vuld zij on-ze mond`` + ``met`` as
    three notes on one pitch: two simple lyrics around one multi-syllable
    underlay. Absorb those flanks into the recite when pitch **and** duration
    match (so a longer cadence note like ``Licht_`` stays separate).

    Pure pairs of simple syllables (e.g. ``we``/``gen``) are left alone.
    """
    if len(positions) < 2:
        return positions
    out: list[_Position] = []
    i = 0
    while i < len(positions):
        pitch = _position_pitch(positions[i])
        dur = _position_duration(positions[i])
        frag0 = _position_lyric_fragment(positions[i])
        if pitch is None or dur is None or not frag0:
            out.append(positions[i])
            i += 1
            continue
        run = [positions[i]]
        j = i + 1
        while j < len(positions):
            pj = positions[j]
            if (
                _position_pitch(pj) != pitch
                or _position_duration(pj) != dur
                or not _position_lyric_fragment(pj)
            ):
                break
            run.append(pj)
            j += 1
        has_recite = any(p.recite for p in run)
        if has_recite and len(run) >= 2:
            out.append(_merge_positions_to_recite(run))
        elif (not has_recite) and len(run) >= _MIN_SIMPLE_RECITE_RUN:
            out.append(_merge_positions_to_recite(run))
        else:
            out.extend(run)
        i = j
    return out


def _note_has_simple_lyric(note: _Note) -> bool:
    """True when the note carries a single-syllable MusicXML lyric (not underlay)."""
    if not note.lyrics or note.pitch is None:
        return False
    text = note.lyrics[0].text or ""
    if not text.strip() or text.strip() == "-":
        return False
    return not _lyric_looks_multi_syllable(text)


def _same_pitch_simple_lyric_run(notes: list[_Note], start: int) -> list[_Note]:
    """Consecutive same-pitch notes each with a simple lyric (MuseScore recite).

    Stops when pitch, lyric simplicity, or duration changes — so a longer
    cadence note on the same pitch (e.g. ``Licht_`` after recite quarters)
    stays its own L-position.
    """
    if start >= len(notes) or not _note_has_simple_lyric(notes[start]):
        return []
    first = notes[start]
    pitch = first.pitch
    dur = first.duration
    run = [first]
    j = start + 1
    while j < len(notes):
        nj = notes[j]
        if (
            not _note_has_simple_lyric(nj)
            or nj.pitch != pitch
            or nj.duration != dur
        ):
            break
        run.append(nj)
        j += 1
    return run


_SYLL_PUNCT_RE = re.compile(r"^(.*?)([.,;:!?]*)$", re.UNICODE)


def _split_syllable_punct(text: str) -> tuple[str, str]:
    """Split trailing punctuation from a syllable/word token."""
    t = (text or "").strip()
    match = _SYLL_PUNCT_RE.match(t)
    if not match:
        return t, ""
    return match.group(1), match.group(2)


def _syllable_units(token: str) -> list[tuple[str, str]]:
    """Return ``(match_core, display)`` units for one flattened token.

    Space-separated pieces are separate units (MuseScore often puts
    ``zin-gen voor mijn God`` in one ``end`` lyric).
    """
    raw = (token or "").strip()
    if not raw:
        return []
    if any(ch.isspace() for ch in raw):
        units: list[tuple[str, str]] = []
        for piece in raw.split():
            units.extend(_syllable_units(piece))
        return units
    core, punct = _split_syllable_punct(raw)
    if not core:
        return []
    if "-" in core:
        bits = [b for b in core.split("-") if b]
        units = []
        for i, bit in enumerate(bits):
            units.append((bit, bit + (punct if i == len(bits) - 1 else "")))
        return units
    return [(core, core + punct)]


# Function words that must not start or end a hyphenated compound
# (Pyphen happily hyphenates nonsense like ``het-wa`` / ``mond-met``).
# Keep ``aan``/``in``/``op`` out so real compounds like ``aan-schouwd`` work.
# Include ``van``/``is``/``tot``/``mijn`` — frequent false compounds in underlay
# (``steun-van``, ``is-van``, ``tot-stof``, ``mijn-God``).
_CLOSED_CLASS = frozenset(
    """
    wij ik jij gij je u uw hij zij het we jullie men
    ons hun hen mijn
    de den der des een en er of maar want dat die dit dus
    te met zonder van is tot zal voor
    zo nu dan wat wie hoe hier daar nog wel eens
    """.split()
)

# Function words that must not *end* a glued compound. Omits short articles /
# endings (``de``/``den``/``te``) that are also common final syllables
# (``aan-bid-den``). Includes prepositions kept out of ``_CLOSED_CLASS`` as
# starters (``aan``/``in``/``op``).
_CLOSED_CLASS_LAST = frozenset(
    """
    wij ik jij gij je u uw hij zij het we jullie men
    ons hun hen mijn
    een en er of maar want dat die dit dus
    met zonder van is tot zal voor
    zo nu dan wat wie hoe hier daar nog wel eens
    aan in op
    """.split()
)

# Short capitalised prefixes that may start a compound (``Be-waar``).
_SHORT_CAPITAL_COMPOUND_STARTERS = frozenset(
    "be ont al ge ver her er".split()
)

# Pyphen false positives: two real words that concatenate into a "valid" hyphenation.
_FALSE_COMPOUND_PAIRS = frozenset(
    {
        ("dag", "gaan"),
        ("heer", "richt"),
        ("steun", "van"),
        ("weg", "van"),
        ("van", "ge"),
        ("al", "zijn"),
        ("tot", "stof"),
        ("is", "van"),
        ("van", "zon"),
        ("van", "wees"),
        ("mijn", "god"),
    }
)


def _pyphen_matches_syllables(cores: list[str]) -> bool:
    if not cores:
        return False
    joined = "".join(cores)
    hyp_parts = hyphenate_dutch_word(joined).split("-")
    return len(hyp_parts) == len(cores) and all(
        hyp_parts[k].casefold() == cores[k].casefold()
        for k in range(len(cores))
    )


def _is_false_compound_pair(left: str, right: str) -> bool:
    return (left.casefold(), right.casefold()) in _FALSE_COMPOUND_PAIRS


def _can_hyphenate_syllables(cores: list[str]) -> bool:
    """Pyphen match, rejecting closed-class glue (``het-wa``, ``mond-met``).

    Exception: pronoun ``we`` may start a content word of ≥3 syllables
    (``we-der-ke``); interior closed-class lookalikes (``der``) are allowed
    only in that ``we-…`` pattern. Adjacent false-compound pairs
    (``dag``+``gaan``, ``Heer``+``richt``) are always rejected, also inside
    longer n-grams (``Heer-richt-de-ge``).
    """
    if not cores:
        return False
    if any(
        _is_false_compound_pair(cores[i], cores[i + 1])
        for i in range(len(cores) - 1)
    ):
        return False
    if not _pyphen_matches_syllables(cores):
        return False
    first = cores[0].casefold()
    last = cores[-1].casefold()
    we_word = first == "we" and len(cores) >= 3
    if first in _CLOSED_CLASS and not we_word:
        return False
    if last in _CLOSED_CLASS_LAST:
        return False
    # Articles as last of a bigram (``richt-de``, ``deel-te``).
    if len(cores) == 2 and last in ("de", "den", "te", "der", "des"):
        return False
    # ``de``/``te`` after an already-complete word (``wiens-hel-per``|``de``,
    # ``heer-lijk-heid``|``te``) — keep ``den`` for infinitives (``aan-bid-den``).
    if last in ("de", "te") and len(cores) >= 3 and _pyphen_matches_syllables(
        cores[:-1]
    ):
        return False
    for i, core in enumerate(cores):
        cf = core.casefold()
        if cf not in _CLOSED_CLASS:
            continue
        if i == 0 and we_word:
            continue
        if we_word and 0 < i < len(cores) - 1:
            continue
        # Final syllable already checked above.
        if i == len(cores) - 1:
            continue
        return False
    return True


def _format_word(chunk: list[tuple[str, str]]) -> str:
    if len(chunk) == 1:
        return chunk[0][1]
    pieces: list[str] = []
    for k, (_core, disp) in enumerate(chunk):
        if k < len(chunk) - 1:
            pieces.append(_split_syllable_punct(disp)[0])
        else:
            pieces.append(disp)
    return "-".join(pieces)


def _normalize_lyric_piece(raw: str) -> str:
    t = (raw or "").strip()
    while t.endswith(".") and len(t) > 1:
        t = t[:-1].rstrip()
    if not t or t == "-":
        return ""
    return t


def _hyphenate_underlay_word(word: str) -> str:
    """Hyphenate one underlay word; keep existing soft hyphens intact."""
    core, punct = _split_syllable_punct(word)
    if not core:
        return word
    if "-" in core:
        return core + punct
    return hyphenate_dutch_word(core) + punct


def _merge_hyphen_word_list(words: list[str]) -> list[str]:
    """Greedy Pyphen-glue of adjacent tokens (``he-mel-se``+``Geest``)."""
    out: list[str] = []
    for word in words:
        if out and _can_glue_pending_single(out[-1], word):
            out[-1] = _extend_pending_single(out[-1], word)
        else:
            out.append(word)
    return out


def _merge_underlay_word_list(words: list[str]) -> list[str]:
    """Glue underlay tokens only from a bare syllable (``aan``+``bid-den``).

    Already-hyphenated words stay apart so ``on-ze``+``mond`` does not become
    ``on-ze-mond`` (Pyphen false positive).
    """
    out: list[str] = []
    for word in words:
        if (
            out
            and "-" not in out[-1]
            and _can_glue_pending_single(out[-1], word)
        ):
            out[-1] = _extend_pending_single(out[-1], word)
        else:
            out.append(word)
    return out


def _bigrams_in_chain(units: list[tuple[str, str]]) -> list[str]:
    """Greedy longest matches (4/3/2) inside a long begin…end chain (N≥4)."""
    words: list[list[tuple[str, str]]] = []
    i = 0
    n = len(units)
    while i < n:
        matched = False
        for width in (4, 3, 2):
            if i + width > n:
                continue
            if any(units[i + k][1][:1].isupper() for k in range(1, width)):
                continue
            cores = [units[i + k][0] for k in range(width)]
            if _can_hyphenate_syllables(cores):
                words.append(units[i : i + width])
                i += width
                matched = True
                break
        if not matched:
            words.append([units[i]])
            i += 1
    # Bigram/trigram + light suffix mono → longer word (``he-mel`` + ``se``).
    suffix_mono = frozenset("se te de je ke ge ne re le pe ve me".split())
    finished: list[str] = []
    j = 0
    while j < len(words):
        mono = words[j + 1][0][0].casefold() if j + 1 < len(words) else ""
        if (
            j + 1 < len(words)
            and len(words[j]) in (2, 3)
            and len(words[j + 1]) == 1
            and mono in suffix_mono
            and not words[j + 1][0][1][:1].isupper()
            and _can_hyphenate_syllables(
                [u[0] for u in words[j]] + [words[j + 1][0][0]]
            )
        ):
            finished.append(_format_word(words[j] + words[j + 1]))
            j += 2
        else:
            finished.append(_format_word(words[j]))
            j += 1
    return finished


def _attach_trailing_syllable(words: list[str], trailing: str) -> list[str]:
    """Attach ``re``/``Geest`` after a chain when Pyphen confirms the join."""
    if not words or not trailing:
        return words
    t_core, t_punct = _split_syllable_punct(trailing)
    if not t_core:
        return words + [trailing]
    parts = words[-1].split("-")
    last_core = _split_syllable_punct(parts[-1])[0]
    if _can_hyphenate_syllables([last_core, t_core]):
        parts[-1] = last_core
        words[-1] = "-".join(parts + [t_core + t_punct])
        return words
    return words + [trailing]


def _trailing_prefers_next(trailing: str, nxt: str) -> bool:
    """True when ``trailing+next`` is a word (prefer over chain attach).

    Avoids ``wa-re-ge`` when ``ge``+``loof`` → ``ge-loof``.
    """
    t_core, _ = _split_syllable_punct(trailing)
    n_core, _ = _split_syllable_punct(nxt)
    if not t_core or not n_core or n_core[:1].isupper():
        return False
    return _can_hyphenate_syllables([t_core, n_core])


def _pending_last_core(pending: str) -> str:
    """Last syllable core of a pending token (``he-mel`` → ``mel``)."""
    core, _ = _split_syllable_punct(pending)
    if not core:
        return ""
    return _split_syllable_punct(core.split("-")[-1])[0]


def _can_glue_pending_single(pending: str, nxt: str) -> bool:
    """Allow cautious glue (``Be-waar``, ``he-mel``+``se``); block ``Gij-hebt``."""
    p_first, _ = _split_syllable_punct(pending)
    p_first = p_first.split("-")[0] if p_first else ""
    last = _pending_last_core(pending)
    n_core, _ = _split_syllable_punct(nxt.split("-")[0] if nxt else "")
    if not last or not n_core:
        return False
    if p_first[:1].isupper() and (
        p_first.casefold() not in _SHORT_CAPITAL_COMPOUND_STARTERS
    ):
        return False
    return _can_hyphenate_syllables([last, n_core])


def _extend_pending_single(pending: str, nxt: str) -> str:
    """Join pending+next and re-hyphenate (``aan``+``bid-den`` → ``aan-bid-den``)."""
    p_core, _ = _split_syllable_punct(pending)
    n_core, n_punct = _split_syllable_punct(nxt)
    p_plain = dehyphenate_dutch_word(p_core)
    n_plain = dehyphenate_dutch_word(n_core)
    glued = hyphenate_dutch_word(p_plain + n_plain) + n_punct
    if p_plain[:1].isupper() and glued[:1].islower():
        glued = glued[0].upper() + glued[1:]
    return glued


def _prepend_flank_to_chain(
    flank: str, chain: list[tuple[str, str]]
) -> list[tuple[str, str]] | None:
    """Absorb pending single into a begin…end chain (``aan``+``bid``…``den``)."""
    if not flank or not chain:
        return None
    f_core, _ = _split_syllable_punct(flank)
    first_core, _ = _split_syllable_punct(chain[0][0])
    if not f_core or not first_core:
        return None
    if not _can_hyphenate_syllables([f_core, first_core]):
        return None
    out: list[tuple[str, str]] = [(flank, "begin")]
    for text, syl in chain:
        if syl == "begin":
            out.append((text, "middle"))
        else:
            out.append((text, syl))
    return out


def _format_units_as_words(units: list[tuple[str, str]]) -> list[str]:
    """Hyphenate a contiguous syllable-unit run into one or more words."""
    if not units:
        return []
    cores = [u[0] for u in units]
    last_punct = _split_syllable_punct(units[-1][1])[1]
    if len(units) <= 3:
        joined = "".join(cores)
        hyp = hyphenate_dutch_word(joined)
        hyp_parts = hyp.split("-")
        absorb_letter = (
            len(cores) >= 2
            and len(cores[-1]) == 1
            and len(hyp_parts) == len(cores) - 1
            and not any(
                _is_false_compound_pair(hyp_parts[i], hyp_parts[i + 1])
                for i in range(len(hyp_parts) - 1)
            )
            and (
                hyp_parts[0].casefold() not in _CLOSED_CLASS
                or (
                    hyp_parts[0].casefold() == "we" and len(hyp_parts) >= 3
                )
            )
        )
        if _can_hyphenate_syllables(cores) or absorb_letter:
            if units[0][1][:1].isupper() and hyp[:1].islower():
                hyp = hyp[0].upper() + hyp[1:]
            return [hyp + last_punct]
    # N≤3 false compound / closed-class, or longer chain: greedy pieces.
    return _merge_hyphen_word_list(_bigrams_in_chain(units))


def _format_syllabic_chain(
    chain: list[tuple[str, str]],
    trailing_single: str | None = None,
) -> list[str]:
    """Format a begin…(middle)*…end group; optional trailing single (``wa-re``).

    When an ``end`` lyric embeds spaces (``zin-gen voor mijn God``), only the
    first space-separated word closes the syllabic word; the rest stay separate.
    """
    words: list[str] = []
    pending_units: list[tuple[str, str]] = []
    for text, _syl in chain:
        pieces = text.split()
        if not pieces:
            continue
        if len(pieces) == 1:
            pending_units.extend(_syllable_units(pieces[0]))
            continue
        # First piece continues the syllabic word; remainder are new words.
        pending_units.extend(_syllable_units(pieces[0]))
        words.extend(_format_units_as_words(pending_units))
        pending_units = []
        for piece in pieces[1:]:
            words.extend(
                _merge_underlay_word_list([_hyphenate_underlay_word(piece)])
            )
    if pending_units:
        words.extend(_format_units_as_words(pending_units))
    if trailing_single:
        words = _attach_trailing_syllable(words, trailing_single)
    # Cautious glue only (``he-mel``+``se``); do not re-join space-split words.
    return _merge_hyphen_word_list(words)


def _process_underlay_text(text: str, flank: str | None) -> tuple[list[str], str | None]:
    """Split underlay on spaces; optionally absorb a preceding single flank."""
    words = _merge_underlay_word_list(
        [_hyphenate_underlay_word(w) for w in text.split() if w]
    )
    if not words:
        return [], flank
    if flank:
        if _can_glue_pending_single(flank, words[0]):
            words[0] = _extend_pending_single(flank, words[0])
            return words, None
        return [flank] + words, None
    return words, None


def join_import_lyrics(items: list[tuple[str, str]]) -> str:
    """Join ``(text, syllabic)`` into canonical underlay.

    Rules:

    1. Two MusicXML ``single``s glue only when Pyphen confirms and closed-class
       / long-capital guards pass (``Be-waar``, not ``ons-heeft`` / ``Licht-aan``).
    2. A ``begin``…``end`` chain is re-hyphenated (N≤3) or repaired with
       in-group bigrams (N≥4); a following ``single`` may attach when Pyphen
       confirms (``wa-re``, ``he-mel-se-Geest``), unless that single+next forms
       a better word (``ge``+``loof``).
    3. A pending single may prepend to a begin…end chain (``aan-bid-den``).
    4. Underlay text with spaces is split into words, then hyphenated; a
       preceding single flank may absorb into the first word (``Ver``+``vuld``).
    """
    finished: list[str] = []
    pending_single: str | None = None
    i = 0
    n = len(items)

    def flush_pending() -> None:
        nonlocal pending_single
        if pending_single:
            finished.append(pending_single)
            pending_single = None

    def _peek_plain_single(at: int) -> str | None:
        if at >= n:
            return None
        t = _normalize_lyric_piece(items[at][0])
        s = (items[at][1] or "single").strip().lower()
        if (
            t
            and s == "single"
            and not any(ch.isspace() for ch in t)
            and "-" not in t
        ):
            return t
        return None

    while i < n:
        raw, syl = items[i]
        text = _normalize_lyric_piece(raw)
        syl = (syl or "single").strip().lower()
        if not text:
            i += 1
            continue

        if syl == "begin":
            chain: list[tuple[str, str]] = [(text, syl)]
            i += 1
            while i < n:
                t2 = _normalize_lyric_piece(items[i][0])
                s2 = (items[i][1] or "single").strip().lower()
                if not t2:
                    i += 1
                    continue
                if s2 == "middle":
                    chain.append((t2, s2))
                    i += 1
                elif s2 == "begin":
                    # Broken MuseScore: second begin inside a word (Ja/co/b).
                    chain.append((t2, "middle"))
                    i += 1
                elif s2 == "end":
                    chain.append((t2, s2))
                    i += 1
                    break
                else:
                    break
            if pending_single:
                merged = _prepend_flank_to_chain(pending_single, chain)
                if merged is not None:
                    chain = merged
                    pending_single = None
                else:
                    flush_pending()
            trailing: str | None = None
            t3 = _peek_plain_single(i)
            if t3 is not None:
                t4 = _peek_plain_single(i + 1)
                if t4 is not None and _trailing_prefers_next(t3, t4):
                    pass  # leave t3 for later single handling
                else:
                    plain = _format_syllabic_chain(chain, None)
                    attached = _attach_trailing_syllable(list(plain), t3)
                    if attached != plain:
                        trailing = t3
                        i += 1
            finished.extend(_format_syllabic_chain(chain, trailing))
            continue

        if syl in ("middle", "end"):
            # Orphan middle/end without a begin: emit as bare token.
            flush_pending()
            finished.append(text)
            i += 1
            continue

        # single (or unknown)
        if any(ch.isspace() for ch in text):
            words, pending_single = _process_underlay_text(text, pending_single)
            finished.extend(words)
            i += 1
            continue

        # Plain or pre-hyphenated single: extend pending when Pyphen agrees.
        if pending_single and _can_glue_pending_single(pending_single, text):
            pending_single = _extend_pending_single(pending_single, text)
            i += 1
            continue

        if "-" in text:
            flush_pending()
            finished.append(text)
            i += 1
            continue

        flush_pending()
        pending_single = text
        i += 1

    flush_pending()
    return " ".join(finished)


def join_import_syllables(
    parts: list[str],
    syllabics: list[str] | None = None,
) -> str:
    """Join lyric syllables; optional ``syllabics`` parallel to ``parts``."""
    if not parts:
        return ""
    if syllabics is None:
        syllabics = ["single"] * len(parts)
    if len(syllabics) != len(parts):
        raise ValueError("syllabics must match parts length")
    return join_import_lyrics(list(zip(parts, syllabics, strict=True)))


def _edge_syllable(pos: _Position, *, first: bool) -> str | None:
    """First or last alphabetic syllable inside a position's lyric text."""
    frag = _position_lyric_fragment(pos)
    if not frag:
        return None
    units: list[str] = []
    for token in frag.replace("(", " ").replace(")", " ").split():
        for _core, disp in _syllable_units(token):
            units.append(_split_syllable_punct(disp)[0])
    if not units:
        return None
    return units[0] if first else units[-1]


def _two_syllables_form_word(left: str, right: str) -> bool:
    """True when ``left+right`` is a real hyphenated word (not ``Licht-aan``)."""
    la, _ = _split_syllable_punct(left)
    ra, _ = _split_syllable_punct(right)
    la = la.replace("-", "")
    ra = ra.replace("-", "")
    if not la or not ra or not ra[:1].islower():
        return False
    if la[:1].isupper() and (
        la.casefold() not in _SHORT_CAPITAL_COMPOUND_STARTERS
    ):
        # Short proper-name syllables (``Ja-cob``); not long tokens (``Licht-aan``).
        return len(la) <= 3 and _pyphen_matches_syllables([la, ra])
    return _can_hyphenate_syllables([la, ra])


def _right_accepts_word_link(right: _Position) -> bool:
    """Woordstreep alleen bij MusicXML continuation or recite (stap 4)."""
    if right.recite:
        return True
    return (right.syllabic or "single") in ("middle", "end")


def _left_is_open_begin(left: _Position) -> bool:
    """True when left started a word that MuseScore never closed (second begin)."""
    return (left.syllabic or "single") == "begin" and not left.recite


def _lyric_core(text: str) -> str:
    core, _ = _split_syllable_punct(_clean_import_lyric_text(text) or text.strip())
    return core.replace("-", "")


def _combined_is_one_syllable(left: str, right: str) -> bool:
    """True when left+right collapse to one Pyphen syllable (``co``+``b`` → cob).

    Only single-letter leftovers are merged (``b``, ``s``) — longer pieces like
    ``ont`` must not glue onto ``Heer`` as ``Heeront``.
    """
    la = _lyric_core(left)
    ra = _lyric_core(right)
    if not la or not ra or len(ra) != 1:
        return False
    return len(hyphenate_dutch_word(la + ra).split("-")) == 1


def _merge_fragment_lyric_positions(positions: list[_Position]) -> list[_Position]:
    """Merge a one-syllable continuation into the previous lyric (``co``+``b``).

    Keeps the follower notes as melisma slots so S/A/T/B sync stays aligned.
    """
    if len(positions) < 2:
        return positions
    out: list[_Position] = []
    for pos in positions:
        if (
            out
            and not out[-1].recite
            and not pos.recite
            and out[-1].notes
            and pos.notes
            and out[-1].notes[0].lyrics
            and pos.notes[0].lyrics
            and (pos.syllabic or "single") in ("middle", "end", "begin")
            and _combined_is_one_syllable(
                out[-1].notes[0].lyrics[0].text,
                pos.notes[0].lyrics[0].text,
            )
        ):
            prev = out[-1]
            left = prev.notes[0].lyrics[0].text
            right = pos.notes[0].lyrics[0].text
            la = _lyric_core(left)
            ra, rp = _split_syllable_punct(
                _clean_import_lyric_text(right) or right.strip()
            )
            ra = ra.replace("-", "")
            merged = la + ra + rp
            if left[:1].isupper() and merged[:1].islower():
                merged = merged[0].upper() + merged[1:]
            # Rebuild previous position: lyric on first note, melisma notes after.
            new_notes = list(prev.notes) + [
                _Note(pitch=n.pitch, duration=n.duration, lyrics=[])
                for n in pos.notes
            ]
            new_notes[0] = _Note(
                pitch=new_notes[0].pitch,
                duration=new_notes[0].duration,
                lyrics=[_Lyric(text=merged, syllabic=pos.syllabic or "end")],
                is_breve=new_notes[0].is_breve,
            )
            out[-1] = _Position(
                notes=new_notes,
                recite=False,
                source_count=prev.source_count + pos.source_count,
                duration_units=_position_duration_units(prev)
                + _position_duration_units(pos),
                syllabic=pos.syllabic or "end",
            )
        else:
            out.append(pos)
    return out


def _allow_capital_compound_link(left: _Position, right: _Position) -> bool:
    """Exception: ``Ont``+``ferm`` as adjacent singles (allowlist capital)."""
    if right.recite:
        return False
    left_syl = _edge_syllable(left, first=False)
    right_syl = _edge_syllable(right, first=True)
    if left_syl is None or right_syl is None:
        return False
    if left_syl[:1].isupper() and (
        left_syl.casefold() in _SHORT_CAPITAL_COMPOUND_STARTERS
    ):
        return _two_syllables_form_word(left_syl, right_syl)
    return False


def _apply_word_links_in_sequence(positions: list[_Position]) -> None:
    """Mark woordstreepjes between adjacent positions in one measure."""
    for i in range(len(positions) - 1):
        left = positions[i]
        right = positions[i + 1]
        accept = _right_accepts_word_link(right) or _allow_capital_compound_link(
            left, right
        )
        # Second ``begin`` after an open begin (Ja / co) still continues the word.
        if not accept and _left_is_open_begin(left) and (
            (right.syllabic or "single") == "begin"
        ):
            accept = True
        if not accept:
            continue
        left_syl = _edge_syllable(left, first=False)
        right_syl = _edge_syllable(right, first=True)
        if left_syl is None or right_syl is None:
            continue
        if not _two_syllables_form_word(left_syl, right_syl):
            continue
        left.word_continues_after = True
        if not right.recite:
            right.leading_word_hyphen = True


def _apply_cross_measure_word_links(
    measures: list[list[_Position]],
) -> None:
    """Link a word split across a barline (e.g. two recites: ``(… wa)-|(re…)``)."""
    for mi in range(len(measures) - 1):
        left_meas = measures[mi]
        right_meas = measures[mi + 1]
        if not left_meas or not right_meas:
            continue
        last = next(
            (
                p
                for p in reversed(left_meas)
                if _position_lyric_fragment(p)
            ),
            None,
        )
        first = next(
            (p for p in right_meas if _position_lyric_fragment(p)),
            None,
        )
        if last is None or first is None:
            continue
        if not _right_accepts_word_link(first):
            continue
        left_syl = _edge_syllable(last, first=False)
        right_syl = _edge_syllable(first, first=True)
        if left_syl is None or right_syl is None:
            continue
        if not _two_syllables_form_word(left_syl, right_syl):
            continue
        last.word_continues_after = True
        if not first.recite:
            first.leading_word_hyphen = True


def _l_duration_suffix(
    elms: list[str], *, after_recite: bool = False
) -> str:
    """ELM-suffix for one L-positie.

    Lone standaard-``~`` is impliciet en wordt weggelaten — behalve na
    recite-``)`` (zonder ELM = breve) en in ``&``-melisma (``ziel~&~``).
    """
    if not elms:
        return ""
    if len(elms) == 1:
        if elms[0] == "~" and not after_recite:
            return ""
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
            # Underlay was already joined at collapse time; do not re-run
            # join_import_lyrics as one ``single`` (that re-glues ``dag gaan``
            # → ``dag-gaan``). Only light repair of false compounds / gaps.
            text = _repair_recite_underlay(raw) if raw.strip() else ""
            body = f"({text})" if text else "()"
            # Explicit non-breve duration after ) if present (keep ``~``:
            # bare ``)`` means breve, not quarter).
            if not n0.is_breve:
                body += _l_duration_suffix(
                    [_duration_to_elm(n0.duration)], after_recite=True
                )
            if pos.word_continues_after:
                body += "-"
            piece = body
        else:
            text = _clean_import_lyric_text(raw)
            elms = [_duration_to_elm(n.duration) for n in pos.notes]
            # Lyric-less / extender-only slot: bare ``~`` is not an L-position —
            # use empty recite ``()~`` so sync-telling matches the stem.
            if not text:
                piece = "()" + _l_duration_suffix(elms, after_recite=True)
            else:
                prev = positions[idx - 1] if idx > 0 else None
                # ``)-`` on a previous recite already links the word.
                linked_by_prev_recite = bool(
                    prev is not None
                    and prev.recite
                    and prev.word_continues_after
                )
                need_leading = (
                    pos.leading_word_hyphen or syllabic in ("end", "middle")
                ) and (not linked_by_prev_recite)
                if need_leading and not text.startswith("-"):
                    text = f"-{text}"
                piece = text + _l_duration_suffix(elms)

        # Glue ``(… Al)-`` + ``le~`` and ``Za_`` + ``-lig`` (no space).
        if parts and piece and (
            piece.startswith("-")
            or (parts[-1].endswith("-") and piece[0].isalpha())
        ):
            parts[-1] += piece
        else:
            parts.append(piece)
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


def _split_false_compound_token(token: str) -> list[str]:
    """Split known false compounds (``steun-van`` → ``steun``, ``van``)."""
    core, punct = _split_syllable_punct(token)
    if "-" not in core:
        return [token]
    bits = [b for b in core.split("-") if b]
    if len(bits) == 2 and _is_false_compound_pair(bits[0], bits[1]):
        return [bits[0], bits[1] + punct]
    return [token]


def _merge_underlay_syllable_gaps(words: list[str]) -> list[str]:
    """Join spaced syllable fragments when Pyphen confirms (``we der ke``).

    Only short unhyphenated tokens (≤3 letters) are considered — full words
    like ``gaan`` stay separate.
    """
    if len(words) < 2:
        return words
    out: list[str] = []
    i = 0
    while i < len(words):
        matched = False
        for width in (4, 3, 2):
            if i + width > len(words):
                continue
            chunk = words[i : i + width]
            cores: list[str] = []
            ok = True
            for wi, w in enumerate(chunk):
                c, p = _split_syllable_punct(w)
                if not c or "-" in c or len(c) > 3:
                    ok = False
                    break
                if p and wi != len(chunk) - 1:
                    ok = False
                    break
                cores.append(c)
            if not ok:
                continue
            if _can_hyphenate_syllables(cores):
                last_punct = _split_syllable_punct(chunk[-1])[1]
                hyp = hyphenate_dutch_word("".join(cores)) + last_punct
                if chunk[0][:1].isupper() and hyp[:1].islower():
                    hyp = hyp[0].upper() + hyp[1:]
                out.append(hyp)
                i += width
                matched = True
                break
        if not matched:
            out.append(words[i])
            i += 1
    return out


def _extend_hyphen_stem_with_fragment(words: list[str]) -> list[str]:
    """``psalm-zin`` + ``gen`` → ``psalm-zin-gen`` when Pyphen confirms."""
    if len(words) < 2:
        return words
    out: list[str] = []
    i = 0
    while i < len(words):
        if i + 1 < len(words) and "-" in words[i]:
            left_bits = [
                _split_syllable_punct(b)[0] for b in words[i].split("-") if b
            ]
            r_core, r_punct = _split_syllable_punct(words[i + 1])
            if (
                left_bits
                and r_core
                and "-" not in r_core
                and len(r_core) <= 3
                and r_core.casefold() not in ("de", "te")
                and _can_hyphenate_syllables(left_bits + [r_core])
            ):
                hyp = hyphenate_dutch_word("".join(left_bits + [r_core]))
                if words[i][:1].isupper() and hyp[:1].islower():
                    hyp = hyp[0].upper() + hyp[1:]
                out.append(hyp + r_punct)
                i += 2
                continue
        out.append(words[i])
        i += 1
    return out


def _repair_recite_underlay(text: str) -> str:
    """Light repair for already-joined recite underlay (no re-glue of words)."""
    t = _clean_recite_lyric_text(text)
    if not t:
        return ""
    words: list[str] = []
    for raw in t.split():
        words.extend(_split_false_compound_token(raw))
    words = _extend_hyphen_stem_with_fragment(words)
    words = _merge_underlay_syllable_gaps(words)
    return " ".join(words)


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
