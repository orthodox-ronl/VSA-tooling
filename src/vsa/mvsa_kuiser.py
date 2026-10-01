"""Kuiser: canonieke authoring-vorm voor .mvsa (draft-v0).

Past de kuiser-toleranties uit de draft-spec toe:

1. op L: canonieke standaard-lengte als ``~`` (niet kale ELM-``-``);
   samengestelde ELM’s zoals ``-.`` blijven; input-``-`` als duur mag;
2. waarschuwing bij ambiguë ``-`` (regel + kolom) — geen stille
   ``hei- li``→``hei-li``-collapse (dat breekt o.a. ``…_&_  -li``);
3. semantische woordstreepjes: waarschuwing bij ontbrekende streepjes
   wanneer Pyphen de lettergrepen exact zo zou splitsen;
4. maatstrepen syncen waar eenduidig;
5. daarna :func:`vsa.mvsa_normalize.normalize_mvsa_text` (pitch + align).

Canonieke woordstreep met extra breedte: spaties **vóór** het streepje
(``hei_&_&_  -li``), nooit ``hei-_&…`` / ``le-  lu``.

Zie docs/specification-mvsa/syntax.md en semantics.md § Canonieke layout.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .mvsa_align import _l_tokens, _voice_tokens
from .mvsa_normalize import (
    DEFAULT_MVSA_PITCH,
    MvsaNormalizeError,
    normalize_mvsa_text,
)
from .mvsa_parse import _ELMS, _is_syllable_char, _is_woordstreepje, parse_l_positions
from .mvsa_validate import (
    MvsaValidationError,
    _BarSplit,
    _bar_starts_at,
    _read_bar_anchor,
    _split_bars,
    is_lyrics_stem,
    parse_regelidentifier,
    validate_mvsa_text,
)
from .syllabify import dehyphenate_dutch_word, hyphenate_dutch_word

# ``letter-`` + witruimte + letter: mogelijk woordstreepje i.p.v. ELM.
# Niet na ``&`` (melisma-slot ``…&-  ia`` is eenduidig ELM).
_AMBIGUOUS_DASH = re.compile(r"(?<=[^\W_&])-(?=\s+[^\W_])", re.UNICODE)


class MvsaKuiserError(Exception):
    def __init__(self, message: str, *, line: int = 0) -> None:
        self.line = line
        super().__init__(message)


@dataclass(frozen=True)
class KuiserWarning:
    """Advisory note (does not fail kuiser by itself)."""

    line: int
    column: int  # 1-based in the source line
    message: str

    def format(self, path: Path | None = None) -> str:
        loc = f"{path}:" if path else ""
        return f"{loc}{self.line}:{self.column}: WARNING: {self.message}"


@dataclass
class KuiserResult:
    text: str
    warnings: list[KuiserWarning]


def kuiser_mvsa_text(
    text: str,
    *,
    pitch: str = DEFAULT_MVSA_PITCH,
    octave_style: str = "@oct",
    align: bool = True,
) -> KuiserResult:
    """Return kuiser-canonieke mvsa-tekst + eventuele waarschuwingen."""
    repaired, warnings = _repair_systems(text)
    try:
        out = normalize_mvsa_text(
            repaired, pitch=pitch, octave_style=octave_style, align=align
        )
    except MvsaValidationError:
        raise
    except MvsaNormalizeError as exc:
        raise MvsaKuiserError(str(exc), line=exc.line) from exc

    errors = [d for d in validate_mvsa_text(out) if d.severity == "error"]
    if errors:
        raise MvsaValidationError(errors)
    return KuiserResult(text=out, warnings=warnings)


def kuiser_mvsa_path(
    path: Path,
    out: Path | None = None,
    *,
    pitch: str = DEFAULT_MVSA_PITCH,
    octave_style: str = "@oct",
    align: bool = True,
    check: bool = False,
) -> tuple[bool, list[KuiserWarning]]:
    """Kuis ``path``. Returns ``(changed, warnings)``.

    ``out`` None → in-place. ``check`` True → geen schrijfactie.
    """
    text = path.read_text(encoding="utf-8-sig")
    result = kuiser_mvsa_text(
        text, pitch=pitch, octave_style=octave_style, align=align
    )
    changed = result.text != text
    if check:
        return changed, result.warnings
    target = out if out is not None else path
    if changed or out is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(result.text, encoding="utf-8", newline="\n")
    return changed, result.warnings


def _repair_systems(text: str) -> tuple[str, list[KuiserWarning]]:
    """L-ELM-canonisatie + ambigu-dash-warnings + maatstreep-sync."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    warnings: list[KuiserWarning] = []
    i = 0
    while i < len(lines):
        raw = lines[i].rstrip("\n\r")
        rid0 = parse_regelidentifier(raw.lstrip())
        if not rid0:
            out.append(lines[i])
            i += 1
            continue

        system_lines: list[tuple[str, str | None, str, str, int, int]] = []
        j = i
        while j < len(lines):
            r = lines[j].rstrip("\n\r")
            rid = parse_regelidentifier(r.lstrip())
            if not rid:
                break
            indent = len(r) - len(r.lstrip())
            after_colon = r.lstrip()[rid.match_end :]
            stripped_lead = len(after_colon) - len(after_colon.lstrip())
            content_start = indent + rid.match_end + stripped_lead
            content = after_colon.lstrip()
            eol = lines[j][len(r) :] or "\n"
            system_lines.append(
                (rid.stem_id, rid.ehm, content, eol, j + 1, content_start)
            )
            j += 1

        order = [mk for mk, *_ in system_lines]
        contents = {mk: c for mk, _, c, *_ in system_lines}
        start_line = i + 1

        for mk, _ehm, content, _eol, line_no, content_start in system_lines:
            if not is_lyrics_stem(mk):
                continue
            warnings.extend(
                _ambiguous_dash_warnings(content, line_no, content_start)
            )
            warnings.extend(
                _semantic_hyphen_warnings(content, line_no, content_start)
            )
            contents[mk] = _canonicalize_l_standard_elms(content)

        try:
            contents = _sync_bars(contents, order, line=start_line)
        except MvsaKuiserError:
            raise
        except ValueError as exc:
            raise MvsaKuiserError(str(exc), line=start_line) from exc

        for mk, ehm, _, eol, *_rest in system_lines:
            label = f"{mk}{ehm}" if ehm else mk
            out.append(f"{label}: {contents[mk]}{eol}")
        i = j
    return "".join(out), warnings


