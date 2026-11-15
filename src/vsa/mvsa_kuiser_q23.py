"""Kuiser Q2 (@-blok) + Q3 (#maat N) — docs/formats/kuiser.md."""

from __future__ import annotations

import re
from pathlib import Path

from .mvsa_validate import (
    _split_bars,
    is_lyrics_stem,
    parse_regelidentifier,
)
from .mvsa_vsa import _soort_toon_from_source_name
from .yaml_frontmatter import strip_yaml_frontmatter

# Soorten met kuiser-tempo 181 (fingerprint).
_FAST_SOORTEN = frozenset({"tropaar", "kondak", "stichier"})
# BPM die als “tool-default” mogen worden overschreven (Q2).
_TOOL_DEFAULT_TEMPOS = frozenset({130, 180})

_AT_LINE = re.compile(
    r"^@(?P<name>[A-Za-z][A-Za-z0-9_-]*)\s*(?P<rest>.*)$"
)
_MAAT_COMMENT = re.compile(r"^#\s*maat\b", re.IGNORECASE)
_TITLE_QUOTED = re.compile(r'^"(.*)"\s*$')


def apply_q2_q3(
    text: str,
    *,
    source_path: Path | str | None = None,
) -> str:
    """Zet document-``@``-blok (Q2) en ``#maat N`` per systeem (Q3).

    YAML-frontmatter blijft onaangeroerd (Q1 volgt). ``@``-blok wint voor
    titel/do/mode/tempo t.o.v. ontbrekende waarden.
    """
    fm, body, _ = strip_yaml_frontmatter(text)
    yaml_prefix = text[: len(text) - len(body)] if body != text else ""

    soort, toon = _resolve_soort_toon(fm, source_path)
    lines = body.splitlines(keepends=True)
    preamble, systems = _split_preamble_and_systems(lines)

    meta = _collect_doc_meta(preamble, fm, source_path, soort=soort, toon=toon)
    new_preamble = _rewrite_preamble_with_at_block(preamble, meta)
    new_systems = _rewrite_systems_with_maat(systems)
    return yaml_prefix + "".join(new_preamble + new_systems)


def kuiser_tempo_for_soort(soort: str | None) -> int:
    """Fingerprint-tempo: 181 voor tropaar/kondak/stichier, anders 131."""
    if soort and soort.strip().lower() in _FAST_SOORTEN:
        return 181
    return 131


def should_replace_tempo(bpm: int | None) -> bool:
    """True als tempo ontbreekt of een bekende tool-default is."""
    return bpm is None or bpm in _TOOL_DEFAULT_TEMPOS


def _resolve_soort_toon(
    fm: dict, source_path: Path | str | None
) -> tuple[str | None, int | None]:
    soort = fm.get("soort") if isinstance(fm.get("soort"), str) else None
    toon_raw = fm.get("toon")
    toon: int | None = None
    if isinstance(toon_raw, int) and 1 <= toon_raw <= 8:
        toon = toon_raw
    elif isinstance(toon_raw, str) and toon_raw.strip().isdigit():
        n = int(toon_raw.strip())
        if 1 <= n <= 8:
            toon = n
    if source_path is not None:
        derived = _soort_toon_from_source_name(str(source_path))
        if soort is None:
            soort = derived.get("soort")
        if toon is None:
            t = derived.get("toon")
            toon = t if isinstance(t, int) else None
    return soort, toon


