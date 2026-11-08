#!/usr/bin/env python3
"""Compat-shim: Fase A-onderzoek → officiële ``vsa.vsa_mvsa`` (T1–T7).

Nieuw werk: ``vsa mvsa`` of ``from vsa.vsa_mvsa import convert_vsa_to_mvsa``.
Dit script blijft bestaan zodat oude notes/steekproeven blijven werken.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from vsa.vsa_mvsa import *  # noqa: F403
from vsa.vsa_mvsa import (  # noqa: E402,F401
    DEFAULT_OCT_LINE,
    DEFAULT_TEMPO_TROPAAR_KONDAK,
    DEFAULT_VOICE_OCT,
    TEMPLATE_DERIVED_WARNING_BANNER,
    FileResult,
    VsaMvsaResult,
    _VOICE_OCT,
    _format_syllable_l,
    analyze_mapped,
    collect_emit_warnings,
    convert_vsa_to_mvsa,
    emit_mapped_document,
    emit_mvsa_block,
    ensure_stanza_stars,
    format_emit_warnings,
    map_vsa_to_template,
    restore_vsa,
)

# Paden die het oude research-main verwachtte.
VSA_DIR = Path(__file__).resolve().parents[1] / "vsa-bestanden"
TEMPLATE_YAML = (
    ROOT
    / "docs"
    / "specification-vsa-templates"
    / "library"
    / "tropaar-toon-4"
    / "template.yaml"
)
FORMULE_MVSA = (
    Path(__file__).resolve().parents[1]
    / "tropaar-toon-4"
    / "formules"
    / "tropaar-toon-4.formule.mvsa"
)


def main() -> int:
    """Steekproef via de officiële converter (Hemelum toon 4)."""
    files = sorted(VSA_DIR.glob("*toon-4*.vsa"))
    if not files:
        print(f"geen *toon-4*.vsa in {VSA_DIR}", file=sys.stderr)
        return 1
    ok = 0
    for path in files:
        out = path.with_suffix(".fase-a.mvsa")
        try:
            result = convert_vsa_to_mvsa(
                path,
                template="tropaar-toon-4",
                output=out,
                write=True,
            )
        except Exception as exc:  # noqa: BLE001 — research CLI
            print(f"FAIL {path.name}: {exc}")
            continue
        ok += 1
        print(
            f"OK {path.name} → {out.name} frases={result.phrase_ids} "
            f"warn={len(result.warnings)}"
        )
    print(f"geslaagd {ok}/{len(files)}")
    return 0 if ok == len(files) else 1


if __name__ == "__main__":
    raise SystemExit(main())
