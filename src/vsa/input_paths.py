"""Bestand-of-map-invoer voor CLI-commando's.

**Afspraak:** een ``path``-argument is:

1. **één bronbestand** met de juiste extensie, of
2. **een map** waarvan recursief alle bestanden met die extensie(s)
   worden verzameld, of
3. **een catalogus-id** (slash-pad of bestandsstam) die onder
   ``content-source/catalogus/`` wordt opgezocht.

**Batch (map):** sla geneste afgeleiden over — bestanden waarvan de stam al
een brontype-extensie heeft (``lied.mvsa.mscz`` bij zoeken op ``.mscz``).
Eén expliciet bestandspad blijft toegestaan.

Zie ``docs/reference/cli/input-pad.md`` (inventaris + catalogus-id).
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Sequence
from pathlib import Path

# Extensies die als brontype in ``stem.brontype.doeltype`` voorkomen.
# Een batch mag geen product-van-product oppikken (``*.mvsa.mscz`` → svg).
BRONTYPE_SUFFIXES = frozenset(
    {
        ".mvsa",
        ".vsa",
        ".mscz",
        ".mxl",
        ".musicxml",
        ".xml",
    }
)

_ID_PART = re.compile(r"^[a-z0-9_-]+$", re.IGNORECASE)
_CATALOGUS_ID = re.compile(
    r"^[a-z0-9][a-z0-9_-]*(?:/[a-z0-9][a-z0-9_-]*)*$",
    re.IGNORECASE,
)


class InputPathError(ValueError):
    """Pad ontbreekt, is geen bestand/map, of past niet bij de extensies."""


def normalize_suffixes(suffixes: Sequence[str]) -> frozenset[str]:
    """Normaliseer tot lowercase extensies met leidende punt (``.mvsa``)."""
    out: set[str] = set()
    for raw in suffixes:
        s = str(raw).strip().lower()
        if not s:
            continue
        if not s.startswith("."):
            s = f".{s}"
        out.add(s)
    if not out:
        raise InputPathError("minstens één bestands-extensie vereist")
    return frozenset(out)


def is_nested_derived_source(path: Path | str) -> bool:
    """True als ``path`` een afgeleide is van een ander brontype.

    Voorbeeld: ``lied.mvsa.mscz`` (stam eindigt op ``.mvsa``) — product van
    ``lied.mvsa``, geen losse ``.mscz``-bron voor batch-``products``.
    """
    stem = Path(path).stem.lower()
    return any(stem.endswith(bron) for bron in BRONTYPE_SUFFIXES)


def catalogus_id_from_path(path: Path | str | None) -> str | None:
    """``soort/variant/uitvoeringsvorm`` uit ``…/catalogus/…``, of ``None``."""
    if path is None:
        return None
    parts = Path(path).resolve().parts
    for i, part in enumerate(parts):
        if part != "catalogus":
            continue
        if i + 3 >= len(parts):
            return None
        segs = parts[i + 1 : i + 4]
        if all(_ID_PART.fullmatch(s) for s in segs):
            return "/".join(segs)
        return None
    return None


def source_id_for_prompt(path: Path | str | None) -> str:
    """Label voor TTY-prompts: catalogus-id, anders bestandsstam."""
    if path is None:
        return ""
    hit = catalogus_id_from_path(path)
    if hit:
        return hit
    p = Path(path)
    return p.stem if p.suffix else p.name


def looks_like_catalogus_id(raw: str | Path) -> bool:
    """True als ``raw`` een catalogus-id kan zijn (geen bestaand pad-check)."""
    s = str(raw).strip().replace("\\", "/")
    if not s or ":" in s:
        return False
    if s.startswith(".") or s.startswith("/"):
        return False
    if Path(s).suffix:
        return False
    return bool(_CATALOGUS_ID.fullmatch(s))


def discover_catalogus_roots(
    *,
    extra: Sequence[Path | str] | None = None,
) -> list[Path]:
    """Zoek ``content-source/catalogus`` (cwd, sibling bibliotheek, env)."""
    found: list[Path] = []
    seen: set[Path] = set()

    def _add(p: Path) -> None:
        try:
            resolved = p.resolve()
        except OSError:
            return
        if resolved in seen or not resolved.is_dir():
            return
        seen.add(resolved)
        found.append(resolved)

    for item in extra or ():
        _add(Path(item))

    env = (os.environ.get("VSA_CATALOGUS") or "").strip()
    if env:
        _add(Path(env))

    tooling = Path(__file__).resolve().parents[2]
    cwd = Path.cwd()
    bases = [
        cwd,
        cwd / "content-source" / "catalogus",
        tooling.parent / "bibliotheek",
        tooling / ".." / "bibliotheek",
    ]
    for base in bases:
        b = Path(base)
        if b.name == "catalogus" and (b.parent.name == "content-source"):
            _add(b)
            continue
        _add(b / "content-source" / "catalogus")
        if b.name == "content-source":
            _add(b / "catalogus")
    return found


def resolve_catalogus_id(
    catalogus_id: str,
    *,
    suffixes: Sequence[str],
    roots: Sequence[Path | str] | None = None,
    recursive: bool = True,
) -> list[Path]:
    """Zoek bestanden voor een catalogus-id onder de catalogus-roots.

    Slash-id (``tropaar/…/hemelum``): leaf-map onder elke root.
    Stam-id (``tropaar-…-hemelum``): bestanden met die exacte stem.
    """
    allowed = normalize_suffixes(suffixes)
    cid = str(catalogus_id).strip().replace("\\", "/")
    if not looks_like_catalogus_id(cid):
        raise InputPathError(f"Geen geldige catalogus-id: {catalogus_id!r}")

    search_roots = (
        [Path(r) for r in roots]
        if roots is not None
        else discover_catalogus_roots()
    )
    if not search_roots:
        raise InputPathError(
            "Geen catalogus-root gevonden "
            "(verwacht content-source/catalogus of VSA_CATALOGUS)."
        )

    hits: list[Path] = []
    if "/" in cid:
        for root in search_roots:
            leaf = root.joinpath(*cid.split("/"))
            if leaf.is_dir():
                hits.extend(
                    collect_input_files(
                        leaf,
                        suffixes=sorted(allowed),
                        recursive=recursive,
                        resolve_ids=False,
                    )
                )
            elif leaf.is_file() and leaf.suffix.lower() in allowed:
                hits.append(leaf)
    else:
        stem = cid.lower()
        for root in search_roots:
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in allowed:
                    continue
                if is_nested_derived_source(path):
                    continue
                if path.stem.lower() == stem:
                    hits.append(path)

    # Uniek op resolve
    uniq: list[Path] = []
    seen: set[Path] = set()
    for h in sorted(hits):
        try:
            key = h.resolve()
        except OSError:
            key = h
        if key in seen:
            continue
        seen.add(key)
        uniq.append(h)
    if not uniq:
        raise InputPathError(
            f"Catalogus-id {cid!r} niet gevonden onder "
            + ", ".join(str(r) for r in search_roots)
        )
    return uniq


def collect_input_files(
    path: Path | str,
    *,
    suffixes: Sequence[str],
    recursive: bool = True,
    resolve_ids: bool = True,
    catalogus_roots: Sequence[Path | str] | None = None,
) -> list[Path]:
    """Verzamel bronbestanden: één file, map, of catalogus-id.

    Parameters
    ----------
    path:
        Bestaand bestand/map, of catalogus-id als het pad niet bestaat.
    suffixes:
        Toegestane extensies (``.mvsa``, ``mvsa``, …). Case-insensitive.
    recursive:
        Bij een map: ``rglob`` (True) of alleen directe kinderen (False).
    resolve_ids:
        Zoek catalogus-id's als het pad niet bestaat (default True).
    catalogus_roots:
        Optionele roots i.p.v. :func:`discover_catalogus_roots`.

    Returns
    -------
    list[Path]
        Gesorteerde lijst van bestaande bestanden. Mag leeg zijn als de map
        geen matches heeft. Bij een **map** worden geneste afgeleiden
        (zie :func:`is_nested_derived_source`) weggelaten. Bij één
        **bestand** blijft het pad staan, ook als het genest is.

    Raises
    ------
    InputPathError
        Pad bestaat niet (en is geen id); is geen file/dir; of is een file
        met verkeerde extensie.
    """
    p = Path(path)
    allowed = normalize_suffixes(suffixes)
    if p.exists():
        if p.is_file():
            if p.suffix.lower() not in allowed:
                want = ", ".join(sorted(allowed))
                raise InputPathError(
                    f"Verwacht bestand met extensie {want}; kreeg: {p.name}"
                )
            return [p]
        if p.is_dir():
            if recursive:
                candidates: Iterable[Path] = p.rglob("*")
            else:
                candidates = p.iterdir()
            return sorted(
                c
                for c in candidates
                if c.is_file()
                and c.suffix.lower() in allowed
                and not is_nested_derived_source(c)
            )
        raise InputPathError("Geen bestand of map.")

    if resolve_ids and looks_like_catalogus_id(path):
        return resolve_catalogus_id(
            str(path),
            suffixes=sorted(allowed),
            roots=catalogus_roots,
            recursive=recursive,
        )

    raise InputPathError("Pad niet gevonden.")


def collect_cli_sources(
    path: Path | str,
    *,
    suffixes: Sequence[str],
    recursive: bool = True,
    resolve_ids: bool = True,
    catalogus_roots: Sequence[Path | str] | None = None,
) -> list[Path]:
    """Zoals :func:`collect_input_files`, maar lege map → :exc:`InputPathError`."""
    files = collect_input_files(
        path,
        suffixes=suffixes,
        recursive=recursive,
        resolve_ids=resolve_ids,
        catalogus_roots=catalogus_roots,
    )
    if not files:
        raise InputPathError("Geen passende bestanden gevonden.")
    return files
