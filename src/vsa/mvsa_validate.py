"""mvsa draft-v0: parse + structure/sync-validatie.

Zie ``docs/specification-mvsa/``. Blokhergebruik buiten scope.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Legacy: single-letter SATB+digits only. Prefer :func:`parse_regelidentifier`.
MARKER_RE = re.compile(r"^([LSATB])(\d*):")
SECTIE_ID_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
# Speelblok-id: cijfers of sectie-vorm (zie speelplan.md).
BLOK_ID_RE = re.compile(r"^(?:[1-9][0-9]*|[a-z][a-z0-9_-]*)$")
DO_RE = re.compile(r"^[A-Ga-g](#|b)?[0-9]$")
OCT_ASSIGN_RE = re.compile(r"^([A-Za-z0-9_-]+)=(-?\d+)$")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
STEM_ID_BODY_RE = re.compile(r"^[A-Za-z0-9_-]+$")
# Same shape as stem height EHMs (``/``, ``\6``, ``-``, ``#\``, …).
IDENTIFIER_EHM_RE = re.compile(
    # Zelfde vorm als HEIGHT_EHM_RE: unidirectioneel, geen \/ of /\.
    r"^[+#b♯♭]*(?:/+\d*|\\+\d*|[-~])$"
)

# Keyword after ``@``: [A-Za-z][A-Za-z-_]*
DIRECTIVE_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z-_]*$")


def normalize_directive_name(name: str) -> str:
    """Strip optional trailing ``:`` (``@bron: "…"`` ≡ ``@bron "…"``)."""
    if name.endswith(":") and DIRECTIVE_NAME_RE.fullmatch(name[:-1]):
        return name[:-1]
    return name


# Gedefinieerde keywords (zie docs/specification-mvsa/keywords.md).
ALLOWED_DIRECTIVES = frozenset(
    {
        "do",
        "mode",
        "oct",
        "sectie",
        "blok",
        "speelplan",
        "start",
        "tekst",
        "title",
        "composer",
        "copyright",
        "bron",
        "ondertitel",
        "tekstdichter",
        "arrangeur",
        "vertaler",
        # Gereserveerd: geaccepteerd, nog niet in export/praktijk.
        "toon",
        "genre",
        "opmerkingen",
        "mscz-newline",
        "taal",  # sticky passage-taal (nl|ksl|auto)
    }
)
# Document-metadata met quoted string (laatste waarde wint).
STRING_META_DIRECTIVES = frozenset(
    {
        "title",
        "composer",
        "copyright",
        "bron",
        "ondertitel",
        "tekstdichter",
        "arrangeur",
        "vertaler",
        "toon",
        "genre",
        "opmerkingen",
    }
)
# Nog geen MuseScore/MusicXML-invulling; wel parse + validate.
RESERVED_META_DIRECTIVES = frozenset(
    {"toon", "genre", "opmerkingen"}
)
# Sticky context (geldig vanaf eerstvolgend LSATB-systeem tot herzetting).
STICKY_DIRECTIVES = frozenset({"do", "mode", "oct", "start", "taal"})
ALLOWED_MODES = frozenset({"major", "minor"})
ALLOWED_TALEN = frozenset({"nl", "ksl"})
ALLOWED_TAAL_ARGS = frozenset({"nl", "ksl", "auto"})


def is_noop_separator_directive(name: str, rest: str) -> bool:
    """True for ``@---`` / ``@ ---`` (optionele no-op LSATB-systemscheider).

    Een lege regel scheidt systemen al; ``@---`` is vooral nuttig met
    trailing commentaar na de streepjes (genegeerd), bv.
    ``@--- volgende frase`` of ``@ --- zie blad 2``.
    """
    if name == "---":
        return True
    if not name:
        # ``@ ---`` → rest ``---``; ``@ --- comment`` → rest ``--- comment``.
        return rest == "---" or rest.startswith("--- ")
    return False

# Longest-first ELM match (VSA 1.0 set used on L).
_ELMS = ("__", "_.", "-.", "~.", "..", "_", ".", "-", "~")

_BAR_TOKENS = (":||", "||", "|:", ":|", "|")


@dataclass
class MvsaDiagnostic:
    code: str
    message: str
    line: int
    severity: str = "error"


@dataclass(frozen=True)
class RegelIdentifier:
    """Parsed ``stemidentifier`` + optional EHM + ``:`` at the start of a line."""

    stem_id: str
    ehm: str | None
    is_lyrics: bool
    prefix: str  # stem_id + ehm (ehm may be empty)
    match_end: int  # index after ``:`` in the matched string

    @property
    def identity(self) -> str:
        """Stable id for sectie-volgorde (includes EHM when present)."""
        return self.prefix


def is_lyrics_stem(stem_id: str) -> bool:
    return bool(stem_id) and stem_id[0] in "Ll"


def stem_id_ok(stem_id: str) -> bool:
    """True if *stem_id* matches the stemidentifier production."""
    if not stem_id or not STEM_ID_BODY_RE.fullmatch(stem_id):
        return False
    return stem_id[-1] not in "_-"


def parse_regelidentifier(line: str) -> RegelIdentifier | None:
    """Parse a leading regelidentifier from a (typically stripped) line.

    Returns ``None`` if the line does not start with a valid identifier.
    Lyrics-lines with an EHM still parse; callers must reject that as an error.
    """
    if not line:
        return None
    colon = line.find(":")
    if colon <= 0:
        return None
    prefix = line[:colon]
    stem_id: str | None = None
    ehm: str | None = None
    for i in range(len(prefix)):
        suffix = prefix[i:]
        if not IDENTIFIER_EHM_RE.fullmatch(suffix):
            continue
        cand = prefix[:i]
        if stem_id_ok(cand):
            stem_id = cand
            ehm = suffix
            break
    if stem_id is None:
        if not stem_id_ok(prefix):
            return None
        stem_id = prefix
        ehm = None
    return RegelIdentifier(
        stem_id=stem_id,
        ehm=ehm,
        is_lyrics=is_lyrics_stem(stem_id),
        prefix=prefix,
        match_end=colon + 1,
    )


@dataclass
class _RawLine:
    line_no: int
    marker: str  # stem_id (dict key), e.g. L, L1, S, cantus
    content: str
    ehm: str | None = None
    is_lyrics: bool = False

    @property
    def identity(self) -> str:
        return self.marker if not self.ehm else f"{self.marker}{self.ehm}"


@dataclass
class _System:
    start_line: int
    markers: list[str]  # stem_ids in order
    lines: dict[str, _RawLine]  # stem_id -> line
    ends_section: bool
    identities: list[str] = field(default_factory=list)  # stem+ehm order keys


@dataclass
class _Section:
    id: str | None
    start_line: int
    systems: list[_System] = field(default_factory=list)
    # ``blok`` | ``sectie`` | None (anonieme sectie)
    origin: str | None = None


class MvsaValidationError(Exception):
    """Aggregated validation failure (CLI prints diagnostics separately)."""

    def __init__(self, diagnostics: list[MvsaDiagnostic]) -> None:
        self.diagnostics = diagnostics
        errors = [d for d in diagnostics if d.severity == "error"]
        super().__init__(f"{len(errors)} mvsa error(s)")


def validate_mvsa_text(text: str, *, source: str = "<mvsa>") -> list[MvsaDiagnostic]:
    """Return diagnostics (errors and warnings). Empty list = OK."""
    if text.startswith("\ufeff"):
        text = text[1:]
    diagnostics: list[MvsaDiagnostic] = []
    sections = _parse_document(text, diagnostics)
    if any(d.severity == "error" for d in diagnostics):
        return diagnostics
    for section in sections:
        _validate_section(section, diagnostics)
    # Pitch-level eindanker + speelplan (shared with parse_mvsa).
    from .mvsa_parse import parse_mvsa

    doc = parse_mvsa(text)
    _MERGE_FROM_PARSE = (
        "MVSA-BAR-ANKER",
        "MVSA-BLOK-ID",
        "MVSA-BLOK-DUP",
        "MVSA-SPEELPLAN-SYNTAX",
        "MVSA-SPEELPLAN-MULTI",
        "MVSA-SPEELPLAN-UNKNOWN-ID",
        "MVSA-SPEELPLAN-ANON",
        "MVSA-SPEELPLAN-REPEAT-BAR",
        "MVSA-SPEELPLAN-UNUSED",
        "MVSA-BLOK-EMPTY",
    )
    for d in doc.diagnostics:
        if d.code in _MERGE_FROM_PARSE:
            diagnostics.append(d)
    return diagnostics


def validate_mvsa_path(path: Path) -> list[MvsaDiagnostic]:
    text = path.read_text(encoding="utf-8-sig")
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
    pending_sectie: tuple[str, int, str] | None = None  # id, line, origin
    pending_tekst_lines: list[int] = []
    pending_mscz_newline_lines: list[int] = []
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
            name = normalize_directive_name(name.strip())
            rest = rest.strip()
            if is_noop_separator_directive(name, rest):
                pass  # optionele no-op; lege regel scheidt systemen al
            elif not name or not DIRECTIVE_NAME_RE.fullmatch(name):
                diagnostics.append(
                    MvsaDiagnostic(
                        "MVSA-DIRECTIVE",
                        f"ongeldige @-keyword {name!r} "
                        f"(verwacht [A-Za-z][A-Za-z-_]* of @---)",
                        line_no,
                        severity="warning",
                    )
                )
            elif name == "sectie":
                if not rest or not SECTIE_ID_RE.match(rest):
                    diagnostics.append(
                        MvsaDiagnostic(
                            "MVSA-SECTIE-ID",
                            f"ongeldige @sectie-id {rest!r} "
                            f"(verwacht [a-z][a-z0-9_-]*)",
                            line_no,
                        )
                    )
                else:
                    # Nieuwe @sectie: laatste maatstreep van vorige sectie
                    # (ook |) is sectie-einde; geen MVSA-SECTIE-IMPLICIT.
                    pending_sectie = (rest, line_no, "sectie")
                    current = None
            elif name == "blok":
                if not rest or not BLOK_ID_RE.match(rest):
                    diagnostics.append(
                        MvsaDiagnostic(
                            "MVSA-BLOK-ID",
                            f"ongeldige @blok-id {rest!r} "
                            f"(verwacht [1-9][0-9]* of [a-z][a-z0-9_-]*)",
                            line_no,
                        )
                    )
                else:
                    # Speelblok ≠ sectie: geen ||-eis tussen @blok's.
                    pending_sectie = (rest, line_no, "blok")
                    current = None
            elif name in ALLOWED_DIRECTIVES:
                _validate_directive_value(name, rest, line_no, diagnostics)
                if name == "tekst" and parse_tekst_argument(rest) is not None:
                    pending_tekst_lines.append(line_no)
                elif name == "mscz-newline" and not rest:
                    pending_mscz_newline_lines.append(line_no)
            else:
                diagnostics.append(
                    MvsaDiagnostic(
                        "MVSA-DIRECTIVE",
                        f"onbekende @-keyword @{name} (experimenteel; "
                        f"nog niet in de specificatie)",
                        line_no,
                        severity="warning",
                    )
                )
            i += 1
            continue

        m = parse_regelidentifier(stripped)
        if not m:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-LINE",
                    f"regel hoort commentaar, directive of regelidentifier te zijn: {stripped[:40]!r}",
                    line_no,
                )
            )
            i += 1
            continue

        # Consume LSATB lines: #-commentaar mag ertussen; lege regel eindigt het systeem.
        system_lines: list[_RawLine] = []
        while i < n:
            s2 = lines[i].strip()
            if not s2:
                break
            if s2.startswith("#"):
                i += 1
                continue
            if s2.startswith("@"):
                break
            rid = parse_regelidentifier(s2)
            if not rid:
                break
            if rid.is_lyrics and rid.ehm is not None:
                diagnostics.append(
                    MvsaDiagnostic(
                        "MVSA-EHM-L",
                        f"lyrics-regelidentifier mag geen EHM bevatten: {rid.prefix!r}",
                        i + 1,
                    )
                )
            content = s2[rid.match_end :].lstrip()
            system_lines.append(
                _RawLine(
                    i + 1,
                    rid.stem_id,
                    content,
                    ehm=rid.ehm,
                    is_lyrics=rid.is_lyrics,
                )
            )
            i += 1

        if not system_lines:
            i += 1
            continue

        markers = [rl.marker for rl in system_lines]
        identities = [rl.identity for rl in system_lines]
        if len(markers) != len(set(markers)):
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-MARKER-DUP",
                    f"dubbele stemidentifier in LSATB-systeem: {markers}",
                    system_lines[0].line_no,
                )
            )

        ends = _system_ends_section(system_lines, diagnostics)
        system = _System(
            start_line=system_lines[0].line_no,
            markers=markers,
            lines={rl.marker: rl for rl in system_lines},
            ends_section=ends,
            identities=identities,
        )
        pending_tekst_lines.clear()
        pending_mscz_newline_lines.clear()

        if current is None:
            if pending_sectie:
                sid, start, origin = pending_sectie
            else:
                sid, start, origin = None, system.start_line, None
            current = _Section(id=sid, start_line=start, origin=origin)
            sections.append(current)
            pending_sectie = None
        elif pending_sectie is not None:
            sid, start, origin = pending_sectie
            current = _Section(id=sid, start_line=start, origin=origin)
            sections.append(current)
            pending_sectie = None

        current.systems.append(system)
        if ends:
            current = None

    for tekst_line in pending_tekst_lines:
        diagnostics.append(
            MvsaDiagnostic(
                "MVSA-TEKST",
                "@tekst zonder volgend LSATB-systeem",
                tekst_line,
                severity="warning",
            )
        )
    for nl_line in pending_mscz_newline_lines:
        diagnostics.append(
            MvsaDiagnostic(
                "MVSA-MSCZ-NEWLINE",
                "@mscz-newline zonder volgend LSATB-systeem",
                nl_line,
                severity="warning",
            )
        )
    if pending_sectie is not None:
        sid, start, origin = pending_sectie
        label = "@blok" if origin == "blok" else "@sectie"
        diagnostics.append(
            MvsaDiagnostic(
                "MVSA-BLOK-EMPTY" if origin == "blok" else "MVSA-SECTIE-EMPTY",
                f"{label} {sid!r} zonder LSATB-systeem",
                start,
            )
        )
    # EOF / fence-::: : open sectie eindigt op de laatste maatstreep
    # van het laatste systeem (| of ||); geen warning. Speelblokken: idem.
    return sections


# ---------------------------------------------------------------------------
# Directive values
# ---------------------------------------------------------------------------


def parse_tekst_argument(rest: str) -> str | None:
    """Parse ``@tekst`` argument: a double-quoted string.

    Supports ``\\\\`` and ``\\"`` escapes. Returns ``None`` if *rest* is not a
    single well-formed quoted string (optional trailing whitespace only).
    """
    s = rest.strip()
    if len(s) < 2 or s[0] != '"':
        return None
    out: list[str] = []
    i = 1
    while i < len(s):
        ch = s[i]
        if ch == "\\":
            if i + 1 >= len(s):
                return None
            nxt = s[i + 1]
            if nxt in '"\\':
                out.append(nxt)
            else:
                out.append(nxt)
            i += 2
            continue
        if ch == '"':
            if s[i + 1 :].strip():
                return None
            return "".join(out)
        out.append(ch)
        i += 1
    return None


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
    elif name == "taal":
        if rest in ALLOWED_TAAL_ARGS:
            return
        if parse_tekst_argument(rest) is None:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-TAAL",
                    f"ongeldige @taal {rest!r} "
                    f'(nl|ksl|auto, of quoted string bv. @taal "nl")',
                    line_no,
                )
            )
    elif name == "tekst":
        if parse_tekst_argument(rest) is None:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-TEKST",
                    f"ongeldige @tekst-waarde {rest!r} "
                    f'(verwacht een string tussen dubbele aanhalingstekens, '
                    f'bv. @tekst "P: …")',
                    line_no,
                )
            )
    elif name in STRING_META_DIRECTIVES:
        if parse_tekst_argument(rest) is None:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-META",
                    f"ongeldige @{name}-waarde {rest!r} "
                    f'(verwacht een string tussen dubbele aanhalingstekens, '
                    f'bv. @{name} "…")',
                    line_no,
                )
            )
    elif name == "mscz-newline":
        if rest:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-MSCZ-NEWLINE",
                    f"@mscz-newline neemt geen argumenten (kreeg {rest!r})",
                    line_no,
                )
            )
    # sectie / blok / speelplan: structuur + semantiek in parse_mvsa
    # (via merge in validate_mvsa_text).
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
    bar_tokens: list[str]  # bare bar after each segment
    bar_anchors: list[str | None] = field(default_factory=list)
    # Streep vóór de eerste inhoudsmaat (``|: …`` zonder lege maat ervoor)
    leading_bar: str | None = None


def _bar_starts_at(content: str, index: int) -> str | None:
    for tok in _BAR_TOKENS:
        if content.startswith(tok, index):
            return tok
    return None


def _read_bar_anchor(content: str, start: int) -> tuple[str | None, int]:
    """Read optional eindanker glued to a bar (no leading space).

    Returns ``(anchor, index_after)``. A bare bar (space or end) yields
    ``(None, start)``. Non-empty glued text is returned as-is; callers validate.
    """
    n = len(content)
    if start >= n or content[start] in " \t":
        return None, start
    j = start
    while j < n and content[j] not in " \t":
        if _bar_starts_at(content, j):
            break
        j += 1
    candidate = content[start:j]
    if not candidate:
        return None, start
    return candidate, j


def _split_bars(content: str) -> _BarSplit:
    segments: list[str] = []
    bar_tokens: list[str] = []
    bar_anchors: list[str | None] = []
    buf: list[str] = []
    i = 0
    n = len(content)
    while i < n:
        matched = _bar_starts_at(content, i)
        if matched:
            segments.append("".join(buf))
            buf = []
            bar_tokens.append(matched)
            i += len(matched)
            anchor, i = _read_bar_anchor(content, i)
            bar_anchors.append(anchor)
        else:
            buf.append(content[i])
            i += 1
    trailing = "".join(buf)
    # Leidende streep(en) zonder inhoud → geen lege maat; bewaar als leading_bar.
    leading_bar: str | None = None
    while segments and not segments[0].strip() and bar_tokens:
        leading_bar = bar_tokens[0]
        segments.pop(0)
        bar_tokens.pop(0)
        if bar_anchors:
            bar_anchors.pop(0)
    final_bar = bar_tokens[-1] if bar_tokens else None
    return _BarSplit(
        segments=segments,
        final_bar=final_bar,
        trailing_text=trailing.strip(),
        bar_tokens=bar_tokens,
        bar_anchors=bar_anchors,
        leading_bar=leading_bar,
    )


# ---------------------------------------------------------------------------
# Section / sync validation
# ---------------------------------------------------------------------------


def _validate_section(section: _Section, diagnostics: list[MvsaDiagnostic]) -> None:
    if not section.systems:
        return
    expected_ids = section.systems[0].identities or section.systems[0].markers
    for system in section.systems:
        got_ids = system.identities or system.markers
        if got_ids != expected_ids:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-MARKERS",
                    "regelidentifier-volgorde wijkt af van het eerste systeem van de sectie: "
                    f"verwacht {expected_ids}, kreeg {got_ids}",
                    system.start_line,
                )
            )
        _validate_system_sync(system, diagnostics)
        _validate_system_height_tokens(system, diagnostics)
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
        is_lyrics = rl.is_lyrics or is_lyrics_stem(marker)
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


def _validate_system_height_tokens(
    system: _System, diagnostics: list[MvsaDiagnostic]
) -> None:
    """Reject L-ELMs and other non-pitch tokens on stem lines (MVSA-HOOGTE)."""
    from .mvsa_parse import is_valid_height_slot, parse_voice_positions

    for marker, rl in system.lines.items():
        if rl.is_lyrics or is_lyrics_stem(marker):
            continue
        split = _split_bars(rl.content)
        for mi, seg in enumerate(split.segments):
            for pi, vpos in enumerate(parse_voice_positions(seg)):
                for si, slot in enumerate(vpos.slots):
                    if is_valid_height_slot(slot):
                        continue
                    diagnostics.append(
                        MvsaDiagnostic(
                            "MVSA-HOOGTE",
                            f"{marker}: onbekende hoogte-token {slot!r} "
                            f"(maat {mi + 1}, positie {pi + 1}, slot {si + 1})",
                            rl.line_no,
                        )
                    )


# ---------------------------------------------------------------------------
# CLI helper
# ---------------------------------------------------------------------------


def format_diagnostic(d: MvsaDiagnostic, path: Path | None = None) -> str:
    loc = f"{path}:" if path else ""
    return f"{loc}{d.line}: {d.severity}: {d.code}: {d.message}"
