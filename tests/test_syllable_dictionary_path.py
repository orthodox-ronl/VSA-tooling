"""Padresolutie voor de syllable-dictionary."""

from pathlib import Path

from vsa.syllable_dictionary import (
    apply_syllable_dictionary_from_config,
    clear_syllable_dictionary_cache,
    core_matches_lyrics_lang,
    detect_lyrics_lang_from_cores,
    detect_lyrics_lang_from_text,
    dictionary_basename,
    dictionary_file_path,
    ensure_lyrics_lang_for_cores,
    get_lyrics_lang,
    get_lyrics_lang_mode,
    load_syllable_dictionary,
    resolve_syllable_dictionary_path,
    set_lyrics_lang,
    set_syllable_dictionary_path,
)


def test_resolve_prefers_cli_over_config(tmp_path: Path) -> None:
    cli = tmp_path / "cli.txt"
    cfg = tmp_path / "cfg.txt"
    cli.write_text("cli-vorm\n", encoding="utf-8")
    cfg.write_text("cfg-vorm\n", encoding="utf-8")
    resolved = resolve_syllable_dictionary_path(
        cli_path=cli,
        config_value=str(cfg),
        config_dir=tmp_path,
    )
    assert resolved == cli.resolve()


def test_resolve_config_relative_to_toml_dir(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    target = data / "syllable_dictionary.nl.txt"
    target.write_text("proef-woord\n", encoding="utf-8")
    resolved = resolve_syllable_dictionary_path(
        config_value="data/syllable_dictionary.nl.txt",
        config_dir=tmp_path,
    )
    assert resolved == target.resolve()


def test_resolve_env(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "env-dict.txt"
    target.write_text("env-woord\n", encoding="utf-8")
    resolved = resolve_syllable_dictionary_path(
        environ={"VSA_SYLLABLE_DICTIONARY": str(target)},
    )
    assert resolved == target.resolve()


def test_set_path_loads_that_file(tmp_path: Path) -> None:
    target = tmp_path / "dict.txt"
    target.write_text("los-se-test\n", encoding="utf-8")
    set_syllable_dictionary_path(target)
    clear_syllable_dictionary_cache()
    assert dictionary_file_path() == target.resolve()
    assert load_syllable_dictionary().get("lossetest") == "los-se-test"
    set_syllable_dictionary_path(None)
    clear_syllable_dictionary_cache()


def test_core_matches_lyrics_lang_script_filter() -> None:
    assert core_matches_lyrics_lang("Heer", "nl")
    assert not core_matches_lyrics_lang("Господи", "nl")
    assert core_matches_lyrics_lang("Господи", "ksl")
    assert not core_matches_lyrics_lang("Heer", "ksl")


def test_dictionary_basename_per_lang() -> None:
    assert dictionary_basename("nl") == "syllable_dictionary.nl.txt"
    assert dictionary_basename("ksl") == "syllable_dictionary.ksl.txt"


def test_resolve_ksl_env(tmp_path: Path) -> None:
    target = tmp_path / "ksl.txt"
    target.write_text("# leeg\n", encoding="utf-8")
    resolved = resolve_syllable_dictionary_path(
        lang="ksl",
        environ={"VSA_SYLLABLE_DICTIONARY_KSL": str(target)},
    )
    assert resolved == target.resolve()


def test_resolve_ksl_ignores_nl_config(tmp_path: Path) -> None:
    nl = tmp_path / "syllable_dictionary.nl.txt"
    nl.write_text("a-pos-tel\n", encoding="utf-8")
    resolved = resolve_syllable_dictionary_path(
        config_value=str(nl),
        config_dir=tmp_path,
        lang="ksl",
        environ={},
    )
    assert resolved is None or resolved.name.endswith(".ksl.txt")


def test_apply_lyrics_lang_ksl_loads_empty_file(tmp_path: Path) -> None:
    set_syllable_dictionary_path(None)
    clear_syllable_dictionary_cache()
    ksl = tmp_path / "syllable_dictionary.ksl.txt"
    ksl.write_text("# leeg stub\n", encoding="utf-8")
    apply_syllable_dictionary_from_config(cli_path=ksl, lang="ksl")
    assert get_lyrics_lang() == "ksl"
    assert dictionary_file_path() == ksl.resolve()
    assert load_syllable_dictionary() == {}
    set_lyrics_lang("nl")
    set_syllable_dictionary_path(None)
    clear_syllable_dictionary_cache()


def test_cli_exposes_lyrics_lang() -> None:
    from vsa.cli import _build_mvsa_parser, _build_parser

    vsa = _build_parser()
    mvsa = _build_mvsa_parser()
    assert vsa.parse_args(["validate", "x.vsa"]).lyrics_lang == "auto"
    for args in (
        vsa.parse_args(["validate", "x.vsa", "--lyrics-lang", "ksl"]),
        vsa.parse_args(["syllabify", "x.vsa", "--lyrics-lang", "ksl"]),
        mvsa.parse_args(["validate", "x.mvsa", "--lyrics-lang", "ksl"]),
        mvsa.parse_args(["syllabify", "x.mvsa", "--lyrics-lang", "ksl"]),
    ):
        assert args.lyrics_lang == "ksl"


def test_detect_and_ensure_auto(tmp_path: Path) -> None:
    ksl = tmp_path / "syllable_dictionary.ksl.txt"
    ksl.write_text("# leeg\n", encoding="utf-8")
    nl = tmp_path / "syllable_dictionary.nl.txt"
    nl.write_text("a-pos-tel\n", encoding="utf-8")
    apply_syllable_dictionary_from_config(lang="auto")
    assert get_lyrics_lang_mode() == "auto"
    assert detect_lyrics_lang_from_cores(["Heer", "Licht"]) == "nl"
    assert detect_lyrics_lang_from_cores(["Heer", "Господи"]) == "ksl"
    assert detect_lyrics_lang_from_text("Господи помилуй") == "ksl"
    assert detect_lyrics_lang_from_text("Heer ontferm U") == "nl"

    apply_syllable_dictionary_from_config(cli_path=ksl, lang="auto")
    assert ensure_lyrics_lang_for_cores(["Гос-по-ди"]) == "ksl"
    assert get_lyrics_lang() == "ksl"
    assert dictionary_file_path() == ksl.resolve()

    apply_syllable_dictionary_from_config(cli_path=nl, lang="auto")
    assert ensure_lyrics_lang_for_cores(["a-pos-tel"]) == "nl"
    assert get_lyrics_lang() == "nl"
    set_lyrics_lang("auto")
    set_syllable_dictionary_path(None)
    clear_syllable_dictionary_cache()


def test_auto_mixed_script_uses_per_word_dictionary(tmp_path: Path) -> None:
    from vsa.syllable_dict_check import CODE_UNKNOWN, find_dictionary_syllable_issues_from_cores

    ksl = tmp_path / "syllable_dictionary.ksl.txt"
    ksl.write_text("гос-по-ди\n", encoding="utf-8")
    nl = tmp_path / "syllable_dictionary.nl.txt"
    nl.write_text("a-men\n", encoding="utf-8")
    apply_syllable_dictionary_from_config(lang="auto")
    clear_syllable_dictionary_cache()
    try:
        findings = find_dictionary_syllable_issues_from_cores(
            ["a-men", "xyznlonbekend", "Гос-по-ди"],
            source_text="a-men xyznlonbekend Гос-по-ди\n",
            lyrics_lang="auto",
        )
        by_surface = {f.surface: f for f in findings if f.code == CODE_UNKNOWN}
        assert "xyznlonbekend" in by_surface
        assert "(nl" in by_surface["xyznlonbekend"].message_nl
        assert "Гос-по-ди" not in by_surface
    finally:
        set_syllable_dictionary_path(None)
        clear_syllable_dictionary_cache()
