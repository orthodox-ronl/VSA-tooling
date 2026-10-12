"""Default output paths: ``stem.brontype.doeltype``.

Appends the doel-extension to the full source filename so the brontype
remains visible (``lied.mvsa`` → ``lied.mvsa.mscz``).
"""

from __future__ import annotations

from pathlib import Path


def derived_output_path(source: Path, doel_suffix: str) -> Path:
    """Return ``<source.name><doel_suffix>`` next to ``source``.

    ``doel_suffix`` may be ``mscz`` or ``.mscz``.
    """
    suffix = doel_suffix if doel_suffix.startswith(".") else f".{doel_suffix}"
    return source.with_name(f"{source.name}{suffix}")
