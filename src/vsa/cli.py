from __future__ import annotations

from .markdown_newline_policy import preserve_vsa_source_newlines
from .include_vsa import IncludeVsaError, prepare_markdown_block_body, prepare_vsa_body
import argparse
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .block_parser import DEFAULT_METADATA, parse_markdown_blocks
from .config import load_config
from .markdown_builder import build_markdown_site
from .markdown_pdf import PdfError, write_markdown_pdf
from .markdown_processor import ProcessValidationError, process_path
from .musicxml_package import (
    _MUSICXML_SUFFIX,
    _MXL_SUFFIX,
    _KNOWN_SUFFIXES,
    musicxml_output_suffix,
    write_musicxml_output,
)
from .musicxml_renderer import MusicXMLExportError, MusicXMLRenderer
from .parser import Parser
from .svg_renderer import SVGRenderer
from .validation_display import format_validation_message
from .validation_runner import validate_path
from .resolve_catalogus import ResolveCatalogusError, write_resolved_markdown
from .syllabify import (
    iter_vsa_files,
    normalize_output_extension,
    output_path_for,
    transform_vsa_source,
)
from .yaml_frontmatter import frontmatter_to_block_metadata, parse_vsa_frontmatter


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        return _run(args)
    except ProcessValidationError as exc:
        _print_validation_messages(exc.messages)
        return 1
    except PdfError as exc:
        print(f"ERROR: {exc.message_nl}", file=sys.stderr)
        if exc.hint_nl:
            print(exc.hint_nl, file=sys.stderr)
        return 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _build_parser():
    parser = argparse.ArgumentParser(prog="vsa")
    parser.add_argument("--config", help="Pad naar vsa.toml", default=None)
    parser.add_argument("--version", action="store_true", help="Toon versie")

    subparsers = parser.add_subparsers(dest="command")

    validate = subparsers.add_parser("validate")
    validate.add_argument("path")
    validate.add_argument("--config", default=None)
    validate.add_argument(
        "--summary",
        action="store_true",
        help="Compacte eenregelige foutmeldingen (zonder broncontext).",
    )

    parse = subparsers.add_parser("parse")
    parse.add_argument("path")
    parse.add_argument("--ast", action="store_true")

    blocks = subparsers.add_parser("blocks")
    blocks.add_argument("path")
    blocks.add_argument("--json", action="store_true")

    svg = subparsers.add_parser("svg")
    svg.add_argument("input")
    svg.add_argument("output")
    svg.add_argument("--config", default=None)
    svg.add_argument("--max-line-width", type=float, default=None)

    process = subparsers.add_parser("process")
    process.add_argument("input")
    process.add_argument("output_dir")
    process.add_argument("--config", default=None)
    process.add_argument("--no-validate", action="store_true")
    process.add_argument("--max-line-width", type=float, default=None)

    build_markdown = subparsers.add_parser("build-markdown")
    build_markdown.add_argument("input_dir")
    build_markdown.add_argument("output_dir")
    build_markdown.add_argument("assets_dir")
    build_markdown.add_argument("--config", default=None)
    build_markdown.add_argument("--assets-url-prefix", default=None)
    build_markdown.add_argument("--max-line-width", type=float, default=None)
    build_markdown.add_argument(
        "--output-mode",
        choices=["img", "shortcode"],
        default=None,
    )

    resolve_catalogus = subparsers.add_parser(
        "resolve-catalogus",
        help="Los :::include zoek= op naar catalogus-paden in markdown.",
    )
    resolve_catalogus.add_argument("path", help="Markdown-bestand met zoek= includes")
    resolve_catalogus.add_argument(
        "--content-root",
        default=None,
        help="Content-root (default: auto via lokaal/ in bovenliggende mappen)",
    )
    resolve_catalogus.add_argument(
        "--bron-root",
        default=None,
        help="Bron-repo root (default: auto via vendor/bron of ../bron)",
    )
    resolve_catalogus.add_argument(
        "-o",
        "--output",
        default=None,
        help="Uitvoerbestand (default: overschrijf invoer)",
    )
    resolve_catalogus.add_argument(
        "--dry-run",
        action="store_true",
        help="Toon resultaat zonder bestand te schrijven",
    )

    syllabify = subparsers.add_parser(
        "syllabify",
        help=(
            "Zet of verwijder lettergreepstreepjes in VSA-tekst "
            "(Pyphen nl_NL; ook brugstreepjes op scope-grenzen)."
        ),
    )
    syllabify.add_argument(
        "path",
        help="VSA-bestand (.vsa) of map (recursief alle .vsa).",
    )
    syllabify_out = syllabify.add_mutually_exclusive_group()
    syllabify_out.add_argument(
        "--dry-run",
        action="store_true",
        help="Toon resultaat zonder bestanden te schrijven (default zonder schrijfmodus).",
    )
    syllabify_out.add_argument(
        "--in-place",
        action="store_true",
        help="Schrijf het resultaat terug naar elk bronbestand.",
    )
    syllabify.add_argument(
        "--extension",
        metavar="EXT",
        default=None,
        help=(
            "Schrijf naast het bronbestand met deze extensie "
            "(bijv. .syl.vsa of syl.vsa: xyz.vsa wordt xyz.syl.vsa). "
            "Niet combineren met --in-place."
        ),
    )
    syllabify.add_argument(
        "--unsyllabify",
        action="store_true",
        help=(
            "Verwijder lettergreepstreepjes (ook brugstreepjes rond scopes; "
            "scope-inhoud en ELM-'-' blijven staan)."
        ),
    )

    musicxml = subparsers.add_parser("musicxml")
    musicxml.add_argument(
        "input",
        help="VSA-bestand (.vsa), Markdown-bestand (.md) of map.",
    )
    musicxml.add_argument(
        "output",
        help=(
            "Uitvoerbestand (.mxl standaard, of .musicxml) voor een enkel "
            "invoerbestand, of uitvoermap voor meerdere bestanden."
        ),
    )
    musicxml.add_argument("--config", default=None)
    musicxml.add_argument(
        "--format",
        choices=["musicxml", "mxl"],
        default=None,
        help=(
            "Uitvoerformaat: .mxl (default) of .musicxml. "
            "Bij een enkel bestand overschrijft een expliciete extensie dit."
        ),
    )
    musicxml.add_argument(
        "--do",
        default=None,
        help="Grondtoon, bijv. F4 (overschrijft bestand-metadata).",
    )
    musicxml.add_argument(
        "--mode",
        default=None,
        help="Modus, bijv. major of minor (overschrijft bestand-metadata).",
    )
    musicxml.add_argument(
        "--tempo",
        default=None,
        help="Tempo in BPM (overschrijft bestand-metadata).",
    )
    musicxml.add_argument(
        "--musicxml-profile",
        choices=["playback", "engraving"],
        default=None,
        help=(
            "MusicXML-exportprofiel: playback (default, Coria/MuseScore) "
            "of engraving (expliciete maatstrepen, typografie)."
        ),
    )

    template = subparsers.add_parser(
        "template",
        help="vsa-template: valideren van formule-YAML.",
    )
    template_sub = template.add_subparsers(dest="template_command")
    t_validate = template_sub.add_parser(
        "validate",
        help="Valideer template.yaml (schema + documentregels).",
    )
    t_validate.add_argument(
        "path",
        help="template.yaml of map met template.yaml-bestanden.",
    )

    mvsa = subparsers.add_parser(
        "mvsa",
        help="mvsa draft: valideren, normaliseren, MusicXML of MSCZ.",
        description=(
            "Draft-tooling voor meerstemmige .mvsa-bestanden "
            "(L + SATB). Zie docs/specification-mvsa/."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "subcommando's:\n"
            "  validate PATH\n"
            "      Valideer .mvsa (bestand of map).\n"
            "  musicxml PATH [-o OUTPUT] [--section SECTION]\n"
            "      Exporteer naar SATB MusicXML (.mxl/.musicxml).\n"
            "  mscz PATH [-o OUTPUT] [--section SECTION]\n"
            "      Exporteer naar MuseScore (.mscz) via .mxl.\n"
            "  import PATH [-o OUTPUT] --pitch {doremi,abc,vsa}\n"
            "      Importeer .mxl/.mscz naar .mvsa.\n"
            "  normalize PATH [-o OUTPUT] --pitch {doremi,abc,vsa}\n"
            "      Herschrijf stemhoogten naar canonieke spelling.\n"
            "\n"
            "voorbeelden:\n"
            "  vsa mvsa validate examples\\mvsa\n"
            "  vsa mvsa musicxml lied.mvsa -o out.mxl --section schets1\n"
            "  vsa mvsa mscz lied.mvsa -o out.mscz\n"
            "  vsa mvsa import out.mxl -o out.mvsa --pitch doremi\n"
            "  vsa mvsa normalize lied.mvsa -o out.mvsa --pitch abc\n"
            "\n"
            "Top-level alias: mvsa …  (ook: mxl … / mscz … voor andere bronnen).\n"
            "\n"
            "Hulp: vsa mvsa validate -h | vsa mvsa musicxml -h | "
            "vsa mvsa mscz -h | vsa mvsa import -h | vsa mvsa normalize -h"
        ),
    )
    mvsa_sub = mvsa.add_subparsers(
        dest="mvsa_command",
        required=True,
        metavar="{validate,musicxml,mscz,import,normalize}",
    )
    m_validate = mvsa_sub.add_parser(
        "validate",
        help="Valideer .mvsa (structuur + sync-telling; draft-spec).",
        description=(
            "Controleer .mvsa-bestanden op structuur, maatstrepen en "
            "sync-telling L tegen stemmen (draft-spec docs/specification-mvsa/)."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    m_validate.add_argument(
        "path",
        help=".mvsa-bestand of map met .mvsa-bestanden.",
    )
    m_musicxml = mvsa_sub.add_parser(
        "musicxml",
        help="Exporteer .mvsa naar SATB MusicXML (.mxl/.musicxml).",
        description=(
            "Exporteer een .mvsa-bestand naar SATB MusicXML. "
            "Optioneel een @sectie-id; anders alle secties achter elkaar."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  vsa mvsa musicxml examples\\mvsa\\kleine-intocht-zondag-hemelum.mvsa\n"
            "  vsa mvsa musicxml lied.mvsa -o generated\\lied.mxl\n"
            "  vsa mvsa musicxml lied.mvsa --section schets-a-bladcijfer -o out.mxl"
        ),
    )
    m_musicxml.add_argument(
        "path",
        help=".mvsa-bestand om te exporteren.",
    )
    m_musicxml.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        default=None,
        help="Uitvoerbestand (default: <stem>.mxl naast het bronbestand).",
    )
    m_musicxml.add_argument(
        "--section",
        metavar="SECTION",
        default=None,
        help="Alleen deze @sectie-id exporteren (default: alle secties).",
    )
    m_mscz = mvsa_sub.add_parser(
        "mscz",
        help="Exporteer .mvsa naar MuseScore (.mscz) via MusicXML.",
        description=(
            "Keten: .mvsa -> .mxl -> MuseScore CLI -> .mscz. "
            "Vereist MuseScore 4 (of 3) op PATH of standaard Windows-pad. "
            "Zie docs/plans/mvsa-conversions.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  vsa mvsa mscz examples\\mvsa\\alleluia-toon-8.canonieke.mvsa\n"
            "  vsa mvsa mscz lied.mvsa -o generated\\lied.mscz "
            "--section schets2-oct-doremi\n"
            "  vsa mvsa mscz lied.mvsa -o out.mscz --keep-mxl generated\\lied.mxl"
        ),
    )
    m_mscz.add_argument(
        "path",
        help=".mvsa-bestand om te exporteren.",
    )
    m_mscz.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        default=None,
        help="Uitvoer-.mscz (default: <stem>.mscz naast het bronbestand).",
    )
    m_mscz.add_argument(
        "--section",
        metavar="SECTION",
        default=None,
        help="Alleen deze @sectie-id exporteren (default: alle secties).",
    )
    m_mscz.add_argument(
        "--musescore",
        metavar="PATH",
        default=None,
        help="Pad naar MuseScore-executable (default: auto-detectie).",
    )
    m_mscz.add_argument(
        "--keep-mxl",
        metavar="PATH",
        default=None,
        help="Bewaar ook het tussenliggende .mxl op dit pad.",
    )
    m_import = mvsa_sub.add_parser(
        "import",
        help="Importeer .mxl/.musicxml/.mscz naar .mvsa.",
        description=(
            "Lees SATB MusicXML (of MSCZ via MuseScore) en schrijf .mvsa. "
            "Kies stem-spelling met --pitch. Zie docs/plans/mvsa-conversions.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  vsa mvsa import generated\\lied.mxl -o generated\\lied.import.mvsa "
            "--pitch doremi\n"
            "  vsa mvsa import lied.mscz -o lied.mvsa --pitch abc"
        ),
    )
    m_import.add_argument(
        "path",
        help=".mxl, .musicxml, .xml of .mscz bronbestand.",
    )
    m_import.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        default=None,
        help="Uitvoer-.mvsa (default: <stem>.import.mvsa).",
    )
    m_import.add_argument(
        "--pitch",
        choices=["doremi", "abc", "vsa"],
        required=True,
        help="Doel-spelling op stemregels.",
    )
    m_import.add_argument(
        "--octave-style",
        choices=["@oct", "marker"],
        default="@oct",
        help="Schrijfoctaaf-stijl (marker nog niet geïmplementeerd).",
    )
    m_import.add_argument(
        "--section",
        metavar="SECTION",
        default="import",
        help="Id voor @sectie in de output (default: import).",
    )
    m_import.add_argument(
        "--musescore",
        metavar="PATH",
        default=None,
        help="Pad naar MuseScore (alleen bij .mscz-bron).",
    )
    m_import.add_argument(
        "--no-align",
        action="store_true",
        help="Sla canonieke kolomuitlijning over.",
    )
    m_normalize = mvsa_sub.add_parser(
        "normalize",
        help="Normaliseer stemhoogte-spelling (.mvsa -> .mvsa).",
        description=(
            "Herschrijf S/A/T/B naar doremi, abc (wetenschappelijk cijfer) "
            "of vsa (EHM). Behoudt L-semantiek en @oct. Zie "
            "docs/plans/mvsa-conversions.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  vsa mvsa normalize examples\\mvsa\\alleluia-toon-8.canonieke.mvsa "
            "--pitch abc -o generated\\alleluia.abc.mvsa\n"
            "  vsa mvsa normalize lied.mvsa --pitch doremi --octave-style @oct"
        ),
    )
    m_normalize.add_argument(
        "path",
        help=".mvsa-bestand om te normaliseren.",
    )
    m_normalize.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        default=None,
        help="Uitvoerbestand (default: <stem>.normalized.mvsa).",
    )
    m_normalize.add_argument(
        "--pitch",
        choices=["doremi", "abc", "vsa"],
        required=True,
        help="Doel-spelling op stemregels.",
    )
    m_normalize.add_argument(
        "--octave-style",
        choices=["@oct", "marker"],
        default="@oct",
        help="Schrijfoctaaf-stijl (marker nog niet geïmplementeerd).",
    )
    m_normalize.add_argument(
        "--no-align",
        action="store_true",
        help="Sla canonieke kolomuitlijning over.",
    )

    pdf = subparsers.add_parser(
        "pdf",
        help="Render een Markdownbestand (VSA, includes, pagebreaks) naar PDF.",
    )
    pdf.add_argument("input", help="Markdownbestand (.md) met VSA-blokken en/of includes.")
    pdf.add_argument(
        "-o",
        "--output",
        default=None,
        help="Uitvoer-PDF (default: <stem>.pdf in de huidige map).",
    )
    pdf.add_argument("--config", default=None)
    pdf.add_argument(
        "--content-root",
        default=None,
        help="Content-root voor includes (default: map met lokaal/, anders de map van het bestand).",
    )
    pdf.add_argument(
        "--bron-root",
        default=None,
        help="Bron-repo root (default: auto via vendor/bron of ../bron).",
    )
    pdf.add_argument("--max-line-width", type=float, default=None)
    pdf.add_argument(
        "--chrome",
        default=None,
        help="Pad naar Edge/Chrome/Chromium (anders CHROME_PATH of auto-detectie).",
    )

    return parser


