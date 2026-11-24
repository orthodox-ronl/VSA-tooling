"""Logische ``id:``-verwijzingen naar bibliotheek-catalogusbestanden.

Een ``id:`` is een pad onder ``content-source/catalogus/`` (zangstuk/variant/uitvoeringsvorm).
``lokaal:`` en ``bron:`` bestaan niet meer (migratie stap 4, deel 2).
"""

from __future__ import annotations

from pathlib import Path

from .input_paths import InputPathError, resolve_catalogus_id

ID_PREFIX = "id:"
_VERVALLEN_PREFIXES = ("lokaal:", "bron:")


def is_logical_reference(reference: str) -> bool:
    """True voor ``id:``-verwijzingen en voor de vervallen ``lokaal:``/``bron:``."""
    text = str(reference).strip()
    return text.startswith(ID_PREFIX) or text.startswith(_VERVALLEN_PREFIXES)


def resolve_logical_vsa_path(reference: str, *, content_root: Path) -> Path:
    """Los ``id:<pad>`` op naar precies \u00e9\u00e9n ``.vsa`` onder ``content_root/catalogus``."""
    text = str(reference).strip()
    for prefix in _VERVALLEN_PREFIXES:
        if text.startswith(prefix):
            raise ValueError(
                f"{prefix[:-1]}= wordt niet meer ondersteund. "
                "Gebruik id=<zangstuk>/<variant>/<uitvoeringsvorm> "
                "(pad onder content-source/catalogus)."
            )
    if not text.startswith(ID_PREFIX):
        raise ValueError(f"Geen logische referentie: {reference!r}")
    catalogus_id = text[len(ID_PREFIX):].strip().strip("/")
    try:
        hits = resolve_catalogus_id(
            catalogus_id,
            suffixes=[".vsa"],
            roots=[content_root / "catalogus"],
        )
    except InputPathError as exc:
        raise ValueError(str(exc)) from exc
    if not hits:
        raise ValueError(f"Geen .vsa gevonden voor id {catalogus_id!r} onder {content_root / 'catalogus'}.")
    if len(hits) > 1:
        namen = ", ".join(str(h.relative_to(content_root)) for h in hits)
        raise ValueError(f"id {catalogus_id!r} is niet uniek; gevonden: {namen}.")
    return hits[0]
