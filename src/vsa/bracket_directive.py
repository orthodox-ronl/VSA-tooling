from __future__ import annotations

from typing import Literal, NamedTuple


BRACKET_DIRECTIVE_END = ":]"

_BASE_EHM_VALUES = [
    "/////",
    "////",
    "///",
    "//",
    "/",
    "\\\\\\\\\\",
    "\\\\\\\\",
    "\\\\\\",
    "\\\\",
    "\\",
    "-",
    "~",
]

_HALFTOON_PREFIXES = ["#", "♯", "+", "b", "♭"]

# Valid EHM values for pitch/height-marker directives.
# The empty string represents the neutral marker `[:]`.
# "/\\" is a legacy special case preserved for compatibility.
VALID_EHM_VALUES: set[str] = (
    {"", "/\\"}
    | set(_BASE_EHM_VALUES)
    | {p + b for p in _HALFTOON_PREFIXES for b in _BASE_EHM_VALUES}
)

BracketDirectiveKind = Literal["pitch_marker", "pitch_transition", "directive"]


class BracketDirective(NamedTuple):
    start: int
    end: int
    body: str
    kind: BracketDirectiveKind = "directive"

    @property
    def source(self) -> str:
        if self.kind == "pitch_transition":
            return "[" + self.body + "]"
        return "[" + self.body + BRACKET_DIRECTIVE_END


def find_bracket_directives(text: str) -> list[BracketDirective]:
    """Find bracket-directives between ``[`` and ``]``.

    Recognizes:

    - hoogte-markeringen ``[<EHM>:]`` (also marker-*shaped* invalid bodies such as
      ``[_:]``, kept as ``kind="directive"`` for existing dispatch callers);
    - toonhoogte-overgangen ``[<EHM>:<EHM>]`` with non-empty rechterzijde.

    Control tokens without ``:`` (e.g. ``[/]``) are intentionally skipped.
    """
    directives: list[BracketDirective] = []
    index = 0

    while index < len(text):
        start = text.find("[", index)
        if start < 0:
            break

        close = text.find("]", start + 1)
        if close < 0:
            index = start + 1
            continue

        inner = text[start + 1 : close]
        end = close + 1

        if inner.endswith(":"):
            body = inner[:-1]
            kind: BracketDirectiveKind = (
                "pitch_marker" if is_valid_ehm(body) else "directive"
            )
            directives.append(
                BracketDirective(start=start, end=end, body=body, kind=kind)
            )
            index = end
            continue

        split = split_pitch_transition_body(inner)
        if split is not None:
            directives.append(
                BracketDirective(
                    start=start,
                    end=end,
                    body=inner,
                    kind="pitch_transition",
                )
            )
            index = end
            continue

        index = start + 1

    return directives


def is_pitch_marker_directive(directive: BracketDirective) -> bool:
    return directive.kind == "pitch_marker" and is_valid_ehm(directive.body)


def is_pitch_transition_directive(directive: BracketDirective) -> bool:
    return directive.kind == "pitch_transition"


def split_pitch_transition_body(body: str) -> tuple[str, str] | None:
    """Return ``(old_ehm, new_ehm)`` for a valid transition body, or ``None``."""
    if ":" not in body or body.endswith(":"):
        return None
    old, _sep, new = body.partition(":")
    if new == "" or ":" in new:
        return None
    if not is_valid_ehm(old) or not is_valid_ehm(new):
        return None
    return old, new


def is_valid_ehm(value: str) -> bool:
    return value in VALID_EHM_VALUES


def pitch_marker_bodies(text: str) -> list[str]:
    return [
        directive.body
        for directive in find_bracket_directives(text)
        if is_pitch_marker_directive(directive)
    ]
