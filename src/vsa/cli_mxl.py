"""Top-level ``mxl`` CLI (bron: ``.mxl`` / ``.musicxml``).

Acties: import -> mvsa; mscz (via MuseScore). Zie docs/plans/mvsa-conversions.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()
    ns = parser.parse_args(args)
    if ns.mxl_command == "import":
        from .cli import main as vsa_main

        forwarded = ["mvsa", "import", ns.path, "--pitch", ns.pitch]
        if ns.output:
            forwarded.extend(["-o", ns.output])
        if ns.octave_style:
            forwarded.extend(["--octave-style", ns.octave_style])
        if ns.section:
            forwarded.extend(["--section", ns.section])
        if ns.no_align:
            forwarded.append("--no-align")
        return vsa_main(forwarded)
    if ns.mxl_command == "mscz":
        return _cmd_mxl_to_mscz(ns)
    parser.print_help()
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mxl",
        description=(
            "Conversies met .mxl / .musicxml als bron. "
            "Zie docs/plans/mvsa-conversions.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "subcommando's:\n"
            "  import PATH --pitch {doremi,a-g,vsa} [-o OUT]\n"
            "      Importeer naar .mvsa.\n"
            "  mscz PATH [-o OUT] [--musescore PATH]\n"
            "      Converteer naar .mscz via MuseScore.\n"
            "\n"
            "voorbeelden:\n"
            "  mxl import lied.mxl --pitch doremi -o lied.mvsa\n"
            "  mxl mscz lied.mxl -o lied.mscz\n"
            "\n"
            "Alias: vsa mvsa import … (zelfde import-pad)."
        ),
    )
    sub = parser.add_subparsers(
        dest="mxl_command",
        required=True,
        metavar="{import,mscz}",
    )
    imp = sub.add_parser(
        "import",
        help="Importeer .mxl/.musicxml naar .mvsa.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    imp.add_argument("path", help=".mxl, .musicxml of .xml bronbestand.")
    imp.add_argument(
        "-o",
        "--output",
        default=None,
        help="Uitvoer-.mvsa (default: <stem>.import.mvsa).",
    )
    imp.add_argument(
        "--pitch",
        choices=["doremi", "a-g", "abc", "vsa"],
        required=True,
        help="Doel-spelling (a-g = toonnamen met cijfer; abc = alias).",
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
        "--no-align",
        action="store_true",
        help="Sla canonieke kolomuitlijning over.",
    )

    mscz = sub.add_parser(
        "mscz",
        help="Converteer .mxl naar .mscz via MuseScore.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mscz.add_argument("path", help=".mxl / .musicxml bronbestand.")
    mscz.add_argument(
        "-o",
        "--output",
        default=None,
        help="Uitvoer-.mscz (default: <stem>.mscz).",
    )
    mscz.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore-executable (default: auto).",
    )
    return parser


def _cmd_mxl_to_mscz(ns: argparse.Namespace) -> int:
    import os
    import tempfile

    from .mscz_partituur import MsczPartituurError, apply_partituur_mscz_conventions
    from .musicxml_package import write_musicxml_output
    from .musicxml_satb_layout import ensure_partituur_musicxml
    from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError, convert_with_musescore
    from .mvsa_import import read_musicxml_file

    path = Path(ns.path)
    if not path.is_file():
        print(f"Bestand niet gevonden: {path}", file=sys.stderr)
        return 1
    if path.suffix.lower() not in {".mxl", ".musicxml", ".xml"}:
        print(
            f"Verwacht .mxl/.musicxml/.xml als bron; kreeg {path.suffix!r}",
            file=sys.stderr,
        )
        return 1
    out = Path(ns.output) if ns.output else path.with_suffix(".mscz")
    if out.suffix.lower() != ".mscz":
        out = out.with_suffix(".mscz")
    musescore = Path(ns.musescore) if ns.musescore else None

    fd, tmp_name = tempfile.mkstemp(suffix=".mxl", prefix="mxl-partituur-")
    os.close(fd)
    tmp_mxl = Path(tmp_name)
    try:
        try:
            xml = read_musicxml_file(path)
            partituur = ensure_partituur_musicxml(xml)
            write_musicxml_output(tmp_mxl, partituur)
            convert_with_musescore(tmp_mxl, out, musescore=musescore)
            apply_partituur_mscz_conventions(out)
        except (MuseScoreNotFoundError, MuseScoreConvertError, MsczPartituurError) as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            return 1
    finally:
        tmp_mxl.unlink(missing_ok=True)
    print(f"Geschreven: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
