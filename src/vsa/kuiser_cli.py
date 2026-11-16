"""Gedeelde ``{straat} kuiser``-registratie en fout bij ontbrekende spec.

Canonieke hub: ``docs/formats/kuiser.md``.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable

# Straat → korte status voor help / foutmelding.
KUISER_STATUS: dict[str, str] = {
    "mvsa": "Q1–Q9 (docs/formats/kuiser.md); bestaande layout-kuiser actief",
    "vsa": "V1–V8 (docs/formats/kuiser.md)",
    "mscz": "geen kuiser-spec",
    "mxl": "geen kuiser-spec",
}


def kuiser_spec_missing_message(street: str) -> str:
    """Nederlandse fouttekst als er (nog) geen kuiser-contract is."""
    status = KUISER_STATUS.get(street, "geen kuiser-spec")
    return (
        f"{street} kuiser: {status}.\n"
        "Canonieke hub: docs/formats/kuiser.md "
        "(of https://github.com/orthodox-ronl/VSA-tooling/blob/main/docs/formats/kuiser.md).\n"
        "Leg eerst een checklist vast voor dit bestandstype, of gebruik "
        "mvsa kuiser voor .mvsa."
    )


def add_kuiser_parser(
    sub: argparse._SubParsersAction,
    *,
    street: str,
    implemented: bool = False,
) -> argparse.ArgumentParser:
    """Voeg ``kuiser`` toe. ``implemented=False`` → handler moet weigeren."""
    status = KUISER_STATUS.get(street, "geen kuiser-spec")
    p = sub.add_parser(
        "kuiser",
        help=f"Authoring-kuiser ({status}).",
        description=(
            f"Opkuisen naar canonieke authoring-vorm ({street}). "
            f"Status: {status}. Hub: docs/formats/kuiser.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Voorbeelden:\n"
            f"  {street} kuiser pad\\naar\\bestand\n"
            f"  {street} kuiser pad\\naar\\map --check\n"
            f"  {street} kuiser communievers/kruisverheffing/hemelum --check\n"
            "\n"
            "Invoer: bestand, map of catalogus-id "
            "(docs/reference/cli/input-pad.md).\n"
        ),
    )
    p.add_argument(
        "path",
        nargs="+" if implemented else "*",
        help=(
            "Bronbestand, map (recursief), of catalogus-id "
            "(docs/reference/cli/input-pad.md)."
        ),
    )
    p.add_argument(
        "-o",
        "--output",
        help="Uitvoerpad (alleen bij precies één bron; default: in-place of sibling)",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="Dry-run: toon of er iets zou wijzigen (standaard: uit)",
    )
    if street == "vsa" and implemented:
        p.add_argument(
            "--werkbank",
            action="store_true",
            help=(
                "Behoud werkbank-FM-skelet / schetscomments (V5). "
                "Default: catalogus-strip."
            ),
        )
    p.set_defaults(_kuiser_street=street, _kuiser_implemented=implemented)
    return p


def run_kuiser_stub(street: str) -> int:
    """Exit 2: geen (of nog niet vastgelegde) kuiser-spec."""
    print(kuiser_spec_missing_message(street), flush=True)
    return 2


def dispatch_kuiser(
    ns: argparse.Namespace,
    *,
    implemented_handler: Callable[[argparse.Namespace], int] | None = None,
) -> int:
    """Roep implementatie aan of stub-fout."""
    street = getattr(ns, "_kuiser_street", "?")
    implemented = bool(getattr(ns, "_kuiser_implemented", False))
    if implemented and implemented_handler is not None:
        return implemented_handler(ns)
    return run_kuiser_stub(street)
