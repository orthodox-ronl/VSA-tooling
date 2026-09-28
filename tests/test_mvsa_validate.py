"""Tests for mvsa draft validate (structuur + sync)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vsa.mvsa_validate import (
    _l_position_slots,
    _voice_position_slots,
    parse_regelidentifier,
    validate_mvsa_text,
)

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "mvsa"


def test_l_recite_and_melisma_slots():
    # Recite = ``( … )`` (niet meer leidende ``~``); melisma-slots via ``&``.
    assert _l_position_slots(
        "(Al-le-lu-ia,) (Al-le-lu-ia,) al-le lu_&-&-&_ i_ a__"
    ) == [1, 1, 1, 1, 4, 1, 1]
    assert _l_position_slots("O Hei_.-li~&~-ge God_.&_.") == [1, 1, 2, 1, 2]
    assert _voice_position_slots("f#4 g4 f#4&g4 a4 g4&a4") == [1, 1, 2, 1, 2]


def test_validate_minimal_ok():
    text = """\
@do F4
@mode major

@sectie demo
L: a_ b_ ||
S: do re ||
A: do re ||
T: do re ||
B: do re ||
"""
    assert validate_mvsa_text(text) == []


def test_validate_hash_comment_between_lsatb_ok():
    """``#``-commentaar tussen LSATB-markers van hetzelfde systeem: toegestaan."""
    text = """\
@do F4
@mode major

@sectie demo
L: a_ b_ ||
# stemmen
S: do re ||
A: do re ||
T: do re ||
B: do re ||
"""
    assert validate_mvsa_text(text) == []


def test_validate_blank_line_separates_systems():
    """Lege regel eindigt een LSATB-systeem; daarna mag een nieuw systeem."""
    text = """\
@do F4
@mode major
@sectie demo
L: a_ |
S: do |
A: do |
T: do |
B: do |

L: b_ ||
S: re ||
A: re ||
T: re ||
B: re ||
"""
    diags = validate_mvsa_text(text)
    errors = [d for d in diags if d.severity == "error"]
    assert errors == [], errors
    assert not any(d.code == "MVSA-MARKER-DUP" for d in diags)


def test_validate_blank_line_inside_system_splits():
    """Lege regel midden in L/S/A/T/B breekt het systeem (marker-volgorde)."""
    text = """\
@do F4
@mode major
@sectie demo
L: a_ b_ |

S: do re |
A: do re |
T: do re |
B: do re |

L: c_ ||
S: mi ||
A: mi ||
T: mi ||
B: mi ||
"""
    diags = validate_mvsa_text(text)
    assert any(d.code == "MVSA-MARKERS" for d in diags), diags


def test_validate_sync_mismatch():
    text = """\
@sectie demo
L: a_ b_ c_ ||
S: do re ||
"""
    diags = validate_mvsa_text(text)
    assert any(d.code == "MVSA-SYNC" for d in diags)


def test_validate_unknown_directive():
    text = """\
@voices =:x
@sectie demo
L: a_ ||
S: do ||
"""
    diags = validate_mvsa_text(text)
    unknown = [d for d in diags if d.code == "MVSA-DIRECTIVE"]
    assert unknown, diags
    assert unknown[0].severity == "warning"
    assert "onbekende" in unknown[0].message


def test_validate_invalid_keyword_form_is_warning():
    text = """\
@1foo
@sectie demo
L: a_ ||
S: do ||
"""
    diags = validate_mvsa_text(text)
    errors = [d for d in diags if d.severity == "error"]
    assert errors == [], errors
    assert any(
        d.code == "MVSA-DIRECTIVE"
        and d.severity == "warning"
        and "ongeldige" in d.message
        for d in diags
    )


def test_validate_noop_separator_splits_systems():
    """``@---`` blijft een geldige (optionele) systemscheider naast lege regels."""
    text = """\
@do F4
@mode major
@sectie demo
L: a_ |
S: do |
A: do |
T: do |
B: do |
@---
L: b_ ||
S: re ||
A: re ||
T: re ||
B: re ||
"""
    diags = validate_mvsa_text(text)
    errors = [d for d in diags if d.severity == "error"]
    assert errors == [], errors
    assert not any(d.code == "MVSA-MARKER-DUP" for d in diags)


def test_validate_noop_separator_spaced_form():
    text = """\
@sectie demo
L: a_ |
S: do |
@ ---
L: b_ ||
S: re ||
"""
    diags = validate_mvsa_text(text)
    assert not any(d.code == "MVSA-MARKER-DUP" for d in diags)
    assert not any(d.code == "MVSA-DIRECTIVE" for d in diags)


