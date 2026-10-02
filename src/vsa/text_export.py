"""Platte gezongen tekst uit .vsa / .mvsa / MusicXML / .mscz (zoekindex, geen notatie)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .musicxml_satb_layout import local
from .mvsa_parse import LPosition, parse_mvsa
from .mvsa_validate import is_lyrics_stem
from .syllabify import HARD_HYPHEN, dehyphenate_dutch_word, strip_soft_hyphens
from .vsa_stanzas import VsaNote, extract_stanza_notes

# MusicXML-bronnen voor lyrics-export (geen .mvsa-schrijven).
_MUSICXML_SUFFIXES = {".mxl", ".musicxml", ".xml"}


def join_lyric_syllables(
    syllables: list[str],
    links: list[bool],
    hard_links: list[bool] | None = None,
) -> str:
    """Zelfde regel als MVSA-MusicXML: streepje binnen woord, spatie tussen woorden.

    Zachte links worden ``-``; harde links (bron ``=``) blijven ``=`` tot
    ``dehyphenate_dutch_word`` ze omzet naar een zichtbaar streepje.
    """
    if not syllables:
        return ""
    out = syllables[0]
    for i, syl in enumerate(syllables[1:]):
        if i < len(links) and links[i]:
            hard = bool(hard_links and i < len(hard_links) and hard_links[i])
            sep = HARD_HYPHEN if hard else "-"
        else:
            sep = " "
        out += sep + syl
    return out


def _piece_for_plain(text: str) -> str:
    """Binnen een woord: zachte ``-`` weg, hard ``=`` nog laten staan."""
    if not text:
        return ""
    return " ".join(
        strip_soft_hyphens(part) for part in text.split(" ") if part != ""
    )


def _events_to_plain(events: list[tuple[str, str]]) -> str:
    """Voeg (lyric, syllabic)-events samen tot leesbare woorden.

    ``syllabic`` volgt MusicXML: ``single`` / ``begin`` / ``middle`` / ``end``.
    """
    words: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        if not buf:
            return
        words.append(dehyphenate_dutch_word("".join(buf)))
        buf.clear()

    for lyric, syllabic in events:
        if not lyric:
            continue
        syl = syllabic or "single"
        if syl == "single":
            flush()
            words.append(dehyphenate_dutch_word(lyric))
        elif syl == "begin":
            flush()
            buf.append(lyric)
        elif syl in ("middle", "end"):
            buf.append(lyric)
            if syl == "end":
                flush()
        else:
            flush()
            words.append(dehyphenate_dutch_word(lyric))
    flush()
    return " ".join(words)


def _stanza_to_plain(notes: list[VsaNote]) -> str:
    """Voeg lettergrepen van één VSA-frase samen tot leesbare woorden."""
    return _events_to_plain(
        [(note.lyric, note.syllabic or "single") for note in notes if note.lyric]
    )


def plain_text_from_vsa(source: str) -> str:
    """Gezongen tekst uit een .vsa-bron (frontmatter + body)."""
    stanzas = extract_stanza_notes(source)
    lines = [_stanza_to_plain(notes) for notes in stanzas]
    return "\n".join(line for line in lines if line).strip()


def _append_lpos(parts: list[str], lpos: LPosition, *, open_word: bool) -> bool:
    """Voeg één L-positie toe. Retourneert of het volgende stuk aan het woord plakt.

    Woordvoortzetting komt van ``continues_word`` op *deze* positie (leidend
    ``-``/``=``), niet van interne lettergreep-links binnen de positie.
    Onderdelen houden ``=`` tot de eindregel; pas daar wordt het zichtbare ``-``.
    """
    joined = join_lyric_syllables(lpos.syllables, lpos.links, lpos.hard_links)
    if not joined:
        return open_word
    piece = _piece_for_plain(joined)
    if not piece:
        return open_word
    if open_word or lpos.continues_word:
        glue = HARD_HYPHEN if lpos.continues_word_hard else ""
        if parts:
            parts[-1] = parts[-1] + glue + piece
        else:
            parts.append(piece)
    else:
        parts.append(piece)
    # Interne links horen bij deze positie; de *volgende* positie zet
    # ``continues_word`` als het woord verdergaat.
    return False


def plain_text_from_mvsa(source: str) -> str:
    """Gezongen tekst uit een .mvsa-bron (alle L-stems, documentvolgorde)."""
    doc = parse_mvsa(source)
    chunks: list[str] = []
    for section in doc.sections:
        for system in section.systems:
            parts: list[str] = []
            open_word = False
            for measure in system.measures:
                for marker in system.markers:
                    if not is_lyrics_stem(marker):
                        continue
                    positions = measure.lyrics.get(marker) or []
                    for lpos in positions:
                        open_word = _append_lpos(
                            parts, lpos, open_word=open_word
                        )
            if parts:
                chunks.append(
                    " ".join(dehyphenate_dutch_word(p) for p in parts)
                )
    return "\n".join(chunks).strip()


def _child_text(el: ET.Element, name: str) -> str:
    for child in el:
        if local(child.tag) == name:
            return (child.text or "").strip()
    return ""


def _lyric_plain_text(lyric: ET.Element) -> str:
    """Alle ``text``-kinderen van één lyric (elision = aaneen, geen spatie)."""
    parts: list[str] = []
    for child in lyric:
        tag = local(child.tag)
        if tag == "text":
            parts.append((child.text or "").strip())
        elif tag == "elision":
            # Elision koppelt lettergrepen zonder spatie; geen extra teken.
            continue
    return "".join(parts)


def _parse_voice(note: ET.Element) -> int | None:
    raw = _child_text(note, "voice")
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _is_chord_note(note: ET.Element) -> bool:
    return any(local(c.tag) == "chord" for c in note)


def _lyric_events_from_part(part: ET.Element) -> list[tuple[str, str]]:
    """Lyrics ``number=1`` uit één part, in maat-/notenvolgorde.

    Bij meerdere voices met lyrics: alleen de laagste voice (bij voorkeur 1),
    zodat SA/TB-partituur de lead-tekst niet verdubbelt.
    """
    collected: list[tuple[int | None, str, str]] = []
    voices_with_lyrics: set[int | None] = set()

    for meas in part:
        if local(meas.tag) != "measure":
            continue
        for note in meas:
            if local(note.tag) != "note":
                continue
            if _is_chord_note(note):
                continue
            voice = _parse_voice(note)
            for ly in note:
                if local(ly.tag) != "lyric":
                    continue
                number = (ly.get("number") or "1").strip() or "1"
                if number != "1":
                    continue
                text = _lyric_plain_text(ly)
                if not text:
                    continue
                syllabic = _child_text(ly, "syllabic") or "single"
                collected.append((voice, text, syllabic))
                voices_with_lyrics.add(voice)

    if not collected:
        return []

    if 1 in voices_with_lyrics:
        preferred: int | None = 1
    else:
        numbered = [v for v in voices_with_lyrics if v is not None]
        preferred = min(numbered) if numbered else None

    return [
        (text, syllabic)
        for voice, text, syllabic in collected
        if voice == preferred
    ]


def plain_text_from_musicxml(xml: str) -> str:
    """Gezongen tekst uit MusicXML (uncompressed string).

    Regel (SATB / partituur): neem de **eerste part** (documentvolgorde) die
    lyrics met ``number=\"1\"`` (of zonder number) heeft; binnen die part alleen
    die lyric-laag, geen chord-noten, en bij meerdere voices alleen de laagste
    voice met lyrics (bij voorkeur voice 1). Lettergrepen worden samengevoegd
    zoals bij VSA (``single``/``begin``/``middle``/``end`` + dehyphenate).

    Lege of lyric-loze scores geven een lege string (zelfde als ``vsa text``
    zonder gezongen tekst).
    """
    root = ET.fromstring(xml)
    for part in root:
        if local(part.tag) != "part":
            continue
        events = _lyric_events_from_part(part)
        if events:
            return _events_to_plain(events).strip()
    return ""


def plain_text_from_mscz(
    path: Path | str,
    *,
    musescore: Path | None = None,
) -> str:
    """Gezongen tekst uit ``.mscz`` via tijdelijke MuseScore-``.mxl`` (geen ``.mvsa``)."""
    from .musescore_cli import convert_with_musescore
    from .mvsa_import import read_musicxml_file

    path = Path(path)
    fd, tmp_name = tempfile.mkstemp(suffix=".mxl", prefix="vsa-text-")
    os.close(fd)
    tmp_mxl = Path(tmp_name)
    try:
        convert_with_musescore(path, tmp_mxl, musescore=musescore)
        return plain_text_from_musicxml(read_musicxml_file(tmp_mxl))
    finally:
        tmp_mxl.unlink(missing_ok=True)


def plain_text_from_path(
    path: Path | str,
    *,
    musescore: Path | None = None,
) -> str:
    """Lees .vsa / .mvsa / .mxl / .musicxml / .xml / .mscz en geef platte tekst terug."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".vsa":
        return plain_text_from_vsa(p.read_text(encoding="utf-8"))
    if suffix == ".mvsa":
        return plain_text_from_mvsa(p.read_text(encoding="utf-8"))
    if suffix in _MUSICXML_SUFFIXES:
        from .mvsa_import import read_musicxml_file

        return plain_text_from_musicxml(read_musicxml_file(p))
    if suffix == ".mscz":
        return plain_text_from_mscz(p, musescore=musescore)
    raise ValueError(
        f"verwacht .vsa, .mvsa, .mxl, .musicxml, .xml of .mscz; kreeg {p.suffix!r}"
    )
