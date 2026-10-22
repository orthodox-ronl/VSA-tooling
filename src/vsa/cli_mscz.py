"""Top-level ``mscz`` CLI (bron: ``.mscz``).

Acties: import -> mvsa; mxl (via MuseScore); text (lyrics via temp-mxl).
Zie docs/plans/mvsa-conversions.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .derived_path import derived_output_path
from .input_paths import InputPathError, collect_cli_sources

_MSCZ_SUFFIXES = (".mscz",)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()
    ns = parser.parse_args(args)
    if ns.mscz_command == "import":
        from .cli import main as vsa_main

        forwarded = ["mvsa", "import", ns.path, "--pitch", ns.pitch or "ag-vsa"]
        if ns.output:
            forwarded.extend(["-o", ns.output])
        if ns.do:
            forwarded.extend(["--do", ns.do])
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
    if ns.mscz_command == "text":
        return _cmd_mscz_text(ns)
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
            "  import PATH [--pitch {doremi,a-g,vsa,ag-vsa}] [-o OUT]\n"
            "      Importeer naar .mvsa (default --pitch: ag-vsa).\n"
            "  mxl PATH [-o OUT] [--musescore PATH]\n"
            "      Exporteer naar .mxl via MuseScore.\n"
            "  text PATH [-o OUT] [--musescore PATH]\n"
            "      Platte gezongen tekst (via temp-.mxl; geen .mvsa).\n"
            "\n"
            "PATH = één .mscz of map (recursief). "
            "-o alleen bij precies één bron.\n"
            "\n"
            "voorbeelden:\n"
            "  mscz import lied.mscz -o lied.mvsa\n"
            "  mscz import lied.mscz --pitch doremi -o lied.mvsa\n"
            "  mscz mxl lied.mscz -o lied.mxl\n"
            "  mscz text lied.mscz -o lied.lyrics.txt\n"
            "\n"
            "Alias import: vsa mvsa import …\n"
            "Alias text: vsa text … (ook .mxl / .vsa / .mvsa)."
        ),
    )
    sub = parser.add_subparsers(
        dest="mscz_command",
        required=True,
        metavar="{import,mxl,text}",
    )
    imp = sub.add_parser(
        "import",
        help="Importeer .mscz naar .mvsa.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    imp.add_argument(
        "path",
        help=".mscz-bestand of map met .mscz-bestanden (recursief; zelfde batch als mvsa import).",
    )
    imp.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoer-.mvsa (default: <stem>.import.mvsa per bron). "
            "Alleen bij precies één bronbestand."
        ),
    )
    imp.add_argument(
        "--pitch",
        choices=["doremi", "a-g", "abc", "vsa", "ag-vsa"],
        default="ag-vsa",
        help=(
            "Doel-spelling (default: ag-vsa). "
            "a-g = toonnamen met cijfer; abc = alias."
        ),
    )
    imp.add_argument(
        "--do",
        metavar="PITCH",
        default=None,
        help="Forceer @do (bijv. F4). Zonder: uit KeySig/fifths.",
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
            "Schrijft geen import-sibling (.mvsa).\n"
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
    return parser


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
