"""Lettergreepstreepjes in VSA-brontekst (TextNode + grenzen met scopes)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .ast import ScopeNode, TextNode
from .parser import Parser
from .vsa_comments import COMMENT_ONLY_LINE_RE
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


@dataclass(frozen=True)
class _Atom:
    """Bronfragment: platte tekst, scope, of scheiding (spatie/barline/marker)."""

    kind: str  # 'text' | 'scope' | 'sep'
    source: str
    plain: str = ""


@dataclass(frozen=True)
class _ContentPart:
    """Bijdrage aan één woord (scope of tekstkern, zonder brugstreepjes)."""

    kind: str  # 'text' | 'scope'
    source: str
    plain: str
    prefix: str = ""
    core: str = ""
    suffix: str = ""


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


def dutch_hyphen_positions(word: str) -> list[int]:
    """Pyphen-breekposities (index vóór het teken waar ``-`` komt)."""
    if not word or "-" in word:
        return []
    if not any(ch.isalpha() for ch in word):
        return []
    return list(_dutch_dic().positions(word))


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
    """Hypheneer woorden in een VSA-body, inclusief streepjes op scope-grenzen."""
    return _transform_vsa_body(body, unsyllabify=False)


def unsyllabify_vsa_body(body: str) -> SyllabifyResult:
    """Verwijder lettergreepstreepjes, inclusief brugstreepjes rond scopes."""
    return _transform_vsa_body(body, unsyllabify=True)


def syllabify_vsa_source(text: str) -> SyllabifyResult:
    """Hypheneer VSA-brontekst; YAML-frontmatter blijft onaangeroerd."""
    return _transform_vsa_source(text, syllabify_vsa_body)


def unsyllabify_vsa_source(text: str) -> SyllabifyResult:
    """Verwijder lettergreepstreepjes uit VSA-brontekst; scope-inhoud blijft intact."""
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


def _transform_vsa_body(body: str, *, unsyllabify: bool) -> SyllabifyResult:
    document = Parser(body).parse()
    atoms = _atoms_from_document(body, document)
    pieces: list[str] = []
    replacements = 0

    for kind, group in _group_runs(atoms):
        if kind == "sep":
            pieces.append("".join(atom.source for atom in group))
            continue
        new_run, n = _transform_word_run(group, unsyllabify=unsyllabify)
        replacements += n
        pieces.append(new_run)

    new_body = "".join(pieces)
    return SyllabifyResult(
        text=new_body,
        changed=new_body != body,
        replacements=replacements,
    )


def _atoms_from_document(body: str, document) -> list[_Atom]:
    atoms: list[_Atom] = []
    cursor = 0

    for node in document.nodes:
        if node.start is None or node.end is None:
            continue
        if node.start < cursor:
            raise ValueError(
                f"Overlappende AST-offsets bij {node.start} (cursor={cursor})"
            )
        if node.start > cursor:
            atoms.extend(_atoms_from_text_segment(body[cursor : node.start]))

        if isinstance(node, ScopeNode):
            atoms.append(
                _Atom("scope", body[node.start : node.end], plain=node.text)
            )
        elif isinstance(node, TextNode):
            atoms.extend(_atoms_from_text_segment(body[node.start : node.end]))
        else:
            atoms.append(_Atom("sep", body[node.start : node.end]))
        cursor = node.end

    if cursor < len(body):
        atoms.extend(_atoms_from_text_segment(body[cursor:]))
    return atoms


def _atoms_from_text_segment(segment: str) -> list[_Atom]:
    if not segment:
        return []
    if "<!--" in segment:
        return _atoms_from_text_with_comments(segment)
    return _atoms_from_plain_text(segment)


def _atoms_from_plain_text(segment: str) -> list[_Atom]:
    atoms: list[_Atom] = []
    for match in _TOKEN_RE.finditer(segment):
        token = match.group(0)
        if token.isspace() or token in _BARLINE_TOKENS:
            atoms.append(_Atom("sep", token))
        else:
            atoms.append(_Atom("text", token))
    return atoms


def _atoms_from_text_with_comments(segment: str) -> list[_Atom]:
    atoms: list[_Atom] = []
    index = 0
    length = len(segment)
    plain_parts: list[str] = []

    def flush_plain() -> None:
        if not plain_parts:
            return
        atoms.extend(_atoms_from_plain_text("".join(plain_parts)))
        plain_parts.clear()

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
            flush_plain()
            atoms.append(_Atom("sep", line_content + line_ending))
            index = next_index
            continue

        content_index = 0
        while content_index < len(line_content):
            if line_content[content_index : content_index + 4] == "<!--":
                comment_end = line_content.find("-->", content_index)
                if comment_end >= 0:
                    flush_plain()
                    atoms.append(
                        _Atom("sep", line_content[content_index : comment_end + 3])
                    )
                    content_index = comment_end + 3
                    continue
            plain_parts.append(line_content[content_index])
            content_index += 1

        flush_plain()
        if line_ending:
            atoms.append(_Atom("sep", line_ending))
        index = next_index

    return atoms


def _group_runs(atoms: list[_Atom]):
    current: list[_Atom] = []
    for atom in atoms:
        if atom.kind == "sep":
            if current:
                yield "word", current
                current = []
            yield "sep", [atom]
        else:
            current.append(atom)
    if current:
        yield "word", current


def _transform_word_run(
    atoms: list[_Atom], *, unsyllabify: bool
) -> tuple[str, int]:
    original = "".join(atom.source for atom in atoms)
    if unsyllabify:
        new = _unsyllabify_word_run(atoms)
    else:
        new = _syllabify_word_run(atoms)
    return new, _count_hyphen_delta(original, new)


def _content_parts(atoms: list[_Atom]) -> list[_ContentPart]:
    parts: list[_ContentPart] = []
    for atom in atoms:
        if atom.kind == "scope":
            parts.append(_ContentPart("scope", atom.source, atom.plain))
            continue
        parsed = _parse_text_part(atom.source)
        if parsed is not None:
            parts.append(parsed)
    return parts


def _parse_text_part(source: str) -> _ContentPart | None:
    """Tekstatom zonder brugstreepjes; ``None`` als het atom alleen ``-`` is."""
    if source == "-":
        return None

    match = _WORD_CORE_RE.match(source)
    if not match:
        return _ContentPart("text", source, source.replace("-", ""), core=source)

    prefix, core, suffix = match.group(1), match.group(2), match.group(3)

    while prefix.startswith("-"):
        prefix = prefix[1:]
    if suffix and set(suffix) == {"-"}:
        suffix = ""

    if not core and not prefix and not suffix:
        return None

    plain = core.replace("-", "")
    return _ContentPart("text", source, plain, prefix=prefix, core=core, suffix=suffix)


def _syllabify_word_run(atoms: list[_Atom]) -> str:
    parts = _content_parts(atoms)
    if not parts:
        return "".join(atom.source for atom in atoms)

    if len(parts) == 1 and parts[0].kind == "text":
        part = parts[0]
        return f"{part.prefix}{hyphenate_dutch_word(part.core)}{part.suffix}"

    plain = "".join(part.plain for part in parts)
    if not plain or not any(ch.isalpha() for ch in plain):
        return "".join(atom.source for atom in atoms)

    # Bestaande interne streepjes in één tekstdeel: hergebruik die breekpunten
    # alleen wanneer het hele woord uit één tekstdeel bestaat (hierboven).
    # Over scope-grenzen heen altijd Pyphen op het samengestelde woord.
    positions = set(dutch_hyphen_positions(plain))
    return _render_syllabified_parts(parts, positions)


def _render_syllabified_parts(parts: list[_ContentPart], positions: set[int]) -> str:
    out: list[str] = []
    offset = 0
    last_index = len(parts) - 1

    for index, part in enumerate(parts):
        start = offset
        end = offset + len(part.plain)

        if part.kind == "scope":
            out.append(part.source)
        else:
            internal = sorted(p - start for p in positions if start < p < end)
            chunk = _insert_hyphens(part.plain, internal)
            out.append(f"{part.prefix}{chunk}{part.suffix}")

        if index < last_index and end in positions:
            out.append("-")

        offset = end

    return "".join(out)


def _insert_hyphens(text: str, positions: list[int]) -> str:
    if not positions:
        return text
    pieces: list[str] = []
    prev = 0
    for pos in positions:
        pieces.append(text[prev:pos])
        prev = pos
    pieces.append(text[prev:])
    return "-".join(pieces)


def _unsyllabify_word_run(atoms: list[_Atom]) -> str:
    parts = _content_parts(atoms)
    if not parts:
        return "".join(atom.source for atom in atoms)

    out: list[str] = []
    for part in parts:
        if part.kind == "scope":
            out.append(part.source)
        else:
            out.append(f"{part.prefix}{dehyphenate_dutch_word(part.core)}{part.suffix}")
    return "".join(out)


def _count_hyphen_delta(before: str, after: str) -> int:
    if before == after:
        return 0
    return abs(after.count("-") - before.count("-"))
