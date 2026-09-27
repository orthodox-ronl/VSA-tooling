"""Speelplan / @blok helpers (fase 1).

Zie ``docs/specification-mvsa/speelplan.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .mvsa_validate import BLOK_ID_RE, MvsaDiagnostic

if TYPE_CHECKING:
    from .mvsa_parse import ParsedDocument, ParsedSection

_FORBIDDEN_REPEAT_BARS = frozenset({"|:", ":|", ":||"})


def parse_speelplan_argument(rest: str) -> tuple[list[str] | None, str | None]:
    """Parse ``1, 2, 1, 3`` → ids, or (None, error_message)."""
    if not rest.strip():
        return None, "leeg speelplan"
    parts = [p.strip() for p in rest.split(",")]
    if any(not p for p in parts):
        return None, "leeg id in speelplan (dubbele komma of trailing komma?)"
    for p in parts:
        if not BLOK_ID_RE.match(p):
            return None, f"ongeldig speelplan-id {p!r}"
    return parts, None


def format_speelplan_text(ids: list[str]) -> str:
    """Bladmarkering fase 1: ``Speel: 1-2-1-2-1-3``."""
    return "Speel: " + "-".join(ids)


def sections_for_layout(
    doc: ParsedDocument,
    *,
    layout: str,
) -> list[ParsedSection]:
    """Playback: expand speelplan. Partituur: document order (bladvorm)."""
    if layout == "playback" and doc.speelplan:
        return expand_speelplan(doc)
    return list(doc.sections)


def expand_speelplan(doc: ParsedDocument) -> list[ParsedSection]:
    """Ordered sections for klinkende vorm (may repeat the same section)."""
    if not doc.speelplan:
        return list(doc.sections)
    by_id = {s.id: s for s in doc.sections if s.id is not None}
    out: list[ParsedSection] = []
    for bid in doc.speelplan:
        section = by_id.get(bid)
        if section is None:
            raise KeyError(bid)
        out.append(section)
    return out


def collect_speelplan_diagnostics(doc: ParsedDocument) -> list[MvsaDiagnostic]:
    """Validate speelplan / @blok constraints on a parsed document."""
    diags: list[MvsaDiagnostic] = []
    plan = doc.speelplan
    plan_line = doc.speelplan_line or 1

    if plan is None:
        return diags

    blok_sections = [s for s in doc.sections if s.origin == "blok"]

    seen: dict[str, int] = {}
    for s in blok_sections:
        if s.id is None:
            continue
        if s.id in seen:
            diags.append(
                MvsaDiagnostic(
                    "MVSA-BLOK-DUP",
                    f"dubbele @blok-id {s.id!r} (eerder op regel {seen[s.id]})",
                    s.start_line,
                )
            )
        else:
            seen[s.id] = s.start_line

    for s in doc.sections:
        if s.origin == "blok":
            continue
        diags.append(
            MvsaDiagnostic(
                "MVSA-SPEELPLAN-ANON",
                "bestand met @speelplan: elk muzikaal segment moet via @blok "
                f"(gevonden: {s.origin or 'anonieme sectie'}"
                + (f" {s.id!r}" if s.id else "")
                + ")",
                s.start_line,
            )
        )

    for bid in plan:
        if bid not in seen:
            diags.append(
                MvsaDiagnostic(
                    "MVSA-SPEELPLAN-UNKNOWN-ID",
                    f"speelplan-id {bid!r} heeft geen @blok",
                    plan_line,
                )
            )

    used = set(plan)
    for s in blok_sections:
        if s.id and s.id not in used:
            diags.append(
                MvsaDiagnostic(
                    "MVSA-SPEELPLAN-UNUSED",
                    f"@blok {s.id!r} komt niet voor in @speelplan",
                    s.start_line,
                    severity="warning",
                )
            )

    for s in blok_sections:
        if not s.id or s.id not in used:
            continue
        for system in s.systems:
            for bundle in system.measures:
                for bar in (bundle.start_bar, bundle.final_bar):
                    if bar in _FORBIDDEN_REPEAT_BARS:
                        diags.append(
                            MvsaDiagnostic(
                                "MVSA-SPEELPLAN-REPEAT-BAR",
                                f"herhaalstreep {bar!r} mag niet in speelplan-blok "
                                f"{s.id!r} (gebruik @speelplan i.p.v. |: / :|)",
                                system.start_line,
                            )
                        )

    return diags
