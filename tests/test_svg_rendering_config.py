from pathlib import Path

from vsa.config import load_config
from vsa.parser import Parser
from vsa.svg_renderer import SVGRenderer


def test_svg_config_loads_nested_values(tmp_path: Path):
    config_file = tmp_path / "vsa.toml"

    config_file.write_text(
        """
[rendering.svg]
font-family = "Noto Serif"
font-size = 24
relative-size = 1.1
line-height = 96
text-gap = 7
scope-gap = 8
pitch-marker-gap = 12

[rendering.svg.glyphs.upper]
color = "blue"
width-factor = 0.5

[rendering.svg.glyphs.lower]
color = "green"
width-factor = 0.75

[rendering.svg.pitch-marker]
width = 30
dash-width-factor = 0.4
""",
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.rendering.svg.font_family == "Noto Serif"
    assert config.rendering.svg.font_size == 24
    assert config.rendering.svg.relative_size == 1.1
    assert config.rendering.svg.upper.color == "blue"
    assert config.rendering.svg.lower.color == "green"
    assert config.rendering.svg.pitch_marker.width == 30


def test_svg_renderer_uses_dom_classes():
    document = Parser(r"[:] {/Hei_} [:]").parse()

    svg = SVGRenderer().render_document(document)

    assert 'class="vsa-svg"' in svg
    assert 'class="vsa-score"' in svg
    assert 'class="vsa-line"' in svg
    assert "vsa-unit" in svg
    assert "vsa-pitch-marker" in svg


def test_pitch_marker_dash_is_compact():
    document = Parser(r"[:]").parse()

    svg = SVGRenderer().render_document(document)

    assert "vsa-pitch-marker-dash" in svg
    assert 'x1="13.50"' in svg
    assert 'x2="22.50"' in svg


def test_svg_renderer_uses_configured_font():
    document = Parser(r"{tekst}").parse()

    from vsa.config import SVGRenderingConfig

    config = SVGRenderingConfig(font_family="Noto Serif", font_size=24)
    svg = SVGRenderer(svg_config=config).render_document(document)

    assert "Noto Serif" in svg
    assert 'font-size="24.00"' in svg
