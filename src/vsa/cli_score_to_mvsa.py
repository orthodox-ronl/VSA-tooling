"""Shared CLI: ``{mxl|mscz} mvsa`` — score → werkbank-``.mvsa``.

Conventie: eerste token = brontype, tweede = doeltype (geen ``import``).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .derived_path import derived_output_path
from .input_paths import InputPathError, collect_cli_sources


def add_score_to_mvsa_arguments(parser: argparse.ArgumentParser) -> None:
    """Common flags for ``mxl mvsa`` / ``mscz mvsa``."""
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoer-.mvsa (default: sibling <bronnaam>.mvsa, bijv. "
            "lied.mscz.mvsa). Alleen bij precies één bronbestand."
        ),
    )
    parser.add_argument(
        "--pitch",
        choices=["doremi", "a-g", "abc", "vsa", "ag-vsa"],
        default="ag-vsa",
        help=(
            "Doel-spelling (default: ag-vsa). "
            "a-g = toonnamen met cijfer; abc = alias."
        ),
    )
    parser.add_argument(
        "--do",
        metavar="PITCH",
        default=None,
        help="Forceer @do (bijv. F4). Zonder: uit KeySig/fifths.",
    )
    parser.add_argument(
        "--octave-style",
        choices=["@oct", "marker"],
        default="@oct",
        help="Schrijfoctaaf-stijl (default: @oct).",
    )
    parser.add_argument(
        "--section",
        default="schets",
        help="Id voor @sectie in de output (default: schets).",
    )
    parser.add_argument(
        "--no-align",
        action="store_true",
        help="Sla canonieke kolomuitlijning over.",
    )


def run_score_to_mvsa(
    ns: argparse.Namespace,
    *,
    suffixes: tuple[str, ...],
) -> int:
    """Convert score file(s) to ``.mvsa``; default out = ``stem.brontype.mvsa``."""
    from .mvsa_import import MvsaImportError, import_score_path
    from .mvsa_partituur_stamp import is_mscz_import_mvsa, stamp_mscz_import_mvsa

    try:
        files = collect_cli_sources(ns.path, suffixes=suffixes)
    except InputPathError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if len(files) > 1 and ns.output:
        print(
            "-o/--output is alleen toegestaan bij precies één bronbestand "
            "(bij een map: sibling-output per bron).",
            file=sys.stderr,
        )
        return 1
    musescore = Path(ns.musescore) if getattr(ns, "musescore", None) else None
    exit_code = 0
    for path in files:
        out = (
            Path(ns.output)
            if ns.output
            else derived_output_path(path, ".mvsa")
        )
        try:
            import_score_path(
                path,
                out,
                pitch=ns.pitch,
                octave_style=ns.octave_style,
                align=not ns.no_align,
                section_id=ns.section,
                musescore=musescore,
                do=getattr(ns, "do", None),
            )
        except MvsaImportError as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        # Bibliotheek-importcontrole: sibling *.mscz.mvsa krijgt partituur-hash.
        if path.suffix.lower() == ".mscz" and is_mscz_import_mvsa(out):
            stamp_mscz_import_mvsa(out, path)
        print(f"Geschreven: {out}")
    return exit_code
