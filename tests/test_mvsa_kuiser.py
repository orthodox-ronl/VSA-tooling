"""Tests for mvsa kuiser (authoring canonicalize)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from vsa.cli_mvsa import main as mvsa_main
from vsa.mvsa_kuiser import (
    MvsaKuiserError,
    kuiser_mvsa_path,
    kuiser_mvsa_text,
)
from vsa.mvsa_validate import validate_mvsa_text

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "mvsa"


def test_kuiser_rewrites_elm_dash_then_omits_lone_tilde():
    text = """\
@do F4
@mode major
@sectie a
L: hei- li- ge ||
S: fa  so  mi  ||
A: re  re  do  ||
T: la- so- so- ||
B: re  re  do  ||
"""
    result = kuiser_mvsa_text(text, align=False)
    # ELM '-' → '~' → lone '~' weggelaten; geen collapse naar woordstreepje.
    assert re.search(r"L:\s*hei\s+li\s+ge", result.text)
    assert "hei~" not in result.text
    assert "hei-li" not in result.text
    assert any("ambiguë" in w.message for w in result.warnings)
    assert all(w.line >= 1 and w.column >= 1 for w in result.warnings)
    diags = validate_mvsa_text(result.text)
    assert not [d for d in diags if d.severity == "error"]


def test_kuiser_keeps_tilde_in_melisma_omits_after_recite():
    text = """\
@do F4
@mode major
@sectie a
L: ziel~&~ (ia)~ ||
S: fa&so   la   ||
A: re&re   re   ||
T: la-&so- so-  ||
B: re&re   re   ||
"""
    result = kuiser_mvsa_text(text, align=False)
    assert "ziel~&~" in result.text
    assert "(ia)" in result.text
    assert "(ia)~" not in result.text
    diags = validate_mvsa_text(result.text)
    assert not [d for d in diags if d.severity == "error"]


def test_kuiser_omits_lone_tilde_and_elm_dash_keeps_soft_hyphen():
    """Soft ``ge-neest`` blijft; trailing ELM-``-``/lone ``~`` weg."""
    text = """\
@do F4
@mode major
@sectie a
L: Hij~ ge-neest- al~ uw~ kwa_-len_. ||
S: fa   so so     la  so  fa   mi    ||
A: re   re re     re  re  re   do    ||
T: la-  so- so-   so- so- la-  so-   ||
B: re   re re     re  re  re   do    ||
"""
    result = kuiser_mvsa_text(text, align=False)
    l_line = next(ln for ln in result.text.splitlines() if ln.startswith("L:"))
    assert re.search(r"\bge-neest\b", l_line)
    assert "ge-neest-" not in l_line
    assert "ge-neest~" not in l_line
    assert "Hij~" not in l_line
    assert "al~" not in l_line
    assert "uw~" not in l_line
    assert "kwa_-len_." in l_line
    diags = validate_mvsa_text(result.text)
    assert not [d for d in diags if d.severity == "error"]


def test_kuiser_no_ambiguous_warn_on_melisma_elm_before_word():
    text = """\
@do F4
@mode major
@sectie a
L: lu_&-&-  ia_ ||
S: fa&so&la si ||
A: re&re&re re ||
T: la-&so-&la- si- ||
B: re&re&re re ||
"""
    result = kuiser_mvsa_text(text, align=False)
    assert "lu_&~&~" in result.text
    assert not any("ambiguë" in w.message for w in result.warnings)


def test_kuiser_semantic_missing_hyphen_warning():
    """Alleen bij lemma in de woordenlijst (``vader``), niet bij Pyphen-ruis."""
    text = """\
@do F4
@mode major
@sectie a
L: Va der ||
S: fa so ||
A: re re ||
T: la- so- ||
B: re re ||
"""
    result = kuiser_mvsa_text(text, align=False)
    assert any("missen woordstreepjes" in w.message for w in result.warnings)
    assert any("va-der" in w.message.lower() for w in result.warnings)


def test_kuiser_warning_line_includes_yaml_frontmatter_offset():
    """Warning-regelnummers tellen mee vanaf het hele bestand (YAML + body)."""
    text = """\
---
titel: Test
taal: nl
---

@do F4
@mode major
@sectie a
L: Va der ||
S: fa so ||
A: re re ||
T: la- so- ||
B: re re ||
"""
    result = kuiser_mvsa_text(text, align=False)
    miss = [w for w in result.warnings if "missen woordstreepjes" in w.message]
    assert miss
    # Regelnummer = L-regel in de tekst ná Q6/Q2/Q3 (YAML + geïnjecteerde @).
    from vsa.mvsa_kuiser_q23 import apply_q2_q3
    from vsa.mvsa_kuiser_q67 import apply_q6

    prepared = apply_q2_q3(apply_q6(text, werkbank=False))
    prep_lines = prepared.splitlines()
    assert 1 <= miss[0].line <= len(prep_lines)
    assert "Va der" in prep_lines[miss[0].line - 1]


def test_kuiser_semantic_no_false_hyphen_across_words():
    """Losse woorden (``in eeu…``) → geen Pyphen-ruis-warning."""
    text = """\
@do F4
@mode major
@sectie a
L: in eeu_-wig-heid_ ||
S: fa so   la  si    ||
A: re re   re  re    ||
T: la- so- so- so-   ||
B: re re   re  re    ||
"""
    result = kuiser_mvsa_text(text, align=False)
    assert not any("missen woordstreepjes" in w.message for w in result.warnings)
    assert not any("in-eeu" in w.message for w in result.warnings)


def test_kuiser_semantic_does_not_glue_next_capital_word():
    text = """\
