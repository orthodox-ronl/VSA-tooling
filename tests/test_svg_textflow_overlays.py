from vsa.parser import Parser
from vsa.scope_layout import build_scope_layout
from vsa.svg_line_layout import build_lines
from vsa.svg_renderer import SVGRenderer


def test_multi_ehm_scope_creates_filler_space():
    document = Parser(r"{/&\tij_&_}").parse()
    layout = build_scope_layout(document.nodes[0])

    assert layout.filler_width > 0


def test_no_midword_wrapping():
    document = Parser(r"eerstge{/bo_}re{\ne_}").parse()
    lines = build_lines(document, max_width=120)

    assert len(lines) == 1


def test_word_wrapping_allows_break_after_space():
    document = Parser(r"eerste woord tweede").parse()
    lines = build_lines(document, max_width=90)

    assert len(lines) >= 2


def test_plain_scope_sequence_can_wrap():
    document = Parser(" ".join(["{tekst}"] * 20)).parse()
    lines = build_lines(document, max_width=300)

    assert len(lines) > 1


def test_can_wrap_before_final_pitch_marker():
    document = Parser(r"tekst [:]").parse()
    lines = build_lines(document, max_width=55)

    assert len(lines) == 2


def test_scope_spacing_preserves_word_gap_in_svg_text():
    document = Parser(r"grote ge{na_}{\de} {\ge}").parse()
    svg = SVGRenderer().render_document(document)

    assert "grote" in svg
    assert 'xml:space="preserve"' in svg
