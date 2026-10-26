"""mvsa → muziek-only SVG (MuseScore bridge)."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from vsa.musescore_cli import (
    MuseScoreNotFoundError,
    _resolve_musescore_svg_pages,
    find_musescore,
)
from vsa.mvsa_mscz import MvsaMsczError, export_mvsa_to_svg

ROOT = Path(__file__).resolve().parents[1]
VREDE = ROOT / "examples" / "mvsa" / "1a-vredeslitanie.mvsa"
MUSESCORE = find_musescore()

_MINI_MSCX_WITH_CHROME = """<?xml version='1.0'?>
<museScore version="4.20">
  <Score>
    <Style>
      <showFooter>1</showFooter>
      <oddFooterC>© Test</oddFooterC>
    </Style>
    <metaTag name="workTitle">Titel Hier</metaTag>
    <metaTag name="copyright">© Test</metaTag>
    <Staff id="1">
      <VBox>
        <height>10</height>
        <eid>fake-eid-vbox</eid>
        <Text>
          <eid>fake-eid-title</eid>
          <style>title</style>
          <text>Titel Hier</text>
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


def _write_mini_mscz(path: Path, mscx: str = _MINI_MSCX_WITH_CHROME) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(f"{path.stem}.mscx", mscx)
    return path


def test_resolve_single_svg_page_folds_to_dest(tmp_path: Path) -> None:
    dest = tmp_path / "lied.svg"
    page = tmp_path / "lied-1.svg"
    page.write_text("<svg/>", encoding="utf-8")
    assert _resolve_musescore_svg_pages(dest) == [dest]
    assert dest.is_file()
    assert not page.exists()


def test_resolve_multi_svg_pages_keeps_bladreeks(tmp_path: Path) -> None:
    dest = tmp_path / "lied.svg"
    p1 = tmp_path / "lied-1.svg"
    p2 = tmp_path / "lied-2.svg"
    p1.write_text("<svg>1</svg>", encoding="utf-8")
    p2.write_text("<svg>2</svg>", encoding="utf-8")
    pages = _resolve_musescore_svg_pages(dest)
    assert pages == [p1, p2]
    assert not dest.exists()
    assert p1.is_file() and p2.is_file()


def test_export_mscz_to_svg_trims_bladreeks(tmp_path: Path) -> None:
    from vsa.mvsa_mscz import export_mscz_to_svg

    mscz = _write_mini_mscz(tmp_path / "lied.mscz")
    out = tmp_path / "lied.svg"
    page_svg = (
        '<?xml version="1.0"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" '
        'viewBox="0 0 100 200">'
        '<path fill="#ffffff" d="M0,0 L100,0 L100,200 L0,200 z"/>'
        '<path fill="#000000" d="M10,10 L20,10 L20,20 L10,20 z"/>'
        "</svg>\n"
    )

    def _fake_convert(_src, dest, **_kwargs):
        dest = Path(dest)
        p1 = dest.parent / f"{dest.stem}-1.svg"
        p2 = dest.parent / f"{dest.stem}-2.svg"
        p1.write_text(page_svg, encoding="utf-8")
        p2.write_text(page_svg, encoding="utf-8")
        return p1

    with patch("vsa.mvsa_mscz.convert_with_musescore", side_effect=_fake_convert):
        written = export_mscz_to_svg(mscz, out, trim=True)
    assert [p.name for p in written] == ["lied-1.svg", "lied-2.svg"]
    assert not out.exists()
    for path in written:
        text = path.read_text(encoding="utf-8")
        height = re.search(r'\bheight="([^"]+)"', text)
        assert height is not None
        assert "297" not in height.group(1)


def test_export_svg_without_musescore_raises(tmp_path: Path) -> None:
    out = tmp_path / "x.svg"
    with patch(
        "vsa.mvsa_mscz.require_musescore",
        side_effect=MuseScoreNotFoundError("x"),
    ):
        with pytest.raises(MvsaMsczError):
            export_mvsa_to_svg(VREDE, out)


def test_export_mscz_to_svg_passes_through(tmp_path: Path) -> None:
    """Bestaand .mscz → SVG; bronbestand blijft ongewijzigd."""
    from vsa.mvsa_mscz import export_mscz_to_svg

    mscz = _write_mini_mscz(tmp_path / "lied.mscz")
    before = mscz.read_bytes()
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
    assert mscz.read_bytes() == before


def test_export_mscz_to_svg_strips_chrome_before_convert(tmp_path: Path) -> None:
    """Kale SVG: MuseScore krijgt een kopie zonder titel/copyright; bron intact."""
    from vsa.mvsa_mscz import export_mscz_to_svg

    mscz = _write_mini_mscz(tmp_path / "lied.mscz")
    before = mscz.read_bytes()
    out = tmp_path / "lied.svg"
    seen: dict[str, str] = {}

    def _fake_convert(src, dest, **_kwargs):
        src = Path(src)
        with zipfile.ZipFile(src) as z:
            mscx_name = next(n for n in z.namelist() if n.lower().endswith(".mscx"))
            body = z.read(mscx_name).decode("utf-8")
        seen["body"] = body
        Path(dest).write_text(
            '<?xml version="1.0"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" '
            'viewBox="0 0 10 10"></svg>\n',
            encoding="utf-8",
        )

    with patch("vsa.mvsa_mscz.convert_with_musescore", side_effect=_fake_convert):
        export_mscz_to_svg(mscz, out, trim=False)

    assert "Titel Hier" not in seen["body"]
    assert "<style>title</style>" not in seen["body"]
    assert "© Test" not in seen["body"]
    assert "<showFooter>0</showFooter>" in seen["body"]
    assert mscz.read_bytes() == before
    with zipfile.ZipFile(mscz) as z:
        bron = z.read("lied.mscx").decode("utf-8")
    assert "Titel Hier" in bron
    assert "© Test" in bron


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


def test_strip_chrome_clears_footer_in_score_style_mss(tmp_path: Path) -> None:
    """MS4: Style vaak alleen in mss — footer uitzetten moet daar ook."""
    from vsa.mscz_partituur import strip_mscz_sheet_chrome

    mscx = """<?xml version='1.0'?>
<museScore version="4.20">
  <Score>
    <Staff id="1">
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
    mss = """<?xml version="1.0" encoding="UTF-8"?>
<museScore version="4.70">
  <Style>
    <pageHeight>11.6929</pageHeight>
    <showFooter>1</showFooter>
    <oddFooterC>CC BY — zie colofon</oddFooterC>
  </Style>
</museScore>
"""
    path = tmp_path / "mss-only.mscz"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("score.mscx", mscx)
        z.writestr("score_style.mss", mss)
    strip_mscz_sheet_chrome(path)
    with zipfile.ZipFile(path) as z:
        body = z.read("score_style.mss").decode("utf-8")
    assert "<showFooter>0</showFooter>" in body
    assert "<oddFooterC></oddFooterC>" in body
    assert "CC BY" not in body


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
