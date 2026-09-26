"""Align mvsa LSATB columns: syllable/recite starts line up with voice pitches.

Canonical rule (see docs/specification-mvsa/syntax.md):
  In each system, the first letter of each L-position (recite: first char of
  ``(…``; continued word: first letter after the joining ``-``) shares the
  same 0-based column as the first character of the matching voice token.

Usage:
  python scripts/align_mvsa_columns.py examples/mvsa
  python scripts/align_mvsa_columns.py examples/mvsa --check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vsa.mvsa_parse import (  # noqa: E402
    LPosition,
    _ELMS,
    _is_syllable_char,
    _read_elms,
    parse_l_positions,
)
from vsa.mvsa_validate import MARKER_RE, _split_bars  # noqa: E402


def _l_position_spans(measure: str) -> list[tuple[int, int]]:
    """Return (start, end) spans for each L-position within ``measure``."""
    s = measure
    stripped = s.strip()
    if not stripped:
        return []
    offset = len(s) - len(s.lstrip()) if s.strip() else 0
    # Prefer left index of stripped content
    offset = s.find(stripped[0]) if stripped else 0
    positions = parse_l_positions(stripped)
    spans: list[tuple[int, int]] = []
    i = 0
    n = len(stripped)
    pi = 0
    while i < n and pi < len(positions):
        if stripped[i].isspace():
            i += 1
            continue
        if stripped[i] in ",;:!?":
            i += 1
            continue
        if stripped[i] == ".":
            is_elm_dot = any(
                stripped.startswith(e, i) and e in (".", "..", "_.", "-.", "~.")
                for e in _ELMS
            )
            if not is_elm_dot:
                i += 1
                continue
        start = i
        if stripped[i] == "(":
            close = stripped.find(")", i + 1)
            if close < 0:
                close = n - 1
            i = close + 1
            _, i = _read_elms(stripped, i, allow_bare_dash=False)
            spans.append((start + offset, i + offset))
            pi += 1
            continue
        if stripped[i] == "-" and i + 1 < n and _is_syllable_char(stripped[i + 1]):
            i += 1
        while True:
            while i < n and (
                _is_syllable_char(stripped[i]) or stripped[i] in "'’ʹ"
            ):
                i += 1
            while i < n and stripped[i] in ",;:!?":
                i += 1
            _, i = _read_elms(stripped, i)
            while i < n and stripped[i] in ",;:!?":
                i += 1
            if (
                i < n
                and stripped[i] == "-"
                and i + 1 < n
                and _is_syllable_char(stripped[i + 1])
            ):
                break
            break
        spans.append((start + offset, i + offset))
        pi += 1
    return spans


def _l_tokens(measure: str) -> list[str]:
    spans = _l_position_spans(measure)
    if spans:
        return [measure[a:b] for a, b in spans]
    return [_format_lpos(p) for p in parse_l_positions(measure)]


def _format_lpos(p: LPosition) -> str:
    if p.recite:
        parts: list[str] = []
        for i, syl in enumerate(p.syllables):
            if i:
                parts.append("-" if (i - 1 < len(p.links) and p.links[i - 1]) else " ")
            parts.append(syl)
        return "(" + "".join(parts) + ")" + "".join(p.elms)
    prefix = "-" if p.continues_word else ""
    if not p.syllables:
        return prefix + "".join(p.elms)
    body = p.syllables[0]
    for i, syl in enumerate(p.syllables[1:]):
        link = p.links[i] if i < len(p.links) else True
        body += ("-" if link else " ") + syl
    return prefix + body + "".join(p.elms)


def _voice_tokens(measure: str) -> list[str]:
    return [t for t in measure.split() if t]


def _place_at_anchors(tokens: list[str], anchors: list[int]) -> str:
    if not tokens:
        return ""
    width = max(a + len(t) for a, t in zip(anchors, tokens))
    buf = [" "] * width
    for a, t in zip(anchors, tokens):
        for j, ch in enumerate(t):
            buf[a + j] = ch
    return "".join(buf).rstrip()


def _build_aligned_measure(
    l_tokens: list[str], voice_rows: list[list[str]]
) -> tuple[str, list[str]]:
    """Align voice pitch starts under L position starts (first letter / '(').

    Word-joining '-' stays on the syllable (``le-lu`` or ``le -lu`` when a
    stem-token needs an extra column so voice tokens stay space-separated).
    Extra width for long stem-tokens is absorbed in gaps, never by turning
    the joining '-' into an ELM (no ``le-  lu``).
    """
    n = len(l_tokens)
    if n == 0:
        return "", ["" for _ in voice_rows]
    for row in voice_rows:
        if len(row) != n:
            raise ValueError(f"positietelling L={n} vs stem={len(row)}")

    contents: list[str] = []
    glues: list[str] = []
    for i, raw in enumerate(l_tokens):
        if i == 0:
            glues.append("")
            contents.append(raw)
        elif raw.startswith("-"):
            glues.append("-")
            contents.append(raw[1:])
        else:
            glues.append(" ")
            contents.append(raw)

    if voice_rows:
        voice_w = [max(len(row[i]) for row in voice_rows) for i in range(n)]
    else:
        voice_w = [len(contents[i]) for i in range(n)]

    starts = [0] * n
    for i in range(1, n):
        # Always leave ≥1 free column after the previous stem-token so
        # whitespace still separates voice tokens on re-parse.
        voice_need = starts[i - 1] + voice_w[i - 1] + 1
        if glues[i] == "-":
            tight = starts[i - 1] + len(contents[i - 1]) + 1
            starts[i] = max(tight, voice_need)
        else:
            prev_span = max(len(contents[i - 1]), voice_w[i - 1])
            starts[i] = max(starts[i - 1] + prev_span + 1, voice_need)

    parts: list[str] = []
    col = 0
    out_anchors: list[int] = []
    for i in range(n):
        if i > 0:
            if glues[i] == "-":
                # Place '-' immediately before the syllable (anker = first letter).
                # Extra room becomes spaces *before* the hyphen: ``le -lu``, not
                # ``le-  lu`` (the latter makes '-' an ELM).
                hyphen_at = starts[i] - 1
                if hyphen_at < col:
                    hyphen_at = col
                    starts[i] = hyphen_at + 1
                if col < hyphen_at:
                    parts.append(" " * (hyphen_at - col))
                    col = hyphen_at
                parts.append("-")
                col += 1
            else:
                need = starts[i] - col
                if need < 1:
                    need = 1
                parts.append(" " * need)
                col += need
        if col < starts[i]:
            parts.append(" " * (starts[i] - col))
            col = starts[i]
        out_anchors.append(col)
        parts.append(contents[i])
        col += len(contents[i])

    l_out = "".join(parts).rstrip()
    voice_out = [_place_at_anchors(row, out_anchors) for row in voice_rows]
    return l_out, voice_out


def _align_system_contents(contents: dict[str, str], order: list[str]) -> dict[str, str]:
    splits = {m: _split_bars(contents[m]) for m in order}
    n_seg = len(splits[order[0]].segments)
    for m in order[1:]:
        if len(splits[m].segments) != n_seg:
            raise ValueError(
                f"maat-telling verschilt: {order[0]}={n_seg} vs {m}={len(splits[m].segments)}"
            )

    l_marker = next(m for m in order if m == "L" or m.startswith("L"))
    ref_bars = splits[l_marker].bar_tokens
    for m in order:
        if splits[m].bar_tokens != ref_bars:
            raise ValueError(
                f"maatstrepen verschillen: {l_marker}={ref_bars} vs {m}={splits[m].bar_tokens}"
            )

    out_segs: dict[str, list[str]] = {m: [] for m in order}

    for si in range(n_seg):
        l_toks = _l_tokens(splits[l_marker].segments[si])
        voice_order = [m for m in order if m != l_marker]
        voice_rows = [_voice_tokens(splits[m].segments[si]) for m in voice_order]
        extra_l = [m for m in order if m != l_marker and (m == "L" or m.startswith("L"))]
        if extra_l:
            raise ValueError("meerdere L-regels: aligner ondersteunt één L per systeem")
        l_line, v_lines = _build_aligned_measure(l_toks, voice_rows)
        out_segs[l_marker].append(l_line)
        for m, text in zip(voice_order, v_lines):
            out_segs[m].append(text)

    # Pad each measure so `|` / `||` / specialisations start on the same column.
    widths = [
        max(len(out_segs[m][si].rstrip()) for m in order) for si in range(n_seg)
    ]

    result: dict[str, str] = {}
    for m in order:
        parts: list[str] = []
        for i, seg in enumerate(out_segs[m]):
            parts.append(seg.rstrip().ljust(widths[i]))
            if i < len(ref_bars):
                parts.append(" ")
                parts.append(ref_bars[i])
                if i + 1 < n_seg:
                    parts.append(" ")
        result[m] = "".join(parts).rstrip()
    return result


def align_mvsa_text(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        raw = line.rstrip("\n\r")
        if MARKER_RE.match(raw.lstrip()):
            system_lines: list[tuple[str, str, str]] = []
            j = i
            while j < len(lines):
                r = lines[j].rstrip("\n\r")
                m = MARKER_RE.match(r.lstrip())
                if not m:
                    break
                key = f"{m.group(1)}{m.group(2)}"
                content = r.lstrip()[len(m.group(0)) :].lstrip()
                eol = lines[j][len(r) :]
                system_lines.append((key, content, eol or "\n"))
                j += 1
            if not system_lines:
                out.append(line)
                i += 1
                continue
            order = [mk for mk, _, _ in system_lines]
            contents = {mk: c for mk, c, _ in system_lines}
            if not any(k == "L" or k.startswith("L") for k in order):
                out.extend(lines[i:j])
                i = j
                continue
            try:
                aligned = _align_system_contents(contents, order)
            except ValueError as exc:
                out.extend(lines[i:j])
                print(f"skip system @ line {i + 1}: {exc}", file=sys.stderr)
                i = j
                continue
            for mk, _, eol in system_lines:
                out.append(f"{mk}: {aligned[mk]}{eol}")
            i = j
            continue
        out.append(line)
        i += 1
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    files: list[Path] = []
    for p in args.paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.mvsa")))
        else:
            files.append(p)
    changed = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        new = align_mvsa_text(text)
        if new != text:
            changed += 1
            if args.check:
                print(f"would change: {path}")
            else:
                path.write_text(new, encoding="utf-8", newline="\n")
                print(f"aligned: {path}")
        else:
            print(f"ok: {path}")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
