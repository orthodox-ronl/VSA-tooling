"""Unit/CLI tests for mscz normalize (layout on existing .mscz)."""

from __future__ import annotations

import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from vsa.cli_mscz import main as mscz_main
from vsa.mscz_layout import MsczLayoutError, normalize_mscz_path


def _minimal_mscz(path: Path) -> Path:
    mscx = (
        '<?xml version="1.0"?>'
        "<museScore><Score><Style>"
        "<pageWidth>1</pageWidth>"
        "</Style>"
        "<Part><longName>Soprano</longName></Part>"
        "</Score></museScore>"
    )
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(f"{path.stem}.mscx", mscx)
    return path


def test_normalize_mscz_path_plain_copy(tmp_path: Path) -> None:
    src = _minimal_mscz(tmp_path / "lied.mscz")
    dest = tmp_path / "out.mscz"
    written, profile = normalize_mscz_path(src, dest, layout="plain")
    assert written == dest
    assert profile == "plain"
    assert dest.is_file()
    assert dest.read_bytes() == src.read_bytes()


def test_normalize_mscz_path_rejects_style_with_plain(tmp_path: Path) -> None:
    src = _minimal_mscz(tmp_path / "lied.mscz")
    with pytest.raises(MsczLayoutError, match="plain"):
        normalize_mscz_path(
            src,
            layout="plain",
            style_overrides={"minSystemDistance": "4"},
        )


def test_normalize_mscz_path_wrong_suffix(tmp_path: Path) -> None:
    bad = tmp_path / "lied.mxl"
    bad.write_text("<score/>", encoding="utf-8")
    with pytest.raises(MsczLayoutError, match=r"\.mscz"):
        normalize_mscz_path(bad)


def test_mscz_normalize_cli_plain(tmp_path: Path, capsys) -> None:
    src = _minimal_mscz(tmp_path / "lied.mscz")
    out = tmp_path / "norm.mscz"
    assert mscz_main(["normalize", str(src), "-o", str(out), "--layout", "plain"]) == 0
    assert out.is_file()
    printed = capsys.readouterr().out
    assert "Geschreven:" in printed
    assert "layout plain" in printed


def test_mscz_normalize_cli_calls_layout(tmp_path: Path) -> None:
    src = _minimal_mscz(tmp_path / "lied.mscz")
    with patch(
        "vsa.mscz_layout.apply_mscz_layout_profile",
        return_value="partituur",
    ) as mocked:
        assert mscz_main(["normalize", str(src), "--layout", "partituur"]) == 0
    mocked.assert_called_once()
    assert mocked.call_args.args[0] == src
    assert mocked.call_args.kwargs["layout"] == "partituur"


def test_mscz_normalize_cli_rejects_style_on_plain(tmp_path: Path, capsys) -> None:
    src = _minimal_mscz(tmp_path / "lied.mscz")
    rc = mscz_main(
        [
            "normalize",
            str(src),
            "--layout",
            "plain",
            "--min-system-distance",
            "4",
        ]
    )
    assert rc == 1
    assert "plain" in capsys.readouterr().err
