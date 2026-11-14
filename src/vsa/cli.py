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
from .markdown_pdf import PdfError
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
from .cli_messages import emit_cli_error, emit_cli_exception
from .derived_path import derived_output_path, derived_svg_output_path
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
        emit_cli_exception(exc, hint=getattr(exc, "hint_nl", None) or None)
        return 1
    except Exception as exc:
        emit_cli_exception(
            exc,
            hint="Controleer het commando en de bestandsnamen; zie vsa -h.",
        )
        return 1


def _add_translit_args(
    parser: argparse.ArgumentParser, *, with_as_parts: bool = False
) -> None:
    """``--translit`` + ``--translit-modus``; optioneel ``--translit-as-parts``."""
    parser.add_argument(
        "--translit",
        action="store_true",
        help=(
            "Tweede lyric-laag (number=2): ksl→Latijn / nl→Cyrillisch "
            "(filter met --translit-modus)."
        ),
    )
    parser.add_argument(
        "--translit-modus",
        choices=("nls", "ksl"),
        default=None,
        dest="translit_modus",
        help=(
            "Filter hulpregel: nls = alleen ksl→Latijn; ksl = alleen "
            "nl→Cyrillisch. Zonder deze vlag (met --translit): beide. "
            "Alleen --translit-modus impliceert --translit."
        ),
    )
    if with_as_parts:
        parser.add_argument(
            "--translit-as-parts",
            action="store_true",
            dest="translit_as_parts",
            help=(
                "Alleen bij .mvsa: Coria-extra parts (volume 0). "
                "Auto-translit: Soprano (nls)/(ksl); parallelle L/L1: "
                "labels via @taal. Impliceert --translit. Alleen playback."
            ),
        )


def _cli_translit_kwargs(args) -> dict:
    """Gemeenschappelijke kwargs voor mvsa-export met translit."""
    modus = getattr(args, "translit_modus", None)
    translit = bool(getattr(args, "translit", False)) or modus is not None
    kwargs: dict = {
        "translit": translit,
        "translit_modus": modus if modus is not None else "both",
    }
    if hasattr(args, "translit_as_parts"):
        kwargs["translit_as_parts"] = bool(args.translit_as_parts)
    return kwargs


def _build_mvsa_parser() -> argparse.ArgumentParser:
    """Standalone top-level ``mvsa`` parser (not nested under ``vsa``)."""
    parser = argparse.ArgumentParser(
        prog="mvsa",
        description=(
            "mvsa draft: valideren, normaliseren, MusicXML of MSCZ. "
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
            "  syllabify PATH [--dry-run] [--extension EXT] [--unsyllabify]\n"
            "      Soft ``-`` in L-recite/cadens (Pyphen + dictionary; sync-veilig).\n"
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
            "  mvsa syllabify examples\\mvsa\\syllabificatie-recite-mini.mvsa\n"
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
            "mvsa transpose -h | mvsa kuiser -h | mvsa syllabify -h"
        ),
    )
    mvsa_sub = parser.add_subparsers(
        dest="mvsa_command",
        required=True,
        metavar="{validate,mxl,mscz,pdf,svg,mp3,ogg,wav,score-ir,normalize,transpose,kuiser,syllabify,text,vsa,import,products}",
    )
    m_validate = mvsa_sub.add_parser(
        "validate",
        help="Valideer .mvsa (structuur + sync-telling; draft-spec).",
        description=(
            "Controleer .mvsa-bestanden op structuur, maatstrepen en "
            "sync-telling L tegen stemmen (draft-spec docs/specification-mvsa/). "
            "Ook L-lyrics tegen de canonieke syllable-dictionary "
            "(warning; zie docs/formats/syllabificatie.md)."
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
    m_validate.add_argument(
        "--config",
        default=None,
        help="Pad naar vsa.toml (o.a. [syllabificatie] dictionary).",
    )
    m_validate.add_argument(
        "--syllable-dictionary",
        metavar="PAD",
        default=None,
        help=(
            "Pad naar canonieke syllable_dictionary.nl.txt "
            "(overschrijft vsa.toml [syllabificatie] dictionary)."
        ),
    )
    m_musicxml = mvsa_sub.add_parser(
        "mxl",
        aliases=["musicxml"],
        help="Exporteer .mvsa naar Coria-playback MusicXML.",
        description=(
            "Schrijf een Coria-playback-.mxl uit .mvsa (straat-puur). "
            "Zelfde vorm als vsa mxl / mscz mxl: PATH [-o OUTPUT]. "
            "Voor .mscz: mscz mxl. Voor bestaande .mxl: mxl normalize. "
            "Alias: musicxml (verouderd)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mvsa mxl examples\\mvsa\\kleine-intocht-zondag-hemelum.mvsa\n"
            "  mvsa mxl lied.mvsa -o generated\\lied.mxl\n"
            "  mvsa mxl lied.mvsa --section schets-a-bladcijfer -o out.mxl"
        ),
    )
    m_musicxml.add_argument(
        "path",
        help=".mvsa-bestand of map met .mvsa-bestanden (recursief).",
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
        help=(
            "Deze @sectie-id (niet @blok; default: hele bestand)."
        ),
    )
    m_musicxml.add_argument(
        "--bibliotheek-id",
        metavar="ID",
        default=None,
        dest="bibliotheek_id",
        help=(
            "Bibliotheek-id in MusicXML identification/rights "
            "(default: pad-sniff onder content-source/bibliotheek)."
        ),
    )
    _add_translit_args(m_musicxml, with_as_parts=True)
    from .canonicity_gate import add_allow_noncanonical_arg as _add_c3_mmxl

    _add_c3_mmxl(m_musicxml)
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
        help=(
            "Alleen deze @sectie-id exporteren (niet @blok; "
            "default: hele bestand)."
        ),
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
    _add_translit_args(m_mscz)
    _add_partituur_style_args(m_mscz)
    from .canonicity_gate import add_allow_noncanonical_arg as _add_c3_mmscz

    _add_c3_mmscz(m_mscz)
    m_pdf = mvsa_sub.add_parser(
        "pdf",
        help="Exporteer .mvsa naar print-PDF voor zangers.",
        description=(
            "Partituur-PDF via MuseScore. Keten: .mvsa -> .mscz -> .pdf. "
            "Vereist MuseScore 4 (of 3). Bron .mscz: gebruik mscz pdf."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mvsa pdf examples\\mvsa\\alleluia-toon-1.mvsa\n"
            "  mvsa pdf lied.mvsa -o generated\\lied.pdf --keep-mscz generated\\lied.mscz\n"
            "  mvsa pdf lied.mvsa --layout partituur --bibliotheek-id zangstuk/var/uv\n"
            "  mscz pdf lied.mscz -o lied.pdf"
        ),
    )
    m_pdf.add_argument(
        "path",
        help=".mvsa-bestand of map met .mvsa-bestanden (recursief).",
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
        help=(
            "Alleen bij .mvsa: deze @sectie-id (niet @blok; "
            "default: hele bestand)."
        ),
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
    _add_translit_args(m_pdf)
    _add_partituur_style_args(m_pdf)
    m_svg = mvsa_sub.add_parser(
        "svg",
        help="Exporteer .mvsa naar partituur-SVG (koormap).",
        description=(
            "Bron .mvsa: kale muziek-SVG. Default --engine musescore "
            "(geen titel/colofon; layout muziek; viewBox-trim; MuseScore 4). "
            "--engine osmd: Score-IR → from-ir MusicXML → headless OSMD "
            "(Node + scripts/osmd-svg; geen MuseScore). "
            "Bron .mscz: gebruik mscz svg."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mvsa svg examples\\mvsa\\1a-vredeslitanie.mvsa\n"
            "  mvsa svg lied.mvsa -o generated\\lied.mvsa.svg\n"
            "  mvsa svg lied.mvsa --lyrics-font-size 14 --cue-font-size 11\n"
            "  mvsa svg lied.mvsa -o generated\\lied-osmd.svg --engine osmd\n"
            "  mscz svg generated\\lied.mscz -o generated\\lied.svg\n"
            "  mvsa svg lied.mvsa --section schets1 --keep-mscz generated\\lied.mscz"
        ),
    )
    m_svg.add_argument(
        "path",
        help=".mvsa-bestand of map met .mvsa-bestanden (recursief).",
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
        help=(
            "Alleen bij .mvsa: deze @sectie-id (niet @blok; "
            "default: hele bestand)."
        ),
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
    _add_translit_args(m_svg)
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
            "Default: witte rechthoek achter de notatie. "
            "Alleen bij --engine musescore."
        ),
    )
    m_svg.add_argument(
        "--engine",
        metavar="NAME",
        choices=["musescore", "osmd"],
        default="musescore",
        help=(
            "SVG-engine: musescore (default; print/fallback) of osmd "
            "(Score-IR → headless OSMD; vereist Node + scripts/osmd-svg)."
        ),
    )
    _add_partituur_style_args(m_svg)
    from .canonicity_gate import add_allow_noncanonical_arg as _add_c3_msvg

    _add_c3_msvg(m_svg)
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
            "Doel-spelling op stemregels. Default bij .mvsa-bron: preserve. "
            "doremi = laddergraden t.o.v. @do/@oct; "
            "a-g (alias abc) = toonnamen (octaaf via --octave-style); "
            "vsa = eerste toon doremi + EHM; "
            "ag-vsa = per systeem eerste a–g + EHM + eindanker."
        ),
    )
    m_normalize.add_argument(
        "--octave-style",
        choices=["@oct", "marker", "none"],
        default="@oct",
        help=(
            "Octaafschrijfwijze voor a–g/ag-vsa: "
            "@oct = relatief (Bb, c+; default); "
            "none = absoluut (Bb4; niet met --pitch doremi); "
            "marker = nog niet geïmplementeerd."
        ),
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
        help=(
            "Spelling na transpositie (default: ag-vsa). "
            "doremi / a-g / vsa / ag-vsa; a–g-octaaf via --octave-style."
        ),
    )
    m_transpose.add_argument(
        "--octave-style",
        choices=["@oct", "marker", "none"],
        default="@oct",
        help=(
            "Octaafschrijfwijze voor a–g/ag-vsa: "
            "@oct = relatief (default); none = absoluut (niet met doremi); "
            "marker = nog niet klaar."
        ),
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
        help="Alleen deze @sectie-id exporteren (niet @blok).",
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
    from .canonicity_gate import add_allow_noncanonical_arg as _add_c4_msir

    _add_c4_msir(m_score_ir)
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
            "Doel-spelling (default: preserve). Zelfde als normalize: "
            "doremi / a-g / vsa / ag-vsa."
        ),
    )
    m_kuiser.add_argument(
        "--octave-style",
        choices=["@oct", "marker", "none"],
        default="@oct",
        help=(
            "Octaafschrijfwijze voor a–g/ag-vsa: "
            "@oct = relatief (default); none = absoluut (niet met doremi)."
        ),
    )
    m_kuiser.add_argument(
        "--no-align",
        action="store_true",
        help="Sla canonieke kolomuitlijning over.",
    )
    m_syllabify = mvsa_sub.add_parser(
        "syllabify",
        help=(
            "Zet of verwijder lettergreepstreepjes in .mvsa L-tekst "
            "(recite + cadens; sync-veilig)."
        ),
        description=(
            "Schrijfhulp: soft ``-`` in L-recite ``(…)`` en uitbreiding van "
            "ongesplitste cadens-woorden naar hyphen-ketens, met ``-``-holds "
            "op stemmen zodat sync klopt. Zelfde Pyphen/dictionary als "
            "``vsa syllabify``. Norm: docs/formats/syllabificatie.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mvsa syllabify examples\\mvsa\\syllabificatie-recite-mini.mvsa\n"
            "  mvsa syllabify lied.mvsa --dry-run\n"
            "  mvsa syllabify lied.mvsa --extension .syl.mvsa\n"
            "  mvsa syllabify lied.mvsa --unsyllabify --dry-run"
        ),
    )
    m_syllabify.add_argument(
        "path",
        help=".mvsa-bestand of map (recursief alle .mvsa).",
    )
    m_syllabify.add_argument(
        "--dry-run",
        action="store_true",
        help="Toon resultaat zonder bestanden te schrijven (default: schrijf in-place).",
    )
    m_syllabify.add_argument(
        "--in-place",
        action="store_true",
        help=(
            "Schrijf terug naar elk bronbestand (default-gedrag; "
            "flag blijft voor expliciete scripts)."
        ),
    )
    m_syllabify.add_argument(
        "--extension",
        metavar="EXT",
        default=None,
        help=(
            "Schrijf naast het bronbestand met deze extensie "
            "(bijv. .syl.mvsa) i.p.v. in-place."
        ),
    )
    m_syllabify.add_argument(
        "--unsyllabify",
        action="store_true",
        help=(
            "Verwijder soft ``-`` binnen recite ``(…)``. "
            "Cadens-ketens worden niet samengevoegd."
        ),
    )
    m_syllabify.add_argument(
        "--no-align",
        action="store_true",
        help="Sla kolomuitlijning na herschrijven over.",
    )
    m_syllabify.add_argument(
        "--config",
        default=None,
        help="Pad naar vsa.toml (o.a. [syllabificatie] dictionary).",
    )
    m_syllabify.add_argument(
        "--syllable-dictionary",
        metavar="PAD",
        default=None,
        help=(
            "Pad naar canonieke syllable_dictionary.nl.txt "
            "(overschrijft vsa.toml [syllabificatie] dictionary)."
        ),
    )
    m_text = mvsa_sub.add_parser(
        "text",
        help="Platte gezongen tekst → sibling .lyrics.txt (product lyrics).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mvsa text lied.mvsa\n"
            "  mvsa text lied.mvsa -o generated\\lied.lyrics.txt"
        ),
    )
    m_text.add_argument(
        "path",
        help=".mvsa-bestand of map met .mvsa-bestanden (recursief).",
    )
    m_text.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoer (default: sibling <bronnaam>.lyrics.txt). "
            "Alleen bij precies één bronbestand."
        ),
    )
    from .canonicity_gate import add_allow_noncanonical_arg as _add_c3_mvsa_text

    _add_c3_mvsa_text(m_text)
    m_vsa = mvsa_sub.add_parser(
        "vsa",
        help="Extraheer eenstemmige .mvsa.vsa uit .mvsa (E1–E6).",
        description=(
            "Zet een .mvsa om naar een eenstemmige .vsa (product). "
            "Zonder --voice of met één --voice x → sibling "
            "<bronnaam>.vsa (default-stem S). "
            "--voice all → per stem <bronnaam>.{stem}.vsa (lowercase). "
            "Elke MVSA-maat wordt één VSA-strofe (*). "
            "Contract: docs/formats/mvsa-vsa-contract.md (E1–E6)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  mvsa vsa lied.mvsa\n"
            "  mvsa vsa lied.mvsa --voice t\n"
            "  mvsa vsa lied.mvsa --voice all\n"
            "  mvsa vsa lied.mvsa -o generated\\lied.mvsa.vsa"
        ),
    )
    m_vsa.add_argument(
        "path",
        help=".mvsa-bestand of map met .mvsa-bestanden (recursief).",
    )
    m_vsa.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoerbestand (default: sibling <bronnaam>.vsa). "
            "Alleen bij precies één bron én één uitvoerbestand "
            "(niet bij --voice all)."
        ),
    )
    m_vsa.add_argument(
        "--voice",
        metavar="ID",
        default="S",
        help=(
            "Stem-id in de MVSA (default: S). Eén stem → altijd "
            "sibling <bronnaam>.vsa. Met 'all': per stem "
            "<bronnaam>.{stem}.vsa (stem lowercase, ook .s.vsa)."
        ),
    )

    from .cli_import import add_mvsa_import_parser
    from .street_products import add_products_parser

    add_mvsa_import_parser(mvsa_sub)
    add_products_parser(mvsa_sub, street="mvsa", with_skip_svg=True)
    return parser


