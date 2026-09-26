"""Export .mvsa to MuseScore .mscz via MusicXML intermediate (draft-v0).

Chain: ``.mvsa`` → ``.mxl`` (playback MusicXML) → MuseScore CLI → ``.mscz``.
Native MSCX writing is out of scope for this slice; see
``docs/plans/mvsa-conversions.md``.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .musescore_cli import (
    MuseScoreConvertError,
    MuseScoreNotFoundError,
    convert_with_musescore,
    require_musescore,
)
from .mvsa_musicxml import MvsaExportError, export_mvsa_path
from .mvsa_validate import MvsaValidationError

__all__ = [
    "MvsaMsczError",
    "export_mvsa_to_mscz",
    "MuseScoreConvertError",
    "MuseScoreNotFoundError",
]


class MvsaMsczError(Exception):
    """MSCZ export failed (validation, MusicXML, or MuseScore)."""


def export_mvsa_to_mscz(
    path: Path,
    out: Path,
    *,
    section_id: str | None = None,
    musescore: Path | None = None,
    keep_mxl: Path | None = None,
) -> Path:
    """Export ``path`` (.mvsa) to ``out`` (.mscz).

    Writes an intermediate ``.mxl`` (temp, or ``keep_mxl`` if given), then
    converts with MuseScore. Returns ``out``.
    """
    path = Path(path)
    out = Path(out)
    if out.suffix.lower() != ".mscz":
        out = out.with_suffix(".mscz")

    try:
        require_musescore(override=musescore)
    except MuseScoreNotFoundError as exc:
        raise MvsaMsczError(str(exc)) from exc

    tmp_mxl: Path | None = None
    if keep_mxl is not None:
        mxl_path = Path(keep_mxl)
        if mxl_path.suffix.lower() not in {".mxl", ".musicxml", ".xml"}:
            mxl_path = mxl_path.with_suffix(".mxl")
        mxl_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        fd, name = tempfile.mkstemp(suffix=".mxl", prefix="mvsa-")
        # Close handle immediately; Windows needs the file closed for MuseScore.
        os.close(fd)
        tmp_mxl = Path(name)
        mxl_path = tmp_mxl

    try:
        try:
            export_mvsa_path(path, mxl_path, section_id=section_id)
        except (MvsaValidationError, MvsaExportError):
            raise
        except Exception as exc:
            raise MvsaMsczError(f"MusicXML-tussenbestand mislukt: {exc}") from exc

        try:
            convert_with_musescore(mxl_path, out, musescore=musescore)
        except (MuseScoreNotFoundError, MuseScoreConvertError) as exc:
            raise MvsaMsczError(str(exc)) from exc
    finally:
        if tmp_mxl is not None:
            tmp_mxl.unlink(missing_ok=True)

    return out
