import re

from vsa.parser import Parser
from vsa.svg_renderer import SVGRenderer


def _svg_text_contents(svg: str) -> list[str]:
    return re.findall(r"<text[^>]*>([^<]*)</text>", svg)


def test_svg_renderer_keeps_text_nodes():
    document = Parser("[:] {/Hei_}{/lig_} is de Heer. [:]").parse()

    svg = SVGRenderer().render_document(document)

    assert svg.startswith("<svg")
    assert "</svg>" in svg
    assert "Hei" in svg
    assert "lig" in svg
    assert "is" in svg
    assert "de" in svg
    assert "Heer" in svg


def test_svg_renderer_strips_soft_hyphens_in_lyrics():
    """Standaard .vsa.svg: soft - weg; hard = blijft zichtbaar streepje."""
    document = Parser("ge-wo-ne mede=eeuwige e-nig=ge-boren tekst").parse()

    texts = _svg_text_contents(SVGRenderer().render_document(document))

    assert "gewone" in texts
    assert "mede-eeuwige" in texts
    assert "enig-geboren" in texts
    assert "tekst" in texts
    assert not any("ge-wo-ne" in t for t in texts)
    assert not any("e-nig=ge-boren" in t for t in texts)
    assert not any("=" in t for t in texts)


def test_svg_renderer_translit_keeps_soft_hyphens():
    document = Parser("ge-wo-ne tekst").parse()

    texts = _svg_text_contents(
        SVGRenderer(translit=True, translit_modus="nls").render_document(document)
    )

    assert any("ge-wo-ne" in t for t in texts)


def test_svg_renderer_does_not_use_debug_circles():
    document = Parser("{/tekst_}").parse()

    svg = SVGRenderer().render_document(document)

    assert "<circle" not in svg
    assert "tekst" in svg
    assert "<line" in svg


def test_svg_renderer_pitch_marker_line():
    document = Parser("[:] {tekst} [:]").parse()

    svg = SVGRenderer().render_document(document)

    assert svg.count("<line") == 2
