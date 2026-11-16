"""Tests for mvsa syllabify (recite + cadens expand, sync-safe)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from vsa.mvsa_align import _l_tokens, align_mvsa_text
from vsa.mvsa_marks import ACTIVE_MARKS, CAESURA_DURATION_ELMS, MarkSpec
from vsa.mvsa_syllabify import (
    MvsaSyllabifyError,
    syllabify_mvsa_text,
)
from vsa.mvsa_validate import validate_mvsa_text
from vsa.syllable_dictionary import (
    clear_syllable_dictionary_cache,
    set_syllable_dictionary_path,
)


MINI = Path("examples/mvsa/syllabificatie-recite-mini.mvsa")
STRUCTURAL = Path("examples/mvsa/syllabificatie-structural-marks.mvsa")
HEMELUM = Path("examples/mvsa/syllabificatie-marks-hemelum.mvsa")

_BRACKET_RE = re.compile(r"\[[^\]]+\]")


def _errors(text: str) -> list[str]:
    return [
        f"{d.code}:{d.message}"
        for d in validate_mvsa_text(text)
        if d.severity == "error"
    ]


def _l_lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.lstrip().startswith("L:")]


def _l_brackets(text: str) -> list[str]:
    """Alle ``[…]``-tokens op L-regels (volgorde behouden)."""
    out: list[str] = []
    for ln in _l_lines(text):
        out.extend(_BRACKET_RE.findall(ln))
    return out


def _mini_mvsa(l_body: str, s_body: str = "a4 |") -> str:
    return (
        '@title "t"\n'
        "@do F4\n"
        "@mode major\n"
        "@oct S=0\n"
        "\n"
        f"L: {l_body}\n"
        f"S: {s_body}\n"
    )


def _stop_raw_for(kind: str) -> str | None:
    for raw, spec in ACTIVE_MARKS.items():
        if spec.kind == kind and spec.span_role == "stop":
            return raw
    return None


def _assert_structure_spared(src: str, out: str) -> None:
    """Structurele L-tokens blijven; alleen zing-deling mag wijzigen."""
    assert _errors(out) == []
    assert _l_brackets(src) == _l_brackets(out)
    for token in ("|:", ":|"):
        assert src.count(token) == out.count(token)
    # Recite-haakjes op L (niet in zoektekst/FM)
    assert sum(ln.count("(") for ln in _l_lines(src)) == sum(
        ln.count("(") for ln in _l_lines(out)
    )
    assert sum(ln.count(")") for ln in _l_lines(src)) == sum(
        ln.count(")") for ln in _l_lines(out)
    )


def test_syllabify_recite_adds_soft_hyphens(tmp_path: Path):
    dict_file = tmp_path / "dict.txt"
    dict_file.write_text("leer-lin-gen\ntoon-de\n", encoding="utf-8")
    set_syllable_dictionary_path(dict_file)
    clear_syllable_dictionary_cache()
    try:
        src = """\
@title "t"
@do F4
@mode major
@oct S=0

@sectie demo
L: (Leerlingen toonde Gij Uw) heer_ |
S: a4                           -    |
"""
        result = syllabify_mvsa_text(src, align=False)
        assert result.changed
        assert "(Leer-lin-gen toon-de Gij Uw)" in result.text
        assert _errors(result.text) == []
    finally:
        set_syllable_dictionary_path(None)
        clear_syllable_dictionary_cache()


def test_syllabify_cadens_expands_and_pads_stem():
    src = """\
@title "t"
@do F4
@mode major
@oct S=0

@sectie demo
L: heerlijkheid_ |
S: a4_           |
"""
    result = syllabify_mvsa_text(src, align=False)
    assert result.changed
    assert "heer" in result.text
    # Hyphen-keten + holds
    assert "-lijk" in result.text or "lijk" in result.text
    l_line = next(
        ln for ln in result.text.splitlines() if ln.lstrip().startswith("L:")
    )
    s_line = next(
        ln for ln in result.text.splitlines() if ln.lstrip().startswith("S:")
    )
    from vsa.mvsa_align import _l_tokens, _voice_tokens
    from vsa.mvsa_validate import _split_bars

    l_seg = _split_bars(l_line.split(":", 1)[1].lstrip()).segments[0]
    s_seg = _split_bars(s_line.split(":", 1)[1].lstrip()).segments[0]
    assert len(_l_tokens(l_seg)) == len(_voice_tokens(s_seg))
    assert _voice_tokens(s_seg).count("-") >= 1
    assert _errors(result.text) == []


def test_syllabify_does_not_rehyphenate_continues_word_piece():
    """Al gedeeld ``ge``+``-neest`` mag niet opnieuw ``nee-st`` worden (loop)."""
    from vsa.syllable_dict_check import find_mvsa_dictionary_syllable_issues

    src = """\
