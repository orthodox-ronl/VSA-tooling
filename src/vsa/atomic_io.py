"""Atomisch schrijven/vervangen van bestanden (Windows EINVAL-hardening).

Op Windows kan ``open(bestaand, \"w\")`` of ``os.replace`` soms falen met
``[Errno 22] Invalid argument`` terwijl het pad geldig is (vergrendelde of
“vastzittende” sibling). Schrijf daarom eerst naar een nieuw temp-bestand
naast de bestemming en vervang; bij EINVAL: bestemming wissen en opnieuw
vervangen.
"""

from __future__ import annotations

import errno
import os
import tempfile
from pathlib import Path


def _is_einval(exc: BaseException) -> bool:
    return isinstance(exc, OSError) and exc.errno == errno.EINVAL


def replace_into(dest: Path, src: Path) -> None:
    """Verplaats *src* naar *dest* (overschrijven); retry na unlink bij EINVAL."""
    dest = Path(dest)
    src = Path(src)
    try:
        os.replace(src, dest)
        return
    except OSError as exc:
        if not _is_einval(exc):
            raise
    dest.unlink(missing_ok=True)
    os.replace(src, dest)


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
