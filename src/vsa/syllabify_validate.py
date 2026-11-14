"""Validate: ontbrekende soft lettergreepstreepjes in platte VSA-tekst."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .ast import Document, TextNode
from .monosyllable_exceptions import (
    EXCEPTIONS_RELATIVE_PATH,
    is_monosyllable_exception,
)
from .syllabify import HARD_HYPHEN, dutch_hyphen_positions, hyphenate_dutch_word

CODE = "VSA-SYLLABIFY-MISSING-HYPHENS"
DOC_URL = "docs/formats/syllabificatie.md"
DEFAULT_SEVERITY = "warning"

_TOKEN_RE = re.compile(r"\S+|\s+", re.UNICODE)
_WORD_CORE_RE = re.compile(r"^(\W*)(.*?)(\W*)$", re.UNICODE)
_BARLINE_TOKENS = frozenset({"/", "//", "*"})


@dataclass(frozen=True)
class MissingHyphenFinding:
    """Eén verdacht plat woord zonder soft ``-``."""

    word: str
    suggestion: str
    line: int
    column: int


def find_missing_syllable_hyphens(
    document: Document,
    *,
    source_text: str = "",
) -> list[MissingHyphenFinding]:
    """Zoek platte TextNode-tokens die Pyphen zou splitsen maar geen soft ``-`` hebben."""
    findings: list[MissingHyphenFinding] = []
    seen: set[tuple[int, int, str]] = set()
    for node in getattr(document, "nodes", []):
        if not isinstance(node, TextNode):
            continue
        text = node.text or ""
        if not text:
            continue
        base = getattr(node, "start", None)
        for match in _TOKEN_RE.finditer(text):
            token = match.group(0)
            if token.isspace() or token in _BARLINE_TOKENS:
                continue
            for core, abs_offset in _iter_cores_needing_hyphen(token, match.start()):
                if is_monosyllable_exception(core):
                    continue
                from .syllable_dictionary import canonical_syllable_form

                # Dictionary-afwijkingen gaan via syllable_dict_check.
                if canonical_syllable_form(core) is not None:
                    continue
                suggestion = hyphenate_dutch_word(core)
                if suggestion == core or "-" not in suggestion:
                    continue
                line, column = _line_column(source_text, base, abs_offset)
                key = (line, column, core.casefold())
                if key in seen:
                    continue
                seen.add(key)
                findings.append(
                    MissingHyphenFinding(
                        word=core,
                        suggestion=suggestion,
                        line=line,
                        column=column,
                    )
                )
    return findings


def format_missing_hyphen_message(finding: MissingHyphenFinding) -> tuple[str, str]:
    """``(message_nl, hint_nl)`` met beide herstelpaden."""
    word = finding.word
    suggestion = finding.suggestion
    message_nl = (
        f"Woord `{word}` heeft geen lettergreepstreepje(s), maar lijkt "
        f"meerlettergrepig (Pyphen: `{suggestion}`)."
    )
    hint_nl = (
        f"Doe één van beide: (1) Zet soft `-` in de bron, bijv. `{word}` → "
        f"`{suggestion}` (zing-deling; ter hulp: "
        f"`vsa syllabify <bestand.vsa> --dry-run`, daarna handmatig "
        f"controleren). (2) Of: als het woord één lettergreep moet blijven, "
        f"voeg `{word.casefold()}` toe als nieuwe regel in "
        f"`{EXCEPTIONS_RELATIVE_PATH}` en draai validate opnieuw. "
        f"Norm: {DOC_URL}."
    )
    return message_nl, hint_nl


def _iter_cores_needing_hyphen(
    token: str, token_start: int
) -> list[tuple[str, int]]:
    """Geef (kern, offset-in-node) voor delen zonder soft ``-`` die Pyphen splitst."""
    m = _WORD_CORE_RE.match(token)
    if not m:
        return []
    prefix, core, _suffix = m.group(1), m.group(2), m.group(3)
    if not core or not any(ch.isalpha() for ch in core):
        return []
    core_start = token_start + len(prefix)
    if HARD_HYPHEN in core:
        out: list[tuple[str, int]] = []
        cursor = core_start
        for part in core.split(HARD_HYPHEN):
            if part and "-" not in part and dutch_hyphen_positions(part):
                out.append((part, cursor))
            cursor += len(part) + 1
        return out
    if "-" in core:
        return []
    if not dutch_hyphen_positions(core):
        return []
    return [(core, core_start)]


def _line_column(
    source_text: str, node_start: int | None, offset_in_node: int
) -> tuple[int, int]:
    if not source_text or node_start is None:
        return 1, 1
    pos = max(0, min(node_start + offset_in_node, len(source_text)))
    before = source_text[:pos]
    line = before.count("\n") + 1
    last_nl = before.rfind("\n")
    col = (pos + 1) if last_nl == -1 else (pos - last_nl)
    return line, col
