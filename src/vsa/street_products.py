"""Street ``products``: bare exports + ``*.products-meta.json``.

Contract map: docs/formats/contract-index.md.
Does **not** write bibliotheek stamps (consumer responsibility).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .derived_path import derived_output_path
from .input_paths import InputPathError, collect_cli_sources
from .products_meta import freshness, write_meta

# Product keys written into meta (stable ids for consumers).
MVSA_CORE_KEYS = ("mxl", "score-ir", "from-ir")
MVSA_SVG_KEY = "svg"
MSCZ_CORE_KEYS = ("mxl",)
MSCZ_SVG_KEY = "svg"
VSA_CORE_KEYS = ("mxl", "svg")


def _log(msg: str, *, dry_run: bool) -> None:
    prefix = "dry-run: " if dry_run else ""
    print(f"{prefix}{msg}", flush=True)


def _assign_svg_products(products: dict[str, Path], written: list[Path]) -> None:
    """One page → ``svg``; bladreeks → ``svg-1``, ``svg-2``, …"""
    if len(written) == 1:
        products["svg"] = written[0]
        return
    for i, path in enumerate(written, start=1):
        products[f"svg-{i}"] = path


def _need_regen(bron: Path, *, force: bool, required_keys: set[str]) -> bool:
    if force:
        return True
    status, _ = freshness(bron, required_keys=required_keys)
    return status != "ok"


def products_mvsa_one(
    bron: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
    skip_svg: bool = False,
    musescore: Path | None = None,
) -> int:
    """Export Coria-mxl + Score-IR + from-ir (+ optional SVG) for one ``.mvsa``."""
    from .mvsa_mscz import MvsaMsczError, export_mvsa_to_svg
    from .mvsa_musicxml import MvsaExportError, export_mvsa_path
    from .mvsa_validate import MvsaValidationError, format_diagnostic
    from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError
    from .score_ir import export_mvsa_path_to_score_ir
    from .score_ir_musicxml import ScoreIrMusicxmlError, export_score_ir_path_to_musicxml

    required = set(MVSA_CORE_KEYS)
    if not skip_svg:
        required.add(MVSA_SVG_KEY)
    if not _need_regen(bron, force=force, required_keys=required):
        _log(f"ok (meta): {bron}", dry_run=dry_run)
        return 0

    mxl = derived_output_path(bron, ".mxl")
    score_ir = derived_output_path(bron, ".score-ir.json")
    from_ir = derived_output_path(bron, ".from-ir.musicxml")
    svg = derived_output_path(bron, ".svg")
    products: dict[str, Path] = {
        "mxl": mxl,
        "score-ir": score_ir,
        "from-ir": from_ir,
    }

    _log(f"mxl  {bron.name} -> {mxl.name}", dry_run=dry_run)
    _log(f"ir   {bron.name} -> {score_ir.name} + {from_ir.name}", dry_run=dry_run)
    if not skip_svg:
        _log(f"svg  {bron.name} -> {svg.name}", dry_run=dry_run)
        products["svg"] = svg

    if dry_run:
        return 0

    try:
        export_mvsa_path(bron, mxl, layout="playback")
        export_mvsa_path_to_score_ir(bron, score_ir)
        export_score_ir_path_to_musicxml(score_ir, from_ir)
        if not skip_svg:
            written = export_mvsa_to_svg(bron, svg, musescore=musescore)
            _assign_svg_products(products, written)
    except MvsaValidationError as exc:
        for d in exc.diagnostics:
            print(format_diagnostic(d, bron), file=sys.stderr)
        return 1
    except (MvsaExportError, ScoreIrMusicxmlError, MvsaMsczError) as exc:
        print(f"{bron}: ERROR: {exc}", file=sys.stderr)
        return 1
    except (MuseScoreNotFoundError, MuseScoreConvertError) as exc:
        print(f"{bron}: ERROR: {exc}", file=sys.stderr)
        print(
            "Hint: installeer MuseScore 4, of gebruik --skip-svg.",
            file=sys.stderr,
        )
        return 1

    meta = write_meta(bron, products)
    print(f"Meta: {meta.name}", flush=True)
    return 0


def products_mscz_one(
    bron: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
    skip_svg: bool = False,
    musescore: Path | None = None,
) -> int:
    """Export Coria-mxl (+ optional SVG) for one ``.mscz``."""
    from .musicxml_playback_normalize import export_mscz_to_playback_mxl
    from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError
    from .mvsa_mscz import MvsaMsczError, export_mscz_to_svg

    required = set(MSCZ_CORE_KEYS)
    if not skip_svg:
        required.add(MSCZ_SVG_KEY)
    if not _need_regen(bron, force=force, required_keys=required):
        _log(f"ok (meta): {bron}", dry_run=dry_run)
        return 0

    mxl = derived_output_path(bron, ".mxl")
    svg = derived_output_path(bron, ".svg")
    products: dict[str, Path] = {"mxl": mxl}
    _log(f"mxl  {bron.name} -> {mxl.name}", dry_run=dry_run)
    if not skip_svg:
        _log(f"svg  {bron.name} -> {svg.name}", dry_run=dry_run)
        products["svg"] = svg

    if dry_run:
        return 0

    try:
        export_mscz_to_playback_mxl(bron, mxl, musescore=musescore)
        if not skip_svg:
            written = export_mscz_to_svg(bron, svg, musescore=musescore)
            _assign_svg_products(products, written)
    except (MuseScoreNotFoundError, MuseScoreConvertError, MvsaMsczError) as exc:
        print(f"{bron}: ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"{bron}: ERROR: {exc}", file=sys.stderr)
        return 1

    meta = write_meta(bron, products)
    print(f"Meta: {meta.name}", flush=True)
    return 0


def products_vsa_one(
    bron: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> int:
    """Export playback MusicXML (syllabify + Coria-finalize) + native SVG."""
    from .config import load_config
    from .include_vsa import IncludeVsaError, prepare_vsa_body
    from .markdown_newline_policy import preserve_vsa_source_newlines
    from .parser import Parser
    from .svg_renderer import SVGRenderer
    from .vsa_musicxml_export import MusicXMLExportError, export_vsa_to_musicxml
    from .yaml_frontmatter import parse_vsa_frontmatter

    required = set(VSA_CORE_KEYS)
    if not _need_regen(bron, force=force, required_keys=required):
        _log(f"ok (meta): {bron}", dry_run=dry_run)
        return 0

    mxl = derived_output_path(bron, ".mxl")
    svg = derived_output_path(bron, ".svg")
    products = {"mxl": mxl, "svg": svg}
    _log(f"mxl  {bron.name} -> {mxl.name}", dry_run=dry_run)
    _log(f"svg  {bron.name} -> {svg.name}", dry_run=dry_run)
    if dry_run:
        return 0

    try:
        # MXL: syllabify + finalize (Coria). SVG: canonieke bron, geen syllabify.
        export_vsa_to_musicxml(bron, mxl, syllabify=True)

        text = bron.read_text(encoding="utf-8")
        _frontmatter, _ = parse_vsa_frontmatter(text)
        body, _ = prepare_vsa_body(text, bron)
        document = Parser(preserve_vsa_source_newlines(body)).parse()
        config = load_config(None)
        svg_renderer = SVGRenderer(svg_config=config.rendering.svg)
        svg_renderer.max_line_width = config.rendering.max_line_width
        svg_text = svg_renderer.render_document(document)
        svg.parent.mkdir(parents=True, exist_ok=True)
        svg.write_text(svg_text, encoding="utf-8", newline="\n")
    except IncludeVsaError as exc:
        print(f"{bron}: {exc.message_nl}", file=sys.stderr)
        return 1
    except MusicXMLExportError as exc:
        print(f"{bron}: ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"{bron}: ERROR: {exc}", file=sys.stderr)
        return 1

    meta = write_meta(bron, products)
    print(f"Meta: {meta.name}", flush=True)
    return 0


def run_street_products(
    street: str,
    path: str | Path,
    *,
    force: bool = False,
    dry_run: bool = False,
    skip_svg: bool = False,
    musescore: Path | None = None,
) -> int:
    """Run ``products`` for all sources under *path* for *street*."""
    suffixes = {
        "mvsa": (".mvsa",),
        "mscz": (".mscz",),
        "vsa": (".vsa",),
    }[street]
    try:
        files = collect_cli_sources(path, suffixes=suffixes)
    except InputPathError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not files:
        print(f"{street} products: geen bronnen ({', '.join(suffixes)}) onder {path}.")
        return 1
    exit_code = 0
    for bron in files:
        if street == "mvsa":
            code = products_mvsa_one(
                bron,
                force=force,
                dry_run=dry_run,
                skip_svg=skip_svg,
                musescore=musescore,
            )
        elif street == "mscz":
            code = products_mscz_one(
                bron,
                force=force,
                dry_run=dry_run,
                skip_svg=skip_svg,
                musescore=musescore,
            )
        else:
            code = products_vsa_one(bron, force=force, dry_run=dry_run)
        if code:
            exit_code = code
    return exit_code


def add_products_parser(
    sub: argparse._SubParsersAction,
    *,
    street: str,
    with_skip_svg: bool,
) -> None:
    help_txt = {
        "mvsa": "Coria-.mxl + Score-IR + from-ir (+ SVG) + products-meta",
        "mscz": "Coria-.mxl (+ SVG) + products-meta",
        "vsa": "playback-.mxl (syllabify+Coria) + SVG + products-meta",
    }[street]
    p = sub.add_parser(
        "products",
        help=help_txt,
        description=(
            f"Genereer standaardproducten voor {street}-bronnen en schrijf "
            f"{{stam}}.{street}.products-meta.json (versheid). "
            "Kaal (geen bibliotheek-stamps). "
            "Contract: docs/formats/contract-index.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "path",
        help=f".{street}-bestand of map (recursief).",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Regenereer ook als meta zegt dat alles vers is.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Alleen tonen wat er zou gebeuren.",
    )
    if with_skip_svg:
        p.add_argument(
            "--skip-svg",
            action="store_true",
            help="Sla MuseScore-SVG over (geen MuseScore nodig).",
        )
        p.add_argument(
            "--musescore",
            default=None,
            help="Pad naar MuseScore-executable (default: auto).",
        )
