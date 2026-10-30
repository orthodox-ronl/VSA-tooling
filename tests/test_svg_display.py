from vsa.svg_display import (
    DEFAULT_RELATIVE_SIZE,
    notation_style_attr,
    notation_width_css,
    scale_to_width_value,
    svg_natural_width,
)


def test_default_relative_size():
    assert DEFAULT_RELATIVE_SIZE == 1.25


def test_svg_natural_width():
    assert svg_natural_width('<svg width="248" height="55"></svg>') == 248.0
    assert svg_natural_width("<svg></svg>") is None


def test_scale_to_width_value_percent():
    assert scale_to_width_value("50%", 200.0) == "100px"


def test_notation_width_css_em_default():
    width = notation_width_css(natural_width=250.0, design_font_size=20.0)
    assert width == "calc(12.5 * var(--vsa-size, 1.25) * 1em)"


def test_notation_width_css_size_override():
    width = notation_width_css(
        natural_width=250.0,
        design_font_size=20.0,
        size="1",
    )
    assert width == "calc(12.5 * 1 * 1em)"


def test_notation_width_css_scale_wins():
    width = notation_width_css(
        natural_width=200.0,
        design_font_size=20.0,
        scale="50%",
        size="1.0",
    )
    assert width == "100px"


def test_notation_style_attr():
    attr = notation_style_attr(natural_width=100.0, design_font_size=20.0)
    assert attr.startswith(' style="width: calc(5 * var(--vsa-size, 1.25) * 1em)')
    assert "height: auto" in attr
