"""Top-level ``mscz`` CLI (bron: ``.mscz``).

Acties: mvsa (score → werkbank); import (.mvsa/.mxl → .mscz); mxl; svg; pdf;
normalize; text; compare (score ↔ ``.mvsa``); products.
Conventie: ``mscz {doeltype}`` of ``mscz import`` — zie
docs/plans/mvsa-conversions.md · docs/formats/contract-index.md.
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
            "      Coria-.mxl (+ SVG) + products-meta.json.\n"
            "  mxl PATH [-o OUT] [--musescore PATH]\n"
            "      Exporteer naar .mxl via MuseScore.\n"
            "  svg PATH [-o OUT] [--musescore PATH] [--no-trim] [--transparent]\n"
            "      Kale muziek-SVG (chrome-strip op tijdelijke kopie).\n"
            "  pdf PATH [-o OUT] [--musescore PATH]\n"
            "      Print-PDF voor zangers (MuseScore).\n"
            "  normalize PATH [-o OUT] [--layout PROFILE] [--bibliotheek-id ID]\n"
            "      Leesbaarheid + layoutprofiel op bestaand .mscz "
            "(default partituur).\n"
            "  text PATH [-o OUT] [--musescore PATH]\n"
            "      Platte gezongen tekst (via temp-.mxl; geen .mvsa).\n"
            "  compare SCORE MVSA [--musescore PATH] [--pitch …]\n"
            "      [--strict-duration]\n"
            "      Vergelijk .mvsa met verse import van de score "
            "(+ import-gaten).\n"
            "\n"
            "PATH = één bronbestand of map (recursief). "
            "-o alleen bij precies één bron.\n"
            "compare: SCORE = .mscz of MusicXML; MVSA = .mvsa-bestand.\n"
            "\n"
            "voorbeelden:\n"
            "  mscz mvsa lied.mscz\n"
            "  mscz import lied.mvsa\n"
            "  mscz mxl lied.mscz -o lied.mxl\n"
            "  mscz svg lied.mscz -o lied.svg\n"
            "  mscz pdf lied.mscz -o lied.pdf\n"
            "  mscz normalize lied.mscz --layout partituur\n"
            "  mscz text lied.mscz -o lied.lyrics.txt\n"
            "  mscz compare lied.mscz lied.mscz.mvsa\n"
            "\n"
            "Alias text: vsa text … (ook .mxl / .vsa / .mvsa)."
        ),
    )
    sub = parser.add_subparsers(
        dest="mscz_command",
        required=True,
        metavar="{mvsa,import,mxl,svg,pdf,normalize,text,compare,products}",
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
        help="Laat MuseScore-A4-SVG ongewijzigd (geen viewBox-trim).",
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
        help="Platte gezongen tekst uit .mscz (via MuseScore; geen .mvsa).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Zelfde extractie als ``vsa text`` op MusicXML: eerste part met\n"
            "lyric number 1, lettergrepen samengevoegd tot woorden.\n"
            "Schrijft geen .mvsa-sibling.\n"
            "Bij een map: één run per .mscz; -o alleen bij één bronbestand."
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
            "Schrijf platte tekst naar dit bestand i.p.v. stdout. "
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
    """Forward naar ``vsa text`` per bronbestand (geen .mvsa)."""
    from .cli import main as vsa_main

    files = _collect(ns.path)
    if files is None:
        return 1
    if _reject_multi_output(files, ns.output):
        return 1
    exit_code = 0
    for path in files:
        forwarded = ["text", str(path)]
        if ns.output:
            forwarded.extend(["-o", ns.output])
        if ns.musescore:
            forwarded.extend(["--musescore", ns.musescore])
        if len(files) > 1:
            print(f"=== {path} ===", flush=True)
        rc = vsa_main(forwarded)
        if rc != 0:
            exit_code = rc
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