def _ambiguous_dash_warnings(
    content: str, line_no: int, content_start: int
) -> list[KuiserWarning]:
    """Warn when ``letter-`` + spaces + letter may be a mistyped woordstreepje."""
    warnings: list[KuiserWarning] = []
    for m in _AMBIGUOUS_DASH.finditer(content):
        col = content_start + m.start() + 1
        warnings.append(
            KuiserWarning(
                line_no,
                col,
                "ambiguë '-' op L: parser leest dit als ELM-standaardduur. "
                "Bedoelde je een woordstreepje? Schrijf '-li' of '  -li' "
                "(streepje direct vóór de lettergreep; spaties ervóór OK). "
                "Bedoelde je duur? Schrijf liever '~'.",
            )
        )
    # Spec-pitfall: ELM-`-` direct vóór een woordstreepje (`li-&--ge`).
    for m in re.finditer(r"-&--(?=[^\s\-|&:])", content):
        col = content_start + m.start() + 1
        warnings.append(
            KuiserWarning(
                line_no,
                col,
                "ambiguë '-&--' op L: schrijf liever melisma met '~' "
                "(bijv. 'li~&~-ge'), niet 'li-&--ge'.",
            )
        )
    return warnings


def _semantic_hyphen_warnings(
    content: str, line_no: int, content_start: int
) -> list[KuiserWarning]:
    """Warn on missing / spurious woordstreepjes via Pyphen (exact match only)."""
    warnings: list[KuiserWarning] = []
    split = _split_bars(content)

    def flush(cores: list[str], linked_to_prev: list[bool]) -> None:
        warnings.extend(
            _warn_missing_hyphens_in_run(
                cores, linked_to_prev, line_no, content_start
            )
        )
        warnings.extend(
            _warn_spurious_hyphen_links(
                cores, linked_to_prev, line_no, content_start
            )
        )

    for seg in split.segments:
        try:
            positions = parse_l_positions(seg)
        except Exception:
            continue
        cores: list[str] = []
        linked_to_prev: list[bool] = []
        for p in positions:
            if p.recite:
                flush(cores, linked_to_prev)
                cores = []
                linked_to_prev = []
                continue
            if not p.syllables:
                continue
            core = _syllable_letters(p.syllables[0])
            if not core:
                continue
            cores.append(core)
            linked_to_prev.append(bool(p.continues_word))
        flush(cores, linked_to_prev)
    return warnings


