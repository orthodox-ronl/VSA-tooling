"""Kolomalign L↔stem: geen wees-``-`` vóór ``(`` (T5 / MVSA-SYNC)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vsa.mvsa_align import _build_aligned_measure, _l_tokens, _voice_tokens, align_mvsa_text
from vsa.mvsa_parse import parse_l_positions, parse_voice_positions
from vsa.mvsa_validate import validate_mvsa_text
from vsa.vsa_mvsa import convert_vsa_to_mvsa

BIB = Path(r"C:\Git\orthodox-ronl\bibliotheek\content-source\catalogus")


def _slot_seqs(l_line: str, s_line: str) -> tuple[list[int], list[int]]:
    lseq = [max(1, len(p.elms)) for p in parse_l_positions(l_line)]
    sseq = [max(1, len(p.slots)) for p in parse_voice_positions(s_line)]
    return lseq, sseq


def test_l_tokens_skips_stray_hyphen_before_paren():
    """``mach_-(ti`` mag geen wees-token ``-`` krijgen (T5)."""
    measure = "(als Al)-mach_-(ti-ge) ver-brij_&~-zeld_,"
    toks = _l_tokens(measure)
    assert "-" not in toks
    assert any("zeld" in t for t in toks)
    assert len(toks) == len(parse_l_positions(measure))


def test_align_hyphen_before_paren_keeps_sync():
    """Align na ``_-(``: L-tokens even lang als parse-L; sync met stem."""
    l = "(als Al)-mach_-(ti-ge) ver-brij_&~-zeld_,"
    lt = _l_tokens(l)
    assert len(lt) == len(parse_l_positions(l))
    assert all(t != "-" for t in lt)
    # Stem: één token per L-positie; melisma-duur op brij via ``/&\\``.
    vt: list[str] = []
    for t in lt:
        if "brij" in t:
            vt.append(r"/&\\")
        else:
            vt.append("g" if not vt else "-")
    lo, vo = _build_aligned_measure(lt, [vt])
    lseq, sseq = _slot_seqs(lo, vo[0])
    assert lseq == sseq, (lseq, sseq, lo, vo[0], lt)


@pytest.mark.parametrize(
    ("rel", "template"),
    [
        (
            "kondak/zondag-toon-5/groningen/kondak-zondag-toon-5-groningen.vsa",
            "kondak-toon-5",
        ),
        (
            "tropaar/zaterdag-heiligen-toon-2/hemelum/"
            "tropaar-zaterdag-heiligen-toon-2-hemelum.vsa",
            "tropaar-toon-2",
        ),
        (
            "kondak/zondag-toon-8/groningen/kondak-zondag-toon-8-groningen.vsa",
            "kondak-toon-8",
        ),
    ],
)
def test_vsa_mvsa_corpus_no_sync_after_align(rel: str, template: str):
    """Regressie: drie bekende SYNC-cases na ``vsa mvsa`` (T5)."""
    src = BIB / rel
    if not src.is_file():
        pytest.skip(f"bibliotheek-bron ontbreekt: {src}")
    result = convert_vsa_to_mvsa(src, template=template, write=False)
    sync = [d for d in validate_mvsa_text(result.text) if d.code == "MVSA-SYNC"]
    assert sync == [], sync


def test_align_text_skips_orphan_hyphen_column():
    """``)-(`` in L: wees-``-`` telt niet mee; stem even lang als echte L-posities."""
    text = """\
@do F4
@mode major
@oct S=0 A=-1 T=-1 B=-1

L: (aa bb)-(cc dd) ee-ff_ |
S: g       /       \\  \\  |g
A: e       /       -  -  |e
T: c       -       \\  \\  |c
B: f       /       -  -  |f
"""
    out = align_mvsa_text(text)
    sync = [d for d in validate_mvsa_text(out) if d.code == "MVSA-SYNC"]
    assert sync == [], (sync, out)
