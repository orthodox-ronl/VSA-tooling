"""Tests for ``vsa syllabify`` (Pyphen nl_NL on TextNode content)."""

from pathlib import Path

import pytest

from vsa.cli import main
from vsa.syllabify import (
    hyphenate_dutch_word,
    iter_vsa_files,
    normalize_output_extension,
    output_path_for,
    pyphen_hyphenate_core,
    syllabify_plain_text,
    syllabify_vsa_source,
    unsyllabify_plain_text,
    unsyllabify_vsa_source,
)


@pytest.fixture
def tty_syllabify(monkeypatch):
    import vsa.syllable_dict_check as sdc

    monkeypatch.setattr(sdc, "is_interactive_stdin", lambda: True)


def test_hyphenate_dutch_examples() -> None:
    assert hyphenate_dutch_word("lijden") == "lij-den"
    assert hyphenate_dutch_word("onbederfelijke") == "on-be-der-fe-lij-ke"
    assert hyphenate_dutch_word("machteloze") == "mach-te-lo-ze"
    assert hyphenate_dutch_word("marte") == "marte"
    assert pyphen_hyphenate_core("marte") == "mar-te"
    assert hyphenate_dutch_word("Gij") == "Gij"
    assert hyphenate_dutch_word("al-len") == "al-len"


def test_hyphenate_strips_trailing_punctuation() -> None:
    """Leestekens mogen Pyphen niet in de kern lokken (Coria/recite-expansie)."""
    assert hyphenate_dutch_word("Geest,") == "Geest,"
    assert hyphenate_dutch_word("Geest.") == "Geest."
    assert hyphenate_dutch_word("komst,") == "komst,"
    assert hyphenate_dutch_word("Heilige!") == "Hei-li-ge!"


def test_hard_hyphen_equals_preserved_through_syllabify() -> None:
    assert hyphenate_dutch_word("mede=eeuwige") == "me-de=eeu-wi-ge"
    assert unsyllabify_plain_text("me-de=eeu-wi-ge") == "mede=eeuwige"
    from vsa.syllabify import dehyphenate_dutch_word, display_lyric_text

    assert dehyphenate_dutch_word("me-de=eeu-wi-ge") == "mede-eeuwige"
    assert display_lyric_text("me-de=eeu-wi-ge") == "me-de-eeu-wi-ge"
    assert display_lyric_text("me-de=eeu-wi-ge", strip_soft=True) == "mede-eeuwige"
    assert display_lyric_text("hei-lig", strip_soft=True) == "heilig"
    assert display_lyric_text("e-nig=ge-boren", strip_soft=True) == "enig-geboren"


def test_plain_text_preserves_barlines_and_punct() -> None:
    assert syllabify_plain_text("lijden / gebeden") == "lij-den / ge-be-den"
    assert syllabify_plain_text("komst,") == "komst,"


def test_unsyllabify_plain_text() -> None:
    assert unsyllabify_plain_text("lij-den / ge-be-den") == "lijden / gebeden"
    assert unsyllabify_plain_text("on-be-der-fe-lij-ke") == "onbederfelijke"


def test_scopes_and_frontmatter_untouched(tty_syllabify) -> None:
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
    assert "-{la_}" not in result.text
    assert "}{-" not in result.text and "}-{" not in result.text
    assert "lij-den" in result.text
    assert "on-be-der-fe-lij-ke" in result.text
    assert "mach-te-lo-ze" in result.text
    assert result.text.startswith("---\nidentificatie:")


def test_no_hyphen_at_scope_boundaries(tty_syllabify) -> None:
    """Scope-accolade = lettergreepgrens: geen soft ``-`` ernaast."""
    source = "Voorloper van de Verlosser Jo{+\\han_}{/nes_}\n"
    result = syllabify_vsa_source(source)
    assert (
        result.text
        == "Voor-lo-per van de Ver-los-ser Jo{+\\han_}{/nes_}\n"
    )
    assert "-{" not in result.text
    assert "}-" not in result.text
    back = unsyllabify_vsa_source(result.text)
    assert back.text == source


def test_scope_claims_one_syllable_schepping(tty_syllabify) -> None:
    """Letters herverdeeld: scope = één lettergreep, rest in platte tekst."""
    source = "{/toen} de {/sche_}pping zag\n"
    result = syllabify_vsa_source(source)
    assert "{/schep_}ping" in result.text
    assert "{/sche_}" not in result.text
    assert "p-ping" not in result.text
    assert "-{" not in result.text
    assert "}-" not in result.text


def test_scope_claims_one_syllable_adam(tty_syllabify) -> None:
    """Meersyllabige scope-inhoud → eerste lettergreep in scope, rest erna."""
    source = "{/Adam} juicht\n"
    result = syllabify_vsa_source(source)
    assert "{/A}dam" in result.text
    assert "{/Adam}" not in result.text
    assert "-{" not in result.text
    assert "}-" not in result.text


def test_scope_redistribution_keeps_trailing_punctuation(tty_syllabify) -> None:
    """Leestekens rond scopes blijven staan (geen VSA-syntax)."""
    assert syllabify_vsa_source("{/Adam},\n").text == "{/A}dam,\n"
    assert (
        syllabify_vsa_source("Jo{+\\han_}{/nes_}.\n").text
        == "Jo{+\\han_}{/nes_}.\n"
    )
    assert (
        syllabify_vsa_source("marte{la_}{/ren}!\n").text
        == "mar-te{la_}{/ren}!\n"
    )
    assert syllabify_vsa_source("{/sche_}pping.\n").text == "{/schep_}ping.\n"
    assert syllabify_vsa_source("lijden,\n").text == "lij-den,\n"
    # Komma vastgeplakt vóór een scope mag niet verdwijnen.
    assert syllabify_vsa_source("zie,{/daar}\n").text == "zie,{/daar}\n"
    assert syllabify_vsa_source("o Chris{/tus},\n").text == "o Chris{/tus},\n"


