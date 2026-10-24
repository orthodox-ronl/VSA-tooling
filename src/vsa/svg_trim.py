"""Trim MuseScore page-SVG to content (drop empty A4 tail / margins)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

_NUM_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_WHITE_PAGE_PATH_RE = re.compile(
    r'<path\b[^>]*\bfill="#ffffff"[^>]*/>\s*',
    re.IGNORECASE,
)
_SVG_OPEN_RE = re.compile(r"<svg\b([^>]*)>", re.IGNORECASE)
_VIEWBOX_RE = re.compile(r'\bviewBox="([^"]*)"', re.IGNORECASE)
_WIDTH_RE = re.compile(r'\bwidth="([^"]*)"', re.IGNORECASE)
_HEIGHT_RE = re.compile(r'\bheight="([^"]*)"', re.IGNORECASE)

_Matrix = tuple[float, float, float, float, float, float]
_IDENTITY: _Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


class SvgTrimError(ValueError):
    """SVG had no drawable content to trim to."""


def _local_tag(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _parse_transform(value: str | None) -> _Matrix:
    """Parse a single ``matrix(...)`` or ``translate(...)``; else identity."""
    if not value:
        return _IDENTITY
    raw = value.strip()
    m = re.fullmatch(r"matrix\(\s*([^)]+)\)", raw)
    if m:
        nums = [float(x) for x in re.split(r"[,\s]+", m.group(1).strip()) if x]
        if len(nums) != 6:
            return _IDENTITY
        return (nums[0], nums[1], nums[2], nums[3], nums[4], nums[5])
    m = re.fullmatch(r"translate\(\s*([^)]+)\)", raw)
    if m:
        nums = [float(x) for x in re.split(r"[,\s]+", m.group(1).strip()) if x]
        if not nums:
            return _IDENTITY
        tx = nums[0]
        ty = nums[1] if len(nums) > 1 else 0.0
        return (1.0, 0.0, 0.0, 1.0, tx, ty)
    return _IDENTITY


def _mul(a: _Matrix, b: _Matrix) -> _Matrix:
    a0, a1, a2, a3, a4, a5 = a
    b0, b1, b2, b3, b4, b5 = b
    return (
        a0 * b0 + a2 * b1,
        a1 * b0 + a3 * b1,
        a0 * b2 + a2 * b3,
        a1 * b2 + a3 * b3,
        a0 * b4 + a2 * b5 + a4,
        a1 * b4 + a3 * b5 + a5,
    )


def _apply(m: _Matrix, x: float, y: float) -> tuple[float, float]:
    a, b, c, d, e, f = m
    return a * x + c * y + e, b * x + d * y + f


def _add_pairs(
    xs: list[float],
    ys: list[float],
    matrix: _Matrix,
    blob: str,
) -> None:
    nums = [float(n) for n in _NUM_RE.findall(blob)]
    for i in range(0, len(nums) - 1, 2):
        gx, gy = _apply(matrix, nums[i], nums[i + 1])
        xs.append(gx)
        ys.append(gy)


def _collect_xy(svg: str) -> tuple[list[float], list[float]]:
    """Collect drawable x/y in **user** space (MuseScore ``transform`` applied).

    MuseScore puts noteheads/glyphs in local coordinates near ``(0,0)`` and
    places them with ``transform="matrix(...)"``. Ignoring those transforms
    made the content bbox include local ``0`` and left huge left/top margins
    after padding.
    """
    xs: list[float] = []
    ys: list[float] = []
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        # Fallback: pre-transform naive scan (same as historical behaviour).
        for pts in re.findall(r'\bpoints="([^"]+)"', svg):
            _add_pairs(xs, ys, _IDENTITY, pts)
        for d in re.findall(r'\bd="([^"]+)"', svg):
            _add_pairs(xs, ys, _IDENTITY, d)
        return xs, ys

    def walk(el: ET.Element, matrix: _Matrix) -> None:
        tag = _local_tag(el.tag)
        if tag == "rect" and (el.get("class") or "") == "vsa-page-bg":
            return
        if tag == "path" and (el.get("fill") or "").lower() == "#ffffff":
            # Full-page MuseScore background (also stripped by regex earlier).
            return
        local = _parse_transform(el.get("transform"))
        m2 = _mul(matrix, local)
        if tag == "path":
            d = el.get("d")
            if d:
                _add_pairs(xs, ys, m2, d)
        elif tag in ("polyline", "polygon"):
            pts = el.get("points")
            if pts:
                _add_pairs(xs, ys, m2, pts)
        for child in el:
            walk(child, m2)

    walk(root, _IDENTITY)
    return xs, ys


def trim_musescore_svg(
    svg: str,
    *,
    padding: float = 120.0,
    white_background: bool = True,
) -> str:
    """Crop MuseScore SVG ``viewBox``/size to drawn content.

    Removes the full-page white background path, then sets ``viewBox`` from
    polyline/path coordinates (with ``transform`` applied) plus *padding*.
    Width stays ``210mm``; height scales with the content aspect ratio (no
    empty A4 underbelly).

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
