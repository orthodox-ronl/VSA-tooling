"""``@taal xx`` voor talen zonder woordenlijst: niet controleren, niet aanraken."""

from __future__ import annotations

from vsa.mvsa_validate import validate_mvsa_text
from vsa.parser import Parser
from vsa.syllabify import syllabify_vsa_body
from vsa.syllable_dict_check import (
    CODE_UNKNOWN,
    find_dictionary_syllable_issues,
    find_mvsa_dictionary_syllable_issues,
    iter_mvsa_lyric_word_cores_tagged,
    iter_vsa_lyric_word_cores_tagged,
)

MVSA = """\
@taal nl
L: Qwerty-plonk_ |
S: do |

@nieuw-systeem
@taal ro
L: Doam-ne mi-lu-es-te_ |
S: do |

@nieuw-systeem
@taal auto
L: Zzyzx-voort_ |
S: do |
"""


def test_mvsa_accepts_language_codes() -> None:
    diags = validate_mvsa_text("@taal ro\nL: a_ |\nS: do |\n")
    assert not any(d.code == "MVSA-TAAL" for d in diags)
    diags = validate_mvsa_text("@taal frans\nL: a_ |\nS: do |\n")
    assert any(d.code == "MVSA-TAAL" for d in diags)


def test_mvsa_cores_tagged_by_sticky_taal() -> None:
    tagged = dict(iter_mvsa_lyric_word_cores_tagged(MVSA))
    assert tagged["Qwerty-plonk"] == "nl"
    assert tagged["Doam-ne"] == "ro"
    assert tagged["mi-lu-es-te"] == "ro"
    assert tagged["Zzyzx-voort"] is None


def test_mvsa_language_without_wordlist_is_not_checked() -> None:
    surfaces = {
        f.surface
        for f in find_mvsa_dictionary_syllable_issues(MVSA, lyrics_lang="auto")
        if f.code == CODE_UNKNOWN
    }
    assert "Qwerty-plonk" in surfaces  # nl: wel gecontroleerd
    assert "Zzyzx-voort" in surfaces  # auto: wel gecontroleerd
    assert "Doam-ne" not in surfaces and "mi-lu-es-te" not in surfaces


VSA_BODY = "Qwerty-plonk\n@taal ro\nDoam-ne mi-lu-es-te\n@taal auto\nZzyzx-voort\n"


def test_vsa_body_taal_directive_tags_and_skips() -> None:
    document = Parser(VSA_BODY).parse()
    tagged = dict(iter_vsa_lyric_word_cores_tagged(document))
    assert tagged["Qwerty-plonk"] is None
    assert tagged["Doam-ne"] == "ro"
    assert tagged["Zzyzx-voort"] is None
    surfaces = {
        f.surface
        for f in find_dictionary_syllable_issues(
            document, source_text=VSA_BODY, lyrics_lang="auto"
        )
        if f.code == CODE_UNKNOWN
    }
    assert {"Qwerty-plonk", "Zzyzx-voort"} <= surfaces
    assert not {"Doam-ne", "mi-lu-es-te"} & surfaces


def test_syllabify_leaves_foreign_language_alone() -> None:
    out = syllabify_vsa_body("de aarde\n@taal ro\nde aarde\n@taal auto\nde aarde\n").text
    assert out == "de aar-de\n@taal ro\nde aarde\n@taal auto\nde aar-de\n"
