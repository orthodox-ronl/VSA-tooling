"""Tests for ``vsa syllabify`` (Pyphen nl_NL on TextNode content)."""

from pathlib import Path

from vsa.cli import main
from vsa.syllabify import (
    hyphenate_dutch_word,
    syllabify_plain_text,
    syllabify_vsa_source,
)


def test_hyphenate_dutch_examples() -> None:
    assert hyphenate_dutch_word("lijden") == "lij-den"
    assert hyphenate_dutch_word("onbederfelijke") == "on-be-der-fe-lij-ke"
    assert hyphenate_dutch_word("machteloze") == "mach-te-lo-ze"
    assert hyphenate_dutch_word("marte") == "mar-te"
    assert hyphenate_dutch_word("Gij") == "Gij"
    assert hyphenate_dutch_word("al-len") == "al-len"


def test_plain_text_preserves_barlines_and_punct() -> None:
    assert syllabify_plain_text("lijden / gebeden") == "lij-den / ge-be-den"
    assert syllabify_plain_text("komst,") == "komst,"


def test_scopes_and_frontmatter_untouched() -> None:
    source = (
        "---\n"
        "identificatie:\n"
        "  title: Test\n"
        "---\n"
        "marte{la_}{/ren} lijden onbederfelijke\n"
        "{/heb}ben machteloze\n"
    )
    result = syllabify_vsa_source(source)
    assert result.changed
    assert "marte{la_}{/ren}" not in result.text
    assert "mar-te{la_}{/ren}" in result.text
    assert "{/heb}ben" in result.text
    assert "lij-den" in result.text
    assert "on-be-der-fe-lij-ke" in result.text
    assert "mach-te-lo-ze" in result.text
    assert result.text.startswith("---\nidentificatie:")


def test_existing_hyphens_win() -> None:
    source = "voor-beeld lijden\n"
    result = syllabify_vsa_source(source)
    assert "voor-beeld" in result.text
    assert "lij-den" in result.text


def test_html_comment_preserved() -> None:
    source = "lijden <!-- note --> machteloze\n"
    result = syllabify_vsa_source(source)
    assert "<!-- note -->" in result.text
    assert "lij-den" in result.text
    assert "mach-te-lo-ze" in result.text


def test_cli_dry_run_stdout(tmp_path: Path, capsys) -> None:
    path = tmp_path / "voorbeeld.vsa"
    path.write_text("lijden machteloze\n", encoding="utf-8")
    assert main(["syllabify", str(path), "--dry-run"]) == 0
    out = capsys.readouterr()
    assert "lij-den" in out.out
    assert "mach-te-lo-ze" in out.out
    assert "dry-run" in out.err
    assert path.read_text(encoding="utf-8") == "lijden machteloze\n"


def test_cli_in_place(tmp_path: Path, capsys) -> None:
    path = tmp_path / "voorbeeld.vsa"
    path.write_text("lijden\n", encoding="utf-8")
    assert main(["syllabify", str(path), "--in-place"]) == 0
    assert path.read_text(encoding="utf-8") == "lij-den\n"
    out = capsys.readouterr()
    assert "lettergreepstreepje" in out.out