def test_unsyllabify_removes_legacy_junction_hyphens() -> None:
    source = "lij-den mar-te-{la_}-{/ren} Al-&-\n"
    result = unsyllabify_vsa_source(source)
    assert result.text == "lijden marte{la_}{/ren} Al-&-\n"


def test_unsyllabify_leaves_scope_elms() -> None:
    source = "lij-den mar-te-{la_}-{/ren} Al-&-\n"
    result = unsyllabify_vsa_source(source)
    assert "lijden" in result.text
    assert "marte{la_}{/ren}" in result.text
    assert "Al-&-" in result.text


def test_syllabify_strips_legacy_junction_hyphens() -> None:
    source = "ver-{/&\\heer}-{\\lijkt} Chris-{/tus} {/stra_}-{len_}\n"
    result = syllabify_vsa_source(source)
    assert "ver{/&\\heer}{\\lijkt}" in result.text
    assert "Chris{/tus}" in result.text
    assert "{/stra_}{len_}" in result.text or "stra" in result.text
    assert "-{" not in result.text
    assert "}-{" not in result.text


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


def test_cli_default_writes_in_place(tmp_path: Path, capsys) -> None:
    path = tmp_path / "voorbeeld.vsa"
    path.write_text("lijden\n", encoding="utf-8")
    assert main(["syllabify", str(path)]) == 0
    assert path.read_text(encoding="utf-8") == "lij-den\n"
    out = capsys.readouterr()
    assert "syllabify: 1 bestand" in out.out
    assert "streepjes toegevoegd" in out.out
    assert str(path) not in out.out  # per-file alleen met --verbose


def test_cli_in_place(tmp_path: Path, capsys) -> None:
    path = tmp_path / "voorbeeld.vsa"
    path.write_text("lijden\n", encoding="utf-8")
    assert main(["syllabify", str(path), "--in-place", "--verbose"]) == 0
    assert path.read_text(encoding="utf-8") == "lij-den\n"
    out = capsys.readouterr()
    assert "lettergreepstreepje" in out.out
    assert path.as_posix() in out.out


def test_cli_extension_writes_sibling(tmp_path: Path) -> None:
    path = tmp_path / "xyz.vsa"
    path.write_text("eeuwig\n", encoding="utf-8")
    assert main(["syllabify", str(path), "--extension", ".syl.vsa"]) == 0
    sibling = tmp_path / "xyz.syl.vsa"
    assert sibling.read_text(encoding="utf-8") == "eeu-wig\n"
    assert path.read_text(encoding="utf-8") == "eeuwig\n"


def test_cli_extension_syl_without_dot(tmp_path: Path) -> None:
    path = tmp_path / "xyz.vsa"
    path.write_text("eeuwig\n", encoding="utf-8")
    assert main(["syllabify", str(path), "--extension", "syl.vsa"]) == 0
    assert (tmp_path / "xyz.syl.vsa").read_text(encoding="utf-8") == "eeu-wig\n"


def test_cli_directory_in_place(tmp_path: Path, capsys) -> None:
    (tmp_path / "a.vsa").write_text("eeuwig\n", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.vsa").write_text("apostel\n", encoding="utf-8")
    assert main(["syllabify", str(tmp_path), "--in-place"]) == 0
    assert (tmp_path / "a.vsa").read_text(encoding="utf-8") == "eeu-wig\n"
    assert (sub / "b.vsa").read_text(encoding="utf-8") == "a-pos-tel\n"
    out = capsys.readouterr().out
    assert "syllabify: 2 bestand" in out
    assert "a.vsa" not in out  # zonder --verbose geen per-file
    assert main(["syllabify", str(tmp_path), "--verbose"]) == 0
    verbose_out = capsys.readouterr().out
    assert "a.vsa" in verbose_out
    assert "b.vsa" in verbose_out


def test_cli_unsyllabify_in_place(tmp_path: Path) -> None:
    path = tmp_path / "voorbeeld.vsa"
    path.write_text("eeu-wig a-pos-tel-{la_}\n", encoding="utf-8")
    assert main(["syllabify", str(path), "--unsyllabify", "--in-place"]) == 0
    assert path.read_text(encoding="utf-8") == "eeuwig apostel{la_}\n"


def test_syllabify_leaves_unknown_word_without_tty(monkeypatch) -> None:
    import vsa.syllable_dict_check as sdc

    monkeypatch.setattr(sdc, "is_interactive_stdin", lambda: False)
    result = syllabify_vsa_source("xyzonbekendwoord\n")
    assert result.text == "xyzonbekendwoord\n"
    assert not result.changed


def test_plus_forms_stay_and_wrong_form_is_corrected() -> None:
    """Plusteken-vormen blijven; een foute vorm wordt de canonieke lijstvorm."""
    source = "al-le-lu-i-a mij-nen-twil or-tho-do-xe eeuwi-ge\n"
    result = syllabify_vsa_source(source)
    assert result.text == "al-le-lu-i-a mij-nen-twil or-tho-do-xe eeu-wi-ge\n"


def test_cli_rejects_in_place_with_extension(tmp_path: Path, capsys) -> None:
    path = tmp_path / "xyz.vsa"
    path.write_text("lijden\n", encoding="utf-8")
    assert main(["syllabify", str(path), "--in-place", "--extension", ".syl.vsa"]) == 1
    err = capsys.readouterr().err
    assert "--in-place" in err and "--extension" in err
