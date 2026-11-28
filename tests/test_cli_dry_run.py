"""Tests voor gedeelde same-type ``--dry-run`` / ``--verbose``."""

from __future__ import annotations

from pathlib import Path

from vsa.cli_dry_run import (
    content_would_change,
    format_bounded_unified_diff,
    report_would_write,
)


def test_content_would_change_new_and_same() -> None:
    assert content_would_change(None, "a\n") is True
    assert content_would_change("a\n", "a\n") is False
    assert content_would_change("a\r\n", "a\n") is False
    assert content_would_change("a\n", "b\n") is True


def test_format_bounded_unified_diff_truncates() -> None:
    old = "\n".join(f"line-{i}" for i in range(200)) + "\n"
    new = "\n".join(f"line-{i}-x" for i in range(200)) + "\n"
    text = format_bounded_unified_diff(
        old, new, from_label="a.mvsa", to_label="a.mvsa", max_lines=20
    )
    assert "a.mvsa" in text
    assert "weggelaten" in text


def test_report_would_write_dry_run(capsys, tmp_path: Path) -> None:
    target = tmp_path / "out.mvsa"
    assert report_would_write(
        target, None, "nieuw\n", dry_run=True, verbose=False
    )
    out = capsys.readouterr().out
    assert "would write:" in out
    assert not target.exists()


def test_mvsa_normalize_dry_run_lists_target(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from vsa.cli import _cmd_mvsa_normalize

    src = tmp_path / "lied.mvsa"
    src.write_text(
        "@do F4\n@mode major\n@oct S=0\n\nL: a_ |\nS: a4  |\n",
        encoding="utf-8",
    )

    class Args:
        path = str(src)
        output = None
        pitch = "preserve"
        octave_style = "@oct"
        no_align = False
        dry_run = True
        verbose = False
        config = None

    # _cli_collect_sources needs real path resolution from cwd — use absolute.
    monkeypatch.chdir(tmp_path)
    rc = _cmd_mvsa_normalize(Args())
    assert rc == 0
    captured = capsys.readouterr().out
    assert "would write:" in captured
    assert "normalized.mvsa" in captured
    assert "dry-run:" in captured
    assert not (tmp_path / "lied.normalized.mvsa").exists()


def test_mvsa_kuiser_dry_run_does_not_write(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from vsa.cli import _cmd_mvsa_kuiser

    src = tmp_path / "lied.mvsa"
    # Minimaal geldig; kuiser mag wijzigen of ok zijn.
    src.write_text(
        "@do F4\n@mode major\n@oct S=0\n\nL: a_ |\nS: a4  |\n",
        encoding="utf-8",
    )
    before = src.read_bytes()

    class Args:
        paths = [str(src)]
        output = None
        check = False
        dry_run = True
        verbose = False
        pitch = "preserve"
        octave_style = "@oct"
        no_align = False
        werkbank = False

    monkeypatch.chdir(tmp_path)
    rc = _cmd_mvsa_kuiser(Args())
    assert rc == 0
    assert src.read_bytes() == before
    out = capsys.readouterr().out
    assert "dry-run:" in out
