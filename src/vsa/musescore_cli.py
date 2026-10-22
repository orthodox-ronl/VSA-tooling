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
    musicxml_infer_text_type: bool = False,
) -> Path:
    """Convert ``source`` to ``dest`` via MuseScore CLI (``-f -o``).

    Typical: ``.mxl`` / ``.musicxml`` → ``.mscz``, or ``.mscz`` → ``.pdf``.

    *musicxml_infer_text_type*: zet MuseScore ``--musicxml-infer-text-type`` aan
    (alleen zinvol bij MusicXML→MSCZ). Dan worden Fine / D.S. / Segno echte
    Marker/Jump met rechtsuitlijning i.p.v. losse StaffText.
    """
    exe = require_musescore(override=musescore)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    # MuseScore SVG: wis eventuele oude pagina-bestanden (stem-1.svg, …).
    if dest.suffix.lower() == ".svg":
        for stale in dest.parent.glob(f"{dest.stem}-*.svg"):
            stale.unlink(missing_ok=True)
    cmd = [str(exe), "-f"]
    if musicxml_infer_text_type:
        cmd.append("--musicxml-infer-text-type")
    cmd.extend(["-o", str(dest), str(source)])
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise MuseScoreConvertError(f"MuseScore starten mislukt: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        msg = f"MuseScore schreef geen {dest} (exit {proc.returncode})"
        if detail:
            msg = f"{msg}: {detail[:500]}"
        raise MuseScoreConvertError(msg)
    if dest.suffix.lower() == ".svg" and not dest.is_file():
        _resolve_musescore_svg_pages(dest)
    if not dest.is_file():
        detail = (proc.stderr or proc.stdout or "").strip()
        msg = f"MuseScore schreef geen {dest} (exit {proc.returncode})"
        if detail:
            msg = f"{msg}: {detail[:500]}"
        raise MuseScoreConvertError(msg)
    return dest


def _resolve_musescore_svg_pages(dest: Path) -> None:
    """MuseScore writes ``name-1.svg`` (etc.); fold into requested ``name.svg``.

    Multiple pages are rejected — use ``--section`` for a single-page SVG.
    """
    pages = sorted(
        dest.parent.glob(f"{dest.stem}-*.svg"),
        key=lambda p: p.name,
    )
    if not pages:
        return
    if len(pages) > 1:
        names = ", ".join(p.name for p in pages)
        for p in pages:
            p.unlink(missing_ok=True)
        raise MuseScoreConvertError(
            f"MuseScore schreef {len(pages)} SVG-pagina's ({names}); "
            "koormap-SVG ondersteunt één pagina — gebruik --section of "
            "verkort het stuk"
        )
    pages[0].replace(dest)
