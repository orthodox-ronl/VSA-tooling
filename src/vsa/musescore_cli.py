"""Locate MuseScore and convert scores via its CLI.

MuseScore-conversies lopen **één tegelijk** (thread- én procesbreed lock):
twee CLI-runs tegelijk vergrendelen elkaars ``.mscz``/SVG’s op Windows
(Access Denied). Andere processen die deze module gebruiken, wachten
tot de vorige conversie klaar is.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

_SVG_PAGE_INDEX_RE = re.compile(r"-(\d+)\.svg$", re.IGNORECASE)


def _musescore_page_svgs(dest: Path) -> list[Path]:
    """Alleen ``{stem}-1.svg`` / ``{stem}-2.svg`` …, niet ``{stem}-nls.svg``.

    Nodig omdat ``lied.mvsa.translit.svg`` als stem ``….translit`` heeft;
    een brede glob ``….translit-*.svg`` zou anders
    ``….translit-nls.svg`` / ``….translit-ksl.svg`` wissen of meenemen.
    """
    dest = Path(dest)
    prefix = f"{dest.stem}-"
    out: list[Path] = []
    for path in dest.parent.glob(f"{dest.stem}-*.svg"):
        rest = path.name[len(prefix) : -len(path.suffix)]
        if rest.isdigit():
            out.append(path)
    return sorted(out, key=_svg_page_index)

MUSESCORE_CANDIDATES = (
    Path(r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"),
    Path(r"C:\Program Files\MuseScore 3\bin\MuseScore3.exe"),
)

# Eén MuseScore-CLI tegelijk (ook over processen heen).
_THREAD_LOCK = threading.Lock()
_LOCK_PATH = Path(tempfile.gettempdir()) / "vsa-musescore-cli.lock"
_LOCK_WAIT_S = 0.25
_LOCK_STALE_S = 2 * 60 * 60  # 2 uur: wees-lock na crash


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


def _try_acquire_lockfile() -> int | None:
    """Open lockfile exclusief; return fd of ``None`` als bezet."""
    flags = os.O_CREAT | os.O_EXCL | os.O_RDWR
    try:
        return os.open(str(_LOCK_PATH), flags)
    except FileExistsError:
        return None
    except OSError:
        return None


def _release_lockfile(fd: int) -> None:
    try:
        os.close(fd)
    finally:
        try:
            _LOCK_PATH.unlink(missing_ok=True)
        except OSError:
            pass


def _lock_holder_alive() -> bool:
    """True als de pid in het lockbestand nog bestaat."""
    try:
        text = _LOCK_PATH.read_text(encoding="ascii", errors="replace").strip()
    except OSError:
        return False
    first = (text.splitlines() or [""])[0].strip()
    if not first.isdigit():
        return False
    pid = int(first)
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _lock_is_stale() -> bool:
    """Wees-lock: houder-pid dood, of ouder dan ``_LOCK_STALE_S``."""
    if not _LOCK_PATH.is_file():
        return False
    if not _lock_holder_alive():
        return True
    try:
        age = time.time() - _LOCK_PATH.stat().st_mtime
    except OSError:
        return False
    return age >= _LOCK_STALE_S


def _unlink_with_retry(path: Path, *, attempts: int = 8) -> None:
    """``unlink`` met korte retries bij Windows Access Denied."""
    path = Path(path)
    last: OSError | None = None
    for attempt in range(max(1, attempts)):
        try:
            path.unlink(missing_ok=True)
            return
        except OSError as exc:
            last = exc
            time.sleep(0.05 * (attempt + 1))
    assert last is not None
    raise last


@contextmanager
def musescore_exclusive() -> Iterator[None]:
    """Wacht tot deze thread/proces exclusief MuseScore mag starten."""
    with _THREAD_LOCK:
        fd: int | None = None
        while True:
            fd = _try_acquire_lockfile()
            if fd is not None:
                break
            if _lock_is_stale():
                try:
                    _LOCK_PATH.unlink(missing_ok=True)
                except OSError:
                    pass
                continue
            time.sleep(_LOCK_WAIT_S)
        try:
            # Pid in lockfile helpt bij diagnose; geen harde eis.
            try:
                os.write(fd, f"{os.getpid()}\n".encode("ascii", errors="replace"))
            except OSError:
                pass
            yield
        finally:
            _release_lockfile(fd)


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

    Start nooit een tweede MuseScore-CLI zolang een andere conversie via
    deze module nog loopt (zie :func:`musescore_exclusive`).
    """
    exe = require_musescore(override=musescore)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with musescore_exclusive():
        _unlink_with_retry(dest)
        # MuseScore SVG: wis oude pagina-bestanden (stem-1.svg, …) — niet
        # translit-nls/ksl-siblings van een ``….translit.svg``-doel.
        if dest.suffix.lower() == ".svg":
            for stale in _musescore_page_svgs(dest):
                _unlink_with_retry(stale)
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
            pages = _resolve_musescore_svg_pages(dest)
            if pages:
                return pages[0]
        if not dest.is_file():
            detail = (proc.stderr or proc.stdout or "").strip()
            msg = f"MuseScore schreef geen {dest} (exit {proc.returncode})"
            if detail:
                msg = f"{msg}: {detail[:500]}"
            raise MuseScoreConvertError(msg)
        return dest


def _svg_page_index(path: Path) -> int:
    match = _SVG_PAGE_INDEX_RE.search(path.name)
    return int(match.group(1)) if match else 0


def list_musescore_svg_pages(dest: Path) -> list[Path]:
    """Return MuseScore page SVGs for ``dest`` stem (``stem-1.svg``, …)."""
    return _musescore_page_svgs(dest)


def _resolve_musescore_svg_pages(dest: Path) -> list[Path]:
    """Fold MuseScore ``name-1.svg`` into ``name.svg``, or keep a bladreeks.

    One page → rename to the requested ``dest``. Several pages → leave
    ``dest.stem-1.svg`` … ``dest.stem-N.svg`` (print blad-SVG’s; see
    ``docs/plans/kale-muziek-svg-en-uitgaven.md``).
    """
    pages = list_musescore_svg_pages(dest)
    if not pages:
        return []
    if len(pages) == 1:
        from .atomic_io import replace_into

        replace_into(dest, pages[0])
        return [dest]
    return pages
