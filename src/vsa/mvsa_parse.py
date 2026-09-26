"""Structured mvsa parse with sticky directives (draft-v0).

Used by validate (sync) and MusicXML export. No blokhergebruik.
"""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from .mvsa_validate import (
    ALLOWED_DIRECTIVES,
    ALLOWED_MODES,
    DO_RE,
    HTML_COMMENT_RE,
    MARKER_RE,
    OCT_ASSIGN_RE,
    SECTIE_ID_RE,
    MvsaDiagnostic,
    _BarSplit,
    _ELMS,
    _split_bars,
    _validate_directive_value,
)

DEGREE_NAMES = {
    "do": 0,
    "re": 1,
    "mi": 2,
    "fa": 3,
    "so": 4,
    "sol": 4,
    "la": 5,
    "si": 6,
    "ti": 6,
}


def _is_syllable_char(c: str) -> bool:
    return c.isalpha() or c in "ëïöüáéíóúýčšžňĚĎŤ#№"


@dataclass
class StickyContext:
    do: str = "F4"
    mode: str = "major"
    oct: dict[str, int] = field(default_factory=dict)  # voice letter -> shift
    start: str | None = None  # raw @start rest

    def oct_for(self, marker: str) -> int:
        letter = marker[0]
        return self.oct.get(letter, 0)


@dataclass
class LPosition:
    """One lengte-positie on a lyrics line."""

    recite: bool
    syllables: list[str]  # syllable texts (punct may be attached)
    elms: list[str]  # one ELM per slot; default "~" if implicit
    # For each syllable after the first: True = hyphen (same word), False = space (new word)
    links: list[bool] = field(default_factory=list)
    # True if this position continues a word started in the previous L-stuk (leading '-')
    continues_word: bool = False


@dataclass
class VoicePosition:
    """One lengte-positie on a stem line."""

    slots: list[str]  # pitch tokens per &-slot (may be "-" hold)


@dataclass
class MeasureBundle:
    """Aligned content for one measure across LSATB markers."""

    lyrics: dict[str, list[LPosition]]  # marker -> positions
    voices: dict[str, list[VoicePosition]]
    final_bar: str


@dataclass
class ParsedSystem:
    start_line: int
    markers: list[str]
    lines: dict[str, str]  # marker -> raw content
    line_nos: dict[str, int]
    ends_section: bool
    context: StickyContext
    measures: list[MeasureBundle] = field(default_factory=list)


@dataclass
class ParsedSection:
    id: str | None
    start_line: int
    systems: list[ParsedSystem] = field(default_factory=list)


@dataclass
class ParsedDocument:
    sections: list[ParsedSection]
    diagnostics: list[MvsaDiagnostic]


