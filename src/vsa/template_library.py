"""Library-resolutie voor VSA-templates (T0/T1): id, alias, same_as.

Nieuwe formules: map ``library/<id>/template.yaml`` met id
``{soort}-toon-{n}-{bron}``. Aliassen staan in ``library/aliases.yaml``
(+ eventuele ingebouwde fallbacks). Defaultkeuze: zie
``infer_template_id``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# Canonieke default als er niets af te leiden is (Hemelum tropaar/kondak 4).
DEFAULT_TEMPLATE_ID = "tropaar-toon-4-hemelum"

# Schrijfoctaven die bij tropaar/kondak-corpus horen (T5 emit / MXL).
# A=0: alt do=F4 wordt ``f``, niet ``f+`` (anders F5 in Coria).
DEFAULT_VOICE_OCT: dict[str, int] = {"S": 0, "A": 0, "T": -1, "B": -1}
DEFAULT_OCT_LINE = "@oct S=0 A=0 T=-1 B=-1"

# Standaardtempo voor tropaar/kondak-stukken (hoort in het stuk, niet in YAML).
DEFAULT_TEMPO_TROPAAR_KONDAK = 180

_BRON_SUFFIXES = ("hemelum", "liturgikon", "groningen", "asten", "pdf")

# Ingebouwde aliassen als aliases.yaml ontbreekt (tests/minimal).
_BUILTIN_ALIASES: dict[str, str] = {
    "hemelum-tropaar-toon-4": "tropaar-toon-4-hemelum",
    "hemelum-toon-4": "tropaar-toon-4-hemelum",
    "tropaar-toon-4": "tropaar-toon-4-hemelum",
}


def __getattr__(name: str) -> Any:
    """Back-compat: ``TEMPLATE_ALIASES`` → ``template_aliases()``."""
    if name == "TEMPLATE_ALIASES":
        return template_aliases()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
    # Exacte string vóór alias-resolutie (``None`` = default/leeg).
    requested_raw: str | None = None


def default_library_root() -> Path:
    """``docs/specification-vsa-templates/library`` t.o.v. de package-root."""
    return (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "specification-vsa-templates"
        / "library"
    )


@lru_cache(maxsize=4)
def _load_aliases_map(library_root_str: str) -> dict[str, str]:
    root = Path(library_root_str)
    path = root / "aliases.yaml"
    out = dict(_BUILTIN_ALIASES)
    if not path.is_file():
        return out
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    block = raw.get("aliases") if isinstance(raw, dict) else None
    if isinstance(block, dict):
        for k, v in block.items():
            if k is None or v is None:
                continue
            out[str(k).strip()] = str(v).strip()
    return out


def clear_alias_cache() -> None:
    """Tests: cache legen na schrijven van aliases.yaml."""
    _load_aliases_map.cache_clear()


def template_aliases(library_root: Path | None = None) -> dict[str, str]:
    root = library_root or default_library_root()
    return dict(_load_aliases_map(str(root.resolve())))


def resolve_template_id(
    name: str | None,
    *,
    library_root: Path | None = None,
) -> str:
    """Alias → canonieke id; ``None``/leeg → default Hemelum toon 4."""
    if name is None or not str(name).strip():
        return DEFAULT_TEMPLATE_ID
    key = str(name).strip()
    aliases = template_aliases(library_root)
    # Meerdere hops (oud → tussenschakel → canoniek).
    seen: set[str] = set()
    while key in aliases and key not in seen:
        seen.add(key)
        key = aliases[key]
    return key


def list_template_ids(library_root: Path | None = None) -> list[str]:
    root = library_root or default_library_root()
    if not root.is_dir():
        return []
    return sorted(
        p.parent.name
        for p in root.glob("*/template.yaml")
        if p.is_file()
    )


def formula_id_parts(template_id: str) -> tuple[str | None, int | None, str | None]:
    """Parse ``{soort}-toon-{n}-{bron}`` → (soort, toon, bron)."""
    m = re.fullmatch(
        r"([a-z0-9-]+)-toon-([1-8])(?:-([a-z0-9-]+))?",
        template_id.strip(),
    )
    if not m:
        return None, None, None
    return m.group(1), int(m.group(2)), m.group(3)


def _bron_from_stem(stem: str) -> str | None:
    lower = stem.lower()
    for bron in _BRON_SUFFIXES:
        if lower.endswith(f"-{bron}") or f"-{bron}-" in lower:
            return "hemelum" if bron == "liturgikon" else bron
    return None


def _normalize_bron(value: str | None) -> str | None:
    """Haal bron-token uit vrije tekst (``Koormap Hemelum``, ``liturgikon``, …)."""
    if value is None or not str(value).strip():
        return None
    lower = str(value).strip().lower()
    if lower == "liturgikon" or "liturgikon" in lower:
        return "hemelum"
    for bron in _BRON_SUFFIXES:
        if bron == "liturgikon":
            continue
        if lower == bron or lower.endswith(f"-{bron}") or f" {bron}" in f" {lower}":
            return bron
    return None


def infer_template_id(
    *,
    soort: str | None = None,
    toon: int | str | None = None,
    bron: str | None = None,
    path: Path | str | None = None,
    library_root: Path | None = None,
) -> str:
    """Leid een formule-id af uit meta/pad; fallback Groningen; anders default.

    Liturgikon telt als Hemelum. Bestandsnaam-suffix wint op vrije
    ``bron.uitgangspunt``-tekst. Ontbrekende bron-specifieke map →
    ``…-groningen`` als die bestaat.
    """
    root = library_root or default_library_root()
    stem = Path(path).stem if path else ""
    soort_s = (soort or "").strip().lower() or None
    # Pad-suffix eerst (klaar-bestanden heten …-hemelum.mvsa).
    bron_s = _bron_from_stem(stem) or _normalize_bron(bron)
    if not soort_s and stem:
        for prefix in (
            "kondak",
            "tropaar",
            "stichier",
            "vers",
        ):
            if stem.lower().startswith(prefix + "-") or stem.lower().startswith(
                prefix + "_"
            ):
                soort_s = prefix
                break

    tone: int | None = None
    if toon is not None and str(toon).strip() != "":
        try:
            tone = int(toon)
        except (TypeError, ValueError):
            tone = None
    if tone is None and stem:
        m = re.search(r"toon-([1-8])", stem.lower())
        if m:
            tone = int(m.group(1))

    if not soort_s or tone is None:
        return resolve_template_id(DEFAULT_TEMPLATE_ID, library_root=root)

    bron_try = bron_s or "groningen"
    candidates = [
        f"{soort_s}-toon-{tone}-{bron_try}",
    ]
    if bron_try == "hemelum":
        candidates.append(f"{soort_s}-toon-{tone}-liturgikon")
    # Soort-wissel tropaar↔kondak (zelfde formule via same_as/alias).
    other = "kondak" if soort_s == "tropaar" else (
        "tropaar" if soort_s == "kondak" else None
    )
    if other:
        candidates.append(f"{other}-toon-{tone}-{bron_try}")
    # Groningen-fallback
    if bron_try != "groningen":
        candidates.append(f"{soort_s}-toon-{tone}-groningen")
        if other:
            candidates.append(f"{other}-toon-{tone}-groningen")

    known = set(list_template_ids(root))
    aliases = template_aliases(root)
    for cand in candidates:
        resolved = resolve_template_id(cand, library_root=root)
        if resolved in known or cand in known:
            return resolved if resolved in known else cand
        # Alias naar iets dat bestaat
        if resolved in aliases.values() or resolved in known:
            if (root / resolved / "template.yaml").is_file():
                return resolved

    # Laatste poging: bestaand pad na alias
    for cand in candidates:
        rid = resolve_template_id(cand, library_root=root)
        if (root / rid / "template.yaml").is_file():
            return rid

    return resolve_template_id(DEFAULT_TEMPLATE_ID, library_root=root)


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

    ``requested_raw``: exacte invoer vóór alias. ``canonical_id``: map na
    alias. ``formula_id``: YAML met frasen (na ``same_as``).
    """
    root = library_root or default_library_root()
    if not root.is_dir():
        raise TemplateLibraryError(
            f"library-map ontbreekt: {root}",
            code="TEMPLATE-LIBRARY-ROOT",
        )

    raw = None if name is None or not str(name).strip() else str(name).strip()
    requested = resolve_template_id(name, library_root=root)
    path = root / requested / "template.yaml"
    if not path.is_file():
        known = ", ".join(list_template_ids(root)) or "(geen)"
        raise TemplateLibraryError(
            f"onbekend template-id {requested!r}. Bekend: {known}",
            code="TEMPLATE-LIBRARY-UNKNOWN",
        )

    doc = _load_yaml(path)
    seen: set[str] = {requested}
    formula_path = path
    formula_doc = dict(doc)
    formula_id = requested

    while "same_as" in formula_doc:
        target = resolve_template_id(
            str(formula_doc["same_as"]), library_root=root
        )
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
        requested_raw=raw,
    )
