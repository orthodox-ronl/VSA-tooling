"""Normalize .mvsa stem pitch spelling (draft-v0).

Rewrites S/A/T/B height tokens to ``doremi``, ``abc``, or ``vsa`` (EHM) while
preserving L-semantics and sticky ``@do`` / ``@mode`` / ``@oct``. Optional
column alignment via :func:`vsa.mvsa_align.align_mvsa_text`.
"""

from __future__ import annotations

from pathlib import Path

from .music import Pitch
from .mvsa_align import align_mvsa_text
from .mvsa_musicxml import (
    MvsaExportError,
    _apply_line_ehm,
    _apply_start,
    _resolve_slot,
    _voice_resolver,
)
from .mvsa_parse import parse_mvsa
from .mvsa_validate import (
    MvsaValidationError,
    _split_bars,
    is_lyrics_stem,
    parse_regelidentifier,
)
from .pitch_resolver import (
    PitchResolver,
    _SCALE_INTERVALS,
    parse_pitch_string,
    pitch_to_degree_and_chrom as _pitch_to_degree_and_chrom,
)

# Canonieke interne waarden (``abc`` = a–g mét wetenschappelijk cijfer).
PITCH_FORMS = ("preserve", "doremi", "abc", "vsa")
# CLI/docs-voorkeur: ``a-g``; ``abc`` blijft alias.
PITCH_FORM_ALIASES = {"a-g": "abc", "ag": "abc"}
OCTAVE_STYLES = ("@oct", "marker")

_DEGREE_LABELS = ("do", "re", "mi", "fa", "so", "la", "si")

# Default when normalizing an existing ``.mvsa``: keep note spellings as written.
DEFAULT_MVSA_PITCH = "preserve"
# Default when importing / converting from a non-``.mvsa`` source.
DEFAULT_IMPORT_PITCH = "doremi"


class MvsaNormalizeError(Exception):
    def __init__(self, message: str, *, line: int = 0) -> None:
        self.line = line
        super().__init__(message)


def canonicalize_pitch_form(pitch: str) -> str:
    """Map CLI aliases (``a-g``) to canonieke forms (``abc``)."""
    return PITCH_FORM_ALIASES.get(pitch, pitch)


def pitch_form_choices(*, include_preserve: bool) -> list[str]:
    """Argparse choices: prefer documenting ``a-g``; keep ``abc`` as alias."""
    base = ["doremi", "a-g", "abc", "vsa"]
    if include_preserve:
        return ["preserve", *base]
    return base


