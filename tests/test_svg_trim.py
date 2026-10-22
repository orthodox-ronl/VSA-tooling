"""Unit tests for MuseScore SVG content trim."""

from __future__ import annotations

import pytest

from vsa.svg_trim import SvgTrimError, trim_musescore_svg

_MINI = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="210mm" height="297mm" viewBox="0 0 1000 2000"
 xmlns="http://www.w3.org/2000/svg" version="1.2">
<title>t</title>
<path class="" fill="#ffffff" fill-rule="evenodd" d="M0,0 L1000,0 L1000,2000 L0,2000 L0,0 "/>
<polyline class="StaffLines" fill="none" stroke="#000000" points="100,400 900,400" />
<polyline class="StaffLines" fill="none" stroke="#000000" points="100,800 900,800" />
<path class="Text" d="M200,350 L250,350 L250,500 L200,500 L200,350 "/>
</svg>
"""


def test_trim_removes_white_page_and_shortens_height() -> None:
    out = trim_musescore_svg(_MINI, padding=10)
    assert 'class="vsa-page-bg"' in out
    assert 'fill="#ffffff"' in out
    assert 'width="210mm"' in out
    assert 'viewBox="' in out
    # Content roughly 100..900 x, 350..800 y → not full 0..2000 height.
    h_attr = out.split('height="', 1)[1].split('"', 1)[0]
    assert "297" not in h_attr
    vb = out.split('viewBox="', 1)[1].split('"', 1)[0]
    assert "2000" not in vb


def test_trim_transparent_skips_background() -> None:
    out = trim_musescore_svg(_MINI, padding=10, white_background=False)
    assert 'class="vsa-page-bg"' not in out


def test_trim_empty_raises() -> None:
    bare = (
        '<?xml version="1.0"?><svg width="1" height="1" viewBox="0 0 1 1" '
        'xmlns="http://www.w3.org/2000/svg"></svg>'
    )
    with pytest.raises(SvgTrimError):
        trim_musescore_svg(bare)