def _run(args):
    if args.version:
        print(f"vsa {_version()}")
        return 0

    if args.command is None:
        print("Geen commando opgegeven.", file=sys.stderr)
        return 1

    config = load_config(getattr(args, "config", None))

    if args.command == "validate":
        return _cmd_validate(args, config)

    if args.command == "parse":
        return _cmd_parse(args)

    if args.command == "blocks":
        return _cmd_blocks(args)

    if args.command == "svg":
        return _cmd_svg(args, config)

    if args.command == "process":
        return _cmd_process(args, config)

    if args.command == "build-markdown":
        return _cmd_build_markdown(args, config)

    if args.command == "resolve-catalogus":
        return _cmd_resolve_catalogus(args)

    if args.command == "syllabify":
        return _cmd_syllabify(args)

    if args.command == "musicxml":
        return _cmd_musicxml(args, config)

    if args.command == "template":
        return _cmd_template(args)

    if args.command == "mvsa":
        return _cmd_mvsa(args)

    if args.command == "pdf":
        return _cmd_pdf(args, config)

    print(f"Onbekend commando: {args.command}", file=sys.stderr)
    return 1


def _version():
    for package_name in ["vsa-tool", "vsa"]:
        try:
            return version(package_name)
        except PackageNotFoundError:
            continue

    return "0.1.0"


