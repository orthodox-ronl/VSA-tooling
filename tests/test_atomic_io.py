"""Tests voor atomic_io (Windows EINVAL-hardening)."""

from __future__ import annotations

import errno
from pathlib import Path
from unittest.mock import patch

from vsa.atomic_io import replace_into, write_text


def test_write_text_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "a.txt"
    write_text(path, "hallo\n", encoding="utf-8", newline="\n")
    assert path.read_text(encoding="utf-8") == "hallo\n"
    write_text(path, "twee\n", encoding="utf-8", newline="\n")
    assert path.read_text(encoding="utf-8") == "twee\n"


def test_replace_into_retries_einval(tmp_path: Path) -> None:
    dest = tmp_path / "dest.bin"
    src = tmp_path / "src.bin"
    dest.write_bytes(b"old")
    src.write_bytes(b"new")
    calls = {"n": 0}
    real_replace = __import__("os").replace

    def flaky(a: str | Path, b: str | Path) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError(errno.EINVAL, "Invalid argument", str(b))
        real_replace(a, b)

    with patch("vsa.atomic_io.os.replace", side_effect=flaky):
        replace_into(dest, src)
    assert calls["n"] == 2
    assert dest.read_bytes() == b"new"
    assert not src.exists()
