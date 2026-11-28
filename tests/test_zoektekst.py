"""Zoektekst: normaliseren, checken, schrijven, CLI."""

from __future__ import annotations

from pathlib import Path

from vsa.cli import main as vsa_main
from vsa.cli_mvsa import main as mvsa_main
from vsa.zoektekst import (
    apply_zoektekst,
    check_zoektekst,
    expected_zoektekst,
    normalize_zoektekst,
)

_MVSA = """\
@do F4
@mode major

L: Hei_ li_ ge_ ||
S: do   re   mi ||
A: la-  ti-  do ||
T: fa-  so-  la- ||
B: do-  re-  mi- ||
"""

_VSA = """\
---
identificatie:
  title: Test
---
[:] Hei-li{/ge} Ni-ko-laas ||
"""


def test_normalize_collapses_whitespace() -> None:
    assert normalize_zoektekst("  a\n\tb  c  ") == "a b c"


def test_zoektekst_splits_on_star_glued_to_period() -> None:
    """Zoektekst volgt dezelfde `*`/`/`-frasescheiding als extract (ook ``.*``)."""
    src = (
        "---\n"
        "titel: Test\n"
        "---\n"
        "\n"
        "[:] eerste zin ge{\\richt_}.*\n"
        "tweede zin hier [:]\n"
    )
    text = expected_zoektekst(src, kind="vsa")
    lines = text.splitlines()
    assert len(lines) >= 2
    assert lines[0].endswith("gericht.")
    assert "*" not in text
    assert any(ln.startswith("tweede") for ln in lines)


def test_apply_writes_phrase_lines_literal() -> None:
    src = (
        "---\n"
        "titel: Test\n"
        "---\n"
        "\n"
        "[:] Eerste frase hier *\n"
        "tweede frase daar *\n"
        "derde frase slot [:]\n"
    )
    result = apply_zoektekst(src, kind="vsa")
    assert result.changed
    assert "zoektekst: |" in result.text or "zoektekst:|-" in result.text.replace(
        " ", ""
    )
    # Frases op eigen regels in het literal-blok
    fm = result.text.split("---", 2)[1]
    assert "Eerste frase hier" in fm
    assert "\n  tweede frase daar\n" in fm or "\n tweede frase daar\n" in fm
    assert check_zoektekst(result.text, kind="vsa", require=True) == []
    again = apply_zoektekst(result.text, kind="vsa")
    assert not again.changed


def test_check_missing_on_mvsa() -> None:
    issues = check_zoektekst(_MVSA, kind="mvsa", require=True)
    assert [i.code for i in issues] == ["ZOEKTEKST-MISSING"]


def test_check_ok_without_require_when_missing() -> None:
    assert check_zoektekst(_MVSA, kind="mvsa", require=False) == []


def test_apply_and_check_mvsa_roundtrip() -> None:
    result = apply_zoektekst(_MVSA, kind="mvsa")
    assert result.changed
    assert "zoektekst:" in result.text
    assert result.text.startswith("---\n")
    assert check_zoektekst(result.text, kind="mvsa", require=True) == []
    again = apply_zoektekst(result.text, kind="mvsa")
    assert not again.changed


def test_apply_updates_mismatch() -> None:
    wrong = (
        "---\n"
        "zoektekst: Helemaal fout\n"
        "---\n"
        "\n"
        f"{_MVSA}"
    )
    issues = check_zoektekst(wrong, kind="mvsa", require=True)
    assert issues[0].code == "ZOEKTEKST-MISMATCH"
    fixed = apply_zoektekst(wrong, kind="mvsa")
    assert fixed.changed
    assert check_zoektekst(fixed.text, kind="mvsa", require=True) == []
    assert "Helemaal fout" not in fixed.text


def test_apply_preserves_other_frontmatter_keys() -> None:
    src = (
        "---\n"
        "identificatie:\n"
        "  title: Antifoon\n"
        "---\n"
        "\n"
        f"{_MVSA}"
    )
    out = apply_zoektekst(src, kind="mvsa").text
    assert "title: Antifoon" in out or "title: Antifoon" in out.replace('"', "")
    meta_title_ok = "Antifoon" in out and "zoektekst:" in out
    assert meta_title_ok


def test_apply_vsa_with_existing_frontmatter() -> None:
    result = apply_zoektekst(_VSA, kind="vsa")
    assert result.changed
    assert "zoektekst:" in result.text
    assert "identificatie:" in result.text or "title:" in result.text
    assert check_zoektekst(result.text, kind="vsa", require=True) == []
    # Body-extractie blijft bruikbaar
    assert expected_zoektekst(result.text, kind="vsa")


def test_cli_check_and_write(tmp_path: Path) -> None:
    path = tmp_path / "lied.mvsa"
    path.write_text(_MVSA, encoding="utf-8")
    assert vsa_main(["zoektekst", str(path), "--check"]) == 1
    assert vsa_main(["zoektekst", str(path)]) == 0
    text = path.read_text(encoding="utf-8")
    assert "zoektekst:" in text
    assert vsa_main(["zoektekst", str(path), "--check"]) == 0


def test_cli_mvsa_validate_require_zoektekst(tmp_path: Path) -> None:
    path = tmp_path / "lied.mvsa"
    path.write_text(_MVSA, encoding="utf-8")
    assert mvsa_main(["validate", str(path)]) == 0
    assert mvsa_main(["validate", str(path), "--require-zoektekst"]) == 1
    assert vsa_main(["zoektekst", str(path)]) == 0
    assert mvsa_main(["validate", str(path), "--require-zoektekst"]) == 0