def _cmd_validate(args, config):
    result = validate_path(args.path, config=config)

    if result.messages:
        _print_validation_messages(result.messages, summary=args.summary)

    if result.ok:
        if not result.messages:
            print("OK")
        return 0

    return 1


def _cmd_parse(args):
    path = Path(args.path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".vsa":
        try:
            text, _ = prepare_vsa_body(text, path)
        except IncludeVsaError as exc:
            print(f"{path}: {exc.message_nl}", file=sys.stderr)
            return 1
    document = Parser(preserve_vsa_source_newlines(text)).parse()

    if args.ast:
        print(json.dumps(document.to_dict(), ensure_ascii=False, indent=2))
    else:
        print("OK")

    return 0


def _cmd_blocks(args):
    text = Path(args.path).read_text(encoding="utf-8")
    blocks = parse_markdown_blocks(text)

    if args.json:
        data = []

        for block in blocks:
            item = {
                "start_line": block.start_line,
                "end_line": block.end_line,
                "metadata": block.effective_metadata(),
                "body": block.body,
                "ast": block.parse_body().to_dict(),
            }
            data.append(item)

        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"{len(blocks)} VSA-blok(ken) gevonden")

    return 0


def _cmd_svg(args, config):
    input_path = Path(args.input)
    text = input_path.read_text(encoding="utf-8")
    try:
        body, _ = prepare_vsa_body(text, input_path)
    except IncludeVsaError as exc:
        print(f"{input_path}: {exc.message_nl}", file=sys.stderr)
        return 1
    document = Parser(preserve_vsa_source_newlines(body)).parse()

    renderer = SVGRenderer(svg_config=config.rendering.svg)
    renderer.max_line_width = (
        args.max_line_width
        if args.max_line_width is not None
        else config.rendering.max_line_width
    )

    svg = renderer.render_document(document)
    Path(args.output).write_text(svg, encoding="utf-8")

    print(f"SVG geschreven naar: {args.output}")
    return 0