def test_validate_noop_separator_allows_trailing_comment():
    """``@--- …`` / ``@ --- …``: tekst na de streepjes is commentaar."""
    from vsa.mvsa_validate import is_noop_separator_directive

    assert is_noop_separator_directive("---", "")
    assert is_noop_separator_directive("---", "volgende frase")
    assert is_noop_separator_directive("", "---")
    assert is_noop_separator_directive("", "--- zie blad 2")
    assert not is_noop_separator_directive("", "-- niet drie")
    assert not is_noop_separator_directive("tekst", "---")

    text = """\
@do F4
@mode major
@sectie demo
L: a_ |
S: do |
A: do |
T: do |
B: do |
@--- tweede systeem (commentaar)
L: b_ ||
S: re ||
A: re ||
T: re ||
B: re ||
@ --- ook met spatie vóór ---
L: c_ ||
S: mi ||
A: mi ||
T: mi ||
B: mi ||
"""
    diags = validate_mvsa_text(text)
    errors = [d for d in diags if d.severity == "error"]
    assert errors == [], errors
    assert not any(d.code == "MVSA-MARKER-DUP" for d in diags)
    assert not any(d.code == "MVSA-DIRECTIVE" for d in diags)


def test_validate_tekst_ok_and_bad():
    ok = """\
@do F4
@mode major
@title "(1a) Demo"
@tekst "P: Gezegend … der eeuwen"
@sectie demo
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
"""
    assert validate_mvsa_text(ok) == []

    bad = """\
@tekst zonder-quotes
@sectie demo
L: a_ ||
S: do ||
"""
    diags = validate_mvsa_text(bad)
    assert any(d.code == "MVSA-TEKST" and d.severity == "error" for d in diags)


def test_validate_title_bad():
    text = """\
@title zonder-quotes
@sectie demo
L: a_ ||
S: do ||
"""
    diags = validate_mvsa_text(text)
    assert any(d.code == "MVSA-META" and d.severity == "error" for d in diags)


def test_validate_tekst_orphan_warning():
    text = """\
@sectie demo
L: a_ ||
S: do ||
@tekst "zwevend"
"""
    diags = validate_mvsa_text(text)
    orphans = [d for d in diags if d.code == "MVSA-TEKST" and d.severity == "warning"]
    assert orphans, diags
    assert "zonder volgend" in orphans[0].message


def test_validate_mscz_newline_ok_and_bad():
    ok = """\
@do F4
@mode major
@sectie demo
L: a_ |
S: do |
A: do |
T: do |
B: do |
@mscz-newline
L: b_ ||
S: re ||
A: re ||
T: re ||
B: re ||
"""
    assert validate_mvsa_text(ok) == []

    bad = """\
@mscz-newline extra
@sectie demo
L: a_ ||
S: do ||
"""
    diags = validate_mvsa_text(bad)
    assert any(d.code == "MVSA-MSCZ-NEWLINE" and d.severity == "error" for d in diags)


def test_validate_mscz_newline_orphan_warning():
    text = """\
@sectie demo
L: a_ ||
S: do ||
@mscz-newline
"""
    diags = validate_mvsa_text(text)
    orphans = [
        d for d in diags if d.code == "MVSA-MSCZ-NEWLINE" and d.severity == "warning"
    ]
    assert orphans, diags
    assert "zonder volgend" in orphans[0].message


def test_validate_height_token_elm_on_stem():
    """L-duur '_' hoort niet op de stem; validate moet MVSA-HOOGTE melden met regel."""
    text = """\
@do F4
@mode major

@sectie demo
L: le.&. ||
S: _&/ ||
A: -&- ||
T: -&/ ||
B: -&- ||
"""
    diags = validate_mvsa_text(text)
    hoogte = [d for d in diags if d.code == "MVSA-HOOGTE"]
    assert hoogte, diags
    assert hoogte[0].line == 6
    assert "_'" in hoogte[0].message or "'_'" in hoogte[0].message
    assert "positie" in hoogte[0].message


def test_validate_height_token_equals_on_stem():
    text = """\
@sectie demo
L: a_ ||
S: = ||
A: - ||
T: - ||
B: - ||
"""
    diags = validate_mvsa_text(text)
    assert any(d.code == "MVSA-HOOGTE" and "'_'" not in d.message for d in diags)
    assert any("=" in d.message for d in diags)


