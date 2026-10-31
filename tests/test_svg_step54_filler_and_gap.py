from vsa.config import SVGRenderingConfig
from vsa.parser import Parser
from vsa.scope_layout import build_scope_layout
from vsa.scope_spacing import (
    collision_optical_gap,
    leading_ink_clearance,
    trailing_ink_clearance,
)
from vsa.svg_renderer import SVGRenderer


def test_filler_line_uses_text_dash_height_not_upper_glyph_height():
    document = Parser(r"{/&/&/&/schon}").parse()
    svg = SVGRenderer().render_document(document)

    assert "vsa-filler-line" in svg
    assert 'y1="30.00"' in svg


def test_optical_scope_gap_is_configurable_default():
    assert SVGRenderingConfig().optical_scope_gap == 4.0


def test_adjacent_modified_scopes_keep_ink_clearance():
    """mede-eeuwige style pair: clearance + injected gap ≥ configured minimum (D)."""
    renderer = SVGRenderer()
    de = Parser(r"{\\de}").parse().nodes[0]
    eeu = Parser(r"{/eeu_}").parse().nodes[0]
    gap = collision_optical_gap(
        de,
        eeu,
        glyphs=renderer.glyphs,
        font_size=renderer.font_size,
        font_family=renderer.font_family,
        configured_gap=renderer.optical_scope_gap,
        left_leading_safety=False,
        left_trailing_safety=False,
        right_leading_safety=False,
        right_trailing_safety=False,
    )
    left = build_scope_layout(
        de,
        font_family=renderer.font_family,
        leading_safety=False,
        trailing_safety=False,
    )
    right = build_scope_layout(
        eeu,
        font_family=renderer.font_family,
        leading_safety=False,
        trailing_safety=False,
    )
    clearance = trailing_ink_clearance(renderer.glyphs, left) + leading_ink_clearance(
        renderer.glyphs, right
    )
    assert clearance + gap >= renderer.optical_scope_gap - 1e-6

    svg = renderer.render_document(Parser(r"me{\\de}{/eeu_}wi{\ge}").parse())
    assert "de" in svg and "eeu" in svg
