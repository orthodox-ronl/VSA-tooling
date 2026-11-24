"""Een maatstreep gevolgd door een Unicode-spatie (bijv. U+2006) is een kale streep."""

from __future__ import annotations

from vsa.mvsa_validate import validate_mvsa_text

HEAD = "@do F4\n@mode major\n\n@sectie demo\n"


def _codes(text: str) -> list[str]:
    return [d.code for d in validate_mvsa_text(text)]


def test_bar_followed_by_thin_space_is_bare() -> None:
    text = HEAD + "L: a_ | b_ ||\nS: a  | b ||\nA: f  | g ||\nT: c  | c ||\nB: f  | f ||\n"
    assert "MVSA-BAR-ANKER" not in _codes(text)


def test_glued_anchor_still_read() -> None:
    text = HEAD + "L: a_ |\nS: a |a\nA: f |f\nT: c |c\nB: f |f\n"
    assert "MVSA-BAR-ANKER" not in _codes(text)
