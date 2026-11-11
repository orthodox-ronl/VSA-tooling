"""CLI-foutvorm: pad + locatie + Hint (error-handling contract)."""

from __future__ import annotations

from pathlib import Path

from vsa.cli_messages import emit_cli_error, format_cli_error
from vsa.cli import main as vsa_main


def test_format_cli_error_path_line_column() -> None:
    text = format_cli_error(
        "Scope zonder sluitaccolade.",
        path="lied.vsa",
        line=3,
        column=1,
        hint="Sluit de { … } af.",
    )
    assert text.startswith("lied.vsa:3:1: Scope zonder sluitaccolade.")
    assert "Hint: Sluit de { … } af." in text


def test_format_cli_error_path_only() -> None:
    text = format_cli_error("Pad niet gevonden.", path="missing.vsa")
    assert text == "missing.vsa: Pad niet gevonden."


def test_format_cli_error_multiline_message_and_hint() -> None:
    text = format_cli_error(
        "hoogte-mismatch op lettergreep 'x'.\nGeen passend slot meer.",
        path="lied.vsa",
        line=10,
        column=4,
        hint="Pas de markeringen aan.\nOf kies --template andere-formule.",
    )
    lines = text.splitlines()
    assert lines[0] == "lied.vsa:10:4: hoogte-mismatch op lettergreep 'x'."
    assert lines[1] == "Geen passend slot meer."
    assert lines[2] == ""
    assert lines[3] == "Hint: Pas de markeringen aan."
    assert lines[4] == "Of kies --template andere-formule."


def test_vsa_mp3_reject_has_path_and_hint(tmp_path: Path, capsys) -> None:
    bron = tmp_path / "lied.mscz"
    bron.write_bytes(b"PK\x03\x04")
    assert vsa_main(["mp3", str(bron)]) == 1
    err = capsys.readouterr().err
    assert "lied.mscz" in err
    assert "weigert .mscz" in err
    assert "Hint:" in err
    assert "mscz mp3" in err


def test_vsa_no_command_has_hint(capsys) -> None:
    assert vsa_main([]) == 1
    err = capsys.readouterr().err
    assert "Geen subcommando" in err
    assert "Hint:" in err
