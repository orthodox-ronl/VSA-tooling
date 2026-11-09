"""Library-resolutie voor VSA-templates (T0/T1): id, alias, same_as.

Nieuwe formules: map ``library/<id>/template.yaml``. Aliassen en
``same_as`` (tropaar = kondak-formule) horen hier, niet in de CLI.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Canonieke default (playbook): Hemelum tropaar/kondak toon 4.
DEFAULT_TEMPLATE_ID = "tropaar-toon-4"

# Playbook-/mensnamen → canonieke library-id (mapnaam = id).
TEMPLATE_ALIASES: dict[str, str] = {
    "hemelum-tropaar-toon-4": "tropaar-toon-4",
    "hemelum-toon-4": "tropaar-toon-4",
}

# Schrijfoctaven die bij tropaar/kondak-corpus horen (T5 emit / MXL).
# A=0: alt do=F4 wordt ``f``, niet ``f+`` (anders F5 in Coria).
DEFAULT_VOICE_OCT: dict[str, int] = {"S": 0, "A": 0, "T": -1, "B": -1}
DEFAULT_OCT_LINE = "@oct S=0 A=0 T=-1 B=-1"

# Standaardtempo voor tropaar/kondak-stukken (hoort in het stuk, niet in YAML).
DEFAULT_TEMPO_TROPAAR_KONDAK = 180


class TemplateLibraryError(Exception):
    """Onbekend template-id, ontbrekende map, of same_as-ketenfout."""

    def __init__(self, message: str, *, code: str = "TEMPLATE-LIBRARY") -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class ResolvedTemplate:
    """Geladen formule klaar voor ``map_vsa_to_template``."""

    requested_id: str
    canonical_id: str
    formula_id: str
    path: Path
    formula_path: Path
    doc: dict[str, Any]


def default_library_root() -> Path:
    """``docs/specification-vsa-templates/library`` t.o.v. de package-root."""
    # src/vsa/template_library.py → repo-root = parents[2]
    return (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "specification-vsa-templates"
        / "library"
    )


def resolve_template_id(name: str | None) -> str:
    """Alias → canonieke id; ``None``/leeg → default Hemelum toon 4."""
    if name is None or not str(name).strip():
        return DEFAULT_TEMPLATE_ID
    key = str(name).strip()
    return TEMPLATE_ALIASES.get(key, key)


def list_template_ids(library_root: Path | None = None) -> list[str]:
    root = library_root or default_library_root()
    if not root.is_dir():
        return []
    ids = sorted(
        p.parent.name
        for p in root.glob("*/template.yaml")
        if p.is_file()
    )
    return ids


def _load_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TemplateLibraryError(
            f"template.yaml is geen mapping: {path}",
            code="TEMPLATE-LIBRARY-YAML",
        )
    return raw


def load_resolved_template(
    name: str | None = None,
    *,
    library_root: Path | None = None,
) -> ResolvedTemplate:
    """Laad template; volg ``same_as`` tot een formule met ``phrases``.

    ``requested_id`` / ``canonical_id`` blijven wat de gebruiker vroeg
    (na alias). ``formula_id`` is de YAML met de echte frasen (T1: beide
    noemen in emit-commentaar).
    """
    root = library_root or default_library_root()
    if not root.is_dir():
        raise TemplateLibraryError(
            f"library-map ontbreekt: {root}",
            code="TEMPLATE-LIBRARY-ROOT",
        )

    requested = resolve_template_id(name)
    path = root / requested / "template.yaml"
    if not path.is_file():
        known = ", ".join(list_template_ids(root)) or "(geen)"
        raise TemplateLibraryError(
            f"onbekend template-id {requested!r}. Bekend: {known}",
            code="TEMPLATE-LIBRARY-UNKNOWN",
        )

    doc = _load_yaml(path)
    yaml_id = str(doc.get("id") or requested)
    if yaml_id != requested:
        # Mapnaam wint voor CLI-resolutie; waarschuw via formula meta.
        pass

    seen: set[str] = {requested}
    formula_path = path
    formula_doc = dict(doc)
    formula_id = requested

    while "same_as" in formula_doc:
        target = str(formula_doc["same_as"])
        if target in seen:
            raise TemplateLibraryError(
                f"same_as-cyclus bij {requested!r}: {' → '.join(seen)} → {target}",
                code="TEMPLATE-LIBRARY-SAME-AS-CYCLE",
            )
        seen.add(target)
        formula_path = root / target / "template.yaml"
        if not formula_path.is_file():
            raise TemplateLibraryError(
                f"same_as {target!r} van {formula_id!r} bestaat niet onder {root}",
                code="TEMPLATE-LIBRARY-SAME-AS-MISSING",
            )
        formula_doc = _load_yaml(formula_path)
        formula_id = str(formula_doc.get("id") or target)
        if "same_as" in formula_doc:
            continue
        break

    if "phrases" not in formula_doc:
        raise TemplateLibraryError(
            f"formule {formula_id!r} heeft geen phrases (na same_as vanaf {requested!r})",
            code="TEMPLATE-LIBRARY-NO-PHRASES",
        )

    # Mapping gebruikt frasen/cycle van de formule; metadata-id blijft gevraagd.
    merged = dict(formula_doc)
    merged["id"] = requested
    if formula_id != requested:
        merged["_formula_id"] = formula_id
        merged["_same_as_resolved"] = formula_id

    return ResolvedTemplate(
        requested_id=requested,
        canonical_id=requested,
        formula_id=formula_id,
        path=path,
        formula_path=formula_path,
        doc=merged,
    )
