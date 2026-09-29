"""Platte gezongen tekst uit .vsa / .mvsa (zoekindex, geen notatie)."""

from __future__ import annotations

from pathlib import Path

from .mvsa_parse import LPosition, parse_mvsa
from .mvsa_validate import is_lyrics_stem
from .syllabify import dehyphenate_dutch_word
from .vsa_stanzas import VsaNote, extract_stanza_notes


def join_lyric_syllables(syllables: list[str], links: list[bool]) -> str:
    """Zelfde regel als MVSA-MusicXML: '-' binnen woord, spatie tussen woorden."""
    if not syllables:
        return ""
    out = syllables[0]
    for i, syl in enumerate(syllables[1:]):
        sep = "-" if (i < len(links) and links[i]) else " "
        out += sep + syl
    return out


def _dehyphenate_words(text: str) -> str:
    """Verwijder lettergreepstreepjes per woord; spaties blijven woordgrenzen."""
    if not text:
        return ""
    return " ".join(
        dehyphenate_dutch_word(part) for part in text.split(" ") if part != ""
    )


def _stanza_to_plain(notes: list[VsaNote]) -> str:
    """Voeg lettergrepen van één VSA-frase samen tot leesbare woorden."""
    words: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        if not buf:
            return
        words.append(dehyphenate_dutch_word("".join(buf)))
        buf.clear()

    for note in notes:
        if not note.lyric:
            continue
        syl = note.syllabic or "single"
        if syl == "single":
            flush()
            words.append(dehyphenate_dutch_word(note.lyric))
        elif syl == "begin":
            flush()
            buf.append(note.lyric)
        elif syl in ("middle", "end"):
            buf.append(note.lyric)
            if syl == "end":
                flush()
        else:
            flush()
            words.append(dehyphenate_dutch_word(note.lyric))
    flush()
    return " ".join(words)


def plain_text_from_vsa(source: str) -> str:
    """Gezongen tekst uit een .vsa-bron (frontmatter + body)."""
    stanzas = extract_stanza_notes(source)
    lines = [_stanza_to_plain(notes) for notes in stanzas]
    return "\n".join(line for line in lines if line).strip()


def _append_lpos(parts: list[str], lpos: LPosition, *, open_word: bool) -> bool:
    """Voeg één L-positie toe. Retourneert of het volgende stuk aan het woord plakt."""
    joined = join_lyric_syllables(lpos.syllables, lpos.links)
    if not joined:
        return open_word
    plain = _dehyphenate_words(joined)
    if not plain:
        return open_word
    if open_word or lpos.continues_word:
        if parts:
            parts[-1] = parts[-1] + plain
        else:
            parts.append(plain)
    else:
        parts.append(plain)
    # Hyphen-link naar volgende positie? Laatste link True → woord open.
    if lpos.links and lpos.links[-1] and len(lpos.syllables) > 1:
        return True
    # Enkele lettergreep met trailing hyphen-semantiek via continues op next.
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
                chunks.append(" ".join(parts))
    return "\n".join(chunks).strip()


def plain_text_from_path(path: Path | str) -> str:
    """Lees .vsa of .mvsa en geef platte tekst terug."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    if suffix == ".vsa":
        return plain_text_from_vsa(text)
    if suffix == ".mvsa":
        return plain_text_from_mvsa(text)
    raise ValueError(f"verwacht .vsa of .mvsa, kreeg {p.suffix!r}")
