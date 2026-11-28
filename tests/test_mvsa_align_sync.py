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
            "kondak-toon-5-groningen",
        ),
        (
            "tropaar/zaterdag-heiligen-toon-2/hemelum/"
            "tropaar-zaterdag-heiligen-toon-2-hemelum.vsa",
            "tropaar-toon-2-groningen",
        ),
        (
            "kondak/zondag-toon-8/groningen/kondak-zondag-toon-8-groningen.vsa",
            "kondak-toon-8-groningen",
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


def _ampersand_columns(line: str) -> list[int]:
    """0-based columns of ``&`` after ``X: `` prefix."""
    body = line.split(":", 1)[1]
    if body.startswith(" "):
        body = body[1:]
    return [i for i, ch in enumerate(body) if ch == "&"]


def test_align_ampersand_columns_pad_l_and_voice():
    """L met ``&``: stem-``&`` onder L-``&`` (spaties in slots)."""
    l_toks = ["Heer_&_", "(ik roep)", "hoor_&~"]
    v_row = ["Bb&/", "-", "/&\\"]
    lo, vo = _build_aligned_measure(l_toks, [v_row])
    # Bouw mini-systeemregels om kolommen te vergelijken.
    l_line = f"L: {lo}"
    s_line = f"S: {vo[0]}"
    assert _ampersand_columns(l_line) == _ampersand_columns(s_line), (
        l_line,
        s_line,
    )
    lseq, sseq = _slot_seqs(lo, vo[0])
    assert lseq == sseq, (lseq, sseq, lo, vo[0])


def test_align_mvsa_text_ampersand_columns():
    text = """\
@do F4
@mode major

@sectie demo
L: Heer_&_ (ik) hoor_&~ ||
S: Bb&/    -    /&\\     ||
A: g&/     -    -&-     ||
T: c&-     -    -&-     ||
B: c&/     -    /&\\     ||
"""
    out = align_mvsa_text(text)
    lines = {
        ln[0]: ln
        for ln in out.splitlines()
        if ln[:2] in ("L:", "S:", "A:", "T:", "B:")
    }
    l_amps = _ampersand_columns(lines["L"])
    assert l_amps, out
    for stem in "SATB":
        assert _ampersand_columns(lines[stem]) == l_amps, (stem, out)
    sync = [d for d in validate_mvsa_text(out) if d.code == "MVSA-SYNC"]
    assert sync == [], (sync, out)


def test_parse_voice_allows_spaces_around_ampersand():
    from vsa.mvsa_parse import parse_l_positions, parse_voice_positions

    assert [p.slots for p in parse_voice_positions("Bb  &/ c")] == [
        ["Bb", "/"],
        ["c"],
    ]
    ps = parse_l_positions("Heer_  &_")
    assert len(ps) == 1
    assert ps[0].elms == ["_", "_"]


def test_align_ampersand_after_woordstreepje_not_off_by_one():
    """``wan-neer_&_``: woordstreep-``-`` mag stem-``&`` niet één kolom verschuiven."""
    lt = _l_tokens("wan-neer_&_ ik tot U_&~ roep_")
    assert lt[0] == "wan" and lt[1].startswith("-neer")
    s = ["Bb4", "-&/", "\\", "\\2", "/&\\", "\\"]
    a = ["g4", "-&/", "\\", "\\2", "/&\\", "\\"]
    t = ["c4", "-&-", "-", "-", "-&-", "\\2"]
    b = ["c3", "-&/3", "\\3", "-", "/3&\\3", "/"]
    lo, vo = _build_aligned_measure(lt, [s, a, t, b])
    l_amps = [i for i, ch in enumerate(lo) if ch == "&"]
    for row in vo:
        assert [i for i, ch in enumerate(row) if ch == "&"] == l_amps, (lo, row)