def _build_parser():
    parser = argparse.ArgumentParser(prog="vsa")
    parser.add_argument("--config", help="Pad naar vsa.toml", default=None)
    parser.add_argument("--version", action="store_true", help="Toon versie")

    subparsers = parser.add_subparsers(dest="command")

    validate = subparsers.add_parser("validate")
    validate.add_argument("path")
    validate.add_argument("--config", default=None)
    validate.add_argument(
        "--syllable-dictionary",
        metavar="PAD",
        default=None,
        help=(
            "Pad naar canonieke syllable_dictionary.nl.txt "
            "(overschrijft vsa.toml [syllabificatie] dictionary)."
        ),
    )
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
    from .canonicity_gate import add_allow_noncanonical_arg as _add_c3_arg

    _add_c3_arg(svg)
    _add_translit_args(svg)

    from .street_products import add_products_parser as _add_vsa_products_parser

    _add_vsa_products_parser(subparsers, street="vsa", with_skip_svg=True)

    vsa_score_ir = subparsers.add_parser(
        "score-ir",
        help="Score-IR (+ optioneel from-ir) uit .vsa.",
    )
    vsa_score_ir.add_argument("path", help=".vsa-bestand of map (recursief).")
    vsa_score_ir.add_argument("-o", "--output", default=None)
    vsa_score_ir.add_argument(
        "--musicxml",
        nargs="?",
        const="",
        default=None,
        metavar="PATH",
        help="Schrijf ook from-ir MusicXML (zonder PATH: sibling).",
    )
    vsa_score_ir.add_argument("--musescore", default=None)
    from .canonicity_gate import add_allow_noncanonical_arg as _add_c3_sir

    _add_c3_sir(vsa_score_ir)

    vsa_mscz = subparsers.add_parser(
        "mscz",
        help="Partituur-.mscz-sibling uit .vsa (meta-key mscz).",
    )
    vsa_mscz.add_argument("path", help=".vsa-bestand of map (recursief).")
    vsa_mscz.add_argument("-o", "--output", default=None)
    vsa_mscz.add_argument("--musescore", default=None)
    from .canonicity_gate import add_allow_noncanonical_arg as _add_c3_vmscz

    _add_c3_vmscz(vsa_mscz)

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
    syllabify.add_argument(
        "--dry-run",
        action="store_true",
        help="Toon resultaat zonder bestanden te schrijven (default: schrijf in-place).",
    )
    syllabify.add_argument(
        "--in-place",
        action="store_true",
        help=(
            "Schrijf terug naar elk bronbestand (default-gedrag; "
            "flag blijft voor expliciete scripts)."
        ),
    )
    syllabify.add_argument(
        "--extension",
        metavar="EXT",
        default=None,
        help=(
            "Schrijf naast het bronbestand met deze extensie "
            "(bijv. .syl.vsa of syl.vsa: xyz.vsa wordt xyz.syl.vsa) "
            "i.p.v. in-place."
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
    syllabify.add_argument(
        "--config",
        default=None,
        help="Pad naar vsa.toml (o.a. [syllabificatie] dictionary).",
    )
    syllabify.add_argument(
        "--syllable-dictionary",
        metavar="PAD",
        default=None,
        help=(
            "Pad naar canonieke syllable_dictionary.nl.txt "
            "(overschrijft vsa.toml [syllabificatie] dictionary)."
        ),
    )

    text_cmd = subparsers.add_parser(
        "text",
        help=(
            "Lyrics-product uit .vsa → sibling .lyrics.txt (meta lyrics)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Alleen .vsa (straat-puur). Voor .mvsa: mvsa text; voor .mscz: "
            "mscz text.\n"
            "Default: sibling <bronnaam>.lyrics.txt + products-meta.\n"
            "\n"
            "voorbeelden:\n"
            "  vsa text lied.vsa\n"
            "  vsa text lied.vsa -o generated\\lied.lyrics.txt"
        ),
    )
    text_cmd.add_argument(
        "path",
        help=".vsa-bestand of map met .vsa-bestanden (recursief).",
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
    from .canonicity_gate import add_allow_noncanonical_arg as _add_c3_text

    _add_c3_text(text_cmd)

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

    musicxml = subparsers.add_parser(
        "mxl",
        aliases=["musicxml"],
        help="Exporteer .vsa naar Coria-playback MusicXML (.mxl).",
        description=(
            "Schrijf een Coria-playback-.mxl uit .vsa (straat-puur). "
            "Zelfde vorm als mvsa mxl / mscz mxl: PATH [-o OUTPUT]. "
            "Default: sibling <bronnaam>.vsa.mxl. Alias: musicxml."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  vsa mxl examples\\minimal\\050_svg_demo.vsa\n"
            "  vsa mxl lied.vsa -o generated\\lied.mxl\n"
            "  vsa mxl lied.vsa --syllabify\n"
            "  vsa mxl examples\\minimal"
        ),
    )
    musicxml.add_argument(
        "path",
        help=".vsa-bestand of map met .vsa-bestanden (recursief).",
    )
    musicxml.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT",
        default=None,
        help=(
            "Uitvoer-.mxl (default: sibling per bron). "
            "Alleen bij precies één bronbestand."
        ),
    )
    musicxml.add_argument("--config", default=None)
    musicxml.add_argument(
        "--format",
        choices=["musicxml", "mxl"],
        default=None,
        help=(
            "Uitvoerformaat wanneer -o geen expliciete extensie heeft "
            "(default: .mxl). Bij sibling-default: kies .mxl of .musicxml."
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
    musicxml.add_argument(
        "--syllabify",
        action="store_true",
        help=(
            "Voeg tijdelijke lettergreepstreepjes toe vóór export "
            "(canonieke .vsa blijft ongewijzigd). C3-uitzondering voor "
            "deling; bronvalidate blijft gelden tenzij "
            "--allow-noncanonical."
        ),
    )
    from .canonicity_gate import add_allow_noncanonical_arg as _add_c3_mxl

    _add_c3_mxl(musicxml)

    _add_vsa_audio_format_parsers(subparsers)

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

    from .cli_vsa_mvsa import add_vsa_mvsa_parser

    add_vsa_mvsa_parser(subparsers)

    pdf = subparsers.add_parser(
        "pdf",
        help="Print-PDF uit .vsa (partituur via MuseScore).",
        description=(
            "Partituur-PDF via MuseScore. Alleen .vsa. "
            "Pagina-Markdown (index.md.pdf): markdown pdf. "
            "Bron .mvsa: mvsa pdf; bron .mscz: mscz pdf."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  vsa pdf examples\\minimal\\valid-demo.vsa\n"
            "  vsa pdf lied.vsa -o generated\\lied.pdf\n"
            "  markdown pdf index.md\n"
            "  mvsa pdf lied.mvsa\n"
            "  mscz pdf lied.mscz"
        ),
    )
    pdf.add_argument(
        "path",
        help=".vsa-bestand of map met .vsa-bestanden (recursief).",
    )
    pdf.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoer-.pdf (default: sibling <bronnaam>.pdf). "
            "Alleen bij precies één bronbestand."
        ),
    )
    pdf.add_argument(
        "--musescore",
        default=None,
        help="Pad naar MuseScore-executable (default: auto).",
    )

    return parser


def _run(args):
    if args.version:
        print(f"vsa {_version()}")
        return 0

    if args.command is None:
        emit_cli_error(
            "Geen subcommando opgegeven.",
            hint="Gebruik bijvoorbeeld: vsa validate <pad>  of  vsa -h",
        )
        return 1

    config = load_config(_resolve_config_arg(getattr(args, "config", None)))
    _apply_syllable_dictionary_setting(args, config)

    if args.command == "validate":
        return _cmd_validate(args, config)

    if args.command == "parse":
        return _cmd_parse(args)

    if args.command == "blocks":
        return _cmd_blocks(args)

    if args.command == "svg":
        return _cmd_svg(args, config)

    if args.command == "products":
        from .street_products import run_street_products

        musescore = Path(args.musescore) if getattr(args, "musescore", None) else None
        return run_street_products(
            "vsa",
            args.path,
            force=bool(args.force),
            dry_run=bool(args.dry_run),
            skip_svg=bool(getattr(args, "skip_svg", False)),
            quiet=bool(getattr(args, "quiet", False)),
            musescore=musescore,
            allow_noncanonical=bool(
                getattr(args, "allow_noncanonical", False)
            ),
        )

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

    if args.command == "score-ir":
        return _cmd_vsa_score_ir(args)

    if args.command == "mscz":
        return _cmd_vsa_mscz_product(args)

    if args.command == "zoektekst":
        return _cmd_zoektekst(args)

    if args.command in ("mxl", "musicxml"):
        return _cmd_musicxml(args, config)

    if args.command in ("mp3", "ogg", "wav", "audio"):
        return _cmd_audio(args, config)

    if args.command == "template":
        return _cmd_template(args)
    if args.command == "mvsa":
        from .cli_vsa_mvsa import run_vsa_mvsa

        return run_vsa_mvsa(args)


    if args.command == "pdf":
        return _cmd_pdf(args, config)

    emit_cli_error(
        f"Onbekend subcommando: {args.command}",
        hint="Bekijk de lijst met: vsa -h",
    )
    return 1


def _version():
    for package_name in ["vsa-tool", "vsa"]:
        try:
            return version(package_name)
        except PackageNotFoundError:
            continue

    return "0.2.0"


def _resolve_config_arg(explicit: str | None) -> str | None:
    """Expliciete ``--config``, anders ``vsa.toml`` in de werkmap indien aanwezig."""
    if explicit:
        return explicit
    candidate = Path.cwd() / "vsa.toml"
    return str(candidate) if candidate.is_file() else None


def _apply_syllable_dictionary_setting(args, config) -> None:
    from .syllable_dictionary import apply_syllable_dictionary_from_config

    apply_syllable_dictionary_from_config(
        cli_path=getattr(args, "syllable_dictionary", None),
        config_value=config.syllabificatie.dictionary,
        config_dir=config.config_dir,
    )


def _cmd_validate(args, config):
    path = Path(args.path)
    if path.is_file() and _reject_wrong_street_source(
        "vsa", "validate", path, wrong_suffix=".mvsa"
    ):
        return 1
    if path.is_file() and _reject_non_street_file(
        "vsa",
        "validate",
        path,
        allowed=(".vsa", ".md", ".markdown"),
    ):
        return 1
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
            emit_cli_exception(
                exc,
                path=path,
                hint="Controleer @include-vsa in dit .vsa-bestand.",
            )
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
    from .canonicity_gate import cli_gate_source

    files = _cli_collect_sources(args.input, (".vsa",))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args):
        return 1

    tkw = _cli_translit_kwargs(args)
    renderer = SVGRenderer(
        svg_config=config.rendering.svg,
        translit=bool(tkw.get("translit")),
        translit_modus=str(tkw.get("translit_modus") or "both"),
    )
    renderer.max_line_width = (
        args.max_line_width
        if args.max_line_width is not None
        else config.rendering.max_line_width
    )

    exit_code = 0
    for input_path in files:
        if cli_gate_source(input_path, args, config=config):
            exit_code = 1
            continue
        out = (
            Path(args.output)
            if args.output
            else derived_svg_output_path(
                input_path,
                translit=bool(tkw.get("translit")),
                translit_modus=str(tkw.get("translit_modus") or "both"),
            )
        )
        try:
            text = input_path.read_text(encoding="utf-8")
            body, _ = prepare_vsa_body(text, input_path)
            document = Parser(preserve_vsa_source_newlines(body)).parse()
            from .atomic_io import write_text

            svg = renderer.render_document(document)
            out.parent.mkdir(parents=True, exist_ok=True)
            write_text(out, svg, encoding="utf-8")
        except IncludeVsaError as exc:
            emit_cli_exception(
                exc,
                path=input_path,
                hint="Controleer @include-vsa in dit .vsa-bestand.",
            )
            exit_code = 1
            continue
        except Exception as exc:
            emit_cli_exception(
                exc,
                path=input_path,
                hint="Controleer de VSA-notatie met: vsa validate <pad>",
            )
            exit_code = 1
            continue
        print(f"SVG geschreven naar: {out}")
        from .street_products import merge_street_product_meta

        meta = merge_street_product_meta(input_path, {"svg": out})
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
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
    """``vsa pdf``: alleen ``.vsa`` → partituur-PDF (los gereedschap, niet products)."""
    from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError
    from .street_product_export import (
        StreetProductExportError,
        export_bron_to_partituur_pdf,
    )
    from .street_products import MSCZ_PDF_KEY, merge_street_product_meta

    del config  # partituur-PDF gebruikt geen vsa.toml-renderconfig
    if _reject_wrong_street_source(
        "vsa", "pdf", args.path, wrong_suffix=".md", hint_street="markdown"
    ):
        return 1
    if _reject_wrong_street_source(
        "vsa", "pdf", args.path, wrong_suffix=".markdown", hint_street="markdown"
    ):
        return 1
    if _reject_wrong_street_source("vsa", "pdf", args.path, wrong_suffix=".mvsa"):
        return 1
    if _reject_wrong_street_source("vsa", "pdf", args.path, wrong_suffix=".mscz"):
        return 1
    if _reject_non_street_file("vsa", "pdf", args.path, allowed=(".vsa",)):
        return 1
    files = _cli_collect_sources(args.path, (".vsa",))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args):
        return 1
    musescore = Path(args.musescore) if getattr(args, "musescore", None) else None
    exit_code = 0
    for path in files:
        out = (
            Path(args.output)
            if getattr(args, "output", None)
            else derived_output_path(path, ".pdf")
        )
        try:
            written = export_bron_to_partituur_pdf(
                path, out, musescore=musescore
            )
        except (
            StreetProductExportError,
            MuseScoreNotFoundError,
            MuseScoreConvertError,
        ) as exc:
            emit_cli_exception(
                exc,
                path=path,
                hint=(
                    "Installeer MuseScore 4 of geef --musescore PATH; "
                    "controleer daarna of de bron met vsa validate klopt."
                ),
            )
            exit_code = 1
            continue
        except Exception as exc:
            emit_cli_exception(
                exc,
                path=path,
                hint="Controleer de bron met vsa validate en of MuseScore werkt.",
            )
            exit_code = 1
            continue
        print(f"Geschreven: {written}")
        meta = merge_street_product_meta(path, {MSCZ_PDF_KEY: written})
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_text(args) -> int:
    """``vsa text``: alleen ``.vsa`` → sibling ``*.lyrics.txt`` (+ meta)."""
    from .musescore_cli import MuseScoreConvertError, MuseScoreNotFoundError
    from .street_product_export import write_lyrics_product
    from .street_products import LYRICS_KEY, merge_street_product_meta

    if _reject_wrong_street_source(
        "vsa", "text", args.path, wrong_suffix=".mscz"
    ):
        return 1
    if _reject_wrong_street_source(
        "vsa", "text", args.path, wrong_suffix=".mvsa"
    ):
        return 1
    if _reject_non_street_file("vsa", "text", args.path, allowed=(".vsa",)):
        return 1

    files = _cli_collect_sources(args.path, (".vsa",))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args):
        return 1
    from .canonicity_gate import cli_gate_source

    musescore = Path(args.musescore) if getattr(args, "musescore", None) else None
    exit_code = 0
    for path in files:
        if cli_gate_source(path, args):
            exit_code = 1
            continue
        out = (
            Path(args.output)
            if getattr(args, "output", None)
            else derived_output_path(path, ".lyrics.txt")
        )
        try:
            written = write_lyrics_product(path, out, musescore=musescore)
        except ValueError as exc:
            emit_cli_exception(
                exc,
                path=path,
                hint="Controleer of dit een geldig .vsa-bestand is.",
            )
            exit_code = 1
            continue
        except (MuseScoreNotFoundError, MuseScoreConvertError) as exc:
            emit_cli_exception(
                exc,
                path=path,
                hint="Installeer MuseScore 4 of geef --musescore PATH.",
            )
            exit_code = 1
            continue
        except Exception as exc:  # noqa: BLE001
            emit_cli_exception(
                exc,
                path=path,
                hint="Controleer of het bestand leesbaar is (UTF-8-tekst).",
            )
            exit_code = 1
            continue
        print(f"Geschreven: {written}")
        meta = merge_street_product_meta(path, {LYRICS_KEY: written})
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_syllabify(args) -> int:
    source_path = Path(args.path)
    if args.extension and args.in_place:
        emit_cli_error(
            "Gebruik --in-place of --extension, niet beide.",
            hint="Zonder --extension schrijft syllabify standaard in-place.",
        )
        return 1

    extension: str | None = None
    if args.extension is not None:
        try:
            extension = normalize_output_extension(args.extension)
        except ValueError as exc:
            emit_cli_exception(
                exc,
                hint="Geef een extensie zoals .syll.vsa; zie vsa syllabify -h.",
            )
            return 1

    # Uniform met kuiser/zoektekst: default schrijven; --dry-run = preview.
    dry_run = bool(args.dry_run)

    try:
        files = iter_vsa_files(source_path)
    except FileNotFoundError:
        emit_cli_error(
            "Pad niet gevonden.",
            path=source_path,
            hint=(
                "Controleer of het pad bestaat, of geef een catalogus-id "
                "(docs/reference/cli/input-pad.md)."
            ),
        )
        return 1
    except ValueError as exc:
        emit_cli_exception(
            exc,
            path=source_path,
            hint=(
                "Geef een .vsa-bestand, map, of catalogus-id "
                "(docs/reference/cli/input-pad.md)."
            ),
        )
        return 1

    if not files:
        emit_cli_error(
            "Geen .vsa-bestanden gevonden.",
            path=source_path,
            hint="Zet .vsa-bestanden in deze map of geef een ander pad.",
        )
        return 1

    multi = len(files) > 1 or source_path.is_dir()
    any_error = False
    verb = "verwijderd" if args.unsyllabify else "toegevoegd"

    for file_path in files:
        try:
            target = output_path_for(file_path, extension)
        except ValueError as exc:
            emit_cli_exception(exc, path=file_path)
            any_error = True
            continue

        if extension is not None and file_path.name.lower().endswith(extension.lower()):
            emit_cli_error(
                f"Overgeslagen: bestandsnaam eindigt al op {extension}.",
                path=file_path,
                hint="Kies een andere --extension of hernoem het bronbestand.",
            )
            continue

        original = file_path.read_text(encoding="utf-8")
        try:
            result = transform_vsa_source(original, unsyllabify=args.unsyllabify)
        except Exception as exc:
            emit_cli_exception(
                exc,
                path=file_path,
                hint="Controleer de VSA-notatie met: vsa validate <pad>",
            )
            any_error = True
            continue

        if not args.unsyllabify:
            from .syllabify import SyllabifyResult

            dict_rc, gated_text = _syllabify_dictionary_gate(
                file_path, result.text
            )
            if gated_text != result.text:
                result = SyllabifyResult(
                    text=gated_text,
                    changed=True,
                    replacements=result.replacements,
                )
            if dict_rc != 0:
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


