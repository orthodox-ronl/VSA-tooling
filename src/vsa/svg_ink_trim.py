"""Snij een VSA-SVG bij tot de getekende inhoud (veiligheidsnet voor witruimte).

``SVGRenderer`` rekent marges en rijen vooraf uit. Daardoor kunnen lege rijen
(bijv. uit bronstructuur boven de notatie), de vaste ``extra_top`` of de
breedte van een langere regel witruimte rond de notatie geven. Deze stap meet
de *getekende* elementen (``line``, ``circle``, ``text``) en zet de grootte
en viewBox terug naar inhoud + een kleine rand, ongeacht de oorzaak.

De inhoud wordt verschoven met een ``translate`` zodat de viewBox ``0 0 w h``
blijft (andere tools mogen die vorm blijven aannemen).
"""

from __future__ import annotations

import html
import math
import re

from .text_metrics import estimate_text_width

_SVG_OPEN_RE = re.compile(r"<svg\b[^>]*>")
_BG_RE = re.compile(r'<rect\b[^>]*width="100%"[^>]*height="100%"[^>]*/>')
_TAG_RE = re.compile(r"<(line|circle|text)\b([^>]*?)(/?)>", re.DOTALL)
_ATTR_RE = re.compile(r'([\w:-]+)="([^"]*)"')

ASCENT = 0.80
DESCENT = 0.25
MIN_SIZE = 20.0


def _attrs(raw: str) -> dict[str, str]:
    return {k: v for k, v in _ATTR_RE.findall(raw)}


def _f(attrs: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(attrs[key])
    except (KeyError, ValueError):
        return default


def ink_bounds(svg: str) -> tuple[float, float, float, float] | None:
    """(min_x, min_y, max_x, max_y) van line/circle/text, of None."""
    xs: list[float] = []
    ys: list[float] = []
    for m in _TAG_RE.finditer(svg):
        tag, raw, selfclose = m.group(1), m.group(2), m.group(3)
        a = _attrs(raw)
        if tag == "line":
            half = _f(a, "stroke-width", 1.0) / 2.0
            for kx in ("x1", "x2"):
                if kx in a:
                    xs += [_f(a, kx) - half, _f(a, kx) + half]
            for ky in ("y1", "y2"):
                if ky in a:
                    ys += [_f(a, ky) - half, _f(a, ky) + half]
        elif tag == "circle":
            r = _f(a, "r") + _f(a, "stroke-width", 0.0) / 2.0
            cx, cy = _f(a, "cx"), _f(a, "cy")
            xs += [cx - r, cx + r]
            ys += [cy - r, cy + r]
        else:
            if selfclose:
                continue
            end = svg.find("</text>", m.end())
            if end < 0:
                continue
            content = html.unescape(re.sub(r"<[^>]+>", "", svg[m.end() : end]))
            if not content.strip():
                continue
            size = _f(a, "font-size", 20.0)
            family = a.get("font-family", "DejaVu Sans").split(",")[0].strip()
            width = estimate_text_width(
                content, size, preserve_whitespace=True, font_family=family
            )
            x, y = _f(a, "x"), _f(a, "y")
            anchor = a.get("text-anchor", "start")
            if anchor == "middle":
                x0, x1 = x - width / 2, x + width / 2
            elif anchor == "end":
                x0, x1 = x - width, x
            else:
                x0, x1 = x, x + width
            xs += [x0, x1]
            ys += [y - size * ASCENT, y + size * DESCENT]
    if not xs or not ys:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def trim_vsa_svg(svg: str, *, pad_x: float = 6.0, pad_y: float = 4.0) -> str:
    """Zet breedte/hoogte/viewBox op inhoud + rand; lege SVG blijft ongewijzigd."""
    bounds = ink_bounds(svg)
    if bounds is None:
        return svg
    min_x, min_y, max_x, max_y = bounds
    left, top = min_x - pad_x, min_y - pad_y
    width = max(math.ceil(max_x + pad_x - left), MIN_SIZE)
    height = max(math.ceil(max_y + pad_y - top), MIN_SIZE)

    m = _SVG_OPEN_RE.search(svg)
    if m is None:
        return svg
    tag = m.group(0)
    tag = re.sub(r'\bwidth="[^"]*"', f'width="{width:.0f}"', tag, count=1)
    tag = re.sub(r'\bheight="[^"]*"', f'height="{height:.0f}"', tag, count=1)
    tag = re.sub(
        r'\bviewBox="[^"]*"', f'viewBox="0 0 {width:.0f} {height:.0f}"', tag, count=1
    )
    head, rest = svg[: m.start()], svg[m.end() :]
    close = rest.rfind("</svg>")
    if close < 0:
        return svg
    body, tail = rest[:close], rest[close:]
    bg = _BG_RE.search(body)
    insert = bg.end() if bg else 0
    wrapped = (
        body[:insert]
        + f'\n<g class="vsa-trim" transform="translate({-left:.2f} {-top:.2f})">'
        + body[insert:]
        + "\n</g>\n"
    )
    return head + tag + wrapped + tail
