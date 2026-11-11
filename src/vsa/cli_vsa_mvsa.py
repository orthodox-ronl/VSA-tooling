"""CLI: ``vsa mvsa`` — VSA + template → schets-MVSA (T1–T7)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .template_instance import TemplateInstanceError
from .template_library import (
    TemplateLibraryError,
    list_template_ids,
)
from .vsa_mvsa import convert_vsa_to_mvsa, default_vsa_mvsa_output


def add_vsa_mvsa_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "mvsa",
        help="VSA + formule-template → schets-.vsa.mvsa (T1–T7).",
        description=(
            "Zet een .vsa om naar een SATB-schets-.mvsa via een library-"
            "template (mapper + emit). Default-uitvoer: sibling "
            "<stam>.vsa.mvsa (naamgeving stem.brontype.doeltype). "
            "Uitvoer (T6): gekuiste frontmatter, VSA-commentaar, "
            "waarschuwingen, @-kop; geen @speelplan/@blok; "
            "secties cyclus-1/herhaling/laatste (niet toon 3). "
            "Zonder --template: keuze op soort+toon uit de .vsa (T1); "
            "ontbrekend of ambigu → fout. Zie "
            "docs/specification-vsa-templates/vsa-mvsa-contract.md (T1–T7)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  vsa mvsa lied.vsa\n"
            "  vsa mvsa lied.vsa --template tropaar-toon-4-groningen\n"
            "  vsa mvsa lied.vsa --template kondak-toon-1-groningen "
            "-o generated\\lied.vsa.mvsa\n"
            "  vsa mvsa lied.vsa --melody A\n"
            "  vsa mvsa --list-templates\n"
        ),
    )
    p.add_argument(
        "path",
        nargs="?",
        default=None,
        help=".vsa-bronbestand (verplicht tenzij --list-templates).",
    )
    p.add_argument(
        "--template",
        metavar="ID",
        default=None,
        help=(
            "Library-template-id of alias. Zonder deze vlag: afleiden uit "
            "soort+toon in de .vsa (T1). Voorbeelden: tropaar-toon-4-hemelum, "
            "kondak-toon-8, tropaar-toon-4-groningen."
        ),
    )
    p.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        default=None,
        help="Uitvoer-.mvsa (default: sibling <bron>.vsa.mvsa).",
    )
    p.add_argument(
        "--melody",
        metavar="VOICE",
        default="S",
        choices=["S", "A", "T", "B", "s", "a", "t", "b"],
        help="Melodiestem in de template/MVSA (T2; default S).",
    )
    p.add_argument(
        "--library",
        metavar="DIR",
        default=None,
        help="Alternatieve library-map (default: docs/.../library).",
    )
    p.add_argument(
        "--list-templates",
        action="store_true",
        help="Toon bekende template-ids en stop.",
    )
    p.add_argument(
        "--tempo",
        type=int,
        default=None,
        help=(
            "Tempo BPM in de MVSA (default: 180 voor tropaar/kondak; "
            "VSA-frontmatter wordt genegeerd)."
        ),
    )


def run_vsa_mvsa(args: argparse.Namespace) -> int:
    from .cli_messages import emit_cli_error, emit_cli_exception

    library = Path(args.library) if args.library else None
    if args.list_templates:
        for tid in list_template_ids(library):
            print(tid)
        return 0

    if not args.path:
        emit_cli_error(
            "Geen .vsa-pad opgegeven.",
            hint="Gebruik: vsa mvsa <pad.vsa>  of  vsa mvsa --list-templates",
        )
        return 2

    out = (
        Path(args.output)
        if args.output
        else default_vsa_mvsa_output(args.path)
    )
    try:
        result = convert_vsa_to_mvsa(
            args.path,
            template=args.template,
            library_root=library,
            melody_voice=str(args.melody).upper(),
            output=out,
            write=True,
            tempo=args.tempo,
        )
    except TemplateLibraryError as exc:
        emit_cli_exception(
            exc,
            path=args.path,
            hint="Controleer --template / --library; zie vsa mvsa -h.",
        )
        return 2
    except TemplateInstanceError as exc:
        emit_cli_exception(exc, path=args.path)
        return 1
    except FileNotFoundError as exc:
        emit_cli_exception(
            exc,
            path=args.path,
            hint="Controleer of het .vsa-bestand bestaat.",
        )
        return 2

    assert result.output_path is not None
    print(f"Geschreven: {result.output_path}")
    print(
        f"template: {result.resolved.canonical_id}"
        + (
            f" (formule {result.resolved.formula_id})"
            if result.resolved.formula_id != result.resolved.canonical_id
            else ""
        )
    )
    print(f"frases: {len(result.phrase_ids)} {result.phrase_ids}")
    if result.warnings:
        print(f"waarschuwingen: {len(result.warnings)}")
        for w in result.warnings[:8]:
            print(f"  - {w}")
        if len(result.warnings) > 8:
            print(f"  … +{len(result.warnings) - 8} meer")
    return 0