def _syllabify_dictionary_gate(
    file_path: Path, source_text: str
) -> tuple[int, str]:
    """Dictionary-check; op TTY corrigeren (bron + lijst). Retourneert (rc, tekst)."""
    from .parser import Parser
    from .syllable_dict_check import (
        CODE_MISMATCH,
        CODE_UNKNOWN,
        apply_replacements_to_source,
        find_dictionary_syllable_issues,
        is_interactive_stdin,
        prompt_dictionary_fixes,
    )
    from .vsa_comments import strip_vsa_html_comments_with_offset_map
    from .yaml_frontmatter import parse_vsa_frontmatter

    _fm, body = parse_vsa_frontmatter(source_text)
    body, _ = strip_vsa_html_comments_with_offset_map(body)
    try:
        document = Parser(body).parse()
    except Exception as exc:
        emit_cli_exception(
            exc,
            path=file_path,
            hint="Controleer de VSA-notatie met: vsa validate <pad>",
        )
        return 1, source_text

    findings = find_dictionary_syllable_issues(document, source_text=body)
    if is_interactive_stdin():
        actionable = [
            f for f in findings if f.code in {CODE_MISMATCH, CODE_UNKNOWN}
        ]
        if actionable:
            from .input_paths import source_id_for_prompt

            session = prompt_dictionary_fixes(
                actionable, source_id=source_id_for_prompt(file_path)
            )
            if session.replacements:
                source_text = apply_replacements_to_source(
                    source_text, session.replacements
                )
                _fm2, body = parse_vsa_frontmatter(source_text)
                body, _ = strip_vsa_html_comments_with_offset_map(body)
                try:
                    document = Parser(body).parse()
                except Exception:
                    pass
                findings = find_dictionary_syllable_issues(
                    document, source_text=body
                )
            else:
                findings = find_dictionary_syllable_issues(
                    document, source_text=body
                )

    hard = [f for f in findings if f.code in {CODE_MISMATCH, CODE_UNKNOWN}]
    if not hard:
        return 0, source_text
    for finding in hard:
        emit_cli_error(
            finding.message_nl,
            path=file_path,
            hint=finding.hint_nl,
        )
    return 1, source_text


