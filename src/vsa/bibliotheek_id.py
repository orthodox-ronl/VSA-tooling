"""Bibliotheek-id op partituur-export (mechanisme, niet beleid).

**Ownership:** welke id bij een zangstuk hoort, bepaalt de consumer
(bibliotheek-repo / product-scripts). VSA-tooling biedt alleen manieren om
een id *door te geven* naar colofon/metadata (parameter op layout/export).

``bibliotheek_id_from_path`` is een **optioneel hulpmiddel**: het herkent
``…/bibliotheek/<zangstuk>/<variant>/<uitvoeringsvorm>/…`` in een pad.
Consumers mogen die helper gebruiken of — bij voorkeur — de id expliciet
aan de export geven. Zie
docs/guides/reuse-vsa-tooling.md#ownership-tooling-vs-consumer.
"""

from __future__ import annotations

import re
from pathlib import Path

_ID_PART = re.compile(r"^[a-z0-9_-]+$")


def bibliotheek_id_from_path(path: Path | str | None) -> str | None:
    """Return ``zangstuk/variant/uitvoeringsvorm`` of ``None``.

    Convenience only — not authoritative. Prefer an explicit id from the
    consumer when writing colophon/metadata.
    """
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
