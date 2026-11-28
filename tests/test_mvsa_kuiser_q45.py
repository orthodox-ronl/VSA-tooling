"""Kuiser Q4 (syllabify) + Q5 (dictionary) — docs/formats/kuiser.md."""

from __future__ import annotations

from vsa.mvsa_kuiser import kuiser_mvsa_text
from vsa.mvsa_kuiser_q45 import apply_q4_q5
from vsa.yaml_frontmatter import strip_yaml_frontmatter


def test_q4_syllabifies_cadens_word():
    text = """\
@do F4
@mode major
@sectie a
L: heerlijkheid_ ||
S: fa_           ||
A: re_           ||
T: la-_          ||
B: re_           ||
"""
    out, warnings = apply_q4_q5(text, align=False, dict_interactive=False)
    l_line = next(ln for ln in out.splitlines() if ln.lstrip().startswith("L:"))
    assert "lijk" in l_line
    assert "-" in l_line
    # Geen fatale dictionary-fout voor bekende lemma's na Q4.
    assert not any("MISMATCH" in w.message for w in warnings)


def test_q5_emits_warning_for_unknown_lemma():
    from vsa.syllable_dict_check import (
        CODE_UNKNOWN,
        find_mvsa_dictionary_syllable_issues,
    )

    text = """\
@do F4
@mode major
@sectie a
L: zzqxvvm_ ||
S: fa_      ||
A: re_      ||
T: la-_     ||
B: re_      ||
"""
    out, warnings = apply_q4_q5(text, align=False, dict_interactive=False)
    findings = find_mvsa_dictionary_syllable_issues(out)
    # Onbekend lemma → UNKNOWN in findings en/of kuiser-warnings.
    assert any(f.code == CODE_UNKNOWN for f in findings) or any(
        "UNKNOWN" in w.message for w in warnings
    )


def test_kuiser_pipeline_q4_then_q1_zoektekst_plain():
    text = """\
@do F4
@mode major
@sectie a
L: heerlijkheid_ ||
S: fa_           ||
A: re_           ||
T: la-_          ||
B: re_           ||
"""
    result = kuiser_mvsa_text(
        text,
        align=False,
        source_path="alleluia-toon-8-groningen.mvsa",
        dict_interactive=False,
    )
    fm, body, _ = strip_yaml_frontmatter(result.text)
    zt = str(fm.get("zoektekst", ""))
    assert "heerlijkheid" in zt.replace("-", "").replace(" ", "")
    assert "lijk" in body
    assert "#maat 1" in body
