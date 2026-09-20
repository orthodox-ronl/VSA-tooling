"""Lettergreepstreepjes in VSA-brontekst (alleen ongescoopte TextNode-inhoud)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

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
_VSA_SUFFIX = ".vsa"


@dataclass(frozen=True)
class SyllabifyResult:
    """Resultaat van ``syllabify_vsa_source`` / ``unsyllabify_vsa_source``."""

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


def dehyphenate_dutch_word(word: str) -> str:
    """Verwijder lettergreepstreepjes uit een woordkern."""
    if not word or "-" not in word:
        return word
    return word.replace("-", "")


def syllabify_plain_text(text: str) -> str:
    """Hypheneer woorden in platte tekst; whitespace en barlines blijven staan."""
    return _map_plain_tokens(text, hyphenate_dutch_word)


def unsyllabify_plain_text(text: str) -> str:
    """Verwijder lettergreepstreepjes in platte tekst; barlines blijven staan."""
    return _map_plain_tokens(text, dehyphenate_dutch_word)


def syllabify_vsa_body(body: str) -> SyllabifyResult:
    """Hypheneer alleen ``TextNode``-inhoud in een VSA-body (zonder frontmatter)."""
    return _transform_vsa_body(body, syllabify_plain_text)


def unsyllabify_vsa_body(body: str) -> SyllabifyResult:
    """Verwijder lettergreepstreepjes alleen uit ``TextNode``-inhoud."""
    return _transform_vsa_body(body, unsyllabify_plain_text)


def syllabify_vsa_source(text: str) -> SyllabifyResult:
    """Hypheneer VSA-brontekst; YAML-frontmatter blijft onaangeroerd."""
    return _transform_vsa_source(text, syllabify_vsa_body)


def unsyllabify_vsa_source(text: str) -> SyllabifyResult:
    """Verwijder lettergreepstreepjes uit VSA-brontekst; scopes blijven onaangeroerd."""
    return _transform_vsa_source(text, unsyllabify_vsa_body)


def transform_vsa_source(text: str, *, unsyllabify: bool = False) -> SyllabifyResult:
    """Syllabify of unsyllabify afhankelijk van ``unsyllabify``."""
    if unsyllabify:
        return unsyllabify_vsa_source(text)
    return syllabify_vsa_source(text)


def iter_vsa_files(path: Path) -> list[Path]:
    """Geef `.vsa`-bestanden: één bestand, of recursief in een map."""
    path = Path(path)
    if path.is_file():
        if path.suffix.lower() != _VSA_SUFFIX:
            raise ValueError(f"verwacht een .vsa-bestand, kreeg: {path}")
        return [path]
    if path.is_dir():
        return sorted(p for p in path.rglob(f"*{_VSA_SUFFIX}") if p.is_file())
    raise FileNotFoundError(str(path))


def normalize_output_extension(extension: str) -> str:
    """Normaliseer ``syl.vsa`` / ``.syl.vsa`` naar ``.syl.vsa``."""
    raw = extension.strip()
    if not raw:
        raise ValueError("extensie mag niet leeg zijn")
    if not raw.startswith("."):
        raw = "." + raw
    if not raw.lower().endswith(_VSA_SUFFIX):
        raise ValueError(
            f"extensie moet eindigen op {_VSA_SUFFIX}, kreeg: {extension!r}"
        )
    return raw


def output_path_for(source: Path, extension: str | None) -> Path:
    """Doelpad: zelfde bestand, of ``xyz.vsa`` → ``xyz`` + genormaliseerde extensie."""
    if extension is None:
        return source
    ext = normalize_output_extension(extension)
    name = source.name
    if not name.lower().endswith(_VSA_SUFFIX):
        raise ValueError(f"bronbestand moet op {_VSA_SUFFIX} eindigen: {source}")
    stem = name[: -len(_VSA_SUFFIX)]
    return source.with_name(stem + ext)


def _map_plain_tokens(text: str, word_fn) -> str:
    if not text:
        return text
    parts: list[str] = []
    for match in _TOKEN_RE.finditer(text):
        token = match.group(0)
        if token.isspace() or token in _BARLINE_TOKENS:
            parts.append(token)
            continue
        parts.append(_map_token_core(token, word_fn))
    return "".join(parts)


def _map_token_core(token: str, word_fn) -> str:
    match = _WORD_CORE_RE.match(token)
    if not match:
        return token
    prefix, core, suffix = match.group(1), match.group(2), match.group(3)
    if not core:
        return token
    return f"{prefix}{word_fn(core)}{suffix}"


def _transform_vsa_source(text: str, body_fn) -> SyllabifyResult:
    _meta, body, body_offset = parse_vsa_frontmatter_with_body_offset(text)
    result = body_fn(body)
    if not result.changed:
        return SyllabifyResult(text=text, changed=False, replacements=0)
    return SyllabifyResult(
        text=text[:body_offset] + result.text,
        changed=True,
        replacements=result.replacements,
    )


def _transform_vsa_body(body: str, plain_fn) -> SyllabifyResult:
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
        pieces.append(body[cursor : node.start])
        segment = body[node.start : node.end]
        if isinstance(node, TextNode):
            new_segment, n = _transform_text_segment(segment, node.text, plain_fn)
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


def _transform_text_segment(
    segment: str,
    expected_stripped: str,
    plain_fn,
) -> tuple[str, int]:
    stripped, _offset_map = strip_vsa_html_comments_with_offset_map(segment)
    if stripped != expected_stripped or "<!--" in segment:
        return _transform_preserving_comments(segment, plain_fn)

    new_text = plain_fn(segment)
    return new_text, _count_hyphen_delta(segment, new_text)


def _transform_preserving_comments(segment: str, plain_fn) -> tuple[str, int]:
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
            new_plain = plain_fn(plain)
            replacements += _count_hyphen_delta(plain, new_plain)
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


def _count_hyphen_delta(before: str, after: str) -> int:
    if before == after:
        return 0
    return abs(after.count("-") - before.count("-"))
