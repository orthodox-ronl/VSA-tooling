from vsa.bracket_directive import (
    BRACKET_DIRECTIVE_END,
    BracketDirective,
    find_bracket_directives,
    is_pitch_marker_directive,
    pitch_marker_bodies,
)


def test_bracket_directive_end_token_is_single_contract_value():
    assert BRACKET_DIRECTIVE_END == ":]"


def test_finds_single_pitch_marker_directive():
    directives = find_bracket_directives("[:] Heer")

    assert directives == [
        BracketDirective(start=0, end=3, body="", kind="pitch_marker")
    ]


def test_finds_multiple_directives_in_order():
    directives = find_bracket_directives("voor [:] midden [\\:] na")

    assert [item.body for item in directives] == ["", "\\"]
    assert directives[0].source == "[:]"
    assert directives[1].source == "[\\:]"


def test_text_before_first_marker_is_allowed_by_scanner():
    directives = find_bracket_directives("Heer, [:] ontferm U.")

    assert [item.body for item in directives] == [""]


def test_missing_end_token_is_not_a_directive():
    assert find_bracket_directives("[/] geen marker") == []


def test_ampersand_directive_is_not_pitch_marker():
    directive = find_bracket_directives("[/&\\:]")[0]

    assert directive.body == "/&\\"
    assert not is_pitch_marker_directive(directive)


def test_length_modifier_directive_is_not_pitch_marker():
    directive = find_bracket_directives("[_:]")[0]

    assert directive.body == "_"
    assert not is_pitch_marker_directive(directive)


def test_pitch_marker_bodies_filters_non_pitch_directives():
    bodies = pitch_marker_bodies("[:] [/:] [/&\\:] [_:] [\\:]")

    assert bodies == ["", "/", "\\"]
