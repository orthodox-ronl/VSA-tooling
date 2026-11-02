"""Vorm A: .vsa SVG met translit-regel (kolommetjes)."""

from __future__ import annotations

import re

from vsa.parser import Parser
from vsa.svg_renderer import SVGRenderer


def _viewbox_width(svg: str) -> float:
    m = re.search(r'viewBox="0 0 ([0-9.]+) ', svg)
    assert m is not None
    return float(m.group(1))


def _max_text_x(svg: str) -> float:
    xs = [float(x) for x in re.findall(r'\bx="([0-9.]+)"', svg)]
    assert xs
    return max(xs)


def test_scope_translit_nls_adds_latin_under_cyrillic() -> None:
    doc = Parser(r"{\Свя}").parse()
    svg = SVGRenderer(translit=True, translit_modus="nls").render_document(doc)
    assert "vsa-translit-text" in svg
    assert "Svja" in svg
    assert "Свя" in svg


def test_scope_translit_ksl_modus_skips_cyrillic_source() -> None:
    doc = Parser(r"{\Свя}").parse()
    svg = SVGRenderer(translit=True, translit_modus="ksl").render_document(doc)
    assert "vsa-translit-text" not in svg
    assert "Svja" not in svg


def test_free_text_translit_ksl() -> None:
    doc = Parser("Heer").parse()
    svg = SVGRenderer(translit=True, translit_modus="ksl").render_document(doc)
    assert "vsa-translit-text" in svg
    assert "Хиир" in svg
    assert "Heer" in svg


def test_without_translit_no_second_line() -> None:
    doc = Parser(r"{\Свя}").parse()
    svg = SVGRenderer().render_document(doc)
    assert "vsa-translit-text" not in svg


def test_translit_ksl_viewbox_fits_wider_cyrillic() -> None:
    """Regelmeting gebruikt max(bron, translit); canvas kapte eerder af (vorm A)."""
    # Woorden die in Ksl-translit vaak breder uitvallen dan NL.
    src = (
        "verbazing mochten Leerlingen heerlijkheid "
        "vrijwillig gekruisigd aanschouwen"
    )
    doc = Parser(src).parse()
    svg = SVGRenderer(translit=True, translit_modus="ksl").render_document(doc)
    assert "vsa-translit-text" in svg
    # Ruime marge: glyph-tippen kunnen iets voorbij text-x reiken, maar
    # de oude bug had max-x ~50px voorbij viewBox.
    assert _max_text_x(svg) <= _viewbox_width(svg) + 1.0


def test_translit_ksl_wraps_earlier_than_plain() -> None:
    """Met translit-breedte eerder ombreken dan zonder."""
    src = (
        "verbazing mochten Leerlingen heerlijkheid "
        "vrijwillig gekruisigd aanschouwen Verkondiging"
    )
    doc = Parser(src).parse()
    plain = SVGRenderer().render_document(doc)
    translit = SVGRenderer(translit=True, translit_modus="ksl").render_document(doc)
    plain_lines = len(re.findall(r'data-vsa-line="', plain))
    translit_lines = len(re.findall(r'data-vsa-line="', translit))
    assert translit_lines >= plain_lines
    assert _max_text_x(translit) <= _viewbox_width(translit) + 1.0
