"""Locate MuseScore and convert scores via its CLI."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

MUSESCORE_CANDIDATES = (
    Path(r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"),
    Path(r"C:\Program Files\MuseScore 3\bin\MuseScore3.exe"),
)


class MuseScoreNotFoundError(RuntimeError):
    """Raised when no MuseScore executable can be resolved."""


class MuseScoreConvertError(RuntimeError):
    """Raised when MuseScore CLI conversion fails."""


def find_musescore() -> Path | None:
    """Return MuseScore binary path, or ``None`` if not found."""
    which = shutil.which("MuseScore4") or shutil.which("mscore") or shutil.which(
        "MuseScore3"
    )
    if which:
        return Path(which)
    for path in MUSESCORE_CANDIDATES:
        if path.is_file():
            return path
    return None


def require_musescore(*, override: Path | None = None) -> Path:
    """Return MuseScore path or raise :class:`MuseScoreNotFoundError`."""
    if override is not None:
        path = Path(override)
        if not path.is_file():
            raise MuseScoreNotFoundError(f"MuseScore niet gevonden: {path}")
        return path
    found = find_musescore()
    if found is None:
        raise MuseScoreNotFoundError(
            "MuseScore niet gevonden. Installeer MuseScore 4, of geef "
            "--musescore PATH. Gezocht: PATH (MuseScore4/mscore) en "
            r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"
        )
    return found


def convert_with_musescore(
    source: Path,
    dest: Path,
    *,
    musescore: Path | None = None,
) -> Path:
    """Convert ``source`` to ``dest`` via MuseScore CLI (``-f -o``).

    Typical: ``.mxl`` / ``.musicxml`` → ``.mscz``, or ``.mscz`` → ``.pdf``.
    """
    exe = require_musescore(override=musescore)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    try:
        proc = subprocess.run(
            [str(exe), "-f", "-o", str(dest), str(source)],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise MuseScoreConvertError(f"MuseScore starten mislukt: {exc}") from exc
    if proc.returncode != 0 or not dest.is_file():
        detail = (proc.stderr or proc.stdout or "").strip()
        msg = f"MuseScore schreef geen {dest} (exit {proc.returncode})"
        if detail:
            msg = f"{msg}: {detail[:500]}"
        raise MuseScoreConvertError(msg)
    return dest
