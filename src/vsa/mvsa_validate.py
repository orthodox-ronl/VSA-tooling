"""mvsa draft-v0: parse + structure/sync-validatie.

Zie ``docs/specification-mvsa/``. Blokhergebruik buiten scope.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

MARKER_RE = re.compile(r"^([LSATB])(\d*):")
SECTIE_ID_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
DO_RE = re.compile(r"^[A-Ga-g](#|b)?[0-9]$")
OCT_ASSIGN_RE = re.compile(r"^([SATB])(\d*)=(-?\d+)$")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

ALLOWED_DIRECTIVES = frozenset({"do", "mode", "oct", "sectie", "start"})
ALLOWED_MODES = frozenset({"major", "minor"})

# Longest-first ELM match (VSA 1.0 set used on L).
_ELMS = ("__", "_.", "-.", "~.", "..", "_", ".", "-", "~")

_BAR_TOKENS = (":||", "||", "|:", ":|", "|")


@dataclass
class MvsaDiagnostic:
    code: str
    message: str
    line: int
    severity: str = "error"


@dataclass
class _RawLine:
    line_no: int
    marker: str  # e.g. L, L1, S
    content: str


@dataclass
class _System:
    start_line: int
    markers: list[str]
    lines: dict[str, _RawLine]  # marker -> line
    ends_section: bool


@dataclass
class _Section:
    id: str | None
    start_line: int
    systems: list[_System] = field(default_factory=list)


class MvsaValidationError(Exception):
    """Aggregated validation failure (CLI prints diagnostics separately)."""

    def __init__(self, diagnostics: list[MvsaDiagnostic]) -> None:
        self.diagnostics = diagnostics
        errors = [d for d in diagnostics if d.severity == "error"]
        super().__init__(f"{len(errors)} mvsa error(s)")


def validate_mvsa_text(text: str, *, source: str = "<mvsa>") -> list[MvsaDiagnostic]:
    """Return diagnostics (errors and warnings). Empty list = OK."""
    diagnostics: list[MvsaDiagnostic] = []
    sections = _parse_document(text, diagnostics)
    if any(d.severity == "error" for d in diagnostics):
        return diagnostics
    for section in sections:
        _validate_section(section, diagnostics)
    return diagnostics


def validate_mvsa_path(path: Path) -> list[MvsaDiagnostic]:
    text = path.read_text(encoding="utf-8")
    return validate_mvsa_text(text, source=str(path))


def collect_mvsa_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.rglob("*.mvsa"))


# ---------------------------------------------------------------------------
# Document parse (structure)
# ---------------------------------------------------------------------------


def _parse_document(text: str, diagnostics: list[MvsaDiagnostic]) -> list[_Section]:
    # Strip HTML comments (may span lines) so nested content is ignored.
    cleaned = HTML_COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    lines = cleaned.splitlines()

    sections: list[_Section] = []
    current: _Section | None = None
    pending_sectie: tuple[str, int] | None = None  # id, line
    i = 0
    n = len(lines)

    while i < n:
        raw = lines[i]
        line_no = i + 1
        stripped = raw.strip()

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
                            f"ongeldige @sectie-id {rest!r} (verwacht [a-z][a-z0-9_-]*)",
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
                                f"nieuwe @sectie {rest!r} terwijl vorige sectie niet met || eindigde",
                                line_no,
                            )
                        )
                    pending_sectie = (rest, line_no)
                    current = None
            elif name in ALLOWED_DIRECTIVES:
                _validate_directive_value(name, rest, line_no, diagnostics)
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

        m = MARKER_RE.match(stripped)
        if not m:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-LINE",
                    f"regel hoort commentaar, directive of LSATB-marker te zijn: {stripped[:40]!r}",
                    line_no,
                )
            )
            i += 1
            continue

        # Start or continue a system: consume consecutive LSATB lines.
        system_lines: list[_RawLine] = []
        while i < n:
            s2 = lines[i].strip()
            if not s2 or s2.startswith("#"):
                break
            if s2.startswith("@"):
                break
            m2 = MARKER_RE.match(s2)
            if not m2:
                break
            letter, digits = m2.group(1), m2.group(2)
            marker = f"{letter}{digits}"
            content = s2[m2.end() :].lstrip()
            system_lines.append(_RawLine(i + 1, marker, content))
            i += 1

        if not system_lines:
            i += 1
            continue

        markers = [rl.marker for rl in system_lines]
        if len(markers) != len(set(markers)):
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-MARKER-DUP",
                    f"dubbele marker in LSATB-systeem: {markers}",
                    system_lines[0].line_no,
                )
            )

        ends = _system_ends_section(system_lines, diagnostics)
        system = _System(
            start_line=system_lines[0].line_no,
            markers=markers,
            lines={rl.marker: rl for rl in system_lines},
            ends_section=ends,
        )

        if current is None:
            sid = pending_sectie[0] if pending_sectie else None
            start = pending_sectie[1] if pending_sectie else system.start_line
            current = _Section(id=sid, start_line=start)
            sections.append(current)
            pending_sectie = None
        elif pending_sectie is not None:
            # @sectie without closing previous — already flagged; start new
            current = _Section(id=pending_sectie[0], start_line=pending_sectie[1])
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
    return sections


# ---------------------------------------------------------------------------
# Directive values
# ---------------------------------------------------------------------------


def _validate_directive_value(
    name: str, rest: str, line_no: int, diagnostics: list[MvsaDiagnostic]
) -> None:
    if name == "do":
        if not rest or not DO_RE.match(rest):
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-DO",
                    f"ongeldige @do-waarde {rest!r} (bv. F4, G4)",
                    line_no,
                )
            )
    elif name == "mode":
        if rest not in ALLOWED_MODES:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-MODE",
                    f"ongeldige @mode {rest!r} (major|minor)",
                    line_no,
                )
            )
    elif name == "oct":
        if not rest:
            diagnostics.append(
                MvsaDiagnostic("MVSA-OCT", "leeg @oct", line_no)
            )
            return
        for part in rest.split():
            if not OCT_ASSIGN_RE.match(part):
                diagnostics.append(
                    MvsaDiagnostic(
                        "MVSA-OCT",
                        f"ongeldige @oct-toekenning {part!r} (bv. S=0 B=-1)",
                        line_no,
                    )
                )
    elif name == "start":
        if not rest:
            diagnostics.append(
                MvsaDiagnostic("MVSA-START", "leeg @start", line_no)
            )
    # sectie handled elsewhere


def _system_ends_section(
    system_lines: list[_RawLine], diagnostics: list[MvsaDiagnostic]
) -> bool:
    """True if every line ends with || or :||."""
    endings: list[str | None] = []
    for rl in system_lines:
        bars = _split_bars(rl.content)
        if not bars.segments and not bars.final_bar:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-BAR",
                    f"{rl.marker}: regel eindigt niet op een maat-/sectiestreep",
                    rl.line_no,
                )
            )
            endings.append(None)
            continue
        if bars.trailing_text:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-BAR",
                    f"{rl.marker}: tekst na laatste maatstreep: {bars.trailing_text!r}",
                    rl.line_no,
                )
            )
        endings.append(bars.final_bar)

    if not endings or any(e is None for e in endings):
        return False
    if len(set(endings)) != 1:
        diagnostics.append(
            MvsaDiagnostic(
                "MVSA-BAR-SYNC",
                f"LSATB-regels eindigen niet met dezelfde streep: {endings}",
                system_lines[0].line_no,
            )
        )
    final = endings[0]
    return final in ("||", ":||")


@dataclass
class _BarSplit:
    segments: list[str]  # measure contents (between bars)
    final_bar: str | None
    trailing_text: str
    bar_tokens: list[str]  # bar after each segment


def _split_bars(content: str) -> _BarSplit:
    segments: list[str] = []
    bar_tokens: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(content)
    while i < n:
        matched = None
        for tok in _BAR_TOKENS:
            if content.startswith(tok, i):
                matched = tok
                break
        if matched:
            segments.append("".join(buf))
            buf = []
            bar_tokens.append(matched)
            i += len(matched)
        else:
            buf.append(content[i])
            i += 1
    trailing = "".join(buf)
    final_bar = bar_tokens[-1] if bar_tokens else None
    return _BarSplit(
        segments=segments,
        final_bar=final_bar,
        trailing_text=trailing.strip(),
        bar_tokens=bar_tokens,
    )


# ---------------------------------------------------------------------------
# Section / sync validation
# ---------------------------------------------------------------------------


def _validate_section(section: _Section, diagnostics: list[MvsaDiagnostic]) -> None:
    if not section.systems:
        return
    expected_markers = section.systems[0].markers
    for system in section.systems:
        if system.markers != expected_markers:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-MARKERS",
                    "LSATB-marker-volgorde wijkt af van het eerste systeem van de sectie: "
                    f"verwacht {expected_markers}, kreeg {system.markers}",
                    system.start_line,
                )
            )
        _validate_system_sync(system, diagnostics)
        # Intermediate systems must not end section; last must — checked at parse
        if system is not section.systems[-1] and system.ends_section:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-SECTIE-EARLY",
                    "|| beëindigt de sectie; verdere systemen horen bij een nieuwe sectie",
                    system.start_line,
                    severity="warning",
                )
            )


def _validate_system_sync(system: _System, diagnostics: list[MvsaDiagnostic]) -> None:
    # Split each line into measures; compare position slot-count sequences.
    per_marker: dict[str, list[list[int]]] = {}
    bar_counts: dict[str, int] = {}

    for marker, rl in system.lines.items():
        split = _split_bars(rl.content)
        bar_counts[marker] = len(split.bar_tokens)
        measures: list[list[int]] = []
        is_lyrics = marker[0] == "L"
        for seg in split.segments:
            if is_lyrics:
                measures.append(_l_position_slots(seg))
            else:
                measures.append(_voice_position_slots(seg))
        per_marker[marker] = measures

    # Same number of barlines / measures
    if len(set(bar_counts.values())) != 1:
        diagnostics.append(
            MvsaDiagnostic(
                "MVSA-MEASURE-COUNT",
                f"ongelijk aantal maatstrepen in systeem: {bar_counts}",
                system.start_line,
            )
        )
        return

    n_measures = next(iter(per_marker.values()))
    n = len(n_measures)
    markers = system.markers
    ref = markers[0]
    for mi in range(n):
        ref_slots = per_marker[ref][mi]
        for marker in markers[1:]:
            other = per_marker[marker][mi]
            if other != ref_slots:
                diagnostics.append(
                    MvsaDiagnostic(
                        "MVSA-SYNC",
                        f"maat {mi + 1}: {marker} slots {other} ≠ {ref} slots {ref_slots}",
                        system.lines[marker].line_no,
                    )
                )


# ---------------------------------------------------------------------------
# Position counting
# ---------------------------------------------------------------------------


def _voice_position_slots(measure: str) -> list[int]:
    tokens = measure.split()
    return [max(1, token.count("&") + 1) if token else 0 for token in tokens if token]


def _l_position_slots(measure: str) -> list[int]:
    """Return slot-count per lengte-positie in one L measure."""
    from .mvsa_parse import parse_l_positions

    return [max(1, len(p.elms)) if p.elms else 1 for p in parse_l_positions(measure)]


# ---------------------------------------------------------------------------
# CLI helper
# ---------------------------------------------------------------------------


def format_diagnostic(d: MvsaDiagnostic, path: Path | None = None) -> str:
    loc = f"{path}:" if path else ""
    return f"{loc}{d.line}: {d.severity}: {d.code}: {d.message}"
