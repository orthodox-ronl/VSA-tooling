"""Gedeelde Coria/playback-normalisatie voor MXL.

Keten: SATB-explode (M2) + piano (M8) → optioneel recite-explosie (M10) →
``finalize_coria_musicxml`` (timing/sanitize/accidentals).
"""

from __future__ import annotations

from pathlib import Path

from .musicxml_coria_timing import finalize_coria_musicxml
from .musicxml_package import write_musicxml_output
from .musicxml_recite_expand import expand_recite_notes
from .musicxml_satb_layout import ensure_playback_musicxml
from .mvsa_import import read_musicxml_file


def normalize_playback_musicxml(
    xml: str,
    *,
    apply_timing: bool = False,
    expand_recite: bool | None = None,
) -> str:
    """Normalize MusicXML to Coria playback profile.

    *apply_timing*: ``True`` for MuseScore/MSCZ-derived XML (pause/caesura
    inserts). MVSA playback export already emits pauses → ``False``.

    *expand_recite*: defaults to *apply_timing* (feathered ``||O||`` from
    partituur MSCZ). Set explicitly when needed.
    """
    if expand_recite is None:
        expand_recite = apply_timing
    playback = ensure_playback_musicxml(xml)
    if expand_recite:
        from xml.etree import ElementTree as ET

        from .musicxml_coria_timing import strip_doctype

        root = ET.fromstring(strip_doctype(playback))
        expand_recite_notes(root)
        body = ET.tostring(root, encoding="unicode")
        if not body.startswith("<?xml"):
            body = '<?xml version="1.0" encoding="UTF-8"?>\n' + body
        playback = body
    return finalize_coria_musicxml(playback, apply_timing=apply_timing)


def normalize_playback_mxl_path(
    path: Path,
    out: Path | None = None,
    *,
    apply_timing: bool = False,
    expand_recite: bool | None = None,
) -> Path:
    """Read *path*, normalize, write *out* (default: overwrite *path*)."""
    path = Path(path)
    dest = Path(out) if out is not None else path
    xml = read_musicxml_file(path)
    normalized = normalize_playback_musicxml(
        xml,
        apply_timing=apply_timing,
        expand_recite=expand_recite,
    )
    write_musicxml_output(dest, normalized)
    return dest
