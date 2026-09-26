"""Top-level ``mscz`` CLI (bron: ``.mscz``).

Acties: import -> mvsa; mxl (via MuseScore). Zie docs/plans/mvsa-conversions.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()
    ns = parser.parse_args(args)
    if ns.mscz_command == "import":
        from .cli import main as vsa_main

        forwarded = ["mvsa", "import", ns.path, "--pitch", ns.pitch]
        if ns.output:
            forwarded.extend(["-o", ns.output])
        if ns.octave_style:
            forwarded.extend(["--octave-style", ns.octave_style])
        if ns.section:
            forwarded.extend(["--section", ns.section])
        if ns.musescore:
            forwarded.extend(["--musescore", ns.musescore])
        if ns.no_align:
            forwarded.append("--no-align")
        return vsa_main(forwarded)
    if ns.mscz_command == "mxl":
        return _cmd_mscz_to_mxl(ns)
    parser.print_help()
    return 1


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
            "  import PATH --pitch {doremi,abc,vsa} [-o OUT]\n"
            "      Importeer naar .mvsa (via MuseScore -> mxl).\n"
            "  mxl PATH [-o OUT] [--musescore PATH]\n"
            "      Exporteer naar .mxl via MuseScore.\n"
            "\n"
            "voorbeelden:\n"
            "  mscz import lied.mscz --pitch doremi -o lied.mvsa\n"
            "  mscz mxl lied.mscz -o lied.mxl\n"
            "\n"
            "Alias: vsa mvsa import … (zelfde import-pad)."
        ),
    )
    sub = parser.add_subparsers(
        dest="mscz_command",
        required=True,
        metavar="{import,mxl}",
    )
    imp = sub.add_parser(
        "import",
        help="Importeer .mscz naar .mvsa.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    imp.add_argument("path", help=".mscz bronbestand.")
    imp.add_argument(
        "-o",
        "--output",
        default=None,
        help="Uitvoer-.mvsa (default: <stem>.import.mvsa).",
    )
    imp.add_argument(
        "--pitch",
        choices=["doremi", "abc", "vsa"],
        required=True,
        help="Doel-spelling op stemregels.",
    )
    imp.add_argument(
        "--octave-style",
        choices=["@oct", "marker"],
        default="@oct",
        help="Schrijfoctaaf-stijl (default: @oct).",
    )
    imp.add_argument(
        "--section",
        default="import",
        help="Id voor @sectie in de output (default: import).",
    )
    imp.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore-executable (default: auto).",
    )
    imp.add_argument(
        "--no-align",
        action="store_true",
        help="Sla canonieke kolomuitlijning over.",
    )

    mxl = sub.add_parser(
        "mxl",
        help="Exporteer .mscz naar .mxl via MuseScore.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mxl.add_argument("path", help=".mscz bronbestand.")
    mxl.add_argument(
        "-o",
        "--output",
        default=None,
        help="Uitvoer-.mxl (default: <stem>.mxl).",
    )
    mxl.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore-executable (default: auto).",
    )
    return parser


def _cmd_mscz_to_mxl(ns: argparse.Namespace) -> int:
    from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError, convert_with_musescore

    path = Path(ns.path)
    if not path.is_file():
        print(f"Bestand niet gevonden: {path}", file=sys.stderr)
        return 1
    if path.suffix.lower() != ".mscz":
        print(f"Verwacht .mscz als bron; kreeg {path.suffix!r}", file=sys.stderr)
        return 1
    out = Path(ns.output) if ns.output else path.with_suffix(".mxl")
    if out.suffix.lower() not in {".mxl", ".musicxml", ".xml"}:
        out = out.with_suffix(".mxl")
    musescore = Path(ns.musescore) if ns.musescore else None
    try:
        convert_with_musescore(path, out, musescore=musescore)
    except (MuseScoreNotFoundError, MuseScoreConvertError) as exc:
        print(f"{path}: ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Geschreven: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
