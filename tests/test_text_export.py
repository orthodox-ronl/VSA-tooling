"""Tests for ``vsa text`` / plain lyric export."""

from vsa.cli import main
from vsa.text_export import plain_text_from_mvsa, plain_text_from_vsa

_ANTIFOON_SNIPPET = """\
---
do: F4
mode: major
---

[:] Juich {/voor} {/God}, ge{\\he}{/le} {/aar__}{\\de_},
   {\\\\&/breng} {/lof} {\\aan} {\\Zijn} {/heer_}lijk{\\heid_}. [:]
"""


def test_vsa_plain_joins_scopes_and_strips_melisma_markup() -> None:
    text = plain_text_from_vsa(_ANTIFOON_SNIPPET)
    assert "Juich voor God" in text
    assert "gehele aarde" in text.replace(",", "")
    assert "{/" not in text
    assert "\\" not in text


def test_vsa_cli_text(tmp_path, capsys) -> None:
    path = tmp_path / "voorbeeld.vsa"
    path.write_text(_ANTIFOON_SNIPPET, encoding="utf-8")
    assert main(["text", str(path)]) == 0
    out = capsys.readouterr().out
    assert "Juich voor God" in out


_MVSA_MINIMAL = """\
@title "Test"
@do F4
@mode major

L: Heilig God, ||
S: do re ||
A: do re ||
T: do re ||
B: do re ||
"""


def test_mvsa_plain_joins_measures() -> None:
    text = plain_text_from_mvsa(_MVSA_MINIMAL)
    assert "Heilig" in text
    assert "God" in text
