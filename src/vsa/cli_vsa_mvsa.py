"""CLI: ``vsa mvsa`` — VSA + template → schets-MVSA (T1–T7)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .template_instance import TemplateInstanceError
from .template_library import (
    DEFAULT_TEMPLATE_ID,
    TemplateLibraryError,
    list_template_ids,
)
from .vsa_mvsa import convert_vsa_to_mvsa


def add_vsa_mvsa_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "mvsa",
        help="VSA + formule-template → schets-.mvsa (T1–T7).",
        description=(
            "Zet een .vsa om naar een SATB-schets-.mvsa via een library-"
            "template (mapper + emit). Uitvoer (T6): gekuiste frontmatter, "
            "VSA-commentaar, waarschuwingen, @-kop; geen @speelplan/@blok; "
            "secties cyclus-1/herhaling/laatste (niet toon 3). "
            "Default-template: Hemelum tropaar/kondak toon 4. Zie "
            "docs/specification-vsa-templates/vsa-mvsa-contract.md (T1–T7)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "voorbeelden:\n"
            "  vsa mvsa lied.vsa\n"
            "  vsa mvsa lied.vsa --template groningen-tropaar-toon-4\n"
            "  vsa mvsa lied.vsa --template kondak-toon-1 -o schets.mvsa\n"
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
            f"Library-template-id of alias (default: {DEFAULT_TEMPLATE_ID}). "
            "Voorbeelden: tropaar-toon-4, hemelum-tropaar-toon-4, "
            "groningen-tropaar-toon-4, kondak-toon-1, tropaar-toon-2."
        ),
    )
    p.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        default=None,
        help="Uitvoer-.mvsa (default: sibling <bron>.mvsa).",
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
    library = Path(args.library) if args.library else None
    if args.list_templates:
        for tid in list_template_ids(library):
            print(tid)
        return 0

    if not args.path:
        print(
            "vsa mvsa: geef een .vsa-pad, of --list-templates.",
            file=sys.stderr,
        )
        return 2

    out = Path(args.output) if args.output else Path(args.path).with_suffix(".mvsa")
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
        print(f"vsa mvsa: {exc.code}: {exc}", file=sys.stderr)
        return 2
    except TemplateInstanceError as exc:
        print(f"vsa mvsa: {exc.code}: {exc.message_nl}", file=sys.stderr)
        if exc.hint_nl:
            print(f"Hint: {exc.hint_nl}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"vsa mvsa: {exc}", file=sys.stderr)
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
