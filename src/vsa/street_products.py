"""Street ``products``: bare exports + ``*.products-meta.json``.

Contract: docs/formats/contract-index.md (universele productcatalogus).
Does **not** write bibliotheek stamps (consumer responsibility).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .derived_path import derived_output_path
from .input_paths import InputPathError, collect_cli_sources
from .products_meta import freshness, load_meta, write_meta

# Universele standaardkeys (zelfde set voor vsa / mvsa / mscz products).
# ``svg`` = één tall compacte sibling; ``--skip-svg`` laat svg weg.
# Oude meta met ``svg-N`` (bladreeks) wordt bij schrijven gedropt.
UNIVERSAL_PRODUCT_KEYS = (
    "mxl",
    "score-ir",
    "from-ir",
    "mscz",
    "pdf",
    "mp3",
    "lyrics",
)
SVG_KEY = "svg"

# Aliassen (bestaande imports in CLI/tests).
MVSA_CORE_KEYS = UNIVERSAL_PRODUCT_KEYS
MVSA_SVG_KEY = SVG_KEY
MSCZ_CORE_KEYS = UNIVERSAL_PRODUCT_KEYS
MSCZ_SVG_KEY = SVG_KEY
MSCZ_PDF_KEY = "pdf"
VSA_CORE_KEYS = UNIVERSAL_PRODUCT_KEYS
LYRICS_KEY = "lyrics"
MP3_KEY = "mp3"
MSCZ_PRODUCT_KEY = "mscz"


def _log(msg: str, *, dry_run: bool) -> None:
    prefix = "dry-run: " if dry_run else ""
    print(f"{prefix}{msg}", flush=True)


def _assign_svg_products(products: dict[str, Path], written: list[Path]) -> None:
    """Tall product-SVG: altijd één key ``svg`` (geen bladreeks ``svg-N``)."""
    if not written:
        products.pop("svg", None)
        return
    products["svg"] = written[0]


def _paths_are_siblings(bron: Path, paths: list[Path]) -> bool:
    parent = bron.resolve().parent
    return all(Path(p).resolve().parent == parent for p in paths)


def merge_street_product_meta(
    bron: Path,
    products: dict[str, Path],
    *,
    drop_keys: set[str] | None = None,
) -> Path | None:
    """Merge product keys into ``*.products-meta.json`` next to *bron*."""
    if not products:
        return None
    sibling: dict[str, Path] = {}
    for key, path in products.items():
        if _paths_are_siblings(bron, [path]):
            sibling[key] = path
        else:
            print(
                f"{bron.name}: products-meta key '{key}' overgeslagen "
                "(bestand niet naast de bron; gebruik sibling-output).",
                file=sys.stderr,
            )
    if not sibling:
        return None
    return write_meta(bron, sibling, merge=True, drop_keys=drop_keys)


def svg_meta_products(
    bron: Path,
    written: list[Path],
) -> tuple[dict[str, Path], set[str]]:
    """Map SVG-export → key ``svg``; drop legacy bladreeks-keys ``svg-N``."""
    products: dict[str, Path] = {}
    _assign_svg_products(products, written)
    drop: set[str] = set()
    existing = load_meta(bron)
    prev = existing.get("products") if existing else None
    if isinstance(prev, dict):
        for key in prev:
            if key.startswith("svg-"):
                drop.add(key)
    return products, drop


def _need_regen(bron: Path, *, force: bool, required_keys: set[str]) -> bool:
    if force:
        return True
    status, _ = freshness(bron, required_keys=required_keys)
    return status != "ok"


def _required_keys(*, skip_svg: bool) -> set[str]:
    keys = set(UNIVERSAL_PRODUCT_KEYS)
    if not skip_svg:
        keys.add(SVG_KEY)
    return keys


def _plan_universal_paths(
    bron: Path, *, skip_svg: bool
) -> dict[str, Path]:
    products: dict[str, Path] = {
        "mxl": derived_output_path(bron, ".mxl"),
        "score-ir": derived_output_path(bron, ".score-ir.json"),
        "from-ir": derived_output_path(bron, ".from-ir.musicxml"),
        "mscz": derived_output_path(bron, ".mscz"),
        "pdf": derived_output_path(bron, ".pdf"),
        "mp3": derived_output_path(bron, ".mp3"),
        "lyrics": derived_output_path(bron, ".lyrics.txt"),
    }
    if not skip_svg:
        products["svg"] = derived_output_path(bron, ".svg")
    return products


def _log_universal_plan(
    bron: Path, products: dict[str, Path], *, dry_run: bool
) -> None:
    order = (
        "mxl",
        "score-ir",
        "from-ir",
        "mscz",
        "pdf",
        "mp3",
        "lyrics",
        "svg",
    )
    for key in order:
        path = products.get(key)
        if path is not None:
            _log(f"{key:9} {bron.name} -> {path.name}", dry_run=dry_run)


def products_mvsa_one(
    bron: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
    skip_svg: bool = False,
    musescore: Path | None = None,
) -> int:
    """Universele producten voor één ``.mvsa``."""
    from .audio_export import AudioExportError, export_to_audio
    from .mvsa_mscz import MvsaMsczError, export_mvsa_to_svg
    from .mvsa_musicxml import MvsaExportError
    from .mvsa_validate import MvsaValidationError, format_diagnostic
    from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError
    from .score_ir_musicxml import ScoreIrMusicxmlError, export_score_ir_path_to_musicxml
    from .street_product_export import (
        StreetProductExportError,
        export_bron_to_mxl,
        export_bron_to_mscz_product,
        export_bron_to_partituur_pdf,
        export_bron_to_score_ir,
        write_lyrics_product,
    )

    required = _required_keys(skip_svg=skip_svg)
    if not _need_regen(bron, force=force, required_keys=required):
        _log(f"ok (meta): {bron}", dry_run=dry_run)
        return 0

    products = _plan_universal_paths(bron, skip_svg=skip_svg)
    _log_universal_plan(bron, products, dry_run=dry_run)
    if dry_run:
        return 0

    try:
        export_bron_to_mxl(bron, products["mxl"], musescore=musescore)
        export_bron_to_score_ir(
            bron, products["score-ir"], musescore=musescore
        )
        export_score_ir_path_to_musicxml(
            products["score-ir"], products["from-ir"]
        )
        export_bron_to_mscz_product(
            bron, products["mscz"], musescore=musescore
        )
        export_bron_to_partituur_pdf(
            bron, products["pdf"], musescore=musescore
        )
        export_to_audio(
            bron, products["mp3"], format_name="mp3", musescore=musescore
        )
        write_lyrics_product(bron, products["lyrics"], musescore=musescore)
        if not skip_svg:
            written = export_mvsa_to_svg(
                bron, products["svg"], musescore=musescore
            )
            _assign_svg_products(products, written)
    except MvsaValidationError as exc:
        for d in exc.diagnostics:
            print(format_diagnostic(d, bron), file=sys.stderr)
        return 1
    except (
        MvsaExportError,
        ScoreIrMusicxmlError,
        MvsaMsczError,
        StreetProductExportError,
        AudioExportError,
        MuseScoreNotFoundError,
        MuseScoreConvertError,
    ) as exc:
        print(f"{bron}: ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"{bron}: ERROR: {exc}", file=sys.stderr)
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
    """Universele producten voor één ``.mscz``."""
    from .audio_export import AudioExportError, export_to_audio
    from .mvsa_mscz import MvsaMsczError, export_mscz_to_svg
    from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError
    from .score_ir_musicxml import ScoreIrMusicxmlError, export_score_ir_path_to_musicxml
    from .street_product_export import (
        StreetProductExportError,
        export_bron_to_mxl,
        export_bron_to_mscz_product,
        export_bron_to_partituur_pdf,
        export_bron_to_score_ir,
        write_lyrics_product,
    )

    required = _required_keys(skip_svg=skip_svg)
    if not _need_regen(bron, force=force, required_keys=required):
        _log(f"ok (meta): {bron}", dry_run=dry_run)
        return 0

    products = _plan_universal_paths(bron, skip_svg=skip_svg)
    _log_universal_plan(bron, products, dry_run=dry_run)
    if dry_run:
        return 0

    try:
        export_bron_to_mxl(bron, products["mxl"], musescore=musescore)
        export_bron_to_score_ir(
            bron, products["score-ir"], musescore=musescore
        )
        export_score_ir_path_to_musicxml(
            products["score-ir"], products["from-ir"]
        )
        export_bron_to_mscz_product(
            bron, products["mscz"], musescore=musescore
        )
        export_bron_to_partituur_pdf(
            bron, products["pdf"], musescore=musescore
        )
        export_to_audio(
            bron, products["mp3"], format_name="mp3", musescore=musescore
        )
        write_lyrics_product(bron, products["lyrics"], musescore=musescore)
        if not skip_svg:
            written = export_mscz_to_svg(
                bron, products["svg"], musescore=musescore
            )
            _assign_svg_products(products, written)
    except (
        StreetProductExportError,
        ScoreIrMusicxmlError,
        MvsaMsczError,
        AudioExportError,
        MuseScoreNotFoundError,
        MuseScoreConvertError,
    ) as exc:
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
    skip_svg: bool = False,
    musescore: Path | None = None,
) -> int:
    """Universele producten voor één ``.vsa``."""
    from .audio_export import AudioExportError, export_to_audio
    from .config import load_config
    from .include_vsa import IncludeVsaError, prepare_vsa_body
    from .markdown_newline_policy import preserve_vsa_source_newlines
    from .parser import Parser
    from .score_ir_musicxml import ScoreIrMusicxmlError, export_score_ir_path_to_musicxml
    from .street_product_export import (
        StreetProductExportError,
        export_bron_to_mxl,
        export_bron_to_mscz_product,
        export_bron_to_partituur_pdf,
        export_bron_to_score_ir,
        write_lyrics_product,
    )
    from .svg_renderer import SVGRenderer
    from .vsa_musicxml_export import MusicXMLExportError
    from .yaml_frontmatter import parse_vsa_frontmatter
    from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError

    required = _required_keys(skip_svg=skip_svg)
    if not _need_regen(bron, force=force, required_keys=required):
        _log(f"ok (meta): {bron}", dry_run=dry_run)
        return 0

    products = _plan_universal_paths(bron, skip_svg=skip_svg)
    _log_universal_plan(bron, products, dry_run=dry_run)
    if dry_run:
        return 0

    try:
        export_bron_to_mxl(bron, products["mxl"], musescore=musescore)
        export_bron_to_score_ir(
            bron, products["score-ir"], musescore=musescore
        )
        export_score_ir_path_to_musicxml(
            products["score-ir"], products["from-ir"]
        )
        export_bron_to_mscz_product(
            bron, products["mscz"], musescore=musescore
        )
        export_bron_to_partituur_pdf(
            bron, products["pdf"], musescore=musescore
        )
        export_to_audio(
            bron, products["mp3"], format_name="mp3", musescore=musescore
        )
        write_lyrics_product(bron, products["lyrics"], musescore=musescore)
        if not skip_svg:
            text = bron.read_text(encoding="utf-8")
            _frontmatter, _ = parse_vsa_frontmatter(text)
            body, _ = prepare_vsa_body(text, bron)
            document = Parser(preserve_vsa_source_newlines(body)).parse()
            config = load_config(None)
            svg_renderer = SVGRenderer(svg_config=config.rendering.svg)
            svg_renderer.max_line_width = config.rendering.max_line_width
            svg_text = svg_renderer.render_document(document)
            svg_path = products["svg"]
            svg_path.parent.mkdir(parents=True, exist_ok=True)
            svg_path.write_text(svg_text, encoding="utf-8", newline="\n")
    except IncludeVsaError as exc:
        print(f"{bron}: {exc.message_nl}", file=sys.stderr)
        return 1
    except (
        MusicXMLExportError,
        StreetProductExportError,
        ScoreIrMusicxmlError,
        AudioExportError,
        MuseScoreNotFoundError,
        MuseScoreConvertError,
    ) as exc:
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
            code = products_vsa_one(
                bron,
                force=force,
                dry_run=dry_run,
                skip_svg=skip_svg,
                musescore=musescore,
            )
        if code:
            exit_code = code
    return exit_code


def add_products_parser(
    sub: argparse._SubParsersAction,
    *,
    street: str,
    with_skip_svg: bool,
) -> None:
    help_txt = (
        "Universele standaardproducten (mxl, score-ir, from-ir, mscz, "
        "pdf, mp3, lyrics, svg) + products-meta"
    )
    p = sub.add_parser(
        "products",
        help=help_txt,
        description=(
            f"Genereer de universele standaardproducten voor {street}-bronnen "
            f"en schrijf {{stam}}.{street}.products-meta.json (versheid). "
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
            help="Sla SVG over (sneller / geen MuseScore voor svg).",
        )
        p.add_argument(
            "--musescore",
            default=None,
            help="Pad naar MuseScore-executable (default: auto).",
        )
    else:
        # vsa: native svg, maar mp3/mscz/pdf/score-ir kunnen MuseScore nodig hebben
        p.add_argument(
            "--skip-svg",
            action="store_true",
            help="Sla native SVG over.",
        )
        p.add_argument(
            "--musescore",
            default=None,
            help="Pad naar MuseScore (voor mscz/pdf/mp3/score-ir-keten).",
        )
