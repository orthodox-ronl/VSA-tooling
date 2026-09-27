"""Bibliotheek-id afleiden uit bestandspad (niet uit ``.mvsa``-directives).

Spiegel van VSA-demo ``bibliotheek.id_from_path``: zoekt
``…/bibliotheek/<zangstuk>/<variant>/<uitvoeringsvorm>/…`` in het pad.
"""

from __future__ import annotations

import re
from pathlib import Path

_ID_PART = re.compile(r"^[a-z0-9_-]+$")


def bibliotheek_id_from_path(path: Path | str | None) -> str | None:
    """Return ``zangstuk/variant/uitvoeringsvorm`` of ``None``."""
    if path is None:
        return None
    parts = Path(path).resolve().parts
    for i, part in enumerate(parts):
        if part != "bibliotheek":
            continue
        if i + 3 >= len(parts):
            return None
        segs = parts[i + 1 : i + 4]
        if all(_ID_PART.fullmatch(s) for s in segs):
            return "/".join(segs)
        return None
    return None