@do F4
@mode major
@sectie a
L: Va der God ||
S: fa so si ||
A: re re re ||
T: la- so- so- ||
B: re re re ||
"""
    result = kuiser_mvsa_text(text, align=False)
    msgs = [w.message for w in result.warnings if "missen woordstreepjes" in w.message]
    assert any("va-der" in m.lower() for m in msgs)
    assert not any("God" in m for m in msgs)


def test_kuiser_preserves_space_before_word_hyphen():
    """``…_&_  -li`` blijft; streepje vóór de lettergreep, spaties ervóór."""
    text = """\
@do F4
@mode major
@sectie a
L: hei_&_&_&_&_&_ -li ||
S: fa&so&la&si&do&re   mi ||
A: re&re&re&re&re&re   re ||
T: la-&so-&la-&si-&do-&re- mi ||
B: re&re&re&re&re&re   re ||
"""
    result = kuiser_mvsa_text(text, align=False)
    assert re.search(r"hei_&_&_&_&_&_\s+-li", result.text)
    assert "hei_&_&_&_&_&_-li" not in result.text
    diags = validate_mvsa_text(result.text)
    assert not [d for d in diags if d.severity == "error"]


def test_kuiser_rewrites_melisma_elm_dash():
    text = """\
@do F4
@mode major
@sectie a
L: lu_&-&-&_ ||
S: fa&so&la&si ||
A: re&re&re&re ||
T: la-&so-&la-&si- ||
B: re&re&re&re ||
"""
    result = kuiser_mvsa_text(text, align=False)
    assert "lu_&~&~&_" in result.text
    assert "lu_&-&-&_" not in result.text


def test_kuiser_keeps_compound_dash_dot():
    text = """\
@do F4
@mode major
@sectie a
L: hei-. ||
S: fa ||
A: re ||
T: la- ||
B: re ||
"""
    result = kuiser_mvsa_text(text, align=False)
    assert "hei-." in result.text


def test_kuiser_syncs_missing_voice_bars():
    text = """\
@do F4
@mode major
@sectie a
L: Komt_ | Heer_ ||
S: fa so ||
A: re re ||
T: la- so- ||
B: re re ||
"""
    before = [d for d in validate_mvsa_text(text) if d.severity == "error"]
    assert any(d.code == "MVSA-MEASURE-COUNT" for d in before)

    result = kuiser_mvsa_text(text)
    assert re.search(r"^S:.*\|.*\|\|", result.text, re.M)
    diags = validate_mvsa_text(result.text)
    assert not [d for d in diags if d.severity == "error"]
    for stem in ("S", "A", "T", "B"):
        line = next(
            ln for ln in result.text.splitlines() if ln.startswith(f"{stem}:")
        )
        assert line.count("|") >= 2


def test_kuiser_rejects_conflicting_maximal_bars():
    text = """\
@do F4
@mode major
@sectie a
L: a | b ||
S: fa :| so ||
A: re | re ||
T: la- | so- ||
B: re | re ||
"""
    with pytest.raises(MvsaKuiserError, match="niet eenduidig"):
        kuiser_mvsa_text(text)


def test_kuiser_idempotent_on_canonical_example():
    path = EXAMPLES / "alleluia-toon-8.mvsa"
    text = path.read_text(encoding="utf-8")
    once = kuiser_mvsa_text(text)
    twice = kuiser_mvsa_text(once.text)
    assert once.text == twice.text
    diags = validate_mvsa_text(once.text)
    assert not [d for d in diags if d.severity == "error"]


def test_kuiser_preserves_leading_repeat_bar():
    text = """\
@do F4
@mode major
@sectie a
L: |: Heer_ | U__ :|
S: |: a     | -   :|a
A: |: f     | -   :|f
T: |: c     | -   :|c
B: |: f     | -   :|f
"""
    result = kuiser_mvsa_text(text)
    for stem in ("L", "S", "A", "T", "B"):
        line = next(ln for ln in result.text.splitlines() if ln.startswith(f"{stem}:"))
        assert line.lstrip().startswith(f"{stem}: |:") or "|: " in line
    diags = validate_mvsa_text(result.text)
    assert not [d for d in diags if d.severity == "error"]


def test_kuiser_check_and_cli(tmp_path: Path, capsys):
    src = tmp_path / "sketch.mvsa"
    src.write_text(
        """\
@do F4
@mode major
@sectie a
L: hei- li ||
S: fa so ||
A: re re ||
T: la- so- ||
B: re re ||
""",
        encoding="utf-8",
        newline="\n",
    )
    changed, warnings = kuiser_mvsa_path(src, check=True)
    assert changed is True
    assert warnings
    assert mvsa_main(["kuiser", str(src), "--check"]) == 1
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "ambiguë" in err
    assert mvsa_main(["kuiser", str(src)]) == 0
    body = src.read_text(encoding="utf-8")
    assert re.search(r"L:\s*hei\s+li\b", body)
    assert "hei~" not in body
    assert "hei-li" not in body
    assert mvsa_main(["kuiser", str(src), "--check"]) == 0


def test_cli_help_lists_kuiser(capsys):
    with pytest.raises(SystemExit) as exc:
        mvsa_main(["-h"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "kuiser" in out
