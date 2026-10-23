"""Compare a score (``.mscz`` / MusicXML) with a ``.mvsa`` (typically import).

Primary question: does this ``.mvsa`` still match what **current**
``mscz mvsa`` / ``mxl mvsa`` would produce from the score?

That avoids false alarms from:

- raw MusicXML syllable splits vs import word-joining;
- asymmetric score-parse vs ``.mvsa``→MusicXML export (duration noise);
- Coria playback ``.mxl`` with ``[PAUZE]`` bars (warn + strip).

Reports:

1. **Lyrics** — plain text from a fresh reference import vs the given ``.mvsa``
   (content words: punctuation stripped).
2. **Melody pitch** — per-voice pitch sequences (both sides via the same
   ``.mvsa``→MusicXML export). Drives the exit code together with lyrics.
3. **Melody duration** — pitch+duration tokens (informational; optional
   ``strict_duration`` for exit code).
4. **Capability gaps** — ``@tempo``, ``@tekst``, … present in the score but
   missing in the given ``.mvsa``.
"""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from xml.etree import ElementTree as ET

from .music import Duration, Pitch
from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError, convert_with_musescore
from .musicxml_coria_timing import PAUSE_LYRIC
from .musicxml_satb_layout import local
from .mvsa_import import (
    DEFAULT_IMPORT_PITCH,
    MvsaImportError,
    import_score_to_mvsa,
    parse_musicxml_satb,
    read_musicxml_file,
)
from .mvsa_musicxml import export_mvsa_to_musicxml
from .mvsa_normalize import canonicalize_pitch_form
from .text_export import plain_text_from_mvsa

_VOICES = ("S", "A", "T", "B")

_SCORE_SUFFIXES = {".mscz", ".mxl", ".musicxml", ".xml"}
_MVSA_SUFFIXES = {".mvsa"}

# Strip leading/trailing punctuation for "same sung words" compare.
_WORD_EDGE_PUNCT = re.compile(r"^[\W_]+|[\W_]+$", re.UNICODE)


class MsczCompareError(Exception):
    """User-facing compare failure (bad paths, MuseScore, invalid mvsa)."""


@dataclass(frozen=True)
class NoteToken:
    """One sounding event or rest for melody compare."""

    pitch: str  # e.g. ``F#4`` or ``r``
    duration: str  # e.g. ``quarter``, ``quarter.``

    def __str__(self) -> str:
        return f"{self.pitch}/{self.duration}"


@dataclass
class SequenceDiff:
    voice: str
    ref_len: int
    mvsa_len: int
    first_index: int | None
    ref_token: str | None
    mvsa_token: str | None
    equal: bool


@dataclass
class LyricDiff:
    equal: bool  # content words (punctuation stripped)
    raw_equal: bool  # plain text words including punctuation
    ref_plain: str
    mvsa_plain: str
    ref_words: list[str]
    mvsa_words: list[str]
    first_word_index: int | None = None
    ref_word: str | None = None
    mvsa_word: str | None = None


@dataclass
class CapabilityGap:
    """Score has something MVSA can express; the ``.mvsa`` file lacks it."""

    keyword: str
    detail: str


@dataclass
class CompareReport:
    score_path: Path
    mvsa_path: Path
    lyrics: LyricDiff
    pitches: list[SequenceDiff] = field(default_factory=list)
    durations: list[SequenceDiff] = field(default_factory=list)
    gaps: list[CapabilityGap] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    strict_duration: bool = False

    @property
    def musical_ok(self) -> bool:
        pitch_ok = all(m.equal for m in self.pitches)
        if not (self.lyrics.equal and pitch_ok):
            return False
        if self.strict_duration:
            return all(m.equal for m in self.durations)
        return True


