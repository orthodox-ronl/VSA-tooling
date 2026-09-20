"""Tests for ``vsa syllabify`` (Pyphen nl_NL on TextNode content)."""

from pathlib import Path

from vsa.cli import main
from vsa.syllabify import (
    hyphenate_dutch_word,
    iter_vsa_files,
    normalize_output_extension,
    output_path_for,
    syllabify_plain_text,
    syllabify_vsa_source,
    unsyllabify_plain_text,
    unsyllabify_vsa_source,
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


def test_unsyllabify_plain_text() -> None:
    assert unsyllabify_plain_text("lij-den / ge-be-den") == "lijden / gebeden"
    assert unsyllabify_plain_text("on-be-der-fe-lij-ke") == "onbederfelijke"


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
    assert "mar-te-{la_}-{/ren}" in result.text
    assert "{/heb}-ben" in result.text
    assert "lij-den" in result.text
    assert "on-be-der-fe-lij-ke" in result.text
    assert "mach-te-lo-ze" in result.text
    assert result.text.startswith("---\nidentificatie:")


def test_junction_hyphens_across_scopes() -> None:
    source = "Voorloper van de Verlosser Jo{+\\han_}{/nes_}\n"
    result = syllabify_vsa_source(source)
    assert (
        result.text
        == "Voor-lo-per van de Ver-los-ser Jo-{+\\han_}-{/nes_}\n"
    )
    back = unsyllabify_vsa_source(result.text)
    assert back.text == source


def test_unsyllabify_removes_junction_hyphens() -> None:
    source = "lij-den mar-te-{la_}-{/ren} Al-&-\n"
    result = unsyllabify_vsa_source(source)
    assert result.text == "lijden marte{la_}{/ren} Al-&-\n"


def test_unsyllabify_leaves_scope_elms() -> None:
    source = "lij-den mar-te-{la_}-{/ren} Al-&-\n"
    result = unsyllabify_vsa_source(source)
    assert "lijden" in result.text
    assert "marte{la_}{/ren}" in result.text
    assert "Al-&-" in result.text


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


def test_extension_helpers() -> None:
    assert normalize_output_extension("syl.vsa") == ".syl.vsa"
    assert normalize_output_extension(".syl.vsa") == ".syl.vsa"
    path = Path("zang/xyz.vsa")
    assert output_path_for(path, ".syl.vsa") == Path("zang/xyz.syl.vsa")
    assert output_path_for(path, "syl.vsa") == Path("zang/xyz.syl.vsa")
    assert output_path_for(path, None) == path


def test_iter_vsa_files_directory(tmp_path: Path) -> None:
    (tmp_path / "a.vsa").write_text("a\n", encoding="utf-8")
    nested = tmp_path / "sub"
    nested.mkdir()
    (nested / "b.vsa").write_text("b\n", encoding="utf-8")
    (nested / "c.md").write_text("x\n", encoding="utf-8")
    files = iter_vsa_files(tmp_path)
    assert [p.name for p in files] == ["a.vsa", "b.vsa"]


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


def test_cli_extension_writes_sibling(tmp_path: Path) -> None:
    path = tmp_path / "xyz.vsa"
    path.write_text("lijden\n", encoding="utf-8")
    assert main(["syllabify", str(path), "--extension", ".syl.vsa"]) == 0
    sibling = tmp_path / "xyz.syl.vsa"
    assert sibling.read_text(encoding="utf-8") == "lij-den\n"
    assert path.read_text(encoding="utf-8") == "lijden\n"


def test_cli_extension_syl_without_dot(tmp_path: Path) -> None:
    path = tmp_path / "xyz.vsa"
    path.write_text("lijden\n", encoding="utf-8")
    assert main(["syllabify", str(path), "--extension", "syl.vsa"]) == 0
    assert (tmp_path / "xyz.syl.vsa").read_text(encoding="utf-8") == "lij-den\n"


def test_cli_directory_in_place(tmp_path: Path, capsys) -> None:
    (tmp_path / "a.vsa").write_text("lijden\n", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.vsa").write_text("marte\n", encoding="utf-8")
    assert main(["syllabify", str(tmp_path), "--in-place"]) == 0
    assert (tmp_path / "a.vsa").read_text(encoding="utf-8") == "lij-den\n"
    assert (sub / "b.vsa").read_text(encoding="utf-8") == "mar-te\n"
    out = capsys.readouterr().out
    assert "a.vsa" in out
    assert "b.vsa" in out


def test_cli_unsyllabify_in_place(tmp_path: Path) -> None:
    path = tmp_path / "voorbeeld.vsa"
    path.write_text("lij-den mar-te-{la_}\n", encoding="utf-8")
    assert main(["syllabify", str(path), "--unsyllabify", "--in-place"]) == 0
    assert path.read_text(encoding="utf-8") == "lijden marte{la_}\n"


def test_cli_rejects_in_place_with_extension(tmp_path: Path, capsys) -> None:
    path = tmp_path / "xyz.vsa"
    path.write_text("lijden\n", encoding="utf-8")
    assert main(["syllabify", str(path), "--in-place", "--extension", ".syl.vsa"]) == 1
    err = capsys.readouterr().err
    assert "--in-place" in err and "--extension" in err
