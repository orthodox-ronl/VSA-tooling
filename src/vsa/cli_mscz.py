"""Top-level ``mscz`` CLI (bron: ``.mscz``).

Acties: mvsa (score → werkbank); import (.mvsa/.mxl → .mscz); mxl; text;
compare (score ↔ ``.mvsa``).
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
            "  mscz text lied.mscz -o lied.lyrics.txt\n"
            "  mscz compare lied.mscz lied.mscz.mvsa\n"
            "\n"
            "Alias text: vsa text … (ook .mxl / .vsa / .mvsa)."
        ),
    )
    sub = parser.add_subparsers(
        dest="mscz_command",
        required=True,
        metavar="{mvsa,import,mxl,text,compare,products}",
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