def _cmd_resolve_catalogus(args) -> int:
    source_path = Path(args.path)
    if not source_path.is_file():
        emit_cli_error(
            "Bestand niet gevonden.",
            path=source_path,
            hint="Geef een bestaand Markdown-bestand (.md).",
        )
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
        emit_cli_exception(
            exc,
            path=source_path,
            hint="Controleer zoek= en catalogus-paden in dit Markdown-bestand.",
        )
        return 1

    for warning in result.warnings:
        emit_cli_error(
            f"WARNING: {warning.code}: {warning.message_nl}",
            path=source_path,
            line=getattr(warning, "line", None),
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
    """``vsa mxl`` / alias ``musicxml``: straat-puur ``path [-o]`` → playback-MXL."""
    from .street_products import merge_street_product_meta

    cmd = "mxl"
    if _reject_wrong_street_source("vsa", cmd, args.path, wrong_suffix=".mscz"):
        return 1
    if _reject_wrong_street_source("vsa", cmd, args.path, wrong_suffix=".mvsa"):
        return 1
    if _reject_non_street_file("vsa", cmd, args.path, allowed=(".vsa",)):
        return 1
    files = _cli_collect_sources(args.path, (".vsa",))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args):
        return 1

    cli_overrides: dict[str, str] = {}
    if args.do:
        cli_overrides["do"] = args.do
    if args.mode:
        cli_overrides["mode"] = args.mode
    if args.tempo:
        cli_overrides["tempo"] = args.tempo
    if args.musicxml_profile:
        cli_overrides["musicxml-profile"] = args.musicxml_profile

    from .canonicity_gate import cli_gate_source

    default_suffix = _musicxml_batch_suffix(args)
    syllabify = bool(getattr(args, "syllabify", False))
    exit_code = 0
    written = 0
    for path in files:
        if cli_gate_source(path, args, config=config):
            exit_code = 1
            continue
        if args.output:
            out = Path(args.output)
            if out.suffix.lower() not in _KNOWN_SUFFIXES:
                out = out.with_suffix(default_suffix)
        else:
            out = derived_output_path(path, default_suffix)
        rc = _export_vsa_to_musicxml(
            path, out, cli_overrides, syllabify=syllabify
        )
        if rc != 0:
            exit_code = 1
            continue
        # C4: Coria/playback-checklist (niet bij engraving-profiel).
        profile = (args.musicxml_profile or "playback").lower()
        if profile != "engraving":
            from .canonicity_gate import (
                NonCanonicalTargetError,
                emit_noncanonical_error,
                require_canonical_mxl_target,
            )

            try:
                require_canonical_mxl_target(
                    out,
                    bron=path,
                    allow_noncanonical=bool(
                        getattr(args, "allow_noncanonical", False)
                    ),
                )
            except NonCanonicalTargetError as exc:
                emit_noncanonical_error(exc)
                exit_code = 1
                continue
        written += 1
        print(f"Geschreven: {out}")
        meta = merge_street_product_meta(path, {"mxl": out})
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    if len(files) > 1 and written:
        label = "MXL" if default_suffix == _MXL_SUFFIX else "MusicXML"
        print(f"{written} {label}-bestand(en) geschreven")
    return exit_code


