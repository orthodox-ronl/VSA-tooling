from pathlib import Path

from vsa.validation_runner import validate_file, validate_path


def test_validate_valid_vsa_file(tmp_path: Path):
    file = tmp_path / "valid.vsa"
    file.write_text("{tekst}", encoding="utf-8")

    result = validate_file(file)

    assert result.ok
    assert result.messages == []


def test_validate_non_utf8_file_reports_path(tmp_path: Path):
    file = tmp_path / "cp1252.md"
    # 0xd7 = × in Windows-1252; invalid as UTF-8 continuation
    file.write_bytes(b"# Titel\n\n1\xd7 melisma\n")

    result = validate_file(file)

    assert not result.ok
    assert result.messages[0].code == "VSA-ENCODING-ERROR"
    assert result.messages[0].source == str(file)


def test_validate_invalid_vsa_file(tmp_path: Path):
    file = tmp_path / "invalid.vsa"
    file.write_text(r"{/&\tekst_}", encoding="utf-8")

    result = validate_file(file)

    assert not result.ok
    assert result.messages[0].code == "VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH"


def test_validate_valid_markdown_block(tmp_path: Path):
    file = tmp_path / "valid.md"
    file.write_text(
        r"""# Titel

::: vsa-notatie
{tekst}
:::
""",
        encoding="utf-8",
    )

    result = validate_file(file)

    assert result.ok


def test_validate_invalid_markdown_block_reports_file_source(tmp_path: Path):
    file = tmp_path / "invalid.md"
    file.write_text(
        r"""# Titel

::: vsa-notatie
{/&\tekst_}
:::
""",
        encoding="utf-8",
    )

    result = validate_file(file)

    assert not result.ok
    assert result.messages[0].source == str(file)
    assert result.messages[0].line >= 1
