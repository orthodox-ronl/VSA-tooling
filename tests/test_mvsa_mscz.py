"""Tests for mvsa → MSCZ (via MuseScore CLI)."""

from __future__ import annotations

import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from vsa.musescore_cli import (
    MuseScoreNotFoundError,
    find_musescore,
    require_musescore,
)
from vsa.mvsa_mscz import MvsaMsczError, export_mvsa_to_mscz

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "mvsa"
ALLELUIA = EXAMPLES / "alleluia-toon-8.canonieke.mvsa"
MUSESCORE = find_musescore()


def test_require_musescore_override_missing(tmp_path: Path):
    with pytest.raises(MuseScoreNotFoundError):
        require_musescore(override=tmp_path / "nope.exe")


def test_export_mscz_without_musescore_raises(tmp_path: Path):
    out = tmp_path / "out.mscz"
    with patch("vsa.mvsa_mscz.require_musescore", side_effect=MuseScoreNotFoundError("x")):
        with pytest.raises(MvsaMsczError, match="x"):
            export_mvsa_to_mscz(ALLELUIA, out, section_id="schets2-oct-doremi")


@pytest.mark.skipif(MUSESCORE is None, reason="MuseScore niet geïnstalleerd")
def test_export_alleluia_section_to_mscz(tmp_path: Path):
    out = tmp_path / "alleluia.mscz"
    keep = tmp_path / "alleluia.mxl"
    export_mvsa_to_mscz(
        ALLELUIA,
        out,
        section_id="schets2-oct-doremi",
        keep_mxl=keep,
    )
    assert out.is_file()
    assert out.stat().st_size > 500
    assert keep.is_file()
    with zipfile.ZipFile(out) as archive:
        names = archive.namelist()
    assert any(n.endswith(".mscx") for n in names)
