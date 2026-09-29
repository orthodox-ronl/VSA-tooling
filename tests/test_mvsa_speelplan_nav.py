"""Unit tests for speelplan partituur-navigation matching."""

from __future__ import annotations

from vsa.mvsa_speelplan import (
    match_ds_al_coda,
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


def test_match_ds_al_coda_classic():
    """``1,2,3,2,4`` → Segno@2, To Coda@2, D.S.@3, Coda@4."""
    ids = ["1", "2", "3", "4"]
    plan = ["1", "2", "3", "2", "4"]
    coda = match_ds_al_coda(plan, ids)
    assert coda is not None
    assert coda.segno_id == "2"
    assert coda.to_coda_id == "2"
    assert coda.ds_after_id == "3"
    assert coda.coda_id == "4"
    assert coda.use_da_capo is False


def test_match_dc_al_coda():
    """``intro,mid,bridge,intro,mid,coda`` → D.C. al Coda (niet volta: 4 bladblokken)."""
    ids = ["intro", "mid", "bridge", "coda"]
    plan = ["intro", "mid", "bridge", "intro", "mid", "coda"]
    coda = match_ds_al_coda(plan, ids)
    assert coda is not None
    assert coda.segno_id == "intro"
    assert coda.to_coda_id == "mid"
    assert coda.ds_after_id == "bridge"
    assert coda.coda_id == "coda"
    assert coda.use_da_capo is True
    # Zelfde plan is geen volta (volta eist precies 3 bladblokken).
    assert match_volta_ab_ac(plan, ids) is None


def test_match_ds_al_coda_rejects_fine_shape():
    """Trisagion-vorm is Fine, geen Coda."""
    ids = ["nls-1", "nls-2", "ksl", "doxologie"]
    plan = ["nls-1", "nls-2", "ksl", "doxologie", "nls-2", "ksl"]
    assert match_ds_al_coda(plan, ids) is None
    assert match_ds_al_fine(plan, ids) is not None


def test_match_ds_al_coda_rejects_ambiguous_nested():
    """Onherleidbaar / genest plan → geen Coda-match (expand-vangnet)."""
    ids = ["1", "2", "3"]
    plan = ["1", "3", "2", "1"]
    assert match_ds_al_coda(plan, ids) is None
    assert match_ds_al_fine(plan, ids) is None


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


def test_plan_ds_al_coda():
    doc = parse_mvsa(
        """\
@do F4
@mode major
@speelplan 1, 2, 3, 2, 4
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
L: c_ |
S: mi |
A: mi |
T: mi |
B: mi |
@blok 4
L: d_ ||
S: fa ||
A: fa ||
T: fa ||
B: fa ||
"""
    )
    nav = plan_partituur_navigation(doc)
    assert nav is not None
    assert nav.kind == "ds_al_coda"
    assert nav.coda is not None
    assert nav.coda.segno_id == "2"
    assert nav.coda.to_coda_id == "2"
    assert nav.coda.ds_after_id == "3"
    assert nav.coda.coda_id == "4"


def test_plan_prefers_fine_over_coda():
    """Fine wint op prioriteit; Coda-matcher zou toch None geven."""
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
