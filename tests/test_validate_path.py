from pathlib import Path

from vsa.validation_runner import validate_path


def test_validate_path_accepts_file(tmp_path: Path):
    file = tmp_path / "valid.vsa"
    file.write_text("{tekst}", encoding="utf-8")

    result = validate_path(file)

    assert result.ok


def test_validate_path_accepts_directory(tmp_path: Path):
    content = tmp_path / "content"
    content.mkdir()

    (content / "valid-1.vsa").write_text("{tekst}", encoding="utf-8")
    (content / "valid-2.md").write_text(
        """::: vsa-notatie
{woord}
:::
""",
        encoding="utf-8",
    )

    result = validate_path(content)

    assert result.ok


def test_validate_path_directory_collects_multiple_errors(tmp_path: Path):
    content = tmp_path / "content"
    content.mkdir()

    (content / "invalid-1.vsa").write_text(r"{/&\tekst_}", encoding="utf-8")
    (content / "invalid-2.md").write_text(
        r"""::: vsa-notatie
{/&\woord_}
:::
""",
        encoding="utf-8",
    )

    result = validate_path(content)

    assert not result.ok

    codes = [message.code for message in result.messages]

    assert codes.count("VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH") == 2


def test_validate_path_not_found():
    result = validate_path("niet-bestaand-pad")

    assert not result.ok
    assert result.messages[0].code == "VSA-PATH-NOT-FOUND"


def test_validate_path_rejects_mvsa(tmp_path: Path):
    path = tmp_path / "lied.mvsa"
    path.write_text('@title "x"\n@do F4\n@sectie a\nL: (hallo) |\nS: g |\n', encoding="utf-8")
    result = validate_path(path)
    assert not result.ok
    assert any(m.code == "VSA-WRONG-FILE-TYPE" for m in result.messages)
