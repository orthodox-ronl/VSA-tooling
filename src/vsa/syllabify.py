"""Lettergreepstreepjes in VSA-brontekst (alleen ongescoopte TextNode-inhoud)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from .ast import TextNode
from .parser import Parser
from .vsa_comments import (
    COMMENT_ONLY_LINE_RE,
    strip_vsa_html_comments_with_offset_map,
)
from .yaml_frontmatter import parse_vsa_frontmatter_with_body_offset

_BARLINE_TOKENS = frozenset({"/", "//", "*"})
_TOKEN_RE = re.compile(r"\S+|\s+", re.UNICODE)
_WORD_CORE_RE = re.compile(r"^(\W*)(.*?)(\W*)$", re.UNICODE)


@dataclass(frozen=True)
class SyllabifyResult:
    """Resultaat van ``syllabify_vsa_source``."""

    text: str
    changed: bool
    replacements: int


@lru_cache(maxsize=1)
def _dutch_dic():
    import pyphen

    return pyphen.Pyphen(lang="nl_NL")


def hyphenate_dutch_word(word: str) -> str:
    """Voeg orthografische lettergreepstreepjes toe (Pyphen ``nl_NL``).

    Bestaande ``-`` in het woord blijven leidend (geen her-hyphenatie).
    """
    if not word or "-" in word:
        return word
    if not any(ch.isalpha() for ch in word):
        return word
    return _dutch_dic().inserted(word)


def syllabify_plain_text(text: str) -> str:
    """Hypheneer woorden in platte tekst; whitespace en barlines blijven staan."""
    if not text:
        return text
    parts: list[str] = []
    for match in _TOKEN_RE.finditer(text):
        token = match.group(0)
        if token.isspace() or token in _BARLINE_TOKENS:
            parts.append(token)
            continue
        parts.append(_hyphenate_token(token))
    return "".join(parts)


def syllabify_vsa_body(body: str) -> SyllabifyResult:
    """Hypheneer alleen ``TextNode``-inhoud in een VSA-body (zonder frontmatter)."""
    document = Parser(body).parse()
    replacements = 0
    pieces: list[str] = []
    cursor = 0

    for node in document.nodes:
        if node.start is None or node.end is None:
            continue
        if node.start < cursor:
            raise ValueError(
                f"Overlappende AST-offsets bij {node.start} (cursor={cursor})"
            )
        pieces.append(body[cursor:node.start])
        segment = body[node.start:node.end]
        if isinstance(node, TextNode):
            new_segment, n = _syllabify_text_segment(segment, node.text)
            replacements += n
            pieces.append(new_segment)
        else:
            pieces.append(segment)
        cursor = node.end

    pieces.append(body[cursor:])
    new_body = "".join(pieces)
    return SyllabifyResult(
        text=new_body,
        changed=new_body != body,
        replacements=replacements,
    )


def syllabify_vsa_source(text: str) -> SyllabifyResult:
    """Hypheneer VSA-brontekst; YAML-frontmatter blijft onaangeroerd."""
    _meta, body, body_offset = parse_vsa_frontmatter_with_body_offset(text)
    result = syllabify_vsa_body(body)
    if not result.changed:
        return SyllabifyResult(text=text, changed=False, replacements=0)
    return SyllabifyResult(
        text=text[:body_offset] + result.text,
        changed=True,
        replacements=result.replacements,
    )


def _hyphenate_token(token: str) -> str:
    match = _WORD_CORE_RE.match(token)
    if not match:
        return token
    prefix, core, suffix = match.group(1), match.group(2), match.group(3)
    if not core:
        return token
    return f"{prefix}{hyphenate_dutch_word(core)}{suffix}"


def _syllabify_text_segment(segment: str, expected_stripped: str) -> tuple[str, int]:
    """Hypheneer een TextNode-bronsegment; HTML-comments blijven staan."""
    stripped, _offset_map = strip_vsa_html_comments_with_offset_map(segment)
    if stripped != expected_stripped:
        # Offsets/comments onverwacht: hypheneer veilig per plain-run.
        return _syllabify_preserving_comments(segment)

    if "<!--" not in segment:
        new_text = syllabify_plain_text(segment)
        return new_text, _count_new_hyphens(segment, new_text)

    return _syllabify_preserving_comments(segment)


def _syllabify_preserving_comments(segment: str) -> tuple[str, int]:
    """Spiegel de comment-stripper: comments/comment-regels kopiëren, plain hypheneren."""
    out: list[str] = []
    replacements = 0
    index = 0
    length = len(segment)

    while index < length:
        line_start = index
        line_end = index
        while line_end < length and segment[line_end] not in "\r\n":
            line_end += 1

        if line_end < length:
            if segment[line_end : line_end + 2] == "\r\n":
                line_ending = "\r\n"
                next_index = line_end + 2
            else:
                line_ending = segment[line_end]
                next_index = line_end + 1
        else:
            line_ending = ""
            next_index = line_end

        line_content = segment[line_start:line_end]
        if COMMENT_ONLY_LINE_RE.match(line_content + line_ending):
            out.append(line_content + line_ending)
            index = next_index
            continue

        content_index = 0
        plain_parts: list[str] = []

        def flush_plain() -> None:
            nonlocal replacements
            if not plain_parts:
                return
            plain = "".join(plain_parts)
            plain_parts.clear()
            new_plain = syllabify_plain_text(plain)
            replacements += _count_new_hyphens(plain, new_plain)
            out.append(new_plain)

        while content_index < len(line_content):
            if line_content[content_index : content_index + 4] == "<!--":
                comment_end = line_content.find("-->", content_index)
                if comment_end >= 0:
                    flush_plain()
                    out.append(line_content[content_index : comment_end + 3])
                    content_index = comment_end + 3
                    continue
            plain_parts.append(line_content[content_index])
            content_index += 1

        flush_plain()
        out.append(line_ending)
        index = next_index

    return "".join(out), replacements


def _count_new_hyphens(before: str, after: str) -> int:
    if before == after:
        return 0
    # Tel toegevoegde lettergreepstreepjes grofweg als verschil in '-'-aantal.
    return max(0, after.count("-") - before.count("-"))
