"""Kuiser Q1 — YAML-frontmatter (docs/formats/kuiser.md).

``@``-blok wint voor titel/do/mode/tempo (na Q2). Zoektekst uit L-body
via :mod:`vsa.zoektekst`. Catalogus: alleen gevulde sleutels.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .mvsa_vsa import _soort_toon_from_source_name
from .yaml_frontmatter import strip_yaml_frontmatter
from .zoektekst import (
    LiteralZoektekst,
    _ZoektekstDumper,
    expected_zoektekst,
    format_zoektekst,
    normalize_zoektekst,
)

# Voorkeursvolgorde (bibliotheek vsa-frontmatter); overige sleutels erna.
_KEY_ORDER = (
    "titel",
    "taal",
    "soort",
    "toon",
    "formule",
    "template",
    "template_opgegeven",
    "partituur",
    "bron",
    "gelegenheid",
    "zoektekst",
    "do",
    "mode",
    "tempo",
)

_AT_LINE = re.compile(
    r"^@(?P<name>[A-Za-z][A-Za-z0-9_-]*)\s*(?P<rest>.*)$"
)
_TITLE_QUOTED = re.compile(r'^"(.*)"\s*$')


def apply_q1(
    text: str,
    *,
    source_path: Path | str | None = None,
) -> str:
    """Schrijf/vul minimale YAML-FM; sync vanaf document-``@``-blok."""
    bom = ""
    if text.startswith("\ufeff"):
        bom = "\ufeff"
        text = text[1:]

    old_fm, body, _ = strip_yaml_frontmatter(text)
    at = _parse_doc_at_block(body)
    soort, toon = _resolve_soort_toon(old_fm, source_path)

    new_fm: dict[str, Any] = {
        k: v
        for k, v in old_fm.items()
        if k
        not in {
            "titel",
            "title",
            "taal",
            "soort",
            "toon",
            "zoektekst",
            "do",
            "mode",
            "tempo",
            "bron",
        }
        and v is not None
        and v != ""
        and v != {}
        and v != []
    }

    title = at.get("title") or _fm_title(old_fm)
    if title:
        new_fm["titel"] = title

    taal = _resolve_taal(at, old_fm, body)
    new_fm["taal"] = taal

    if soort:
        new_fm["soort"] = soort
    if toon is not None:
        new_fm["toon"] = toon

    bron = _merge_bron(old_fm.get("bron"), source_path)
    if bron:
        new_fm["bron"] = bron

    zt = expected_zoektekst(text, kind="mvsa")
    if zt:
        new_fm["zoektekst"] = LiteralZoektekst(zt)

    if at.get("do"):
        new_fm["do"] = at["do"]
    if at.get("mode"):
        new_fm["mode"] = at["mode"]
    if at.get("tempo") is not None:
        new_fm["tempo"] = at["tempo"]

    ordered = _order_meta(new_fm)
    if not ordered:
        return bom + body

    # Idempotent: geen churn als inhoud gelijk is (genormaliseerde zoektekst).
    if old_fm and _fm_equivalent(old_fm, ordered):
        return bom + text

    return bom + _dump_fm(ordered) + body


def _fm_equivalent(old: dict[str, Any], new: dict[str, Any]) -> bool:
    """Vergelijk canonieke sleutels; zoektekst genormaliseerd."""
    keys = set(old) | set(new)
    for key in keys:
        ov = old.get(key)
        nv = new.get(key)
        if key == "zoektekst":
            o_norm = (
                None
                if ov is None
                else normalize_zoektekst(format_zoektekst(str(ov)))
            )
            n_norm = (
                None
                if nv is None
                else normalize_zoektekst(format_zoektekst(str(nv)))
            )
            if o_norm != n_norm:
                return False
            continue
        if ov != nv:
            return False
    return True


def _dump_fm(meta: dict[str, Any]) -> str:
    dumped = yaml.dump(
        meta,
        Dumper=_ZoektekstDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=88,
    )
    if not dumped.endswith("\n"):
        dumped += "\n"
    return f"---\n{dumped}---\n\n"


def _order_meta(meta: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in _KEY_ORDER:
        if key in meta:
            out[key] = meta[key]
    for key, val in meta.items():
        if key not in out:
            out[key] = val
    return out


def _parse_doc_at_block(body: str) -> dict[str, Any]:
    """Eerste document-``@title/@do/@mode/@tempo/@taal`` vóór LSATB."""
    from .mvsa_validate import parse_regelidentifier

    found: dict[str, Any] = {}
    for raw in body.splitlines():
        line = raw.strip()
        if parse_regelidentifier(line.lstrip() if line else ""):
            break
        m = _AT_LINE.match(line)
        if not m:
            continue
        name = m.group("name").lower()
        rest = m.group("rest").strip()
        if name == "title":
            qm = _TITLE_QUOTED.match(rest)
            found["title"] = qm.group(1) if qm else rest
        elif name == "do":
            found["do"] = rest
        elif name == "mode":
            found["mode"] = rest
        elif name == "taal":
            # @taal "nl" or @taal nl
            qm = _TITLE_QUOTED.match(rest)
            found["taal"] = (qm.group(1) if qm else rest).strip()
        elif name == "tempo":
            from .mvsa_validate import parse_tempo_argument

            parsed = parse_tempo_argument(rest)
            if parsed is not None:
                found["tempo"] = parsed[0]
    return found


def _fm_title(fm: dict[str, Any]) -> str | None:
    for key in ("titel", "title"):
        val = fm.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    part = fm.get("partituur")
    if isinstance(part, dict):
        for key in ("title", "titel"):
            val = part.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return None


def _resolve_taal(at: dict[str, Any], fm: dict[str, Any], body: str) -> str:
    if isinstance(at.get("taal"), str) and at["taal"].strip():
        return at["taal"].strip()
    val = fm.get("taal")
    if isinstance(val, str) and val.strip():
        return val.strip()
    # @taal later in body (sticky) — scan whole body once.
    for raw in body.splitlines():
        m = _AT_LINE.match(raw.strip())
        if m and m.group("name").lower() == "taal":
            rest = m.group("rest").strip()
            qm = _TITLE_QUOTED.match(rest)
            return (qm.group(1) if qm else rest).strip() or "nl"
    return "nl"


def _resolve_soort_toon(
    fm: dict[str, Any], source_path: Path | str | None
) -> tuple[str | None, int | None]:
    soort = fm.get("soort") if isinstance(fm.get("soort"), str) else None
    toon_raw = fm.get("toon")
    toon: int | None = None
    if isinstance(toon_raw, int) and 1 <= toon_raw <= 8:
        toon = toon_raw
    elif isinstance(toon_raw, str) and toon_raw.strip().isdigit():
        n = int(toon_raw.strip())
        if 1 <= n <= 8:
            toon = n
    if source_path is not None:
        derived = _soort_toon_from_source_name(str(source_path))
        if soort is None:
            soort = derived.get("soort")
        if toon is None and isinstance(derived.get("toon"), int):
            toon = derived["toon"]
        if soort is None:
            # Fallback: ``alleluia-toon-8-…`` e.d. (niet in VSA-prefixlijst).
            stem = Path(source_path).stem.lower()
            m = re.match(r"^([a-z0-9]+)-toon-[1-8](?:-|$)", stem)
            if m:
                soort = m.group(1)
    return soort, toon


def _merge_bron(
    existing: Any, source_path: Path | str | None
) -> dict[str, str] | None:
    bron: dict[str, str] = {}
    if isinstance(existing, dict):
        for key in ("uitgangspunt", "bewerking"):
            val = existing.get(key)
            if isinstance(val, str) and val.strip():
                bron[key] = val.strip()
        # Bewaar overige bron-velden.
        for key, val in existing.items():
            if key not in bron and val not in (None, "", {}, []):
                if isinstance(val, str):
                    bron[key] = val
    bewerking = _bewerking_from_path(source_path)
    if bewerking and "bewerking" not in bron:
        bron["bewerking"] = bewerking
    return bron or None


def _bewerking_from_path(source_path: Path | str | None) -> str | None:
    if source_path is None:
        return None
    stem = Path(source_path).name
    for suf in (".mvsa", ".vsa", ".mscz", ".mxl"):
        if stem.lower().endswith(suf):
            stem = stem[: -len(suf)]
            break
    m = re.search(r"-toon-[1-8]-(.+)$", stem, re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip().lower() or None