def _syllable_letters(syll: str) -> str:
    return "".join(ch for ch in syll if ch.isalpha() or ch in "'’ʹ")


def _is_latin_core(core: str) -> bool:
    """Pyphen nl_NL is only meaningful for Latin-script syllables."""
    letters = [ch for ch in core if ch.isalpha()]
    return bool(letters) and all(
        ("A" <= ch <= "Z") or ("a" <= ch <= "z") for ch in letters
    )


def _warn_missing_hyphens_in_run(
    cores: list[str],
    linked_to_prev: list[bool],
    line_no: int,
    content_start: int,
) -> list[KuiserWarning]:
    """One warning per maximal unlinked run that Pyphen would hyphenate identically."""
    if len(cores) < 2:
        return []
    if not all(_is_latin_core(c) for c in cores):
        return []
    warnings: list[KuiserWarning] = []
    i = 0
    while i < len(cores):
        group = [cores[i]]
        j = i + 1
        grew_without_link = False
        while j < len(cores):
            if linked_to_prev[j]:
                # Already-correct woordstreepjes: don't fold into a Pyphen-miss warning.
                if grew_without_link:
                    break
                group.append(cores[j])
                j += 1
                continue
            # Don't glue a new capitalized word onto a lowercase/title run.
            if (
                cores[j][:1].isupper()
                and any(c[:1].islower() for c in group)
            ):
                break
            candidate = group + [cores[j]]
            joined = dehyphenate_dutch_word("".join(candidate))
            expected_parts = hyphenate_dutch_word(joined).split("-")
            if [p.lower() for p in expected_parts] == [
                p.lower() for p in candidate
            ]:
                group.append(cores[j])
                grew_without_link = True
                j += 1
                continue
            break
        if grew_without_link:
            warnings.append(
                KuiserWarning(
                    line_no,
                    content_start + 1,
                    "ontbrekend woordstreepje op L: "
                    f"{' '.join(group)} → {'-'.join(group)} (Pyphen). "
                    "Canoniek: streepje direct vóór de volgende lettergreep.",
                )
            )
        i = j if j > i else i + 1
    return warnings


def _warn_spurious_hyphen_links(
    cores: list[str],
    linked_to_prev: list[bool],
    line_no: int,
    content_start: int,
) -> list[KuiserWarning]:
    """Warn when continues_word likely joins two separate words.

    Conservative: both sides start with a capital (``God-Is``), Latin-only,
    and Pyphen does not break after the left part. Liturgical splits such as
    ``lu-ia`` stay silent.
    """
    warnings: list[KuiserWarning] = []
    for i in range(1, len(cores)):
        if not linked_to_prev[i]:
            continue
        left = cores[i - 1]
        right = cores[i]
        if not _is_latin_core(left) or not _is_latin_core(right):
            continue
        if not (left[:1].isupper() and right[:1].isupper()):
            continue
        if len(left) < 2 or len(right) < 2:
            continue
        joined = dehyphenate_dutch_word(left + right)
        hyp = hyphenate_dutch_word(joined)
        parts = hyp.split("-")
        acc = ""
        break_after_left = False
        for part in parts:
            acc += part
            if acc.lower() == left.lower():
                break_after_left = True
                break
        if break_after_left:
            continue
        warnings.append(
            KuiserWarning(
                line_no,
                content_start + 1,
                "mogelijk woordstreepje tussen woorden op L: "
                f"'{left}-{right}' (Pyphen: '{hyp}'). "
                "Tussen woorden hoort een spatie, geen '-'.",
            )
        )
    return warnings