def parse_mvsa(text: str) -> ParsedDocument:
    """Parse structure + sticky context + per-measure L/voice tokens."""
    diagnostics: list[MvsaDiagnostic] = []
    cleaned = HTML_COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    lines = cleaned.splitlines()

    sections: list[ParsedSection] = []
    current: ParsedSection | None = None
    pending_sectie: tuple[str, int] | None = None
    ctx = StickyContext()
    i = 0
    n = len(lines)

    while i < n:
        stripped = lines[i].strip()
        line_no = i + 1

        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        if stripped.startswith("@"):
            name, _, rest = stripped[1:].partition(" ")
            name = name.strip()
            rest = rest.strip()
            if name == "sectie":
                if not rest or not SECTIE_ID_RE.match(rest):
                    diagnostics.append(
                        MvsaDiagnostic(
                            "MVSA-SECTIE-ID",
                            f"ongeldige @sectie-id {rest!r}",
                            line_no,
                        )
                    )
                else:
                    if (
                        current is not None
                        and current.systems
                        and not current.systems[-1].ends_section
                    ):
                        diagnostics.append(
                            MvsaDiagnostic(
                                "MVSA-SECTIE-OPEN",
                                f"nieuwe @sectie {rest!r} terwijl vorige niet met || eindigde",
                                line_no,
                            )
                        )
                    pending_sectie = (rest, line_no)
                    current = None
            elif name in ALLOWED_DIRECTIVES:
                _validate_directive_value(name, rest, line_no, diagnostics)
                _apply_directive(ctx, name, rest)
            else:
                diagnostics.append(
                    MvsaDiagnostic(
                        "MVSA-DIRECTIVE",
                        f"onbekende directive @{name}",
                        line_no,
                    )
                )
            i += 1
            continue

        if not MARKER_RE.match(stripped):
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-LINE",
                    f"regel hoort commentaar, directive of LSATB-marker te zijn: {stripped[:40]!r}",
                    line_no,
                )
            )
            i += 1
            continue

        system_lines: list[tuple[int, str, str]] = []
        while i < n:
            s2 = lines[i].strip()
            if not s2 or s2.startswith("#") or s2.startswith("@"):
                break
            m2 = MARKER_RE.match(s2)
            if not m2:
                break
            marker = f"{m2.group(1)}{m2.group(2)}"
            content = s2[m2.end() :].lstrip()
            system_lines.append((i + 1, marker, content))
            i += 1

        if not system_lines:
            i += 1
            continue

        markers = [m for _, m, _ in system_lines]
        if len(markers) != len(set(markers)):
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-MARKER-DUP",
                    f"dubbele marker in LSATB-systeem: {markers}",
                    system_lines[0][0],
                )
            )

        line_map = {m: c for _, m, c in system_lines}
        line_nos = {m: ln for ln, m, _ in system_lines}
        ends, final_bars = _ends_section(system_lines, diagnostics)

        system = ParsedSystem(
            start_line=system_lines[0][0],
            markers=markers,
            lines=line_map,
            line_nos=line_nos,
            ends_section=ends,
            context=deepcopy(ctx),
        )
        system.measures = _build_measures(system, diagnostics)

        if current is None:
            sid = pending_sectie[0] if pending_sectie else None
            start = pending_sectie[1] if pending_sectie else system.start_line
            current = ParsedSection(id=sid, start_line=start)
            sections.append(current)
            pending_sectie = None
        elif pending_sectie is not None:
            current = ParsedSection(id=pending_sectie[0], start_line=pending_sectie[1])
            sections.append(current)
            pending_sectie = None

        current.systems.append(system)
        if ends:
            current = None

    if pending_sectie is not None:
        diagnostics.append(
            MvsaDiagnostic(
                "MVSA-SECTIE-EMPTY",
                f"@sectie {pending_sectie[0]!r} zonder LSATB-systeem",
                pending_sectie[1],
            )
        )
    if current is not None and current.systems and not current.systems[-1].ends_section:
        diagnostics.append(
            MvsaDiagnostic(
                "MVSA-SECTIE-END",
                "laatste sectie eindigt niet met || (of :||) op alle LSATB-regels",
                current.systems[-1].start_line,
            )
        )

    _validate_sync(sections, diagnostics)
    return ParsedDocument(sections=sections, diagnostics=diagnostics)


def _apply_directive(ctx: StickyContext, name: str, rest: str) -> None:
    if name == "do" and rest and DO_RE.match(rest):
        ctx.do = rest[0].upper() + rest[1:]
    elif name == "mode" and rest in ALLOWED_MODES:
        ctx.mode = rest
    elif name == "oct" and rest:
        for part in rest.split():
            m = OCT_ASSIGN_RE.match(part)
            if m:
                ctx.oct[m.group(1)] = int(m.group(3))
    elif name == "start":
        ctx.start = rest or None


def _ends_section(
    system_lines: list[tuple[int, str, str]], diagnostics: list[MvsaDiagnostic]
) -> tuple[bool, list[str | None]]:
    endings: list[str | None] = []
    for line_no, marker, content in system_lines:
        bars = _split_bars(content)
        if not bars.bar_tokens:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-BAR",
                    f"{marker}: regel eindigt niet op een maat-/sectiestreep",
                    line_no,
                )
            )
            endings.append(None)
            continue
        if bars.trailing_text:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-BAR",
                    f"{marker}: tekst na laatste maatstreep: {bars.trailing_text!r}",
                    line_no,
                )
            )
        endings.append(bars.final_bar)
    if not endings or any(e is None for e in endings):
        return False, endings
    if len(set(endings)) != 1:
        diagnostics.append(
            MvsaDiagnostic(
                "MVSA-BAR-SYNC",
                f"LSATB-regels eindigen niet met dezelfde streep: {endings}",
                system_lines[0][0],
            )
        )
    final = endings[0]
    return final in ("||", ":||"), endings


def _build_measures(
    system: ParsedSystem, diagnostics: list[MvsaDiagnostic]
) -> list[MeasureBundle]:
    splits: dict[str, _BarSplit] = {
        m: _split_bars(content) for m, content in system.lines.items()
    }
    counts = {m: len(sp.bar_tokens) for m, sp in splits.items()}
    if len(set(counts.values())) != 1:
        diagnostics.append(
            MvsaDiagnostic(
                "MVSA-MEASURE-COUNT",
                f"ongelijk aantal maatstrepen in systeem: {counts}",
                system.start_line,
            )
        )
        return []

    n = next(iter(counts.values()))
    bundles: list[MeasureBundle] = []
    for mi in range(n):
        lyrics: dict[str, list[LPosition]] = {}
        voices: dict[str, list[VoicePosition]] = {}
        final_bar = next(iter(splits.values())).bar_tokens[mi]
        for marker, sp in splits.items():
            seg = sp.segments[mi]
            if marker[0] == "L":
                lyrics[marker] = parse_l_positions(seg)
            else:
                voices[marker] = parse_voice_positions(seg)
        bundles.append(
            MeasureBundle(lyrics=lyrics, voices=voices, final_bar=final_bar)
        )
    return bundles


