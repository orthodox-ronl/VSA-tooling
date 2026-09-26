"""Top-level ``mvsa`` CLI (bron: ``.mvsa``).

Alias van ``vsa mvsa …``. Zie docs/plans/mvsa-conversions.md.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    from .cli import main as vsa_main

    args = list(sys.argv[1:] if argv is None else argv)
    return vsa_main(["mvsa", *args])


if __name__ == "__main__":
    raise SystemExit(main())
