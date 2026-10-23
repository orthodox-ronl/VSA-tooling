"""Top-level ``mvsa`` CLI (bron: ``.mvsa``).

Zie docs/plans/mvsa-conversions.md.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    from .cli import run_standalone_mvsa

    args = list(sys.argv[1:] if argv is None else argv)
    return run_standalone_mvsa(args)


if __name__ == "__main__":
    raise SystemExit(main())
