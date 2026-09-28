"""Unit tests for speelplan partituur-navigation matching."""

from __future__ import annotations

from vsa.mvsa_speelplan import (
    match_ds_al_fine,
    match_simple_repeat,
    match_volta_ab_ac,
    plan_partituur_navigation,
)
from vsa.mvsa_parse import parse_mvsa


def test_match_volta_alleluia():
    v = match_volta_ab_ac(["1", "2", "1", "2", "1", "3"], ["1", "2", "3"])
    assert v is not None
    assert v.n == 2
    assert v.first_ending_numbers == "1,2"
    assert v.second_ending_number == "3"


def test_match_ds_trisagion():
    ids = ["nls-1", "nls-2", "ksl", "doxologie"]
    plan = ["nls-1", "nls-2", "ksl", "doxologie", "nls-2", "ksl"]
    ds = match_ds_al_fine(plan, ids)
    assert ds is not None
    assert ds.segno_id == "nls-2"
    assert ds.fine_id == "ksl"
    assert ds.ds_after_id == "doxologie"
    assert ds.use_da_capo is False


def test_match_simple_repeat_with_tail():
    r = match_simple_repeat(["1", "2", "1", "2", "3"], ["1", "2", "3"])
    assert r is not None
    assert r.start_id == "1"
    assert r.end_id == "2"
    assert r.times == 2


def test_plan_prefers_volta_over_repeat():
    doc = parse_mvsa(
        """\
@do F4
@mode major
@speelplan 1, 2, 1, 2, 1, 3
@blok 1
L: a_ |
S: do |
A: do |
T: do |
B: do |
@blok 2
L: b_ |
S: re |
A: re |
T: re |
B: re |
@blok 3
L: c_ ||
S: mi ||
A: mi ||
T: mi ||
B: mi ||
"""
    )
    nav = plan_partituur_navigation(doc)
    assert nav is not None
    assert nav.kind == "volta_ab_ac"


def test_plan_trisagion_ds():
    doc = parse_mvsa(
        """\
@do G4
@mode major
@speelplan nls-1, nls-2, ksl, doxologie, nls-2, ksl
@blok nls-1
L: a_ |
S: do |
A: do |
T: do |
B: do |
@blok nls-2
L: b_ |
S: re |
A: re |
T: re |
B: re |
@blok ksl
L: c_ |
S: mi |
A: mi |
T: mi |
B: mi |
@blok doxologie
L: d_ ||
S: fa ||
A: fa ||
T: fa ||
B: fa ||
"""
    )
    nav = plan_partituur_navigation(doc)
    assert nav is not None
    assert nav.kind == "ds_al_fine"
    assert nav.ds is not None
    assert nav.ds.segno_id == "nls-2"
