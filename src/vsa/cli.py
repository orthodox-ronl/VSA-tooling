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
from .derived_path import derived_output_path
from .input_paths import InputPathError, collect_cli_sources
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

    svg = subparsers.add_parser(
        "svg",
        help="Render .vsa naar muziek-only SVG (default: sibling .vsa.svg).",
        description=(
            "Render eenstemmige .vsa naar SVG (alleen notatie, geen titel). "
            "INPUT = één .vsa of map (recursief). Default-uitvoer: sibling "
            "<bronnaam>.vsa.svg naast elke bron (zelfde naamgeving als "
            "mvsa svg → .mvsa.svg). -o/--output alleen bij precies één bron."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Voorbeelden:\n"
            "  vsa svg examples\\minimal\\050_svg_demo.vsa\n"
            "  vsa svg lied.vsa -o generated\\lied.vsa.svg\n"
            "  vsa svg examples\\minimal --max-line-width 400"
        ),
    )
    svg.add_argument(
        "input",
        help=".vsa-bestand of map met .vsa-bestanden (recursief).",
    )
    svg.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        default=None,
        help=(
            "Uitvoer-.svg (default: sibling <naam>.vsa.svg per bron). "
            "Alleen bij precies één bronbestand."
        ),
    )
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

    text_cmd = subparsers.add_parser(
        "text",
        help=(
            "Platte gezongen tekst uit .vsa / .mvsa / MusicXML / .mscz "
            "(zonder notatie; voor zoekindex)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Bronnen:\n"
            "  .vsa / .mvsa — directe extractie\n"
            "  .mxl / .musicxml / .xml — lyrics uit MusicXML\n"
            "  .mscz — via tijdelijke MuseScore-.mxl (geen .mvsa)\n"
            "\n"
            "MusicXML-regel: eerste part met lyric number 1; geen dubbele\n"
            "SATB-lyrics. Alias voor .mscz: mscz text PATH.\n"
            "\n"
            "PATH = één bronbestand of map (recursief). "
            "-o alleen bij precies één bron.\n"
            "\n"
            "voorbeelden:\n"
            "  vsa text lied.vsa\n"
            "  vsa text lied.mscz.mxl -o lied.lyrics.txt\n"
            "  vsa text lied.mscz --musescore \"C:\\\\Program Files\\\\MuseScore 4\\\\bin\\\\MuseScore4.exe\""
        ),
    )
    text_cmd.add_argument(
        "path",
        help=(
            ".vsa/.mvsa/.mxl/.musicxml/.xml/.mscz-bestand, of map met "
            "zulke bestanden (recursief)."
        ),
    )
    text_cmd.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Schrijf platte tekst naar dit bestand i.p.v. stdout. "
            "Alleen bij precies één bronbestand."
        ),
    )
    text_cmd.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore (alleen bij .mscz; default: auto).",
    )

    zoektekst_cmd = subparsers.add_parser(
        "zoektekst",
        help=(
            "Vul of controleer YAML-zoektekst in canonieke .vsa / .mvsa "
            "(platte gezongen tekst voor editorzoeken)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Default: schrijf/update zoektekst in-place.\n"
            "--check = geen schrijven; exit 1 bij ontbrekend/afwijkend veld.\n"
            "\n"
            "voorbeelden:\n"
            "  vsa zoektekst examples\\mvsa\\alleluia-toon-1.mvsa\n"
            "  vsa zoektekst examples\\mvsa --check\n"
            "  vsa zoektekst lied.vsa -o generated\\lied.zoektekst.vsa\n"
            "\n"
            "Contract: docs/formats/zoektekst.md"
        ),
    )
    zoektekst_cmd.add_argument(
        "paths",
        nargs="+",
        help=".vsa / .mvsa-bestand of map (recursief).",
    )
    zoektekst_cmd.add_argument(
        "--check",
        action="store_true",
        help="Alleen controleren (geen schrijven); exit 1 bij problemen.",
    )
    zoektekst_cmd.add_argument(
        "-o",
        "--output",
        default=None,
        help="Schrijf naar dit pad i.p.v. in-place (alleen bij één bronbestand).",
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

    audio = subparsers.add_parser(
        "audio",
        help="Exporteer naar audio (.mp3/.ogg/.wav) via MuseScore (preview-luisteren).",
        description=(
            "Maak een afspeelbaar audiobestand uit playback-MusicXML of "
            ".vsa / .mvsa / .mscz (via .mxl). Alleen het artefact - geen "
            "speler. Vereist MuseScore 4 (of 3)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "INPUT = één bronbestand of map (recursief). Bij een map is "
            "OUTPUT een uitvoermap; --keep-mxl alleen bij één bron.\n"
            "\n"
            "voorbeelden:\n"
            "  vsa audio examples\\docs-walkthroughs\\coria-oefenlink\\"
            "oefenmelodie.vsa generated\\oefenmelodie.mp3\n"
            "  vsa audio lied.mxl generated\\lied.mp3\n"
            "  vsa audio lied.mxl generated\\lied --format ogg"
        ),
    )
    audio.add_argument(
        "input",
        help=(
            ".mxl/.musicxml/.vsa/.mvsa/.mscz-bestand, of map met zulke "
            "bestanden (recursief)."
        ),
    )
    audio.add_argument(
        "output",
        help=(
            "Uitvoerbestand (.mp3/.ogg/.wav), of uitvoermap bij meerdere "
            "bronnen."
        ),
    )
    audio.add_argument("--config", default=None)
    audio.add_argument(
        "--format",
        choices=["mp3", "ogg", "wav"],
        default=None,
        help=(
            "Uitvoerformaat wanneer output geen expliciete extensie heeft "
            "(default: mp3, of [audio].format in vsa.toml)."
        ),
    )
    audio.add_argument(
        "--musescore",
        metavar="PATH",
        default=None,
        help="Pad naar MuseScore-executable (default: auto-detectie).",
    )
    audio.add_argument(
        "--section",
        metavar="SECTION",
        default=None,
        help="Alleen bij .mvsa: deze @sectie-id (default: alle secties).",
    )
    audio.add_argument(
        "--keep-mxl",
        metavar="PATH",
        default=None,
        help=(
            "Bewaar ook het tussenliggende playback-.mxl op dit pad. "
            "Alleen bij precies één bronbestand."
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
            "  mxl PATH [-o OUTPUT] [--section SECTION]\n"
            "      Exporteer naar SATB MusicXML (.mxl/.musicxml).\n"
            "  score-ir PATH [-o OUTPUT] [--section SECTION]\n"
            "      Exporteer naar Score-IR JSON (partituur; koormap/CoriB).\n"
            "  mscz PATH [-o OUTPUT] [--section SECTION]\n"
            "      Exporteer naar MuseScore (.mscz) via .mxl.\n"
            "  pdf PATH [-o OUTPUT] [--section SECTION]\n"
            "      Exporteer naar print-PDF via MuseScore.\n"
            "  svg PATH [-o OUTPUT] [--section SECTION]\n"
            "      Exporteer naar muziek-only SVG (koormap; MuseScore-brug).\n"
            "  mp3|ogg|wav PATH [-o OUTPUT]\n"
            "      Exporteer naar preview-audio (.mp3 / .ogg / .wav) via MuseScore.\n"
            "  normalize PATH [-o OUTPUT] [--pitch {preserve,doremi,a-g,vsa,ag-vsa}]\n"
            "      Canoniseer .mvsa (default: behoud noteernamen; optioneel herschrijf).\n"
            "  transpose PATH --to TONIC [-o OUTPUT] [--pitch {doremi,a-g,vsa,ag-vsa}]\n"
            "      Transponeer naar opgegeven tonica (@do); @mode blijft gelijk.\n"
            "  kuiser PATH [PATH…] [-o OUTPUT] [--check] [--pitch …]\n"
            "      Authoring-kuiser: strepen syncen, woordstreep-spatie, align "
            "(+ optioneel pitch).\n"
            "\n"
            "voorbeelden:\n"
            "  mvsa validate examples\\mvsa\n"
            "  mvsa mxl lied.mvsa -o out.mxl --section schets1\n"
            "  mvsa mscz lied.mvsa -o out.mscz\n"
            "  mvsa mp3 lied.mvsa -o out.mp3\n"
            "  mvsa ogg lied.mvsa\n"
            "  mvsa normalize lied.mvsa -o out.mvsa\n"
            "  mvsa normalize lied.mvsa -o out.mvsa --pitch a-g\n"
            "  mvsa transpose lied.mvsa --to F4 -o out.mvsa\n"
            "  mvsa kuiser lied.mvsa\n"
            "  mvsa kuiser examples\\mvsa --check\n"
            "\n"
            "Andere bronnen: mxl … / mscz …\n"
            "Score → .mvsa: mxl mvsa … / mscz mvsa …\n"
            "\n"
            "Hulp: mvsa validate -h | mvsa mxl -h | "
            "mvsa mscz -h | mvsa pdf -h | mvsa svg -h | "
            "mvsa mp3 -h | "
            "mvsa ogg -h | mvsa wav -h | "
            "mvsa score-ir -h | "
            "mvsa normalize -h | "
            "mvsa transpose -h | mvsa kuiser -h"
        ),
    )
    mvsa_sub = mvsa.add_subparsers(
        dest="mvsa_command",
        required=True,
        metavar="{validate,mxl,mscz,pdf,svg,mp3,ogg,wav,score-ir,normalize,transpose,kuiser}",
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
    m_validate.add_argument(
        "--require-zoektekst",
        action="store_true",
        help=(
            "Eis genormaliseerde YAML-zoektekst gelijk aan body "
            "(catalogusbronnen; zie docs/formats/zoektekst.md)."
        ),
    )
    m_musicxml = mvsa_sub.add_parser(
        "mxl",
        aliases=["musicxml"],
        help="Exporteer .mvsa/.mscz/.mxl naar Coria-playback MusicXML.",
        description=(
            "Schrijf een Coria-playback-.mxl. Bron .mvsa: SATB-export. "
            "Bron .mscz: MuseScore → playback-normalisatie (zelfde als mscz mxl). "
            "Bron .mxl/.musicxml: normaliseer naar playback. "
            "Alias: musicxml (verouderd)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mvsa mxl examples\\mvsa\\kleine-intocht-zondag-hemelum.mvsa\n"
            "  mvsa mxl lied.mvsa -o generated\\lied.mxl\n"
            "  mvsa mxl lied.mvsa --section schets-a-bladcijfer -o out.mxl\n"
            "  mvsa mxl lied.mscz -o generated\\lied.mxl"
        ),
    )
    m_musicxml.add_argument(
        "path",
        help=(
            ".mvsa-/.mscz-/.mxl/.musicxml-bestand, of map met zulke "
            "bestanden (recursief)."
        ),
    )
    m_musicxml.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        default=None,
        help=(
            "Uitvoer-.mxl (default: sibling per bron). "
            "Alleen bij precies één bronbestand."
        ),
    )
    m_musicxml.add_argument(
        "--section",
        metavar="SECTION",
        default=None,
        help="Alleen bij .mvsa: deze @sectie-id (default: alle secties).",
    )
    m_musicxml.add_argument(
        "--bibliotheek-id",
        metavar="ID",
        default=None,
        dest="bibliotheek_id",
        help=(
            "Alleen bij .mvsa: bibliotheek-id in MusicXML identification/rights "
            "(default: pad-sniff onder content-source/bibliotheek)."
        ),
    )
    m_musicxml.add_argument(
        "--hulptekst",
        action="store_true",
        help=(
            "Alleen bij .mvsa: tweede lyric-laag (number=2): ksl→Latijn / "
            "nl→Cyrillisch per lettergreep."
        ),
    )
    m_musicxml.add_argument(
        "--hulptekst-as-parts",
        action="store_true",
        dest="hulptekst_as_parts",
        help=(
            "Alleen bij .mvsa: Coria-extra SATB-parts met hulptekst (volume 0). "
            "Part-namen: Soprano (ksl)/(nl) via @taal. "
            "Impliceert --hulptekst. Alleen playback-layout."
        ),
    )
    m_musicxml.add_argument(
        "--musescore",
        metavar="PATH",
        default=None,
        help="Pad naar MuseScore (alleen bij .mscz; default: auto).",
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
            "  mvsa mscz examples\\mvsa\\alleluia-toon-8.canonieke.mvsa\n"
            "  mvsa mscz lied.mvsa -o generated\\lied.mscz "
            "--section schets2-oct-doremi\n"
            "  mvsa mscz lied.mvsa -o out.mscz --layout partituur "
            "--bibliotheek-id zangstuk/var/uv\n"
            "  mvsa mscz lied.mvsa -o out.mscz --keep-mxl generated\\lied.mxl"
        ),
    )
    m_mscz.add_argument(
        "path",
        help=".mvsa-bestand of map met .mvsa-bestanden (recursief).",
    )
    m_mscz.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        default=None,
        help=(
            "Uitvoer-.mscz (default: sibling naast elke bron, bijv. "
            "lied.mvsa.mscz). Alleen bij precies één bronbestand."
        ),
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
    m_mscz.add_argument(
        "--layout",
        metavar="PROFILE",
        default=None,
        help=(
            "MSCZ-layoutprofiel: partituur (default; A4/leesbaarheid/colofon), "
            "muziek (zelfde zonder titel/colofon; koormap-SVG), of plain "
            "(geen nabewerking). Zie docs/formats/mscz-leesbaarheid.md."
        ),
    )
    m_mscz.add_argument(
        "--bibliotheek-id",
        metavar="ID",
        default=None,
        dest="bibliotheek_id",
        help=(
            "Expliciete bibliotheek-id voor colofon (profiel partituur). "
            "Zonder deze optie: optionele pad-afleiding. Consumer bepaalt de id."
        ),
    )
    m_mscz.add_argument(
        "--hulptekst",
        action="store_true",
        help=(
            "Tweede lyric-laag (number=2) in partituur-MXL: ksl→Latijn / "
            "nl→Cyrillisch."
        ),
    )
    _add_partituur_style_args(m_mscz)
    m_pdf = mvsa_sub.add_parser(
        "pdf",
        help="Exporteer .mvsa (of .mscz) naar print-PDF voor zangers.",
        description=(
            "Partituur-PDF via MuseScore. Bron .mvsa: keten mvsa -> mscz -> pdf. "
            "Bron .mscz: alleen MuseScore-conversie. Vereist MuseScore 4 (of 3)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mvsa pdf examples\\mvsa\\alleluia-toon-1.mvsa\n"
            "  mvsa pdf lied.mvsa -o generated\\lied.pdf --keep-mscz generated\\lied.mscz\n"
            "  mvsa pdf lied.mvsa --layout partituur --bibliotheek-id zangstuk/var/uv\n"
            "  mvsa pdf lied.mscz -o lied.pdf"
        ),
    )
    m_pdf.add_argument(
        "path",
        help=".mvsa- of .mscz-bestand, of map met zulke bestanden (recursief).",
    )
    m_pdf.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        default=None,
        help=(
            "Uitvoer-.pdf (default: sibling per bron). "
            "Alleen bij precies één bronbestand."
        ),
    )
    m_pdf.add_argument(
        "--section",
        metavar="SECTION",
        default=None,
        help="Alleen bij .mvsa: deze @sectie-id (default: alle secties).",
    )
    m_pdf.add_argument(
        "--musescore",
        metavar="PATH",
        default=None,
        help="Pad naar MuseScore-executable (default: auto-detectie).",
    )
    m_pdf.add_argument(
        "--keep-mscz",
        metavar="PATH",
        default=None,
        help="Bij .mvsa: bewaar ook het tussenliggende .mscz op dit pad.",
    )
    m_pdf.add_argument(
        "--keep-mxl",
        metavar="PATH",
        default=None,
        help="Bij .mvsa: bewaar ook het tussenliggende partituur-.mxl.",
    )
    m_pdf.add_argument(
        "--layout",
        metavar="PROFILE",
        default=None,
        help=(
            "Bij .mvsa: MSCZ-layoutprofiel partituur (default) of plain "
            "(zie mvsa mscz --layout)."
        ),
    )
    m_pdf.add_argument(
        "--bibliotheek-id",
        metavar="ID",
        default=None,
        dest="bibliotheek_id",
        help="Bij .mvsa + layout partituur: expliciete bibliotheek-id voor colofon.",
    )
    _add_partituur_style_args(m_pdf)
    m_svg = mvsa_sub.add_parser(
        "svg",
        help="Exporteer .mvsa of .mscz naar partituur-SVG (koormap).",
        description=(
            "Bron .mvsa: muziek-only SVG via MuseScore (geen titel/colofon), "
            "daarna viewBox-trim. Bron .mscz: alleen MuseScore → SVG (+ trim); "
            "Style/fonts in het .mscz blijven behouden. Vereist MuseScore 4."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mvsa svg examples\\mvsa\\1a-vredeslitanie.mvsa\n"
            "  mvsa svg lied.mvsa -o generated\\lied.mvsa.svg\n"
            "  mvsa svg lied.mvsa --lyrics-font-size 14 --cue-font-size 11\n"
            "  mvsa svg generated\\lied.mscz -o generated\\lied.svg\n"
            "  mvsa svg lied.mvsa --section schets1 --keep-mscz generated\\lied.mscz"
        ),
    )
    m_svg.add_argument(
        "path",
        help=".mvsa- of .mscz-bestand, of map met zulke bestanden (recursief).",
    )
    m_svg.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        default=None,
        help=(
            "Uitvoer-.svg (default: sibling per bron). "
            "Alleen bij precies één bronbestand."
        ),
    )
    m_svg.add_argument(
        "--section",
        metavar="SECTION",
        default=None,
        help="Alleen bij .mvsa: deze @sectie-id (default: alle secties).",
    )
    m_svg.add_argument(
        "--musescore",
        metavar="PATH",
        default=None,
        help="Pad naar MuseScore-executable (default: auto-detectie).",
    )
    m_svg.add_argument(
        "--keep-mscz",
        metavar="PATH",
        default=None,
        help="Bij .mvsa: bewaar ook het tussenliggende .mscz (layout muziek).",
    )
    m_svg.add_argument(
        "--keep-mxl",
        metavar="PATH",
        default=None,
        help="Bij .mvsa: bewaar ook het tussenliggende partituur-.mxl.",
    )
    m_svg.add_argument(
        "--bibliotheek-id",
        metavar="ID",
        default=None,
        dest="bibliotheek_id",
        help="Alleen bij .mvsa; genegeerd voor layout muziek (geen colofon).",
    )
    m_svg.add_argument(
        "--no-trim",
        action="store_true",
        help="Laat MuseScore-A4-SVG ongewijzigd (geen viewBox-trim).",
    )
    m_svg.add_argument(
        "--transparent",
        action="store_true",
        help=(
            "Geen witte achtergrond na trim (transparant). "
            "Default: witte rechthoek achter de notatie."
        ),
    )
    _add_partituur_style_args(m_svg)
    _add_mvsa_audio_format_parsers(mvsa_sub)
    m_normalize = mvsa_sub.add_parser(
        "normalize",
        help="Normaliseer .mvsa (uitlijning; optioneel herschrijf hoogten).",
        description=(
            "Canoniseer een .mvsa-bestand. Default --pitch preserve: "
            "noteernamen op S/A/T/B blijven zoals in de bron; alleen "
            "kolomuitlijning. Met --pitch doremi|a-g|vsa|ag-vsa herschrijf je "
            "hoogten (abc blijft alias van a-g). "
            "(Score → .mvsa via mxl/mscz mvsa gebruikt ag-vsa als default.) "
            "Zie docs/plans/mvsa-conversions.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mvsa normalize examples\\mvsa\\alleluia-toon-8.mvsa "
            "-o generated\\alleluia.normalized.mvsa\n"
            "  mvsa normalize examples\\mvsa\\alleluia-toon-8.mvsa "
            "--pitch a-g -o generated\\alleluia.ag.mvsa\n"
            "  mvsa normalize lied.mvsa --pitch doremi --octave-style @oct"
        ),
    )
    m_normalize.add_argument(
        "path",
        help=".mvsa-bestand of map met .mvsa-bestanden (recursief).",
    )
    m_normalize.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        default=None,
        help=(
            "Uitvoerbestand (default: <stem>.normalized.mvsa per bron). "
            "Alleen bij precies één bronbestand."
        ),
    )
    m_normalize.add_argument(
        "--pitch",
        choices=["preserve", "doremi", "a-g", "abc", "vsa", "ag-vsa"],
        default=None,
        help=(
            "Doel-spelling op stemregels. Default bij .mvsa-bron: preserve "
            "(namen ongewijzigd). doremi / a-g / vsa / ag-vsa herschrijven "
            "hoogten; abc is alias van a-g."
        ),
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
    m_transpose = mvsa_sub.add_parser(
        "transpose",
        help="Transponeer .mvsa naar een opgegeven tonica (@do).",
        description=(
            "Verschuif alle @do-regels en klinkende stemtonen naar --to "
            "(zelfde vorm als @do: F4, Bb3, of F zonder octaafcijfer). "
            "@mode blijft gelijk (majeur blijft majeur). "
            "Default --pitch ag-vsa. Uitvoer: sibling "
            "<stem>.transposed.mvsa (of -o bij één bron)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mvsa transpose "
            "examples\\bug-cases\\alleluia-9b-toon-3-vokn.mvsa --to F4\n"
            "  mvsa transpose lied.mvsa --to F -o generated\\lied.in-F.mvsa\n"
            "  mvsa transpose examples\\bug-cases --to F4"
        ),
    )
    m_transpose.add_argument(
        "path",
        help=".mvsa-bestand of map met .mvsa-bestanden (recursief).",
    )
    m_transpose.add_argument(
        "--to",
        required=True,
        metavar="TONIC",
        help="Doeltonica, bv. F4 of F (octaaf van bron-@do).",
    )
    m_transpose.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        default=None,
        help=(
            "Uitvoerbestand (default: <stem>.transposed.mvsa per bron). "
            "Alleen bij precies één bronbestand."
        ),
    )
    m_transpose.add_argument(
        "--pitch",
        choices=["doremi", "a-g", "abc", "vsa", "ag-vsa"],
        default="ag-vsa",
        help="Spelling op stemregels na transpositie (default: ag-vsa).",
    )
    m_transpose.add_argument(
        "--octave-style",
        choices=["@oct", "marker"],
        default="@oct",
        help="Schrijfoctaaf-stijl (marker nog niet geïmplementeerd).",
    )
    m_transpose.add_argument(
        "--no-align",
        action="store_true",
        help="Sla canonieke kolomuitlijning over.",
    )
    m_score_ir = mvsa_sub.add_parser(
        "score-ir",
        aliases=["ir"],
        help="Exporteer .mvsa naar Score-IR JSON (partituur-profiel).",
        description=(
            "Schrijf Score-IR (format score-ir, profile partituur): "
            "maatgerichte JSON met SA/TB-voices, lyrics en @tekst-cues. "
            "Contract: docs/plans/partituur-ir.md. Alias: ir."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mvsa score-ir examples\\mvsa\\1a-vredeslitanie.mvsa\n"
            "  mvsa score-ir lied.mvsa -o generated\\lied.score-ir.json\n"
            "  mvsa ir lied.mvsa --section schets1 -o out.json\n"
            "  mvsa score-ir lied.mvsa --musicxml\n"
            "  mvsa score-ir lied.mvsa --musicxml generated\\lied.from-ir.musicxml\n"
            "  mvsa score-ir examples\\mvsa --musicxml"
        ),
    )
    m_score_ir.add_argument(
        "path",
        help=".mvsa-bestand of map met .mvsa-bestanden (recursief).",
    )
    m_score_ir.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        default=None,
        help=(
            "Uitvoerbestand (.json). Default: sibling "
            "lied.mvsa.score-ir.json."
        ),
    )
    m_score_ir.add_argument(
        "--section",
        metavar="SECTION",
        default=None,
        help="Alleen deze @sectie-id exporteren.",
    )
    m_score_ir.add_argument(
        "--bibliotheek-id",
        metavar="ID",
        default=None,
        help="Optionele bibliotheek-id in meta.bibliotheekId.",
    )
    m_score_ir.add_argument(
        "--musicxml",
        nargs="?",
        const="",
        default=None,
        metavar="PATH",
        help=(
            "Schrijf ook partituur-MusicXML uit Score-IR (OSMD-brug). "
            "Zonder PATH: sibling lied.mvsa.from-ir.musicxml (ook bij "
            "map). Met PATH: alleen bij precies één bron."
        ),
    )
    m_kuiser = mvsa_sub.add_parser(
        "kuiser",
        help="Kuiser: canonieke authoring-vorm (strepen, woordstreep, align).",
        description=(
            "Pas kuiser-toleranties toe op .mvsa (draft-spec): "
            "canonieke L-standaardduur '~' (ELM '-' → '~'), "
            "waarschuwing bij ambiguë '-' (regel+kolom), "
            "maatstrepen syncen waar eenduidig, daarna kolomuitlijning. "
            "Geen stille 'hei- li'→'hei-li'-collapse. "
            "Default: schrijf in-place. --check = dry-run (exit 1 bij wijziging). "
            "Optioneel --pitch zoals bij normalize. "
            "Zie docs/specification-mvsa/syntax.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mvsa kuiser examples\\mvsa\\alleluia-toon-8.mvsa\n"
            "  mvsa kuiser examples\\mvsa --check\n"
            "  mvsa kuiser lied.mvsa -o generated\\lied.kuiser.mvsa\n"
            "  mvsa kuiser lied.mvsa --pitch a-g"
        ),
    )
    m_kuiser.add_argument(
        "paths",
        nargs="+",
        help=".mvsa-bestand(en) of map(pen) met .mvsa-bestanden.",
    )
    m_kuiser.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        default=None,
        help=(
            "Uitvoerbestand (alleen bij één bronbestand). "
            "Default: schrijf in-place."
        ),
    )
    m_kuiser.add_argument(
        "--check",
        action="store_true",
        help="Dry-run: geen schrijfactie; exit 1 als er iets zou wijzigen.",
    )
    m_kuiser.add_argument(
        "--pitch",
        choices=["preserve", "doremi", "a-g", "abc", "vsa", "ag-vsa"],
        default="preserve",
        help=(
            "Doel-spelling op stemregels (default: preserve). "
            "Zelfde keuzes als normalize."
        ),
    )
    m_kuiser.add_argument(
        "--octave-style",
        choices=["@oct", "marker"],
        default="@oct",
        help="Schrijfoctaaf-stijl (marker nog niet geïmplementeerd).",
    )
    m_kuiser.add_argument(
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

    if args.command == "text":
        return _cmd_text(args)

    if args.command == "zoektekst":
        return _cmd_zoektekst(args)

    if args.command == "musicxml":
        return _cmd_musicxml(args, config)

    if args.command == "audio":
        return _cmd_audio(args, config)

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

    return "0.2.0"


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
                "kind": block.kind,
                "info_string": block.info_string,
                "metadata": (
                    block.effective_metadata()
                    if block.kind == "vsa"
                    else dict(block.metadata)
                ),
                "body": block.body,
            }
            if block.kind == "vsa":
                item["ast"] = block.parse_body().to_dict()
            data.append(item)

        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        vsa_n = sum(1 for b in blocks if b.kind == "vsa")
        mvsa_n = sum(1 for b in blocks if b.kind == "mvsa")
        parts = []
        if vsa_n:
            parts.append(f"{vsa_n} VSA-blok(ken)")
        if mvsa_n:
            parts.append(f"{mvsa_n} mvsa-blok(ken)")
        print(
            (", ".join(parts) + " gevonden")
            if parts
            else "0 notatieblok(ken) gevonden"
        )

    return 0


