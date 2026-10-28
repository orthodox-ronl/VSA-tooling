"""Top-level ``mscz`` CLI (bron: ``.mscz``).

Universele producten + import/normalize/compare. Alleen invoer ``.mscz``
(uitzondering: ``compare`` SCORE mag MusicXML; ``import`` andere bron).
Contract: docs/formats/contract-index.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cli_score_to_mvsa import add_score_to_mvsa_arguments, run_score_to_mvsa
from .derived_path import derived_output_path
from .input_paths import InputPathError, collect_cli_sources

_MSCZ_SUFFIXES = (".mscz",)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()
    ns = parser.parse_args(args)
    if ns.mscz_command == "mvsa":
        return run_score_to_mvsa(ns, suffixes=_MSCZ_SUFFIXES)
    if ns.mscz_command == "import":
        from .cli_import import run_mscz_import

        return run_mscz_import(ns)
    if ns.mscz_command == "products":
        from .street_products import run_street_products

        musescore = Path(ns.musescore) if getattr(ns, "musescore", None) else None
        return run_street_products(
            "mscz",
            ns.path,
            force=bool(ns.force),
            dry_run=bool(ns.dry_run),
            skip_svg=bool(getattr(ns, "skip_svg", False)),
            musescore=musescore,
        )
    if ns.mscz_command == "mxl":
        return _cmd_mscz_to_mxl(ns)
    if ns.mscz_command == "svg":
        return _cmd_mscz_svg(ns)
    if ns.mscz_command == "pdf":
        return _cmd_mscz_pdf(ns)
    if ns.mscz_command in ("mp3", "ogg", "wav"):
        return _cmd_mscz_audio(ns)
    if ns.mscz_command == "score-ir":
        return _cmd_mscz_score_ir(ns)
    if ns.mscz_command == "mscz":
        return _cmd_mscz_product(ns)
    if ns.mscz_command == "normalize":
        return _cmd_mscz_normalize(ns)
    if ns.mscz_command == "text":
        return _cmd_mscz_text(ns)
    if ns.mscz_command == "compare":
        return _cmd_mscz_compare(ns)
    parser.print_help()
    return 1


def _collect(path: str | Path) -> list[Path] | None:
    try:
        return collect_cli_sources(path, suffixes=_MSCZ_SUFFIXES)
    except InputPathError as exc:
        print(str(exc), file=sys.stderr)
        return None


def _reject_multi_output(files: list[Path], output: str | None) -> bool:
    if len(files) > 1 and output:
        print(
            "-o/--output is alleen toegestaan bij precies één bronbestand "
            "(bij een map: sibling-output per bron).",
            file=sys.stderr,
        )
        return True
    return False


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mscz",
        description=(
            "Conversies met .mscz als bron. "
            "Zie docs/plans/mvsa-conversions.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "subcommando's:\n"
            "  mvsa PATH [--pitch {doremi,a-g,vsa,ag-vsa}] [-o OUT]\n"
            "      Naar .mvsa (werkbank-schets; default --pitch: ag-vsa).\n"
            "  import PATH …\n"
            "      .mvsa/.mxl → .mscz (catalogus-vrij; = mvsa mscz / mxl mscz).\n"
            "  products PATH [--force] [--dry-run] [--skip-svg]\n"
            "      Universele standaardproducten + products-meta.json.\n"
            "  mxl|svg|pdf|mp3|ogg|wav|score-ir|mscz|text PATH …\n"
            "      Individuele producten (alleen .mscz).\n"
            "  normalize PATH …\n"
            "      Layoutprofiel op bestaand .mscz.\n"
            "  compare SCORE MVSA …\n"
            "      SCORE = .mscz of MusicXML.\n"
            "\n"
            "PATH = één .mscz of map (recursief). -o alleen bij één bron.\n"
            "\n"
            "voorbeelden:\n"
            "  mscz mp3 lied.mscz --force\n"
            "  mscz products lied.mscz --force\n"
            "  mscz text lied.mscz\n"
            "  mscz score-ir lied.mscz --musicxml\n"
        ),
    )
    sub = parser.add_subparsers(
        dest="mscz_command",
        required=True,
        metavar="{mvsa,import,mxl,svg,pdf,mp3,ogg,wav,score-ir,mscz,normalize,text,compare,products}",
    )
    to_mvsa = sub.add_parser(
        "mvsa",
        help="Converteer .mscz naar .mvsa (werkbank).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    to_mvsa.add_argument(
        "path",
        help=".mscz-bestand of map met .mscz-bestanden (recursief).",
    )
    add_score_to_mvsa_arguments(to_mvsa)
    to_mvsa.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore-executable (default: auto).",
    )

    from .cli import _add_partituur_style_args
    from .cli_import import add_mscz_import_parser
    from .mscz_layout import MSCZ_LAYOUT_PROFILES
    from .street_products import add_products_parser

    add_mscz_import_parser(sub, add_style_args=_add_partituur_style_args)
    add_products_parser(sub, street="mscz", with_skip_svg=True)

    mxl = sub.add_parser(
        "mxl",
        help="Exporteer .mscz naar .mxl via MuseScore.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mxl.add_argument(
        "path",
        help=".mscz-bestand of map met .mscz-bestanden (recursief).",
    )
    mxl.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoer-.mxl (default: sibling <bronnaam>.mxl). "
            "Alleen bij precies één bronbestand."
        ),
    )
    mxl.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore-executable (default: auto).",
    )

    svg = sub.add_parser(
        "svg",
        help="Exporteer .mscz naar kale muziek-SVG (koormap).",
        description=(
            "Kale muziek-SVG via MuseScore: blad-chrome op tijdelijke kopie "
            "gestript (bron-.mscz ongewijzigd), daarna viewBox-trim. "
            "Vereist MuseScore 4. Cross-street: niet via mvsa svg."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mscz svg lied.mscz\n"
            "  mscz svg lied.mscz -o generated\\lied.svg\n"
            "  mscz svg lied.mscz --transparent\n"
            "  mscz svg map-met-mscz\\\n"
        ),
    )
    svg.add_argument(
        "path",
        help=".mscz-bestand of map met .mscz-bestanden (recursief).",
    )
    svg.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoer-.svg (default: sibling <bronnaam>.svg). "
            "Alleen bij precies één bronbestand."
        ),
    )
    svg.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore-executable (default: auto).",
    )
    svg.add_argument(
        "--no-trim",
        action="store_true",
        help="Sla viewBox-trim over (tall compacte SVG blijft één bestand).",
    )
    svg.add_argument(
        "--transparent",
        action="store_true",
        help=(
            "Geen witte achtergrond na trim (transparant). "
            "Default: witte rechthoek achter de notatie."
        ),
    )

    pdf = sub.add_parser(
        "pdf",
        help="Exporteer .mscz naar print-PDF voor zangers.",
        description=(
            "Print-PDF via MuseScore CLI (partituur zoals in het .mscz). "
            "Vereist MuseScore 4 (of 3). Cross-street: niet via mvsa pdf."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mscz pdf lied.mscz\n"
            "  mscz pdf lied.mscz -o generated\\lied.pdf\n"
            "  mscz pdf map-met-mscz\\\n"
        ),
    )
    pdf.add_argument(
        "path",
        help=".mscz-bestand of map met .mscz-bestanden (recursief).",
    )
    pdf.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoer-.pdf (default: sibling <bronnaam>.pdf). "
            "Alleen bij precies één bronbestand."
        ),
    )
    pdf.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore-executable (default: auto).",
    )

    from .audio_export import AUDIO_FORMATS

    for format_name in AUDIO_FORMATS:
        audio_p = sub.add_parser(
            format_name,
            help=f"Exporteer .mscz naar preview-audio (.{format_name}).",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        audio_p.add_argument(
            "path",
            help=".mscz-bestand of map met .mscz-bestanden (recursief).",
        )
        audio_p.add_argument(
            "-o",
            "--output",
            default=None,
            help=(
                f"Uitvoer (default: sibling .{format_name}). "
                "Alleen bij precies één bronbestand."
            ),
        )
        audio_p.add_argument(
            "--musescore",
            default=None,
            help="Pad naar MuseScore-executable (default: auto).",
        )

    score_ir = sub.add_parser(
        "score-ir",
        help="Exporteer Score-IR (+ optioneel from-ir MusicXML).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    score_ir.add_argument(
        "path",
        help=".mscz-bestand of map met .mscz-bestanden (recursief).",
    )
    score_ir.add_argument(
        "-o",
        "--output",
        default=None,
        help="Uitvoer Score-IR JSON (default: sibling .score-ir.json).",
    )
    score_ir.add_argument(
        "--musicxml",
        nargs="?",
        const="",
        default=None,
        metavar="PATH",
        help=(
            "Schrijf ook from-ir MusicXML. Zonder PATH: sibling "
            ".from-ir.musicxml."
        ),
    )
    score_ir.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore-executable (default: auto).",
    )

    mscz_prod = sub.add_parser(
        "mscz",
        help="Partituur-conform .mscz-sibling (layout partituur).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mscz_prod.add_argument(
        "path",
        help=".mscz-bestand of map met .mscz-bestanden (recursief).",
    )
    mscz_prod.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoer (default: sibling <bronnaam>.mscz). "
            "Alleen bij precies één bronbestand."
        ),
    )
    mscz_prod.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore (ongebruikt bij pure normalize; default: auto).",
    )

    normalize = sub.add_parser(
        "normalize",
        help="Pas layoutprofiel/leesbaarheid toe op bestaand .mscz.",
        description=(
            "Past een MSCZ-layoutprofiel toe op een bestaand .mscz "
            "(checklist S* + leesbaarheid). Default: partituur. "
            "Geen MuseScore-CLI nodig. Zie docs/formats/mscz-leesbaarheid.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mscz normalize lied.mscz\n"
            "  mscz normalize lied.mscz -o generated\\lied.partituur.mscz\n"
            "  mscz normalize lied.mscz --layout muziek\n"
            "  mscz normalize lied.mscz --layout partituur --compact\n"
            "  mscz normalize lied.mscz --bibliotheek-id zangstuk/var/uv\n"
        ),
    )
    normalize.add_argument(
        "path",
        help=".mscz-bestand of map met .mscz-bestanden (recursief).",
    )
    normalize.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoer-.mscz (default: overschrijf elke bron). "
            "Alleen bij precies één bronbestand."
        ),
    )
    normalize.add_argument(
        "--layout",
        metavar="PROFILE",
        default=None,
        choices=list(MSCZ_LAYOUT_PROFILES),
        help=(
            "MSCZ-layoutprofiel: partituur (default; A4/leesbaarheid/colofon), "
            "muziek (zelfde zonder titel/colofon), of plain (geen nabewerking)."
        ),
    )
    normalize.add_argument(
        "--bibliotheek-id",
        metavar="ID",
        default=None,
        dest="bibliotheek_id",
        help=(
            "Expliciete bibliotheek-id voor colofon (profiel partituur). "
            "Consumer bepaalt de id."
        ),
    )
    _add_partituur_style_args(normalize)

    text = sub.add_parser(
        "text",
        help="Lyrics-product: sibling .lyrics.txt (+ meta).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Default: sibling <bronnaam>.lyrics.txt + products-meta key lyrics.\n"
            "Alleen .mscz (straat-puur)."
        ),
    )
    text.add_argument(
        "path",
        help=".mscz-bestand of map met .mscz-bestanden (recursief).",
    )
    text.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoer (default: sibling .lyrics.txt). "
            "Alleen bij precies één bronbestand."
        ),
    )
    text.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore-executable (default: auto).",
    )

    compare = sub.add_parser(
        "compare",
        help=(
            "Vergelijk .mvsa met verse import van .mscz/MusicXML "
            "(lyrics, toonhoogte, duur, import-gaten)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Controleert of het .mvsa nog overeenkomt met wat mscz mvsa /\n"
            "mxl mvsa nu uit de score zou maken. Rapporteert:\n"
            "  1) lyrics (inhoud; leestekens genegeerd)\n"
            "  2) toonhoogte per stem S/A/T/B\n"
            "  3) duur (informatief; met --strict-duration in exitcode)\n"
            "  4) import-gaten (@tempo, @tekst, @speelplan, @composer, …)\n"
            "\n"
            "Exitcode 0 als lyrics-inhoud én toonhoogte kloppen; 1 bij\n"
            "verschil of fout. Coria-.mxl met [PAUZE]: waarschuwing + strip.\n"
            "\n"
            "SCORE mag .mscz, .mxl, .musicxml of .xml zijn.\n"
            "\n"
            "voorbeelden:\n"
            "  mscz compare lied.mscz lied.mscz.mvsa\n"
            "  mscz compare lied.mscz.mxl lied.mscz.mvsa\n"
            "  mscz compare lied.mscz lied.mscz.mvsa --strict-duration\n"
        ),
    )
    compare.add_argument(
        "score",
        help=".mscz- of MusicXML-bestand (bronpartituur).",
    )
    compare.add_argument(
        "mvsa",
        help=".mvsa-bestand om mee te vergelijken (bijv. import-sibling).",
    )
    compare.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore-executable (alleen bij .mscz; default: auto).",
    )
    compare.add_argument(
        "--pitch",
        default=None,
        metavar="FORM",
        help=(
            "Pitch-vorm voor de verse referentie-import "
            "(default: zelfde als mscz mvsa, ag-vsa)."
        ),
    )
    compare.add_argument(
        "--strict-duration",
        action="store_true",
        help="Laat duurverschillen de exitcode 1 maken (standaard alleen info).",
    )
    return parser


def _cmd_mscz_compare(ns: argparse.Namespace) -> int:
    from .mscz_compare import MsczCompareError, compare_score_to_mvsa, format_report

    musescore = Path(ns.musescore) if ns.musescore else None
    try:
        report = compare_score_to_mvsa(
            Path(ns.score),
            Path(ns.mvsa),
            musescore=musescore,
            pitch=ns.pitch,
            strict_duration=bool(ns.strict_duration),
        )
    except MsczCompareError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    sys.stdout.write(format_report(report))
    return 0 if report.musical_ok else 1


def _cmd_mscz_to_mxl(ns: argparse.Namespace) -> int:
    from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError
    from .musicxml_playback_normalize import export_mscz_to_playback_mxl
    from .street_products import MSCZ_CORE_KEYS, merge_street_product_meta

    files = _collect(ns.path)
    if files is None:
        return 1
    if _reject_multi_output(files, ns.output):
        return 1
    musescore = Path(ns.musescore) if ns.musescore else None
    exit_code = 0
    for path in files:
        out = Path(ns.output) if ns.output else derived_output_path(path, ".mxl")
        try:
            export_mscz_to_playback_mxl(path, out, musescore=musescore)
        except (MuseScoreNotFoundError, MuseScoreConvertError) as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        except Exception as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"Geschreven: {out}")
        meta = merge_street_product_meta(path, {MSCZ_CORE_KEYS[0]: out})
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_mscz_svg(ns: argparse.Namespace) -> int:
    from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError
    from .mvsa_mscz import MvsaMsczError, export_mscz_to_svg
    from .street_products import merge_street_product_meta, svg_meta_products

    files = _collect(ns.path)
    if files is None:
        return 1
    if _reject_multi_output(files, ns.output):
        return 1
    musescore = Path(ns.musescore) if ns.musescore else None
    trim = not bool(ns.no_trim)
    white_background = not bool(ns.transparent)
    exit_code = 0
    for path in files:
        out = Path(ns.output) if ns.output else derived_output_path(path, ".svg")
        try:
            written = export_mscz_to_svg(
                path,
                out,
                musescore=musescore,
                trim=trim,
                white_background=white_background,
            )
        except (MvsaMsczError, MuseScoreNotFoundError, MuseScoreConvertError) as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        except Exception as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        for written_path in written:
            print(f"Geschreven: {written_path}")
        products, drop = svg_meta_products(path, written)
        meta = merge_street_product_meta(path, products, drop_keys=drop or None)
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_mscz_pdf(ns: argparse.Namespace) -> int:
    from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError
    from .mvsa_mscz import MvsaMsczError, export_mscz_to_pdf
    from .street_products import MSCZ_PDF_KEY, merge_street_product_meta

    files = _collect(ns.path)
    if files is None:
        return 1
    if _reject_multi_output(files, ns.output):
        return 1
    musescore = Path(ns.musescore) if ns.musescore else None
    exit_code = 0
    for path in files:
        out = Path(ns.output) if ns.output else derived_output_path(path, ".pdf")
        try:
            export_mscz_to_pdf(path, out, musescore=musescore)
        except (MvsaMsczError, MuseScoreNotFoundError, MuseScoreConvertError) as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        except Exception as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"Geschreven: {out}")
        meta = merge_street_product_meta(path, {MSCZ_PDF_KEY: out})
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_mscz_normalize(ns: argparse.Namespace) -> int:
    from .cli_import import _partituur_style_kwargs
    from .mscz_layout import MsczLayoutError, normalize_mscz_path
    from .mscz_partituur import (
        MsczPartituurError,
        build_partituur_style_overrides,
    )

    files = _collect(ns.path)
    if files is None:
        return 1
    if _reject_multi_output(files, ns.output):
        return 1
    try:
        style_overrides = build_partituur_style_overrides(**_partituur_style_kwargs(ns))
    except MsczPartituurError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    exit_code = 0
    for path in files:
        out = Path(ns.output) if ns.output else None
        try:
            written, profile = normalize_mscz_path(
                path,
                out,
                layout=ns.layout,
                bibliotheek_id=ns.bibliotheek_id,
                style_overrides=style_overrides or None,
            )
        except (MsczLayoutError, MsczPartituurError) as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        except Exception as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"Geschreven: {written} (layout {profile})")
    return exit_code


def _cmd_mscz_text(ns: argparse.Namespace) -> int:
    from .street_product_export import write_lyrics_product
    from .street_products import LYRICS_KEY, merge_street_product_meta

    files = _collect(ns.path)
    if files is None:
        return 1
    if _reject_multi_output(files, ns.output):
        return 1
    musescore = Path(ns.musescore) if ns.musescore else None
    exit_code = 0
    for path in files:
        out = (
            Path(ns.output)
            if ns.output
            else derived_output_path(path, ".lyrics.txt")
        )
        try:
            written = write_lyrics_product(path, out, musescore=musescore)
        except Exception as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"Geschreven: {written}")
        meta = merge_street_product_meta(path, {LYRICS_KEY: written})
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_mscz_audio(ns: argparse.Namespace) -> int:
    from .audio_export import AUDIO_FORMATS, AudioExportError, export_to_audio
    from .street_products import MP3_KEY, merge_street_product_meta

    fmt = ns.mscz_command
    if fmt not in AUDIO_FORMATS:
        fmt = "mp3"
    files = _collect(ns.path)
    if files is None:
        return 1
    if _reject_multi_output(files, ns.output):
        return 1
    musescore = Path(ns.musescore) if ns.musescore else None
    exit_code = 0
    for path in files:
        out = (
            Path(ns.output)
            if ns.output
            else derived_output_path(path, f".{fmt}")
        )
        try:
            written = export_to_audio(
                path, out, format_name=fmt, musescore=musescore
            )
        except AudioExportError as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        except Exception as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"Geschreven: {written}")
        if fmt == "mp3":
            meta = merge_street_product_meta(path, {MP3_KEY: written})
            if meta is not None:
                print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_mscz_score_ir(ns: argparse.Namespace) -> int:
    from .score_ir_musicxml import (
        ScoreIrMusicxmlError,
        export_score_ir_path_to_musicxml,
    )
    from .street_product_export import (
        StreetProductExportError,
        export_bron_to_score_ir,
    )
    from .street_products import merge_street_product_meta

    files = _collect(ns.path)
    if files is None:
        return 1
    if _reject_multi_output(files, ns.output):
        return 1
    musescore = Path(ns.musescore) if ns.musescore else None
    mxl_opt = getattr(ns, "musicxml", None)
    exit_code = 0
    for path in files:
        out = (
            Path(ns.output)
            if ns.output
            else derived_output_path(path, ".score-ir.json")
        )
        mxl_path = None
        if mxl_opt is not None:
            if mxl_opt == "":
                mxl_path = derived_output_path(path, ".from-ir.musicxml")
            else:
                mxl_path = Path(mxl_opt)
        try:
            export_bron_to_score_ir(path, out, musescore=musescore)
            if mxl_path is not None:
                export_score_ir_path_to_musicxml(out, mxl_path)
        except (StreetProductExportError, ScoreIrMusicxmlError) as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        except Exception as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"Geschreven: {out}")
        meta_products: dict[str, Path] = {"score-ir": out}
        if mxl_path is not None:
            print(f"MusicXML: {mxl_path}")
            meta_products["from-ir"] = mxl_path
        meta = merge_street_product_meta(path, meta_products)
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_mscz_product(ns: argparse.Namespace) -> int:
    """Partituur-sibling ``*.mscz.mscz`` (meta-key ``mscz``)."""
    from .street_product_export import (
        StreetProductExportError,
        export_bron_to_mscz_product,
    )
    from .street_products import MSCZ_PRODUCT_KEY, merge_street_product_meta

    files = _collect(ns.path)
    if files is None:
        return 1
    if _reject_multi_output(files, ns.output):
        return 1
    musescore = Path(ns.musescore) if ns.musescore else None
    exit_code = 0
    for path in files:
        out = (
            Path(ns.output)
            if ns.output
            else derived_output_path(path, ".mscz")
        )
        try:
            written = export_bron_to_mscz_product(
                path, out, musescore=musescore
            )
        except StreetProductExportError as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        except Exception as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"Geschreven: {written}")
        meta = merge_street_product_meta(path, {MSCZ_PRODUCT_KEY: written})
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
