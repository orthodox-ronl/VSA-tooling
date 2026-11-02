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


def translit_svg_doel_suffix(translit_modus: str | None) -> str:
    """Doel-suffix voor translit-SVG-siblings (§5a).

    ``nls`` → ``.translit-nls.svg``; ``ksl`` → ``.translit-ksl.svg``;
    ``both`` / leeg → ``.translit.svg`` (beide hulprichtingen in één bestand).
    """
    from .transliterate import normalize_translit_modus

    modus = normalize_translit_modus(translit_modus)
    if modus == "nls":
        return ".translit-nls.svg"
    if modus == "ksl":
        return ".translit-ksl.svg"
    return ".translit.svg"


def derived_svg_output_path(
    source: Path,
    *,
    translit: bool = False,
    translit_modus: str | None = "both",
) -> Path:
    """Default SVG-pad: bron-SVG of translit-sibling naast de bron."""
    if not translit:
        return derived_output_path(source, ".svg")
    return derived_output_path(
        source, translit_svg_doel_suffix(translit_modus)
    )
