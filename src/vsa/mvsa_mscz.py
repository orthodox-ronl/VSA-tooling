"""Export .mvsa to MuseScore .mscz via partituur MusicXML (draft-v0).

Chain: ``.mvsa`` → partituur ``.mxl`` (SA/TB, lege part-namen) → MuseScore CLI
→ ``.mscz`` → strip stem-indicaties (Style + longName/shortName).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .mscz_partituur import MsczPartituurError, apply_partituur_mscz_conventions
from .musescore_cli import (
    MuseScoreConvertError,
    MuseScoreNotFoundError,
    convert_with_musescore,
    require_musescore,
)
from .mvsa_musicxml import MvsaExportError, export_mvsa_path
from .mvsa_parse import parse_mvsa
from .mvsa_validate import MvsaValidationError

__all__ = [
    "MvsaMsczError",
    "export_mvsa_to_mscz",
    "MuseScoreConvertError",
    "MuseScoreNotFoundError",
]


class MvsaMsczError(Exception):
    """MSCZ export failed (validation, MusicXML, or MuseScore)."""


def export_mvsa_to_mscz(
    path: Path,
    out: Path,
    *,
    section_id: str | None = None,
    musescore: Path | None = None,
    keep_mxl: Path | None = None,
) -> Path:
    """Export ``path`` (.mvsa) to checklist-conformant ``out`` (.mscz).

    Intermediate MusicXML uses **partituur** layout (twee balken SA/TB).
    Returns ``out``.
    """
    path = Path(path)
    out = Path(out)
    if out.suffix.lower() != ".mscz":
        out = out.with_suffix(".mscz")

    try:
        require_musescore(override=musescore)
    except MuseScoreNotFoundError as exc:
        raise MvsaMsczError(str(exc)) from exc

    tmp_mxl: Path | None = None
    if keep_mxl is not None:
        mxl_path = Path(keep_mxl)
        if mxl_path.suffix.lower() not in {".mxl", ".musicxml", ".xml"}:
            mxl_path = mxl_path.with_suffix(".mxl")
        mxl_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        fd, name = tempfile.mkstemp(suffix=".mxl", prefix="mvsa-")
        os.close(fd)
        tmp_mxl = Path(name)
        mxl_path = tmp_mxl

    try:
        try:
            export_mvsa_path(
                path, mxl_path, section_id=section_id, layout="partituur"
            )
        except (MvsaValidationError, MvsaExportError):
            raise
        except Exception as exc:
            raise MvsaMsczError(f"MusicXML-tussenbestand mislukt: {exc}") from exc

        try:
            convert_with_musescore(mxl_path, out, musescore=musescore)
        except (MuseScoreNotFoundError, MuseScoreConvertError) as exc:
            raise MvsaMsczError(str(exc)) from exc

        try:
            from .bibliotheek_id import bibliotheek_id_from_path

            doc = parse_mvsa(path.read_text(encoding="utf-8-sig"))
            # Geen mid-systeem-HBox vóór @tekst (accolade). Scheiding = ‖ +
            # SystemText; lege spacer-maten worden weggestript.
            apply_partituur_mscz_conventions(
                out,
                system_texts=_collect_staff_texts_from_doc(doc),
                copyright=doc.copyright,
                bibliotheek_id=bibliotheek_id_from_path(path),
                title=doc.title,
                composer=doc.composer,
                bron=doc.bron,
                ondertitel=doc.ondertitel,
                tekstdichter=doc.tekstdichter,
                arrangeur=doc.arrangeur,
                vertaler=doc.vertaler,
            )
        except MsczPartituurError as exc:
            raise MvsaMsczError(str(exc)) from exc
    finally:
        if tmp_mxl is not None:
            tmp_mxl.unlink(missing_ok=True)

    return out


def _collect_staff_texts_from_doc(doc) -> list[str]:
    out: list[str] = []
    for section in doc.sections:
        for system in section.systems:
            out.extend(system.staff_texts)
    return out


def _collect_staff_texts(path: Path) -> list[str]:
    """All ``@tekst`` strings in document order (for MSCZ SystemText promote)."""
    return _collect_staff_texts_from_doc(parse_mvsa(path.read_text(encoding="utf-8-sig")))