def _cmd_audio(args, config) -> int:
    """``vsa mp3|ogg|wav`` / alias ``audio`` (= mp3): ``path [-o]``."""
    from .audio_export import AUDIO_FORMATS, AudioExportError, export_to_audio
    from .mvsa_musicxml import MvsaExportError
    from .mvsa_validate import MvsaValidationError, format_diagnostic
    from .street_products import MP3_KEY, merge_street_product_meta

    cmd = getattr(args, "command", None)
    format_name = cmd if cmd in AUDIO_FORMATS else "mp3"
    if _reject_wrong_street_source(
        "vsa", format_name, args.path, wrong_suffix=".mscz"
    ):
        return 1
    if _reject_wrong_street_source(
        "vsa", format_name, args.path, wrong_suffix=".mvsa"
    ):
        return 1
    if _reject_non_street_file("vsa", format_name, args.path, allowed=(".vsa",)):
        return 1
    files = _cli_collect_sources(args.path, (".vsa",))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args, "keep_mxl"):
        return 1
    from .canonicity_gate import cli_gate_source

    musescore = Path(args.musescore) if args.musescore else None
    exit_code = 0
    for path in files:
        if cli_gate_source(path, args, config=config):
            exit_code = 1
            continue
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
                keep_mxl=keep_mxl,
            )
        except MvsaValidationError as exc:
            for d in exc.diagnostics:
                print(format_diagnostic(d, path), file=sys.stderr)
            exit_code = 1
            continue
        except MvsaExportError as exc:
            emit_cli_exception(
                exc,
                path=path,
                hint="Controleer de bron; bij .vsa: vsa validate <pad>.",
            )
            exit_code = 1
            continue
        except AudioExportError as exc:
            emit_cli_exception(
                exc,
                path=path,
                hint=(
                    "Installeer MuseScore 4 of geef --musescore PATH; "
                    "controleer daarna of de bron valide is."
                ),
            )
            exit_code = 1
            continue
        print(f"Geschreven: {written}")
        if keep_mxl is not None:
            print(f"MXL: {keep_mxl}")
        if format_name == "mp3":
            meta = merge_street_product_meta(path, {MP3_KEY: written})
            if meta is not None:
                print(f"Meta: {meta.name}", flush=True)
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
    *,
    syllabify: bool = False,
) -> int:
    from .vsa_musicxml_export import (
        IncludeVsaError as ExportIncludeError,
        MusicXMLExportError as ExportMusicXMLError,
        export_vsa_to_musicxml,
    )

    try:
        export_vsa_to_musicxml(
            input_path,
            output_path,
            cli_overrides=cli_overrides,
            syllabify=syllabify,
        )
    except ExportIncludeError as exc:
        emit_cli_exception(
            exc,
            path=input_path,
            hint="Controleer @include-vsa in dit .vsa-bestand.",
        )
        return 1
    except ExportMusicXMLError as exc:
        emit_cli_exception(
            exc,
            path=input_path,
            prefix="MusicXML-export mislukt: ",
            hint="Controleer de notatie met: vsa validate <pad>",
        )
        return 1
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
                emit_cli_exception(
                    exc,
                    path=input_path,
                    prefix=f"(blok {i + 1}) ",
                    hint="Controleer het mvsa-blok in dit Markdown-bestand.",
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
            emit_cli_exception(
                exc,
                path=input_path,
                prefix=f"(blok {i + 1}) ",
                hint="Controleer @include-vsa in dit blok.",
            )
            return 1, written
        document = block.parse_body(expanded_body)

        explicit_keys = set(block.metadata.keys()) | set(cli_overrides.keys())

        try:
            renderer = MusicXMLRenderer(metadata=metadata, explicit_keys=explicit_keys)
            xml_str = renderer.render(document)
        except MusicXMLExportError as exc:
            emit_cli_exception(
                exc,
                path=input_path,
                prefix=f"(blok {i + 1}) MusicXML-export mislukt: ",
                hint="Controleer de VSA in dit blok met vsa validate.",
            )
            return 1, written

        write_musicxml_output(out_file, xml_str)
        written += 1

    return 0, written


def _cmd_template(args) -> int:
    if getattr(args, "template_command", None) == "validate":
        return _cmd_template_validate(args)
    emit_cli_error(
        "Ontbrekend of onbekend template-subcommando.",
        hint="Gebruik: vsa template validate <pad>",
    )
    return 1


def _cli_collect_sources(
    path: Path | str,
    suffixes: tuple[str, ...] | list[str],
) -> list[Path] | None:
    """Bestand of map → bronlijst; bij fout: stderr + ``None``."""
    try:
        return collect_cli_sources(path, suffixes=suffixes)
    except InputPathError as exc:
        want = ", ".join(sorted({s if str(s).startswith(".") else f".{s}" for s in suffixes}))
        emit_cli_exception(
            exc,
            path=path,
            hint=(
                f"Geef één bestand met extensie {want}, of een map die zulke "
                "bestanden bevat."
            ),
        )
        return None


def _reject_mscz_use_mscz_street(cmd: str, path: Path | str) -> bool:
    """True = ``.mscz``-bestand geweigerd; stderr wijst naar ``mscz {cmd}``."""
    return _reject_wrong_street_source("mvsa", cmd, path, wrong_suffix=".mscz")


def _reject_wrong_street_source(
    cli: str,
    cmd: str,
    path: Path | str,
    *,
    wrong_suffix: str,
    hint_street: str | None = None,
    hint_cmd: str | None = None,
) -> bool:
    """True = bronbestand met *wrong_suffix* geweigerd; stderr met hint."""
    p = Path(path)
    if not (p.is_file() and p.suffix.lower() == wrong_suffix.lower()):
        return False
    street = hint_street or wrong_suffix.lstrip(".")
    sub = hint_cmd or cmd
    emit_cli_error(
        f"{cli} {cmd} weigert {wrong_suffix}-bestanden.",
        path=p,
        hint=f"Gebruik: {street} {sub} {p}",
    )
    return True


def _reject_non_street_file(
    cli: str,
    cmd: str,
    path: Path | str,
    *,
    allowed: tuple[str, ...],
) -> bool:
    """True = enkel bestand met verkeerde extensie geweigerd."""
    p = Path(path)
    if not p.is_file():
        return False
    suf = p.suffix.lower()
    if suf in {a.lower() for a in allowed}:
        return False
    # Hint: map extensie → straat
    hint_street = {
        ".mscz": "mscz",
        ".mvsa": "mvsa",
        ".vsa": "vsa",
        ".mxl": "mxl",
        ".musicxml": "mxl",
        ".xml": "mxl",
    }.get(suf, "de juiste straat-CLI")
    want = ", ".join(sorted(a.lower() for a in allowed))
    emit_cli_error(
        f"{cli} {cmd} weigert {suf or '(geen extensie)'}; verwacht {want}.",
        path=p,
        hint=f"Gebruik: {hint_street} {cmd} {p}",
    )
    return True


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
        emit_cli_error(
            "-o/--output is alleen toegestaan bij precies één bronbestand.",
            hint="Laat -o weg bij een map; dan komt sibling-output naast elke bron.",
        )
        return True
    for attr in attr_names:
        if getattr(args, attr, None):
            flag = "--" + attr.replace("_", "-")
            emit_cli_error(
                f"{flag} is alleen toegestaan bij precies één bronbestand.",
                hint="Roep het commando per bestand aan, of laat deze vlag weg.",
            )
            return True
    return False


def _add_partituur_style_args(parser: argparse.ArgumentParser) -> None:
    """Shared MuseScore Style overrides (systeemafstand + fonts; partituur/muziek)."""
    parser.add_argument(
        "--compact",
        action="store_true",
        help=(
            "Dichtste Style-baseline: systeemafstand min=max 7 spatium, "
            "lyric-clearance 0.1 (SA/TB), boven-/ondermarge 5 mm, "
            "maat-spreiding 1.6. Andere Style-opties winnen van deze preset. "
            "Niet bij --layout plain."
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
            "Default: 1.2 (bij --compact: 1.6). Hoger = meer spreiding. "
            "Niet bij --layout plain. Lost geen cue-brede maten op "
            "(aparte maat-width)."
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


def _add_vsa_audio_format_parsers(subparsers) -> None:
    """Register ``vsa mp3`` / ``ogg`` / ``wav`` (+ ``audio`` alias for mp3)."""
    from .audio_export import AUDIO_FORMATS

    for format_name in AUDIO_FORMATS:
        extra: dict = {}
        if format_name == "mp3":
            extra["aliases"] = ["audio"]
        parser = subparsers.add_parser(
            format_name,
            help=(
                f"Exporteer .vsa naar audio (.{format_name}) via MuseScore."
            ),
            description=(
                f"Preview-luisteren: .vsa → playback-.mxl → MuseScore → "
                f".{format_name}. Alleen .vsa (straat-puur); voor .mvsa: "
                f"mvsa {format_name}; voor .mscz: mscz {format_name}. "
                "Zelfde vorm als mvsa/mscz: PATH [-o OUTPUT]."
                + (
                    " Alias: audio (verouderd; zelfde als mp3)."
                    if format_name == "mp3"
                    else ""
                )
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=(
                "voorbeelden:\n"
                f"  vsa {format_name} examples\\minimal\\valid-demo.vsa\n"
                f"  vsa {format_name} lied.vsa "
                f"-o generated\\lied.{format_name}"
            ),
            **extra,
        )
        parser.add_argument(
            "path",
            help=".vsa-bestand of map met .vsa-bestanden (recursief).",
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
        from .canonicity_gate import add_allow_noncanonical_arg

        add_allow_noncanonical_arg(parser)


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
                f"Exporteer .mvsa naar audio (.{format_name}) via MuseScore."
            ),
            description=(
                f"Preview-luisteren: .mvsa → playback-.mxl → MuseScore → "
                f".{format_name}. Alleen .mvsa (straat-puur); voor .mscz: "
                f"mscz {format_name}; voor .vsa: vsa {format_name}."
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
                f"-o generated\\lied.{format_name}"
            ),
            **extra,
        )
        parser.add_argument(
            "path",
            help=".mvsa-bestand of map met .mvsa-bestanden (recursief).",
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
            help=(
            "Alleen bij .mvsa: deze @sectie-id (niet @blok; "
            "default: hele bestand)."
        ),
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
        from .canonicity_gate import add_allow_noncanonical_arg

        add_allow_noncanonical_arg(parser)


def run_standalone_mvsa(argv: list[str] | None = None) -> int:
    """Entry for top-level ``mvsa`` console-script / ``cli_mvsa``."""
    parser = _build_mvsa_parser()
    args = parser.parse_args(argv)
    return _cmd_mvsa(args)


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
    if getattr(args, "mvsa_command", None) == "syllabify":
        return _cmd_mvsa_syllabify(args)
    if getattr(args, "mvsa_command", None) == "text":
        return _cmd_mvsa_text(args)
    if getattr(args, "mvsa_command", None) == "vsa":
        return _cmd_mvsa_vsa(args)
    if getattr(args, "mvsa_command", None) == "import":
        from .cli_import import run_mvsa_import

        return run_mvsa_import(args)
    if getattr(args, "mvsa_command", None) == "products":
        from .street_products import run_street_products

        musescore = Path(args.musescore) if getattr(args, "musescore", None) else None
        return run_street_products(
            "mvsa",
            args.path,
            force=bool(args.force),
            dry_run=bool(args.dry_run),
            skip_svg=bool(getattr(args, "skip_svg", False)),
            quiet=bool(getattr(args, "quiet", False)),
            musescore=musescore,
            allow_noncanonical=bool(
                getattr(args, "allow_noncanonical", False)
            ),
        )
    # required=True op subparsers voorkomt dit normaal; fallback voor duidelijkheid.
    print(
        "Gebruik: mvsa "
        "{validate,mxl,mscz,pdf,svg,mp3,ogg,wav,score-ir,normalize,transpose,kuiser,import,products} …\n"
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
            "  mvsa syllabify PATH [--dry-run] [--extension EXT]\n"
            "Score → .mvsa: mxl mvsa … / mscz mvsa …\n"
            "Hulp: mvsa -h | mvsa kuiser -h | mvsa syllabify -h",
        file=sys.stderr,
    )
    return 1


def _cmd_mvsa_validate(args) -> int:
    from .config import load_config
    from .mvsa_validate import (
        MvsaDiagnostic,
        collect_mvsa_files,
        format_diagnostic,
        validate_mvsa_path,
    )
    from .zoektekst import check_zoektekst

    config = load_config(_resolve_config_arg(getattr(args, "config", None)))
    _apply_syllable_dictionary_setting(args, config)

    path = Path(args.path)
    from .input_paths import InputPathError, looks_like_catalogus_id

    if not path.exists() and not looks_like_catalogus_id(args.path):
        emit_cli_error(
            "Pad niet gevonden.",
            path=path,
            hint=(
                "Controleer of het pad bestaat, of geef een catalogus-id "
                "(docs/reference/cli/input-pad.md)."
            ),
        )
        return 1
    try:
        files = collect_mvsa_files(path if path.exists() else args.path)
    except InputPathError as exc:
        emit_cli_error(
            str(exc),
            path=path,
            hint="Geef een .mvsa-bestand, map, of catalogus-id.",
        )
        return 1
    if not files:
        emit_cli_error(
            "Geen .mvsa gevonden.",
            path=path,
            hint="Geef een .mvsa-bestand, map met .mvsa, of catalogus-id.",
        )
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
            emit_cli_error(
                "Pad niet gevonden.",
                path=path,
                hint="Controleer of het bestand of de map bestaat.",
            )
            return 1
        except ValueError as exc:
            emit_cli_exception(
                exc,
                path=path,
                hint="Geef .vsa/.mvsa-bestanden of een map met zulke bestanden.",
            )
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
        emit_cli_error(
            "Geen .vsa / .mvsa gevonden.",
            hint="Geef een bronbestand of een map met .vsa/.mvsa.",
        )
        return 1

    if args.output is not None:
        if len(files) != 1 or not paths[0].is_file():
            emit_cli_error(
                "-o is alleen toegestaan bij precies één bronbestand.",
                hint="Laat -o weg bij een map, of geef één bestand.",
            )
            return 1

    errors = 0
    changed_n = 0
    for file_path in files:
        try:
            kind = kind_from_path(file_path)
        except ValueError as exc:
            emit_cli_exception(exc, path=file_path)
            errors += 1
            continue
        text = file_path.read_text(encoding="utf-8-sig")
        if args.check:
            issues = check_zoektekst(text, kind=kind, require=True)
            if issues:
                errors += 1
                for issue in issues:
                    emit_cli_error(
                        f"{issue.code}: {issue.message}",
                        path=file_path,
                        hint="Werk zoektekst bij met: vsa zoektekst <pad>",
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
    from .canonicity_gate import (
        NonCanonicalTargetError,
        emit_noncanonical_error,
    )
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
        allow = bool(getattr(args, "allow_noncanonical", False))
        try:
            export_mvsa_path_to_score_ir(
                path,
                out,
                section_id=args.section,
                bibliotheek_id=getattr(args, "bibliotheek_id", None),
                allow_noncanonical=allow,
            )
            if mxl_path is not None:
                export_score_ir_path_to_musicxml(out, mxl_path)
        except NonCanonicalTargetError as exc:
            emit_noncanonical_error(exc)
            exit_code = 1
            continue
        except MvsaValidationError as exc:
            for d in exc.diagnostics:
                print(format_diagnostic(d, path), file=sys.stderr)
            exit_code = 1
            continue
        except MvsaExportError as exc:
            emit_cli_exception(exc, path=path)
            exit_code = 1
            continue
        except ScoreIrMusicxmlError as exc:
            emit_cli_exception(exc, path=path)
            exit_code = 1
            continue
        print(f"Geschreven: {out}")
        if mxl_path is not None:
            print(f"MusicXML: {mxl_path}")
        from .street_products import merge_street_product_meta

        meta_products: dict[str, Path] = {"score-ir": out}
        if mxl_path is not None:
            meta_products["from-ir"] = mxl_path
        meta = merge_street_product_meta(path, meta_products)
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_mvsa_musicxml(args) -> int:
    from .canonicity_gate import cli_gate_source
    from .musicxml_package import musicxml_output_suffix
    from .mvsa_musicxml import MvsaExportError, export_mvsa_path
    from .mvsa_validate import MvsaValidationError, format_diagnostic
    from .street_products import merge_street_product_meta

    if _reject_wrong_street_source("mvsa", "mxl", args.path, wrong_suffix=".mscz"):
        return 1
    if _reject_non_street_file("mvsa", "mxl", args.path, allowed=(".mvsa",)):
        return 1
    files = _cli_collect_sources(args.path, (".mvsa",))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args):
        return 1
    exit_code = 0
    for path in files:
        if cli_gate_source(path, args):
            exit_code = 1
            continue
        out = (
            Path(args.output)
            if args.output
            else derived_output_path(path, ".mxl")
        )
        if out.suffix.lower() not in {".mxl", ".musicxml", ".xml"}:
            out = out.with_suffix(musicxml_output_suffix(path=out))
        tkw = _cli_translit_kwargs(args)
        try:
            export_mvsa_path(
                path,
                out,
                section_id=args.section,
                bibliotheek_id=getattr(args, "bibliotheek_id", None),
                **tkw,
            )
        except MvsaValidationError as exc:
            for d in exc.diagnostics:
                print(format_diagnostic(d, path), file=sys.stderr)
            exit_code = 1
            continue
        except MvsaExportError as exc:
            emit_cli_exception(exc, path=path)
            exit_code = 1
            continue
        # Translit-Coria (``--translit-as-parts`` / ``*.translit.mxl``) is een
        # apart product; niet de canonieke key ``mxl`` overschrijven.
        # C4 geldt alleen voor de standaard playback-key ``mxl``.
        out_name = out.name.lower()
        if tkw.get("translit_as_parts") or out_name.endswith(".translit.mxl"):
            meta_key = "mxl-translit"
        else:
            meta_key = "mxl"
            from .canonicity_gate import (
                NonCanonicalTargetError,
                emit_noncanonical_error,
                require_canonical_mxl_target,
            )

            try:
                require_canonical_mxl_target(
                    out,
                    bron=path,
                    allow_noncanonical=bool(
                        getattr(args, "allow_noncanonical", False)
                    ),
                )
            except NonCanonicalTargetError as exc:
                emit_noncanonical_error(exc)
                exit_code = 1
                continue
        print(f"Geschreven: {out}")
        meta = merge_street_product_meta(path, {meta_key: out})
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_mvsa_mscz(args) -> int:
    from .canonicity_gate import cli_gate_source
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
        if cli_gate_source(path, args):
            exit_code = 1
            continue
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
                **{
                    k: v
                    for k, v in _cli_translit_kwargs(args).items()
                    if k != "translit_as_parts"
                },
                **_partituur_style_kwargs(args),
            )
        except MvsaValidationError as exc:
            for d in exc.diagnostics:
                print(format_diagnostic(d, path), file=sys.stderr)
            exit_code = 1
            continue
        except MvsaExportError as exc:
            emit_cli_exception(exc, path=path)
            exit_code = 1
            continue
        except MvsaMsczError as exc:
            emit_cli_exception(exc, path=path)
            exit_code = 1
            continue
        print(f"Geschreven: {out}")
        if keep_mxl is not None:
            print(f"MXL: {keep_mxl}")
        from .street_products import MSCZ_PRODUCT_KEY, merge_street_product_meta

        meta = merge_street_product_meta(path, {MSCZ_PRODUCT_KEY: out})
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_mvsa_vsa(args) -> int:
    """``mvsa vsa`` — E1–E6 extractie naar sibling ``.mvsa.vsa``."""
    from .cli_messages import emit_cli_exception
    from .mvsa_vsa import (
        MvsaVsaError,
        convert_mvsa_path_all_voices,
        convert_mvsa_to_vsa,
        default_mvsa_vsa_output,
    )

    files = _cli_collect_sources(args.path, (".mvsa",))
    if files is None:
        return 1
    voice = str(getattr(args, "voice", "S") or "S").strip()
    all_voices = voice.lower() == "all"
    if all_voices and getattr(args, "output", None):
        print(
            "ERROR: -o is niet toegestaan bij --voice all "
            "(meerdere uitvoerbestanden).",
            file=sys.stderr,
        )
        return 2
    if _cli_reject_multi_single_opts(files, args):
        return 1
    exit_code = 0
    for path in files:
        try:
            if all_voices:
                written = convert_mvsa_path_all_voices(path)
                for out in written:
                    print(f"Geschreven: {out}")
            else:
                out = (
                    Path(args.output)
                    if args.output
                    else default_mvsa_vsa_output(path)
                )
                convert_mvsa_to_vsa(path, out, voice=voice)
                print(f"Geschreven: {out}")
        except MvsaVsaError as exc:
            emit_cli_exception(exc, path=path)
            exit_code = 1
            continue
        except Exception as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
    return exit_code


def _cmd_mvsa_text(args) -> int:
    """``mvsa text``: alleen ``.mvsa`` → sibling lyrics + meta."""
    from .canonicity_gate import cli_gate_source
    from .street_product_export import write_lyrics_product
    from .street_products import LYRICS_KEY, merge_street_product_meta

    if _reject_wrong_street_source("mvsa", "text", args.path, wrong_suffix=".mscz"):
        return 1
    if _reject_wrong_street_source(
        "mvsa", "text", args.path, wrong_suffix=".vsa", hint_street="vsa"
    ):
        return 1
    if _reject_non_street_file("mvsa", "text", args.path, allowed=(".mvsa",)):
        return 1
    files = _cli_collect_sources(args.path, (".mvsa",))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args):
        return 1
    exit_code = 0
    for path in files:
        if cli_gate_source(path, args):
            exit_code = 1
            continue
        out = (
            Path(args.output)
            if args.output
            else derived_output_path(path, ".lyrics.txt")
        )
        try:
            written = write_lyrics_product(path, out)
        except Exception as exc:
            emit_cli_exception(exc, path=path)
            exit_code = 1
            continue
        print(f"Geschreven: {written}")
        meta = merge_street_product_meta(path, {LYRICS_KEY: written})
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_vsa_score_ir(args) -> int:
    from .canonicity_gate import (
        NonCanonicalTargetError,
        emit_noncanonical_error,
    )
    from .score_ir_musicxml import (
        ScoreIrMusicxmlError,
        export_score_ir_path_to_musicxml,
    )
    from .street_product_export import (
        StreetProductExportError,
        export_bron_to_score_ir,
    )
    from .street_products import merge_street_product_meta

    if _reject_non_street_file("vsa", "score-ir", args.path, allowed=(".vsa",)):
        return 1
    files = _cli_collect_sources(args.path, (".vsa",))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args):
        return 1
    musescore = Path(args.musescore) if args.musescore else None
    mxl_opt = getattr(args, "musicxml", None)
    allow = bool(getattr(args, "allow_noncanonical", False))
    exit_code = 0
    for path in files:
        out = (
            Path(args.output)
            if args.output
            else derived_output_path(path, ".score-ir.json")
        )
        mxl_path = None
        if mxl_opt is not None:
            mxl_path = (
                derived_output_path(path, ".from-ir.musicxml")
                if mxl_opt == ""
                else Path(mxl_opt)
            )
        try:
            export_bron_to_score_ir(
                path,
                out,
                musescore=musescore,
                allow_noncanonical=allow,
            )
            if mxl_path is not None:
                export_score_ir_path_to_musicxml(out, mxl_path)
        except NonCanonicalTargetError as exc:
            emit_noncanonical_error(exc)
            exit_code = 1
            continue
        except (StreetProductExportError, ScoreIrMusicxmlError) as exc:
            emit_cli_exception(
                exc,
                path=path,
                hint="Controleer de bron met vsa validate; bij MuseScore: --musescore PATH.",
            )
            exit_code = 1
            continue
        except Exception as exc:
            emit_cli_exception(
                exc,
                path=path,
                hint="Controleer de bron met vsa validate.",
            )
            exit_code = 1
            continue
        print(f"Geschreven: {out}")
        meta_products: dict[str, Path] = {"score-ir": out}
        if mxl_path is not None:
            print(f"MusicXML: {mxl_path}")
            meta_products["from-ir"] = mxl_path
        meta = merge_street_product_meta(path, meta_products)
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_vsa_mscz_product(args) -> int:
    from .street_product_export import (
        StreetProductExportError,
        export_bron_to_mscz_product,
    )
    from .street_products import MSCZ_PRODUCT_KEY, merge_street_product_meta

    from .canonicity_gate import cli_gate_source

    if _reject_non_street_file("vsa", "mscz", args.path, allowed=(".vsa",)):
        return 1
    files = _cli_collect_sources(args.path, (".vsa",))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args):
        return 1
    musescore = Path(args.musescore) if args.musescore else None
    exit_code = 0
    for path in files:
        if cli_gate_source(path, args):
            exit_code = 1
            continue
        out = (
            Path(args.output)
            if args.output
            else derived_output_path(path, ".mscz")
        )
        try:
            written = export_bron_to_mscz_product(
                path, out, musescore=musescore
            )
        except StreetProductExportError as exc:
            emit_cli_exception(
                exc,
                path=path,
                hint=(
                    "Installeer MuseScore 4 of geef --musescore PATH; "
                    "controleer de bron met vsa validate."
                ),
            )
            exit_code = 1
            continue
        except Exception as exc:
            emit_cli_exception(
                exc,
                path=path,
                hint="Controleer de bron met vsa validate.",
            )
            exit_code = 1
            continue
        print(f"Geschreven: {written}")
        meta = merge_street_product_meta(path, {MSCZ_PRODUCT_KEY: written})
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_mvsa_pdf(args) -> int:
    from .mvsa_mscz import MvsaMsczError, export_mvsa_to_pdf
    from .mvsa_musicxml import MvsaExportError
    from .mvsa_validate import MvsaValidationError, format_diagnostic

    if _reject_mscz_use_mscz_street("pdf", args.path):
        return 1
    files = _cli_collect_sources(args.path, (".mvsa",))
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
        try:
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
                **{
                    k: v
                    for k, v in _cli_translit_kwargs(args).items()
                    if k != "translit_as_parts"
                },
                **_partituur_style_kwargs(args),
            )
        except MvsaValidationError as exc:
            for d in exc.diagnostics:
                print(format_diagnostic(d, path), file=sys.stderr)
            exit_code = 1
            continue
        except MvsaExportError as exc:
            emit_cli_exception(exc, path=path)
            exit_code = 1
            continue
        except MvsaMsczError as exc:
            emit_cli_exception(exc, path=path)
            exit_code = 1
            continue
        print(f"Geschreven: {out}")
        if args.keep_mscz:
            print(f"MSCZ: {args.keep_mscz}")
        if args.keep_mxl:
            print(f"MXL: {args.keep_mxl}")
        from .street_products import MSCZ_PDF_KEY, merge_street_product_meta

        meta = merge_street_product_meta(path, {MSCZ_PDF_KEY: out})
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_mvsa_svg(args) -> int:
    from .mvsa_mscz import MvsaMsczError, export_mvsa_to_svg
    from .mvsa_musicxml import MvsaExportError
    from .mvsa_validate import MvsaValidationError, format_diagnostic

    if _reject_mscz_use_mscz_street("svg", args.path):
        return 1
    files = _cli_collect_sources(args.path, (".mvsa",))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args, "keep_mscz", "keep_mxl"):
        return 1
    engine = getattr(args, "engine", "musescore") or "musescore"
    tkw = {
        k: v
        for k, v in _cli_translit_kwargs(args).items()
        if k != "translit_as_parts"
    }
    if engine == "osmd":
        if tkw.get("translit"):
            print(
                "mvsa svg: --translit werkt niet met --engine osmd "
                "(translit-SVG alleen via MuseScore-keten; zie §5a).",
                file=sys.stderr,
            )
            return 1
        if args.keep_mscz or args.musescore or args.no_trim or args.transparent:
            print(
                "mvsa svg --engine osmd: --keep-mscz/--musescore/--no-trim/"
                "--transparent gelden niet (alleen MuseScore-keten)",
                file=sys.stderr,
            )
            return 1
        if _has_partituur_style_cli(args):
            print(
                "mvsa svg --engine osmd: Style-opties (afstand/fonts/spacing) "
                "gelden niet; die zijn MuseScore-Style. "
                "OSMD gebruikt Score-IR/from-ir MusicXML.",
                file=sys.stderr,
            )
            return 1
    from .canonicity_gate import cli_gate_source

    musescore = Path(args.musescore) if args.musescore else None
    trim = not bool(getattr(args, "no_trim", False))
    white_background = not bool(getattr(args, "transparent", False))
    exit_code = 0
    for path in files:
        if cli_gate_source(path, args):
            exit_code = 1
            continue
        out = (
            Path(args.output)
            if args.output
            else derived_svg_output_path(
                path,
                translit=bool(tkw.get("translit")),
                translit_modus=str(tkw.get("translit_modus") or "both"),
            )
        )
        keep_mscz = Path(args.keep_mscz) if args.keep_mscz else None
        keep_mxl = Path(args.keep_mxl) if args.keep_mxl else None
        try:
            written = export_mvsa_to_svg(
                path,
                out,
                section_id=args.section,
                musescore=musescore,
                keep_mscz=keep_mscz,
                keep_mxl=keep_mxl,
                bibliotheek_id=getattr(args, "bibliotheek_id", None),
                **tkw,
                trim=trim,
                white_background=white_background,
                engine=engine,
                **_partituur_style_kwargs(args),
            )
        except MvsaValidationError as exc:
            for d in exc.diagnostics:
                print(format_diagnostic(d, path), file=sys.stderr)
            exit_code = 1
            continue
        except MvsaExportError as exc:
            emit_cli_exception(exc, path=path)
            exit_code = 1
            continue
        except MvsaMsczError as exc:
            emit_cli_exception(exc, path=path)
            exit_code = 1
            continue
        for written_path in written:
            print(f"Geschreven: {written_path}")
        if keep_mscz is not None:
            print(f"MSCZ: {keep_mscz}")
        if keep_mxl is not None:
            print(f"MXL: {keep_mxl}")
        from .street_products import merge_street_product_meta, svg_meta_products

        products, drop = svg_meta_products(path, written)
        meta = merge_street_product_meta(path, products, drop_keys=drop or None)
        if meta is not None:
            print(f"Meta: {meta.name}", flush=True)
    return exit_code


