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
    "export_mvsa_to_svg",
    "export_mscz_to_pdf",
    "export_mscz_to_svg",
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
    translit: bool = False,
    min_system_distance: float | None = None,
    max_system_distance: float | None = None,
    staff_distance: float | None = None,
    page_margin_top_mm: float | None = None,
    page_margin_bottom_mm: float | None = None,
    lyrics_min_top_distance: float | None = None,
    lyrics_min_bottom_distance: float | None = None,
    lyrics_min_distance: float | None = None,
    lyrics_font: str | None = None,
    lyrics_font_size: float | None = None,
    cue_font: str | None = None,
    cue_font_size: float | None = None,
    measure_spacing: float | None = None,
) -> Path:
    """Export ``path`` (.mvsa) to checklist-conformant ``out`` (.mscz).

    Intermediate MusicXML uses **partituur** layout (twee balken SA/TB).
    Post-process follows *layout* (default ``partituur``). *bibliotheek_id*
    is preferred over path sniffing for the colofon (``partituur`` only).
    *translit*: tweede lyric-laag in het tussen-MXL (blad «tweede couplet»).
    Style-overrides (systeem-/stafafstand, pagina-marges, lyric-clearance,
    fonts, measureSpacing): not valid with layout ``plain``.

    Returns ``out``.
    """
    from .mscz_partituur import build_partituur_style_overrides

    path = Path(path)
    out = Path(out)
    if out.suffix.lower() != ".mscz":
        out = out.with_suffix(".mscz")

    try:
        profile = normalize_mscz_layout(layout)
    except MsczLayoutError as exc:
        raise MvsaMsczError(str(exc)) from exc

    try:
        style_overrides = build_partituur_style_overrides(
            min_system_distance=min_system_distance,
            max_system_distance=max_system_distance,
            staff_distance=staff_distance,
            page_margin_top_mm=page_margin_top_mm,
            page_margin_bottom_mm=page_margin_bottom_mm,
            lyrics_min_top_distance=lyrics_min_top_distance,
            lyrics_min_bottom_distance=lyrics_min_bottom_distance,
            lyrics_min_distance=lyrics_min_distance,
            lyrics_font=lyrics_font,
            lyrics_font_size=lyrics_font_size,
            cue_font=cue_font,
            cue_font_size=cue_font_size,
            measure_spacing=measure_spacing,
        )
    except MsczPartituurError as exc:
        raise MvsaMsczError(str(exc)) from exc
    if style_overrides and profile == "plain":
        raise MvsaMsczError(
            "Style-opties (systeem-/stafafstand / pagina-marges / fonts / "
            "measure-spacing) gelden niet bij --layout plain "
            "(geen Style-nabewerking)"
        )

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
                path,
                mxl_path,
                section_id=section_id,
                layout="partituur",
                translit=translit,
            )
        except (MvsaValidationError, MvsaExportError):
            raise
        except Exception as exc:
            raise MvsaMsczError(f"MusicXML-tussenbestand mislukt: {exc}") from exc

        try:
            convert_with_musescore(
                mxl_path,
                out,
                musescore=musescore,
                musicxml_infer_text_type=True,
            )
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
                style_overrides=style_overrides or None,
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
    translit: bool = False,
    min_system_distance: float | None = None,
    max_system_distance: float | None = None,
    staff_distance: float | None = None,
    page_margin_top_mm: float | None = None,
    page_margin_bottom_mm: float | None = None,
    lyrics_min_top_distance: float | None = None,
    lyrics_min_bottom_distance: float | None = None,
    lyrics_min_distance: float | None = None,
    lyrics_font: str | None = None,
    lyrics_font_size: float | None = None,
    cue_font: str | None = None,
    cue_font_size: float | None = None,
    measure_spacing: float | None = None,
) -> Path:
    """Export ``.mvsa`` to print-PDF via partituur ``.mscz`` (zangers).

    Returns ``out`` (``.pdf``). Intermediate ``.mscz`` is kept when
    ``keep_mscz`` is set; otherwise a temp file is used.
    *translit*: tweede lyric-laag in de tussen-MXL/MSCZ (blad «tweede regel»).
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
            translit=translit,
            min_system_distance=min_system_distance,
            max_system_distance=max_system_distance,
            staff_distance=staff_distance,
            page_margin_top_mm=page_margin_top_mm,
            page_margin_bottom_mm=page_margin_bottom_mm,
            lyrics_min_top_distance=lyrics_min_top_distance,
            lyrics_min_bottom_distance=lyrics_min_bottom_distance,
            lyrics_min_distance=lyrics_min_distance,
            lyrics_font=lyrics_font,
            lyrics_font_size=lyrics_font_size,
            cue_font=cue_font,
            cue_font_size=cue_font_size,
            measure_spacing=measure_spacing,
        )
        export_mscz_to_pdf(mscz_path, out, musescore=musescore)
    finally:
        if tmp_mscz is not None:
            tmp_mscz.unlink(missing_ok=True)

    return out


def export_mscz_to_svg(
    mscz: Path,
    out: Path,
    *,
    musescore: Path | None = None,
    trim: bool = True,
    white_background: bool = True,
) -> list[Path]:
    """Convert ``.mscz`` to één kale tall-SVG (compact Style, geen bladreeks).

    Sheet chrome wordt op een tijdelijke kopie gestript; daarna compacte
    Style + hoge ``pageHeight`` zodat MuseScore geen A4-pagina’s splitst.
    Schrijft altijd ``out`` (sibling ``*.svg``). Oude ``stem-N.svg`` worden
    verwijderd. Bron ``.mscz`` blijft ongewijzigd.
    """
    import shutil

    from .mscz_partituur import (
        pad_mscz_lyric_word_gaps,
        patch_mscz_style,
        strip_mscz_sheet_chrome,
        tall_compact_svg_style_overrides,
    )
    from .musescore_cli import list_musescore_svg_pages
    from .svg_trim import SvgTrimError, trim_musescore_svg

    mscz = Path(mscz)
    out = Path(out)
    if out.suffix.lower() != ".svg":
        out = out.with_suffix(".svg")
    if not mscz.is_file():
        raise MvsaMsczError(f"Bestand niet gevonden: {mscz}")
    if mscz.suffix.lower() != ".mscz":
        raise MvsaMsczError(f"SVG-export verwacht .mscz, kreeg: {mscz.name}")

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    for stale in out.parent.glob(f"{out.stem}-*.svg"):
        stale.unlink(missing_ok=True)

    fd, tmp_name = tempfile.mkstemp(suffix=".mscz", prefix="mscz-svg-")
    os.close(fd)
    tmp_mscz = Path(tmp_name)
    try:
        shutil.copy2(mscz, tmp_mscz)
        try:
            strip_mscz_sheet_chrome(tmp_mscz)
            pad_mscz_lyric_word_gaps(tmp_mscz)
            patch_mscz_style(tmp_mscz, tall_compact_svg_style_overrides())
        except MsczPartituurError as exc:
            raise MvsaMsczError(str(exc)) from exc
        try:
            first = convert_with_musescore(tmp_mscz, out, musescore=musescore)
        except (MuseScoreNotFoundError, MuseScoreConvertError) as exc:
            raise MvsaMsczError(str(exc)) from exc
    finally:
        tmp_mscz.unlink(missing_ok=True)

    pages = list_musescore_svg_pages(out)
    if out.is_file() and not pages:
        written = [out]
    elif len(pages) == 1 and not out.exists():
        from .atomic_io import replace_into

        replace_into(out, pages[0])
        written = [out]
    elif pages:
        for path in pages:
            path.unlink(missing_ok=True)
        raise MvsaMsczError(
            f"tall-SVG leverde {len(pages)} MuseScore-pagina’s i.p.v. één "
            f"({out.name}); verhoog pageHeight of meld als bug"
        )
    else:
        written = [first]
        if first.resolve() != out.resolve() and first.is_file():
            from .atomic_io import replace_into

            replace_into(out, first)
            written = [out]

    from .atomic_io import write_text
    from .svg_lyric_gaps import enforce_svg_lyric_word_gaps

    for path in written:
        text = path.read_text(encoding="utf-8")
        text = enforce_svg_lyric_word_gaps(text)
        if trim:
            try:
                text = trim_musescore_svg(
                    text,
                    white_background=white_background,
                )
            except SvgTrimError as exc:
                raise MvsaMsczError(str(exc)) from exc
        write_text(path, text, encoding="utf-8", newline="\n")
    return written


def export_mvsa_to_svg(
    path: Path,
    out: Path,
    *,
    section_id: str | None = None,
    musescore: Path | None = None,
    keep_mscz: Path | None = None,
    keep_mxl: Path | None = None,
    bibliotheek_id: str | None = None,
    translit: bool = False,
    trim: bool = True,
    white_background: bool = True,
    engine: str | None = None,
    min_system_distance: float | None = None,
    max_system_distance: float | None = None,
    staff_distance: float | None = None,
    page_margin_top_mm: float | None = None,
    page_margin_bottom_mm: float | None = None,
    lyrics_min_top_distance: float | None = None,
    lyrics_min_bottom_distance: float | None = None,
    lyrics_min_distance: float | None = None,
    lyrics_font: str | None = None,
    lyrics_font_size: float | None = None,
    cue_font: str | None = None,
    cue_font_size: float | None = None,
    measure_spacing: float | None = None,
) -> list[Path]:
    """Export ``.mvsa`` to één kale tall-SVG.