def _canonicalize_l_standard_elms(content: str) -> str:
    """Rewrite bare ELM ``-`` → ``~`` on L; keep ``-.`` and woordstreepjes."""
    dashes = _bare_elm_dash_indices(content)
    if not dashes:
        return content
    chars = list(content)
    for idx in dashes:
        chars[idx] = "~"
    return "".join(chars)


def _bare_elm_dash_indices(s: str) -> list[int]:
    """0-based indices of bare ELM ``-`` in L content (not ``-.`` / woordstreep / bars)."""
    found: list[int] = []
    i = 0
    n = len(s)
    while i < n:
        bar = _bar_starts_at(s, i)
        if bar:
            i += len(bar)
            _anchor, i = _read_bar_anchor(s, i)
            continue
        if s[i].isspace() or s[i] in ",;:!?":
            i += 1
            continue
        if s[i] == ".":
            is_elm_dot = any(
                s.startswith(e, i) and e in (".", "..", "_.", "-.", "~.")
                for e in _ELMS
            )
            if not is_elm_dot:
                i += 1
                continue

        if s[i] == "(":
            close = s.find(")", i + 1)
            if close < 0:
                break
            i = close + 1
            dash_at, i = _read_elms_dash_indices(s, i, allow_bare_dash=False)
            found.extend(dash_at)
            continue

        # Stray woordstreepje not before a letter: skip (same as parse_l_positions).
        if _is_woordstreepje(s[i]) and not (i + 1 < n and _is_syllable_char(s[i + 1])):
            i += 1
            continue

        if _is_woordstreepje(s[i]) and i + 1 < n and _is_syllable_char(s[i + 1]):
            i += 1  # woordstreepje

        leading, i = _read_elms_dash_indices(s, i)
        found.extend(leading)

        while i < n:
            if _bar_starts_at(s, i):
                break
            start = i
            while i < n and (_is_syllable_char(s[i]) or s[i] in "'’ʹ"):
                i += 1
            if i == start:
                break
            while i < n and s[i] in ",;:!?":
                i += 1
            dash_at, i = _read_elms_dash_indices(s, i)
            found.extend(dash_at)
            while i < n and s[i] in ",;:!?":
                i += 1
            if (
                i < n
                and _is_woordstreepje(s[i])
                and i + 1 < n
                and _is_syllable_char(s[i + 1])
            ):
                i += 1
                continue
            break
    return found


def _read_elms_dash_indices(
    s: str, i: int, *, allow_bare_dash: bool = True
) -> tuple[list[int], int]:
    """Like ``_read_elms``, but returns indices of bare ``-`` ELMs."""
    n = len(s)
    dash_at: list[int] = []
    while True:
        if _bar_starts_at(s, i):
            break
        elm = None
        for e in _ELMS:
            if not s.startswith(e, i):
                continue
            if e == "-" and i + 1 < n and _is_syllable_char(s[i + 1]):
                continue
            if e == "-" and not allow_bare_dash:
                continue
            elm = e
            break
        if elm is None:
            break
        if elm == "-":
            dash_at.append(i)
        i += len(elm)
        if i < n and s[i] == "&":
            i += 1
            continue
        break
    return dash_at, i


