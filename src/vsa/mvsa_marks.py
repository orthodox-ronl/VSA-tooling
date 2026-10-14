"""Uitvoeraanwijzingen op mvsa-L: registry (fase-gewijs geactiveerd).

Zie ``docs/specification-mvsa/uitvoeraanwijzingen.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Attach = Literal["before", "after"]
SpanRole = Literal["none", "start", "stop"]


@dataclass(frozen=True)
class MarkSpec:
    raw: str
    kind: str
    attach: Attach
    span_role: SpanRole = "none"


@dataclass(frozen=True)
class Mark:
    kind: str
    raw: str
    span_role: SpanRole = "none"


# Alleen actieve tokens; rest = onbekend tot hun fase.
ACTIVE_MARKS: dict[str, MarkSpec] = {
    "//": MarkSpec(raw="//", kind="caesura", attach="after"),
    "adem": MarkSpec(raw="adem", kind="breath", attach="after"),
    "ferm": MarkSpec(raw="ferm", kind="fermata", attach="after"),
    "cresc": MarkSpec(raw="cresc", kind="cresc", attach="before", span_role="start"),
    "/cresc": MarkSpec(
        raw="/cresc", kind="cresc", attach="after", span_role="stop"
    ),
    "dim": MarkSpec(raw="dim", kind="dim", attach="before", span_role="start"),
    "/dim": MarkSpec(raw="/dim", kind="dim", attach="after", span_role="stop"),
    "decresc": MarkSpec(
        raw="decresc", kind="dim", attach="before", span_role="start"
    ),
    "/decresc": MarkSpec(
        raw="/decresc", kind="dim", attach="after", span_role="stop"
    ),
    "rit": MarkSpec(raw="rit", kind="rit", attach="before"),
    "atempo": MarkSpec(raw="atempo", kind="atempo", attach="before"),
    "ppp": MarkSpec(raw="ppp", kind="dyn_ppp", attach="before"),
    "pp": MarkSpec(raw="pp", kind="dyn_pp", attach="before"),
    "p": MarkSpec(raw="p", kind="dyn_p", attach="before"),
    "mp": MarkSpec(raw="mp", kind="dyn_mp", attach="before"),
    "mf": MarkSpec(raw="mf", kind="dyn_mf", attach="before"),
    "f": MarkSpec(raw="f", kind="dyn_f", attach="before"),
    "ff": MarkSpec(raw="ff", kind="dyn_ff", attach="before"),
    "fff": MarkSpec(raw="fff", kind="dyn_fff", attach="before"),
}

DYNAMICS_RAWS = frozenset({"ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"})

_WEDGE_MUSICXML = {
    "cresc": "crescendo",
    "dim": "diminuendo",
}

# L-tempo-woorden → zichtbare MusicXML ``<words>``.
TEMPO_WORDS_DISPLAY = {
    "rit": "rit.",
    "atempo": "a tempo",
}


def lookup_mark(raw: str) -> MarkSpec | None:
    return ACTIVE_MARKS.get(raw)


def wedge_musicxml_type(kind: str) -> str | None:
    return _WEDGE_MUSICXML.get(kind)


def tempo_words_display(kind: str) -> str | None:
    return TEMPO_WORDS_DISPLAY.get(kind)


def canonicalize_mark_source(text: str) -> str:
    """Alias-schrijfwijzen → canoniek (``[decresc]`` → ``[dim]``)."""
    return (
        text.replace("[decresc]", "[dim]")
        .replace("[/decresc]", "[/dim]")
    )


def read_bracket_token(s: str, i: int) -> tuple[str | None, int, str | None]:
    """Lees ``[…]`` vanaf *i*.

    Returns ``(raw_or_none, new_index, error_or_none)``.
    ``raw`` is zonder haken; bij ontbrekende ``]`` is raw None en error gezet.
    """
    if i >= len(s) or s[i] != "[":
        return None, i, None
    close = s.find("]", i + 1)
    if close < 0:
        return None, len(s), "unclosed"
    raw = s[i + 1 : close]
    return raw, close + 1, None
