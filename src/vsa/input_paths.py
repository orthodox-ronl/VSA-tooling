"""Bestand-of-map-invoer voor CLI-commando's.

**Afspraak:** een ``path``-argument is óf één bronbestand, óf een map waarvan
recursief alle bestanden met de toegestane extensie(s) worden verzameld.

**Batch (map):** sla geneste afgeleiden over — bestanden waarvan de stam al
een brontype-extensie heeft (``lied.mvsa.mscz`` bij zoeken op ``.mscz``).
Eén expliciet bestandspad blijft toegestaan.

Zie ``docs/reference/cli/input-pad.md`` (inventaris + toekomstige migratie).
"""

from __future__ import annotations

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


def collect_input_files(
    path: Path | str,
    *,
    suffixes: Sequence[str],
    recursive: bool = True,
) -> list[Path]:
    """Verzamel bronbestanden: één file of (recursief) een map.

    Parameters
    ----------
    path:
        Bestaand bestand of bestaande map.
    suffixes:
        Toegestane extensies (``.mvsa``, ``mvsa``, …). Case-insensitive.
    recursive:
        Bij een map: ``rglob`` (True) of alleen directe kinderen (False).

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
        Pad bestaat niet; is geen file/dir; of is een file met verkeerde
        extensie.
    """
    p = Path(path)
    allowed = normalize_suffixes(suffixes)
    if not p.exists():
        raise InputPathError(f"Pad niet gevonden: {p}")
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
    raise InputPathError(f"Geen bestand of map: {p}")


def collect_cli_sources(
    path: Path | str,
    *,
    suffixes: Sequence[str],
    recursive: bool = True,
) -> list[Path]:
    """Zoals :func:`collect_input_files`, maar lege map → :exc:`InputPathError`."""
    files = collect_input_files(path, suffixes=suffixes, recursive=recursive)
    if not files:
        raise InputPathError(f"Geen passende bestanden gevonden: {path}")
    return files
