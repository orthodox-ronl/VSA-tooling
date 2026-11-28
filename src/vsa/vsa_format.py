"""``vsa format`` — body-layout voor strofen (docs/formats/vsa-format.md)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .parser import BRACKET_DIRECTIVE_END, EHM_VALUES, ELM_VALUES
from .vsa_stanzas import (
    _STANZA_MARKERS_LONGEST,
    fold_indent_continuations,
    strip_html_comments,
)
from .yaml_frontmatter import strip_yaml_frontmatter

Boundary = Literal["star", "slash", "newline"]
Layout = Literal["lines", "flow"]

WRAP_INDENT = "    "
_WRAP_INDENT_BUDGET = len(WRAP_INDENT)  # 4 — telt mee in --wrap-budget

# Frasegrenzen (langste eerst) — budget = lengte van de marker.
_PHRASE_MARKERS = ("**", "//", "*", "/")
_PHRASE_MARKER_SET = frozenset(_PHRASE_MARKERS)

# ELM’s buiten scopes die géén zichtbare leestekens zijn.
# ``.`` / ``..`` tellen buiten scopes als leesteken (zichtbaar).
_ELM_SKIP_OUTSIDE = tuple(
    v for v in ELM_VALUES if v not in {".", ".."}
)


class VsaFormatError(ValueError):
    """Ongeldige format-opties of niet-formateerbare bron."""


@dataclass(frozen=True)
class VsaFormatResult:
    text: str
    changed: bool


@dataclass(frozen=True)
class _Phrase:
    text: str
    # Marker die ná deze frase stond (``*``/``**``/``/``/``//``), of None.
    marker_after: str | None


def format_vsa_text(
    text: str,
    *,
    boundary: Boundary = "star",
    layout: Layout = "lines",
    wrap: int = 0,
) -> VsaFormatResult:
    """Herschrijf strofe-layout; YAML-FM blijft onaangeroerd."""
    _validate_combo(boundary, layout)
    _validate_wrap(wrap)

    bom = ""
    original = text
    if text.startswith("\ufeff"):
        bom = "\ufeff"
        text = text[1:]

    fm, body, _ = strip_yaml_frontmatter(text)
    new_body = format_vsa_body(
        body, boundary=boundary, layout=layout, wrap=wrap
    )

    if not fm:
        out = bom + new_body
        if not out.endswith("\n") and out:
            out += "\n"
        return VsaFormatResult(text=out, changed=out != original)

    if text.startswith("---"):
        close = text.find("\n---", 3)
        if close != -1:
            fm_bytes = text[: close + len("\n---")]
            rest = text[close + len("\n---") :]
            lead = rest[: len(rest) - len(rest.lstrip("\n"))]
            if new_body and not lead:
                lead = "\n"
            out = bom + fm_bytes + lead + new_body
            if not out.endswith("\n"):
                out += "\n"
            return VsaFormatResult(text=out, changed=out != original)

    out = bom + new_body
    if not out.endswith("\n") and out:
        out += "\n"
    return VsaFormatResult(text=out, changed=out != original)


def format_vsa_body(
    body: str,
    *,
    boundary: Boundary = "star",
    layout: Layout = "lines",
    wrap: int = 0,
) -> str:
    """Alleen body (geen YAML)."""
    _validate_combo(boundary, layout)
    _validate_wrap(wrap)
    phrases = extract_phrases(body)
    if not phrases:
        return body if body.endswith("\n") or not body else body + "\n"
    return _emit_phrases(
        phrases, boundary=boundary, layout=layout, wrap=wrap
    )


def extract_phrases(body: str) -> list[_Phrase]:
    """Haal strofen uit de body (markers of newline+indent)."""
    cleaned = strip_html_comments(body)
    raw_music = [
        ln
        for ln in cleaned.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    if not raw_music:
        return []

    folded = fold_indent_continuations(raw_music)
    joined = " ".join(ln.strip() for ln in folded)
    if _has_marker_token(joined):
        return _split_marked_phrases(joined)

    return [_Phrase(text=ln.strip(), marker_after=None) for ln in folded if ln.strip()]


def format_vsa_path(
    path: Path,
    out: Path | None = None,
    *,
    boundary: Boundary = "star",
    layout: Layout = "lines",
    wrap: int = 0,
    check: bool = False,
) -> tuple[bool, VsaFormatResult]:
    """Format ``path``. Returns ``(changed, result)``."""
    original = path.read_text(encoding="utf-8-sig")
    result = format_vsa_text(
        original, boundary=boundary, layout=layout, wrap=wrap
    )
    changed = result.text != original
    if check:
        return changed, result
    target = out if out is not None else path
    if changed or out is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(result.text, encoding="utf-8", newline="\n")
    return changed, result


def visible_budget(text: str) -> int:
    """Zichtbare-tekst-budget (docs/formats/vsa-format.md ``--wrap``)."""
    total = 0
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "[":
            end = text.find(BRACKET_DIRECTIVE_END, i)
            if end != -1:
                total += 2
                i = end + len(BRACKET_DIRECTIVE_END)
                continue
            # Misvormd: skip ``[`` als pure syntax.
            i += 1
            continue
        if ch == "{":
            end = text.find("}", i + 1)
            if end == -1:
                i += 1
                continue
            total += _scope_sung_budget(text[i + 1 : end])
            i = end + 1
            continue
        if ch == "&":
            i += 1
            continue
        marker = _match_prefix(text, i, _PHRASE_MARKERS)
        if marker is not None:
            total += len(marker)
            i += len(marker)
            continue
        if ch == "-" and _is_soft_hyphen_at(text, i):
            total += 1
            i += 1
            continue
        elm = _match_prefix(text, i, _ELM_SKIP_OUTSIDE)
        if elm is not None:
            # Soft ``-`` is hierboven al geteld; hier o.a. trailing ELM-``-``.
            i += len(elm)
            continue
        if ch in "{}[]\\":
            # Pure syntax / losse EHM-achtige backslash.
            i += 1
            continue
        # Letters, spaties, leestekens, ``=``, overige zichtbare tekens.
        total += 1
        i += 1
    return total


def split_wrap_units(text: str) -> list[str]:
    """Split op spaties buiten ``{…}`` en ``[…]``."""
    units: list[str] = []
    buf: list[str] = []
    depth_brace = 0
    depth_bracket = 0
    for ch in text:
        if ch == "{" and depth_bracket == 0:
            depth_brace += 1
            buf.append(ch)
        elif ch == "}" and depth_bracket == 0 and depth_brace > 0:
            depth_brace -= 1
            buf.append(ch)
        elif ch == "[" and depth_brace == 0:
            depth_bracket += 1
            buf.append(ch)
        elif ch == "]" and depth_brace == 0 and depth_bracket > 0:
            depth_bracket -= 1
            buf.append(ch)
        elif ch == " " and depth_brace == 0 and depth_bracket == 0:
            if buf:
                units.append("".join(buf))
                buf = []
        else:
            buf.append(ch)
    if buf:
        units.append("".join(buf))
    return units


def wrap_text_lines(text: str, wrap: int) -> list[str]:
    """Soft-wrap ``text`` op budget ``wrap``; voortzetting met 4 spaties.

    De indent telt mee (voortzetting: ``N − 4`` inhoud). Strofe-delimiters
    worden nooit alleen op een nieuwe regel gezet.
    """
    if wrap <= 0:
        return [text] if text else []
    _validate_wrap(wrap)
    units = split_wrap_units(text.strip())
    if not units:
        return [text.strip()] if text.strip() else []

    content_lines: list[list[str]] = []
    current: list[str] = []

    def _start_budget(line_index: int) -> int:
        return 0 if line_index == 0 else _WRAP_INDENT_BUDGET

    line_index = 0
    current_budget = 0

    for unit in units:
        ub = visible_budget(unit)
        marker_only = unit in _PHRASE_MARKER_SET
        if not current:
            current_budget = _start_budget(line_index) + ub
            current = [unit]
            continue
        needed = current_budget + 1 + ub
        if needed <= wrap or marker_only:
            current.append(unit)
            current_budget = needed
            continue
        content_lines.append(current)
        line_index = len(content_lines)
        current = [unit]
        current_budget = _start_budget(line_index) + ub

    if current:
        content_lines.append(current)

    # Delimiter nooit alleen op een (voortzettings)regel.
    while (
        len(content_lines) >= 2
        and content_lines[-1]
        and all(u in _PHRASE_MARKER_SET for u in content_lines[-1])
    ):
        content_lines[-2].extend(content_lines.pop())

    out: list[str] = []
    for i, units_line in enumerate(content_lines):
        body = " ".join(units_line)
        if i == 0:
            out.append(body)
        else:
            out.append(WRAP_INDENT + body)
    return out


def _validate_combo(boundary: Boundary, layout: Layout) -> None:
    if boundary == "newline" and layout == "flow":
        raise VsaFormatError(
            "combinatie --boundary newline met --layout flow is niet "
            "toegestaan (doorlopende tekst vereist * of /)."
        )


def _validate_wrap(wrap: int) -> None:
    if wrap < 0:
        raise VsaFormatError(
            "--wrap moet 0 of een geheel getal ≥ 4 zijn."
        )
    if 0 < wrap < _WRAP_INDENT_BUDGET:
        raise VsaFormatError(
            f"--wrap {wrap} is te klein: voortzettingsindent is "
            f"{_WRAP_INDENT_BUDGET} spaties (kies 0 of ≥ {_WRAP_INDENT_BUDGET})."
        )


def _has_marker_token(text: str) -> bool:
    for tok in text.split():
        if _peel_end_marker(tok)[0] is not None:
            return True
        if tok in {"*", "**", "/", "//"}:
            return True
    return False


def _peel_end_marker(token: str) -> tuple[str | None, str]:
    for marker in _STANZA_MARKERS_LONGEST:
        if token == marker:
            return marker, ""
        if token.endswith(marker):
            # Geen EHM-achtige ``{/…}`` als geheel token.
            core = token[: -len(marker)]
            return marker, core
    return None, token


def _split_marked_phrases(joined: str) -> list[_Phrase]:
    phrases: list[_Phrase] = []
    buf: list[str] = []
    for tok in joined.split():
        marker, core = _peel_end_marker(tok)
        if marker is None:
            buf.append(tok)
            continue
        if core:
            buf.append(core)
        text = " ".join(buf).strip()
        buf = []
        if text or phrases:
            phrases.append(_Phrase(text=text, marker_after=marker))
        elif not text:
            # Marker zonder voorafgaande tekst: negeer losse rommel.
            continue
    tail = " ".join(buf).strip()
    if tail:
        phrases.append(_Phrase(text=tail, marker_after=None))
    return [p for p in phrases if p.text]


def _weak_marker(boundary: Boundary) -> str:
    if boundary == "star":
        return "*"
    if boundary == "slash":
        return "/"
    return ""


def _strong_marker(boundary: Boundary) -> str:
    if boundary == "star":
        return "**"
    if boundary == "slash":
        return "//"
    return ""


def _map_marker(old: str | None, boundary: Boundary) -> str:
    if boundary == "newline":
        return ""
    if old in {"**", "//"}:
        return _strong_marker(boundary)
    return _weak_marker(boundary)


def _emit_phrases(
    phrases: list[_Phrase],
    *,
    boundary: Boundary,
    layout: Layout,
    wrap: int = 0,
) -> str:
    n = len(phrases)
    parts: list[str] = []
    for i, phrase in enumerate(phrases):
        is_last = i == n - 1
        if is_last:
            marker = ""
        elif phrase.marker_after:
            marker = _map_marker(phrase.marker_after, boundary)
        else:
            marker = _weak_marker(boundary)

        chunk = phrase.text
        if marker:
            # Houd marker bij de laatste wrap-eenheid (niet alleen op lege regel).
            chunk = f"{chunk} {marker}"
        parts.append(chunk.strip())

    if layout == "flow":
        line = " ".join(parts)
        if wrap > 0:
            return "\n".join(wrap_text_lines(line, wrap)) + "\n"
        return line + "\n"

    out_lines: list[str] = []
    for chunk in parts:
        if wrap > 0:
            out_lines.extend(wrap_text_lines(chunk, wrap))
        else:
            out_lines.append(chunk)
    return "\n".join(out_lines) + "\n"


def _match_prefix(text: str, index: int, options: tuple[str, ...]) -> str | None:
    for opt in options:
        if text.startswith(opt, index):
            return opt
    return None


def _is_soft_hyphen_at(text: str, index: int) -> bool:
    """``-`` tussen lyric-tekens (letter/cijfer/``=``-context) telt als soft hyphen."""
    if index <= 0 or index + 1 >= len(text):
        return False
    if text[index] != "-":
        return False
    left = text[index - 1]
    right = text[index + 1]
    return _is_lyric_char(left) and _is_lyric_char(right)


def _is_lyric_char(ch: str) -> bool:
    return ch.isalnum() or ch in {"=", "'", "’"}


def _scope_sung_budget(content: str) -> int:
    """Budget voor scope-inhoud: alleen zangelement (geen EHM/ELM/`&`/`{}`)."""
    if not content:
        return 0
    element = _scope_element_text(content)
    total = 0
    i = 0
    while i < len(element):
        ch = element[i]
        if ch == "&":
            i += 1
            continue
        if ch == "-" and _is_soft_hyphen_at(element, i):
            total += 1
            i += 1
            continue
        if ch in "\\":
            i += 1
            continue
        total += 1
        i += 1
    return total


def _scope_element_text(content: str) -> str:
    """Beste EHM-prefix + ELM-suffix strip (zelfde idee als parser)."""
    # Prefix: herhaalde EHM’s met optionele ``&``.
    prefix_ends = {0}
    stack = [0]
    while stack:
        index = stack.pop()
        for value in EHM_VALUES:
            if content.startswith(value, index):
                nxt = index + len(value)
                if nxt not in prefix_ends:
                    prefix_ends.add(nxt)
                    stack.append(nxt)
                if content.startswith("&", nxt):
                    amp = nxt + 1
                    if amp not in prefix_ends:
                        prefix_ends.add(amp)
                        stack.append(amp)

    best_element = content
    best_score = -1
    n = len(content)
    for prefix_len in sorted(prefix_ends):
        for suffix_start in range(prefix_len, n + 1):
            suffix = content[suffix_start:]
            if suffix and not _is_elm_suffix(suffix):
                continue
            element = content[prefix_len:suffix_start]
            if not element:
                continue
            # Geen modifiertekens in het zangelement.
            if any(ch in "&~+\\/" for ch in element):
                continue
            score = prefix_len + (n - suffix_start)
            if score > best_score:
                best_score = score
                best_element = element
    return best_element


def _is_elm_suffix(suffix: str) -> bool:
    if not suffix:
        return True
    parts = suffix.split("&")
    if any(part == "" for part in parts):
        return False
    return all(part in ELM_VALUES for part in parts)
