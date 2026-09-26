"""Align mvsa LSATB columns (canonical L↔SATB layout).

CLI wrapper around :func:`vsa.mvsa_align.align_mvsa_text`.

Usage:
  python scripts/align_mvsa_columns.py examples/mvsa
  python scripts/align_mvsa_columns.py examples/mvsa --check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vsa.mvsa_align import align_mvsa_text  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    files: list[Path] = []
    for p in args.paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.mvsa")))
        else:
            files.append(p)
    changed = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        new = align_mvsa_text(text)
        if new != text:
            changed += 1
            if args.check:
                print(f"would change: {path}")
            else:
                path.write_text(new, encoding="utf-8", newline="\n")
                print(f"aligned: {path}")
        else:
            print(f"ok: {path}")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
