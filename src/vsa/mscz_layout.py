"""Benoemde MSCZ-layoutprofielen (export na MuseScore-conversie).

Consumers kiezen een profiel; VSA-tooling definieert en handhaaft het.
Zie docs/formats/mscz-leesbaarheid.md en
docs/guides/reuse-vsa-tooling.md#ownership-tooling-vs-consumer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from .mscz_partituur import MsczPartituurError, apply_partituur_mscz_conventions

MsczLayoutName = Literal["partituur", "plain"]

MSCZ_LAYOUT_PROFILES: tuple[str, ...] = ("partituur", "plain")
DEFAULT_MSCZ_LAYOUT: MsczLayoutName = "partituur"

# Korte omschrijvingen voor CLI-help / docs (één zin per profiel).
MSCZ_LAYOUT_DESCRIPTIONS: dict[str, str] = {
    "partituur": (
        "Canonieke koorprint: A4, leesbaarheid (recite-spacers, SystemText), "
        "lege partijnamen, colofon/copyright (zie mscz-leesbaarheid)."
    ),
    "plain": (
        "Alleen MuseScore-conversie van de partituur-MXL; geen Style-/colofon-/"
        "recite-nabewerking door VSA-tooling."
    ),
}


class MsczLayoutError(ValueError):
    """Unknown or invalid MSCZ layout profile."""


def normalize_mscz_layout(name: str | None) -> MsczLayoutName:
    """Return a known layout id or raise :class:`MsczLayoutError`."""
    if name is None or not str(name).strip():
        return DEFAULT_MSCZ_LAYOUT
    key = str(name).strip().lower()
    if key not in MSCZ_LAYOUT_PROFILES:
        known = ", ".join(MSCZ_LAYOUT_PROFILES)
        raise MsczLayoutError(
            f"onbekend MSCZ-layoutprofiel {name!r} (verwacht: {known})"
        )
    return key  # type: ignore[return-value]


def apply_mscz_layout_profile(
    path: Path,
    *,
    layout: str | None = None,
    system_texts: list[str] | None = None,
    copyright: str | None = None,
    bibliotheek_id: str | None = None,
    title: str | None = None,
    composer: str | None = None,
    bron: str | None = None,
    ondertitel: str | None = None,
    tekstdichter: str | None = None,
    arrangeur: str | None = None,
    vertaler: str | None = None,
) -> str:
    """Apply the named layout to ``path`` (.mscz). Returns the profile id used.

    ``plain`` leaves the MuseScore file unchanged. ``partituur`` runs
    :func:`apply_partituur_mscz_conventions`.
    """
    profile = normalize_mscz_layout(layout)
    if profile == "plain":
        return profile
    apply_partituur_mscz_conventions(
        path,
        system_texts=system_texts,
        copyright=copyright,
        bibliotheek_id=bibliotheek_id,
        title=title,
        composer=composer,
        bron=bron,
        ondertitel=ondertitel,
        tekstdichter=tekstdichter,
        arrangeur=arrangeur,
        vertaler=vertaler,
    )
    return profile


__all__ = [
    "DEFAULT_MSCZ_LAYOUT",
    "MSCZ_LAYOUT_DESCRIPTIONS",
    "MSCZ_LAYOUT_PROFILES",
    "MsczLayoutError",
    "MsczLayoutName",
    "MsczPartituurError",
    "apply_mscz_layout_profile",
    "normalize_mscz_layout",
]
