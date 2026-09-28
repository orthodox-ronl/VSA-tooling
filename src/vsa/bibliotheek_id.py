"""Bibliotheek-id op partituur-export (mechanisme, niet beleid).

**Ownership:** welke id bij een zangstuk hoort, bepaalt de consumer
(bibliotheek-repo / product-scripts). VSA-tooling biedt manieren om een id
*door te geven* naar colofon/metadata (``--bibliotheek-id`` / API-parameter).

``bibliotheek_id_from_path`` is een **optioneel hulpmiddel** voor padherkenning.
Consumers horen bij voorkeur de id **expliciet** te zetten. Zie
docs/guides/reuse-vsa-tooling.md#ownership-tooling-vs-consumer.
"""

from __future__ import annotations

import re
from pathlib import Path

_ID_PART = re.compile(r"^[a-z0-9_-]+$")
# Expliciete id: slash-gescheiden segmenten of één token (zoals in colofon).
_EXPLICIT_ID = re.compile(r"^[a-z0-9][a-z0-9_./-]*$", re.IGNORECASE)


def bibliotheek_id_from_path(path: Path | str | None) -> str | None:
    """Return ``zangstuk/variant/uitvoeringsvorm`` of ``None``.

    Convenience only — not authoritative. Prefer an explicit id from the
    consumer when writing colophon/metadata.
    """
    if path is None:
        return None
    parts = Path(path).resolve().parts
    for i, part in enumerate(parts):
        if part != "bibliotheek":
            continue
        if i + 3 >= len(parts):
            return None
        segs = parts[i + 1 : i + 4]
        if all(_ID_PART.fullmatch(s) for s in segs):
            return "/".join(segs)
        return None
    return None


def normalize_bibliotheek_id(value: str) -> str:
    """Validate and return a stripped explicit id, or raise ``ValueError``."""
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("bibliotheek-id mag niet leeg zijn")
    if not _EXPLICIT_ID.fullmatch(cleaned):
        raise ValueError(
            f"ongeldige bibliotheek-id {value!r} "
            f"(verwacht [a-z0-9][a-z0-9_./-]* )"
        )
    return cleaned


def resolve_bibliotheek_id(
    explicit: str | None,
    path: Path | str | None = None,
    *,
    allow_path_fallback: bool = True,
) -> str | None:
    """Prefer *explicit* id; optionally fall back to path sniffing."""
    if explicit is not None:
        return normalize_bibliotheek_id(explicit)
    if allow_path_fallback:
        return bibliotheek_id_from_path(path)
    return None