def _cmd_svg(args, config):
    files = _cli_collect_sources(args.input, (".vsa",))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args):
        return 1

    renderer = SVGRenderer(svg_config=config.rendering.svg)
    renderer.max_line_width = (
        args.max_line_width
        if args.max_line_width is not None
        else config.rendering.max_line_width
    )

    exit_code = 0
    for input_path in files:
        out = (
            Path(args.output)
            if args.output
            else derived_output_path(input_path, ".svg")
        )
        try:
            text = input_path.read_text(encoding="utf-8")
            body, _ = prepare_vsa_body(text, input_path)
            document = Parser(preserve_vsa_source_newlines(body)).parse()
            svg = renderer.render_document(document)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(svg, encoding="utf-8")
        except IncludeVsaError as exc:
            print(f"{input_path}: {exc.message_nl}", file=sys.stderr)
            exit_code = 1
            continue
        except Exception as exc:
            print(f"{input_path}: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"SVG geschreven naar: {out}")
    return exit_code


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

    print(f"{len(result.blocks)} assetbestand(en) gegenereerd")

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
    print(f"{len(result.svg_files)} assetbestand(en) geschreven")
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


def _cmd_text(args) -> int:
    from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError
    from .text_export import plain_text_from_path

    files = _cli_collect_sources(
        args.path, (".vsa", ".mvsa", ".mxl", ".musicxml", ".xml", ".mscz")
    )
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args):
        return 1
    musescore = Path(args.musescore) if getattr(args, "musescore", None) else None
    out_single = Path(args.output) if getattr(args, "output", None) else None
    exit_code = 0
    for path in files:
        try:
            text = plain_text_from_path(path, musescore=musescore)
        except ValueError as exc:
            print(f"{path}: text: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        except (MuseScoreNotFoundError, MuseScoreConvertError) as exc:
            print(f"{path}: text: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        except Exception as exc:  # noqa: BLE001 — CLI toont parsefouten leesbaar
            print(f"text: fout bij lezen van {path}: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        if out_single is not None:
            out_single.parent.mkdir(parents=True, exist_ok=True)
            payload = text if text.endswith("\n") or text == "" else text + "\n"
            out_single.write_text(payload, encoding="utf-8", newline="\n")
            print(f"Geschreven: {out_single}")
        else:
            if len(files) > 1:
                print(f"=== {path} ===", flush=True)
            print(text)
    return exit_code


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


def _cmd_audio(args, config) -> int:
    from .audio_export import AudioExportError, export_to_audio, normalize_audio_format
    from .mvsa_musicxml import MvsaExportError
    from .mvsa_validate import MvsaValidationError, format_diagnostic

    files = _cli_collect_sources(
        args.input, (".mxl", ".musicxml", ".xml", ".vsa", ".mvsa", ".mscz")
    )
    if files is None:
        return 1
    # Positional ``output`` is altijd gezet; bij meerdere bronnen = uitvoermap.
    if len(files) > 1 and getattr(args, "keep_mxl", None):
        print(
            "--keep-mxl is alleen toegestaan bij precies één bronbestand.",
            file=sys.stderr,
        )
        return 1
    format_name = normalize_audio_format(args.format or config.audio.format)
    out_arg = Path(args.output)
    musescore = Path(args.musescore) if args.musescore else None
    keep_mxl = Path(args.keep_mxl) if args.keep_mxl else None
    if len(files) > 1:
        if out_arg.exists() and out_arg.is_file():
            print(
                "Bij meerdere bronnen moet output een map zijn "
                "(geen bestaand audiobestand).",
                file=sys.stderr,
            )
            return 1
        out_arg.mkdir(parents=True, exist_ok=True)
    exit_code = 0
    for path in files:
        if len(files) > 1:
            out = out_arg / derived_output_path(path, f".{format_name}").name
        else:
            out = out_arg
        try:
            written = export_to_audio(
                path,
                out,
                format_name=format_name,
                musescore=musescore,
                section_id=args.section,
                keep_mxl=keep_mxl,
            )
        except MvsaValidationError as exc:
            for d in exc.diagnostics:
                print(format_diagnostic(d, path), file=sys.stderr)
            exit_code = 1
            continue
        except MvsaExportError as exc:
            loc = f"{path}:{exc.line}: " if exc.line else f"{path}: "
            print(f"{loc}ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        except AudioExportError as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"Audio geschreven naar: {written}")
        if keep_mxl is not None:
            print(f"MXL: {keep_mxl}")
    return exit_code


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
        suffix = f"-{i + 1}" if len(blocks) > 1 else ""
        out_file = output_dir / f"{stem}{suffix}{output_suffix}"

        if block.kind == "mvsa":
            from .mvsa_musicxml import MvsaExportError, export_mvsa_to_musicxml
            from .mvsa_validate import MvsaValidationError

            try:
                xml_str = export_mvsa_to_musicxml(
                    block.body,
                    title=out_file.stem,
                    layout="playback",
                )
            except (MvsaValidationError, MvsaExportError) as exc:
                print(
                    f"{input_path} (blok {i + 1}): fout bij mvsa-MusicXML-export: {exc}",
                    file=sys.stderr,
                )
                return 1, written
            write_musicxml_output(out_file, xml_str)
            written += 1
            continue

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

        write_musicxml_output(out_file, xml_str)
        written += 1

    return 0, written


def _cmd_template(args) -> int:
    if getattr(args, "template_command", None) == "validate":
        return _cmd_template_validate(args)
    print("Gebruik: vsa template validate <pad>", file=sys.stderr)
    return 1


def _cli_collect_sources(
    path: Path | str,
    suffixes: tuple[str, ...] | list[str],
) -> list[Path] | None:
    """Bestand of map → bronlijst; bij fout: stderr + ``None``."""
    try:
        return collect_cli_sources(path, suffixes=suffixes)
    except InputPathError as exc:
        print(str(exc), file=sys.stderr)
        return None


def _cli_reject_multi_single_opts(
    files: list[Path],
    args,
    *attr_names: str,
    output_attr: str = "output",
) -> bool:
    """True = fout (stderr al geschreven). ``-o`` en named attrs alleen bij 1 bron."""
    if len(files) <= 1:
        return False
    if getattr(args, output_attr, None):
        print(
            "-o/--output is alleen toegestaan bij precies één bronbestand "
            "(bij een map: sibling-output per bron).",
            file=sys.stderr,
        )
        return True
    for attr in attr_names:
        if getattr(args, attr, None):
            flag = "--" + attr.replace("_", "-")
            print(
                f"{flag} is alleen toegestaan bij precies één bronbestand.",
                file=sys.stderr,
            )
            return True
    return False


def _add_partituur_style_args(parser: argparse.ArgumentParser) -> None:
    """Shared MuseScore Style overrides (systeemafstand + fonts; partituur/muziek)."""
    parser.add_argument(
        "--compact",
        action="store_true",
        help=(
            "Dichtste Style-baseline: systeemafstand min=max 2 spatium, "
            "lyric-clearance 0.1 (SA/TB), boven-/ondermarge 5 mm. Andere "
            "Style-opties winnen van deze preset. Niet bij --layout plain."
        ),
    )
    parser.add_argument(
        "--min-system-distance",
        type=float,
        metavar="SP",
        default=None,
        dest="min_system_distance",
        help=(
            "Minimale afstand tussen systemen (MuseScore Style, spatium-eenheden). "
            "Default bij partituur/muziek: 8. Niet bij --layout plain."
        ),
    )
    parser.add_argument(
        "--max-system-distance",
        type=float,
        metavar="SP",
        default=None,
        dest="max_system_distance",
        help=(
            "Maximale afstand tussen systemen (MuseScore Style, spatium-eenheden). "
            "Default bij partituur/muziek: 14. Niet bij --layout plain."
        ),
    )
    parser.add_argument(
        "--staff-distance",
        type=float,
        metavar="SP",
        default=None,
        dest="staff_distance",
        help=(
            "Afstand tussen notenbalken binnen één systeem (MuseScore Style "
            "staffDistance + accolade, spatium). Geen vaste default in Style "
            "(MuseScore + lyrics). Niet bij --layout plain."
        ),
    )
    parser.add_argument(
        "--page-margin-top",
        type=float,
        metavar="MM",
        default=None,
        dest="page_margin_top",
        help=(
            "Bovenmarge van de pagina in millimeters (MuseScore Style). "
            "Default bij partituur/muziek: 15. Niet bij --layout plain."
        ),
    )
    parser.add_argument(
        "--page-margin-bottom",
        type=float,
        metavar="MM",
        default=None,
        dest="page_margin_bottom",
        help=(
            "Ondermarge van de pagina in millimeters (MuseScore Style). "
            "Default bij partituur/muziek: 15. Niet bij --layout plain."
        ),
    )
    parser.add_argument(
        "--lyrics-font",
        metavar="FACE",
        default=None,
        dest="lyrics_font",
        help=(
            "Lettertype voor zangtekst (lyrics). Default: Source Sans 3. "
            "Niet bij --layout plain."
        ),
    )
    parser.add_argument(
        "--lyrics-font-size",
        type=float,
        metavar="PT",
        default=None,
        dest="lyrics_font_size",
        help="Puntgrootte voor zangtekst. Default: 13. Niet bij --layout plain.",
    )
    parser.add_argument(
        "--cue-font",
        metavar="FACE",
        default=None,
        dest="cue_font",
        help=(
            "Lettertype voor cues (@tekst / SystemText). Default: Source Sans 3. "
            "Niet bij --layout plain."
        ),
    )
    parser.add_argument(
        "--cue-font-size",
        type=float,
        metavar="PT",
        default=None,
        dest="cue_font_size",
        help="Puntgrootte voor cues. Default: 12. Niet bij --layout plain.",
    )
    parser.add_argument(
        "--measure-spacing",
        type=float,
        metavar="F",
        default=None,
        dest="measure_spacing",
        help=(
            "Horizontale maat-afstand (MuseScore Style measureSpacing). "
            "Default: 1.2. Hoger = meer spreiding. Niet bij --layout plain. "
            "Lost geen cue-brede maten op (aparte maat-width)."
        ),
    )


def _partituur_style_kwargs(args) -> dict:
    """Keyword args for export_mvsa_to_mscz/pdf/svg Style overrides."""
    from .mscz_partituur import apply_compact_style_preset

    kw = {
        "min_system_distance": getattr(args, "min_system_distance", None),
        "max_system_distance": getattr(args, "max_system_distance", None),
        "staff_distance": getattr(args, "staff_distance", None),
        "page_margin_top_mm": getattr(args, "page_margin_top", None),
        "page_margin_bottom_mm": getattr(args, "page_margin_bottom", None),
        "lyrics_min_top_distance": None,
        "lyrics_min_bottom_distance": None,
        "lyrics_min_distance": None,
        "lyrics_font": getattr(args, "lyrics_font", None),
        "lyrics_font_size": getattr(args, "lyrics_font_size", None),
        "cue_font": getattr(args, "cue_font", None),
        "cue_font_size": getattr(args, "cue_font_size", None),
        "measure_spacing": getattr(args, "measure_spacing", None),
    }
    if getattr(args, "compact", False):
        kw = apply_compact_style_preset(kw)
    return kw


def _has_partituur_style_cli(args) -> bool:
    if getattr(args, "compact", False):
        return True
    kw = _partituur_style_kwargs(args)
    return any(v is not None for v in kw.values())


def _add_mvsa_audio_format_parsers(mvsa_sub) -> None:
    """Register ``mp3`` / ``ogg`` / ``wav`` (uitvoer = subcommando-naam)."""
    from .audio_export import AUDIO_FORMATS

    for format_name in AUDIO_FORMATS:
        extra: dict = {}
        if format_name == "mp3":
            extra["aliases"] = ["audio"]
        parser = mvsa_sub.add_parser(
            format_name,
            help=(
                f"Exporteer .mvsa (of .mxl/.mscz) naar audio (.{format_name}) "
                "via MuseScore."
            ),
            description=(
                f"Preview-luisteren: playback-.mxl -> MuseScore -> .{format_name}. "
                "Bron .mvsa/.vsa: eerst MusicXML-playback. .mscz: fallback via .mxl. "
                "Alleen het artefact; de consumer-site maakt de afspeelknop."
                + (
                    " Alias: audio (verouderd; zelfde als mp3)."
                    if format_name == "mp3"
                    else ""
                )
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=(
                "voorbeelden:\n"
                f"  mvsa {format_name} examples\\mvsa\\alleluia-toon-1.mvsa\n"
                f"  mvsa {format_name} lied.mvsa "
                f"-o generated\\lied.{format_name}\n"
                f"  mvsa {format_name} lied.mxl\n"
                f"  mvsa {format_name} lied.mscz"
            ),
            **extra,
        )
        parser.add_argument(
            "path",
            help=(
                ".mvsa-/.mxl-/.musicxml-/.vsa-/.mscz-bestand, of map "
                "(recursief)."
            ),
        )
        parser.add_argument(
            "-o",
            "--output",
            metavar="OUTPUT",
            default=None,
            help=(
                f"Uitvoer-audio (default: sibling .{format_name} per bron). "
                "Alleen bij precies één bronbestand."
            ),
        )
        parser.add_argument(
            "--section",
            metavar="SECTION",
            default=None,
            help="Alleen bij .mvsa: deze @sectie-id (default: alle secties).",
        )
        parser.add_argument(
            "--musescore",
            metavar="PATH",
            default=None,
            help="Pad naar MuseScore-executable (default: auto-detectie).",
        )
        parser.add_argument(
            "--keep-mxl",
            metavar="PATH",
            default=None,
            help="Bewaar ook het tussenliggende playback-.mxl op dit pad.",
        )


def _cmd_mvsa(args) -> int:
    from .audio_export import AUDIO_FORMATS

    if getattr(args, "mvsa_command", None) == "validate":
        return _cmd_mvsa_validate(args)
    if getattr(args, "mvsa_command", None) in ("mxl", "musicxml"):
        return _cmd_mvsa_musicxml(args)
    if getattr(args, "mvsa_command", None) == "mscz":
        return _cmd_mvsa_mscz(args)
    if getattr(args, "mvsa_command", None) == "pdf":
        return _cmd_mvsa_pdf(args)
    if getattr(args, "mvsa_command", None) == "svg":
        return _cmd_mvsa_svg(args)
    if getattr(args, "mvsa_command", None) in (*AUDIO_FORMATS, "audio"):
        return _cmd_mvsa_audio(args)
    if getattr(args, "mvsa_command", None) == "normalize":
        return _cmd_mvsa_normalize(args)
    if getattr(args, "mvsa_command", None) == "transpose":
        return _cmd_mvsa_transpose(args)
    if getattr(args, "mvsa_command", None) in ("score-ir", "ir"):
        return _cmd_mvsa_score_ir(args)
    if getattr(args, "mvsa_command", None) == "kuiser":
        return _cmd_mvsa_kuiser(args)
    # required=True op subparsers voorkomt dit normaal; fallback voor duidelijkheid.
    print(
        "Gebruik: mvsa "
        "{validate,mxl,mscz,pdf,svg,mp3,ogg,wav,score-ir,normalize,transpose,kuiser} …\n"
        "  mvsa validate PATH\n"
        "  mvsa mxl PATH [-o OUTPUT] [--section SECTION]\n"
        "  mvsa score-ir PATH [-o OUTPUT] [--section SECTION]\n"
        "  mvsa mscz PATH [-o OUTPUT] [--section SECTION]\n"
        "  mvsa pdf PATH [-o OUTPUT] [--section SECTION] [--keep-mscz PATH]\n"
        "  mvsa svg PATH [-o OUTPUT] [--section SECTION] [--keep-mscz PATH]\n"
        "  mvsa mp3|ogg|wav PATH [-o OUTPUT]\n"
        "  mvsa normalize PATH [--pitch {preserve,doremi,a-g,vsa,ag-vsa}] [-o OUTPUT]\n"
        "  mvsa transpose PATH --to TONIC [-o OUTPUT]\n"
        "  mvsa kuiser PATH [PATH…] [--check] [-o OUTPUT]\n"
        "Score → .mvsa: mxl mvsa … / mscz mvsa …\n"
        "Hulp: mvsa -h | mvsa kuiser -h",
        file=sys.stderr,
    )
    return 1


def _cmd_mvsa_validate(args) -> int:
    from .mvsa_validate import (
        MvsaDiagnostic,
        collect_mvsa_files,
        format_diagnostic,
        validate_mvsa_path,
    )
    from .zoektekst import check_zoektekst

    path = Path(args.path)
    if not path.exists():
        print(f"Pad niet gevonden: {path}", file=sys.stderr)
        return 1
    files = collect_mvsa_files(path)
    if not files:
        print(f"Geen .mvsa gevonden onder {path}", file=sys.stderr)
        return 1
    errors = 0
    had_messages = False
    require_zt = bool(getattr(args, "require_zoektekst", False))
    for mvsa_path in files:
        diags = list(validate_mvsa_path(mvsa_path))
        if require_zt:
            text = mvsa_path.read_text(encoding="utf-8-sig")
            for issue in check_zoektekst(text, kind="mvsa", require=True):
                diags.append(
                    MvsaDiagnostic(
                        issue.code,
                        issue.message,
                        1,
                        severity=issue.severity,
                    )
                )
        fatal = [d for d in diags if d.severity == "error"]
        for d in diags:
            had_messages = True
            print(
                format_diagnostic(d, mvsa_path),
                file=sys.stderr if d.severity == "error" else sys.stdout,
            )
        if fatal:
            errors += 1
    if errors:
        print(f"{errors} mvsa-bestand(en) ongeldig", file=sys.stderr)
        return 1
    if not had_messages:
        print("OK")
    return 0


def _cmd_zoektekst(args) -> int:
    from .zoektekst import (
        apply_zoektekst,
        check_zoektekst,
        iter_vsa_mvsa_files,
        kind_from_path,
    )

    paths = [Path(p) for p in args.paths]
    files: list[Path] = []
    for path in paths:
        try:
            files.extend(iter_vsa_mvsa_files(path))
        except FileNotFoundError:
            print(f"Pad niet gevonden: {path}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"zoektekst: {exc}", file=sys.stderr)
            return 1

    # Uniek, stabiele volgorde
    seen: set[Path] = set()
    unique: list[Path] = []
    for f in files:
        key = f.resolve()
        if key in seen:
            continue
        seen.add(key)
        unique.append(f)
    files = unique

    if not files:
        print("Geen .vsa / .mvsa gevonden.", file=sys.stderr)
        return 1

    if args.output is not None:
        if len(files) != 1 or not paths[0].is_file():
            print(
                "zoektekst: -o alleen bij precies één bronbestand.",
                file=sys.stderr,
            )
            return 1

    errors = 0
    changed_n = 0
    for file_path in files:
        try:
            kind = kind_from_path(file_path)
        except ValueError as exc:
            print(f"{file_path}: {exc}", file=sys.stderr)
            errors += 1
            continue
        text = file_path.read_text(encoding="utf-8-sig")
        if args.check:
            issues = check_zoektekst(text, kind=kind, require=True)
            if issues:
                errors += 1
                for issue in issues:
                    print(
                        f"{file_path}: ERROR: {issue.code}: {issue.message}",
                        file=sys.stderr,
                    )
            else:
                print(f"{file_path}: OK")
            continue

        result = apply_zoektekst(text, kind=kind)
        target = Path(args.output) if args.output else file_path
        if result.changed:
            changed_n += 1
            target.write_text(result.text, encoding="utf-8", newline="\n")
            print(f"{file_path} -> {target}: zoektekst bijgewerkt")
        else:
            print(f"{file_path}: geen wijzigingen")

    if args.check:
        return 1 if errors else 0
    if errors:
        return 1
    if changed_n == 0 and len(files) > 1:
        print("OK")
    return 0


def _cmd_mvsa_score_ir(args) -> int:
    from .mvsa_musicxml import MvsaExportError
    from .mvsa_validate import MvsaValidationError, format_diagnostic
    from .score_ir import export_mvsa_path_to_score_ir
    from .score_ir_musicxml import (
        ScoreIrMusicxmlError,
        export_score_ir_path_to_musicxml,
    )

    files = _cli_collect_sources(args.path, (".mvsa",))
    if files is None:
        return 1
    # Explicit --musicxml PATH only for one source; bare --musicxml = siblings.
    mxl_opt = getattr(args, "musicxml", None)
    if mxl_opt not in (None, "") and _cli_reject_multi_single_opts(
        files, args, "musicxml"
    ):
        return 1
    if _cli_reject_multi_single_opts(files, args):
        return 1
    exit_code = 0
    for path in files:
        out = (
            Path(args.output)
            if args.output
            else derived_output_path(path, ".score-ir.json")
        )
        mxl_path = None
        if mxl_opt is not None:
            if mxl_opt == "":
                mxl_path = derived_output_path(path, ".from-ir.musicxml")
            else:
                mxl_path = Path(mxl_opt)
                if mxl_path.suffix.lower() not in {".musicxml", ".xml", ".mxl"}:
                    mxl_path = mxl_path.with_suffix(".musicxml")
        try:
            export_mvsa_path_to_score_ir(
                path,
                out,
                section_id=args.section,
                bibliotheek_id=getattr(args, "bibliotheek_id", None),
            )
            if mxl_path is not None:
                export_score_ir_path_to_musicxml(out, mxl_path)
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
        except ScoreIrMusicxmlError as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"Geschreven: {out}")
        if mxl_path is not None:
            print(f"MusicXML: {mxl_path}")
    return exit_code


def _cmd_mvsa_musicxml(args) -> int:
    from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError
    from .musicxml_package import musicxml_output_suffix
    from .musicxml_playback_normalize import (
        export_mscz_to_playback_mxl,
        normalize_playback_mxl_path,
    )
    from .mvsa_musicxml import MvsaExportError, export_mvsa_path
    from .mvsa_validate import MvsaValidationError, format_diagnostic

    files = _cli_collect_sources(
        args.path, (".mvsa", ".mscz", ".mxl", ".musicxml", ".xml")
    )
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args):
        return 1
    mvsa_only = (
        args.section
        or getattr(args, "bibliotheek_id", None)
        or bool(getattr(args, "hulptekst", False))
        or bool(getattr(args, "hulptekst_as_parts", False))
    )
    exit_code = 0
    for path in files:
        out = (
            Path(args.output)
            if args.output
            else derived_output_path(path, ".mxl")
        )
        if out.suffix.lower() not in {".mxl", ".musicxml", ".xml"}:
            out = out.with_suffix(musicxml_output_suffix(path=out))
        suffix = path.suffix.lower()
        try:
            if suffix == ".mvsa":
                export_mvsa_path(
                    path,
                    out,
                    section_id=args.section,
                    bibliotheek_id=getattr(args, "bibliotheek_id", None),
                    hulptekst=bool(getattr(args, "hulptekst", False)),
                    hulptekst_as_parts=bool(
                        getattr(args, "hulptekst_as_parts", False)
                    ),
                )
            elif suffix == ".mscz":
                if mvsa_only:
                    print(
                        "mvsa mxl: --section/--bibliotheek-id/--hulptekst/"
                        "--hulptekst-as-parts gelden alleen bij .mvsa",
                        file=sys.stderr,
                    )
                    exit_code = 1
                    continue
                musescore = (
                    Path(args.musescore)
                    if getattr(args, "musescore", None)
                    else None
                )
                export_mscz_to_playback_mxl(path, out, musescore=musescore)
            elif suffix in {".mxl", ".musicxml", ".xml"}:
                if mvsa_only:
                    print(
                        "mvsa mxl: --section/--bibliotheek-id/--hulptekst/"
                        "--hulptekst-as-parts gelden alleen bij .mvsa",
                        file=sys.stderr,
                    )
                    exit_code = 1
                    continue
                if getattr(args, "musescore", None):
                    print(
                        "mvsa mxl: --musescore geldt alleen bij .mscz",
                        file=sys.stderr,
                    )
                    exit_code = 1
                    continue
                normalize_playback_mxl_path(path, out, apply_timing=True)
            else:
                print(
                    f"mvsa mxl verwacht .mvsa, .mscz of .mxl/.musicxml, "
                    f"kreeg: {path.name}",
                    file=sys.stderr,
                )
                exit_code = 1
                continue
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
        except (MuseScoreNotFoundError, MuseScoreConvertError) as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"Geschreven: {out}")
    return exit_code


def _cmd_mvsa_mscz(args) -> int:
    from .mvsa_mscz import MvsaMsczError, export_mvsa_to_mscz
    from .mvsa_musicxml import MvsaExportError
    from .mvsa_validate import MvsaValidationError, format_diagnostic

    files = _cli_collect_sources(args.path, (".mvsa",))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args, "keep_mxl"):
        return 1
    musescore = Path(args.musescore) if args.musescore else None
    exit_code = 0
    for path in files:
        out = (
            Path(args.output)
            if args.output
            else derived_output_path(path, ".mscz")
        )
        keep_mxl = Path(args.keep_mxl) if args.keep_mxl else None
        try:
            export_mvsa_to_mscz(
                path,
                out,
                section_id=args.section,
                musescore=musescore,
                keep_mxl=keep_mxl,
                layout=getattr(args, "layout", None),
                bibliotheek_id=getattr(args, "bibliotheek_id", None),
                hulptekst=bool(getattr(args, "hulptekst", False)),
                **_partituur_style_kwargs(args),
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


def _cmd_mvsa_pdf(args) -> int:
    from .mvsa_mscz import (
        MvsaMsczError,
        export_mscz_to_pdf,
        export_mvsa_to_pdf,
    )
    from .mvsa_musicxml import MvsaExportError
    from .mvsa_validate import MvsaValidationError, format_diagnostic

    files = _cli_collect_sources(args.path, (".mvsa", ".mscz"))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args, "keep_mscz", "keep_mxl"):
        return 1
    musescore = Path(args.musescore) if args.musescore else None
    exit_code = 0
    for path in files:
        out = (
            Path(args.output)
            if args.output
            else derived_output_path(path, ".pdf")
        )
        suffix = path.suffix.lower()
        try:
            if suffix == ".mscz":
                if (
                    args.section
                    or args.keep_mscz
                    or args.keep_mxl
                    or args.layout
                    or args.bibliotheek_id
                    or _has_partituur_style_cli(args)
                ):
                    print(
                        "mvsa pdf: --section/--keep-mscz/--keep-mxl/--layout/"
                        "--bibliotheek-id en Style-opties "
                        "(systeem-/stafafstand/marges/fonts) "
                        "gelden alleen bij .mvsa",
                        file=sys.stderr,
                    )
                    exit_code = 1
                    continue
                export_mscz_to_pdf(path, out, musescore=musescore)
            elif suffix == ".mvsa":
                keep_mscz = Path(args.keep_mscz) if args.keep_mscz else None
                keep_mxl = Path(args.keep_mxl) if args.keep_mxl else None
                export_mvsa_to_pdf(
                    path,
                    out,
                    section_id=args.section,
                    musescore=musescore,
                    keep_mscz=keep_mscz,
                    keep_mxl=keep_mxl,
                    layout=args.layout,
                    bibliotheek_id=args.bibliotheek_id,
                    **_partituur_style_kwargs(args),
                )
            else:
                print(
                    f"mvsa pdf verwacht .mvsa of .mscz, kreeg: {path.name}",
                    file=sys.stderr,
                )
                exit_code = 1
                continue
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
        if args.keep_mscz:
            print(f"MSCZ: {args.keep_mscz}")
        if args.keep_mxl:
            print(f"MXL: {args.keep_mxl}")
    return exit_code


def _cmd_mvsa_svg(args) -> int:
    from .mvsa_mscz import MvsaMsczError, export_mscz_to_svg, export_mvsa_to_svg
    from .mvsa_musicxml import MvsaExportError
    from .mvsa_validate import MvsaValidationError, format_diagnostic

    files = _cli_collect_sources(args.path, (".mvsa", ".mscz"))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args, "keep_mscz", "keep_mxl"):
        return 1
    musescore = Path(args.musescore) if args.musescore else None
    trim = not bool(getattr(args, "no_trim", False))
    white_background = not bool(getattr(args, "transparent", False))
    exit_code = 0
    for path in files:
        out = (
            Path(args.output)
            if args.output
            else derived_output_path(path, ".svg")
        )
        keep_mscz = Path(args.keep_mscz) if args.keep_mscz else None
        keep_mxl = Path(args.keep_mxl) if args.keep_mxl else None
        suffix = path.suffix.lower()
        try:
            if suffix == ".mscz":
                if (
                    args.section
                    or args.keep_mscz
                    or args.keep_mxl
                    or args.bibliotheek_id
                    or _has_partituur_style_cli(args)
                ):
                    print(
                        "mvsa svg: --section/--keep-mscz/--keep-mxl/"
                        "--bibliotheek-id en Style-opties "
                        "(systeem-/stafafstand/marges/fonts) "
                        "gelden alleen bij .mvsa (bij .mscz staat Style "
                        "al in het bestand)",
                        file=sys.stderr,
                    )
                    exit_code = 1
                    continue
                written = export_mscz_to_svg(
                    path,
                    out,
                    musescore=musescore,
                    trim=trim,
                    white_background=white_background,
                )
            elif suffix == ".mvsa":
                written = export_mvsa_to_svg(
                    path,
                    out,
                    section_id=args.section,
                    musescore=musescore,
                    keep_mscz=keep_mscz,
                    keep_mxl=keep_mxl,
                    bibliotheek_id=getattr(args, "bibliotheek_id", None),
                    trim=trim,
                    white_background=white_background,
                    **_partituur_style_kwargs(args),
                )
            else:
                print(
                    f"mvsa svg verwacht .mvsa of .mscz, kreeg: {path.name}",
                    file=sys.stderr,
                )
                exit_code = 1
                continue
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
        for written_path in written:
            print(f"Geschreven: {written_path}")
        if keep_mscz is not None:
            print(f"MSCZ: {keep_mscz}")
        if keep_mxl is not None:
            print(f"MXL: {keep_mxl}")
    return exit_code


def _cmd_mvsa_audio(args) -> int:
    from .audio_export import AUDIO_FORMATS, AudioExportError, export_to_audio
    from .mvsa_musicxml import MvsaExportError
    from .mvsa_validate import MvsaValidationError, format_diagnostic

    files = _cli_collect_sources(
        args.path, (".mvsa", ".mxl", ".musicxml", ".xml", ".vsa", ".mscz")
    )
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args, "keep_mxl"):
        return 1
    cmd = getattr(args, "mvsa_command", None)
    format_name = cmd if cmd in AUDIO_FORMATS else "mp3"
    musescore = Path(args.musescore) if args.musescore else None
    exit_code = 0
    for path in files:
        out = (
            Path(args.output)
            if args.output
            else derived_output_path(path, f".{format_name}")
        )
        keep_mxl = Path(args.keep_mxl) if args.keep_mxl else None
        try:
            written = export_to_audio(
                path,
                out,
                format_name=format_name,
                musescore=musescore,
                section_id=args.section,
                keep_mxl=keep_mxl,
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
        except AudioExportError as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"Geschreven: {written}")
        if keep_mxl is not None:
            print(f"MXL: {keep_mxl}")
    return exit_code