@title "t"
@do F4
@mode major
@oct S=0

@sectie demo
L: Hij ge_-neest_ al |
S: a4  /   /      -  |
"""
    result = syllabify_mvsa_text(src, align=False)
    assert "nee-st" not in result.text.replace("_", "")
    # Geen ge-nee-st-keten; wel ge-neest behouden.
    l_line = next(
        ln for ln in result.text.splitlines() if ln.lstrip().startswith("L:")
    )
    assert "neest" in l_line
    mismatches = [
        f
        for f in find_mvsa_dictionary_syllable_issues(result.text)
        if f.surface == "ge-nee-st"
    ]
    assert mismatches == []
    # Tweede run blijft stabiel t.o.v. woordenboek.
    again = syllabify_mvsa_text(result.text, align=False)
    assert not any(
        f.surface == "ge-nee-st"
        for f in find_mvsa_dictionary_syllable_issues(again.text)
    )


def test_syllabify_idempotent_on_mini_example():
    if not MINI.is_file():
        pytest.skip("example missing")
    text = MINI.read_text(encoding="utf-8")
    assert _errors(text) == []
    result = syllabify_mvsa_text(text, align=True)
    # Al gesyllabificeerd → geen of minimale wijziging; resultaat blijft geldig
    assert _errors(result.text) == []
    again = syllabify_mvsa_text(result.text, align=True)
    assert again.text == result.text


def test_unsyllabify_recite_only():
    src = """\
@title "t"
@do F4
@mode major
@oct S=0

@sectie demo
L: (Leer-lin-gen toon-de) heer_-lijk_ |
S: a4                     -     -     |
"""
    result = syllabify_mvsa_text(src, unsyllabify=True, align=False)
    assert "(Leerlingen toonde)" in result.text
    # Cadens-keten blijft
    assert "heer_" in result.text
    assert "-lijk" in result.text
    assert _errors(result.text) == []


def test_syllabify_rejects_broken_sync():
    src = """\
---
taal: nl
---

@title "t"
@do F4
@mode major
@oct S=0

