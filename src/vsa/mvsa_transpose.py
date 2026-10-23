"""Transpose .mvsa to a target tonic (``@do``); mode stays the same.

Shifts every sticky ``@do`` and absolute stem pitches by the same interval.
Relative tokens (EHM, holds) are re-emitted via the chosen ``--pitch`` form
(default ``ag-vsa``), so sounding pitch rises/falls with the new tonic.
"""

from __future__ import annotations

import re
from pathlib import Path

from .music import Pitch
from .mvsa_align import align_mvsa_text
from .mvsa_musicxml import (
    MvsaExportError,
    _resolve_slot,
    seed_voice_resolver,
)
from .mvsa_normalize import (
    DEFAULT_IMPORT_PITCH,
    OCTAVE_STYLES,
    REWRITE_PITCH_FORMS,
    _apply_rewrites,
    _format_pitch,
    canonicalize_pitch_form,
    format_abc_scientific,
    pitch_to_degree_and_chrom,
)
from .mvsa_parse import parse_mvsa
from .mvsa_validate import (
    MvsaValidationError,
    _split_bars,
    is_lyrics_stem,
)
from .pitch_resolver import (
    STEP_NAMES,
    _NATURAL_SEMITONES,
    _SCALE_INTERVALS,
    _pitch_to_midi,
    parse_pitch_string,
)

_DO_LINE_RE = re.compile(
    r"^([ \t]*@do[ \t]+)(\S+)(.*)$",
    re.IGNORECASE,
)


class MvsaTransposeError(Exception):
    def __init__(self, message: str, *, line: int = 0) -> None:
        self.line = line
        super().__init__(message)


def parse_transpose_target(to: str, *, reference_do: Pitch) -> Pitch:
    """Parse ``--to`` as ``F4`` / ``Bb3``, or ``F`` (octaaf van *reference_do*)."""
    raw = to.strip()
    if not raw:
        raise MvsaTransposeError("--to mag niet leeg zijn")
    if raw[-1].isdigit():
        try:
            return parse_pitch_string(raw)
        except ValueError as exc:
            raise MvsaTransposeError(f"ongeldige --to {to!r}: {exc}") from exc
    # Letter (+ alter) zonder octaaf → zelfde octaafcijfer als bron-@do.
    try:
        return parse_pitch_string(f"{raw}{reference_do.octave}")
    except ValueError as exc:
        raise MvsaTransposeError(f"ongeldige --to {to!r}: {exc}") from exc


def format_do_pitch(pitch: Pitch) -> str:
    """``@do``-argument: ``F4``, ``Eb4``, ``Bb3`` (Pitch.__str__)."""
    return str(pitch)


def transpose_pitch(
    pitch: Pitch,
    *,
    semitones: int,
    letter_shift: int,
) -> Pitch:
    """Shift pitch by *semitones*, keeping diatonic letter distance (*letter_shift*)."""
    new_midi = _pitch_to_midi(pitch) + semitones
    new_step = STEP_NAMES[(STEP_NAMES.index(pitch.step) + letter_shift) % 7]
    natural_semi = _NATURAL_SEMITONES[new_step]
    for octv in range(0, 9):
        alter = float(new_midi - (12 * (octv + 1) + natural_semi))
        if -2.0 <= alter <= 2.0:
            return Pitch(step=new_step, octave=octv, alter=alter)
    # Fallback: nearest octave with clamped alter
    octv = new_midi // 12 - 1
    alter = float(new_midi - (12 * (octv + 1) + natural_semi))
    if alter > 2.0:
        alter -= 12.0
        octv += 1
    elif alter < -2.0:
        alter += 12.0
        octv -= 1
    return Pitch(step=new_step, octave=octv, alter=alter)


def _interval_from_dos(source: Pitch, target: Pitch) -> tuple[int, int]:
    semitones = _pitch_to_midi(target) - _pitch_to_midi(source)
    letter_shift = (
        STEP_NAMES.index(target.step) - STEP_NAMES.index(source.step)
    ) % 7
    return semitones, letter_shift


def _reference_do(doc) -> Pitch:
    for section in doc.sections:
        for system in section.systems:
            return parse_pitch_string(system.context.do)
    return parse_pitch_string("F4")


