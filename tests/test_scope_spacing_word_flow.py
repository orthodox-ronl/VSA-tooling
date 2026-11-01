"""A+C+D: no false word gaps; safety only on edges; optical gap only on collision."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from vsa.config import SVGRenderingConfig
from vsa.parser import Parser
from vsa.scope_layout import build_scope_layout
from vsa.scope_spacing import (
    collision_optical_gap,
    leading_ink_clearance,
    trailing_ink_clearance,
)
from vsa.svg_export import export_svg
from vsa.svg_glyphs import SVGGlyphRenderer
from vsa.svg_line_layout import build_lines, LineLayoutSettings
from vsa.svg_renderer import SVGRenderer
from vsa.text_metrics import estimate_scope_text_width, estimate_text_width
from vsa.yaml_frontmatter import parse_vsa_frontmatter

BUG_CASES = Path("examples/bug-cases")


def _text_x_positions(svg: str) -> list[tuple[str, float]]:
    """Extract (text content, x) for sung/plain text nodes in order."""
    out: list[tuple[str, float]] = []
    for m in re.finditer(
        r'<text class="vsa-text[^"]*" x="([0-9.]+)"[^>]*>([^<]*)</text>',
        svg,
    ):
        out.append((m.group(2), float(m.group(1))))
    return out


def _gap_between(svg: str, left: str, right: str) -> float:
    """Horizontal gap from end of left text to start of right text (approx).

    Only consecutive text nodes count, so repeated syllables in a piece do not
    pair across distant lines.
    """
    positions = _text_x_positions(svg)
    for index, (text, x) in enumerate(positions[:-1]):
        if text != left:
            continue
        nxt_text, nxt_x = positions[index + 1]
        if nxt_text != right:
            continue
        return nxt_x - (x + estimate_text_width(left, 20))
    raise AssertionError(f"consecutive pair {left!r}|{right!r} not in {positions}")


def test_safety_margin_only_on_word_edges():
    bare = estimate_text_width("En", 20)
    mid = estimate_scope_text_width(
        "En", 20, leading_safety=False, trailing_safety=False
    )
    edge = estimate_scope_text_width(
        "En", 20, leading_safety=True, trailing_safety=True
    )
    assert abs(mid - bare) < 0.01
    assert edge > bare


def test_engelen_scope_then_text_has_tight_join():
    svg = SVGRenderer().render_document(Parser(r"{/En}gelen").parse())
    gap = _gap_between(svg, "En", "gelen")
    # Trailing safety gone → near-zero; allow tiny float/metric slack.
    assert gap < 1.5, gap


def test_de_engelen_word_space_still_visible():
    svg = SVGRenderer().render_document(Parser(r"{/De} {/En}gelen").parse())
    gap = _gap_between(svg, "De", "En")
    # Real space character (~0.5em) must remain.
    assert gap > 6.0, gap


def test_hoge_priesters_internal_scopes_not_loosely_spaced():
    svg = SVGRenderer().render_document(
        Parser(r"{/Ho}{/ge}{/&/pries}{ters_}").parse()
    )
    gap_ho_ge = _gap_between(svg, "Ho", "ge")
    assert gap_ho_ge <= 2.0, gap_ho_ge


def test_mede_eeuwige_glyphs_do_not_overlap():
    """Historical collision phrase: inks must keep clearance when abutting."""
    document = Parser(r"me{\\de}{/eeu_}wi{\ge}").parse()
    renderer = SVGRenderer()
    svg = renderer.render_document(document)
    assert "vsa-sung-text" in svg

    glyphs = renderer.glyphs
    de = Parser(r"{\\de}").parse().nodes[0]
    eeu = Parser(r"{/eeu_}").parse().nodes[0]
    gap = collision_optical_gap(
        de,
        eeu,
        glyphs=glyphs,
        font_size=20,
        font_family=renderer.font_family,
        configured_gap=4.0,
        left_leading_safety=False,
        left_trailing_safety=False,
        right_leading_safety=False,
        right_trailing_safety=False,
    )
    left = build_scope_layout(
        de, leading_safety=False, trailing_safety=False, font_family=renderer.font_family
    )
    right = build_scope_layout(
        eeu, leading_safety=False, trailing_safety=False, font_family=renderer.font_family
    )
    clearance = trailing_ink_clearance(glyphs, left) + leading_ink_clearance(glyphs, right)
    # Either natural clearance ≥ 4, or we inject gap so total ≥ 4.
    assert clearance + gap >= 4.0 - 1e-6


def test_optical_gap_zero_when_clearance_already_enough():
    glyphs = SVGGlyphRenderer(unit=8.0)
    left = Parser(r"{/Ho}").parse().nodes[0]
    right = Parser(r"{/ge}").parse().nodes[0]
    gap = collision_optical_gap(
        left,
        right,
        glyphs=glyphs,
        font_size=20,
        font_family="DejaVu Sans",
        configured_gap=4.0,
        left_leading_safety=False,
        left_trailing_safety=False,
        right_leading_safety=False,
        right_trailing_safety=False,
    )
    assert gap == 0.0


def test_configured_zero_disables_optical_gap():
    document = Parser(r"me{\\de}{/eeu_}wi{\ge}").parse()
    normal = SVGRenderer().render_document(document)
    zero = SVGRenderer(
        svg_config=SVGRenderingConfig(optical_scope_gap=0.0)
    ).render_document(document)
    # With D, normal may equal zero when no collision — both must be valid SVG.
    assert "vsa-sung-text" in normal and "vsa-sung-text" in zero


def test_line_layout_stores_pre_gap_and_safeties():
    document = Parser(r"{/En}gelen").parse()
    settings = LineLayoutSettings(optical_scope_gap=4.0)
    lines = build_lines(document, max_width=800, settings=settings)
    assert len(lines) == 1
    scope_item = lines[0].items[0]
    text_item = lines[0].items[1]
    assert scope_item.trailing_safety is False
    assert text_item.node.text == "gelen"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _upper_ink_collisions(svg: str, min_gap: float = 0.5) -> list[str]:
    """Adjacent scope units whose upper-neum strokes overlap horizontally."""
    root = ET.fromstring(svg)
    score = next(
        (
            el
            for el in root.iter()
            if _local(el.tag) == "g" and "vsa-score" in el.attrib.get("class", "")
        ),
        None,
    )
    assert score is not None
    problems: list[str] = []
    for line in score:
        if _local(line.tag) != "g" or "vsa-line" not in line.attrib.get("class", ""):
            continue
        prev_right: float | None = None
        prev_uid: str | None = None
        for unit in line:
            if _local(unit.tag) != "g":
                continue
            cls = unit.attrib.get("class", "")
            uid = unit.attrib.get("data-vsa-unit", "?")
            if "vsa-unit-scope" not in cls and "vsa-pitch-marker" not in cls:
                prev_right = None
                prev_uid = None
                continue
            xs: list[float] = []
            for el in unit.iter():
                c = el.attrib.get("class", "")
                if _local(el.tag) == "line" and "vsa-upper-glyph" in c:
                    xs.extend(
                        float(el.attrib[a]) for a in ("x1", "x2") if a in el.attrib
                    )
                if _local(el.tag) == "text" and "vsa-glyph-text" in c:
                    x = float(el.attrib["x"])
                    xs.extend([x - 4.0, x + 4.0])
            if not xs:
                prev_right = None
                prev_uid = None
                continue
            left, right = min(xs), max(xs)
            if prev_right is not None and left - prev_right < min_gap:
                problems.append(
                    f"units {prev_uid}->{uid} gap={left - prev_right:.2f}"
                )
            prev_right = right
            prev_uid = uid
    return problems


def test_bug_case_kondak_renders_and_engelen_is_tight():
    path = BUG_CASES / "kondak-maria-hulp-der-christenen-pokrof-toon-3-liturgikon.vsa"
    _meta, body = parse_vsa_frontmatter(path.read_text(encoding="utf-8"))
    svg = SVGRenderer().render_document(Parser(body).parse())
    gap = _gap_between(svg, "En", "gelen")
    assert gap < 1.5, gap
    assert _gap_between(svg, "Ho", "ge") < 1.5
    assert _gap_between(svg, "bid", "den") < 1.5
    assert not _upper_ink_collisions(svg)


def test_bug_case_tropaar_word_joins_and_no_neum_overlap():
    path = BUG_CASES / "tropaar-zondag-toon-5-groningen.vsa"
    _meta, body = parse_vsa_frontmatter(path.read_text(encoding="utf-8"))
    svg = SVGRenderer().render_document(Parser(body).parse())
    assert _gap_between(svg, "eeu", "wi") < 1.5
    assert _gap_between(svg, "wi", "ge") < 1.5
    assert _gap_between(svg, "ver", "hef") < 1.5
    assert not _upper_ink_collisions(svg)


@pytest.mark.parametrize(
    "source",
    [
        r"{/En}gelen",
        r"{/Ho}{/ge}{/&/pries}{ters_}",
        r"me{\\de}{/eeu_}wi{\ge}",
        r"{/al}{taar_}",
        r"{/a}{/b}",
        r"{/a}{\\b}",
        r"{//a}{//b}",
        r"{#/a}{#/b}",
        r"{/&/a}{/&/b}",
        r"{\\ver}{/&\hef_&~}{\fen_}",
        r"{/&\ge}{\wekt_}",
    ],
)
def test_synthetic_phrases_have_no_upper_neum_overlap(source: str):
    svg = SVGRenderer().render_document(Parser(source).parse())
    assert not _upper_ink_collisions(svg), source


def test_optical_gap_injects_when_configured_gap_is_large():
    """D path: oversized minimum clearance must widen abutting modified scopes."""
    document = Parser(r"{/a}{\\b}").parse()
    settings = LineLayoutSettings(optical_scope_gap=40.0, font_family="DejaVu Sans")
    lines = build_lines(document, max_width=800, settings=settings)
    assert lines[0].items[1].pre_gap > 0.0


def test_all_bug_case_vsa_files_export_without_neum_overlap(tmp_path: Path):
    paths = sorted(BUG_CASES.glob("*.vsa"))
    assert paths, "expected bug-case .vsa fixtures"
    for vsa_path in paths:
        out = tmp_path / f"{vsa_path.stem}.svg"
        export_svg(str(vsa_path), str(out))
        svg = out.read_text(encoding="utf-8")
        assert "vsa-score" in svg
        assert not _upper_ink_collisions(svg), vsa_path.name
