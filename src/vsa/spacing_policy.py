from __future__ import annotations

from .text_metrics import estimate_text_width


def whitespace_width(text: str, font_size: float, font_family: str = "DejaVu Sans") -> float:
    """Return visual advance for source whitespace.

    Real font metrics make text widths more precise, but a musical text renderer
    still needs a minimum visible source-space. Otherwise separate words can
    visually collapse when many text/scopes are rendered as separate units.
    """

    measured = estimate_text_width(
        text,
        font_size,
        preserve_whitespace=True,
        font_family=font_family,
    )

    space_count = max(1, len(text.replace("\t", "    ")))
    minimum = font_size * 0.52 * space_count

    return round(max(measured, minimum), 2)


def scope_safety_margin(font_size: float) -> float:
    """Small extra width for sung text scopes on word edges (C).

    Pillow measurements are better than heuristics, but SVG/browser rendering,
    hinting and glyph overlays still need a modest safety margin — applied only
    toward word boundaries, not where a word continues into the next unit.
    """

    return round(font_size * 0.10, 2)


def filler_line_geometry(start: float, end: float, filler_width: float, font_size: float) -> tuple[float, float]:
    """Return a shorter, subtler filler-line span.

    The reserved layout width may be larger than the visually drawn filler.
    Liturgikon-like fillers should guide the eye, not dominate the word.
    """

    if end <= start or filler_width <= 2.0:
        return start, start

    max_len = font_size * 1.80
    min_len = font_size * 0.45
    desired = max(min_len, min(filler_width * 0.62, max_len))

    return round(start, 2), round(min(end, start + desired), 2)
