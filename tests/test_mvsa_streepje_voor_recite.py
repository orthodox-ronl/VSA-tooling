"""``-(lijkt …)`` (streepje vóór het haakje) = ``(-lijkt …)`` (streepje erin)."""

from __future__ import annotations

from vsa.mvsa_parse import parse_mvsa
from vsa.syllable_dict_check import iter_mvsa_lyric_word_cores_tagged

HEAD = "@do F4\n@mode major\n@tempo 180\n\n@sectie cyclus-1\n"
TAIL = "S: g   /   /   /  |a\nA: e   /   /   /  |f\nT: c   -   -   -  |c\nB: c-  /   /   /  |f\n"


def _doc(l_line: str):
    return parse_mvsa(HEAD + l_line + "\n" + TAIL)


def _positions(doc):
    return [
        lp
        for sec in doc.sections
        for sy in sec.systems
        for m in sy.measures
        for lp in m.lyrics.get("L", [])
    ]


def test_dash_before_paren_continues_word() -> None:
    voor = _positions(_doc("L: (Gij werd ver)-heer~ -(lijkt op de berg)-tus_ |"))
    erin = _positions(_doc("L: (Gij werd ver)-heer~ (-lijkt op de berg)-tus_ |"))
    assert [p.continues_word for p in voor] == [p.continues_word for p in erin]
    assert voor[2].recite and voor[2].continues_word


def test_word_core_across_recite_bridge() -> None:
    cores = dict(
        iter_mvsa_lyric_word_cores_tagged(
            HEAD + "L: (Gij werd ver)-heer~ -(lijkt op de berg)-tus_ |\n" + TAIL
        )
    )
    assert "ver-heer-lijkt" in cores
    assert "ver-heer" not in cores
