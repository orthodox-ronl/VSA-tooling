"""vsa format — strofe-layout (docs/formats/vsa-format.md)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vsa.cli import main as vsa_main
from vsa.vsa_format import (
    VsaFormatError,
    format_vsa_body,
    format_vsa_text,
    split_wrap_units,
    visible_budget,
    wrap_text_lines,
)


def test_lines_star_from_newlines():
    body = "eerste frase\ntweede frase\n"
    out = format_vsa_body(body, boundary="star", layout="lines")
    assert out == "eerste frase *\ntweede frase\n"


def test_lines_slash():
    body = "a\nb\nc\n"
    out = format_vsa_body(body, boundary="slash", layout="lines")
    assert out == "a /\nb /\nc\n"


def test_newline_layout_no_markers():
    body = "een *\ntwee *\ndrie\n"
    out = format_vsa_body(body, boundary="newline", layout="lines")
    assert "*" not in out
    assert out == "een\ntwee\ndrie\n"


def test_flow_star():
    body = "a\nb\nc\n"
    out = format_vsa_body(body, boundary="star", layout="flow")
    assert out == "a * b * c\n"


def test_flow_newline_forbidden():
    with pytest.raises(VsaFormatError):
        format_vsa_body("a\nb\n", boundary="newline", layout="flow")


def test_indent_continuation_one_phrase():
    body = "lange frase die\n  doorgaat op wrap\n"
    out = format_vsa_body(body, boundary="star", layout="lines")
    assert out == "lange frase die doorgaat op wrap\n"


def test_preserves_strong_as_double():
    body = "a ** b * c\n"
    out = format_vsa_body(body, boundary="star", layout="lines")
    assert "a **" in out or "a **" in out.replace("  ", " ")
    lines = [ln for ln in out.splitlines() if ln.strip()]
    assert lines[0].endswith("**")
    assert lines[1].endswith("*")
    assert lines[2] == "c"


def test_slash_boundary_maps_strong():
    body = "a ** b\n"
    out = format_vsa_body(body, boundary="slash", layout="lines")
    assert lines_end(out, 0) == "//"
    assert "b" in out.splitlines()[1]


def lines_end(text: str, i: int) -> str:
    ln = text.splitlines()[i]
    if ln.endswith("**"):
        return "**"
    if ln.endswith("//"):
        return "//"
    if ln.endswith("*"):
        return "*"
    if ln.endswith("/"):
        return "/"
    return ""


def test_keeps_yaml_frontmatter():
    text = """\
