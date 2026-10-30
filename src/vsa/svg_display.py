"""Display sizing for embedded VSA SVG images (em-relative to surrounding text)."""

from __future__ import annotations

import re

DEFAULT_RELATIVE_SIZE = 1.25

_SVG_WIDTH_RE = re.compile(r"<svg\b[^>]*\bwidth=\"(\d+(?:\.\d+)?)\"")


def svg_natural_width(svg_text: str) -> float | None:
    """Extract the natural pixel width from a rendered SVG string."""
    m = _SVG_WIDTH_RE.search(svg_text)
    return float(m.group(1)) if m else None


def scale_to_width_value(scale: str, natural_width: float | None) -> str:
    """Convert ``scale`` (e.g. ``70%``) to a CSS width value.

    Prefer absolute pixels from natural width so glyph size stays stable.
    Falls back to the raw scale string when conversion is impossible.
    """
    if natural_width is not None:
        try:
            pct = float(scale.rstrip("%"))
            return f"{round(natural_width * pct / 100)}px"
        except ValueError:
            pass
    return scale


def notation_width_css(
    *,
    natural_width: float | None,
    design_font_size: float = 20.0,
    relative_size: float = DEFAULT_RELATIVE_SIZE,
    scale: str | None = None,
    size: str | None = None,
) -> str | None:
    """Return a CSS ``width`` value for a VSA ``<img>``, or ``None``.

    - ``scale`` (absolute, e.g. ``70%`` / ``200px``) wins when set.
    - ``size`` (unitless factor) fixes the em-factor for that image.
    - Otherwise use ``var(--vsa-size, <relative_size>)`` so wrappers/site CSS inherit.
    """
    if scale:
        return scale_to_width_value(scale, natural_width)

    if natural_width is None or design_font_size <= 0:
        return None

    ratio = f"{(natural_width / design_font_size):.4g}"

    if size is not None and str(size).strip() != "":
        try:
            factor = float(size)
            return f"calc({ratio} * {factor:g} * 1em)"
        except ValueError:
            return None

    default = f"{relative_size:g}"
    return f"calc({ratio} * var(--vsa-size, {default}) * 1em)"


def notation_style_attr(
    *,
    natural_width: float | None,
    design_font_size: float = 20.0,
    relative_size: float = DEFAULT_RELATIVE_SIZE,
    scale: str | None = None,
    size: str | None = None,
) -> str:
    """Inline ``style="…"`` for an ``<img>``, or empty string."""
    width = notation_width_css(
        natural_width=natural_width,
        design_font_size=design_font_size,
        relative_size=relative_size,
        scale=scale,
        size=size,
    )
    if not width:
        return ""
    return f' style="width: {width}; height: auto"'


def vsa_shortcode(
    src: str,
    alt: str | None,
    *,
    natural_width: float | None = None,
    design_font_size: float = 20.0,
    relative_size: float = DEFAULT_RELATIVE_SIZE,
    scale: str | None = None,
    size: str | None = None,
) -> str:
    """Emit Hugo ``vsa`` shortcode; ``scale`` param carries the CSS width value."""
    alt_val = alt if alt is not None else "VSA notatie"
    width = notation_width_css(
        natural_width=natural_width,
        design_font_size=design_font_size,
        relative_size=relative_size,
        scale=scale,
        size=size,
    )
    scale_param = f' scale="{width}"' if width else ""
    return f'{{{{< vsa src="{src}" alt="{alt_val}"{scale_param} >}}}}'
