"""Tests for shared bestand-of-map CLI helper."""

from pathlib import Path

import pytest

from vsa.input_paths import (
    InputPathError,
    collect_cli_sources,
    collect_input_files,
    normalize_suffixes,
)


def test_normalize_suffixes():
    assert normalize_suffixes([".mvsa", "MSCZ"]) == frozenset({".mvsa", ".mscz"})
    with pytest.raises(InputPathError, match="extensie"):
        normalize_suffixes([])


def test_collect_single_file(tmp_path: Path):
    f = tmp_path / "lied.mvsa"
    f.write_text("@title x\n", encoding="utf-8")
    assert collect_input_files(f, suffixes=[".mvsa"]) == [f]


def test_collect_file_wrong_suffix(tmp_path: Path):
    f = tmp_path / "lied.txt"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(InputPathError, match="Verwacht"):
        collect_input_files(f, suffixes=[".mvsa"])


def test_collect_missing_path(tmp_path: Path):
    with pytest.raises(InputPathError, match="niet gevonden"):
        collect_input_files(tmp_path / "geen", suffixes=[".mvsa"])


def test_collect_directory_recursive(tmp_path: Path):
    a = tmp_path / "a.mvsa"
    b = tmp_path / "sub" / "b.mvsa"
    skip = tmp_path / "sub" / "c.mscz"
    b.parent.mkdir()
    a.write_text("a", encoding="utf-8")
    b.write_text("b", encoding="utf-8")
    skip.write_text("c", encoding="utf-8")
    got = collect_input_files(tmp_path, suffixes=[".mvsa", ".mscz"])
    assert got == [a, b, skip]


def test_collect_directory_non_recursive(tmp_path: Path):
    top = tmp_path / "top.mvsa"
    nested = tmp_path / "sub" / "nested.mvsa"
    nested.parent.mkdir()
    top.write_text("t", encoding="utf-8")
    nested.write_text("n", encoding="utf-8")
    assert collect_input_files(
        tmp_path, suffixes=[".mvsa"], recursive=False
    ) == [top]


def test_collect_directory_empty_ok(tmp_path: Path):
    assert collect_input_files(tmp_path, suffixes=[".mvsa"]) == []


def test_collect_cli_sources_empty_dir_raises(tmp_path: Path):
    with pytest.raises(InputPathError, match="Geen passende"):
        collect_cli_sources(tmp_path, suffixes=[".mvsa"])


def test_collect_cli_sources_finds_files(tmp_path: Path):
    a = tmp_path / "a.mvsa"
    a.write_text("@title t\n", encoding="utf-8")
    assert collect_cli_sources(tmp_path, suffixes=[".mvsa"]) == [a]