def _sync_bars(
    contents: dict[str, str], order: list[str], *, line: int
) -> dict[str, str]:
    """Copy unambiguous bar tokens onto lines that lack the full sequence."""
    if not any(is_lyrics_stem(m) for m in order):
        return contents

    splits = {m: _split_bars(contents[m]) for m in order}
    ref_bars, ref_leading, ref_marker = _pick_ref_bars(splits, order, line=line)
    if not ref_bars:
        return contents

    widths = _measure_widths(splits[ref_marker], ref_marker)
    if len(widths) != len(ref_bars):
        raise MvsaKuiserError(
            f"interne maat-telling ({len(widths)}) ≠ strepen ({len(ref_bars)})",
            line=line,
        )

    result: dict[str, str] = {}
    for m in order:
        sp = splits[m]
        if (
            sp.bar_tokens == ref_bars
            and sp.leading_bar == ref_leading
            and not sp.trailing_text
        ):
            result[m] = contents[m]
            continue
        flat = _flat_positions(sp, m)
        need = sum(widths)
        if len(flat) != need:
            raise MvsaKuiserError(
                f"{m}: kan maatstrepen niet syncen "
                f"(posities {len(flat)} ≠ verwacht {need} t.o.v. {ref_marker})",
                line=line,
            )
        segments: list[str] = []
        idx = 0
        for w in widths:
            chunk = flat[idx : idx + w]
            idx += w
            segments.append(_join_positions(chunk, m))
        anchors = [None] * len(ref_bars)
        if sp.bar_tokens == ref_bars and sp.bar_anchors:
            anchors = list(sp.bar_anchors)
        result[m] = _join_segments(segments, ref_bars, anchors, ref_leading)
    return result


def _pick_ref_bars(
    splits: dict[str, _BarSplit],
    order: list[str],
    *,
    line: int,
) -> tuple[list[str], str | None, str]:
    sequences = [(m, splits[m]) for m in order if splits[m].bar_tokens]
    if not sequences:
        return [], None, order[0]

    max_len = max(len(sp.bar_tokens) for _, sp in sequences)
    maximal = [(m, sp) for m, sp in sequences if len(sp.bar_tokens) == max_len]
    uniq_bars = {tuple(sp.bar_tokens) for _, sp in maximal}
    if len(uniq_bars) != 1:
        raise MvsaKuiserError(
            "maatstrepen niet eenduidig tussen LSATB-regels: "
            + ", ".join(f"{m}={list(sp.bar_tokens)}" for m, sp in maximal),
            line=line,
        )
    ref_bars = list(uniq_bars.pop())

    leadings = {sp.leading_bar for _, sp in maximal}
    if len(leadings) != 1:
        raise MvsaKuiserError(
            f"leidende maatstreep niet eenduidig: "
            f"{sorted(leadings, key=lambda x: x or '')}",
            line=line,
        )
    ref_leading = next(iter(leadings))

    for m, sp in maximal:
        if is_lyrics_stem(m):
            return ref_bars, ref_leading, m
    return ref_bars, ref_leading, maximal[0][0]


def _measure_widths(split: _BarSplit, marker: str) -> list[int]:
    widths: list[int] = []
    for seg in split.segments:
        if is_lyrics_stem(marker):
            widths.append(len(_l_tokens(seg)))
        else:
            widths.append(len(_voice_tokens(seg)))
    return widths


def _flat_positions(split: _BarSplit, marker: str) -> list[str]:
    toks: list[str] = []
    parts = list(split.segments)
    if split.trailing_text.strip():
        parts.append(split.trailing_text)
    for seg in parts:
        if is_lyrics_stem(marker):
            toks.extend(_l_tokens(seg))
        else:
            toks.extend(_voice_tokens(seg))
    return toks


def _join_positions(tokens: list[str], marker: str) -> str:
    if not tokens:
        return ""
    if is_lyrics_stem(marker):
        parts: list[str] = [tokens[0]]
        for t in tokens[1:]:
            if t.startswith("-"):
                parts.append(t)
            else:
                parts.append(" ")
                parts.append(t)
        return "".join(parts)
    return " ".join(tokens)


def _join_segments(
    segments: list[str],
    bar_tokens: list[str],
    anchors: list[str | None],
    leading: str | None,
) -> str:
    parts: list[str] = []
    if leading:
        parts.append(leading)
        if segments:
            parts.append(" ")
    for i, seg in enumerate(segments):
        parts.append(seg.rstrip())
        if i < len(bar_tokens):
            parts.append(" ")
            anchor = ""
            if i < len(anchors) and anchors[i]:
                anchor = anchors[i] or ""
            parts.append(bar_tokens[i] + anchor)
            if i + 1 < len(segments):
                parts.append(" ")
    return "".join(parts).rstrip()
