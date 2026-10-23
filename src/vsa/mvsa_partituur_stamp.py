"""Herkomststempels op import-``.mscz.mvsa`` (na ``mscz mvsa``).

Bibliotheek-``check_import_mvsa`` eist ``# vsa-partituur-sha256:`` (hash van
de bron-``.mscz``). Zonder deze regels faalt ``check --strict`` op
bestaande siblings.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

FIELD_PARTITUUR_SHA = "vsa-partituur-sha256"
FIELD_SOURCE_KIND = "vsa-source-kind"
FIELD_GENERATED_AT = "vsa-generated-at"
FIELD_GENERATOR = "vsa-generator"
SOURCE_KIND_PARTITUUR = "partituur"
GENERATOR_MSCZ_MVSA = "mscz-mvsa"

_STAMP_LINE = re.compile(
    r"^#\s*vsa-(?:partituur-sha256|hub-sha256|source-kind|generated-at|generator)\s*:",
    re.IGNORECASE,
)


def is_mscz_import_mvsa(path: Path) -> bool:
    return path.name.lower().endswith(".mscz.mvsa")


def partituur_sha256(mscz: Path) -> str:
    return hashlib.sha256(mscz.read_bytes()).hexdigest()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _strip_stamp_lines(text: str) -> str:
    lines = text.splitlines(keepends=True)
    kept: list[str] = []
    for line in lines:
        bare = line.rstrip("\r\n")
        if _STAMP_LINE.match(bare):
            continue
        kept.append(line)
    return "".join(kept)


def stamp_mscz_import_mvsa(
    mvsa: Path,
    mscz: Path,
    *,
    generator: str = GENERATOR_MSCZ_MVSA,
) -> None:
    """Schrijf herkomstcommentaren bovenaan een ``*.mscz.mvsa``."""
    raw = mvsa.read_text(encoding="utf-8")
    body = _strip_stamp_lines(raw).lstrip("\n")
    digest = partituur_sha256(mscz)
    block = "\n".join(
        [
            f"# {FIELD_PARTITUUR_SHA}: {digest}",
            f"# {FIELD_SOURCE_KIND}: {SOURCE_KIND_PARTITUUR}",
            f"# {FIELD_GENERATED_AT}: {_utc_now_iso()}",
            f"# {FIELD_GENERATOR}: {generator}",
            "",
        ]
    )
    if body.startswith("---"):
        end = body.find("\n---", 3)
        if end >= 0:
            close = end + len("\n---")
            if close < len(body) and body[close] == "\n":
                close += 1
            mvsa.write_text(
                body[:close] + block + body[close:].lstrip("\n"),
                encoding="utf-8",
                newline="\n",
            )
            return
    mvsa.write_text(block + body, encoding="utf-8", newline="\n")
