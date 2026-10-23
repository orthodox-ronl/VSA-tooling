"""Check-only eindankers glued to mvsa bar tokens (draft-v0).

Berekende lopende toon voor de check:

- begint bij pitch-carry van het vorige LSATB-systeem (soft-wrap);
- stemrust ``r``/``R`` wijzigt die toon niet;
- een mislukte slot-resolve wist een eerdere goede toon niet;
- eindanker mag geen rust zijn (wel een geldig hoogte-slot voor noten).
"""

from __future__ import annotations

from .music import Pitch
from .mvsa_musicxml import (
    _expand_start_ehm,
    _resolve_slot,
    seed_voice_resolver,
    writing_do_pitch,
)
from .mvsa_parse import (
    HEIGHT_EHM_RE,
    ParsedDocument,
    ParsedSystem,
    StickyContext,
    is_rest_slot,
    is_valid_height_slot,
)
from .mvsa_validate import MvsaDiagnostic, is_lyrics_stem
from .pitch_resolver import (
    _SCALE_INTERVALS,
    PitchResolver,
    degree_to_pitch,
    pitch_marker_degree,
)


def is_valid_bar_anchor(token: str) -> bool:
    """True if ``token`` may appear as check-only eindanker (not a rest)."""
    tok = token.strip()
    if not tok or is_rest_slot(tok):
        return False
    return is_valid_height_slot(tok)


def collect_bar_anchor_diagnostics(doc: ParsedDocument) -> list[MvsaDiagnostic]:
    out: list[MvsaDiagnostic] = []
    # Documentvolgorde: lopende toon loopt door over systeemovergangen (zelfde
    # soft-wrap-``-`` als export), tenzij een beginanker reset.
    pitch_carry: dict[str, Pitch] = {}
    for section in doc.sections:
        for system in section.systems:
            diags, pitch_carry = _check_system_bar_anchors(
                system, pitch_carry=pitch_carry
            )
            out.extend(diags)
    return out


def _check_system_bar_anchors(
    system: ParsedSystem,
    *,
    pitch_carry: dict[str, Pitch] | None = None,
) -> tuple[list[MvsaDiagnostic], dict[str, Pitch]]:
    diags: list[MvsaDiagnostic] = []
    ctx = system.context
    line_ehms = getattr(system, "line_ehms", {}) or {}
    prev_carry = pitch_carry or {}
    new_carry = dict(prev_carry)

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
        carried = prev_carry.get(letter)
        resolver = seed_voice_resolver(
            ctx,
            marker,
            line_ehm=line_ehms.get(marker),
            carried=carried,
        )

        # Soft-wrap / vorig systeem: start met meegenomen lopende toon, zodat
        # een maat van alleen rusten of holds de eindanker-check niet leeg maakt.
        last_pitch: Pitch | None = carried
        dead = False
        for mi, bundle in enumerate(system.measures):
            if not dead:
                for vpos in bundle.voices.get(marker, []):
                    for slot in vpos.slots:
                        try:
                            resolved = _resolve_slot(
                                slot,
                                resolver,
                                ctx,
                                letter,
                                last_pitch=last_pitch,
                            )
                        except Exception:
                            # Shape errors already reported as MVSA-HOOGTE.
                            # Bewaar de laatste goede toon voor ankers in deze maat.
                            dead = True
                            break
                        # Stemrust → None: lopende toon behouden.
                        if resolved is not None:
                            last_pitch = resolved
                    if dead:
                        break

            anchor = (bundle.bar_anchors or {}).get(marker)
            if not anchor:
                continue
            line_no = system.line_nos.get(marker, system.start_line)
            if not is_valid_bar_anchor(anchor):
                diags.append(
                    MvsaDiagnostic(
                        "MVSA-BAR-ANKER",
                        f"{marker}: ongeldig eindanker {anchor!r} "
                        f"na maat {mi + 1} ({bundle.final_bar})",
                        line_no,
                    )
                )
                continue
            sounding = _effective_sounding_pitch(last_pitch, resolver)
            if sounding is None:
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
            if not _pitches_equal(sounding, expected):
                diags.append(
                    MvsaDiagnostic(
                        "MVSA-BAR-ANKER",
                        f"{marker}: eindanker {anchor!r} na maat {mi + 1}: "
                        f"berekend {_fmt_pitch(sounding)}, "
                        f"verwacht {_fmt_pitch(expected)}",
                        line_no,
                    )
                )
        if not dead:
            # Liever expliciete lopende toon dan kale schrijf-do-default.
            new_carry[letter] = (
                last_pitch
                if last_pitch is not None
                else resolver.current_pitch
            )
    return diags, new_carry


def _effective_sounding_pitch(
    last_pitch: Pitch | None, resolver: PitchResolver
) -> Pitch | None:
    """Pitch for eindanker compare: slot-cursor, else resolver's last sounding."""
    if last_pitch is not None:
        return last_pitch
    sounding = getattr(resolver, "_last_sounding", None)
    return sounding if isinstance(sounding, Pitch) else None


def _expected_pitch_for_anchor(anchor: str, ctx: StickyContext, letter: str) -> Pitch:
    """Expected pitch for a check-only bar anchor (does not mutate voice state)."""
    tok = anchor.strip()
    if is_rest_slot(tok):
        raise ValueError("eindanker mag geen rust zijn")
    if HEIGHT_EHM_RE.fullmatch(tok) or tok in ("-", "~"):
        # VSA-style height-marker body relative to schrijf-do (@do + @oct).
        do_p = writing_do_pitch(ctx, letter)
        intervals = _SCALE_INTERVALS[ctx.mode]
        ehm_list = _expand_start_ehm(tok)
        degree = pitch_marker_degree(ehm_list)
        return degree_to_pitch(do_p, degree, intervals)

    # Absolute ladder / scientific: resolve on a throwaway writing-do resolver.
    r = seed_voice_resolver(ctx, letter)
    r.apply_start_marker([])
    pitch = _resolve_slot(tok, r, ctx, letter, last_pitch=None)
    if pitch is None:
        raise ValueError(f"eindanker {tok!r} levert geen toon")
    return pitch


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
