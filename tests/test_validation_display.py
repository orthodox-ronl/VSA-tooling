from pathlib import Path

from vsa.cli import main
from vsa.height_markers import height_marker_mismatch_detail
from vsa.validation_display import (
    format_validation_message,
    validation_detail_headline,
    validation_location_label,
    validation_short_message,
)
from vsa.validation_runner import ValidationMessage


def _message(**kwargs) -> ValidationMessage:
    return ValidationMessage(**kwargs)


def test_height_marker_mismatch_detail_positive_delta():
    assert height_marker_mismatch_detail(0.0, 2.0) == "computed = marker + 2"


def test_height_marker_mismatch_detail_negative_delta():
    assert height_marker_mismatch_detail(0.0, -1.0) == "computed = marker - 1"


def test_validation_location_label_relative_under_cwd(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    nested = tmp_path / "content" / "demo.md"
    nested.parent.mkdir()
    nested.write_text("x", encoding="utf-8")

    message = _message(
        source=str(nested.resolve()),
        code="VSA-PARSE-ERROR",
        message_nl="fout",
        line=3,
        column=4,
    )
    assert validation_location_label(message) == "content/demo.md:3:4"


def test_validation_location_label_keeps_relative_source():
    message = _message(
        source="content-source/demo.md",
        code="VSA-PARSE-ERROR",
        message_nl="fout",
        line=1,
        column=1,
    )
    assert validation_location_label(message) == "content-source/demo.md:1:1"


def test_format_validation_message_default_layout():
    message = _message(
        source="subdir/testm.md",
        code="VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH",
        message_nl="computed = marker - 1",
        line=19,
        column=13,
    )

    lines = format_validation_message(
        message,
        source_line="   {tekst} [:]",
    )

    assert lines == [
        "subdir/testm.md:19:13",
        "ERROR: VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH: computed = marker - 1",
        "   {tekst} [:]",
        "            ^",
    ]


def test_format_validation_message_includes_hint_and_doc():
    message = _message(
        source="demo.md",
        code="VSA-INCLUDE-VSA-ERROR",
        message_nl="Include niet gevonden.",
        line=2,
        column=1,
        hint_nl="Controleer @include-vsa id=.",
        doc_url="https://example.test/docs",
    )

    lines = format_validation_message(message)

    assert lines == [
        "demo.md:2:1",
        "ERROR: VSA-INCLUDE-VSA-ERROR: Include-vsa-fout.",
        "Hint: Controleer @include-vsa id=.",
        "Zie: https://example.test/docs",
    ]


def test_format_validation_message_summary_layout():
    message = _message(
        source="subdir/testm.md",
        code="VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH",
        message_nl="computed = marker - 1",
        line=19,
        column=69,
    )

    lines = format_validation_message(message, summary=True)

    assert lines == ["subdir/testm.md:19:69: VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH"]


def test_validation_detail_headline_uses_short_message_for_other_codes():
    message = _message(
        source="demo.md",
        code="VSA-SYNTAX-MODIFIER-IN-SUNG-TEXT",
        message_nl="modifierteken staat binnen de gezongen tekst van een zangelement.",
        line=3,
        column=2,
    )

    assert (
        validation_detail_headline(message)
        == "ERROR: VSA-SYNTAX-MODIFIER-IN-SUNG-TEXT: Modifierteken in gezongen tekst."
    )


def test_cli_validate_default_output(capsys, tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "demo.md"
    path.write_text(
        r"""::: vsa-notatie
[//:] {/noot}{/mies} [:]
:::
""",
        encoding="utf-8",
    )

    exit_code = main(["validate", "demo.md"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "demo.md:2:22" in output
    assert "ERROR: VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH: computed = marker + 4" in output
    assert "declareert hoogte" not in output
    assert "^" in output
    assert "Hint:" in output


def test_cli_validate_summary_output(capsys, tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "demo.md"
    path.write_text(
        r"""::: vsa-notatie
[//:] {/noot}{/mies} [:]
:::
""",
        encoding="utf-8",
    )

    exit_code = main(["validate", "--summary", "demo.md"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert output.strip() == "demo.md:2:22: VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH"
    assert "computed" not in output
    assert "^" not in output