def _rewrite_do_directives(
    text: str,
    *,
    semitones: int,
    letter_shift: int,
) -> str:
    out: list[str] = []
    for line in text.splitlines(keepends=True):
        raw = line.rstrip("\n\r")
        eol = line[len(raw) :]
        m = _DO_LINE_RE.match(raw)
        if not m:
            out.append(line)
            continue
        prefix, arg, suffix = m.group(1), m.group(2), m.group(3)
        try:
            old = parse_pitch_string(arg)
        except ValueError as exc:
            raise MvsaTransposeError(
                f"ongeldige @do {arg!r}: {exc}"
            ) from exc
        new = transpose_pitch(
            old, semitones=semitones, letter_shift=letter_shift
        )
        out.append(f"{prefix}{format_do_pitch(new)}{suffix}{eol}")
    return "".join(out)


def transpose_mvsa_text(
    text: str,
    *,
    to: str,
    pitch: str = DEFAULT_IMPORT_PITCH,
    octave_style: str = "@oct",
    align: bool = True,
) -> str:
    """Return transposed mvsa text; ``@mode`` unchanged."""
    pitch = canonicalize_pitch_form(pitch)
    if pitch not in REWRITE_PITCH_FORMS:
        raise MvsaTransposeError(
            f"onbekende --pitch {pitch!r}; kies uit "
            f"doremi, a-g (of abc), vsa, ag-vsa"
        )
    if octave_style not in OCTAVE_STYLES:
        raise MvsaTransposeError(
            f"onbekende --octave-style {octave_style!r}; "
            f"kies uit {', '.join(OCTAVE_STYLES)}"
        )
    if octave_style == "marker":
        raise MvsaTransposeError(
            "octave-style 'marker' is nog niet geïmplementeerd; gebruik @oct"
        )

    from .mvsa_marks import canonicalize_mark_source

    text = canonicalize_mark_source(text)

    doc = parse_mvsa(text)
    errors = [d for d in doc.diagnostics if d.severity == "error"]
    if errors:
        raise MvsaValidationError(errors)

    source_do = _reference_do(doc)
    target_do = parse_transpose_target(to, reference_do=source_do)
    semitones, letter_shift = _interval_from_dos(source_do, target_do)

    if semitones == 0 and letter_shift == 0:
        # Zelfde tonica: nog steeds stemregels naar gekozen pitch-vorm.
        pass

    text_do = _rewrite_do_directives(
        text, semitones=semitones, letter_shift=letter_shift
    )

    # Resolve tegen de *oude* context; format tegen de *nieuwe* @do.
    doc_old = parse_mvsa(text)
    rewrites: dict[tuple[int, str], tuple[str, str | None]] = {}
    pitch_carry: dict[str, Pitch] = {}

    for section in doc_old.sections:
        for system in section.systems:
            ctx = system.context
            voice_markers = [m for m in system.markers if not is_lyrics_stem(m)]
            if not voice_markers:
                continue

            old_do = parse_pitch_string(ctx.do)
            new_do = transpose_pitch(
                old_do, semitones=semitones, letter_shift=letter_shift
            )
            intervals = _SCALE_INTERVALS[ctx.mode]
            resolvers: dict = {}
            line_ehms = getattr(system, "line_ehms", {}) or {}
            for vm in voice_markers:
                letter = vm[0]
                resolvers[letter] = seed_voice_resolver(
                    ctx,
                    vm,
                    line_ehm=line_ehms.get(vm),
                    carried=pitch_carry.get(letter),
                )

            # last_old: voor resolve (bron-toonsoort); last_new: na shift.
            last_old: dict[str, Pitch | None] = {
                vm[0]: None for vm in voice_markers
            }
            last_new: dict[str, Pitch | None] = {
                vm[0]: None for vm in voice_markers
            }
            prev_degree: dict[str, int | None] = {
                vm[0]: None for vm in voice_markers
            }
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
                                sounding_old = _resolve_slot(
                                    raw,
                                    resolvers[letter],
                                    ctx,
                                    letter,
                                    last_pitch=last_old[letter],
                                )
                            except MvsaExportError as exc:
                                raise MvsaTransposeError(
                                    str(exc),
                                    line=system.line_nos.get(
                                        vm, system.start_line
                                    ),
                                ) from exc
                            sounding = (
                                None
                                if sounding_old is None
                                else transpose_pitch(
                                    sounding_old,
                                    semitones=semitones,
                                    letter_shift=letter_shift,
                                )
                            )
                            if (
                                pitch == "ag-vsa"
                                and prev_degree[letter] is None
                                and sounding is not None
                            ):
                                slot_out.append(format_abc_scientific(sounding))
                                deg, _chrom = pitch_to_degree_and_chrom(
                                    new_do, sounding, intervals
                                )
                                prev_degree[letter] = deg
                            elif raw in ("-", "~"):
                                slot_out.append("-")
                            else:
                                slot_out.append(
                                    _format_pitch(
                                        sounding,
                                        pitch_form=pitch,
                                        do=new_do,
                                        intervals=intervals,
                                        writing_oct=writing_oct,
                                        prev_degree=prev_degree[letter],
                                    )
                                )
                                deg, _chrom = pitch_to_degree_and_chrom(
                                    new_do, sounding, intervals
                                )
                                prev_degree[letter] = deg
                            last_old[letter] = sounding_old
                            last_new[letter] = sounding
                        tokens.append("&".join(slot_out))
                    new_segs[vm].append(" ".join(tokens))

            out_ehm: str | None = "-" if pitch == "vsa" else None
            for vm in voice_markers:
                letter = vm[0]
                # Carry blijft in bron-toonsoort: volgende system resolve't
                # nog tegen de oude sticky context.
                pitch_carry[letter] = resolvers[letter].current_pitch
                bars = _split_bars(system.lines[vm])
                parts: list[str] = []
                segs = new_segs[vm]
                end_pitch = last_new[letter]
                for i, seg in enumerate(segs):
                    parts.append(seg)
                    if i < len(bars.bar_tokens):
                        anchor = ""
                        if (
                            pitch == "ag-vsa"
                            and i == len(segs) - 1
                            and end_pitch is not None
                        ):
                            anchor = format_abc_scientific(end_pitch)
                        elif i < len(bars.bar_anchors) and bars.bar_anchors[i]:
                            # Oude absolute eindanker: verschuif mee.
                            try:
                                old_anchor = parse_pitch_string(
                                    _anchor_to_scientific(
                                        bars.bar_anchors[i], old_do
                                    )
                                )
                                anchor = format_abc_scientific(
                                    transpose_pitch(
                                        old_anchor,
                                        semitones=semitones,
                                        letter_shift=letter_shift,
                                    )
                                )
                            except ValueError:
                                anchor = bars.bar_anchors[i] or ""
                        parts.append(f" {bars.bar_tokens[i]}{anchor}")
                        if i + 1 < len(segs):
                            parts.append(" ")
                rewrites[(system.start_line, vm)] = (
                    "".join(parts).rstrip(),
                    out_ehm,
                )

    out_lines = _apply_rewrites(text_do, rewrites)
    if align:
        out_lines = align_mvsa_text(out_lines)
    return out_lines


