"""Destination-street ``import``: alias of ``{bron} {doel}``.

Catalogus-vrij. Contract: docs/formats/contract-index.md ·
docs/plans/straat-clis.md.

======= ========== =========================
``doel`` ``bron``  Equivalent bestaand CLI
======= ========== =========================
``mvsa`` ``.mscz`` ``mscz mvsa``
``mvsa`` ``.mxl``  ``mxl mvsa``
``mscz`` ``.mvsa`` ``mvsa mscz``
``mscz`` ``.mxl``  ``mxl mscz``
======= ========== =========================
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cli_score_to_mvsa import add_score_to_mvsa_arguments, run_score_to_mvsa
from .derived_path import derived_output_path
from .input_paths import InputPathError, collect_cli_sources

_MXL_SUFFIXES = (".mxl", ".musicxml", ".xml")
_MVSA_IMPORT_SUFFIXES = (".mscz", *_MXL_SUFFIXES)
_MSCZ_FROM_MVSA = (".mvsa",)
_MSCZ_IMPORT_SUFFIXES = (".mvsa", *_MXL_SUFFIXES)


def _fmt_exts(suffixes: tuple[str, ...]) -> str:
    return ", ".join(suffixes)


def _reject_ext(street: str, path: Path, allowed: tuple[str, ...]) -> str:
    got = path.suffix.lower() or "(geen extensie)"
    return (
        f"{street} import: bestand {path.name} heeft extensie {got}, "
        f"die hier niet is toegestaan. Toegestaan: {_fmt_exts(allowed)}. "
        f"Zelfde conversie als '{{bron}} {street}' "
        f"(zie docs/formats/contract-index.md)."
    )


def run_mvsa_import(ns: argparse.Namespace) -> int:
    """``mvsa import`` → score → werkbank-``.mvsa``."""
    path = Path(ns.path)
    if path.is_file():
        suf = path.suffix.lower()
        if suf == ".mscz":
            return run_score_to_mvsa(ns, suffixes=(".mscz",))
        if suf in _MXL_SUFFIXES:
            return run_score_to_mvsa(ns, suffixes=_MXL_SUFFIXES)
        print(_reject_ext("mvsa", path, _MVSA_IMPORT_SUFFIXES), file=sys.stderr)
        return 1
    try:
        files = collect_cli_sources(ns.path, suffixes=_MVSA_IMPORT_SUFFIXES)
    except InputPathError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not files:
        print(
            f"mvsa import: geen .mscz/.mxl/.musicxml/.xml onder {ns.path}.",
            file=sys.stderr,
        )
        return 1
    if len(files) > 1 and ns.output:
        print(
            "-o/--output is alleen toegestaan bij precies één bronbestand "
            "(bij een map: sibling-output per bron).",
            file=sys.stderr,
        )
        return 1
    # One namespace; process by calling run per suffix group via temp ns.path
    exit_code = 0
    for f in files:
        one = argparse.Namespace(**vars(ns))
        one.path = str(f)
        one.output = ns.output if len(files) == 1 else None
        code = run_mvsa_import(one)
        if code:
            exit_code = code
    return exit_code


def add_mvsa_import_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "import",
        help=(
            "Importeer .mscz/.mxl naar .mvsa (catalogus-vrij; "
            "= mscz mvsa / mxl mvsa)."
        ),
        description=(
            "Zet een partituur- of MusicXML-bestand om naar werkbank-.mvsa. "
            "Zet niets in een catalogus. "
            "Equivalent: mscz mvsa (bij .mscz) of mxl mvsa (bij .mxl). "
            "Contract: docs/formats/contract-index.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "toegestane bronnen: .mscz, .mxl, .musicxml, .xml\n"
            "voorbeelden:\n"
            "  mvsa import lied.mscz\n"
            "  mvsa import lied.mxl -o lied.mvsa --pitch doremi\n"
            "  mscz mvsa lied.mscz   # zelfde als mvsa import lied.mscz\n"
        ),
    )
    p.add_argument(
        "path",
        help="Bronbestand (.mscz/.mxl/…) of map (recursief).",
    )
    add_score_to_mvsa_arguments(p)
    p.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore-executable (alleen bij .mscz; default: auto).",
    )


def run_mscz_import(ns: argparse.Namespace) -> int:
    """``mscz import`` → ``.mscz`` from ``.mvsa`` or MusicXML."""
    path = Path(ns.path)
    if path.is_file():
        suf = path.suffix.lower()
        if suf == ".mvsa":
            return _mscz_from_mvsa(ns)
        if suf in _MXL_SUFFIXES:
            return _mscz_from_mxl(ns)
        print(_reject_ext("mscz", path, _MSCZ_IMPORT_SUFFIXES), file=sys.stderr)
        return 1
    try:
        files = collect_cli_sources(ns.path, suffixes=_MSCZ_IMPORT_SUFFIXES)
    except InputPathError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not files:
        print(
            f"mscz import: geen .mvsa/.mxl/.musicxml/.xml onder {ns.path}.",
            file=sys.stderr,
        )
        return 1
    if len(files) > 1 and getattr(ns, "output", None):
        print(
            "-o/--output is alleen toegestaan bij precies één bronbestand "
            "(bij een map: sibling-output per bron).",
            file=sys.stderr,
        )
        return 1
    exit_code = 0
    for f in files:
        one = argparse.Namespace(**vars(ns))
        one.path = str(f)
        one.output = ns.output if len(files) == 1 else None
        code = run_mscz_import(one)
        if code:
            exit_code = code
    return exit_code


def _partituur_style_kwargs(ns: argparse.Namespace) -> dict:
    """Same mapping as ``cli._partituur_style_kwargs`` (avoid import cycle)."""
    from .mscz_partituur import apply_compact_style_preset

    kw = {
        "min_system_distance": getattr(ns, "min_system_distance", None),
        "max_system_distance": getattr(ns, "max_system_distance", None),
        "staff_distance": getattr(ns, "staff_distance", None),
        "page_margin_top_mm": getattr(ns, "page_margin_top", None),
        "page_margin_bottom_mm": getattr(ns, "page_margin_bottom", None),
        "lyrics_min_top_distance": None,
        "lyrics_min_bottom_distance": None,
        "lyrics_min_distance": None,
        "lyrics_font": getattr(ns, "lyrics_font", None),
        "lyrics_font_size": getattr(ns, "lyrics_font_size", None),
        "cue_font": getattr(ns, "cue_font", None),
        "cue_font_size": getattr(ns, "cue_font_size", None),
        "measure_spacing": getattr(ns, "measure_spacing", None),
    }
    if getattr(ns, "compact", False):
        kw = apply_compact_style_preset(kw)
    return kw


def _mscz_from_mvsa(ns: argparse.Namespace) -> int:
    """Same body as ``mvsa mscz`` (shared export)."""
    from .mvsa_mscz import MvsaMsczError, export_mvsa_to_mscz
    from .mvsa_musicxml import MvsaExportError
    from .mvsa_validate import MvsaValidationError, format_diagnostic

    style = _partituur_style_kwargs(ns)

    try:
        files = collect_cli_sources(ns.path, suffixes=_MSCZ_FROM_MVSA)
    except InputPathError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if len(files) > 1 and ns.output:
        print(
            "-o/--output is alleen toegestaan bij precies één bronbestand.",
            file=sys.stderr,
        )
        return 1
    musescore = Path(ns.musescore) if getattr(ns, "musescore", None) else None
    exit_code = 0
    for path in files:
        out = (
            Path(ns.output)
            if ns.output
            else derived_output_path(path, ".mscz")
        )
        keep_mxl = Path(ns.keep_mxl) if getattr(ns, "keep_mxl", None) else None
        try:
            export_mvsa_to_mscz(
                path,
                out,
                section_id=getattr(ns, "section", None),
                musescore=musescore,
                keep_mxl=keep_mxl,
                layout=getattr(ns, "layout", None),
                bibliotheek_id=getattr(ns, "bibliotheek_id", None),
                hulptekst=bool(getattr(ns, "hulptekst", False)),
                **style,
            )
        except MvsaValidationError as exc:
            for d in exc.diagnostics:
                print(format_diagnostic(d, path), file=sys.stderr)
            exit_code = 1
            continue
        except MvsaExportError as exc:
            loc = f"{path}:{exc.line}: " if getattr(exc, "line", None) else f"{path}: "
            print(f"{loc}ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        except MvsaMsczError as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"Geschreven: {out}")
        if keep_mxl is not None:
            print(f"MXL: {keep_mxl}")
    return exit_code


def _mscz_from_mxl(ns: argparse.Namespace) -> int:
    """Delegate to ``mxl mscz`` implementation."""
    from .cli_mxl import _cmd_mxl_to_mscz

    return _cmd_mxl_to_mscz(ns)


def add_mscz_import_parser(
    sub: argparse._SubParsersAction,
    *,
    add_style_args,
) -> None:
    """Register ``mscz import``; *add_style_args* = cli._add_partituur_style_args."""
    p = sub.add_parser(
        "import",
        help=(
            "Importeer .mvsa/.mxl naar .mscz (catalogus-vrij; "
            "= mvsa mscz / mxl mscz)."
        ),
        description=(
            "Zet .mvsa of MusicXML om naar .mscz (layoutprofiel partituur "
            "tenzij anders). Zet niets in een catalogus. "
            "Equivalent: mvsa mscz of mxl mscz. "
            "Contract: docs/formats/contract-index.md · "
            "docs/formats/mscz-leesbaarheid.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "toegestane bronnen: .mvsa, .mxl, .musicxml, .xml\n"
            "voorbeelden:\n"
            "  mscz import lied.mvsa\n"
            "  mscz import lied.mvsa --layout partituur\n"
            "  mscz import lied.mxl -o lied.mscz\n"
            "  mvsa mscz lied.mvsa   # zelfde als mscz import lied.mvsa\n"
        ),
    )
    p.add_argument(
        "path",
        help="Bronbestand (.mvsa/.mxl/…) of map (recursief).",
    )
    p.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoer-.mscz (default: sibling). "
            "Alleen bij precies één bronbestand."
        ),
    )
    p.add_argument(
        "--section",
        metavar="SECTION",
        default=None,
        help="Alleen bij .mvsa: deze @sectie-id (default: alle).",
    )
    p.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore-executable (default: auto).",
    )
    p.add_argument(
        "--keep-mxl",
        metavar="PATH",
        default=None,
        help="Alleen bij .mvsa: bewaar tussenliggend .mxl.",
    )
    p.add_argument(
        "--layout",
        metavar="PROFILE",
        default=None,
        help=(
            "Alleen bij .mvsa: partituur (default), muziek, of plain. "
            "Zie docs/formats/mscz-leesbaarheid.md."
        ),
    )
    p.add_argument(
        "--bibliotheek-id",
        metavar="ID",
        default=None,
        dest="bibliotheek_id",
        help="Alleen bij .mvsa + layout partituur: colofon-id.",
    )
    p.add_argument(
        "--hulptekst",
        action="store_true",
        help="Alleen bij .mvsa: tweede lyric-laag in partituur-MXL.",
    )
    add_style_args(p)