def _collect_doc_meta(
    preamble: list[str],
    fm: dict,
    source_path: Path | str | None,
    *,
    soort: str | None,
    toon: int | None,
) -> dict[str, str | None]:
    found: dict[str, str] = {}
    for raw in preamble:
        line = raw.rstrip("\n\r").strip()
        m = _AT_LINE.match(line)
        if not m:
            continue
        name = m.group("name").lower()
        rest = m.group("rest").strip()
        if name in {"title", "do", "mode", "tempo", "oct"}:
            found[name] = rest

    title = found.get("title")
    if title:
        qm = _TITLE_QUOTED.match(title)
        title_text = qm.group(1) if qm else title
    else:
        title_text = _title_from_fm_or_path(fm, source_path, toon)

    do = found.get("do") or _fm_str(fm, "do") or "F4"
    mode = found.get("mode") or _fm_str(fm, "mode") or "major"

    tempo_bpm: int | None = None
    tempo_rest = found.get("tempo")
    if tempo_rest:
        from .mvsa_validate import parse_tempo_argument

        parsed = parse_tempo_argument(tempo_rest)
        if parsed is not None:
            tempo_bpm = parsed[0]
    if tempo_bpm is None:
        t_fm = fm.get("tempo")
        if isinstance(t_fm, int):
            tempo_bpm = t_fm
        elif isinstance(t_fm, str) and t_fm.strip().isdigit():
            tempo_bpm = int(t_fm.strip())

    if should_replace_tempo(tempo_bpm):
        tempo_bpm = kuiser_tempo_for_soort(soort)

    oct_rest = found.get("oct")  # only keep if already present
    return {
        "title": title_text,
        "do": do,
        "mode": mode,
        "tempo": str(tempo_bpm),
        "oct": oct_rest,
    }


def _fm_str(fm: dict, key: str) -> str | None:
    val = fm.get(key)
    return val.strip() if isinstance(val, str) and val.strip() else None


def _title_from_fm_or_path(
    fm: dict, source_path: Path | str | None, toon: int | None
) -> str:
    for key in ("titel", "title"):
        val = fm.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    part = fm.get("partituur")
    if isinstance(part, dict):
        for key in ("title", "titel"):
            val = part.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    if source_path is None:
        return "Zonder titel"
    return _title_from_filename(str(source_path), toon)


def _title_from_filename(source_name: str, toon: int | None) -> str:
    stem = Path(source_name).name
    for suf in (".mvsa", ".vsa", ".mscz", ".mxl"):
        if stem.lower().endswith(suf):
            stem = stem[: -len(suf)]
            break
    derived = _soort_toon_from_source_name(source_name)
    if toon is None and isinstance(derived.get("toon"), int):
        toon = derived["toon"]
    soort = derived.get("soort")
    parts = stem.split("-")
    if soort and parts and parts[0].lower() == str(soort).lower():
        parts = parts[1:]
    # Drop toon-N and everything after (uitvoeringsvorm-segment).
    out_parts: list[str] = []
    i = 0
    while i < len(parts):
        if parts[i].lower() == "toon" and i + 1 < len(parts) and parts[i + 1].isdigit():
            break
        if re.fullmatch(r"toon-[1-8]", parts[i].lower()):
            break
        out_parts.append(parts[i])
        i += 1
    if not out_parts:
        out_parts = parts[:1] or ["stuk"]
    words = " ".join(out_parts)
    # Lichte capitalisatie: eerste letter hoofdletter.
    if words:
        words = words[0].upper() + words[1:]
    if toon is not None:
        return f"{words} (Toon {toon})"
    return words


def _rewrite_preamble_with_at_block(
    preamble: list[str], meta: dict[str, str | None]
) -> list[str]:
    """Vervang document-``@title/@do/@mode/@tempo/@oct`` door canonieke kop."""
    kept: list[str] = []
    for raw in preamble:
        line = raw.rstrip("\n\r").strip()
        if _MAAT_COMMENT.match(line):
            continue
        m = _AT_LINE.match(line)
        if m and m.group("name").lower() in {
            "title",
            "do",
            "mode",
            "tempo",
            "oct",
        }:
            continue
        kept.append(raw)

    # Drop leading blank lines; we add our own spacing.
    while kept and not kept[0].strip():
        kept.pop(0)

    block = [
        f'@title "{meta["title"]}"\n',
        f'@do {meta["do"]}\n',
        f'@mode {meta["mode"]}\n',
        f'@tempo {meta["tempo"]}\n',
    ]
    if meta.get("oct"):
        block.append(f'@oct {meta["oct"]}\n')
    block.append("\n")
    return block + kept