def _cmd_mvsa_audio(args) -> int:
    from .audio_export import AUDIO_FORMATS, AudioExportError, export_to_audio
    from .mvsa_musicxml import MvsaExportError
    from .mvsa_validate import MvsaValidationError, format_diagnostic
    from .street_products import MP3_KEY, merge_street_product_meta

    cmd = getattr(args, "mvsa_command", None)
    format_name = cmd if cmd in AUDIO_FORMATS else "mp3"
    if _reject_wrong_street_source(
        "mvsa", format_name, args.path, wrong_suffix=".mscz"
    ):
        return 1
    if _reject_wrong_street_source(
        "mvsa", format_name, args.path, wrong_suffix=".vsa", hint_street="vsa"
    ):
        return 1
    if _reject_non_street_file(
        "mvsa", format_name, args.path, allowed=(".mvsa",)
    ):
        return 1
    files = _cli_collect_sources(args.path, (".mvsa",))
    if files is None:
        return 1
    if _cli_reject_multi_single_opts(files, args, "keep_mxl"):
        return 1
    from .canonicity_gate import cli_gate_source

    musescore = Path(args.musescore) if args.musescore else None
    exit_code = 0
    for path in files:
        if cli_gate_source(path, args):
            exit_code = 1
            continue
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
            emit_cli_exception(exc, path=path)
            exit_code = 1
            continue
        except AudioExportError as exc:
            emit_cli_exception(exc, path=path)
            exit_code = 1
            continue
        print(f"Geschreven: {written}")
        if keep_mxl is not None:
            print(f"MXL: {keep_mxl}")
        if format_name == "mp3":
            meta = merge_street_product_meta(path, {MP3_KEY: written})
            if meta is not None:
                print(f"Meta: {meta.name}", flush=True)
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
            emit_cli_exception(exc, path=path)
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
            emit_cli_exception(exc, path=path)
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
            emit_cli_exception(exc, path=path)
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


