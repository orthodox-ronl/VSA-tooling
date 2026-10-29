"""Post-process MuseScore SVG: enforce readable gaps between lyric words."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Doelgat tussen opeenvolgende lyric-bboxes (spatium). MuseScore laat ze tot
# ~0.1–0.16 sp tegen elkaar aan staan — dat leest als «desheils».
DEFAULT_MIN_GAP_SPATIUM = 0.45

_STAFF_RE = re.compile(
    r'<polyline class="StaffLines"[^>]*points="[^"]*?,\s*([0-9.]+)\s',
)
_LYRIC_PATH_RE = re.compile(
    r'(<path\b[^>]*\bclass="Lyrics"[^>]*\bd=")([^"]+)("(?:\s*/>|>\s*</path>))',
    re.IGNORECASE,
)


@dataclass
class _LyricPath:
    start: int
    end: int
    xmin: float
    xmax: float
    ymid: float
    d: str
    prefix: str
    suffix: str


def _estimate_spatium(svg: str) -> float:
    ys = [float(m.group(1)) for m in _STAFF_RE.finditer(svg)]
    uniq: list[float] = []
    for y in sorted(ys):
        if not uniq or abs(y - uniq[-1]) > 1.0:
            uniq.append(y)
    if len(uniq) >= 5:
        return (uniq[4] - uniq[0]) / 4.0
    return 82.68


def _path_bbox(d: str) -> tuple[float, float, float, float] | None:
    nums = [float(n) for n in re.findall(r"-?[0-9]+\.[0-9]+|-?[0-9]+", d)]
    if len(nums) < 4:
        return None
    xs, ys = nums[0::2], nums[1::2]
    if not xs or not ys:
        return None
    return min(xs), max(xs), min(ys), max(ys)


def _collect_lyrics(svg: str) -> list[_LyricPath]:
    out: list[_LyricPath] = []
    for m in _LYRIC_PATH_RE.finditer(svg):
        d = m.group(2)
        box = _path_bbox(d)
        if box is None:
            continue
        xmin, xmax, ymin, ymax = box
        out.append(
            _LyricPath(
                start=m.start(),
                end=m.end(),
                xmin=xmin,
                xmax=xmax,
                ymid=(ymin + ymax) / 2.0,
                d=d,
                prefix=m.group(1),
                suffix=m.group(3),
            )
        )
    return out


def enforce_svg_lyric_word_gaps(
    svg: str,
    *,
    min_gap_spatium: float = DEFAULT_MIN_GAP_SPATIUM,
) -> str:
    """Schuif lyric-``path``s uit elkaar tot min. gat (in spatium).

    MuseScore centreert lyrics op nootkoppen en houdt bboxes vrijwel tegen
    elkaar. Door te krappe opeenvolgende lyrics in dezelfde y-band naar rechts
    te vertalen, blijven woorden leesbaar gescheiden. Noten blijven staan.
    """
    if min_gap_spatium <= 0:
        return svg
    spatium = _estimate_spatium(svg)
    min_gap = min_gap_spatium * spatium
    lyrics = _collect_lyrics(svg)
    if len(lyrics) < 2:
        return svg

    # Één cluster per lyric-baseline (|Δy| ≤ 15); niet ruimer — anders
    # raken twee dicht-onder-elkaar-liggende regels (of SA-lyrics vs cues)
    # door elkaar en ontstaan verschuivingen van duizenden SVG-units.
    shifts = [0.0] * len(lyrics)
    used = [False] * len(lyrics)
    for seed in range(len(lyrics)):
        if used[seed]:
            continue
        y0 = lyrics[seed].ymid
        band = [
            j
            for j in range(len(lyrics))
            if not used[j] and abs(lyrics[j].ymid - y0) <= 15.0
        ]
        for j in band:
            used[j] = True
        band.sort(key=lambda j: lyrics[j].xmin)
        shifts[band[0]] = 0.0
        for k in range(len(band) - 1):
            left_i = band[k]
            right_i = band[k + 1]
            target_xmin = lyrics[left_i].xmax + shifts[left_i] + min_gap
            shifts[right_i] = max(0.0, target_xmin - lyrics[right_i].xmin)

    if all(abs(s) < 0.01 for s in shifts):
        return svg

    # Vervang van achter naar voren zodat offsets kloppen.
    order = sorted(range(len(lyrics)), key=lambda i: lyrics[i].start, reverse=True)
    out = svg
    for idx in order:
        dx = shifts[idx]
        if abs(dx) < 0.01:
            continue
        lp = lyrics[idx]
        wrapped = (
            f'<g transform="translate({dx:.3f},0)">'
            f"{lp.prefix}{lp.d}{lp.suffix}"
            f"</g>"
        )
        out = out[: lp.start] + wrapped + out[lp.end :]
    return out