def _cmd_mvsa_normalize(args) -> int:
    from .mvsa_normalize import MvsaNormalizeError, normalize_mvsa_path
    from .mvsa_validate import MvsaValidationError, format_diagnostic

    files = _cli_collect_sources(args.path, (".mvsa",))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args):
        return 1
    exit_code = 0
    for path in files:
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
            exit_code = 1
            continue
        except MvsaNormalizeError as exc:
            loc = f"{path}:{exc.line}: " if getattr(exc, "line", None) else f"{path}: "
            print(f"{loc}ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"Geschreven: {out}")
    return exit_code


def _cmd_mvsa_transpose(args) -> int:
    from .mvsa_transpose import MvsaTransposeError, transpose_mvsa_path
    from .mvsa_validate import MvsaValidationError, format_diagnostic

    files = _cli_collect_sources(args.path, (".mvsa",))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args):
        return 1
    exit_code = 0
    for path in files:
        out = (
            Path(args.output)
            if args.output
            else path.with_name(f"{path.stem}.transposed.mvsa")
        )
        try:
            transpose_mvsa_path(
                path,
                out,
                to=args.to,
                pitch=args.pitch,
                octave_style=args.octave_style,
                align=not args.no_align,
            )
        except MvsaValidationError as exc:
            for d in exc.diagnostics:
                print(format_diagnostic(d, path), file=sys.stderr)
            exit_code = 1
            continue
        except MvsaTransposeError as exc:
            loc = f"{path}:{exc.line}: " if getattr(exc, "line", None) else f"{path}: "
            print(f"{loc}ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"Geschreven: {out}")
    return exit_code


def _cmd_mvsa_kuiser(args) -> int:
    from .mvsa_kuiser import MvsaKuiserError, kuiser_mvsa_path
    from .mvsa_normalize import MvsaNormalizeError
    from .mvsa_validate import MvsaValidationError, format_diagnostic

    files: list[Path] = []
    for raw in args.paths:
        batch = _cli_collect_sources(raw, (".mvsa",))
        if batch is None:
            return 1
        files.extend(batch)
    # Deduplicate while preserving order
    seen: set[Path] = set()
    uniq: list[Path] = []
    for f in files:
        key = f.resolve()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(f)
    files = uniq
    if _cli_reject_multi_single_opts(files, args):
        return 1

    would_change = 0
    errors = 0
    for path in files:
        out = Path(args.output) if args.output is not None else None
        try:
            changed, warnings = kuiser_mvsa_path(
                path,
                out,
                pitch=args.pitch,
                octave_style=args.octave_style,
                align=not args.no_align,
                check=args.check,
            )
        except MvsaValidationError as exc:
            for d in exc.diagnostics:
                print(format_diagnostic(d, path), file=sys.stderr)
            errors += 1
            continue
        except (MvsaKuiserError, MvsaNormalizeError) as exc:
            loc = f"{path}:{exc.line}: " if getattr(exc, "line", 0) else f"{path}: "
            print(f"{loc}ERROR: {exc}", file=sys.stderr)
            errors += 1
            continue
        for w in warnings:
            print(w.format(path), file=sys.stderr)
        if changed:
            would_change += 1
            if args.check:
                print(f"would change: {path}")
            else:
                target = out if out is not None else path
                print(f"kuiser: {target}")
        else:
            print(f"ok: {path}")

    if errors:
        return 1
    if args.check and would_change:
        return 1
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
