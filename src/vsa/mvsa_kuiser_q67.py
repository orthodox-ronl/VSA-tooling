"""Kuiser Q6 (schets-/importbanners) + Q7 (validate-gate).

Contract: ``docs/formats/kuiser.md``.
"""

from __future__ import annotations

import re

from .mvsa_validate import MvsaValidationError, validate_mvsa_text
from .yaml_frontmatter import strip_yaml_frontmatter

# Import-/schetsbanners (niet ``#maat`` / gewone redactionele comments).
_IMPORTED = re.compile(r"^#\s*Imported\s*:", re.IGNORECASE)
_WAARSCHUWING = re.compile(r"^#\s*WAARSCHUWING\s*:", re.IGNORECASE)
_EMIT_SECTION = re.compile(
    r"^#\s*---\s*specifieke\s+waarschuwingen", re.IGNORECASE
)
# Box-banner: ``#  #…`` / ``#  ###…`` (import- en template-schets).
_BANNER_BOX = re.compile(r"^#\s+#")


def apply_q6(text: str, *, werkbank: bool = False) -> str:
    """Strip ``# Imported:`` / schets-WAARSCHUWING-banners tenzij ``werkbank``."""
    if werkbank:
        return text

    bom = ""
    if text.startswith("\ufeff"):
        bom = "\ufeff"
        text = text[1:]

    fm, body, _ = strip_yaml_frontmatter(text)
    cleaned = _strip_banner_lines(body)
    if cleaned == body and not fm:
        return bom + text

    if not fm:
        return bom + cleaned

    if text.startswith("---"):
        close = text.find("\n---", 3)
        if close != -1:
            fm_bytes = text[: close + len("\n---")]
            rest = text[close + len("\n---") :]
            lead = rest[: len(rest) - len(rest.lstrip("\n"))]
            # Één lege regel tussen FM en body is genoeg.
            if cleaned and not cleaned.startswith("\n"):
                if not lead:
                    lead = "\n"
            return bom + fm_bytes + lead + cleaned

    return bom + cleaned


def assert_q7_valid(text: str) -> None:
    """Q7: resultaat mag geen ``mvsa validate``-errors hebben."""
    errors = [d for d in validate_mvsa_text(text) if d.severity == "error"]
    if errors:
        raise MvsaValidationError(errors)


def _strip_banner_lines(body: str) -> str:
    lines = body.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        raw = lines[i]
        core = raw.rstrip("\r\n")
        stripped = core.strip()

        if _IMPORTED.match(stripped) or _WAARSCHUWING.match(stripped):
            i += 1
            continue
        if _EMIT_SECTION.match(stripped):
            i += 1
            # Rest van emit-blok: ``# WAARSCHUWING:`` / lone ``#`` / tot non-#.
            while i < len(lines):
                nxt = lines[i].rstrip("\r\n").strip()
                if nxt == "#":
                    i += 1
                    break
                if nxt.startswith("#") and (
                    _WAARSCHUWING.match(nxt) or nxt == ""
                ):
                    i += 1
                    continue
                if nxt.startswith("#") and not nxt.lstrip("#").strip():
                    i += 1
                    continue
                break
            continue
        if _BANNER_BOX.match(stripped):
            # Aaneengesloten box-rijen (``#  #…`` / ``#  ###…``).
            i += 1
            while i < len(lines) and _BANNER_BOX.match(
                lines[i].rstrip("\r\n").strip()
            ):
                i += 1
            continue

        out.append(raw)
        i += 1

    text = "".join(out)
    # Compacte leading newlines (max één).
    if text.startswith("\n\n"):
        text = "\n" + text.lstrip("\n")
    return text