def _cmd_process(args, config):
    max_line_width = (
        args.max_line_width
        if args.max_line_width is not None
        else config.rendering.max_line_width
    )

    result = process_path(
        args.input,
        args.output_dir,
        validate=not args.no_validate,
        max_line_width=max_line_width,
        config=config,
    )

    print(f"{len(result.blocks)} SVG-bestand(en) gegenereerd")

    for block in result.blocks:
        print(f"- {block.output_file}")

    return 0


def _cmd_build_markdown(args, config):
    assets_url_prefix = (
        args.assets_url_prefix
        if args.assets_url_prefix is not None
        else config.hugo.assets_url_prefix
    )
    max_line_width = (
        args.max_line_width
        if args.max_line_width is not None
        else config.rendering.max_line_width
    )
    output_mode = (
        args.output_mode
        if args.output_mode is not None
        else config.hugo.output_mode
    )

    result = build_markdown_site(
        args.input_dir,
        args.output_dir,
        args.assets_dir,
        assets_url_prefix=assets_url_prefix,
        max_line_width=max_line_width,
        output_mode=output_mode,
        config=config,
    )

    print(f"{len(result.markdown_files)} Markdownbestand(en) geschreven")
    print(f"{len(result.svg_files)} SVG-bestand(en) geschreven")
    return 0