def load_score_musicxml_for_import(
    path: Path,
    *,
    musescore: Path | None = None,
) -> str:
    """MusicXML string as ``mscz mvsa`` / ``mxl mvsa`` would see it.

    ``.mscz``: MuseScore → temp ``.mxl``, then SATB-explode (no Coria pause
    bars). ``.mxl`` / ``.musicxml`` / ``.xml``: read as-is (caller may strip
    ``[PAUZE]`` bars for Coria products).
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".mscz":
        fd, name = tempfile.mkstemp(suffix=".mxl", prefix="mscz-compare-")
        os.close(fd)
        tmp_mxl = Path(name)
        try:
            try:
                convert_with_musescore(path, tmp_mxl, musescore=musescore)
            except (MuseScoreNotFoundError, MuseScoreConvertError) as exc:
                raise MsczCompareError(str(exc)) from exc
            xml = read_musicxml_file(tmp_mxl)
            from .musicxml_playback_normalize import normalize_playback_musicxml

            return normalize_playback_musicxml(
                xml, apply_timing=False, expand_recite=True
            )
        finally:
            tmp_mxl.unlink(missing_ok=True)
    if suffix in {".mxl", ".musicxml", ".xml"}:
        try:
            return read_musicxml_file(path)
        except MvsaImportError as exc:
            raise MsczCompareError(str(exc)) from exc
    raise MsczCompareError(
        f"score verwacht .mscz / .mxl / .musicxml / .xml; kreeg {suffix!r}"
    )


def musicxml_has_coria_pauses(xml: str) -> bool:
    return PAUSE_LYRIC in xml


def strip_coria_pause_measures(xml: str) -> str:
    """Drop measures whose only lyric text is ``[PAUZE]`` (Coria timing bars)."""
    root = ET.fromstring(xml)
    for part in list(root):
        if local(part.tag) != "part":
            continue
        for meas in list(part):
            if local(meas.tag) != "measure":
                continue
            lyric_texts: list[str] = []
            for note in meas:
                if local(note.tag) != "note":
                    continue
                for ly in note:
                    if local(ly.tag) != "lyric":
                        continue
                    for child in ly:
                        if local(child.tag) == "text" and (child.text or "").strip():
                            lyric_texts.append((child.text or "").strip())
            if lyric_texts and all(t == PAUSE_LYRIC for t in lyric_texts):
                part.remove(meas)
    return ET.tostring(root, encoding="unicode")


def _duration_token(dur: Duration) -> str:
    dots = "." * max(0, dur.dots)
    return f"{dur.note_type}{dots}"


def _pitch_token(pitch: Pitch | None) -> str:
    if pitch is None:
        return "r"
    return str(pitch)


def _tokens_from_notes(notes: list) -> list[NoteToken]:
    return [
        NoteToken(pitch=_pitch_token(n.pitch), duration=_duration_token(n.duration))
        for n in notes
    ]


def _flatten_voice(score, voice: str) -> list[NoteToken]:
    measures = score.parts.get(voice) or []
    out: list[NoteToken] = []
    for meas in measures:
        out.extend(_tokens_from_notes(meas))
    return out


def _norm_plain(text: str) -> str:
    return " ".join(text.split())


def _word_list(text: str) -> list[str]:
    return _norm_plain(text).split() if _norm_plain(text) else []


def _content_word(word: str) -> str:
    return _WORD_EDGE_PUNCT.sub("", word)


def _content_words(text: str) -> list[str]:
    return [w for w in (_content_word(x) for x in _word_list(text)) if w]


def _first_mismatch(
    left: list, right: list
) -> tuple[int | None, object | None, object | None]:
    for i, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return i, a, b
    if len(left) != len(right):
        i = min(len(left), len(right))
        a = left[i] if i < len(left) else None
        b = right[i] if i < len(right) else None
        return i, a, b
    return None, None, None


def compare_lyrics_texts(ref_plain: str, mvsa_plain: str) -> LyricDiff:
    """Compare two plain lyric strings (typically both from ``.mvsa``)."""
    ref_plain_n = _norm_plain(ref_plain)
    mvsa_plain_n = _norm_plain(mvsa_plain)
    raw_ref = _word_list(ref_plain_n)
    raw_mvsa = _word_list(mvsa_plain_n)
    content_ref = _content_words(ref_plain_n)
    content_mvsa = _content_words(mvsa_plain_n)
    equal = content_ref == content_mvsa
    raw_equal = raw_ref == raw_mvsa
    first, rw, mw = _first_mismatch(content_ref, content_mvsa)
    return LyricDiff(
        equal=equal,
        raw_equal=raw_equal,
        ref_plain=ref_plain_n,
        mvsa_plain=mvsa_plain_n,
        ref_words=content_ref,
        mvsa_words=content_mvsa,
        first_word_index=first,
        ref_word=rw if isinstance(rw, str) or rw is None else str(rw),
        mvsa_word=mw if isinstance(mw, str) or mw is None else str(mw),
    )


def _sequence_diffs(
    ref_score,
    mvsa_score,
    *,
    pitch_only: bool,
) -> list[SequenceDiff]:
    diffs: list[SequenceDiff] = []
    for voice in _VOICES:
        a = _flatten_voice(ref_score, voice)
        b = _flatten_voice(mvsa_score, voice)
        if pitch_only:
            a_cmp: list = [t.pitch for t in a]
            b_cmp: list = [t.pitch for t in b]
            fmt = lambda p: str(p)  # noqa: E731
        else:
            a_cmp = a
            b_cmp = b
            fmt = str
        equal = a_cmp == b_cmp
        first, at, bt = _first_mismatch(a_cmp, b_cmp)
        diffs.append(
            SequenceDiff(
                voice=voice,
                ref_len=len(a_cmp),
                mvsa_len=len(b_cmp),
                first_index=first,
                ref_token=None if at is None else fmt(at),
                mvsa_token=None if bt is None else fmt(bt),
                equal=equal,
            )
        )
    return diffs


def compare_melodies_mvsa_pair(
    ref_mvsa: str, given_mvsa: str
) -> tuple[list[SequenceDiff], list[SequenceDiff]]:
    """Pitch and pitch+duration diffs; both sides via the same export path."""
    try:
        ref_xml = export_mvsa_to_musicxml(ref_mvsa)
        given_xml = export_mvsa_to_musicxml(given_mvsa)
        ref_score = parse_musicxml_satb(ref_xml)
        given_score = parse_musicxml_satb(given_xml)
    except Exception as exc:
        raise MsczCompareError(f".mvsa → MusicXML voor melodie: {exc}") from exc
    pitches = _sequence_diffs(ref_score, given_score, pitch_only=True)
    durations = _sequence_diffs(ref_score, given_score, pitch_only=False)
    return pitches, durations


def reference_import_mvsa(
    score_xml: str,
    *,
    pitch: str | None = None,
) -> str:
    """Fresh ``import_score_to_mvsa`` from MusicXML text (import defaults)."""
    pitch_form = canonicalize_pitch_form(pitch or DEFAULT_IMPORT_PITCH)
    fd, name = tempfile.mkstemp(suffix=".musicxml", prefix="mscz-compare-ref-")
    os.close(fd)
    tmp = Path(name)
    try:
        tmp.write_text(score_xml, encoding="utf-8", newline="\n")
        try:
            return import_score_to_mvsa(tmp, pitch=pitch_form, octave_style="@oct")
        except MvsaImportError as exc:
            raise MsczCompareError(str(exc)) from exc
    finally:
        tmp.unlink(missing_ok=True)


def _xml_has_tag(root: ET.Element, *names: str) -> bool:
    want = set(names)
    for el in root.iter():
        if local(el.tag) in want:
            return True
    return False


def _xml_sound_tempos(root: ET.Element) -> list[str]:
    out: list[str] = []
    for el in root.iter():
        if local(el.tag) != "sound":
            continue
        tempo = (el.get("tempo") or "").strip()
        if tempo:
            out.append(tempo)
    return out


def _xml_direction_words(root: ET.Element) -> list[str]:
    words: list[str] = []
    for el in root.iter():
        if local(el.tag) != "words":
            continue
        text = "".join(el.itertext()).strip()
        if text:
            words.append(text)
    return words


def _xml_creator(root: ET.Element, creator_type: str) -> str | None:
    for el in root.iter():
        if local(el.tag) != "creator":
            continue
        if (el.get("type") or "").strip().lower() != creator_type:
            continue
        text = "".join(el.itertext()).strip()
        if text:
            return text
    return None


def _xml_work_title(root: ET.Element) -> str | None:
    for el in root.iter():
        if local(el.tag) == "work-title":
            text = "".join(el.itertext()).strip()
            if text:
                return text
    return None


def _xml_source(root: ET.Element) -> str | None:
    for el in root.iter():
        if local(el.tag) == "source":
            text = "".join(el.itertext()).strip()
            if text:
                return text
    return None


def _mvsa_has_directive(text: str, keyword: str) -> bool:
    return bool(re.search(rf"(?m)^\s*@{re.escape(keyword)}\b", text))


def find_capability_gaps(score_xml: str, mvsa_text: str) -> list[CapabilityGap]:
    """Score features that ``.mvsa`` can express but this file does not have."""
    root = ET.fromstring(score_xml)
    gaps: list[CapabilityGap] = []

    tempos = _xml_sound_tempos(root)
    if tempos and not _mvsa_has_directive(mvsa_text, "tempo"):
        gaps.append(
            CapabilityGap(
                keyword="@tempo",
                detail=(
                    f"score heeft sound tempo={tempos[0]}"
                    + (f" (en {len(tempos) - 1} meer)" if len(tempos) > 1 else "")
                    + "; .mvsa heeft geen @tempo"
                ),
            )
        )

    words = _xml_direction_words(root)
    if words and not _mvsa_has_directive(mvsa_text, "tekst"):
        sample = words[0][:60]
        gaps.append(
            CapabilityGap(
                keyword="@tekst",
                detail=(
                    f"score heeft {len(words)} direction/words "
                    f"(eerste: {sample!r}); .mvsa heeft geen @tekst"
                ),
            )
        )

    if _xml_has_tag(root, "repeat", "ending") and not (
        _mvsa_has_directive(mvsa_text, "speelplan")
        or _mvsa_has_directive(mvsa_text, "blok")
    ):
        gaps.append(
            CapabilityGap(
                keyword="@speelplan / @blok",
                detail=(
                    "score heeft herhaling/volta (repeat/ending); "
                    ".mvsa heeft geen @speelplan of @blok"
                ),
            )
        )

    composer = _xml_creator(root, "composer")
    if composer and not _mvsa_has_directive(mvsa_text, "composer"):
        gaps.append(
            CapabilityGap(
                keyword="@composer",
                detail=f"score composer={composer!r}; .mvsa heeft geen @composer",
            )
        )

    lyricist = _xml_creator(root, "lyricist")
    if lyricist and not _mvsa_has_directive(mvsa_text, "tekstdichter"):
        gaps.append(
            CapabilityGap(
                keyword="@tekstdichter",
                detail=(
                    f"score lyricist={lyricist!r}; .mvsa heeft geen @tekstdichter"
                ),
            )
        )

    arranger = _xml_creator(root, "arranger")
    if arranger and not _mvsa_has_directive(mvsa_text, "arrangeur"):
        gaps.append(
            CapabilityGap(
                keyword="@arrangeur",
                detail=(
                    f"score arranger={arranger!r}; .mvsa heeft geen @arrangeur"
                ),
            )
        )

    source = _xml_source(root)
    if source and not _mvsa_has_directive(mvsa_text, "bron"):
        gaps.append(
            CapabilityGap(
                keyword="@bron",
                detail=f"score source={source!r}; .mvsa heeft geen @bron",
            )
        )

    title = _xml_work_title(root)
    if title and not _mvsa_has_directive(mvsa_text, "title"):
        gaps.append(
            CapabilityGap(
                keyword="@title",
                detail=(
                    f"score work-title={title!r}; .mvsa heeft geen @title "
                    "(import zet alleen een # Imported:-commentaar)"
                ),
            )
        )

    return gaps


_ALWAYS_LOSSY = (
    "Paginalayout, systeemafbrekingen in MuseScore, dynamiek/articulatie, "
    "grace notes en niet-SATB-stemmen komen niet mee bij import (by design)."
)

_METHOD_NOTE = (
    "Vergelijking t.o.v. een verse import van de score (zelfde keten als "
    "mscz mvsa / mxl mvsa). Lyrics: inhoud zonder rand-leestekens. "
    "Melodie-exitcode: toonhoogte; duur is informatief "
    "(tenzij --strict-duration)."
)


def compare_score_to_mvsa(
    score_path: Path,
    mvsa_path: Path,
    *,
    musescore: Path | None = None,
    pitch: str | None = None,
    strict_duration: bool = False,
) -> CompareReport:
    score_path = Path(score_path)
    mvsa_path = Path(mvsa_path)
    if score_path.suffix.lower() not in _SCORE_SUFFIXES:
        raise MsczCompareError(
            f"score: verwacht {_SCORE_SUFFIXES}; kreeg {score_path.suffix!r}"
        )
    if mvsa_path.suffix.lower() not in _MVSA_SUFFIXES:
        raise MsczCompareError(
            f".mvsa: verwacht .mvsa; kreeg {mvsa_path.suffix!r}"
        )
    if not score_path.is_file():
        raise MsczCompareError(f"bestand niet gevonden: {score_path}")
    if not mvsa_path.is_file():
        raise MsczCompareError(f"bestand niet gevonden: {mvsa_path}")

    score_xml = load_score_musicxml_for_import(score_path, musescore=musescore)
    notes = [_METHOD_NOTE, _ALWAYS_LOSSY]

    if musicxml_has_coria_pauses(score_xml):
        notes.insert(
            0,
            "Waarschuwing: MusicXML bevat Coria-pauzematen ([PAUZE]). "
            "Die horen niet bij import; ze worden voor deze vergelijking "
            "weggelaten. Liever .mscz als score gebruiken.",
        )
        score_xml = strip_coria_pause_measures(score_xml)

    given_mvsa = mvsa_path.read_text(encoding="utf-8")
    ref_mvsa = reference_import_mvsa(score_xml, pitch=pitch)

    lyrics = compare_lyrics_texts(
        plain_text_from_mvsa(ref_mvsa),
        plain_text_from_mvsa(given_mvsa),
    )
    gaps = find_capability_gaps(score_xml, given_mvsa)

    pitches: list[SequenceDiff] = []
    durations: list[SequenceDiff] = []
    try:
        pitches, durations = compare_melodies_mvsa_pair(ref_mvsa, given_mvsa)
    except MsczCompareError as exc:
        notes.append(f"Melodie niet vergelijkbaar: {exc}")
        # Treat as hard musical failure (invalid or unexportable .mvsa).
        pitches = [
            SequenceDiff(
                voice=v,
                ref_len=0,
                mvsa_len=0,
                first_index=0,
                ref_token=None,
                mvsa_token="(export mislukt)",
                equal=False,
            )
            for v in _VOICES
        ]

    if not lyrics.equal and lyrics.ref_words and lyrics.mvsa_words:
        ratio = SequenceMatcher(
            None, lyrics.ref_words, lyrics.mvsa_words
        ).ratio()
        notes.append(f"Lyrics inhoud-overeenkomst: {ratio:.0%}.")
    elif lyrics.equal and not lyrics.raw_equal:
        notes.append(
            "Lyrics-inhoud gelijk; alleen leestekens/spellingrand verschilt."
        )

    if pitches and all(p.equal for p in pitches) and durations and not all(
        d.equal for d in durations
    ):
        notes.append(
            "Toonhoogtes gelijk; duur wijkt af t.o.v. verse import "
            "(zie sectie Melodie — duur)."
        )

    return CompareReport(
        score_path=score_path,
        mvsa_path=mvsa_path,
        lyrics=lyrics,
        pitches=pitches,
        durations=durations,
        gaps=gaps,
        notes=notes,
        strict_duration=strict_duration,
    )


def format_report(report: CompareReport) -> str:
    lines: list[str] = [
        f"Score: {report.score_path}",
        f".mvsa: {report.mvsa_path}",
        "",
        "=== Lyrics (t.o.v. verse import) ===",
    ]
    ly = report.lyrics
    if ly.equal:
        lines.append(f"OK — {len(ly.ref_words)} woorden (inhoud) gelijk")
        if ly.ref_plain:
            preview = ly.ref_plain[:120]
            if len(ly.ref_plain) > 120:
                preview += "…"
            lines.append(f"  {preview}")
        if not ly.raw_equal:
            lines.append("  (ruwe tekst met leestekens verschilt licht)")
    else:
        lines.append(
            f"VERSCHIL — referentie {len(ly.ref_words)} woorden, "
            f".mvsa {len(ly.mvsa_words)} woorden"
        )
        if ly.first_word_index is not None:
            lines.append(
                f"  eerste verschil bij woord {ly.first_word_index}: "
                f"referentie={ly.ref_word!r} .mvsa={ly.mvsa_word!r}"
            )
        lines.append(
            f"  referentie: {ly.ref_plain[:200]}"
            + ("…" if len(ly.ref_plain) > 200 else "")
        )
        lines.append(
            f"  .mvsa: {ly.mvsa_plain[:200]}"
            + ("…" if len(ly.mvsa_plain) > 200 else "")
        )

    lines.append("")
    lines.append("=== Melodie — toonhoogte (t.o.v. verse import) ===")
    for md in report.pitches:
        if md.equal:
            lines.append(f"  {md.voice}: OK — {md.ref_len} events")
        else:
            lines.append(
                f"  {md.voice}: VERSCHIL — referentie {md.ref_len}, "
                f".mvsa {md.mvsa_len}"
            )
            if md.first_index is not None:
                lines.append(
                    f"    eerste verschil bij index {md.first_index}: "
                    f"referentie={md.ref_token!r} .mvsa={md.mvsa_token!r}"
                )

    lines.append("")
    lines.append("=== Melodie — duur (informatief) ===")
    for md in report.durations:
        if md.equal:
            lines.append(f"  {md.voice}: OK — {md.ref_len} events (pitch/duur)")
        else:
            lines.append(
                f"  {md.voice}: VERSCHIL — referentie {md.ref_len}, "
                f".mvsa {md.mvsa_len}"
            )
            if md.first_index is not None:
                lines.append(
                    f"    eerste verschil bij index {md.first_index}: "
                    f"referentie={md.ref_token!r} .mvsa={md.mvsa_token!r}"
                )

    lines.append("")
    lines.append(
        "=== In .mvsa noteerbaar, niet uit de score meegekomen ==="
    )
    if report.gaps:
        for gap in report.gaps:
            lines.append(f"  - {gap.keyword}: {gap.detail}")
    else:
        lines.append(
            "  (geen bekende metadata/cue/speelplan-gaten gevonden in de score)"
        )

    if report.notes:
        lines.append("")
        lines.append("=== Opmerkingen ===")
        for note in report.notes:
            lines.append(f"  - {note}")

    lines.append("")
    if report.musical_ok:
        if report.strict_duration:
            lines.append(
                "Samenvatting: lyrics, toonhoogte en duur komen overeen "
                "met verse import."
            )
        else:
            lines.append(
                "Samenvatting: lyrics en toonhoogte komen overeen met "
                "verse import."
            )
    else:
        lines.append(
            "Samenvatting: er zijn verschillen t.o.v. verse import "
            "(lyrics en/of toonhoogte"
            + (", en/of duur" if report.strict_duration else "")
            + ")."
        )
    return "\n".join(lines) + "\n"