def test_validate_rejects_mixed_slash_ehm():
    """``\\/`` en ``/\\`` zijn geen EHM (alleen unidirectioneel /… of \\…)."""
    from vsa.mvsa_parse import is_valid_height_slot

    assert is_valid_height_slot("/")
    assert is_valid_height_slot("\\")
    assert is_valid_height_slot("/3")
    assert is_valid_height_slot("\\4")
    assert is_valid_height_slot("#\\")
    assert not is_valid_height_slot("\\/")
    assert not is_valid_height_slot("/\\")
    assert not is_valid_height_slot("/\\/")

    text = """\
@do F4
@mode major

@sectie demo
L: Al-&-&-&.&.&- ||
S: -&/&\\&\\&/&/ ||
A: -&/&\\&\\&/&/ ||
T: -&-&-&\\2&/2&- ||
B: \\3&-&-&/&\\/&/3 ||
"""
    diags = validate_mvsa_text(text)
    hoogte = [d for d in diags if d.code == "MVSA-HOOGTE"]
    assert hoogte, diags
    assert any("\\\\/" in d.message or "/\\\\" in repr(d.message) or "\\/" in d.message for d in hoogte)
    assert any("positie" in d.message and "slot" in d.message for d in hoogte)
    # Regel van de B-stem
    assert hoogte[0].line >= 5


def test_chromatic_stay_ehm_not_stripped_as_elm():
    """``+-`` / ``#-`` in melisma: stay-EHM, niet trailing ELM-``-`` strippen."""
    from vsa.mvsa_parse import parse_voice_positions, _strip_trailing_elms

    assert _strip_trailing_elms("+-") == "+-"
    assert _strip_trailing_elms("#-") == "#-"
    assert _strip_trailing_elms("b-") == "b-"
    assert _strip_trailing_elms("-&-&+-") == "-&-&+-"
    assert parse_voice_positions("-&-&+-")[0].slots == ["-", "-", "+-"]
    # Duur-ELM ná EHM mag wél weg: ``+-_`` → ``+-``
    assert _strip_trailing_elms("+-_") == "+-"
    # Absolute toon + duur blijft werken
    assert _strip_trailing_elms("a4_") == "a4"
    assert _strip_trailing_elms("si-__") == "si-"

    text = """\
@do F4
@mode major
@sectie x
L: a_&_&_ ||
S: g&-&+- ||
A: d&-&#- ||
T: bb&-&- ||
B: g&-&- ||
"""
    diags = validate_mvsa_text(text)
    errors = [d for d in diags if d.severity == "error"]
    assert not errors, errors


def test_validate_eof_closes_section_with_warning():
    """EOF sluit een open sectie; ontbrekende || is warning, geen error."""
    text = """\
@sectie demo
L: a_ |
S: do |
"""
    diags = validate_mvsa_text(text)
    errors = [d for d in diags if d.severity == "error"]
    assert errors == [], errors
    assert any(
        d.code == "MVSA-SECTIE-IMPLICIT" and d.severity == "warning" for d in diags
    )


def test_validate_new_sectie_closes_previous_with_warning():
    text = """\
@sectie a
L: a_ |
S: do |

@sectie b
L: b_ ||
S: re ||
"""
    diags = validate_mvsa_text(text)
    errors = [d for d in diags if d.severity == "error"]
    assert errors == [], errors
    assert any(
        d.code == "MVSA-SECTIE-IMPLICIT"
        and "@sectie 'b'" in d.message
        and d.severity == "warning"
        for d in diags
    )


def test_validate_blok_no_implicit_sectie_warning():
    """Tussen @blok's is geen || vereist; geen SECTIE-IMPLICIT."""
    text = """\
@do F4
@mode major
@speelplan 1, 2

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
"""
    diags = validate_mvsa_text(text)
    assert not any(d.code == "MVSA-SECTIE-IMPLICIT" for d in diags)
    assert not any(d.severity == "error" for d in diags)


@pytest.mark.parametrize(
    "name",
    [
        "1a-vredeslitanie.mvsa",
        "alleluia-toon-1.mvsa",
        "alleluia-toon-8.mvsa",
        "kleine-intocht-zondag-hemelum.mvsa",
        "trisagion-8a-slav-hemelum.mvsa",
    ],
)
def test_examples_mvsa_ok(name: str):
    path = EXAMPLES / name
    diags = validate_mvsa_text(path.read_text(encoding="utf-8"), source=str(path))
    errors = [d for d in diags if d.severity == "error"]
    assert errors == [], errors


def test_leading_utf8_bom_is_ignored():
    """Windows-editors zetten soms UTF-8 BOM; dat mag geen MVSA-LINE geven."""
    text = "\ufeff# comment\n@do F4\n@mode major\n@sectie x\nL: a_ ||\nS: do ||\nA: do ||\nT: do ||\nB: do ||\n"
    diags = validate_mvsa_text(text)
    errors = [d for d in diags if d.severity == "error"]
    assert errors == [], errors
    assert not any(d.code == "MVSA-LINE" for d in diags)