@sectie demo
L: a_ b_ |
S: a4    |
"""
    with pytest.raises(MvsaSyllabifyError) as caught:
        syllabify_mvsa_text(src, align=False)
    err = caught.value
    msg = str(err)
    assert "tekstregel (L)" in msg
    assert "zangregel S:" in msg
    assert "2 posities" in msg
    assert "1" in msg  # S heeft 1 positie
    assert "gelijk" in msg
    # YAML-FM is 4 regels (--- / taal / --- / blank); L op body-regel 8 → bestand 12
    # Blok start op L; mismatch op S → één regel later
    rows = src.splitlines()
    assert err.line is not None
    assert rows[err.line - 1].lstrip().startswith("S:")
    assert "sync vóór" not in msg


def test_l_tokens_include_trailing_caesura_mark():
    """``_l_tokens`` houdt ``[//.]`` bij de L-positie (align/syllabify-input)."""
    toks = _l_tokens("ze_-gend_ [//.]")
    assert len(toks) == 2
    assert toks[-1].endswith("[//.]")
    assert "[//.]" in toks[-1]


@pytest.mark.parametrize(
    "raw,spec",
    sorted(ACTIVE_MARKS.items(), key=lambda kv: kv[0]),
    ids=sorted(ACTIVE_MARKS),
)
def test_active_mark_survives_align_and_syllabify(raw: str, spec: MarkSpec):
    """Elke registry-mark blijft op L na align én syllabify (toekomstvaste dekking)."""
    if spec.span_role == "stop":
        pytest.skip("stop-mark gedekt via start-paar")
    bracket = f"[{raw}]"
    if spec.span_role == "start":
        stop = _stop_raw_for(spec.kind)
        assert stop is not None, f"geen stop voor kind={spec.kind}"
        l_body = f"[{raw}]a_ [{stop}] |"
        expected = [bracket, f"[{stop}]"]
    elif spec.attach == "before":
        l_body = f"[{raw}]a_ |"
        expected = [bracket]
    else:
        l_body = f"a_ [{raw}] |"
        expected = [bracket]

    src = _mini_mvsa(l_body)
    assert _errors(src) == [], _errors(src)
    assert _l_brackets(src) == expected

    aligned = align_mvsa_text(src)
    assert _l_brackets(aligned) == expected
    assert _errors(aligned) == []

    syl = syllabify_mvsa_text(src, align=True)
    assert _l_brackets(syl.text) == expected
    assert _errors(syl.text) == []


@pytest.mark.parametrize(
    "elm",
    sorted(CAESURA_DURATION_ELMS),
)
def test_caesura_duration_mark_survives(elm: str):
    """Cesuur met duur-ELM (``[//.]``, ``[//_]``, …) blijft na align/syllabify."""
    raw = "//" if elm == "~" else f"//{elm}"
    # Canonieke aliasen ``[//~]`` / ``[//-]`` mogen wegvallen in andere paden;
    # hier testen we de expliciete bronvorm die lookup accepteert.
    if raw in ("//~", "//-"):
        pytest.skip("alias; canonicalize → [//]")
    bracket = f"[{raw}]"
    src = _mini_mvsa(f"a_ {bracket} |")
    assert _errors(src) == [], _errors(src)
    for out in (align_mvsa_text(src), syllabify_mvsa_text(src, align=True).text):
        assert bracket in "".join(_l_lines(out))
        assert _l_brackets(out) == [bracket]
        assert _errors(out) == []


def test_structural_marks_example_spared_by_align_and_syllabify():
    if not STRUCTURAL.is_file():
        pytest.skip("example missing")
    src = STRUCTURAL.read_text(encoding="utf-8")
    assert _errors(src) == []
    aligned = align_mvsa_text(src)
    _assert_structure_spared(src, aligned)
    syl = syllabify_mvsa_text(src, align=True)
    _assert_structure_spared(src, syl.text)
    # Idempotent op structurele brackets
    again = syllabify_mvsa_text(syl.text, align=True)
    assert _l_brackets(again.text) == _l_brackets(syl.text)


def test_hemelum_marks_example_keeps_caesura_and_repeats():
    """Catalogus-spiegel: ``[//.]`` + herhalingstekens blijven (regres)."""
    if not HEMELUM.is_file():
        pytest.skip("example missing")
    src = HEMELUM.read_text(encoding="utf-8")
    assert src.count("[//.]") == 3
    assert _errors(src) == []

    # Frontmatter / zoektekst mag niet wijzigen
    fm_end = src.find("\n---", 3)
    assert fm_end != -1
    fm = src[: fm_end + len("\n---")]

    for transform, label in (
        (lambda t: align_mvsa_text(t), "align"),
        (lambda t: syllabify_mvsa_text(t, align=True).text, "syllabify"),
    ):
        out = transform(src)
        assert out.startswith(fm), label
        assert out.count("[//.]") == 3, label
        assert out.count("|:") == src.count("|:")
        assert out.count(":|") == src.count(":|")
        assert _l_brackets(out).count("[//.]") == 3
        assert _errors(out) == []
        # Non-lyrics: @-directives en commentaarregels blijven
        src_at = [ln for ln in src.splitlines() if ln.startswith("@")]
        out_at = [ln for ln in out.splitlines() if ln.startswith("@")]
        assert src_at == out_at, label


def test_syllabify_preserves_hash_and_html_comments():
    """``#``-regels en HTML-comments blijven staan (zelfde idee als VSA)."""
    src = """\
@title "t"
@do F4
@mode major
@oct S=0

# regelcommentaar met eeuwig hier
<!-- html commentaar met eeuwig -->
L: (Leerlingen) heer_ |
S: a4           -    |
"""
    result = syllabify_mvsa_text(src, align=False)
    assert "# regelcommentaar met eeuwig hier" in result.text
    assert "<!-- html commentaar met eeuwig -->" in result.text
    assert "Leer-lin-gen" in result.text
    assert _errors(result.text) == []


def test_cli_writes_tty_fixes_even_when_dictionary_still_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Zelfde als vsa: TTY-/gate-correcties schrijven ondanks restfouten."""
    from vsa.cli_mvsa import main as mvsa_main

    path = tmp_path / "lied.mvsa"
    original = _mini_mvsa("(Leerlingen) heer_ |", "a4           -    |")
    path.write_text(original, encoding="utf-8")
    fixed = original.replace("Leerlingen", "Leer-lin-gen")

    def fake_gate(_file_path: Path, source_text: str):
        assert "Leerlingen" in source_text or "Leer-lin-gen" in source_text
        return 1, fixed

    monkeypatch.setattr(
        "vsa.cli._mvsa_syllabify_dictionary_gate", fake_gate
    )
    assert mvsa_main(["syllabify", str(path)]) == 1
    assert "Leer-lin-gen" in path.read_text(encoding="utf-8")


def test_cli_gate_equals_does_not_echo_stale_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    """Na ``=`` (vorm in lijst) geen herhaling van dezelfde MISMATCH-dump."""
    from vsa.cli import _mvsa_syllabify_dictionary_gate
    from vsa.syllable_dict_check import (
        CODE_MISMATCH,
        DictSyllableFinding,
        DictionaryPromptResult,
        clear_syllable_dictionary_cache,
    )
    from vsa.syllable_dictionary import set_syllable_dictionary_path

    dict_file = tmp_path / "dict.txt"
    dict_file.write_text("mij-nent-wil\n", encoding="utf-8")
    set_syllable_dictionary_path(dict_file)
    clear_syllable_dictionary_cache()

    path = tmp_path / "lied.mvsa"
    src = _mini_mvsa("(mij-nen-twil) heer_ |", "a4             -    |")
    path.write_text(src, encoding="utf-8")

    finding = DictSyllableFinding(
        code=CODE_MISMATCH,
        surface="mij-nen-twil",
        expected="mij-nent-wil",
        line=6,
        column=4,
        message_nl="Woord `mij-nen-twil` hoort als `mij-nent-wil`.",
        hint_nl="hint",
    )
    calls = {"n": 0}

    def find_side_effect(_text):
        calls["n"] += 1
        return [finding] if calls["n"] == 1 else []

    def fake_prompt(*_a, **_k):
        return DictionaryPromptResult(
            added_or_updated=["mij-nen-twil"],
            replacements=[],
            aborted=False,
        )

    monkeypatch.setattr(
        "vsa.syllable_dict_check.is_interactive_stdin", lambda stdin=None: True
    )
    monkeypatch.setattr(
        "vsa.syllable_dict_check.prompt_dictionary_fixes", fake_prompt
    )
    monkeypatch.setattr(
        "vsa.syllable_dict_check.find_mvsa_dictionary_syllable_issues",
        find_side_effect,
    )

    try:
        rc, _ = _mvsa_syllabify_dictionary_gate(path, src)
        assert rc == 0
        assert calls["n"] == 2  # vóór én ná TTY
        err = capsys.readouterr().err
        assert "VSA-SYLLABLE-DICT-MISMATCH" not in err
    finally:
        set_syllable_dictionary_path(None)
        clear_syllable_dictionary_cache()


def test_mvsa_dictionary_gate_abort_returns_original_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Esc/Ctrl+C: rc=2 en tekst van vóór de gate (geen partial replace)."""
    from vsa.cli import _mvsa_syllabify_dictionary_gate
    from vsa.syllable_dict_check import (
        CODE_UNKNOWN,
        DICT_PROMPT_ABORT_RC,
        DictionaryPromptResult,
        DictSyllableFinding,
    )

    path = tmp_path / "lied.mvsa"
    src = (
        "@oct S=0\n"
        "L: ge_-nee_-st_ |\n"
        "S: /   -    /   |\n"
    )
    path.write_text(src, encoding="utf-8")
    before = path.read_bytes()

    monkeypatch.setattr(
        "vsa.syllable_dict_check.is_interactive_stdin", lambda stdin=None: True
    )
    monkeypatch.setattr(
        "vsa.syllable_dict_check.find_mvsa_dictionary_syllable_issues",
        lambda _t: [
            DictSyllableFinding(
                code=CODE_UNKNOWN,
                surface="ge-nee-st",
                expected=None,
                line=2,
                column=4,
                message_nl="onbekend",
                hint_nl="",
            )
        ],
    )
    monkeypatch.setattr(
        "vsa.syllable_dict_check.prompt_dictionary_fixes",
        lambda *_a, **_k: DictionaryPromptResult(
            replacements=[("ge-nee-st", "ge-neest")],
            aborted=True,
        ),
    )

    rc, text = _mvsa_syllabify_dictionary_gate(path, src)
    assert rc == DICT_PROMPT_ABORT_RC
    assert text == src
    assert path.read_bytes() == before
    capsys.readouterr()


def test_mvsa_validate_abort_does_not_write(
    tmp_path: Path, monkeypatch
) -> None:
    """Esc tijdens validate-dictionary: .mvsa blijft byte-gelijk."""
    from vsa.mvsa_validate import _add_syllable_dictionary_diagnostics
    from vsa.syllable_dict_check import (
        CODE_MISMATCH,
        DictionaryPromptResult,
        DictSyllableFinding,
    )

    path = tmp_path / "lied.mvsa"
    src = (
        "@do F4\n"
        "@mode major\n"
        "@oct S=0\n"
        "\n"
        "L: ge_-nee_-st_ |\n"
        "S: a4  -    /   |\n"
    )
    path.write_text(src, encoding="utf-8")
    before = path.read_bytes()

    monkeypatch.setattr(
        "vsa.syllable_dict_check.is_interactive_stdin", lambda stdin=None: True
    )
    monkeypatch.setattr(
        "vsa.syllable_dict_check.find_mvsa_dictionary_syllable_issues",
        lambda _t: [
            DictSyllableFinding(
                code=CODE_MISMATCH,
                surface="ge-nee-st",
                expected="ge-neest",
                line=5,
                column=4,
                message_nl="mismatch",
                hint_nl="",
            )
        ],
    )
    monkeypatch.setattr(
        "vsa.syllable_dict_check.prompt_dictionary_fixes",
        lambda *_a, **_k: DictionaryPromptResult(
            replacements=[("ge-nee-st", "ge-neest")],
            aborted=True,
        ),
    )

    diagnostics: list = []
    _add_syllable_dictionary_diagnostics(src, diagnostics, path=path)
    assert path.read_bytes() == before
    assert any(d.code == "VSA-SYLLABLE-DICT-ABORTED" for d in diagnostics)


def _cli_unsyllabified_mvsa() -> str:
    """Mini-.mvsa waarvan recite nog soft ``-`` mist (CLI-loggingtests)."""
    return _mini_mvsa("(Leerlingen toonde) heer_ |", "a4                 -    |")


def test_cli_dry_run_stdout(tmp_path: Path, capsys) -> None:
    from vsa.cli_mvsa import main as mvsa_main

    path = tmp_path / "voorbeeld.mvsa"
    path.write_text(_cli_unsyllabified_mvsa(), encoding="utf-8")
    assert mvsa_main(["syllabify", str(path), "--dry-run", "--no-align"]) == 0
    out = capsys.readouterr()
    assert "Leer-lin-gen" in out.out or "toon-de" in out.out
    assert "dry-run" in out.err
    assert "Leerlingen" in path.read_text(encoding="utf-8")


def test_cli_default_summary_without_verbose(tmp_path: Path, capsys) -> None:
    from vsa.cli_mvsa import main as mvsa_main

    path = tmp_path / "voorbeeld.mvsa"
    path.write_text(_cli_unsyllabified_mvsa(), encoding="utf-8")
    assert mvsa_main(["syllabify", str(path), "--no-align"]) == 0
    assert "Leer-lin-gen" in path.read_text(encoding="utf-8")
    out = capsys.readouterr()
    assert "mvsa syllabify: 1 bestand" in out.out
    assert str(path) not in out.out  # per-file alleen met --verbose


def test_cli_verbose_prints_per_file(tmp_path: Path, capsys) -> None:
    from vsa.cli_mvsa import main as mvsa_main

    path = tmp_path / "voorbeeld.mvsa"
    path.write_text(_cli_unsyllabified_mvsa(), encoding="utf-8")
    assert mvsa_main(
        ["syllabify", str(path), "--in-place", "--verbose", "--no-align"]
    ) == 0
    out = capsys.readouterr()
    assert str(path) in out.out
    assert "lettergreepstreepje" in out.out or "toegevoegd" in out.out


def test_cli_directory_verbose(tmp_path: Path, capsys) -> None:
    from vsa.cli_mvsa import main as mvsa_main

    (tmp_path / "a.mvsa").write_text(
        _mini_mvsa("(Leerlingen) heer_ |", "a4           -    |"),
        encoding="utf-8",
    )
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.mvsa").write_text(
        _mini_mvsa("(toonde) heer_ |", "a4       -    |"),
        encoding="utf-8",
    )
    assert mvsa_main(["syllabify", str(tmp_path), "--no-align"]) == 0
    out = capsys.readouterr().out
    assert "mvsa syllabify: 2 bestand" in out
    assert "a.mvsa" not in out
    assert mvsa_main(
        ["syllabify", str(tmp_path), "--verbose", "--no-align"]
    ) == 0
    verbose_out = capsys.readouterr().out
    assert "a.mvsa" in verbose_out
    assert "b.mvsa" in verbose_out


def test_cli_extension_writes_sibling(tmp_path: Path) -> None:
    from vsa.cli_mvsa import main as mvsa_main

    path = tmp_path / "xyz.mvsa"
    path.write_text(_cli_unsyllabified_mvsa(), encoding="utf-8")
    assert (
        mvsa_main(
            [
                "syllabify",
                str(path),
                "--extension",
                ".syl.mvsa",
                "--no-align",
            ]
        )
        == 0
    )
    sibling = tmp_path / "xyz.syl.mvsa"
    assert sibling.is_file()
    assert "Leer-lin-gen" in sibling.read_text(encoding="utf-8")
    assert "Leerlingen" in path.read_text(encoding="utf-8")
