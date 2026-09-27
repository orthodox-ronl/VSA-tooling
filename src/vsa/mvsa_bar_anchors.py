"""Check-only eindankers glued to mvsa bar tokens (draft-v0)."""

from __future__ import annotations

from .music import Pitch
from .mvsa_musicxml import (
    _apply_line_ehm,
    _apply_start,
    _expand_start_ehm,
    _resolve_slot,
    _voice_resolver,
    writing_do_pitch,
)
from .mvsa_parse import (
    HEIGHT_EHM_RE,
    ParsedDocument,
    ParsedSystem,
    StickyContext,
    is_valid_height_slot,
)
from .mvsa_validate import MvsaDiagnostic, is_lyrics_stem
from .pitch_resolver import (
    _SCALE_INTERVALS,
    degree_to_pitch,
    pitch_marker_degree,
)


def collect_bar_anchor_diagnostics(doc: ParsedDocument) -> list[MvsaDiagnostic]:
    out: list[MvsaDiagnostic] = []
    for section in doc.sections:
        for system in section.systems:
            out.extend(_check_system_bar_anchors(system))
    return out


def _check_system_bar_anchors(system: ParsedSystem) -> list[MvsaDiagnostic]:
    diags: list[MvsaDiagnostic] = []
    ctx = system.context
    line_ehms = getattr(system, "line_ehms", {}) or {}

    for marker in system.markers:
        if is_lyrics_stem(marker):
            for mi, bundle in enumerate(system.measures):
                anchor = (bundle.bar_anchors or {}).get(marker)
                if anchor:
                    diags.append(
                        MvsaDiagnostic(
                            "MVSA-BAR-ANKER",
                            f"{marker}: eindanker hoort niet op een lyrics-regel "
                            f"({bundle.final_bar}{anchor})",
                            system.line_nos.get(marker, system.start_line),
                        )
                    )
            continue

        letter = marker[0]
        resolver = _voice_resolver(ctx, letter)
        if ctx.start:
            _apply_start(resolver, ctx.start, letter)
        line_ehm = line_ehms.get(marker)
        if line_ehm is not None:
            _apply_line_ehm(resolver, line_ehm)

        last_pitch: Pitch | None = None
        dead = False
        for mi, bundle in enumerate(system.measures):
            if not dead:
                for vpos in bundle.voices.get(marker, []):
                    for slot in vpos.slots:
                        try:
                            last_pitch = _resolve_slot(
                                slot,
                                resolver,
                                ctx,
                                letter,
                                last_pitch=last_pitch,
                            )
                        except Exception:
                            # Shape errors already reported as MVSA-HOOGTE
                            last_pitch = None
                            dead = True
                            break
                    if dead:
                        break

            anchor = (bundle.bar_anchors or {}).get(marker)
            if not anchor:
                continue
            line_no = system.line_nos.get(marker, system.start_line)
            if not is_valid_height_slot(anchor):
                diags.append(
                    MvsaDiagnostic(
                        "MVSA-BAR-ANKER",
                        f"{marker}: ongeldig eindanker {anchor!r} "
                        f"na maat {mi + 1} ({bundle.final_bar})",
                        line_no,
                    )
                )
                continue
            if last_pitch is None:
                diags.append(
                    MvsaDiagnostic(
                        "MVSA-BAR-ANKER",
                        f"{marker}: eindanker {anchor!r} na maat {mi + 1} "
                        f"maar geen berekende toon",
                        line_no,
                    )
                )
                continue
            try:
                expected = _expected_pitch_for_anchor(anchor, ctx, letter)
            except Exception as exc:
                diags.append(
                    MvsaDiagnostic(
                        "MVSA-BAR-ANKER",
                        f"{marker}: eindanker {anchor!r} na maat {mi + 1}: {exc}",
                        line_no,
                    )
                )
                continue
            if not _pitches_equal(last_pitch, expected):
                diags.append(
                    MvsaDiagnostic(
                        "MVSA-BAR-ANKER",
                        f"{marker}: eindanker {anchor!r} na maat {mi + 1}: "
                        f"berekend {_fmt_pitch(last_pitch)}, "
                        f"verwacht {_fmt_pitch(expected)}",
                        line_no,
                    )
                )
    return diags


def _expected_pitch_for_anchor(anchor: str, ctx: StickyContext, letter: str) -> Pitch:
    """Expected pitch for a check-only bar anchor (does not mutate voice state)."""
    tok = anchor.strip()
    if HEIGHT_EHM_RE.fullmatch(tok) or tok in ("-", "~"):
        # VSA-style height-marker body relative to schrijf-do (@do + @oct).
        do_p = writing_do_pitch(ctx, letter)
        intervals = _SCALE_INTERVALS[ctx.mode]
        ehm_list = _expand_start_ehm(tok)
        degree = pitch_marker_degree(ehm_list)
        return degree_to_pitch(do_p, degree, intervals)

    # Absolute ladder / scientific: resolve on a throwaway writing-do resolver.
    r = _voice_resolver(ctx, letter)
    r.apply_start_marker([])
    return _resolve_slot(tok, r, ctx, letter, last_pitch=None)


def _pitches_equal(a: Pitch, b: Pitch) -> bool:
    return a.step == b.step and a.octave == b.octave and a.alter == b.alter


def _fmt_pitch(p: Pitch) -> str:
    alter = ""
    if p.alter == 1.0:
        alter = "#"
    elif p.alter == -1.0:
        alter = "b"
    elif p.alter == 2.0:
        alter = "##"
    elif p.alter == -2.0:
        alter = "bb"
    return f"{p.step}{alter}{p.octave}"
