"""Trim MuseScore page-SVG to content (drop empty A4 tail / margins)."""

from __future__ import annotations

import re

_NUM_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_WHITE_PAGE_PATH_RE = re.compile(
    r'<path\b[^>]*\bfill="#ffffff"[^>]*/>\s*',
    re.IGNORECASE,
)
_SVG_OPEN_RE = re.compile(r"<svg\b([^>]*)>", re.IGNORECASE)
_VIEWBOX_RE = re.compile(r'\bviewBox="([^"]*)"', re.IGNORECASE)
_WIDTH_RE = re.compile(r'\bwidth="([^"]*)"', re.IGNORECASE)
_HEIGHT_RE = re.compile(r'\bheight="([^"]*)"', re.IGNORECASE)


class SvgTrimError(ValueError):
    """SVG had no drawable content to trim to."""


def _collect_xy(svg: str) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for pts in re.findall(r'\bpoints="([^"]+)"', svg):
        nums = [float(n) for n in _NUM_RE.findall(pts)]
        for i in range(0, len(nums) - 1, 2):
            xs.append(nums[i])
            ys.append(nums[i + 1])
    for d in re.findall(r'\bd="([^"]+)"', svg):
        nums = [float(n) for n in _NUM_RE.findall(d)]
        for i in range(0, len(nums) - 1, 2):
            xs.append(nums[i])
            ys.append(nums[i + 1])
    return xs, ys


def trim_musescore_svg(
    svg: str,
    *,
    padding: float = 120.0,
    white_background: bool = True,
) -> str:
    """Crop MuseScore SVG ``viewBox``/size to drawn content.

    Removes the full-page white background path, then sets ``viewBox`` from
    polyline/path coordinates plus *padding*. Width stays ``210mm``; height
    scales with the content aspect ratio (no empty A4 underbelly).

    *white_background* (default True): insert an opaque white ``<rect>`` for
    the trimmed viewBox. Set False for a transparent background.
    """
    body = _WHITE_PAGE_PATH_RE.sub("", svg, count=1)
    xs, ys = _collect_xy(body)
    if not xs or not ys:
        raise SvgTrimError("geen tekeninhoud in SVG om bij te snijden")

    min_x = min(xs) - padding
    min_y = min(ys) - padding
    max_x = max(xs) + padding
    max_y = max(ys) + padding
    vb_w = max(max_x - min_x, 1.0)
    vb_h = max(max_y - min_y, 1.0)
    height_mm = 210.0 * (vb_h / vb_w)
    view_box = f"{min_x:.3f} {min_y:.3f} {vb_w:.3f} {vb_h:.3f}"

    m = _SVG_OPEN_RE.search(body)
    if m is None:
        raise SvgTrimError("geen <svg>-root in MuseScore-SVG")
    attrs = m.group(1)
    if _VIEWBOX_RE.search(attrs):
        attrs = _VIEWBOX_RE.sub(f'viewBox="{view_box}"', attrs, count=1)
    else:
        attrs = f'{attrs} viewBox="{view_box}"'
    if _WIDTH_RE.search(attrs):
        attrs = _WIDTH_RE.sub('width="210mm"', attrs, count=1)
    else:
        attrs = f'{attrs} width="210mm"'
    if _HEIGHT_RE.search(attrs):
        attrs = _HEIGHT_RE.sub(f'height="{height_mm:.3f}mm"', attrs, count=1)
    else:
        attrs = f'{attrs} height="{height_mm:.3f}mm"'

    open_tag = f"<svg{attrs}>"
    rest = body[m.end() :]
    if white_background:
        bg = (
            f'<rect class="vsa-page-bg" x="{min_x:.3f}" y="{min_y:.3f}" '
            f'width="{vb_w:.3f}" height="{vb_h:.3f}" fill="#ffffff"/>\n'
        )
        # Na eventuele <title>/<desc> van MuseScore, anders helemaal vooraan.
        insert_at = 0
        for tag in ("title", "desc"):
            tm = re.match(
                rf"\s*<{tag}\b[^>]*>[\s\S]*?</{tag}>\s*",
                rest[insert_at:],
                re.IGNORECASE,
            )
            if tm:
                insert_at += tm.end()
        rest = rest[:insert_at] + bg + rest[insert_at:]
    return body[: m.start()] + open_tag + rest
