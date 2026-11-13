from __future__ import annotations

import re


HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
COMMENT_ONLY_LINE_RE = re.compile(
    r"^[ \t]*<!--.*?-->[ \t]*(?:\r\n|\n|\r|$)",
    re.MULTILINE | re.DOTALL,
)
# Hele regel: optionele spaties/tabs, daarna ``#`` (zoals MVSA-regelcommentaar).
# Geen inline ``#``: in VSA blijft ``#-`` / ``#/`` in scopes halftoon-notatie.
HASH_COMMENT_LINE_RE = re.compile(r"^[ \t]*#")
# Regel begint (na whitespace) met een HTML-commentaar-opening.
HTML_COMMENT_LINE_START_RE = re.compile(r"^([ \t]*)<!--")


def is_vsa_comment_only_line(line_content: str, line_ending: str = "") -> bool:
    """True als de regel alleen broncommentaar is (HTML-regel of ``#``-regel)."""
    if COMMENT_ONLY_LINE_RE.match(line_content + line_ending):
        return True
    return HASH_COMMENT_LINE_RE.match(line_content) is not None


def _consume_eol(text: str, index: int) -> int:
    """Sla optionele spaties/tabs en hoogstens één regeleinde over."""
    length = len(text)
    while index < length and text[index] in " \t":
        index += 1
    if text[index : index + 2] == "\r\n":
        return index + 2
    if index < length and text[index] in "\r\n":
        return index + 1
    return index


def strip_vsa_html_comments(text: str) -> str:
    """Return VSA/MVSA-brontekst zonder commentaar (HTML en ``#``-regels).

    De bron zelf blijft ongewijzigd bij callers. Alleen voor parsing,
    validatie en afgeleide artefacten.

    Commentaar telt niet als tekst, whitespace, newline of layout.
    Commentaar-regels verdwijnen inclusief regeleinde (geen lege SVG-regel).
    Inline HTML-commentaar verdwijnt in-place. Multi-regel ``<!-- … -->``
    verdwijnt volledig (geen restanten, geen lege regels).
    """
    stripped, _ = strip_vsa_html_comments_with_offset_map(text)
    return stripped


def strip_vsa_html_comments_with_offset_map(text: str) -> tuple[str, list[int]]:
    """Return gestripte tekst en een per-karakter bron-offset-map.

    ``offset_map[i]`` is de index in de oorspronkelijke ``text`` van
    gestripte karakter ``i``. Zo blijven foutmeldingen bestand-absoluut
    (commentaarregels tellen mee in regel/kolom van de *resterende* bron).
    """
    offset_map: list[int] = []
    out: list[str] = []

    index = 0
    length = len(text)

    while index < length:
        line_start = index
        line_end = index
        while line_end < length and text[line_end] not in "\r\n":
            line_end += 1

        line_content = text[line_start:line_end]
        if line_end < length:
            if text[line_end : line_end + 2] == "\r\n":
                line_ending = "\r\n"
                next_index = line_end + 2
            else:
                line_ending = text[line_end]
                next_index = line_end + 1
        else:
            line_ending = ""
            next_index = line_end

        # Hele ``#``-commentaarregel (incl. regeleinde) weg.
        if HASH_COMMENT_LINE_RE.match(line_content):
            index = next_index
            continue

        # Hele regel die alleen een (enkele-regel) HTML-commentaar is.
        if COMMENT_ONLY_LINE_RE.match(line_content + line_ending):
            index = next_index
            continue

        # Regel die (na whitespace) met ``<!--`` begint: kan multi-regel zijn.
        # Hele blok weg inclusief trailing regeleinde na ``-->`` wanneer de
        # sluitregel verder leeg is — geen lege restregel.
        start_match = HTML_COMMENT_LINE_START_RE.match(line_content)
        if start_match is not None:
            abs_open = line_start + start_match.start() + len(start_match.group(1))
            close = text.find("-->", abs_open + 4)
            if close < 0:
                break
            after = close + 3
            # Alleen whitespace tot einde van de sluitregel?
            probe = after
            while probe < length and text[probe] in " \t":
                probe += 1
            if probe >= length or text[probe] in "\r\n":
                index = _consume_eol(text, after)
                continue
            # Sluitregel heeft nog inhoud na ``-->``: behoud die inhoud.
            index = after
            continue

        content_index = 0
        while content_index < len(line_content):
            if line_content.startswith("<!--", content_index):
                # Inline (of mid-regel) HTML-commentaar; ``-->`` mag later.
                abs_start = line_start + content_index
                close = text.find("-->", abs_start + 4)
                if close < 0:
                    return "".join(out), offset_map
                after = close + 3
                if after <= line_end:
                    content_index = after - line_start
                    continue
                # Multi-regel vanaf midden van de regel: bewaar prefix,
                # spring naar na ``-->`` (eventueel midden op sluitregel).
                index = after
                content_index = len(line_content)
                next_index = after
                break

            character = line_content[content_index]
            out.append(character)
            offset_map.append(line_start + content_index)
            content_index += 1
        else:
            # Normale regel volledig gekopieerd → regeleinde meenemen.
            for offset_in_ending, character in enumerate(line_ending):
                out.append(character)
                offset_map.append(line_end + offset_in_ending)
            index = next_index
            continue

        index = next_index

    return "".join(out), offset_map


def semantic_offset_to_source(offset_map: list[int], semantic_offset: int) -> int:
    """Map a character offset in stripped text to the original source offset."""
    if not offset_map:
        return max(0, semantic_offset)

    if semantic_offset < 0:
        return offset_map[0]

    if semantic_offset >= len(offset_map):
        return offset_map[-1] + 1

    return offset_map[semantic_offset]
