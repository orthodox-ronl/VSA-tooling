"""Bijsnijden van VSA-SVG tot de getekende inhoud."""

from __future__ import annotations

import re

from vsa.parser import Parser
from vsa.svg_ink_trim import ink_bounds, trim_vsa_svg
from vsa.svg_renderer import SVGRenderer
from vsa.yaml_frontmatter import parse_vsa_frontmatter


def _render(text: str, **cfg) -> str:
    _meta, body = parse_vsa_frontmatter(text)
    renderer = SVGRenderer()
    for key, value in cfg.items():
        setattr(renderer.svg_config, key, value)
    return renderer.render_document(Parser(body).parse())


def _size(svg: str) -> tuple[int, int]:
    m = re.search(r'<svg[^>]*width="(\d+)" height="(\d+)" viewBox="0 0 (\d+) (\d+)"', svg)
    assert m and m.group(1) == m.group(3) and m.group(2) == m.group(4)
    return int(m.group(1)), int(m.group(2))


def test_commentaar_en_lege_regels_boven_de_notatie_geven_geen_witruimte() -> None:
    kaal = _render("Kon-dak {Heer} ik\n")
    met = _render(
        "# een\n# twee\n\n# drie\n<!-- blok\nover meer regels -->\nKon-dak {Heer} ik\n"
    )
    assert _size(met) == _size(kaal)


def test_rand_is_bescheiden() -> None:
    width, height = _size(_render("Kon-dak {Heer} ik\n"))
    assert height <= 34  # één regel: tekst + notatietekens + 2 x 4 rand
    assert width <= 190


def test_inhoud_valt_binnen_de_viewbox() -> None:
    svg = _render("# c\nKon-dak {Heer} ik\n{/e_}ren\n")
    width, height = _size(svg)
    tr = re.search(r'translate\((-?[\d.]+) (-?[\d.]+)\)', svg)
    assert tr
    dx, dy = float(tr.group(1)), float(tr.group(2))
    minx, miny, maxx, maxy = ink_bounds(svg)  # type: ignore[misc]
    assert minx + dx >= 0 and miny + dy >= 0
    assert maxx + dx <= width and maxy + dy <= height


def test_trim_uit_laat_oude_afmeting() -> None:
    svg = _render("# een\n\nKon-dak {Heer} ik\n", trim=False)
    assert "vsa-trim" not in svg


def test_lege_svg_blijft_ongewijzigd() -> None:
    leeg = '<svg width="10" height="10" viewBox="0 0 10 10"></svg>'
    assert trim_vsa_svg(leeg) == leeg
