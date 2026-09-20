from pathlib import Path

from vsa.validation_display import format_validation_message
from vsa.validation_runner import validate_file


def test_valid_prefix_modifiers_are_not_syntax_errors(tmp_path: Path):
    path = tmp_path / "edge-cases.md"
    path.write_text(
        r"""::: vsa-notatie
{/&\tekst_}
:::
""",
        encoding="utf-8",
    )

    result = validate_file(path)
    assert not result.ok
    assert result.messages[0].code == "VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH"


def test_empty_sung_text_scope_reports_specific_error(tmp_path: Path):
    path = tmp_path / "edge-cases.md"
    path.write_text(
        r"""::: vsa-notatie
[:] tekst
{\\}de wachters
:::
""",
        encoding="utf-8",
    )

    result = validate_file(path)
    message = result.messages[0]
    assert message.code == "VSA-SYNTAX-EMPTY-SUNG-TEXT"
    assert message.line == 3
    assert message.column == 1


def test_invalid_alignment_marker_reports_specific_error(tmp_path: Path):
    path = tmp_path / "edge-cases.md"
    path.write_text(
        r"""::: vsa-notatie
[:] tekst
{&\ken__}.
:::
""",
        encoding="utf-8",
    )

    result = validate_file(path)
    message = result.messages[0]
    assert message.code == "VSA-SYNTAX-INVALID-ALIGNMENT-MARKER"
    assert "`&`" in message.message_nl
    assert message.line == 3
    assert message.column == 2


def test_modifier_in_sung_text_has_specific_error(tmp_path: Path):
    path = tmp_path / "edge-cases.md"
    path.write_text(
        r"""::: vsa-notatie
[:] tekst
{fout/}
:::
""",
        encoding="utf-8",
    )

    result = validate_file(path)
    message = result.messages[0]
    assert message.code == "VSA-SYNTAX-MODIFIER-IN-SUNG-TEXT"
    assert message.line == 3
    assert message.column > 1


def test_halftoon_prefix_after_base_reports_specific_error_and_caret(tmp_path: Path):
    path = tmp_path / "edge-cases.md"
    source_line = r"{\+tekst}"
    path.write_text(
        f"""::: vsa-notatie
[:] tekst
{source_line}
:::
""",
        encoding="utf-8",
    )

    result = validate_file(path)
    message = result.messages[0]

    assert message.code == "VSA-SYNTAX-HALFTOON-PREFIX-AFTER-BASE"
    assert "`+`" in message.message_nl
    assert "vóór het rijtje" in message.message_nl
    assert message.line == 3
    # `{` + `\` + `+` → caret under `+` at column 3
    assert message.column == 3

    lines = format_validation_message(message, source_line=source_line)
    assert source_line in lines
    caret_index = lines.index(source_line) + 1
    assert lines[caret_index] == "  ^"


def test_plain_b_after_base_is_sung_text_not_halftoon_postfix_error(tmp_path: Path):
    path = tmp_path / "edge-cases.md"
    path.write_text(
        r"""::: vsa-notatie
[:] {/blok} [:]
:::
""",
        encoding="utf-8",
    )

    result = validate_file(path)
    assert all(
        message.code != "VSA-SYNTAX-HALFTOON-PREFIX-AFTER-BASE"
        for message in result.messages
    )
