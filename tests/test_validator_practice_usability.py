from pathlib import Path

from vsa.parser import Parser
from vsa.semantic_validator import SemanticValidator
from vsa.validation_runner import validate_file


def test_empty_final_pitch_marker_is_valid():
    document = Parser(r"[:] {tekst} [:]").parse()

    result = SemanticValidator(document).validate()

    assert result.ok
    assert result.items == []


def test_markdown_validation_reports_real_line_and_useful_column_for_scope_syntax_error(tmp_path: Path):
    path = tmp_path / "demo.md"

    path.write_text(
        """# Demo

::: vsa-notatie
[:] goede regel
{fout/}
:::
""",
        encoding="utf-8",
    )

    result = validate_file(path)

    assert not result.ok

    message = result.messages[0]

    assert message.source == str(path)
    assert message.code == "VSA-SYNTAX-MODIFIER-IN-SUNG-TEXT"
    assert message.line == 5
    assert message.column > 1


def test_free_text_outside_scope_allows_slashes_and_double_slashes(tmp_path: Path):
    path = tmp_path / "demo.md"

    path.write_text(
        r"""::: vsa-notatie
[:] vrije tekst // met slash \\ en ge-wo-ne tekst [:]
:::
""",
        encoding="utf-8",
    )

    result = validate_file(path)

    assert result.ok, [message.message_nl for message in result.messages]


def test_scope_rejects_modifier_character_inside_sung_element_with_specific_code(tmp_path: Path):
    path = tmp_path / "demo.md"

    path.write_text(
        r"""::: vsa-notatie
[:] {fout/} [:]
:::
""",
        encoding="utf-8",
    )

    result = validate_file(path)

    assert not result.ok
    assert result.messages[0].code == "VSA-SYNTAX-MODIFIER-IN-SUNG-TEXT"
    assert "Modifierteken staat binnen de gezongen tekst" in result.messages[0].message_nl
