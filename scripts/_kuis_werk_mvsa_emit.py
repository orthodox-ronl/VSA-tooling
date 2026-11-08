"""Eenmalig: _werk/toon-* schets-MVSA's naar T6-emitvorm (geen speelplan/@blok).

Gebruik:
  python scripts/_kuis_werk_mvsa_emit.py --dry-run
  python scripts/_kuis_werk_mvsa_emit.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from vsa.vsa_mvsa import clean_emit_frontmatter, section_id_for_phrase_index
from vsa.yaml_frontmatter import parse_vsa_frontmatter

FRASE_RE = re.compile(r"^# template-frase '([^']+)'\s*\((\d+)/(\d+)\)\s*$")
BLOK_RE = re.compile(r"^@blok\s+\S+\s*$")
SPEEL_RE = re.compile(r"^@speelplan\b")


def infer_cycle_len(phrase_ids: list[str]) -> int:
    final_start = next(
        (i for i, p in enumerate(phrase_ids) if p == "laatste"),
        len(phrase_ids),
    )
    prefix = phrase_ids[:final_start]
    if not prefix:
        return 1
    first = prefix[0]
    for i in range(1, len(prefix)):
        if prefix[i] == first:
            return i
    return len(prefix)


def _tone_from_path(path: Path, meta: dict) -> int | None:
    parent = path.parent.name
    if parent.startswith("toon-"):
        try:
            return int(parent.split("-", 1)[1])
        except ValueError:
            pass
    tone = meta.get("toon")
    try:
        return int(tone) if tone is not None else None
    except (TypeError, ValueError):
        return None


def _parse_systems(
    lines: list[str], start: int
) -> tuple[list[str], list[list[str]]]:
    phrase_ids: list[str] = []
    systems: list[list[str]] = []
    j = start
    while j < len(lines):
        ln = lines[j]
        m = FRASE_RE.match(ln)
        if m:
            phrase_ids.append(m.group(1))
            j += 1
            if j < len(lines) and BLOK_RE.match(lines[j]):
                j += 1
            sys_lines: list[str] = []
            while j < len(lines):
                cur = lines[j]
                if FRASE_RE.match(cur) or BLOK_RE.match(cur):
                    break
                if cur.strip() == "":
                    j += 1
                    if sys_lines:
                        break
                    continue
                if cur.startswith(("L:", "S:", "A:", "T:", "B:")):
                    sys_lines.append(cur)
                    j += 1
                    continue
                if cur.startswith("#"):
                    j += 1
                    continue
                break
            systems.append(sys_lines)
            continue
        if BLOK_RE.match(ln):
            phrase_ids.append(str(len(phrase_ids) + 1))
            j += 1
            sys_lines = []
            while j < len(lines):
                cur = lines[j]
                if FRASE_RE.match(cur) or BLOK_RE.match(cur):
                    break
                if cur.strip() == "":
                    j += 1
                    if sys_lines:
                        break
                    continue
                if cur.startswith(("L:", "S:", "A:", "T:", "B:")):
                    sys_lines.append(cur)
                    j += 1
                    continue
                if cur.startswith("#"):
                    j += 1
                    continue
                break
            systems.append(sys_lines)
            continue
        j += 1
    return phrase_ids, systems


def transform(text: str, *, tone: int | None) -> str:
    meta, body = parse_vsa_frontmatter(text)
    fm_out = clean_emit_frontmatter(meta)
    lines = body.splitlines()

    first_sys = next(
        (
            j
            for j, ln in enumerate(lines)
            if FRASE_RE.match(ln) or BLOK_RE.match(ln)
        ),
        None,
    )
    if first_sys is None:
        raise ValueError("geen @blok / template-frase gevonden")

    preamble = lines[:first_sys]
    phrase_ids, systems = _parse_systems(lines, first_sys)
    if not systems:
        raise ValueError("geen systemen geparsed")

    new_pre: list[str] = []
    for ln in preamble:
        if SPEEL_RE.match(ln):
            continue
        if BLOK_RE.match(ln) or FRASE_RE.match(ln):
            continue
        if ln.startswith("@tempo"):
            new_pre.append("@tempo 180")
            continue
        new_pre.append(ln)
    while new_pre and new_pre[-1].strip() == "":
        new_pre.pop()

    with_sections = tone != 3
    cycle_len = infer_cycle_len(phrase_ids) if phrase_ids else 1

    out: list[str] = []
    if fm_out:
        out.append(fm_out)
        out.append("")
    out.extend(new_pre)
    out.append("")

    prev: str | None = None
    for idx, sys_lines in enumerate(systems):
        if with_sections and phrase_ids:
            sec = section_id_for_phrase_index(
                idx,
                phrase_ids,
                cycle_len=cycle_len,
                final_id="laatste",
            )
            if sec and sec != prev:
                out.append(f"@sectie {sec}")
                prev = sec
        out.extend(sys_lines)
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--root",
        type=Path,
        default=Path(
            r"C:\Git\orthodox-ronl\bibliotheek\content-source\input\_werk"
        ),
    )
    ap.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Alleen deze relatieve paden t.o.v. root (steekproef).",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    root: Path = args.root
    if args.only:
        paths = [root / p for p in args.only]
    else:
        paths = sorted(root.glob("toon-*/*.mvsa"))

    ok = 0
    for path in paths:
        raw = path.read_text(encoding="utf-8")
        meta, _ = parse_vsa_frontmatter(raw)
        tone = _tone_from_path(path, meta)
        try:
            new = transform(raw, tone=tone)
        except ValueError as exc:
            print(f"FAIL {path.relative_to(root)}: {exc}", file=sys.stderr)
            return 1
        checks = [
            ("@speelplan" not in new, "speelplan blijft"),
            ("@blok" not in new, "blok blijft"),
            ("template-frase" not in new, "frase-comment blijft"),
            ("@tempo 180" in new, "geen tempo 180"),
        ]
        if tone != 3:
            checks.extend(
                [
                    ("@sectie cyclus-1" in new, "geen cyclus-1"),
                    ("@sectie laatste" in new, "geen laatste"),
                ]
            )
        else:
            checks.append(("@sectie" not in new, "sectie op toon 3"))
        for cond, msg in checks:
            if not cond:
                print(f"FAIL {path.relative_to(root)}: {msg}", file=sys.stderr)
                return 1
        if args.dry_run:
            print(f"OK dry-run {path.relative_to(root)} ({len(new)} chars)")
        else:
            path.write_text(new, encoding="utf-8", newline="\n")
            print(f"wrote {path.relative_to(root)}")
        ok += 1
    print(f"done {ok} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
