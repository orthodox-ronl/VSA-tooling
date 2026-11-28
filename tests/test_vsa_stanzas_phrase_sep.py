"""Frasescheiding `*` / `/` / `**` / `//` in platte VSA-tekst."""

from __future__ import annotations

from vsa.text_export import _stanza_to_plain
from vsa.vsa_stanzas import extract_stanza_notes


def _plain_stanzas(body: str) -> list[str]:
    src = "---\ndo: F4\nmode: major\n---\n\n" + body
    return [_stanza_to_plain(s) for s in extract_stanza_notes(src)]


def test_star_after_period_without_space_splits_phrase() -> None:
    """``ge{\\richt_}.*`` — ster vastgeplakt aan punt blijft frasescheiding."""
    body = "[:] a ge{\\richt_}.*\nb c [:]"
    plains = _plain_stanzas(body)
    assert len(plains) == 2
    assert plains[0].endswith("gericht.")
    assert plains[1].startswith("b")


def test_slash_after_period_without_space_splits_phrase() -> None:
    body = "[:] a woord./\nb c [:]"
    plains = _plain_stanzas(body)
    assert len(plains) == 2
    assert plains[0].endswith("woord.")


def test_star_with_space_still_splits() -> None:
    body = "[:] a ge{\\richt_}. *\nb c [:]"
    plains = _plain_stanzas(body)
    assert len(plains) == 2


def test_double_star_glued_to_punct() -> None:
    body = "[:] a zin.,**\nb slot [:]"
    plains = _plain_stanzas(body)
    assert len(plains) == 2
