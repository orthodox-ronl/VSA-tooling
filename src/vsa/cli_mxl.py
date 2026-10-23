"""Top-level ``mxl`` CLI (bron: ``.mxl`` / ``.musicxml``).

Acties: mvsa (score → werkbank); mscz (via MuseScore); validate / normalize.
Conventie: ``mxl {doeltype}`` — zie docs/plans/mvsa-conversions.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cli_score_to_mvsa import add_score_to_mvsa_arguments, run_score_to_mvsa
from .derived_path import derived_output_path
from .input_paths import InputPathError, collect_cli_sources

_MXL_SUFFIXES = (".mxl", ".musicxml", ".xml")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()
    ns = parser.parse_args(args)
    if ns.mxl_command == "mvsa":
        return run_score_to_mvsa(ns, suffixes=_MXL_SUFFIXES)
    if ns.mxl_command == "mscz":
        return _cmd_mxl_to_mscz(ns)
    if ns.mxl_command == "validate":
        return _cmd_mxl_validate(ns)
    if ns.mxl_command == "normalize":
        return _cmd_mxl_normalize(ns)
    parser.print_help()
    return 1


def _collect(path: str | Path) -> list[Path] | None:
    try:
        return collect_cli_sources(path, suffixes=_MXL_SUFFIXES)
    except InputPathError as exc:
        print(str(exc), file=sys.stderr)
        return None


def _reject_multi_output(files: list[Path], output: str | None) -> bool:
    if len(files) > 1 and output:
        print(
            "-o/--output is alleen toegestaan bij precies één bronbestand "
            "(bij een map: sibling- of in-place-output per bron).",
            file=sys.stderr,
        )
        return True
    return False


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mxl",
        description=(
            "Conversies en playback-gates met .mxl / .musicxml als bron. "
            "Zie docs/plans/mvsa-conversions.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "subcommando's:\n"
            "  mvsa PATH [--pitch {doremi,a-g,vsa,ag-vsa}] [-o OUT]\n"
            "      Naar .mvsa (werkbank-schets; default --pitch: ag-vsa).\n"
            "  mscz PATH [-o OUT] [--musescore PATH]\n"
            "      Converteer naar .mscz via MuseScore.\n"
            "  validate PATH [--profile {satb,mono}]\n"
            "      Checklist Coria/playback (M2/M8/Coria-tags/meta).\n"
            "  normalize PATH [-o OUT] [--apply-timing]\n"
            "      Normaliseer naar playback-profiel.\n"
            "\n"
            "PATH = één bronbestand of map (recursief). "
            "-o alleen bij precies één bron.\n"
            "\n"
            "voorbeelden:\n"
            "  mxl mvsa lied.mxl\n"
            "  mxl mvsa lied.mxl -o lied.mvsa --pitch doremi\n"
            "  mxl mscz lied.mxl -o lied.mscz\n"
            "  mxl validate lied.mvsa.mxl --profile satb\n"
            "  mxl normalize raw.mxl -o out.mxl --apply-timing\n"
        ),
    )
    sub = parser.add_subparsers(
        dest="mxl_command",
        required=True,
        metavar="{mvsa,mscz,validate,normalize}",
    )
    to_mvsa = sub.add_parser(
        "mvsa",
        help="Converteer .mxl/.musicxml naar .mvsa (werkbank).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    to_mvsa.add_argument(
        "path",
        help=(
            ".mxl/.musicxml/.xml-bestand, of map met zulke bestanden "
            "(recursief)."
        ),
    )
    add_score_to_mvsa_arguments(to_mvsa)

    mscz = sub.add_parser(
        "mscz",
        help="Converteer .mxl naar .mscz via MuseScore.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mscz.add_argument(
        "path",
        help=".mxl/.musicxml/.xml-bestand, of map met zulke bestanden (recursief).",
    )
    mscz.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoer-.mscz (default: sibling <bronnaam>.mscz). "
            "Alleen bij precies één bronbestand."
        ),
    )
    mscz.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore-executable (default: auto).",
    )

    validate = sub.add_parser(
        "validate",
        help="Controleer Coria/playback-checklist (niet-muterend).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    validate.add_argument(
        "path",
        help=".mxl/.musicxml/.xml-bestand, of map met zulke bestanden (recursief).",
    )
    validate.add_argument(
        "--profile",
        choices=["satb", "mono"],
        default="satb",
        help="satb = vier parts (default); mono = eenstemmig .vsa.mxl.",
    )

    normalize = sub.add_parser(
        "normalize",
        help="Normaliseer naar Coria/playback-profiel.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    normalize.add_argument(
        "path",
        help=".mxl/.musicxml/.xml-bestand, of map met zulke bestanden (recursief).",
    )
    normalize.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoer (default: overschrijf elke bron). "
            "Alleen bij precies één bronbestand."
        ),
    )
    normalize.add_argument(
        "--apply-timing",
        action="store_true",
        help=(
            "Pauze/caesura + recite-explosie (MSCZ-roundtrip). "
            "Default uit (MVSA-achtige bron)."
        ),
    )
    return parser


def _cmd_mxl_validate(ns: argparse.Namespace) -> int:
    from .musicxml_playback_checklist import validate_playback_mxl_path

    files = _collect(ns.path)
    if files is None:
        return 1
    exit_code = 0
    for path in files:
        findings = validate_playback_mxl_path(path, profile=ns.profile)
        if not findings:
            print(f"OK ({ns.profile}): {path}")
            continue
        for f in findings:
            print(f"{path}: {f.code}: {f.message}", file=sys.stderr)
        print(f"{path}: {len(findings)} checklist-fout(en)", file=sys.stderr)
        exit_code = 1
    return exit_code


def _cmd_mxl_normalize(ns: argparse.Namespace) -> int:
    from .musicxml_playback_normalize import normalize_playback_mxl_path

    files = _collect(ns.path)
    if files is None:
        return 1
    if _reject_multi_output(files, ns.output):
        return 1
    exit_code = 0
    for path in files:
        out = Path(ns.output) if ns.output else path
        try:
            dest = normalize_playback_mxl_path(
                path,
                out,
                apply_timing=bool(ns.apply_timing),
            )
        except Exception as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"Geschreven: {dest}")
    return exit_code


def _cmd_mxl_to_mscz(ns: argparse.Namespace) -> int:
    import os
    import tempfile

    from .mscz_partituur import MsczPartituurError, apply_partituur_mscz_conventions
    from .musicxml_package import write_musicxml_output
    from .musicxml_satb_layout import ensure_partituur_musicxml
    from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError, convert_with_musescore
    from .mvsa_import import read_musicxml_file

    files = _collect(ns.path)
    if files is None:
        return 1
    if _reject_multi_output(files, ns.output):
        return 1
    musescore = Path(ns.musescore) if ns.musescore else None
    exit_code = 0
    for path in files:
        out = Path(ns.output) if ns.output else derived_output_path(path, ".mscz")
        if out.suffix.lower() != ".mscz":
            out = out.with_suffix(".mscz")

        fd, tmp_name = tempfile.mkstemp(suffix=".mxl", prefix="mxl-partituur-")
        os.close(fd)
        tmp_mxl = Path(tmp_name)
        try:
            try:
                xml = read_musicxml_file(path)
                partituur = ensure_partituur_musicxml(xml)
                write_musicxml_output(tmp_mxl, partituur)
                convert_with_musescore(
                    tmp_mxl,
                    out,
                    musescore=musescore,
                    musicxml_infer_text_type=True,
                )
                apply_partituur_mscz_conventions(out)
            except (MuseScoreNotFoundError, MuseScoreConvertError, MsczPartituurError) as exc:
                print(f"{path}: ERROR: {exc}", file=sys.stderr)
                exit_code = 1
                continue
            except Exception as exc:
                print(f"{path}: ERROR: {exc}", file=sys.stderr)
                exit_code = 1
                continue
        finally:
            tmp_mxl.unlink(missing_ok=True)
        print(f"Geschreven: {out}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
