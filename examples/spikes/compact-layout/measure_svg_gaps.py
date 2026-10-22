"""Spike: meet staf-/systeemafstanden in MuseScore-SVG (StaffLines).

Gebruik:
  python examples/spikes/compact-layout/measure_svg_gaps.py pad.svg
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path


_STAFF_RE = re.compile(
    r'<polyline class="StaffLines"[^>]*points="[^"]*?,\s*([0-9.]+)\s',
)
_TEXT_RE = re.compile(
    r'<text[^>]*\by="([0-9.]+)"[^>]*>(.*?)</text>',
    re.DOTALL,
)


def _staff_line_ys(svg: str) -> list[float]:
    ys = [float(m.group(1)) for m in _STAFF_RE.finditer(svg)]
    # unique rounded (MuseScore float noise)
    uniq: list[float] = []
    for y in sorted(ys):
        if not uniq or abs(y - uniq[-1]) > 1.0:
            uniq.append(y)
    return uniq


def _cluster_staves(line_ys: list[float]) -> list[tuple[float, float]]:
    """Groepeer 5 notenbalklijnen → (top, bottom) per balk."""
    staves: list[tuple[float, float]] = []
    i = 0
    while i + 4 < len(line_ys):
        chunk = line_ys[i : i + 5]
        # spatium-achtige lijnafstand: balk is compact
        gaps = [chunk[j + 1] - chunk[j] for j in range(4)]
        if max(gaps) - min(gaps) < 20 and max(gaps) < 200:
            staves.append((chunk[0], chunk[-1]))
            i += 5
        else:
            i += 1
    return staves


def _pair_systems(staves: list[tuple[float, float]]) -> list[dict]:
    """SA/TB: twee opeenvolgende balken = één systeem."""
    systems: list[dict] = []
    for i in range(0, len(staves) - 1, 2):
        sa_top, sa_bot = staves[i]
        tb_top, tb_bot = staves[i + 1]
        systems.append(
            {
                "sa_top": sa_top,
                "sa_bot": sa_bot,
                "tb_top": tb_top,
                "tb_bot": tb_bot,
                "inner_gap": tb_top - sa_bot,
                "height": tb_bot - sa_top,
            }
        )
    return systems


def _cue_ys(svg: str) -> list[tuple[float, str]]:
    out: list[tuple[float, str]] = []
    for m in _TEXT_RE.finditer(svg):
        y = float(m.group(1))
        raw = re.sub(r"<[^>]+>", "", m.group(2))
        text = re.sub(r"\s+", " ", raw).strip()
        if text.startswith("P:") or text.startswith("D:"):
            out.append((y, text[:60]))
    return out


def measure(path: Path) -> None:
    svg = path.read_text(encoding="utf-8")
    lines = _staff_line_ys(svg)
    staves = _cluster_staves(lines)
    systems = _pair_systems(staves)
    cues = _cue_ys(svg)

    print(f"=== {path.name} ===")
    print(f"staff lines: {len(lines)}  staves: {len(staves)}  systems: {len(systems)}")
    for i, s in enumerate(systems, 1):
        print(
            f"  system {i}: height={s['height']:.1f}  "
            f"inner(SA->TB)={s['inner_gap']:.1f}"
        )
    for i in range(len(systems) - 1):
        a, b = systems[i], systems[i + 1]
        gap = b["sa_top"] - a["tb_bot"]
        # cues whose y zit in de gap-zone (ruwweg boven volgend systeem)
        in_gap = [
            t for (y, t) in cues if a["tb_bot"] - 50 < y < b["sa_top"] + 80
        ]
        tag = f" cues={in_gap!r}" if in_gap else " (geen P:/D: in gap)"
        print(f"  gap {i + 1}->{i + 2}: {gap:.1f}{tag}")
    if cues:
        print("  alle cues (y, tekst):")
        for y, t in cues:
            print(f"    y={y:.1f}  {t}")


def main() -> int:
    if len(sys.argv) < 2:
        print("Gebruik: measure_svg_gaps.py <svg> [<svg> ...]", file=sys.stderr)
        return 2
    for arg in sys.argv[1:]:
        measure(Path(arg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
