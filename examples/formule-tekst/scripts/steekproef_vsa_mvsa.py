#!/usr/bin/env python3
"""Steekproef: 3× VSA + Hemelum tropaar-toon-4 → schets-.mvsa + disclaimer.

Schrijft alleen naar instanties/schetsen/ — raakt bron-.vsa niet aan.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fase_a_vsa_template import (  # noqa: E402
    emit_mvsa_block,
    ensure_stanza_stars,
    restore_vsa,
)
from vsa.template_instance import TemplateInstanceError, map_vsa_to_template  # noqa: E402
from vsa.yaml_frontmatter import parse_vsa_frontmatter  # noqa: E402

TEMPLATE_YAML = (
    ROOT
    / "docs"
    / "specification-vsa-templates"
    / "library"
    / "tropaar-toon-4"
    / "template.yaml"
)
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


def load_disclaimer_banner() -> str:
    lines: list[str] = []
    for ln in DISCLAIMER.read_text(encoding="utf-8").splitlines():
        if ln.startswith("#  #") or ln.startswith("#  ##"):
            lines.append(ln)
    return "\n".join(lines)


def build_schets(
    *,
    template: dict,
    source: Path,
    out_name: str,
    banner: str,
) -> tuple[bool, str]:
    raw = source.read_text(encoding="utf-8")
    fm, body = restore_vsa(raw)
    meta, _ = parse_vsa_frontmatter(fm + body)
    do = str(template["do"])
    mode = str(template.get("mode", "major"))
    norm_body, _ = ensure_stanza_stars(body)
    vsa_text = fm + norm_body
    title = meta.get("title") or meta.get("titel") or source.stem

    try:
        mapped = map_vsa_to_template(template, vsa_text, source=source.name)
    except TemplateInstanceError as exc:
        return False, f"{source.name}: {exc.code}: {exc.message_nl}"

    blocks = [
        emit_mvsa_block(pid, notes, do=do, mode=mode, index=i, total=len(mapped))
        for i, (pid, notes) in enumerate(mapped, start=1)
    ]
    speelplan = ", ".join(str(i) for i in range(1, len(mapped) + 1))
    rel_src = source.as_posix()
    if rel_src.startswith(ROOT.as_posix()):
        rel_src = rel_src[len(ROOT.as_posix()) :].lstrip("/")

    text = "\n".join(
        [
            f"# From-vsa: {rel_src}",
            f"# Template: {template['id']} (Hemelum tropaar/kondak toon 4)",
            "# Generated: steekproef_vsa_mvsa.py (voorloper van vsa mvsa)",
            banner,
            "",
            f'@title "{title}"',
            f"@do {do}",
            f"@mode {mode}",
            "@oct S=0 A=0 T=-1 B=-1",
            f"@speelplan {speelplan}",
            "",
            *blocks,
            "",
        ]
    )
    out_path = OUT_DIR / out_name
    out_path.write_text(text, encoding="utf-8", newline="\n")
    return True, f"wrote {out_path.relative_to(ROOT)} ({len(mapped)} frases)"


def main() -> int:
    template = yaml.safe_load(TEMPLATE_YAML.read_text(encoding="utf-8"))
    banner = load_disclaimer_banner()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ok_n = 0
    lines = [
        "# Steekproef — VSA + Hemelum tropaar-toon-4 → schets-`.mvsa`",
        "",
        "Drie bestanden, aparte uitvoermap (bron-`.vsa` ongemoeid).",
        "Disclaimer: [`disclaimer-vsa-mvsa.sjabloon.txt`](../../disclaimer-vsa-mvsa.sjabloon.txt).",
        "",
        "| Uitvoer | Bron | Status |",
        "| -------- | ---- | ------ |",
    ]
    for out_name, src in SAMPLES:
        ok, msg = build_schets(
            template=template, source=src, out_name=out_name, banner=banner
        )
        print(msg)
        status = "OK" if ok else f"FAIL — {msg}"
        if ok:
            ok_n += 1
        lines.append(
            f"| [`schetsen/{out_name}`](schetsen/{out_name}) | `{src.name}` | {status} |"
        )
    lines += [
        "",
        f"Geslaagd: **{ok_n}/{len(SAMPLES)}**.",
        "",
        "Volgende handcheck: `mvsa validate` op de schetsen, daarna steekproef",
        "`mvsa mscz` / MuseScore op A/T/B en ankers.",
        "",
    ]
    report = OUT_DIR.parent / "STEEKPROEF.md"
    report.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("wrote", report.relative_to(ROOT))
    return 0 if ok_n == len(SAMPLES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