def _cmd_pdf(args, config):
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else Path(input_path.stem + ".pdf")
    chrome_command = [args.chrome] if args.chrome else None
    result = write_markdown_pdf(
        input_path,
        output_path,
        content_root=args.content_root,
        bron_root=args.bron_root,
        config=config,
        max_line_width=args.max_line_width,
        chrome_command=chrome_command,
    )
    print(f"PDF geschreven naar: {result}")
    return 0


def _cmd_syllabify(args) -> int:
    source_path = Path(args.path)
    if args.in_place and args.extension:
        print(
            "syllabify: gebruik --in-place of --extension, niet beide.",
            file=sys.stderr,
        )
        return 1

    extension: str | None = None
    if args.extension is not None:
        try:
            extension = normalize_output_extension(args.extension)
        except ValueError as exc:
            print(f"syllabify: {exc}", file=sys.stderr)
            return 1

    write_mode = bool(args.in_place or extension)
    # --dry-run forceert geen schrijven; zonder schrijfmodus is default dry-run.
    dry_run = args.dry_run or not write_mode

    try:
        files = iter_vsa_files(source_path)
    except FileNotFoundError:
        print(f"Pad niet gevonden: {source_path}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"syllabify: {exc}", file=sys.stderr)
        return 1

    if not files:
        print(f"Geen .vsa-bestanden gevonden onder: {source_path}", file=sys.stderr)
        return 1

    multi = len(files) > 1 or source_path.is_dir()
    any_error = False
    verb = "verwijderd" if args.unsyllabify else "toegevoegd"

    for file_path in files:
        try:
            target = output_path_for(file_path, extension)
        except ValueError as exc:
            print(f"{file_path}: {exc}", file=sys.stderr)
            any_error = True
            continue

        if extension is not None and file_path.name.lower().endswith(extension.lower()):
            print(
                f"{file_path}: overgeslagen (naam eindigt al op {extension})",
                file=sys.stderr,
            )
            continue

        original = file_path.read_text(encoding="utf-8")
        try:
            result = transform_vsa_source(original, unsyllabify=args.unsyllabify)
        except Exception as exc:
            print(f"{file_path}: {exc}", file=sys.stderr)
            any_error = True
            continue

        status = (
            f"{result.replacements} lettergreepstreepje(s) {verb}"
            if result.changed
            else "geen wijzigingen"
        )

        if dry_run:
            if multi:
                print(f"{file_path} -> {target}: {status} (dry-run)")
            else:
                sys.stdout.write(result.text)
                if not result.text.endswith("\n"):
                    sys.stdout.write("\n")
                print(
                    f"(dry-run — {status}; bestand niet geschreven)",
                    file=sys.stderr,
                )
            continue

        if result.changed or target != file_path:
            target.write_text(result.text, encoding="utf-8")
        if target == file_path:
            print(f"{file_path}: {status}")
        else:
            print(f"{file_path} -> {target}: {status}")

    return 1 if any_error else 0


def _cmd_resolve_catalogus(args) -> int:
    source_path = Path(args.path)
    if not source_path.is_file():
        print(f"Bestand niet gevonden: {source_path}", file=sys.stderr)
        return 1
    content_root = Path(args.content_root) if args.content_root else None
    bron_root = Path(args.bron_root) if args.bron_root else None
    output_path = Path(args.output) if args.output else None
    try:
        result = write_resolved_markdown(
            source_path,
            content_root=content_root,
            bron_root=bron_root,
            output_path=output_path,
            dry_run=args.dry_run,
        )
    except ResolveCatalogusError as exc:
        location = f"{source_path}:{exc.line}: " if exc.line else f"{source_path}: "
        print(f"{location}{exc.message_nl}", file=sys.stderr)
        return 1

    for warning in result.warnings:
        print(
            f"{source_path}:{warning.line}: WARNING: {warning.code}: "
            f"{warning.message_nl}",
            file=sys.stderr,
        )

    if result.resolved_queries:
        print(
            f"Opgelost: {len(result.resolved_queries)} unieke zoek= "
            f"({', '.join(result.resolved_queries)})"
        )
    else:
        print("Geen zoek= includes gevonden.")

    if args.dry_run:
        print("(dry-run — bestand niet geschreven)")
    return 0


def _cmd_musicxml(args, config):
    input_path = Path(args.input)

    cli_overrides: dict[str, str] = {}
    if args.do:
        cli_overrides["do"] = args.do
    if args.mode:
        cli_overrides["mode"] = args.mode
    if args.tempo:
        cli_overrides["tempo"] = args.tempo
    if args.musicxml_profile:
        cli_overrides["musicxml-profile"] = args.musicxml_profile

    output_suffix = _musicxml_batch_suffix(args)

    if input_path.is_dir():
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        written = 0
        for vsa_file in sorted(input_path.rglob("*.vsa")):
            rel = vsa_file.relative_to(input_path)
            out_file = output_dir / rel.with_suffix(output_suffix)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            rc = _export_vsa_to_musicxml(vsa_file, out_file, cli_overrides)
            if rc != 0:
                return rc
            written += 1
        for md_file in sorted(input_path.rglob("*.md")):
            rel = md_file.relative_to(input_path)
            out_subdir = output_dir / rel.with_suffix("")
            rc, block_count = _export_md_to_musicxml(
                md_file, out_subdir, cli_overrides, output_suffix=output_suffix
            )
            if rc != 0:
                return rc
            written += block_count
        label = "MXL" if output_suffix == _MXL_SUFFIX else "MusicXML"
        print(f"{written} {label}-bestand(en) geschreven")
        return 0

    output_path = Path(args.output)

    if input_path.suffix.lower() == ".vsa":
        out_path = _resolve_musicxml_output_path(output_path, args)
        rc = _export_vsa_to_musicxml(input_path, out_path, cli_overrides)
        if rc == 0:
            print(f"MusicXML geschreven naar: {out_path}")
        return rc

    if input_path.suffix.lower() in {".md", ".markdown"}:
        output_path.mkdir(parents=True, exist_ok=True)
        rc, written = _export_md_to_musicxml(
            input_path, output_path, cli_overrides, output_suffix=output_suffix
        )
        if rc == 0 and written:
            label = "MXL" if output_suffix == _MXL_SUFFIX else "MusicXML"
            print(f"{written} {label}-bestand(en) geschreven")
        return rc

    print(
        f"Onbekend bestandstype: '{input_path.suffix}'. "
        "Gebruik .vsa, .md of een map.",
        file=sys.stderr,
    )
    return 1


def _musicxml_batch_suffix(args) -> str:
    return musicxml_output_suffix(format_name=args.format)


def _resolve_musicxml_output_path(output_path: Path, args) -> Path:
    if output_path.suffix.lower() in _KNOWN_SUFFIXES:
        return output_path
    return output_path.with_suffix(_musicxml_batch_suffix(args))


def _export_vsa_to_musicxml(
    input_path: Path,
    output_path: Path,
    cli_overrides: dict[str, str],
) -> int:
    text = input_path.read_text(encoding="utf-8")
    frontmatter, vsa_body = parse_vsa_frontmatter(text)
    try:
        vsa_body, _ = prepare_vsa_body(text, input_path)
    except IncludeVsaError as exc:
        print(f"{input_path}: {exc.message_nl}", file=sys.stderr)
        return 1
    fm_meta = frontmatter_to_block_metadata(frontmatter)

    metadata = dict(DEFAULT_METADATA)
    metadata.update(fm_meta)
    metadata.update(cli_overrides)

    explicit_keys = set(fm_meta.keys()) | set(cli_overrides.keys())

    document = Parser(preserve_vsa_source_newlines(vsa_body)).parse()

    try:
        renderer = MusicXMLRenderer(metadata=metadata, explicit_keys=explicit_keys)
        xml_str = renderer.render(document)
    except MusicXMLExportError as exc:
        print(f"{input_path}: fout bij MusicXML-export: {exc}", file=sys.stderr)
        return 1

    write_musicxml_output(output_path, xml_str)
    return 0


def _export_md_to_musicxml(
    input_path: Path,
    output_dir: Path,
    cli_overrides: dict[str, str],
    *,
    output_suffix: str = _MUSICXML_SUFFIX,
) -> tuple[int, int]:
    text = input_path.read_text(encoding="utf-8")
    blocks = parse_markdown_blocks(text)

    if not blocks:
        return 0, 0

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem
    written = 0

    for i, block in enumerate(blocks):
        metadata = block.effective_metadata()
        metadata.update(cli_overrides)
        try:
            expanded_body, _ = prepare_markdown_block_body(
                block.body,
                markdown_path=input_path,
                markdown_text=text,
            )
        except IncludeVsaError as exc:
            print(f"{input_path} (blok {i + 1}): {exc.message_nl}", file=sys.stderr)
            return 1, written
        document = block.parse_body(expanded_body)

        explicit_keys = set(block.metadata.keys()) | set(cli_overrides.keys())

        try:
            renderer = MusicXMLRenderer(metadata=metadata, explicit_keys=explicit_keys)
            xml_str = renderer.render(document)
        except MusicXMLExportError as exc:
            print(
                f"{input_path} (blok {i + 1}): fout bij MusicXML-export: {exc}",
                file=sys.stderr,
            )
            return 1, written

        suffix = f"-{i + 1}" if len(blocks) > 1 else ""
        out_file = output_dir / f"{stem}{suffix}{output_suffix}"
        write_musicxml_output(out_file, xml_str)
        written += 1

    return 0, written


def _cmd_template(args) -> int:
    if getattr(args, "template_command", None) == "validate":
        return _cmd_template_validate(args)
    print("Gebruik: vsa template validate <pad>", file=sys.stderr)
    return 1


def _cmd_mvsa(args) -> int:
    if getattr(args, "mvsa_command", None) == "validate":
        return _cmd_mvsa_validate(args)
    if getattr(args, "mvsa_command", None) == "musicxml":
        return _cmd_mvsa_musicxml(args)
    if getattr(args, "mvsa_command", None) == "mscz":
        return _cmd_mvsa_mscz(args)
    if getattr(args, "mvsa_command", None) == "import":
        return _cmd_mvsa_import(args)
    if getattr(args, "mvsa_command", None) == "normalize":
        return _cmd_mvsa_normalize(args)
    # required=True op subparsers voorkomt dit normaal; fallback voor duidelijkheid.
    print(
        "Gebruik: vsa mvsa {validate,musicxml,mscz,import,normalize} …\n"
        "  vsa mvsa validate PATH\n"
        "  vsa mvsa musicxml PATH [-o OUTPUT] [--section SECTION]\n"
        "  vsa mvsa mscz PATH [-o OUTPUT] [--section SECTION]\n"
        "  vsa mvsa import PATH --pitch {doremi,abc,vsa} [-o OUTPUT]\n"
        "  vsa mvsa normalize PATH --pitch {doremi,abc,vsa} [-o OUTPUT]\n"
        "Hulp: vsa mvsa -h | vsa mvsa import -h",
        file=sys.stderr,
    )
    return 1


def _cmd_mvsa_validate(args) -> int:
    from .mvsa_validate import (
        collect_mvsa_files,
        format_diagnostic,
        validate_mvsa_path,
    )

    path = Path(args.path)
    if not path.exists():
        print(f"Pad niet gevonden: {path}", file=sys.stderr)
        return 1
    files = collect_mvsa_files(path)
    if not files:
        print(f"Geen .mvsa gevonden onder {path}", file=sys.stderr)
        return 1
    errors = 0
    for mvsa_path in files:
        diags = validate_mvsa_path(mvsa_path)
        fatal = [d for d in diags if d.severity == "error"]
        for d in diags:
            print(format_diagnostic(d, mvsa_path), file=sys.stderr if d.severity == "error" else sys.stdout)
        if fatal:
            errors += 1
            continue
        print(f"{mvsa_path}: OK")
    if errors:
        print(f"{errors} mvsa-bestand(en) ongeldig", file=sys.stderr)
        return 1
    return 0


def _cmd_mvsa_musicxml(args) -> int:
    from .mvsa_musicxml import MvsaExportError, export_mvsa_path
    from .mvsa_validate import MvsaValidationError, format_diagnostic
    from .musicxml_package import musicxml_output_suffix

    path = Path(args.path)
    if not path.is_file():
        print(f"Bestand niet gevonden: {path}", file=sys.stderr)
        return 1
    out = Path(args.output) if args.output else path.with_suffix(".mxl")
    if out.suffix.lower() not in {".mxl", ".musicxml", ".xml"}:
        out = out.with_suffix(musicxml_output_suffix(path=out))
    try:
        export_mvsa_path(path, out, section_id=args.section)
    except MvsaValidationError as exc:
        for d in exc.diagnostics:
            print(format_diagnostic(d, path), file=sys.stderr)
        return 1
    except MvsaExportError as exc:
        loc = f"{path}:{exc.line}: " if exc.line else f"{path}: "
        print(f"{loc}ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Geschreven: {out}")
    return 0


def _cmd_mvsa_mscz(args) -> int:
    from .mvsa_mscz import MvsaMsczError, export_mvsa_to_mscz
    from .mvsa_musicxml import MvsaExportError
    from .mvsa_validate import MvsaValidationError, format_diagnostic

    path = Path(args.path)
    if not path.is_file():
        print(f"Bestand niet gevonden: {path}", file=sys.stderr)
        return 1
    out = Path(args.output) if args.output else path.with_suffix(".mscz")
    keep_mxl = Path(args.keep_mxl) if args.keep_mxl else None
    musescore = Path(args.musescore) if args.musescore else None
    try:
        export_mvsa_to_mscz(
            path,
            out,
            section_id=args.section,
            musescore=musescore,
            keep_mxl=keep_mxl,
        )
    except MvsaValidationError as exc:
        for d in exc.diagnostics:
            print(format_diagnostic(d, path), file=sys.stderr)
        return 1
    except MvsaExportError as exc:
        loc = f"{path}:{exc.line}: " if exc.line else f"{path}: "
        print(f"{loc}ERROR: {exc}", file=sys.stderr)
        return 1
    except MvsaMsczError as exc:
        print(f"{path}: ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Geschreven: {out}")
    if keep_mxl is not None:
        print(f"MXL: {keep_mxl}")
    return 0


def _cmd_mvsa_import(args) -> int:
    from .mvsa_import import MvsaImportError, import_score_path

    path = Path(args.path)
    if not path.is_file():
        print(f"Bestand niet gevonden: {path}", file=sys.stderr)
        return 1
    out = (
        Path(args.output)
        if args.output
        else path.with_name(f"{path.stem}.import.mvsa")
    )
    musescore = Path(args.musescore) if args.musescore else None
    try:
        import_score_path(
            path,
            out,
            pitch=args.pitch,
            octave_style=args.octave_style,
            align=not args.no_align,
            section_id=args.section,
            musescore=musescore,
        )
    except MvsaImportError as exc:
        print(f"{path}: ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Geschreven: {out}")
    return 0


def _cmd_mvsa_normalize(args) -> int:
    from .mvsa_normalize import MvsaNormalizeError, normalize_mvsa_path
    from .mvsa_validate import MvsaValidationError, format_diagnostic

    path = Path(args.path)
    if not path.is_file():
        print(f"Bestand niet gevonden: {path}", file=sys.stderr)
        return 1
    out = (
        Path(args.output)
        if args.output
        else path.with_name(f"{path.stem}.normalized.mvsa")
    )
    try:
        normalize_mvsa_path(
            path,
            out,
            pitch=args.pitch,
            octave_style=args.octave_style,
            align=not args.no_align,
        )
    except MvsaValidationError as exc:
        for d in exc.diagnostics:
            print(format_diagnostic(d, path), file=sys.stderr)
        return 1
    except MvsaNormalizeError as exc:
        loc = f"{path}:{exc.line}: " if exc.line else f"{path}: "
        print(f"{loc}ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Geschreven: {out}")
    return 0


def _cmd_template_validate(args) -> int:
    from .template_validate import (
        TemplateValidationError,
        collect_template_ids,
        load_template,
        validate_template,
    )

    path = Path(args.path)
    if not path.exists():
        print(f"Pad niet gevonden: {path}", file=sys.stderr)
        return 1
    files: list[Path]
    if path.is_dir():
        files = sorted(path.rglob("template.yaml"))
        known_ids = collect_template_ids(path)
    else:
        files = [path]
        known_ids = collect_template_ids(path.parent)
        parent2 = path.parent.parent
        if parent2.is_dir():
            known_ids |= collect_template_ids(parent2)
    if not files:
        print(f"Geen template.yaml gevonden onder {path}", file=sys.stderr)
        return 1
    errors = 0
    for yaml_path in files:
        try:
            validate_template(load_template(yaml_path), known_ids=known_ids)
        except TemplateValidationError as exc:
            print(f"{yaml_path}: ERROR: {exc.code}: {exc}", file=sys.stderr)
            errors += 1
            continue
        print(f"{yaml_path}: OK")
    if errors:
        print(f"{errors} template(s) ongeldig", file=sys.stderr)
        return 1
    return 0


def _print_validation_messages(messages, *, summary=False):
    source_lines: dict[str, list[str]] = {}

    for message in messages:
        source_line = None
        if not summary:
            source_line = _validation_context_line(message.source, message.line, source_lines)

        for line in format_validation_message(
            message,
            summary=summary,
            source_line=source_line,
        ):
            print(line)


def _validation_context_line(source: str, line_number: int, cache: dict[str, list[str]]) -> str | None:
    if source not in cache:
        path = Path(source)
        if not path.is_file():
            return None
        cache[source] = path.read_text(encoding="utf-8").splitlines()

    lines = cache[source]
    if line_number < 1 or line_number > len(lines):
        return None

    return lines[line_number - 1]


if __name__ == "__main__":
    raise SystemExit(main())