def _split_preamble_and_systems(
    lines: list[str],
) -> tuple[list[str], list[list[str]]]:
    """Preamble = alles vóór het eerste LSATB-systeem; daarna systemen + tussenstof."""
    preamble: list[str] = []
    i = 0
    while i < len(lines):
        raw = lines[i].rstrip("\n\r")
        if parse_regelidentifier(raw.lstrip()):
            break
        preamble.append(lines[i])
        i += 1

    systems: list[list[str]] = []
    while i < len(lines):
        # Collect leading non-LSATB (comments, @sectie, blanks) + one system.
        chunk: list[str] = []
        while i < len(lines):
            raw = lines[i].rstrip("\n\r")
            if parse_regelidentifier(raw.lstrip()):
                break
            chunk.append(lines[i])
            i += 1
        if i >= len(lines):
            if chunk:
                # Trailing comments after last system → attach to last chunk
                # or preamble if no systems yet.
                if systems:
                    systems[-1].extend(chunk)
                else:
                    preamble.extend(chunk)
            break
        while i < len(lines):
            raw = lines[i].rstrip("\n\r")
            if not parse_regelidentifier(raw.lstrip()):
                break
            chunk.append(lines[i])
            i += 1
        systems.append(chunk)
    return preamble, systems


def _rewrite_systems_with_maat(systems: list[list[str]]) -> list[str]:
    out: list[str] = []
    next_maat = 1
    for chunk in systems:
        lead, lsatb, trail = _partition_system_chunk(chunk)
        # Strip old #maat / # maat from lead (and between lead and system).
        lead = [ln for ln in lead if not _MAAT_COMMENT.match(ln.rstrip("\n\r").strip())]
        # Also strip maat comments that snuck into trail.
        trail = [ln for ln in trail if not _MAAT_COMMENT.match(ln.rstrip("\n\r").strip())]

        n_measures = _count_measures_in_lsatb(lsatb)
        maat_line = f"#maat {next_maat}\n"
        next_maat += max(n_measures, 1)

        # Ensure @sectie (if any) stays above #maat; blanks cleaned lightly.
        while lead and not lead[-1].strip():
            lead.pop()
        out.extend(lead)
        if lead and not lead[-1].endswith("\n"):
            pass
        if lead:
            out.append("\n")
        out.append(maat_line)
        out.extend(lsatb)
        out.extend(trail)
        if out and not out[-1].endswith("\n"):
            out.append("\n")
        # Blank line between systems when trail didn't provide one.
        if trail and trail[-1].strip():
            out.append("\n")
        elif not trail:
            out.append("\n")
    return out


def _partition_system_chunk(
    chunk: list[str],
) -> tuple[list[str], list[str], list[str]]:
    lead: list[str] = []
    i = 0
    while i < len(chunk):
        raw = chunk[i].rstrip("\n\r")
        if parse_regelidentifier(raw.lstrip()):
            break
        lead.append(chunk[i])
        i += 1
    lsatb: list[str] = []
    while i < len(chunk):
        raw = chunk[i].rstrip("\n\r")
        if not parse_regelidentifier(raw.lstrip()):
            break
        lsatb.append(chunk[i])
        i += 1
    trail = chunk[i:]
    return lead, lsatb, trail


def _count_measures_in_lsatb(lsatb: list[str]) -> int:
    for raw in lsatb:
        line = raw.rstrip("\n\r")
        rid = parse_regelidentifier(line.lstrip())
        if not rid:
            continue
        if not is_lyrics_stem(rid.stem_id):
            continue
        content = line.lstrip()[rid.match_end :].lstrip()
        split = _split_bars(content)
        return max(len(split.segments), 1)
    # No L-line: fall back to first stem.
    for raw in lsatb:
        line = raw.rstrip("\n\r")
        rid = parse_regelidentifier(line.lstrip())
        if not rid:
            continue
        content = line.lstrip()[rid.match_end :].lstrip()
        split = _split_bars(content)
        return max(len(split.segments), 1)
    return 1
