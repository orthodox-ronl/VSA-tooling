"""Padresolutie voor de syllable-dictionary."""

from pathlib import Path

from vsa.syllable_dictionary import (
    clear_syllable_dictionary_cache,
    dictionary_file_path,
    load_syllable_dictionary,
    resolve_syllable_dictionary_path,
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
