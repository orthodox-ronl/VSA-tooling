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


_TRANSFORMED = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="210mm" height="297mm" viewBox="0 0 10000 10000"
 xmlns="http://www.w3.org/2000/svg" version="1.2">
<title>t</title>
<path fill="#ffffff" d="M0,0 L10000,0 L10000,10000 L0,10000 L0,0 "/>
<polyline class="StaffLines" fill="none" stroke="#000000"
 points="700,1200 9000,1200" />
<g transform="matrix(1,0,0,1,800,1300)">
<path d="M0,0 C10,0 20,10 20,20 L0,20 L0,0 "/>
</g>
</svg>
"""


def test_trim_applies_musescore_transforms() -> None:
    """Glyphs near local (0,0) must not inflate left/top margins."""
    out = trim_musescore_svg(_TRANSFORMED, padding=10)
    vb = out.split('viewBox="', 1)[1].split('"', 1)[0]
    min_x, min_y, vb_w, vb_h = (float(x) for x in vb.split())
    # Staff starts at x=700; glyph at translate(800,1300). Without transform
    # awareness min_x would be ~-10 (local 0 − padding).
    assert min_x == pytest.approx(690.0, abs=0.1)
    assert min_y == pytest.approx(1190.0, abs=0.1)
    # Right edge ~9000 + pad; bottom ~1320 (glyph) + pad
    assert min_x + vb_w == pytest.approx(9010.0, abs=0.1)
    assert min_y + vb_h == pytest.approx(1330.0, abs=0.1)
