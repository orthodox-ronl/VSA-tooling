"""mvsa → muziek-only SVG (MuseScore bridge)."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from vsa.musescore_cli import MuseScoreNotFoundError, find_musescore
from vsa.mvsa_mscz import MvsaMsczError, export_mvsa_to_svg

ROOT = Path(__file__).resolve().parents[1]
VREDE = ROOT / "examples" / "mvsa" / "1a-vredeslitanie.mvsa"
MUSESCORE = find_musescore()


def test_export_svg_without_musescore_raises(tmp_path: Path) -> None:
    out = tmp_path / "x.svg"
    with patch(
        "vsa.mvsa_mscz.require_musescore",
        side_effect=MuseScoreNotFoundError("x"),
    ):
        with pytest.raises(MvsaMsczError):
            export_mvsa_to_svg(VREDE, out)


def test_export_mscz_to_svg_passes_through(tmp_path: Path) -> None:
    """Bestaand .mscz → SVG (Style/fonts blijven in het .mscz)."""
    from vsa.mvsa_mscz import export_mscz_to_svg

    mscz = tmp_path / "lied.mscz"
    mscz.write_bytes(b"PK\x03\x04fake")
    out = tmp_path / "lied.svg"
    fake_svg = (
        '<?xml version="1.0"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50" '
        'viewBox="0 0 100 50"></svg>\n'
    )

    def _fake_convert(src, dest, **_kwargs):
        Path(dest).write_text(fake_svg, encoding="utf-8")

    with patch("vsa.mvsa_mscz.convert_with_musescore", side_effect=_fake_convert):
        export_mscz_to_svg(mscz, out, trim=False)
    assert out.read_text(encoding="utf-8") == fake_svg


def test_normalize_includes_muziek() -> None:
    from vsa.mscz_layout import normalize_mscz_layout

    assert normalize_mscz_layout("muziek") == "muziek"


def test_muziek_layout_strips_title_from_mscz(tmp_path: Path) -> None:
    """Minimal MSCZ (MuseScore 4 eid-order): muziek → geen titel/componist."""
    from vsa.mscz_layout import apply_mscz_layout_profile

    mscx = """<?xml version='1.0'?>
<museScore version="4.20">
  <Score>
    <Style>
      <showFooter>1</showFooter>
    </Style>
    <Staff id="1">
      <VBox>
        <height>10</height>
        <eid>fake-eid-vbox</eid>
        <Text>
          <eid>fake-eid-title</eid>
          <style>title</style>
          <text>Titel Hier</text>
          </Text>
        <Text>
          <eid>fake-eid-composer</eid>
          <style>composer</style>
          <text>Componist X</text>
          </Text>
        </VBox>
      <Measure>
        <voice>
          <Rest>
            <durationType>measure</durationType>
            <duration>1/1</duration>
            </Rest>
          </voice>
        </Measure>
      </Staff>
    </Score>
  </museScore>
"""
    path = tmp_path / "mini.mscz"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mini.mscx", mscx)
    assert apply_mscz_layout_profile(path, layout="muziek") == "muziek"
    with zipfile.ZipFile(path) as z:
        body = z.read("mini.mscx").decode("utf-8")
    assert "<style>title</style>" not in body
    assert "<style>composer</style>" not in body
    assert "Titel Hier" not in body
    assert "Componist X" not in body
    assert "<VBox>" not in body
    assert "<showFooter>0</showFooter>" in body


@pytest.mark.skipif(MUSESCORE is None, reason="MuseScore niet geïnstalleerd")
def test_export_vredeslitanie_svg_trimmed(tmp_path: Path) -> None:
    out = tmp_path / "vrede.svg"
    keep = tmp_path / "vrede.mscz"
    export_mvsa_to_svg(VREDE, out, keep_mscz=keep)
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert text.lstrip().startswith("<?xml") or "<svg" in text[:200]
    m = re.search(r'\bheight="([^"]+)"', text)
    assert m is not None
    # Trimmed: not full A4 297mm (allow small float noise).
    h = m.group(1)
    assert "297" not in h
    vb = re.search(r'viewBox="([^"]+)"', text)
    assert vb is not None
    parts = [float(x) for x in vb.group(1).split()]
    assert len(parts) == 4
    assert parts[3] < 14000  # content height << full MuseScore page units
    # Muziek-only: geen titel/componist in tussen-MSCZ.
    with zipfile.ZipFile(keep) as z:
        mscx = z.read(next(n for n in z.namelist() if n.endswith(".mscx"))).decode(
            "utf-8"
        )
    assert not re.search(r"<style>\s*title\s*</style>", mscx, re.I)
    assert not re.search(r"<style>\s*composer\s*</style>", mscx, re.I)
    assert "Vredeslitanie" not in mscx
