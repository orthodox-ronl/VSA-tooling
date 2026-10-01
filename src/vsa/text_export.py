"""Platte gezongen tekst uit .vsa / .mvsa (zoekindex, geen notatie)."""

from __future__ import annotations

from pathlib import Path

from .mvsa_parse import LPosition, parse_mvsa
from .mvsa_validate import is_lyrics_stem
from .syllabify import HARD_HYPHEN, dehyphenate_dutch_word, strip_soft_hyphens
from .vsa_stanzas import VsaNote, extract_stanza_notes


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
