"""Write MusicXML output as plain XML (``.musicxml``) or compressed MXL (``.mxl``)."""

from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path

from .atomic_io import replace_into, write_bytes

_MXL_CONTAINER = """\
<?xml version="1.0" encoding="UTF-8"?>
<container>
  <rootfiles>
    <rootfile full-path="score.xml"/>
  </rootfiles>
</container>
"""

_MXL_SUFFIX = ".mxl"
_MUSICXML_SUFFIX = ".musicxml"

_KNOWN_SUFFIXES = frozenset({_MXL_SUFFIX, _MUSICXML_SUFFIX, ".xml"})


def musicxml_output_suffix(*, format_name: str | None = None, path: Path | None = None) -> str:
    """Return ``.mxl`` (default) or ``.musicxml`` from *format_name* or *path*."""
    if path is not None:
        suffix = path.suffix.lower()
        if suffix == _MXL_SUFFIX:
            return _MXL_SUFFIX
        if suffix in (_MUSICXML_SUFFIX, ".xml"):
            return _MUSICXML_SUFFIX
    if format_name == "musicxml":
        return _MUSICXML_SUFFIX
    return _MXL_SUFFIX


def write_musicxml_output(path: Path, xml: str) -> None:
    """Write *xml* to *path* as ``.musicxml`` or ``.mxl`` (ZIP with ``score.xml``).

    Uses sibling temp + replace (see ``atomic_io``) against Windows EINVAL.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == _MXL_SUFFIX:
        _write_mxl(path, xml)
    else:
        write_bytes(path, xml.encode("utf-8"))


def _write_mxl(path: Path, xml: str) -> None:
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("META-INF/container.xml", _MXL_CONTAINER)
            archive.writestr("score.xml", xml)
        replace_into(path, tmp_path)
        tmp_path = Path()
    finally:
        if tmp_path.is_file():
            tmp_path.unlink(missing_ok=True)