@pytest.mark.parametrize(
    ("line", "stem", "ehm", "lyrics"),
    [
        ("S: do ||", "S", None, False),
        ("S-: / ||", "S", "-", False),
        ("S/3: / ||", "S", "/3", False),
        ("T\\6: \\ ||", "T", "\\6", False),
        ("L1: a_ ||", "L1", None, True),
        ("lyrics: a_ ||", "lyrics", None, True),
        ("cantus: do ||", "cantus", None, False),
        ("S1/: / ||", "S1", "/", False),
    ],
)
def test_parse_regelidentifier_ok(line: str, stem: str, ehm: str | None, lyrics: bool):
    rid = parse_regelidentifier(line)
    assert rid is not None
    assert rid.stem_id == stem
    assert rid.ehm == ehm
    assert rid.is_lyrics is lyrics


@pytest.mark.parametrize(
    "line",
    [
        "S_: do ||",
        "S--: / ||",
        "no-colon",
        ": empty stem",
    ],
)
def test_parse_regelidentifier_rejects(line: str):
    assert parse_regelidentifier(line) is None


def test_validate_ehm_on_lyrics_error():
    text = """\
@sectie demo
L/: a_ ||
S: do ||
"""
    diags = validate_mvsa_text(text)
    assert any(d.code == "MVSA-EHM-L" for d in diags)


def test_validate_relative_identifier_ok():
    text = """\
@do F4
@mode major

@sectie demo
L: a_ b_ ||
S-: - / ||
A-: - / ||
T-: - / ||
B-: - / ||
"""
    assert validate_mvsa_text(text) == []


def test_validate_cantus_stem_ok():
    text = """\
@sectie demo
L: a_ ||
cantus: do ||
"""
    assert validate_mvsa_text(text) == []


def test_split_bars_reads_eindanker():
    from vsa.mvsa_validate import _split_bars

    sp = _split_bars("do / |mi re ||fa")
    assert sp.bar_tokens == ["|", "||"]
    assert sp.bar_anchors == ["mi", "fa"]
    assert sp.segments[0].strip() == "do /"
    assert sp.segments[1].strip() == "re"

    bare = _split_bars("do | re ||")
    assert bare.bar_anchors == [None, None]

    spaced = _split_bars("do | mi ||")
    assert spaced.bar_anchors == [None, None]
    assert spaced.segments[1].strip() == "mi"


def test_validate_bar_anchor_ok():
    text = """\
@do F4
@mode major

@sectie demo
L: a_ b_ ||
S: do / ||/
A: do - ||-
T: do / ||/
B: do - ||-
"""
    assert validate_mvsa_text(text) == []


def test_validate_bar_anchor_mismatch():
    text = """\
@do F4
@mode major

@sectie demo
L: a_ b_ ||
S: do / ||mi
A: do - ||-
T: do / ||/
B: do - ||-
"""
    diags = validate_mvsa_text(text)
    assert any(d.code == "MVSA-BAR-ANKER" and "S:" in d.message for d in diags)


def test_validate_bar_anchor_on_lyrics_error():
    text = """\
@sectie demo
L: a_||mi
S: do ||-
"""
    diags = validate_mvsa_text(text)
    assert any(d.code == "MVSA-BAR-ANKER" and "lyrics" in d.message for d in diags)


def test_validate_absolute_bar_anchor_ok():
    text = """\
@do F4
@mode major

@sectie demo
L: a_ ||
S: mi ||mi
A: do ||-
T: do ||-
B: do ||-
"""
    assert validate_mvsa_text(text) == []


def test_speelplan_ok():
    text = """\
@do F4
@mode major
@speelplan 1, 2, 1, 2

@blok 1
L: a_ |
S: do |
A: do |
T: do |
B: do |

@blok 2
L: b_ ||
S: re ||
A: re ||
T: re ||
B: re ||
"""
    diags = validate_mvsa_text(text)
    assert not any(d.severity == "error" for d in diags)


def test_speelplan_forbids_repeat_bar():
    text = """\
@do F4
@mode major
@speelplan 1, 2

@blok 1
L: a_ :|
S: do :|
A: do :|
T: do :|
B: do :|

@blok 2
L: b_ ||
S: re ||
A: re ||
T: re ||
B: re ||
"""
    diags = validate_mvsa_text(text)
    assert any(d.code == "MVSA-SPEELPLAN-REPEAT-BAR" for d in diags)


def test_speelplan_unknown_id():
    text = """\
@do F4
@mode major
@speelplan 1, 9

@blok 1
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
"""
    diags = validate_mvsa_text(text)
    assert any(d.code == "MVSA-SPEELPLAN-UNKNOWN-ID" for d in diags)


def test_speelplan_anon_section_error():
    text = """\
@do F4
@mode major
@speelplan 1

@blok 1
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||

@sectie extra
L: b_ ||
S: re ||
A: re ||
T: re ||
B: re ||
"""
    diags = validate_mvsa_text(text)
    assert any(d.code == "MVSA-SPEELPLAN-ANON" for d in diags)