def _cmd_mvsa_syllabify(args) -> int:
    from .config import load_config
    from .mvsa_syllabify import (
        MvsaSyllabifyError,
        iter_mvsa_files,
        mvsa_output_path_for,
        normalize_mvsa_output_extension,
        syllabify_mvsa_text,
    )

    config = load_config(_resolve_config_arg(getattr(args, "config", None)))
    _apply_syllable_dictionary_setting(args, config)

    source_path = Path(args.path)
    if args.extension and args.in_place:
        emit_cli_error(
            "Gebruik --in-place of --extension, niet beide.",
            hint="Zonder --extension schrijft syllabify standaard in-place.",
        )
        return 1

    extension: str | None = None
    if args.extension is not None:
        try:
            extension = normalize_mvsa_output_extension(args.extension)
        except ValueError as exc:
            emit_cli_exception(
                exc,
                hint="Geef een extensie zoals .syl.mvsa; zie mvsa syllabify -h.",
            )
            return 1

    # Uniform met kuiser/zoektekst: default schrijven; --dry-run = preview.
    dry_run = bool(args.dry_run)

    try:
        files = iter_mvsa_files(source_path)
    except FileNotFoundError:
        emit_cli_error(
            "Pad niet gevonden.",
            path=source_path,
            hint="Controleer of het bestand of de map bestaat.",
        )
        return 1
    except ValueError as exc:
        emit_cli_exception(
            exc,
            path=source_path,
            hint="Geef een .mvsa-bestand of een map met .mvsa-bestanden.",
        )
        return 1

    if not files:
        emit_cli_error(
            "Geen .mvsa-bestanden gevonden.",
            path=source_path,
            hint="Zet .mvsa-bestanden in deze map of geef een ander pad.",
        )
        return 1

    multi = len(files) > 1 or source_path.is_dir()
    any_error = False
    verb = "verwijderd" if args.unsyllabify else "toegevoegd"

    for file_path in files:
        try:
            target = mvsa_output_path_for(file_path, extension)
        except ValueError as exc:
            emit_cli_exception(exc, path=file_path)
            any_error = True
            continue

        if extension is not None and file_path.name.lower().endswith(
            extension.lower()
        ):
            emit_cli_error(
                f"Overgeslagen: bestandsnaam eindigt al op {extension}.",
                path=file_path,
                hint="Kies een andere --extension of hernoem het bronbestand.",
            )
            continue

        original = file_path.read_text(encoding="utf-8-sig")
        try:
            result = syllabify_mvsa_text(
                original,
                unsyllabify=args.unsyllabify,
                align=not args.no_align,
            )
        except MvsaSyllabifyError as exc:
            emit_cli_exception(
                exc,
                path=file_path,
                hint="Controleer de .mvsa met: mvsa validate <pad>",
            )
            any_error = True
            continue
        except Exception as exc:
            emit_cli_exception(
                exc,
                path=file_path,
                hint="Controleer de .mvsa met: mvsa validate <pad>",
            )
            any_error = True
            continue

        if not args.unsyllabify:
            dict_rc, gated_text = _mvsa_syllabify_dictionary_gate(
                file_path, result.text
            )
            if gated_text != result.text:
                from .mvsa_syllabify import MvsaSyllabifyResult

                result = MvsaSyllabifyResult(
                    text=gated_text,
                    changed=True,
                    replacements=result.replacements,
                )
            if dict_rc != 0:
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
            target.write_text(result.text, encoding="utf-8", newline="\n")
        if target == file_path:
            print(f"{file_path}: {status}")
        else:
            print(f"{file_path} -> {target}: {status}")

    return 1 if any_error else 0


