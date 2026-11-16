from vsa.parser import Parser
from vsa.scope_layout import build_scope_layout
from vsa.svg_line_layout import build_lines


def test_overlap_case_width_is_driven_by_metrics():
    document = Parser(r"me{\\de}{/eeu_}wi{\ge}").parse()
    lines = build_lines(document, max_width=3000)

    assert len(lines) == 1
    assert lines[0].width > 80


def test_eeu_is_wider_than_de_with_metrics():
    eeu = Parser(r"{/eeu_}").parse().nodes[0]
    de = Parser(r"{\\de}").parse().nodes[0]

    assert build_scope_layout(eeu).width > build_scope_layout(de).width


def test_multi_ehm_still_forces_filler_width():
    node = Parser(r"{/&\tij_&_}").parse().nodes[0]
    layout = build_scope_layout(node)

    assert layout.filler_width > 0
