"""Export universal street products from any notation source.

Contract: docs/formats/contract-index.md (universele productcatalogus).
CLI streets gate extensions; this module accepts `.vsa` / `.mvsa` / `.mscz`.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .derived_path import derived_output_path


class StreetProductExportError(Exception):
    """Export van een universeel product mislukt."""


def lyrics_output_path(bron: Path) -> Path:
    return derived_output_path(bron, ".lyrics.txt")


def write_lyrics_product(
    bron: Path,
    out: Path | None = None,
    *,
    musescore: Path | None = None,
) -> Path:
    """Schrijf platte gezongen tekst (meta-key ``lyrics``)."""
    from .text_export import plain_text_from_path

    dest = Path(out) if out is not None else lyrics_output_path(bron)
    text = plain_text_from_path(bron, musescore=musescore)
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = text if text.endswith("\n") or text == "" else text + "\n"
    dest.write_text(payload, encoding="utf-8", newline="\n")
    return dest


def export_bron_to_score_ir(
    bron: Path,
    out: Path,
    *,
    musescore: Path | None = None,
    section_id: str | None = None,
    bibliotheek_id: str | None = None,
) -> None:
    """Score-IR JSON uit ``.vsa`` / ``.mvsa`` / ``.mscz``."""
    from .mvsa_import import MvsaImportError, import_score_path
    from .mvsa_musicxml import MvsaExportError
    from .score_ir import export_mvsa_path_to_score_ir
    from .vsa_musicxml_export import MusicXMLExportError, export_vsa_to_musicxml

    bron = Path(bron)
    out = Path(out)
    suffix = bron.suffix.lower()
    if suffix == ".mvsa":
        export_mvsa_path_to_score_ir(
            bron,
            out,
            section_id=section_id,
            bibliotheek_id=bibliotheek_id,
        )
        return

    fd, tmp_name = tempfile.mkstemp(suffix=".mvsa", prefix="score-ir-")
    os.close(fd)
    tmp_mvsa = Path(tmp_name)
    tmp_mxl: Path | None = None
    try:
        if suffix == ".mscz":
            import_score_path(bron, tmp_mvsa, musescore=musescore)
        elif suffix == ".vsa":
            fd2, mxl_name = tempfile.mkstemp(suffix=".mxl", prefix="score-ir-vsa-")
            os.close(fd2)
            tmp_mxl = Path(mxl_name)
            export_vsa_to_musicxml(bron, tmp_mxl, syllabify=True)
            import_score_path(tmp_mxl, tmp_mvsa, musescore=musescore)
        else:
            raise StreetProductExportError(
                f"score-ir verwacht .vsa/.mvsa/.mscz, kreeg {bron.name}"
            )
        export_mvsa_path_to_score_ir(
            tmp_mvsa,
            out,
            section_id=section_id,
            bibliotheek_id=bibliotheek_id,
        )
    except (MvsaImportError, MvsaExportError, MusicXMLExportError) as exc:
        raise StreetProductExportError(str(exc)) from exc
    finally:
        tmp_mvsa.unlink(missing_ok=True)
        if tmp_mxl is not None:
            tmp_mxl.unlink(missing_ok=True)


def export_bron_to_mscz_product(
    bron: Path,
    out: Path,
    *,
    musescore: Path | None = None,
) -> Path:
    """Partituur-``.mscz`` (S*) uit notatiebron; ``.mscz`` → normalize sibling."""
    from .mscz_layout import normalize_mscz_path
    from .musescore_cli import convert_with_musescore
    from .mvsa_mscz import export_mvsa_to_mscz
    from .vsa_musicxml_export import export_vsa_to_musicxml

    bron = Path(bron)
    out = Path(out)
    suffix = bron.suffix.lower()
    if suffix == ".mscz":
        written, _ = normalize_mscz_path(bron, out, layout="partituur")
        return written
    if suffix == ".mvsa":
        return export_mvsa_to_mscz(bron, out, musescore=musescore)
    if suffix == ".vsa":
        fd, name = tempfile.mkstemp(suffix=".mxl", prefix="vsa-mscz-")
        os.close(fd)
        tmp_mxl = Path(name)
        try:
            export_vsa_to_musicxml(bron, tmp_mxl, syllabify=True)
            convert_with_musescore(tmp_mxl, out, musescore=musescore)
            written, _ = normalize_mscz_path(out, out, layout="partituur")
            return written
        finally:
            tmp_mxl.unlink(missing_ok=True)
    raise StreetProductExportError(
        f"mscz-product verwacht .vsa/.mvsa/.mscz, kreeg {bron.name}"
    )


def export_bron_to_partituur_pdf(
    bron: Path,
    out: Path,
    *,
    musescore: Path | None = None,
) -> Path:
    """Print-PDF (P*) uit notatiebron."""
    from .mvsa_mscz import export_mscz_to_pdf, export_mvsa_to_pdf

    bron = Path(bron)
    out = Path(out)
    suffix = bron.suffix.lower()
    if suffix == ".mscz":
        export_mscz_to_pdf(bron, out, musescore=musescore)
        return out
    if suffix == ".mvsa":
        export_mvsa_to_pdf(bron, out, musescore=musescore)
        return out
    if suffix == ".vsa":
        fd, name = tempfile.mkstemp(suffix=".mscz", prefix="vsa-pdf-")
        os.close(fd)
        tmp_mscz = Path(name)
        try:
            export_bron_to_mscz_product(bron, tmp_mscz, musescore=musescore)
            export_mscz_to_pdf(tmp_mscz, out, musescore=musescore)
            return out
        finally:
            tmp_mscz.unlink(missing_ok=True)
    raise StreetProductExportError(
        f"pdf-product verwacht .vsa/.mvsa/.mscz, kreeg {bron.name}"
    )


def export_bron_to_mxl(
    bron: Path,
    out: Path,
    *,
    musescore: Path | None = None,
) -> Path:
    """Coria/playback-``.mxl`` uit notatiebron."""
    from .musicxml_playback_normalize import export_mscz_to_playback_mxl
    from .mvsa_musicxml import export_mvsa_path
    from .vsa_musicxml_export import export_vsa_to_musicxml

    bron = Path(bron)
    out = Path(out)
    suffix = bron.suffix.lower()
    if suffix == ".mvsa":
        export_mvsa_path(bron, out, layout="playback")
        return out
    if suffix == ".mscz":
        export_mscz_to_playback_mxl(bron, out, musescore=musescore)
        return out
    if suffix == ".vsa":
        export_vsa_to_musicxml(bron, out, syllabify=True)
        return out
    raise StreetProductExportError(
        f"mxl-product verwacht .vsa/.mvsa/.mscz, kreeg {bron.name}"
    )
