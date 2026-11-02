"""Atomisch schrijven/vervangen van bestanden (Windows-hardening).

Op Windows kan ``open(bestaand, \"w\")`` of ``os.replace`` soms falen met
``[Errno 22] Invalid argument`` of Access Denied (WinError 5/32) terwijl
het pad geldig is (vergrendelde of “vastzittende” sibling: MuseScore,
viewer, Defender). Schrijf daarom eerst naar een nieuw temp-bestand
naast de bestemming en vervang; bij tijdelijke lock: kort wachten en
opnieuw; bij EINVAL: bestemming wissen en opnieuw vervangen.
"""

from __future__ import annotations

import errno
import os
import tempfile
import time
from pathlib import Path

_REPLACE_RETRIES = 8
_REPLACE_PAUSE_S = 0.05


def _is_einval(exc: BaseException) -> bool:
    return isinstance(exc, OSError) and exc.errno == errno.EINVAL


def _is_transient_lock(exc: BaseException) -> bool:
    """True bij tijdelijke Windows-vergrendeling tijdens replace."""
    if isinstance(exc, PermissionError):
        return True
    if not isinstance(exc, OSError):
        return False
    win = getattr(exc, "winerror", None)
    if win in {5, 32, 1224}:
        return True
    return exc.errno in {errno.EACCES, errno.EPERM, errno.EINVAL}


def replace_into(dest: Path, src: Path) -> None:
    """Verplaats *src* naar *dest* (overschrijven); retry bij lock/EINVAL."""
    dest = Path(dest)
    src = Path(src)
    last: OSError | None = None
    for attempt in range(_REPLACE_RETRIES):
        try:
            os.replace(src, dest)
            return
        except OSError as exc:
            last = exc
            if not _is_transient_lock(exc):
                raise
            if _is_einval(exc):
                dest.unlink(missing_ok=True)
            time.sleep(_REPLACE_PAUSE_S * (attempt + 1))
    assert last is not None
    raise last


def write_bytes(path: Path, data: bytes) -> None:
    """Schrijf *data* atomisch naar *path*."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        tmp_path.write_bytes(data)
        replace_into(path, tmp_path)
        tmp_path = Path()
    finally:
        if tmp_path.is_file():
            tmp_path.unlink(missing_ok=True)


def write_text(
    path: Path,
    text: str,
    *,
    encoding: str = "utf-8",
    newline: str | None = "\n",
) -> None:
    """Schrijf tekst atomisch (zelfde kwargs-idee als ``Path.write_text``)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        tmp_path.write_text(text, encoding=encoding, newline=newline)
        replace_into(path, tmp_path)
        tmp_path = Path()
    finally:
        if tmp_path.is_file():
            tmp_path.unlink(missing_ok=True)