def _validate_sync(
    sections: list[ParsedSection], diagnostics: list[MvsaDiagnostic]
) -> None:
    for section in sections:
        if not section.systems:
            continue
        expected = section.systems[0].markers
        for system in section.systems:
            if system.markers != expected:
                diagnostics.append(
                    MvsaDiagnostic(
                        "MVSA-MARKERS",
                        f"marker-volgorde wijkt af: verwacht {expected}, kreeg {system.markers}",
                        system.start_line,
                    )
                )
            if not system.measures:
                continue
            # Prefer primary L as reference
            ref = next((m for m in system.markers if m[0] == "L"), system.markers[0])
            for mi, bundle in enumerate(system.measures):
                ref_slots = _slot_seq(bundle, ref)
                for marker in system.markers:
                    if marker == ref:
                        continue
                    other = _slot_seq(bundle, marker)
                    if other != ref_slots:
                        diagnostics.append(
                            MvsaDiagnostic(
                                "MVSA-SYNC",
                                f"maat {mi + 1}: {marker} slots {other} ≠ {ref} slots {ref_slots}",
                                system.line_nos.get(marker, system.start_line),
                            )
                        )


def _slot_seq(bundle: MeasureBundle, marker: str) -> list[int]:
    if marker in bundle.lyrics:
        return [max(1, len(p.elms)) for p in bundle.lyrics[marker]]
    if marker in bundle.voices:
        return [max(1, len(p.slots)) for p in bundle.voices[marker]]
    return []


# ---------------------------------------------------------------------------
# L / voice tokenizers
# ---------------------------------------------------------------------------


def parse_voice_positions(measure: str) -> list[VoicePosition]:
    out: list[VoicePosition] = []
    for token in measure.split():
        if not token:
            continue
        # Strip trailing ELMs glued to pitch (intocht: a4_, g4__)
        core = _strip_trailing_elms(token)
        parts = core.split("&") if core else token.split("&")
        # If whole token was ELM-only after strip failure, keep raw split
        if not parts or parts == [""]:
            parts = token.split("&")
        out.append(VoicePosition(slots=[p for p in parts if p != ""]))
    return out


def _strip_trailing_elms(token: str) -> str:
    """Remove trailing ELM suffixes from a pitch token (``a4_``, ``si-__``)."""
    # Melisma tokens: strip ELM only from the last slot piece after &
    if "&" in token:
        head, _, last = token.rpartition("&")
        return f"{head}&{_strip_trailing_elms(last)}" if head else _strip_one(token)
    return _strip_one(token)


def _strip_one(token: str) -> str:
    s = token
    while s:
        matched = False
        for e in _ELMS:
            if s.endswith(e) and len(s) > len(e):
                # Don't strip octave suffix "-" from degrees/names: ``si-``, ``g-``
                # ELM "-" at end of ``si-`` is ambiguous; prefer pitch+oct over ELM
                # when remainder looks like a pitch. Strip ``_`` ``__`` ``_.`` etc.
                if e == "-" and _looks_like_pitch_prefix(s[: -len(e)]):
                    break
                if e == "~" and _looks_like_pitch_prefix(s[: -len(e)]):
                    break
                s = s[: -len(e)]
                matched = True
                break
        if not matched:
            break
    return s or token


def _looks_like_pitch_prefix(s: str) -> bool:
    if not s:
        return False
    low = s.lower()
    for name in DEGREE_NAMES:
        if low == name or low.startswith(name):
            return True
    if re.match(r"^[a-gA-G](#|b|bb)?\d*$", s):
        return True
    return False