def normalize_mvsa_text(
    text: str,
    *,
    pitch: str = DEFAULT_MVSA_PITCH,
    octave_style: str = "@oct",
    align: bool = True,
) -> str:
    """Return normalized mvsa text.

    ``pitch=preserve`` (default for ``.mvsa`` → ``.mvsa``) keeps stem token
    spellings unchanged and only applies optional column alignment.
    ``doremi`` / ``abc`` (alias ``a-g``) / ``vsa`` rewrite heights.
    ``octave_style=@oct`` keeps existing ``@oct`` directives when rewriting.
    ``marker`` is reserved.
    """
    pitch = canonicalize_pitch_form(pitch)
    if pitch not in PITCH_FORMS:
        raise MvsaNormalizeError(
            f"onbekende --pitch {pitch!r}; kies uit "
            f"preserve, doremi, a-g (of abc), vsa"
        )
    if octave_style not in OCTAVE_STYLES:
        raise MvsaNormalizeError(
            f"onbekende --octave-style {octave_style!r}; "
            f"kies uit {', '.join(OCTAVE_STYLES)}"
        )
    if octave_style == "marker":
        raise MvsaNormalizeError(
            "octave-style 'marker' is nog niet geïmplementeerd; gebruik @oct"
        )

    doc = parse_mvsa(text)
    errors = [d for d in doc.diagnostics if d.severity == "error"]
    if errors:
        raise MvsaValidationError(errors)

    if pitch == "preserve":
        return align_mvsa_text(text) if align else text

    # (system_start_line, marker) -> (new voice content, output ehm | None)
    rewrites: dict[tuple[int, str], tuple[str, str | None]] = {}

    for section in doc.sections:
        for system in section.systems:
            ctx = system.context
            voice_markers = [m for m in system.markers if not is_lyrics_stem(m)]
            if not voice_markers:
                continue

            do_p = parse_pitch_string(ctx.do)
            intervals = _SCALE_INTERVALS[ctx.mode]
            resolvers: dict[str, PitchResolver] = {}
            line_ehms = getattr(system, "line_ehms", {}) or {}
            for vm in voice_markers:
                letter = vm[0]
                resolvers[letter] = _voice_resolver(ctx, letter)
                if ctx.start:
                    _apply_start(resolvers[letter], ctx.start, letter)
                line_ehm = line_ehms.get(vm)
                if line_ehm is not None:
                    _apply_line_ehm(resolvers[letter], line_ehm)

            last_pitch: dict[str, Pitch | None] = {vm[0]: None for vm in voice_markers}
            prev_degree: dict[str, int | None] = {vm[0]: None for vm in voice_markers}
            new_segs: dict[str, list[str]] = {vm: [] for vm in voice_markers}

            for bundle in system.measures:
                for vm in voice_markers:
                    letter = vm[0]
                    writing_oct = ctx.oct_for(vm)
                    tokens: list[str] = []
                    for vpos in bundle.voices.get(vm, []):
                        slot_out: list[str] = []
                        for slot in vpos.slots:
                            raw = slot.strip()
                            try:
                                sounding = _resolve_slot(
                                    raw,
                                    resolvers[letter],
                                    ctx,
                                    letter,
                                    last_pitch=last_pitch[letter],
                                )
                            except MvsaExportError as exc:
                                raise MvsaNormalizeError(
                                    str(exc),
                                    line=system.line_nos.get(vm, system.start_line),
                                ) from exc
                            if raw in ("-", "~"):
                                slot_out.append("-")
                            else:
                                slot_out.append(
                                    _format_pitch(
                                        sounding,
                                        pitch_form=pitch,
                                        do=do_p,
                                        intervals=intervals,
                                        writing_oct=writing_oct,
                                        prev_degree=prev_degree[letter],
                                    )
                                )
                                deg, _chrom = pitch_to_degree_and_chrom(
                                    do_p, sounding, intervals
                                )
                                prev_degree[letter] = deg
                            last_pitch[letter] = sounding
                        tokens.append("&".join(slot_out))
                    new_segs[vm].append(" ".join(tokens))

            out_ehm: str | None = "-" if pitch == "vsa" else None
            for vm in voice_markers:
                bars = _split_bars(system.lines[vm])
                parts: list[str] = []
                segs = new_segs[vm]
                for i, seg in enumerate(segs):
                    parts.append(seg)
                    if i < len(bars.bar_tokens):
                        anchor = ""
                        if i < len(bars.bar_anchors) and bars.bar_anchors[i]:
                            anchor = bars.bar_anchors[i] or ""
                        parts.append(f" {bars.bar_tokens[i]}{anchor}")
                        if i + 1 < len(segs):
                            parts.append(" ")
                rewrites[(system.start_line, vm)] = (
                    "".join(parts).rstrip(),
                    out_ehm,
                )

    out_lines = _apply_rewrites(text, rewrites)
    if align:
        out_lines = align_mvsa_text(out_lines)
    return out_lines