Default ``engine=musescore``: partituur-MXL → MSCZ → MuseScore → trim.
    ``engine=osmd``: Score-IR → from-ir MusicXML → headless OSMD (geen MuseScore).
    Style-kwargs gelden alleen voor MuseScore.
    *translit*: tweede lyric-laag in de tussen-MXL/MSCZ (koormap «met translit»).
    Return: altijd ``[out]``.
    """
    from .mscz_partituur import apply_compact_style_preset
    from .osmd_svg import OsmdSvgError, export_mvsa_to_osmd_svg, normalize_svg_engine

    path = Path(path)
    out = Path(out)
    if out.suffix.lower() != ".svg":
        out = out.with_suffix(".svg")

    try:
        eng = normalize_svg_engine(engine)
    except OsmdSvgError as exc:
        raise MvsaMsczError(str(exc)) from exc

    if eng == "osmd":
        if keep_mscz is not None:
            raise MvsaMsczError(
                "--keep-mscz geldt niet bij --engine osmd (geen MSCZ-keten)"
            )
        try:
            return export_mvsa_to_osmd_svg(
                path,
                out,
                section_id=section_id,
                bibliotheek_id=bibliotheek_id,
                keep_musicxml=keep_mxl,
            )
        except OsmdSvgError as exc:
            raise MvsaMsczError(str(exc)) from exc
        except MvsaExportError:
            raise
        except Exception as exc:
            raise MvsaMsczError(f"OSMD-SVG mislukt: {exc}") from exc

    style = apply_compact_style_preset(
        {
            "min_system_distance": min_system_distance,
            "max_system_distance": max_system_distance,
            "staff_distance": staff_distance,
            "page_margin_top_mm": page_margin_top_mm,
            "page_margin_bottom_mm": page_margin_bottom_mm,
            "lyrics_min_top_distance": lyrics_min_top_distance,
            "lyrics_min_bottom_distance": lyrics_min_bottom_distance,
            "lyrics_min_distance": lyrics_min_distance,
            "lyrics_font": lyrics_font,
            "lyrics_font_size": lyrics_font_size,
            "cue_font": cue_font,
            "cue_font_size": cue_font_size,
            "measure_spacing": measure_spacing,
        }
    )

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
            layout="muziek",
            bibliotheek_id=bibliotheek_id,
            translit=translit,
            min_system_distance=style.get("min_system_distance"),
            max_system_distance=style.get("max_system_distance"),
            staff_distance=style.get("staff_distance"),
            page_margin_top_mm=style.get("page_margin_top_mm"),
            page_margin_bottom_mm=style.get("page_margin_bottom_mm"),
            lyrics_min_top_distance=style.get("lyrics_min_top_distance"),
            lyrics_min_bottom_distance=style.get("lyrics_min_bottom_distance"),
            lyrics_min_distance=style.get("lyrics_min_distance"),
            lyrics_font=style.get("lyrics_font"),
            lyrics_font_size=style.get("lyrics_font_size"),
            cue_font=style.get("cue_font"),
            cue_font_size=style.get("cue_font_size"),
            measure_spacing=style.get("measure_spacing"),
        )
        return export_mscz_to_svg(
            mscz_path,
            out,
            musescore=musescore,
            trim=trim,
            white_background=white_background,
        )
    finally:
        if tmp_mscz is not None:
            tmp_mscz.unlink(missing_ok=True)



def _collect_staff_texts_from_doc(doc) -> list[str]:
    out: list[str] = []
    for section in doc.sections:
        for system in section.systems:
            out.extend(system.staff_texts)
    return out


def _collect_staff_texts(path: Path) -> list[str]:
    """All ``@tekst`` strings in document order (for MSCZ SystemText promote)."""
    return _collect_staff_texts_from_doc(parse_mvsa(path.read_text(encoding="utf-8-sig")))
