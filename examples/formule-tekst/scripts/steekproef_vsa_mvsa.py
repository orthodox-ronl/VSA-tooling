#!/usr/bin/env python3
"""Steekproef: 3× VSA + Hemelum tropaar-toon-4 → schets-.mvsa via ``vsa mvsa``.

Schrijft alleen naar instanties/schetsen/ — raakt bron-.vsa niet aan.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from vsa.template_instance import TemplateInstanceError  # noqa: E402
from vsa.template_library import TemplateLibraryError  # noqa: E402
from vsa.vsa_mvsa import convert_vsa_to_mvsa  # noqa: E402

DISCLAIMER = (
    Path(__file__).resolve().parents[1] / "disclaimer-vsa-mvsa.sjabloon.txt"
)
OUT_DIR = (
    Path(__file__).resolve().parents[1]
    / "tropaar-toon-4"
    / "instanties"
    / "schetsen"
)

SAMPLES: list[tuple[str, Path]] = [
    (
        "tropaar-profeet-elia-toon-4.schets.mvsa",
        ROOT
        / "docs"
        / "specification-vsa-templates"
        / "library"
        / "tropaar-toon-4"
        / "examples"
        / "corpus"
        / "T4-06-profeet-elia.vsa",
    ),
    (
        "tropaar-nikolaas-van-myra-toon-4.schets.mvsa",
        ROOT
        / "docs"
        / "specification-vsa-templates"
        / "library"
        / "tropaar-toon-4"
        / "examples"
        / "corpus"
        / "T4-11-nicolaas-van-myra.vsa",
    ),
    (
        "kondak-profeet-hosea-toon-4.schets.mvsa",
        Path(__file__).resolve().parents[1]
        / "vsa-bestanden"
        / "kondak-profeet-hosea-toon-4.vsa",
    ),
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ok_n = 0
    lines = [
        "# Steekproef — VSA + Hemelum tropaar-toon-4 → schets-`.mvsa`",
        "",
        "Via officiële `vsa.vsa_mvsa.convert_vsa_to_mvsa` / `vsa mvsa`.",
        "",
        "| Uitvoer | Bron | Status |",
        "| -------- | ---- | ------ |",
    ]
    for out_name, src in SAMPLES:
        out_path = OUT_DIR / out_name
        if not src.is_file():
            msg = f"bron ontbreekt: {src}"
            print(msg)
            lines.append(
                f"| [`schetsen/{out_name}`](schetsen/{out_name}) | `{src.name}` | FAIL — {msg} |"
            )
            continue
        try:
            result = convert_vsa_to_mvsa(
                src,
                template="tropaar-toon-4",
                output=out_path,
                write=True,
            )
        except (TemplateInstanceError, TemplateLibraryError) as exc:
            msg = f"{src.name}: {exc}"
            print(msg)
            lines.append(
                f"| [`schetsen/{out_name}`](schetsen/{out_name}) | `{src.name}` | FAIL — {msg} |"
            )
            continue
        ok_n += 1
        msg = f"wrote {out_path.relative_to(ROOT)} ({len(result.phrase_ids)} frases)"
        print(msg)
        lines.append(
            f"| [`schetsen/{out_name}`](schetsen/{out_name}) | `{src.name}` | OK |"
        )
    lines += [
        "",
        f"Geslaagd: **{ok_n}/{len(SAMPLES)}**.",
        "",
        "Handcheck: `mvsa validate` / `mvsa mxl` op de schetsen.",
        "",
    ]
    report = OUT_DIR.parent / "STEEKPROEF.md"
    report.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("wrote", report.relative_to(ROOT))
    _ = DISCLAIMER  # blijft beschikbaar naast de emit-banner
    return 0 if ok_n == len(SAMPLES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
