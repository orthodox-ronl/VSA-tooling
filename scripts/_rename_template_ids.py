"""Eenmalig: library-mappen → {soort}-toon-{n}-{bron}; aliases.yaml schrijven.

Run vanuit VSA-tooling-root:
  python scripts/_rename_template_ids.py
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "docs" / "specification-vsa-templates" / "library"

# Oude mapnaam → nieuwe canonieke id
RENAME: dict[str, str] = {
    "kondak-toon-1-groningen": "kondak-toon-1-groningen",
    "tropaar-toon-1-groningen": "tropaar-toon-1-groningen",
    "kondak-toon-2-groningen": "kondak-toon-2-groningen",
    "tropaar-toon-2-groningen": "tropaar-toon-2-groningen",
    "tropaar-toon-3-groningen": "tropaar-toon-3-groningen",
    "tropaar-toon-4-hemelum": "tropaar-toon-4-hemelum",
    "tropaar-toon-4-groningen": "tropaar-toon-4-groningen",
    "kondak-toon-5-groningen": "kondak-toon-5-groningen",
    "tropaar-toon-5-groningen": "tropaar-toon-5-groningen",
    "stichier-toon-5-pdf": "stichier-toon-5-pdf",
    "kondak-toon-6-groningen": "kondak-toon-6-groningen",
    "tropaar-toon-6-groningen": "tropaar-toon-6-groningen",
    "kondak-toon-7-groningen": "kondak-toon-7-groningen",
    "tropaar-toon-7-groningen": "tropaar-toon-7-groningen",
    "kondak-toon-8-groningen": "kondak-toon-8-groningen",
    "tropaar-toon-8-groningen": "tropaar-toon-8-groningen",
    "kondak-toon-8-hemelum": "kondak-toon-8-hemelum",
    "tropaar-toon-8-hemelum": "tropaar-toon-8-hemelum",
    "vers-toon-1-groningen": "vers-toon-1-groningen",
    "vers-toon-5-groningen": "vers-toon-5-groningen",
}


def _rewrite_same_as(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        old = m.group(1)
        return f"same_as: {RENAME.get(old, old)}"

    return re.sub(r"^same_as:\s*(\S+)\s*$", repl, text, flags=re.M)


def main() -> None:
    # Rename directories (two-phase if needed to avoid collisions — none here).
    for old, new in sorted(RENAME.items(), key=lambda x: -len(x[0])):
        src = LIB / old
        dst = LIB / new
        if not src.is_dir():
            if dst.is_dir():
                print(f"skip (already): {new}")
                continue
            print(f"missing: {old}")
            continue
        if dst.exists():
            raise SystemExit(f"target exists: {dst}")
        src.rename(dst)
        print(f"renamed {old} → {new}")

    # Update id + same_as inside each template.yaml
    for new in RENAME.values():
        path = LIB / new / "template.yaml"
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        text2 = re.sub(
            r"^id:\s*\S+\s*$",
            f"id: {new}",
            text,
            count=1,
            flags=re.M,
        )
        text2 = _rewrite_same_as(text2)
        if text2 != text:
            path.write_text(text2, encoding="utf-8", newline="\n")
            print(f"updated yaml id/same_as: {new}")

    # Aliases: old → new, plus liturgikon ≡ hemelum, tropaar≡kondak shortcuts
    aliases: dict[str, str] = {}
    for old, new in RENAME.items():
        aliases[old] = new

    # Playbook / short names
    aliases["hemelum-tropaar-toon-4"] = "tropaar-toon-4-hemelum"
    aliases["hemelum-toon-4"] = "tropaar-toon-4-hemelum"
    aliases["hemelum-kondak-toon-4"] = "tropaar-toon-4-hemelum"
    aliases["liturgikon-tropaar-toon-4-hemelum"] = "tropaar-toon-4-hemelum"
    aliases["liturgikon-kondak-toon-4"] = "tropaar-toon-4-hemelum"

    for n in range(1, 9):
        h = f"kondak-toon-{n}-hemelum"
        # liturgikon → hemelum (when hemelum map exists, else still alias name)
        aliases[f"kondak-toon-{n}-liturgikon"] = h
        aliases[f"tropaar-toon-{n}-liturgikon"] = f"tropaar-toon-{n}-hemelum"
        aliases[f"liturgikon-kondak-toon-{n}"] = h
        aliases[f"liturgikon-tropaar-toon-{n}"] = f"tropaar-toon-{n}-hemelum"
        aliases[f"hemelum-kondak-toon-{n}"] = h
        aliases[f"hemelum-tropaar-toon-{n}"] = f"tropaar-toon-{n}-hemelum"

    # Explicit existing hemelum-8 short names already covered by RENAME keys
    aliases["kondak-toon-8-hemelum"] = "kondak-toon-8-hemelum"
    aliases["tropaar-toon-8-hemelum"] = "tropaar-toon-8-hemelum"

    out = {
        "spec_version": "draft-v0",
        "description": (
            "Alias → canonieke library-map-id. Geladen door "
            "vsa.template_library. Liturgikon ≡ Hemelum; oude ids blijven "
            "werken na hernoem naar {soort}-toon-{n}-{bron}."
        ),
        "aliases": dict(sorted(aliases.items())),
    }
    alias_path = LIB / "aliases.yaml"
    alias_path.write_text(
        yaml.safe_dump(
            out,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        ),
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {alias_path} ({len(aliases)} aliases)")


if __name__ == "__main__":
    main()