def parse_l_positions(measure: str) -> list[LPosition]:
    """Parse L measure into positions with syllables + ELMs.

    Reciteertoon: ``( … )`` met optionele ELM direct na ``)``. Binnen de
    haakjes scheiden spaties woorden en ``-`` lettergrepen. Zonder ELM na
    ``)`` is de duur de recite-standaard (export: breve). ``~`` op L is alleen
    nog ELM-duur, nooit recite-marker.
    """
    s = measure.strip()
    if not s:
        return []
    positions: list[LPosition] = []
    i = 0
    n = len(s)

    while i < n:
        if s[i].isspace():
            i += 1
            continue
        if s[i] in ",;:!?":
            i += 1
            continue
        if s[i] == ".":
            is_elm_dot = any(
                s.startswith(e, i) and e in (".", "..", "_.", "-.", "~.") for e in _ELMS
            )
            if not is_elm_dot:
                i += 1
                continue

        if s[i] == "(":
            close = s.find(")", i + 1)
            if close < 0:
                close = n
            interior = s[i + 1 : close]
            i = close + 1 if close < n and s[close] == ")" else n
            syllables, links = _parse_recite_interior(interior)
            # After ')': duration ELMs only — bare '-' is woordstreepje, not ELM.
            elm_list, i = _read_elms(s, i, allow_bare_dash=False)
            positions.append(
                LPosition(
                    recite=True,
                    syllables=syllables,
                    elms=elm_list,
                    links=links,
                    continues_word=False,
                )
            )
            continue

        # Stray '-' (not a woordstreepje before a letter): skip
        if s[i] == "-" and not (i + 1 < n and _is_syllable_char(s[i + 1])):
            i += 1
            continue

        continues_word = False
        if s[i] == "-" and i + 1 < n and _is_syllable_char(s[i + 1]):
            continues_word = True
            i += 1

        syllables: list[str] = []
        links: list[bool] = []
        elms: list[str] = []
        pending_link: bool | None = None

        while True:
            if i >= n:
                break

            start = i
            while i < n and (_is_syllable_char(s[i]) or s[i] in "'’ʹ"):
                i += 1
            syll = s[start:i]
            if not syll:
                break
            while i < n and s[i] in ",;:!?":
                syll += s[i]
                i += 1

            piece_elms, i = _read_elms(s, i)

            if syllables:
                links.append(True if pending_link is None else pending_link)
            syllables.append(syll)
            pending_link = None

            if piece_elms:
                elms.extend(piece_elms)
            else:
                elms.append("~")

            while i < n and s[i] in ",;:!?":
                syllables[-1] += s[i]
                i += 1

            if i < n and s[i] == "-" and i + 1 < n and _is_syllable_char(s[i + 1]):
                i += 1
                pending_link = True
                positions.append(
                    LPosition(
                        recite=False,
                        syllables=syllables,
                        elms=elms if elms else ["~"],
                        links=links,
                        continues_word=continues_word,
                    )
                )
                syllables = []
                links = []
                elms = []
                continues_word = True
                continue

            break

        if elms or syllables:
            if not elms:
                elms = ["~"]
            positions.append(
                LPosition(
                    recite=False,
                    syllables=syllables,
                    elms=elms,
                    links=links,
                    continues_word=continues_word,
                )
            )

    return positions


def _parse_recite_interior(interior: str) -> tuple[list[str], list[bool]]:
    """Syllables + links inside ``( … )`` (space = word, ``-`` = hyphen)."""
    s = interior.strip()
    if not s:
        return [], []
    syllables: list[str] = []
    links: list[bool] = []
    i = 0
    n = len(s)
    pending_link: bool | None = None
    while i < n:
        if s[i].isspace():
            if syllables:
                pending_link = False
            i += 1
            continue
        if s[i] == "-" and i + 1 < n and _is_syllable_char(s[i + 1]):
            pending_link = True
            i += 1
            continue
        if s[i] in ",;:!?" and not syllables:
            i += 1
            continue
        start = i
        while i < n and (_is_syllable_char(s[i]) or s[i] in "'’ʹ"):
            i += 1
        syll = s[start:i]
        if not syll:
            i += 1
            continue
        while i < n and s[i] in ",;:!?":
            syll += s[i]
            i += 1
        if syllables:
            links.append(True if pending_link is None else pending_link)
        syllables.append(syll)
        pending_link = None
        if i < n and s[i] == "-" and i + 1 < n and _is_syllable_char(s[i + 1]):
            pending_link = True
            i += 1
    return syllables, links


def _read_elms(
    s: str, i: int, *, allow_bare_dash: bool = True
) -> tuple[list[str], int]:
    """Read one melisma-chain of ELMs at ``i``; return (elms, new_index).

    After a recite ``)``, pass ``allow_bare_dash=False`` so ``)-lu`` is a
    woordstreepje (not ELM ``-``). Meaningful durations use ``_``, ``~``,
    ``.``, ``-.``, …
    """
    n = len(s)
    piece_elms: list[str] = []
    while True:
        elm = None
        for e in _ELMS:
            if not s.startswith(e, i):
                continue
            if e == "-" and i + 1 < n and _is_syllable_char(s[i + 1]):
                continue
            if e == "-" and not allow_bare_dash:
                continue
            if e == "~" and i + 1 < n and _is_syllable_char(s[i + 1]):
                continue
            elm = e
            break
        if elm is None:
            break
        i += len(elm)
        piece_elms.append(elm)
        if i < n and s[i] == "&":
            i += 1
            continue
        break
    return piece_elms, i
