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


def test_mvsa_recite_group_does_not_glue_next_word() -> None:
    """``(hei-li-ge) Sterke`` mag niet ``heiligeSterke`` worden."""
    src = """\
@do G4
@mode major

L: (hei-li-ge) Ster~&~&~-ke_. ||
S: f#4          a4&b4&c5  b4   ||
A: d#4          f#4&g4&a4 g4   ||
T: b3           d4&-&-    d4   ||
B: b2           d3&-&-    g3   ||
"""
    text = plain_text_from_mvsa(src)
    assert "heilige Sterke" in text
    assert "heiligeSterke" not in text


def test_vsa_bare_ehm_not_in_plain_text() -> None:
    src = """\
---
do: F4
mode: major
---
God_, // om aan de wereld te schenken
"""
    text = plain_text_from_vsa(src)
    assert "//" not in text
    assert "God" in text
    assert "om aan de wereld" in text


def test_hard_hyphen_equals_becomes_visible_dash() -> None:
    vsa = """\
---
do: F4
mode: major
---
het mede=eeuwige woord
"""
    assert "mede-eeuwige" in plain_text_from_vsa(vsa)

    mvsa = """\
@do F4
@mode major

L: mede=eeu-wi-ge ||
S: do re mi fa ||
A: do re mi fa ||
T: do re mi fa ||
B: do re mi fa ||
"""
    text = plain_text_from_mvsa(mvsa)
    assert "mede-eeuwige" in text
    assert "=" not in text
