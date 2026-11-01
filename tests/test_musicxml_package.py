"""Tests voor MusicXML/MXL-schrijven (o.a. Windows EINVAL-hardening)."""

from __future__ import annotations

import errno
import zipfile
from pathlib import Path
from unittest.mock import patch

from vsa.musicxml_package import write_musicxml_output

_MINIMAL = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<score-partwise version="3.1"><part-list/></score-partwise>'
)


def test_write_mxl_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "lied.mxl"
    write_musicxml_output(path, _MINIMAL)
    assert zipfile.is_zipfile(path)
    with zipfile.ZipFile(path) as archive:
        assert "score.xml" in archive.namelist()
        assert _MINIMAL in archive.read("score.xml").decode("utf-8")


def test_write_mxl_overwrites_existing(tmp_path: Path) -> None:
    path = tmp_path / "lied.mxl"
    write_musicxml_output(path, _MINIMAL)
    write_musicxml_output(path, _MINIMAL.replace("3.1", "4.0"))
    with zipfile.ZipFile(path) as archive:
        assert "4.0" in archive.read("score.xml").decode("utf-8")


def test_replace_retries_after_einval(tmp_path: Path) -> None:
    path = tmp_path / "stuck.mxl"
    path.write_bytes(b"old")
    calls = {"n": 0}
    real_replace = __import__("os").replace

    def flaky_replace(src: str | Path, dst: str | Path) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError(errno.EINVAL, "Invalid argument", str(dst))
        real_replace(src, dst)

    with patch("vsa.atomic_io.os.replace", side_effect=flaky_replace):
        write_musicxml_output(path, _MINIMAL)
    assert calls["n"] == 2
    assert zipfile.is_zipfile(path)


def test_write_musicxml_plain(tmp_path: Path) -> None:
    path = tmp_path / "lied.musicxml"
    write_musicxml_output(path, _MINIMAL)
    assert path.read_text(encoding="utf-8") == _MINIMAL
