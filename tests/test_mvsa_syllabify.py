"""Tests for mvsa syllabify (recite + cadens expand, sync-safe)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vsa.mvsa_syllabify import (
    MvsaSyllabifyError,
    syllabify_mvsa_text,
)
from vsa.mvsa_validate import validate_mvsa_text
from vsa.syllable_dictionary import (
    clear_syllable_dictionary_cache,
    set_syllable_dictionary_path,
)


MINI = Path("examples/mvsa/syllabificatie-recite-mini.mvsa")


def _errors(text: str) -> list[str]:
    return [
        f"{d.code}:{d.message}"
        for d in validate_mvsa_text(text)
        if d.severity == "error"
    ]


def test_syllabify_recite_adds_soft_hyphens(tmp_path: Path):
    dict_file = tmp_path / "dict.txt"
    dict_file.write_text("leer-lin-gen\ntoon-de\n", encoding="utf-8")
    set_syllable_dictionary_path(dict_file)
    clear_syllable_dictionary_cache()
    try:
        src = """\
@title "t"
@do F4
@mode major
@oct S=0

@sectie demo
L: (Leerlingen toonde Gij Uw) heer_ |
S: a4                           -    |
"""
        result = syllabify_mvsa_text(src, align=False)
        assert result.changed
        assert "(Leer-lin-gen toon-de Gij Uw)" in result.text
        assert _errors(result.text) == []
    finally:
        set_syllable_dictionary_path(None)
        clear_syllable_dictionary_cache()


def test_syllabify_cadens_expands_and_pads_stem():
    src = """\
@title "t"
@do F4
@mode major
@oct S=0

@sectie demo
L: heerlijkheid_ |
S: a4_           |
"""
    result = syllabify_mvsa_text(src, align=False)
    assert result.changed
    assert "heer" in result.text
    # Hyphen-keten + holds
    assert "-lijk" in result.text or "lijk" in result.text
    l_line = next(
        ln for ln in result.text.splitlines() if ln.lstrip().startswith("L:")
    )
    s_line = next(
        ln for ln in result.text.splitlines() if ln.lstrip().startswith("S:")
    )
    from vsa.mvsa_align import _l_tokens, _voice_tokens
    from vsa.mvsa_validate import _split_bars

    l_seg = _split_bars(l_line.split(":", 1)[1].lstrip()).segments[0]
    s_seg = _split_bars(s_line.split(":", 1)[1].lstrip()).segments[0]
    assert len(_l_tokens(l_seg)) == len(_voice_tokens(s_seg))
    assert _voice_tokens(s_seg).count("-") >= 1
    assert _errors(result.text) == []


def test_syllabify_idempotent_on_mini_example():
    if not MINI.is_file():
        pytest.skip("example missing")
    text = MINI.read_text(encoding="utf-8")
    assert _errors(text) == []
    result = syllabify_mvsa_text(text, align=True)
    # Al gesyllabificeerd → geen of minimale wijziging; resultaat blijft geldig
    assert _errors(result.text) == []
    again = syllabify_mvsa_text(result.text, align=True)
    assert again.text == result.text


def test_unsyllabify_recite_only():
    src = """\
@title "t"
@do F4
@mode major
@oct S=0

@sectie demo
L: (Leer-lin-gen toon-de) heer_-lijk_ |
S: a4                     -     -     |
"""
    result = syllabify_mvsa_text(src, unsyllabify=True, align=False)
    assert "(Leerlingen toonde)" in result.text
    # Cadens-keten blijft
    assert "heer_" in result.text
    assert "-lijk" in result.text
    assert _errors(result.text) == []


def test_syllabify_rejects_broken_sync():
    src = """\
@title "t"
@do F4
@mode major
@oct S=0

@sectie demo
L: a_ b_ |
S: a4    |
"""
    with pytest.raises(MvsaSyllabifyError):
        syllabify_mvsa_text(src, align=False)
