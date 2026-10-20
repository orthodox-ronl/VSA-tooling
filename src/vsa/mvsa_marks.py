"""Uitvoeraanwijzingen op mvsa-L: registry (fase-gewijs geactiveerd).

Zie ``docs/specification-mvsa/uitvoeraanwijzingen.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .duration_model import UnknownELM, elm_to_duration

Attach = Literal["before", "after"]
SpanRole = Literal["none", "start", "stop"]

# Standaard Coria-pauze na ``[//]`` (kwart), zelfde ELM als VSA ``~``.
DEFAULT_CAESURA_ELM = "~"

# ELM's die als cesuur-duur mogen (zelfde set als duration_model default).
CAESURA_DURATION_ELMS = frozenset(
    {"~", "-", "-.", "~.", "_", "_.", "__", ".", ".."}
)


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
    # Cesuur: optionele ELM-duur voor Coria-rust; None = DEFAULT_CAESURA_ELM.
    duration_elm: str | None = None


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
    # Fase 7 — sprongtekens (Segno / Fine / D.S. / Coda); zie uitvoeraanwijzingen §3.5.
    "segno": MarkSpec(raw="segno", kind="segno", attach="before"),
    "coda": MarkSpec(raw="coda", kind="coda", attach="before"),
    "fine": MarkSpec(raw="fine", kind="fine", attach="after"),
    "tocoda": MarkSpec(raw="tocoda", kind="tocoda", attach="after"),
    "dsalfine": MarkSpec(raw="dsalfine", kind="ds_al_fine", attach="after"),
    "dcalfine": MarkSpec(raw="dcalfine", kind="dc_al_fine", attach="after"),
    "dsalcoda": MarkSpec(raw="dsalcoda", kind="ds_al_coda", attach="after"),
    "dcalcoda": MarkSpec(raw="dcalcoda", kind="dc_al_coda", attach="after"),
}

DYNAMICS_RAWS = frozenset({"ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"})

# kind → MusicXML/MSCZ nav-mark id (zelfde ids als speelplan ``_emit_nav_marks``).
JUMP_KIND_TO_NAV: dict[str, str] = {
    "segno": "segno",
    "coda": "coda",
    "fine": "fine",
    "tocoda": "to_coda",
    "ds_al_fine": "ds_al_fine",
    "dc_al_fine": "dc_al_fine",
    "ds_al_coda": "ds_al_coda",
    "dc_al_coda": "dc_al_coda",
}

JUMP_KINDS = frozenset(JUMP_KIND_TO_NAV)

# CamelCase-aliassen → canonieke kleine-letter tokens (normalize).
_JUMP_CANONICALIZE: tuple[tuple[str, str], ...] = (
    ("[Segno]", "[segno]"),
    ("[Coda]", "[coda]"),
    ("[Fine]", "[fine]"),
    ("[ToCoda]", "[tocoda]"),
    ("[DSalFine]", "[dsalfine]"),
    ("[DCalFine]", "[dcalfine]"),
    ("[DSalCoda]", "[dsalcoda]"),
    ("[DCalCoda]", "[dcalcoda]"),
)

_WEDGE_MUSICXML = {
    "cresc": "crescendo",
    "dim": "diminuendo",
}

# L-tempo-woorden → zichtbare MusicXML ``<words>``.
TEMPO_WORDS_DISPLAY = {
    "rit": "rit.",
    "atempo": "a tempo",
}


def parse_caesura_duration_elm(raw: str) -> str | None:
    """Als *raw* een cesuur-token is: ELM-duur (``None`` = standaard kwart).

    ``[//]`` → ``None``; ``[//_]`` → ``"_"``; ongeldig → raise via caller
    (deze functie retourneert alleen voor geldige tokens; gebruik
    :func:`lookup_mark` voor acceptatie).
    """
    if raw == "//":
        return None
    if raw.startswith("//") and raw[2:] in CAESURA_DURATION_ELMS:
        return raw[2:]
    return None


def lookup_mark(raw: str) -> MarkSpec | None:
    hit = ACTIVE_MARKS.get(raw)
    if hit is not None:
        return hit
    # Sprong-aliassen: ``[Segno]`` / ``[DSalFine]`` e.d. (vóór of zonder normalize).
    lowered = raw.lower()
    if lowered != raw:
        jump = ACTIVE_MARKS.get(lowered)
        if jump is not None and jump.kind in JUMP_KINDS:
            return jump
    if raw.startswith("//") and raw[2:] in CAESURA_DURATION_ELMS:
        return MarkSpec(raw=raw, kind="caesura", attach="after")
    return None


def mark_from_raw(raw: str) -> Mark | None:
    """Bouw een :class:`Mark` uit bracket-inhoud, of ``None`` als onbekend."""
    spec = lookup_mark(raw)
    if spec is None:
        return None
    duration_elm: str | None = None
    if spec.kind == "caesura":
        duration_elm = parse_caesura_duration_elm(raw)
        if raw != "//" and duration_elm is None:
            return None
    return Mark(
        kind=spec.kind,
        raw=spec.raw,
        span_role=spec.span_role,
        duration_elm=duration_elm,
    )


def caesura_rest_duration(duration_elm: str | None):
    """MusicXML-:class:`~vsa.music.Duration` voor Coria-cesuur-rust."""
    elm = duration_elm if duration_elm is not None else DEFAULT_CAESURA_ELM
    try:
        return elm_to_duration(elm)
    except UnknownELM:
        return elm_to_duration(DEFAULT_CAESURA_ELM)


def wedge_musicxml_type(kind: str) -> str | None:
    return _WEDGE_MUSICXML.get(kind)


def tempo_words_display(kind: str) -> str | None:
    return TEMPO_WORDS_DISPLAY.get(kind)


def canonicalize_mark_source(text: str) -> str:
    """Alias-schrijfwijzen → canoniek (``[decresc]`` → ``[dim]``; ``[//~]`` → ``[//]``)."""
    out = (
        text.replace("[decresc]", "[dim]")
        .replace("[/decresc]", "[/dim]")
        .replace("[//~]", "[//]")
        .replace("[//-]", "[//]")
    )
    for alias, canon in _JUMP_CANONICALIZE:
        out = out.replace(alias, canon)
    return out


def nav_mark_for_jump_kind(kind: str) -> str | None:
    """MusicXML-nav-id voor een sprong-kind, of ``None``."""
    return JUMP_KIND_TO_NAV.get(kind)


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