def normalize_mvsa_path(
    path: Path,
    out: Path,
    *,
    pitch: str | None = None,
    octave_style: str = "@oct",
    align: bool = True,
) -> None:
    """Normalize ``path`` to ``out``.

    When *pitch* is omitted, ``.mvsa`` sources default to ``preserve`` (keep
    note names). Pass an explicit form to rewrite.
    """
    if pitch is None:
        pitch = (
            DEFAULT_MVSA_PITCH
            if path.suffix.lower() == ".mvsa"
            else DEFAULT_IMPORT_PITCH
        )
    text = path.read_text(encoding="utf-8")
    normalized = normalize_mvsa_text(
        text, pitch=pitch, octave_style=octave_style, align=align
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(normalized, encoding="utf-8", newline="\n")


def pitch_to_degree_and_chrom(
    do: Pitch, pitch: Pitch, intervals: list[int]
) -> tuple[int, float]:
    """Map sounding pitch to scale degree + chromatic alter vs the natural tone."""
    try:
        return _pitch_to_degree_and_chrom(do, pitch, intervals)
    except ValueError as exc:
        raise MvsaNormalizeError(str(exc)) from exc


def _format_pitch(
    pitch: Pitch,
    *,
    pitch_form: str,
    do: Pitch,
    intervals: list[int],
    writing_oct: int,
    prev_degree: int | None,
) -> str:
    if pitch_form == "abc":
        return format_abc_scientific(pitch)
    if pitch_form == "doremi":
        return format_doremi(pitch, do, intervals, writing_oct)
    # vsa: absolute doremi anchor, then EHM
    if prev_degree is None:
        return format_doremi(pitch, do, intervals, writing_oct)
    return format_ehm(prev_degree, pitch, do, intervals)


def format_doremi(
    pitch: Pitch, do: Pitch, intervals: list[int], writing_oct: int
) -> str:
    deg, chrom = pitch_to_degree_and_chrom(do, pitch, intervals)
    adj = deg - 7 * writing_oct
    name = _DEGREE_LABELS[adj % 7]
    oct_off = adj // 7
    if oct_off == 0:
        oct_s = ""
    elif oct_off == -1:
        oct_s = "-"
    elif oct_off == 1:
        oct_s = "+"
    elif oct_off > 1:
        oct_s = f"+{oct_off}"
    else:
        oct_s = str(oct_off)
    acc = _chrom_suffix(chrom)
    return f"{name}{oct_s}{acc}"


def format_abc_scientific(pitch: Pitch) -> str:
    """Scientific octave on a–g (``bb4``, ``c#5``, ``g3``)."""
    step = pitch.step
    alter = pitch.alter
    if alter == -2.0:
        body = f"{step.lower()}bb"
    elif alter == -1.0:
        body = "Bb" if step == "B" else f"{step.lower()}b"
    elif alter == 1.0:
        body = f"{step.lower()}#"
    elif alter == 2.0:
        body = f"{step.lower()}##"
    else:
        body = step.lower()
    return f"{body}{pitch.octave}"


def format_ehm(
    prev_degree: int, pitch: Pitch, do: Pitch, intervals: list[int]
) -> str:
    deg, chrom = pitch_to_degree_and_chrom(do, pitch, intervals)
    steps = deg - prev_degree
    prefix = _chrom_prefix(chrom)
    if steps == 0:
        return f"{prefix}-" if prefix else "-"
    if steps > 0:
        return f"{prefix}/{steps}" if steps != 1 else f"{prefix}/"
    n = -steps
    return f"{prefix}\\{n}" if n != 1 else f"{prefix}\\"


def _chrom_suffix(chrom: float) -> str:
    if chrom == 1.0:
        return "#"
    if chrom == -1.0:
        return "b"
    if chrom == 2.0:
        return "##"
    if chrom == -2.0:
        return "bb"
    return ""


def _chrom_prefix(chrom: float) -> str:
    if chrom == 1.0:
        return "#"
    if chrom == -1.0:
        return "b"
    return ""


def _apply_rewrites(
    text: str, rewrites: dict[tuple[int, str], tuple[str, str | None]]
) -> str:
    """Replace voice lines in systems that appear in ``rewrites``."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        raw = lines[i].rstrip("\n\r")
        if not parse_regelidentifier(raw.lstrip()):
            out.append(lines[i])
            i += 1
            continue

        j = i
        system_lines: list[tuple[int, str, str | None, str]] = []
        while j < len(lines):
            r = lines[j].rstrip("\n\r")
            rid = parse_regelidentifier(r.lstrip())
            if not rid:
                break
            eol = lines[j][len(r) :] or "\n"
            system_lines.append((j + 1, rid.stem_id, rid.ehm, eol))
            j += 1

        start_line = system_lines[0][0]
        for ln, key, ehm, eol in system_lines:
            if not is_lyrics_stem(key) and (start_line, key) in rewrites:
                content, out_ehm = rewrites[(start_line, key)]
                label = f"{key}{out_ehm}" if out_ehm else key
                out.append(f"{label}: {content}{eol}")
            else:
                out.append(lines[ln - 1])
        i = j
    return "".join(out)
