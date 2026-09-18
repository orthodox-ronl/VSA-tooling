from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from vsa.ast import Document, HeightMarkerNode, PitchMarkerNode
from vsa.pitch_resolver import ehm_to_motion


def _degree_of_ehm(ehm: str) -> int:
    """Laddergraad-delta van één EHM (accidens-prefix telt niet mee)."""
    steps, _chromatic = ehm_to_motion(ehm)
    return steps


def _degree_of_ehm_list(ehm_list: list[str]) -> int:
    """Cumulatieve laddergraad-delta van een lijst EHM-waarden."""
    return sum(_degree_of_ehm(e) for e in ehm_list)


# Backwards-compatible aliases (degree-only; no float ½-tone cursor).
_pitch_of_ehm = _degree_of_ehm
_pitch_of_ehm_list = _degree_of_ehm_list


def _format_pitch_delta(delta: float) -> str:
    if delta == int(delta):
        return str(int(delta))
    return str(delta)


def height_marker_mismatch_detail(declared: float, computed: float) -> str:
    """Compacte diagnostische tekst: computed = marker ± N."""
    delta = computed - declared
    if delta == 0:
        return "computed = marker"
    sign = "+" if delta > 0 else "-"
    return f"computed = marker {sign} {_format_pitch_delta(abs(delta))}"


def _marker_for_degree(degree: int) -> str:
    """Canonieke hoogte-markeringsstring voor een diatonische laddergraad.

    Voorbeelden: 0 → '[:]', 2 → '[//:]', -1 → '[\\:]'.
    Accidens-prefixen horen niet in de canonieke marker: zij wijzigen alleen
    de klinkende toon van een EHM, niet de cursor die markeringen controleren.
    """
    if degree == 0:
        return "[:]"
    backslash = "\\"
    if degree > 0:
        return f"[{'/' * degree}:]"
    return f"[{backslash * abs(degree)}:]"


# Alias used by older call sites / tests.
_marker_for_pitch = _marker_for_degree


HeightMarkerRole = Literal["start_height", "local_height"]


@dataclass(frozen=True)
class HeightMarkerRef:
    node: PitchMarkerNode
    index: int
    role: HeightMarkerRole

    @property
    def height_modifier(self) -> list[str]:
        return self.node.height_modifier or []

    @property
    def ehm(self) -> list[str]:
        return self.height_modifier

    @property
    def is_start_marker(self) -> bool:
        return self.role == "start_height"

    @property
    def is_local_marker(self) -> bool:
        return self.role == "local_height"


HeightMarkerInfo = HeightMarkerRef


def is_height_marker_node(node: object) -> bool:
    return isinstance(node, HeightMarkerNode)


def height_marker_refs(document: Document) -> list[HeightMarkerRef]:
    refs: list[HeightMarkerRef] = []

    for index, node in enumerate(document.nodes):
        if is_height_marker_node(node):
            role: HeightMarkerRole = "start_height" if not refs else "local_height"
            refs.append(HeightMarkerRef(node=node, index=index, role=role))

    return refs


def height_marker_nodes(document: Document) -> list[PitchMarkerNode]:
    return [ref.node for ref in height_marker_refs(document)]


def height_markers(document: Document) -> list[HeightMarkerRef]:
    return height_marker_refs(document)


def iter_height_markers(document: Document):
    yield from height_marker_refs(document)


def first_height_marker(document: Document) -> HeightMarkerRef | None:
    refs = height_marker_refs(document)
    return refs[0] if refs else None


def last_height_marker(document: Document) -> HeightMarkerRef | None:
    refs = height_marker_refs(document)
    return refs[-1] if refs else None


def local_height_markers(document: Document) -> list[HeightMarkerRef]:
    return [ref for ref in height_marker_refs(document) if ref.role == "local_height"]