def _anchor_to_scientific(anchor: str, do: Pitch) -> str:
    """Bare ``G`` / ``Bb-`` → scientific string parseable by ``parse_pitch_string``.

    Absolute eindankers zonder cijfer liggen in het do-octaaf; ``-``/``+``
    zijn schrijfoctaaf-suffixen (zoals op stemtokens).
    """
    from .pitch_resolver import pitch_in_do_octave

    a = anchor.strip()
    if not a:
        raise ValueError("leeg anker")
    if a[-1].isdigit():
        return a
    oct_delta = 0
    body = a
    while body.endswith("-"):
        oct_delta -= 1
        body = body[:-1]
    while body.endswith("+"):
        oct_delta += 1
        body = body[:-1]
    # Parse letter + alter without octave
    step = body[0].upper()
    rest = body[1:]
    alter = 0.0
    if rest in ("bb", "♭♭"):
        alter = -2.0
    elif rest in ("b", "♭"):
        alter = -1.0
    elif rest in ("#", "♯", "##"):
        alter = 1.0 if rest in ("#", "♯") else 2.0
    elif rest:
        raise ValueError(f"onbekend anker {anchor!r}")
    p = pitch_in_do_octave(do, step, alter, oct_delta=oct_delta)
    return format_do_pitch(p)


def transpose_mvsa_path(
    path: Path,
    out: Path,
    *,
    to: str,
    pitch: str = DEFAULT_IMPORT_PITCH,
    octave_style: str = "@oct",
    align: bool = True,
) -> None:
    """Transpose ``path`` to ``out``."""
    text = path.read_text(encoding="utf-8-sig")
    transposed = transpose_mvsa_text(
        text,
        to=to,
        pitch=pitch,
        octave_style=octave_style,
        align=align,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(transposed, encoding="utf-8", newline="\n")
