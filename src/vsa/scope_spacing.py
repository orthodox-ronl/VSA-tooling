"""Neighbor-aware scope spacing: safety margins (C) and collision optical gap (D)."""

from __future__ import annotations

from .ast import ScopeNode, TextNode
from .parser import HALFTOON_CANONICAL
from .scope_layout import ScopeLayout, build_scope_layout
from .svg_glyphs import SVGGlyphRenderer, _split_ehm_token


def is_word_atom(node) -> bool:
    """True if this unit continues a sung/plain word (no word boundary)."""
    return isinstance(node, (ScopeNode, TextNode))


def leading_safety_for(previous) -> bool:
    """Apply leading safety margin unless the previous unit continues the word."""
    return previous is None or not is_word_atom(previous)


def trailing_safety_for(nxt) -> bool:
    """Apply trailing safety margin unless the next unit continues the word."""
    return nxt is None or not is_word_atom(nxt)


def _column_glyph_half_width(
    glyphs: SVGGlyphRenderer,
    ehm: str,
    col_width: float,
) -> float:
    if not ehm or ehm == "~":
        return 0.0
    _prefix, base = _split_ehm_token(ehm)
    if not base or base == "~":
        return 0.0
    return glyphs._glyph_width(col_width, glyphs.upper_width_factor, cap_factor=1.35) / 2


def _prefix_overhang(
    glyphs: SVGGlyphRenderer,
    ehm: str,
    col_width: float,
) -> float:
    """How far a halftoon prefix sticks left of the glyph left edge (approx)."""
    if not ehm or len(ehm) < 2 or ehm[0] not in HALFTOON_CANONICAL:
        return 0.0
    glyph_half = _column_glyph_half_width(glyphs, ehm, col_width)
    # Mirror render_height_modifier: prefix at cx - glyph_half - 1, anchor end.
    # Approximate prefix advance as ~0.55 * unit*2.4 (Consolas glyph text).
    prefix_advance = glyphs.unit * 1.3
    return glyph_half + 1.0 + prefix_advance


def trailing_ink_clearance(glyphs: SVGGlyphRenderer, layout: ScopeLayout) -> float:
    """Distance from rightmost upper-glyph ink to the layout's right edge.

    Negative means ink overflows the box (should not happen with prefix_extra).
    """
    if not layout.columns:
        return layout.width
    last = layout.columns[-1]
    # Last column spans [width - last.width, width]; glyph centered.
    glyph_half = _column_glyph_half_width(glyphs, last.ehm, last.width)
    pad = last.width / 2 - glyph_half
    return pad


def leading_ink_clearance(glyphs: SVGGlyphRenderer, layout: ScopeLayout) -> float:
    """Distance from layout left edge to leftmost upper ink (glyph or prefix)."""
    if not layout.columns:
        return layout.width
    first = layout.columns[0]
    glyph_half = _column_glyph_half_width(glyphs, first.ehm, first.width)
    overhang = _prefix_overhang(glyphs, first.ehm, first.width)
    # Without prefix: pad to glyph left = col/2 - glyph_half, plus prefix_extra
    # shifts content — layout already includes prefix_extra at the left.
    # First column includes prefix zone in its width when prefix_extra>0.
    if overhang > 0:
        # Prefix leftmost relative to column start ≈ (col/2 - overhang)
        return layout.prefix_extra + first.width / 2 - overhang
    return layout.prefix_extra + first.width / 2 - glyph_half


def collision_optical_gap(
    left: ScopeNode,
    right: ScopeNode,
    *,
    glyphs: SVGGlyphRenderer,
    font_size: float,
    font_family: str,
    configured_gap: float,
    left_leading_safety: bool,
    left_trailing_safety: bool,
    right_leading_safety: bool,
    right_trailing_safety: bool,
) -> float:
    """Return extra gap before ``right`` when abutting glyphs would be too close (D).

    Uses ``configured_gap`` as the desired minimum clearance between upper inks.
    Returns 0 when clearance is already enough (A for non-colliding word-internal
    pairs). Never applies across whitespace — caller only invokes for adjacent scopes.
    """
    if configured_gap <= 0:
        return 0.0
    if not scope_pair_needs_modifier_gate(left, right):
        return 0.0

    left_layout = build_scope_layout(
        left,
        text_font_size=font_size,
        font_family=font_family,
        leading_safety=left_leading_safety,
        trailing_safety=left_trailing_safety,
    )
    right_layout = build_scope_layout(
        right,
        text_font_size=font_size,
        font_family=font_family,
        leading_safety=right_leading_safety,
        trailing_safety=right_trailing_safety,
    )

    clearance = trailing_ink_clearance(glyphs, left_layout) + leading_ink_clearance(
        glyphs, right_layout
    )
    if clearance >= configured_gap:
        return 0.0
    return round(configured_gap - clearance, 2)


def scope_pair_needs_modifier_gate(left, right) -> bool:
    """Same gate as historical optical gap: at least one scope has visible modifiers."""
    if not isinstance(left, ScopeNode) or not isinstance(right, ScopeNode):
        return False
    return bool(left.height_modifier or left.length_modifier) or bool(
        right.height_modifier or right.length_modifier
    )