---
titel: Demo
taal: nl
---
alfa
beta
"""
    result = format_vsa_text(text, boundary="star", layout="lines")
    assert result.changed
    assert result.text.startswith("---\ntitel: Demo")
    assert "alfa *" in result.text
    assert "beta" in result.text


def test_idempotent_star_lines():
    body = "x\ny\n"
    once = format_vsa_body(body, boundary="star", layout="lines")
    twice = format_vsa_body(once, boundary="star", layout="lines")
    assert once == twice


def test_attached_marker_on_punct():
    body = "ge{\\richt_}.* volgende\n"
    out = format_vsa_body(body, boundary="star", layout="lines")
    assert "ge{\\richt_}." in out.splitlines()[0]
    assert out.splitlines()[0].endswith("*")
    assert "volgende" in out


def test_visible_budget_plain_and_soft_hyphen():
    assert visible_budget("Heer") == 4
    assert visible_budget("ont-ferm") == 8  # o n t - f e r m
    assert visible_budget("mede=eeuw") == 9


def test_visible_budget_scope_skips_ehm_elm():
    # Jo + han + nes; EHM/ELM/braces tellen niet.
    assert visible_budget("Jo{+\\han_}{nes}") == 8
    assert visible_budget("{/Heer_}") == 4


def test_visible_budget_height_marker_fixed_two():
    assert visible_budget("[:]") == 2
    assert visible_budget("[Bb4:] Heer") == 2 + 1 + 4


def test_visible_budget_phrase_markers():
    assert visible_budget("*") == 1
    assert visible_budget("**") == 2
    assert visible_budget("ons *") == 3 + 1 + 1


def test_split_wrap_units_keeps_scoped_word():
    assert split_wrap_units("Jo{+\\han_}{nes} en meer") == [
        "Jo{+\\han_}{nes}",
        "en",
        "meer",
    ]


def test_wrap_lines_indent_counts_toward_budget():
    # Indent = 4 meetelt: voortzetting heeft N-4 voor inhoud.
    text = "Heer ontferm U over ons *"
    lines = wrap_text_lines(text, 10)
    assert lines[0] == "Heer"
    assert all(ln.startswith("    ") for ln in lines[1:])
    assert lines[-1].endswith("*")
    for ln in lines[1:]:
        # Soft: alleen-oversized woord mag over N; anders ≤ N.
        content = ln[4:]
        units = content.split()
        if len(units) == 1 and visible_budget(units[0]) + 4 > 10:
            continue
        assert visible_budget(ln) <= 10 or ln.rstrip().endswith("*")
    joined = " ".join(ln.strip() for ln in lines)
    assert joined == text


def test_wrap_marker_never_alone_on_line():
    # Forceer situatie waarin * anders alleen op nieuwe regel zou komen.
    text = "abcd efgh *"
    lines = wrap_text_lines(text, 8)
    assert not any(ln.strip() in {"*", "**", "/", "//"} for ln in lines)
    assert lines[-1].rstrip().endswith("*")


def test_format_wrap_lines_star():
    body = "Heer ontferm U over ons\n"
    out = format_vsa_body(body, boundary="star", layout="lines", wrap=10)
    lines = out.splitlines()
    assert lines[0] == "Heer"
    assert lines[1].startswith("    ")
    assert "ontferm" in lines[1]


def test_format_wrap_zero_unchanged_shape():
    body = "alfa\nbeta\n"
    out = format_vsa_body(body, boundary="star", layout="lines", wrap=0)
    assert out == "alfa *\nbeta\n"


def test_format_wrap_flow():
    body = "een twee drie vier vijf zes\n"
    out = format_vsa_body(body, boundary="star", layout="flow", wrap=12)
    lines = [ln for ln in out.splitlines() if ln.strip()]
    assert len(lines) >= 2
    assert lines[1].startswith("    ")


def test_format_wrap_oversized_unit_own_line():
    body = "supercalifragilistic\n"
    out = format_vsa_body(body, boundary="star", layout="lines", wrap=5)
    assert out.strip() == "supercalifragilistic"


def test_format_wrap_idempotent():
    body = "Heer ontferm U over ons en heel de wereld\n"
    once = format_vsa_body(body, boundary="star", layout="lines", wrap=15)
    twice = format_vsa_body(once, boundary="star", layout="lines", wrap=15)
    assert once == twice


def test_wrap_negative_rejected():
    with pytest.raises(VsaFormatError):
        format_vsa_body("a\n", wrap=-1)


def test_wrap_too_small_rejected():
    with pytest.raises(VsaFormatError):
        format_vsa_body("a\n", wrap=3)


def test_cli_dry_run_prints_result_no_write(tmp_path: Path, capsys):
    path = tmp_path / "lied.vsa"
    original = "alfa\nbeta\n"
    path.write_text(original, encoding="utf-8")
    assert vsa_main(["format", str(path), "--dry-run"]) == 0
    captured = capsys.readouterr()
    assert "alfa *" in captured.out
    assert "beta" in captured.out
    assert "dry-run" in captured.err
    assert path.read_text(encoding="utf-8") == original


def test_cli_dry_run_rejects_check_and_output(tmp_path: Path):
    path = tmp_path / "lied.vsa"
    path.write_text("a\nb\n", encoding="utf-8")
    assert vsa_main(["format", str(path), "--dry-run", "--check"]) == 1
    assert (
        vsa_main(
            ["format", str(path), "--dry-run", "-o", str(tmp_path / "out.vsa")]
        )
        == 1
    )


def test_cli_format_accepts_catalogus_id(monkeypatch, capsys):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(root)
    code = vsa_main(
        ["format", "communievers/kruisverheffing/hemelum", "--dry-run"]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "dry-run" in captured.err
    assert "[//:]" in captured.out or "Heer" in captured.out
