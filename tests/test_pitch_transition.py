"""Stille toonhoogte-overgang ``[<oud>:<nieuw>]``."""

from __future__ import annotations

from vsa.ast import PitchMarkerNode, PitchTransitionNode, ScopeNode, TextNode
from vsa.bracket_directive import (
    BracketDirective,
    find_bracket_directives,
    is_pitch_marker_directive,
    is_pitch_transition_directive,
    split_pitch_transition_body,
)
from vsa.bracket_token_stream import bracket_token_stream
from vsa.parser import Parser
from vsa.semantic_validator import SemanticValidator
from vsa.svg_line_layout import build_lines, iter_layout_nodes
from vsa.svg_renderer import SVGRenderer


def test_split_distinguishes_marker_from_transition():
    assert split_pitch_transition_body("//:/") == ("//", "/")
    assert split_pitch_transition_body("/://") == ("/", "//")
    assert split_pitch_transition_body(":/") == ("", "/")
    assert split_pitch_transition_body("//") is None
    assert split_pitch_transition_body("//:") is None


def test_scanner_finds_transition_without_breaking_markers():
    text = "[//:] einde\n[//:/]\n[/:] start"
    directives = find_bracket_directives(text)

    assert [d.kind for d in directives] == [
        "pitch_marker",
        "pitch_transition",
        "pitch_marker",
    ]
    assert [d.body for d in directives] == ["//", "//:/", "/"]
    assert directives[1].source == "[//:/]"
    assert is_pitch_transition_directive(directives[1])
    assert is_pitch_marker_directive(directives[0])
    assert not is_pitch_transition_directive(directives[0])


def test_scanner_keeps_ordinary_markers_unchanged():
    assert find_bracket_directives("[/:]") == [
        BracketDirective(start=0, end=4, body="/", kind="pitch_marker")
    ]
    assert find_bracket_directives("[//:]") == [
        BracketDirective(start=0, end=5, body="//", kind="pitch_marker")
    ]


def test_token_stream_emits_pitch_transition_kind():
    tokens = bracket_token_stream("a [//:/] b")
    assert [t.kind for t in tokens] == ["text", "pitch_transition", "text"]
    assert tokens[1].value == "//:/"


def test_parser_parses_transition_node():
    doc = Parser("[//:] x [//:/] [/:] y [/:]").parse()
    types = [type(n).__name__ for n in doc.nodes]
    assert "PitchTransitionNode" in types

    transition = next(n for n in doc.nodes if isinstance(n, PitchTransitionNode))
    assert transition.from_ehm == ["//"]
    assert transition.to_ehm == ["/"]
    assert transition.to_dict()["type"] == "PitchTransitionNode"


def test_parser_keeps_marker_when_body_ends_with_colon():
    doc = Parser("[/:] tekst [/:]").parse()
    assert all(not isinstance(n, PitchTransitionNode) for n in doc.nodes)
    markers = [n for n in doc.nodes if isinstance(n, PitchMarkerNode)]
    assert [m.ehm for m in markers] == [["/"], ["/"]]


def test_parser_accepts_empty_old_side():
    doc = Parser("[:/] [/:]").parse()
    transition = doc.nodes[0]
    assert isinstance(transition, PitchTransitionNode)
    assert transition.from_ehm == []
    assert transition.to_ehm == ["/"]


def test_semantic_antifoon_tropaar_chain_without_fake_descent():
    # Antifoon eindigt op //; stille overgang naar /; tropaar start met Gij
    # zonder dalende scope op het eerste woord.
    text = (
        "[//:] Uw barmhartigheden, wil ik zingen. [//:]\n"
        "[//:/]\n"
        "[/:] Gij werd verheerlijkt. [/:]"
    )
    doc = Parser(text).parse()
    result = SemanticValidator(doc, source_text=text).validate()
    codes = [d.code for d in result.diagnostics]
    assert "VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH" not in codes
    assert "VSA-SEMANTIC-PITCH-TRANSITION-MISMATCH" not in codes
    assert result.ok

    gij_text = next(
        n for n in doc.nodes if isinstance(n, TextNode) and "Gij" in n.text
    )
    assert gij_text.text.lstrip().startswith("Gij")
    # Geen scope die Gij kunstmatig laat dalen.
    assert not any(
        isinstance(n, ScopeNode) and n.text.startswith("Gij") for n in doc.nodes
    )


def test_semantic_wrong_old_side_reports_transition_mismatch():
    text = "[/:] tekst [/:]\n[//:/]\n[/:] verder [/:]"
    doc = Parser(text).parse()
    result = SemanticValidator(doc, source_text=text).validate()
    codes = [d.code for d in result.diagnostics]
    assert "VSA-SEMANTIC-PITCH-TRANSITION-MISMATCH" in codes


def test_transition_not_in_svg_output():
    text = "[//:] Heer [//:]\n[//:/]\n[/:] Gij God [/:]"
    doc = Parser(text).parse()
    svg = SVGRenderer().render_document(doc)
    assert "[//:/]" not in svg
    assert "PitchTransition" not in svg
    # Gewone markeringen blijven zichtbaar als pitch-marker units.
    assert "vsa-pitch-marker" in svg

    layout_types = [type(n).__name__ for n in iter_layout_nodes(doc)]
    assert "PitchTransitionNode" not in layout_types

    lines = build_lines(doc)
    for line in lines:
        for item in line.items:
            assert not isinstance(item.node, PitchTransitionNode)


def test_musicxml_cursor_jumps_on_transition():
    from vsa.musicxml_renderer import MusicXMLRenderer

    # Scopes zonder EHM: pitch volgt de cursor (// → E, na overgang / → D).
    text = "[//:] {Aa_} [//:]\n[//:/]\n[/:] {Bb_} [/:]"
    doc = Parser(text).parse()
    assert SemanticValidator(doc, source_text=text).validate().ok
    xml = MusicXMLRenderer(
        metadata={"do": "C4", "mode": "major", "tempo": "120"}
    ).render(doc)
    # Zonder overgang zou Bb nog op E (degree 2) klinken; met [//:/]
    # springt de cursor naar D (degree 1).
    assert "<step>D</step>" in xml
    assert "<step>E</step>" in xml  # Aa op de antifoon-hoogte
