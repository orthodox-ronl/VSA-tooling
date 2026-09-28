"""Export .mvsa to MuseScore .mscz via partituur MusicXML (draft-v0).

Chain: ``.mvsa`` → partituur ``.mxl`` (SA/TB, lege part-namen) → MuseScore CLI
→ ``.mscz`` → layoutprofiel (default ``partituur``).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .bibliotheek_id import resolve_bibliotheek_id
from .mscz_layout import (
    DEFAULT_MSCZ_LAYOUT,
    MsczLayoutError,
    apply_mscz_layout_profile,
    normalize_mscz_layout,
)
from .mscz_partituur import MsczPartituurError
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
    "DEFAULT_MSCZ_LAYOUT",
    "MvsaMsczError",
    "export_mvsa_to_mscz",
    "export_mvsa_to_pdf",
    "export_mscz_to_pdf",
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
    layout: str | None = None,
    bibliotheek_id: str | None = None,
) -> Path:
    """Export ``path`` (.mvsa) to checklist-conformant ``out`` (.mscz).

    Intermediate MusicXML uses **partituur** layout (twee balken SA/TB).
    Post-process follows *layout* (default ``partituur``). *bibliotheek_id*
    is preferred over path sniffing for the colofon (``partituur`` only).

    Returns ``out``.
    """
    path = Path(path)
    out = Path(out)
    if out.suffix.lower() != ".mscz":
        out = out.with_suffix(".mscz")

    try:
        profile = normalize_mscz_layout(layout)
    except MsczLayoutError as exc:
        raise MvsaMsczError(str(exc)) from exc

    try:
        bib_id = resolve_bibliotheek_id(bibliotheek_id, path)
    except ValueError as exc:
        raise MvsaMsczError(str(exc)) from exc

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
            doc = parse_mvsa(path.read_text(encoding="utf-8-sig"))
            apply_mscz_layout_profile(
                out,
                layout=profile,
                system_texts=_collect_staff_texts_from_doc(doc),
                copyright=doc.copyright,
                bibliotheek_id=bib_id,
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


def export_mscz_to_pdf(
    mscz: Path,
    out: Path,
    *,
    musescore: Path | None = None,
) -> Path:
    """Convert an existing ``.mscz`` to MuseScore print-PDF (zangers)."""
    mscz = Path(mscz)
    out = Path(out)
    if out.suffix.lower() != ".pdf":
        out = out.with_suffix(".pdf")
    if not mscz.is_file():
        raise MvsaMsczError(f"Bestand niet gevonden: {mscz}")
    if mscz.suffix.lower() != ".mscz":
        raise MvsaMsczError(f"PDF-export verwacht .mscz, kreeg: {mscz.name}")
    try:
        convert_with_musescore(mscz, out, musescore=musescore)
    except (MuseScoreNotFoundError, MuseScoreConvertError) as exc:
        raise MvsaMsczError(str(exc)) from exc
    return out


def export_mvsa_to_pdf(
    path: Path,
    out: Path,
    *,
    section_id: str | None = None,
    musescore: Path | None = None,
    keep_mscz: Path | None = None,
    keep_mxl: Path | None = None,
    layout: str | None = None,
    bibliotheek_id: str | None = None,
) -> Path:
    """Export ``.mvsa`` to print-PDF via partituur ``.mscz`` (zangers).

    Returns ``out`` (``.pdf``). Intermediate ``.mscz`` is kept when
    ``keep_mscz`` is set; otherwise a temp file is used.
    """
    path = Path(path)
    out = Path(out)
    if out.suffix.lower() != ".pdf":
        out = out.with_suffix(".pdf")

    tmp_mscz: Path | None = None
    if keep_mscz is not None:
        mscz_path = Path(keep_mscz)
        if mscz_path.suffix.lower() != ".mscz":
            mscz_path = mscz_path.with_suffix(".mscz")
        mscz_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        fd, name = tempfile.mkstemp(suffix=".mscz", prefix="mvsa-")
        os.close(fd)
        tmp_mscz = Path(name)
        mscz_path = tmp_mscz

    try:
        export_mvsa_to_mscz(
            path,
            mscz_path,
            section_id=section_id,
            musescore=musescore,
            keep_mxl=keep_mxl,
            layout=layout,
            bibliotheek_id=bibliotheek_id,
        )
        export_mscz_to_pdf(mscz_path, out, musescore=musescore)
    finally:
        if tmp_mscz is not None:
            tmp_mscz.unlink(missing_ok=True)

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
