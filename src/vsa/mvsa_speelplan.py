"""Speelplan / @blok helpers.

Zie ``docs/specification-mvsa/speelplan.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .mvsa_validate import BLOK_ID_RE, MvsaDiagnostic

if TYPE_CHECKING:
    from .mvsa_parse import ParsedDocument, ParsedSection

_FORBIDDEN_REPEAT_BARS = frozenset({"|:", ":|", ":||"})

NavKind = Literal[
    "identity",
    "volta_ab_ac",
    "repeat",
    "ds_al_fine",
    "ds_al_coda",
    "expand",
]


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
    """Bladmarkering-vangnet: ``Speel: 1-2-1-2-1-3`` (alleen zelden nog)."""
    return "Speel: " + "-".join(ids)


def blok_ids_in_order(doc: ParsedDocument) -> list[str]:
    return [s.id for s in doc.sections if s.origin == "blok" and s.id]


@dataclass(frozen=True)
class VoltaAbAc:
    """Bladvorm ``|: a |1..n. b :| n+1. c`` voor plan ``(a,b)×n + (a,c)``."""

    a: str
    b: str
    c: str
    n: int

    @property
    def first_ending_numbers(self) -> str:
        return ",".join(str(i) for i in range(1, self.n + 1))

    @property
    def second_ending_number(self) -> str:
        return str(self.n + 1)


@dataclass(frozen=True)
class RepeatNav:
    """``|: start … end :|`` (times≥2), optioneel gevolgd door rest van het blad."""

    start_id: str
    end_id: str
    times: int


@dataclass(frozen=True)
class DsAlFineNav:
    """Eerste doorgang tot ``ds_after``, dan terug naar segno tot Fine.

    ``use_da_capo``: segno = eerste blok → D.C. al Fine (geen segno-teken).
    """

    segno_id: str
    fine_id: str
    ds_after_id: str
    use_da_capo: bool = False


@dataclass(frozen=True)
class DsAlCodaNav:
    """Eerste doorgang tot ``ds_after``, terug naar segno tot To Coda, dan coda.

    Planvorm: ``blad[0..ds] + blad[segno..tocoda] + blad[coda..]`` met
    ``coda = blad[ds+1..]`` (minstens één coda-blok).

    ``use_da_capo``: segno = eerste blok → D.C. al Coda (geen segno-teken).
    """

    segno_id: str
    to_coda_id: str
    ds_after_id: str
    coda_id: str
    use_da_capo: bool = False


@dataclass(frozen=True)
class PartituurNav:
    """Hoe het speelplan op de partituur wordt weergegeven."""

    kind: NavKind
    volta: VoltaAbAc | None = None
    repeat: RepeatNav | None = None
    ds: DsAlFineNav | None = None
    coda: DsAlCodaNav | None = None

    @property
    def is_compact(self) -> bool:
        return self.kind not in ("expand",)


def match_volta_ab_ac(
    plan: list[str] | None,
    blok_ids: list[str],
) -> VoltaAbAc | None:
    """Herken ``(a, b)×n + (a, c)`` met precies drie bladen-blokken a,b,c."""
    if not plan or len(plan) < 4 or len(plan) % 2 != 0:
        return None
    a, b = plan[0], plan[1]
    if plan[-2] != a:
        return None
    c = plan[-1]
    if a == b or a == c or b == c:
        return None
    body = plan[:-2]
    if len(body) < 2 or len(body) % 2 != 0:
        return None
    n = len(body) // 2
    for i in range(n):
        if body[2 * i] != a or body[2 * i + 1] != b:
            return None
    if blok_ids != [a, b, c]:
        return None
    return VoltaAbAc(a=a, b=b, c=c, n=n)


def match_simple_repeat(
    plan: list[str] | None,
    blok_ids: list[str],
) -> RepeatNav | None:
    """Herken ``prefix + X×n + suffix`` (n≥2) met X aaneengesloten op het blad."""
    if not plan or len(blok_ids) < 1:
        return None
    best: RepeatNav | None = None
    best_score = (-1, -1)  # longer X, then higher n
    for start in range(len(blok_ids)):
        for end in range(start, len(blok_ids)):
            x = blok_ids[start : end + 1]
            prefix = blok_ids[:start]
            suffix = blok_ids[end + 1 :]
            if len(plan) < len(prefix) + 2 * len(x) + len(suffix):
                continue
            if plan[: len(prefix)] != prefix:
                continue
            rem = plan[len(prefix) :]
            n = 0
            while len(rem) >= len(x) and rem[: len(x)] == x:
                rem = rem[len(x) :]
                n += 1
            if n < 2 or rem != suffix:
                continue
            score = (len(x), n)
            if score > best_score:
                best_score = score
                best = RepeatNav(start_id=x[0], end_id=x[-1], times=n)
    return best


def match_ds_al_fine(
    plan: list[str] | None,
    blok_ids: list[str],
) -> DsAlFineNav | None:
    """Herken ``blad[0..ds] + blad[segno..fine]`` (één sprong terug)."""
    if not plan or len(blok_ids) < 2:
        return None
    best: DsAlFineNav | None = None
    # Prefer longer second pass, then later DS (meer van het blad in 1e doorgang).
    best_score = (-1, -1)
    for ds_after in range(len(blok_ids)):
        first = blok_ids[: ds_after + 1]
        if plan[: len(first)] != first:
            continue
        remainder = plan[len(first) :]
        if not remainder:
            continue
        for segno in range(ds_after + 1):
            for fine in range(segno, ds_after + 1):
                second = blok_ids[segno : fine + 1]
                if second != remainder:
                    continue
                score = (len(second), ds_after)
                if score > best_score:
                    best_score = score
                    best = DsAlFineNav(
                        segno_id=blok_ids[segno],
                        fine_id=blok_ids[fine],
                        ds_after_id=blok_ids[ds_after],
                        use_da_capo=(segno == 0),
                    )
    return best


def match_ds_al_coda(
    plan: list[str] | None,
    blok_ids: list[str],
) -> DsAlCodaNav | None:
    """Herken ``blad[0..ds] + blad[segno..tocoda] + blad[coda..]``.

    ``coda`` is altijd het restant van het blad na ``ds`` (minstens één blok).
    Disjunct van D.S. al Fine: die herhaalt alleen binnen ``[0..ds]``.
    """
    if not plan or len(blok_ids) < 3:
        return None
    best: DsAlCodaNav | None = None
    # Prefer longer second pass (segno..tocoda), then later DS, then longer coda.
    best_score = (-1, -1, -1)
    for ds_after in range(len(blok_ids) - 1):
        first = blok_ids[: ds_after + 1]
        coda = blok_ids[ds_after + 1 :]
        if not coda:
            continue
        if plan[: len(first)] != first:
            continue
        remainder = plan[len(first) :]
        if len(remainder) <= len(coda):
            continue
        if remainder[-len(coda) :] != coda:
            continue
        mid = remainder[: -len(coda)]
        if not mid:
            continue
        for segno in range(ds_after + 1):
            # To Coda strikt vóór D.S.-blok (klassiek blad; geen mark-botsing).
            for to_coda in range(segno, ds_after):
                second = blok_ids[segno : to_coda + 1]
                if second != mid:
                    continue
                score = (len(second), ds_after, len(coda))
                if score > best_score:
                    best_score = score
                    best = DsAlCodaNav(
                        segno_id=blok_ids[segno],
                        to_coda_id=blok_ids[to_coda],
                        ds_after_id=blok_ids[ds_after],
                        coda_id=coda[0],
                        use_da_capo=(segno == 0),
                    )
    return best


def plan_partituur_navigation(doc: ParsedDocument) -> PartituurNav | None:
    """Kies compacte bladvorm-navigatie, of ``expand`` als vangnet.

    Geen speelplan → ``None`` (geen navigatie).
    """
    plan = doc.speelplan
    if not plan:
        return None
    ids = blok_ids_in_order(doc)
    if plan == ids:
        return PartituurNav("identity")
    volta = match_volta_ab_ac(plan, ids)
    if volta is not None:
        return PartituurNav("volta_ab_ac", volta=volta)
    repeat = match_simple_repeat(plan, ids)
    if repeat is not None:
        return PartituurNav("repeat", repeat=repeat)
    ds = match_ds_al_fine(plan, ids)
    if ds is not None:
        return PartituurNav("ds_al_fine", ds=ds)
    coda = match_ds_al_coda(plan, ids)
    if coda is not None:
        return PartituurNav("ds_al_coda", coda=coda)
    return PartituurNav("expand")


def volta_for_document(doc: ParsedDocument) -> VoltaAbAc | None:
    """Backwards-compat: alleen volta-patroon, anders None."""
    nav = plan_partituur_navigation(doc)
    if nav and nav.kind == "volta_ab_ac":
        return nav.volta
    return None


def sections_for_layout(
    doc: ParsedDocument,
    *,
    layout: str,
) -> list[ParsedSection]:
    """Playback: altijd expansie. Partituur: compact tenzij navigatie = expand."""
    if not doc.speelplan:
        return list(doc.sections)
    if layout == "playback":
        return expand_speelplan(doc)
    if layout == "partituur":
        nav = plan_partituur_navigation(doc)
        if nav is not None and nav.kind == "expand":
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