def _mvsa_syllabify_dictionary_gate(
    file_path: Path, source_text: str
) -> tuple[int, str]:
    """Dictionary-check op .mvsa L-lyrics; op TTY corrigeren."""
    from .syllable_dict_check import (
        CODE_MISMATCH,
        CODE_UNKNOWN,
        apply_replacements_to_source,
        find_mvsa_dictionary_syllable_issues,
        is_interactive_stdin,
        prompt_dictionary_fixes,
    )

    findings = find_mvsa_dictionary_syllable_issues(source_text)
    text = source_text
    if is_interactive_stdin():
        actionable = [
            f for f in findings if f.code in {CODE_MISMATCH, CODE_UNKNOWN}
        ]
        if actionable:
            from .input_paths import source_id_for_prompt

            prompt = prompt_dictionary_fixes(
                actionable, source_id=source_id_for_prompt(file_path)
            )
            if prompt.replacements:
                text = apply_replacements_to_source(text, prompt.replacements)
                findings = find_mvsa_dictionary_syllable_issues(text)

    fatal = [f for f in findings if f.code in {CODE_MISMATCH, CODE_UNKNOWN}]
    for finding in findings:
        print(
            f"{file_path}:{finding.line}:{finding.column}: "
            f"{finding.code}: {finding.message_nl}",
            file=sys.stderr if finding.code in {CODE_MISMATCH, CODE_UNKNOWN} else sys.stdout,
        )
        if finding.hint_nl:
            print(f"  hint: {finding.hint_nl}", file=sys.stderr)
    # Zelfde mildheid als mvsa validate: dictionary is warning, geen hard fail.
    _ = fatal
    return 0, text


def _cmd_template_validate(args) -> int:
    from .template_validate import (
        TemplateValidationError,
        collect_template_ids,
        load_template,
        validate_template,
    )

    path = Path(args.path)
    if not path.exists():
        emit_cli_error(
            "Pad niet gevonden.",
            path=path,
            hint="Geef template.yaml of een map met template.yaml-bestanden.",
        )
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
        emit_cli_error(
            "Geen template.yaml gevonden.",
            path=path,
            hint="Zet template.yaml in deze map of geef het bestand expliciet.",
        )
        return 1
    errors = 0
    for yaml_path in files:
        try:
            validate_template(load_template(yaml_path), known_ids=known_ids)
        except TemplateValidationError as exc:
            emit_cli_exception(
                exc,
                path=yaml_path,
                hint="Corrigeer template.yaml; zie vsa template validate -h.",
            )
            errors += 1
            continue
        print(f"{yaml_path}: OK")
    if errors:
        emit_cli_error(
            f"{errors} template(s) ongeldig.",
            hint="Los de gemelde regels hierboven op en draai opnieuw.",
        )
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
