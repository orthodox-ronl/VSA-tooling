"""Library-resolutie voor VSA-templates (T0/T1): id, alias, same_as.

Nieuwe formules: map ``library/<id>/template.yaml`` met id
``{soort}-toon-{n}-{bron}``. Aliassen staan in ``library/aliases.yaml``
(+ eventuele ingebouwde fallbacks). Keuze zonder ``--template``: zie
``select_template_id`` (soort+toon; geen stille default).
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


def _parse_toon(toon: int | str | None) -> int | None:
    if toon is None or str(toon).strip() == "":
        return None
    try:
        n = int(toon)
    except (TypeError, ValueError):
        return None
    if 1 <= n <= 8:
        return n
    return None


def _soort_from_stem(stem: str) -> str | None:
    lower = stem.lower()
    for prefix in ("kondak", "tropaar", "stichier", "vers", "prokimen"):
        if lower.startswith(prefix + "-") or lower.startswith(prefix + "_"):
            return prefix
    return None


def _bron_from_path(path: Path | str | None) -> str | None:
    """Bron uit bestandsnaam-suffix of mapdeel (catalogus-leaf / formule-map)."""
    if path is None:
        return None
    p = Path(path)
    from_stem = _bron_from_stem(p.stem)
    if from_stem:
        return from_stem
    for part in reversed(p.parts):
        low = part.lower()
        parsed = formula_id_parts(low)
        if parsed[2]:
            return _normalize_bron(parsed[2]) or parsed[2]
        norm = _normalize_bron(low)
        if norm:
            return norm
        if low in _BRON_SUFFIXES:
            return "hemelum" if low == "liturgikon" else low
    return None


def list_templates_for_soort_toon(
    soort: str,
    toon: int | str,
    *,
    library_root: Path | None = None,
) -> list[str]:
    """Canonieke library-ids die bij ``{soort}-toon-{n}`` horen (T1).

    Inclusief ids die alleen via ``aliases.yaml`` bereikbaar zijn
    (bijv. ``kondak-toon-4-hemelum`` → ``tropaar-toon-4-hemelum``).
    Tropaar↔kondak: als er voor de gevraagde soort geen map is, ook de
    andere soort meenemen wanneer die via alias/`same_as` de formule dekt.
    """
    root = library_root or default_library_root()
    soort_s = (soort or "").strip().lower()
    tone = _parse_toon(toon)
    if not soort_s or tone is None:
        return []

    known = set(list_template_ids(root))
    aliases = template_aliases(root)
    prefix = f"{soort_s}-toon-{tone}"
    found: set[str] = set()

    def _add_resolved(name: str) -> None:
        rid = resolve_template_id(name, library_root=root)
        if (root / rid / "template.yaml").is_file():
            found.add(rid)
        elif rid in known:
            found.add(rid)

    for tid in known:
        if tid == prefix or tid.startswith(prefix + "-"):
            found.add(tid)

    for alias, _target in aliases.items():
        if alias == prefix or alias.startswith(prefix + "-"):
            _add_resolved(alias)

    # Korte alias zonder bron: ``kondak-toon-5``
    _add_resolved(prefix)

    if not found and soort_s in ("tropaar", "kondak"):
        other = "kondak" if soort_s == "tropaar" else "tropaar"
        return list_templates_for_soort_toon(
            other, tone, library_root=root
        )

    return sorted(found)


def _candidate_matches_hint(hint: str, candidates: list[str], *, library_root: Path) -> str | None:
    """Als ``hint`` (alias of id) bij precies één kandidaat hoort → die id."""
    raw = hint.strip()
    if not raw:
        return None
    if raw in candidates:
        return raw
    resolved = resolve_template_id(raw, library_root=library_root)
    hits = [c for c in candidates if c == resolved or c == raw]
    if len(hits) == 1:
        return hits[0]
    # Hint is alias naar een kandidaat
    if resolved in candidates:
        return resolved
    return None


def _template_hint_from_existing_mvsa(path: Path | None) -> str | None:
    """Lees ``template_opgegeven`` (voorkeur) of ``template`` uit bestaande MVSA."""
    if path is None or not path.is_file() or path.suffix.lower() != ".mvsa":
        return None
    try:
        from .yaml_frontmatter import parse_vsa_frontmatter

        meta, _ = parse_vsa_frontmatter(path.read_text(encoding="utf-8"))
    except OSError:
        return None
    asked = meta.get("template_opgegeven")
    if asked not in (None, ""):
        return str(asked).strip()
    tpl = meta.get("template")
    if tpl not in (None, ""):
        return str(tpl).strip()
    return None


def select_template_id(
    *,
    soort: str | None = None,
    toon: int | str | None = None,
    formule: str | None = None,
    bron: str | None = None,
    path: Path | str | None = None,
    output: Path | str | None = None,
    library_root: Path | None = None,
    explicit: str | None = None,
) -> str:
    """Kies template-id voor ``vsa mvsa`` (T1).

    * ``explicit`` (CLI ``--template``) wint altijd.
    * Anders: kandidaten uit **formulekeuze** + ``toon``:
      - ``formule`` in de VSA = melodieformule (genre of volledige id),
        los van liturgische ``soort`` (bijv. kondak met stichiermelodie);
      - zonder ``formule``: liturgische ``soort`` + ``toon``.
    * 0 kandidaten → harde fout; 1 → die gebruiken.
    * Meerdere: bestaande uitvoer-``.mvsa`` (``template_opgegeven`` /
      ``template``), anders bron uit leaf/pad/meta, anders harde fout.
    """
    root = library_root or default_library_root()
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip()

    path_p = Path(path) if path else None
    out_p = Path(output) if output else None
    stem = path_p.stem if path_p else ""

    formule_s = (formule or "").strip().lower() or None
    # Volledige library-id / alias als formule → direct die gebruiken
    # (mits die bestaat), zonder soort-lookup.
    if formule_s and (
        (root / formule_s / "template.yaml").is_file()
        or formule_s in template_aliases(root)
    ):
        return resolve_template_id(formule_s, library_root=root)

    soort_s = (soort or "").strip().lower() or None
    if not soort_s and stem:
        soort_s = _soort_from_stem(stem)

    # formule: stichier → zoek stichier-toon-N-…; soort blijft liturgisch.
    lookup_soort = formule_s or soort_s

    tone = _parse_toon(toon)
    if tone is None and stem:
        m = re.search(r"toon-([1-8])", stem.lower())
        if m:
            tone = int(m.group(1))

    if not lookup_soort or tone is None:
        raise TemplateLibraryError(
            "vsa mvsa vereist soort en toon in de .vsa-frontmatter "
            "(of --template). Optioneel formule: voor een andere "
            "melodieformule dan soort. Zie vsa-mvsa-contract.md T1.",
            code="TEMPLATE-SELECT-META",
        )

    candidates = list_templates_for_soort_toon(
        lookup_soort, tone, library_root=root
    )
    if not candidates:
        label = (
            f"formule={formule_s!r}"
            if formule_s
            else f"soort={soort_s!r}"
        )
        raise TemplateLibraryError(
            f"geen template voor {label} toon={tone}. "
            f"Voeg library/{lookup_soort}-toon-{tone}-… toe, zet "
            f"formule: op een bestaande formule-soort/id, of geef "
            f"--template. Bekend: {', '.join(list_template_ids(root)) or '(geen)'}",
            code="TEMPLATE-SELECT-MISSING",
        )
    if len(candidates) == 1:
        return candidates[0]

    # Meerdere formules (vaak …-groningen én …-hemelum).
    existing_hint = _template_hint_from_existing_mvsa(out_p)
    if existing_hint:
        hit = _candidate_matches_hint(
            existing_hint, candidates, library_root=root
        )
        if hit:
            # Behoud de opgegeven string (alias) voor template_opgegeven.
            return existing_hint
        raise TemplateLibraryError(
            f"bestaande MVSA noemt template {existing_hint!r}, maar die "
            f"hoort niet bij soort={soort_s!r} toon={tone}. "
            f"Kandidaten: {', '.join(candidates)}",
            code="TEMPLATE-SELECT-EXISTING-MISMATCH",
        )

    bron_s = (
        _bron_from_path(out_p)
        or _bron_from_path(path_p)
        or _normalize_bron(bron)
    )
    if bron_s:
        bron_hits = [
            c
            for c in candidates
            if formula_id_parts(c)[2] == bron_s
            or c.endswith(f"-{bron_s}")
        ]
        # liturgikon-alias → hemelum
        if bron_s == "hemelum" and not bron_hits:
            bron_hits = [
                c
                for c in candidates
                if formula_id_parts(c)[2] in ("hemelum", "liturgikon")
            ]
        if len(bron_hits) == 1:
            return bron_hits[0]
        if len(bron_hits) > 1:
            candidates = bron_hits

    label = (
        f"formule={formule_s!r}"
        if formule_s
        else f"soort={soort_s!r}"
    )
    raise TemplateLibraryError(
        f"meerdere templates voor {label} toon={tone}: "
        f"{', '.join(candidates)}. Geef --template, of regenereer een "
        f"bestaande .mvsa (dan geldt template/template_opgegeven uit die "
        f"frontmatter).",
        code="TEMPLATE-SELECT-AMBIGUOUS",
    )


def infer_template_id(
    *,
    soort: str | None = None,
    toon: int | str | None = None,
    formule: str | None = None,
    bron: str | None = None,
    path: Path | str | None = None,
    library_root: Path | None = None,
    output: Path | str | None = None,
) -> str:
    """Compat-wrapper: zelfde regels als :func:`select_template_id` (T1)."""
    return select_template_id(
        soort=soort,
        toon=toon,
        formule=formule,
        bron=bron,
        path=path,
        output=output,
        library_root=library_root,
    )


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
