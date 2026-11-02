"""Tests voor MuseScore-CLI exclusieve lock (geen echte MuseScore)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vsa import musescore_cli as ms


def test_musescore_exclusive_blocks_second_holder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lock = tmp_path / "vsa-musescore-cli.lock"
    monkeypatch.setattr(ms, "_LOCK_PATH", lock)
    monkeypatch.setattr(ms, "_LOCK_WAIT_S", 0.01)

    order: list[str] = []

    with ms.musescore_exclusive():
        order.append("outer-enter")
        assert lock.is_file()
        # Tweede acquire faalt zolang de eerste lock bestaat.
        assert ms._try_acquire_lockfile() is None
        order.append("outer-hold")
    order.append("outer-exit")
    assert not lock.exists()

    with ms.musescore_exclusive():
        order.append("second")
    assert order == ["outer-enter", "outer-hold", "outer-exit", "second"]


def test_musescore_exclusive_clears_stale_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lock = tmp_path / "vsa-musescore-cli.lock"
    lock.write_text("99999\n", encoding="utf-8")
    # Maak mtime oud genoeg voor stale.
    old = 0.0
    os.utime(lock, (old, old))
    monkeypatch.setattr(ms, "_LOCK_PATH", lock)
    monkeypatch.setattr(ms, "_LOCK_STALE_S", 1.0)
    monkeypatch.setattr(ms, "_LOCK_WAIT_S", 0.01)

    with ms.musescore_exclusive():
        assert lock.is_file()
        assert lock.read_text(encoding="utf-8").strip() == str(os.getpid())
    assert not lock.exists()


def test_convert_uses_exclusive_and_subprocess(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lock = tmp_path / "vsa-musescore-cli.lock"
    monkeypatch.setattr(ms, "_LOCK_PATH", lock)
    source = tmp_path / "in.mscz"
    dest = tmp_path / "out.pdf"
    source.write_bytes(b"PK")
    exe = tmp_path / "MuseScore4.exe"
    exe.write_text("", encoding="utf-8")

    def fake_run(cmd, **_kwargs):  # noqa: ANN001
        assert lock.is_file()  # lock vast tijdens subprocess
        dest.write_bytes(b"%PDF")
        proc = MagicMock()
        proc.returncode = 0
        proc.stderr = ""
        proc.stdout = ""
        return proc

    with patch("vsa.musescore_cli.subprocess.run", side_effect=fake_run):
        out = ms.convert_with_musescore(source, dest, musescore=exe)
    assert out == dest
    assert dest.read_bytes() == b"%PDF"
    assert not lock.exists()
