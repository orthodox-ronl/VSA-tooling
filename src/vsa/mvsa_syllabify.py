"""Lettergreepstreepjes in .mvsa L-tekst (recite + cadens), sync-veilig.

Recite ``(…)``: soft ``-`` binnen woorden (spatie = woordgrens) — zelfde
Pyphen/dictionary-pad als ``vsa syllabify``. Cadens: één L-positie zonder
streepjes die Pyphen/dictionary als meerlettergrepig ziet, wordt een
hyphen-keten (``heerlijkheid_`` → ``heer_-lijk-heid_``); op elke stem in
hetzelfde systeem komen evenveel ``-``-holds bij, zodat MVSA-SYNC blijft
kloppen.

``--unsyllabify``: alleen soft ``-`` binnen recite weg; cadens-ketens worden
niet samengevoegd (dat zou stem-holds moeten schrappen).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from .mvsa_align import _format_lpos, _l_tokens, _voice_tokens, align_mvsa_text
from .mvsa_parse import LPosition, parse_l_positions
from .mvsa_validate import (
    _split_bars,
    is_lyrics_stem,
    parse_regelidentifier,
    validate_mvsa_text,
)
from .syllabify import (
    HARD_HYPHEN,
    SyllabifyResult,
    hyphenate_dutch_word,
    strip_soft_hyphens,
)


class MvsaSyllabifyError(ValueError):
    """Syllabify produceerde ongeldige .mvsa of kon een systeem niet herschrijven."""

    def __init__(self, message: str, *, line: int | None = None) -> None:
        super().__init__(message)
        self.line = line


@dataclass(frozen=True)
class MvsaSyllabifyResult(SyllabifyResult):
    """Alias: zelfde velden als VSA ``SyllabifyResult``."""


def syllabify_mvsa_text(
    text: str,
    *,
    unsyllabify: bool = False,
    align: bool = True,
) -> MvsaSyllabifyResult:
    """Herschrijf L-lyrics met soft ``-``; behoud sync met stemmen.

    YAML-frontmatter blijft onaangeroerd (geneste sleutels mogen niet als
    stemregel ``B…:`` gelezen worden).
    """
    from .yaml_frontmatter import strip_yaml_frontmatter

    bom = ""
    original = text
    if text.startswith("\ufeff"):
        bom = "\ufeff"
        text = text[1:]

    fm, body, line_base = strip_yaml_frontmatter(text)
    result = _syllabify_mvsa_body(
        body,
        unsyllabify=unsyllabify,
        align=align,
        line_base=line_base,
    )
    if not fm:
        out = bom + result.text
        return MvsaSyllabifyResult(
            text=out,
            changed=out != original,
            replacements=result.replacements,
        )

    if text.startswith("---"):
        close = text.find("\n---", 3)
        if close != -1:
            fm_bytes = text[: close + len("\n---")]
            rest = text[close + len("\n---") :]
            lead = rest[: len(rest) - len(rest.lstrip("\n"))]
            out = bom + fm_bytes + lead + result.text
            return MvsaSyllabifyResult(
                text=out,
                changed=out != original,
                replacements=result.replacements,
            )

    out = bom + result.text
    return MvsaSyllabifyResult(
        text=out,
        changed=out != original,
        replacements=result.replacements,
    )


def _syllabify_mvsa_body(
    text: str,
    *,
    unsyllabify: bool = False,
    align: bool = True,
    line_base: int = 0,
) -> MvsaSyllabifyResult:
    """Syllabify alleen de body (geen YAML-FM).

    ``line_base`` = aantal newlines vóór de body in het volledige bestand,
    zodat foutregels bestandregels zijn (niet body-relatief).
    """
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    replacements = 0
    i = 0
    while i < len(lines):
        raw = lines[i].rstrip("\n\r")
        rid0 = parse_regelidentifier(raw.lstrip())
        if not rid0:
            out.append(lines[i])
            i += 1
            continue

        system_lines: list[tuple[str, str | None, str, str]] = []
        j = i
        while j < len(lines):
            r = lines[j].rstrip("\n\r")
            rid = parse_regelidentifier(r.lstrip())
            if not rid:
                break
            content = r.lstrip()[rid.match_end :].lstrip()
            eol = lines[j][len(r) :] or "\n"
            system_lines.append((rid.stem_id, rid.ehm, content, eol))
            j += 1

        order = [mk for mk, *_ in system_lines]
        contents = {mk: c for mk, _, c, _ in system_lines}
        # 1-gebaseerd in het volledige bronbestand
        start_line = i + 1 + line_base

        if any(is_lyrics_stem(m) for m in order):
            try:
                new_contents, n = _syllabify_system(
                    contents,
                    order,
                    unsyllabify=unsyllabify,
                    start_line=start_line,
                )
            except MvsaSyllabifyError as exc:
                if exc.line is None:
                    raise MvsaSyllabifyError(
                        str(exc), line=start_line
                    ) from exc
                raise
            replacements += n
            contents = new_contents

        for mk, ehm, _, eol in system_lines:
            label = f"{mk}{ehm}" if ehm else mk
            out.append(f"{label}: {contents[mk]}{eol}")
        i = j

    if replacements == 0:
        return MvsaSyllabifyResult(text=text, changed=False, replacements=0)

    result_text = "".join(out)
    if align:
        try:
            result_text = align_mvsa_text(result_text)
        except ValueError as exc:
            raise MvsaSyllabifyError(
                f"align na syllabify mislukt: {exc}"
            ) from exc

    errors = [d for d in validate_mvsa_text(result_text) if d.severity == "error"]
    if errors:
        first = errors[0]
        body_line = first.line if first.line else 1
        raise MvsaSyllabifyError(
            f"resultaat ongeldig ({first.code}): {first.message}",
            line=body_line + line_base,
        )

    return MvsaSyllabifyResult(
        text=result_text,
        changed=result_text != text,
        replacements=replacements,
    )



def syllabify_mvsa_path(
    path: Path,
    out: Path | None = None,
    *,
    unsyllabify: bool = False,
    align: bool = True,
    check: bool = False,
) -> tuple[bool, MvsaSyllabifyResult]:
    """Syllabify ``path``. Returns ``(changed, result)``.

    ``out`` None → in-place. ``check`` True → geen schrijfactie.
    """
    original = path.read_text(encoding="utf-8-sig")
    result = syllabify_mvsa_text(
        original, unsyllabify=unsyllabify, align=align
    )
    changed = result.text != original
    if check:
        return changed, result
    target = out if out is not None else path
    if changed or out is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(result.text, encoding="utf-8", newline="\n")
    return changed, result


def _syllabify_system(
    contents: dict[str, str],
    order: list[str],
    *,
    unsyllabify: bool,
    start_line: int = 1,
) -> tuple[dict[str, str], int]:
    l_markers = [m for m in order if is_lyrics_stem(m)]
    if len(l_markers) != 1:
        raise MvsaSyllabifyError(
            "Syllabify ondersteunt precies één tekstregel (L) per blok.",
            line=start_line,
        )
    l_marker = l_markers[0]
    splits = {m: _split_bars(contents[m]) for m in order}
    n_seg = len(splits[l_marker].segments)
    for m in order:
        if len(splits[m].segments) != n_seg:
            raise MvsaSyllabifyError(
                f"Het aantal maten verschilt: tekstregel ({l_marker}) heeft "
                f"{n_seg} maat(en), regel {m}: heeft "
                f"{len(splits[m].segments)}.",
                line=start_line + order.index(m),
            )

    ref_bars = splits[l_marker].bar_tokens
    ref_leading = splits[l_marker].leading_bar
    replacements = 0
    out_segs: dict[str, list[str]] = {m: [] for m in order}

    for si in range(n_seg):
        l_seg = splits[l_marker].segments[si]
        positions = parse_l_positions(l_seg)
        original_tokens = _l_tokens(l_seg)
        if len(original_tokens) != len(positions):
            raise MvsaSyllabifyError(
                f"Op de tekstregel (L) klopt de telling niet in "
                f"{_maat_in_blok(si)} "
                f"({len(original_tokens)} stukken tekst vs "
                f"{len(positions)} posities).",
                line=start_line + order.index(l_marker),
            )
        new_tokens: list[str] = []
        expansions: list[int] = []
        for pos, orig_tok in zip(positions, original_tokens):
            expanded, n = _syllabify_position(pos, unsyllabify=unsyllabify)
            replacements += n
            expansions.append(len(expanded))
            if (
                n == 0
                and len(expanded) == 1
                and _lpos_lyrics_equal(pos, expanded[0])
            ):
                new_tokens.append(orig_tok)
            else:
                new_tokens.extend(
                    _format_lpos_preserving_marks(p) for p in expanded
                )

        out_segs[l_marker].append(_join_l_tokens(new_tokens))

        for m in order:
            if m == l_marker:
                continue
            v_toks = _voice_tokens(splits[m].segments[si])
            if len(positions) == 0 and len(v_toks) == 0:
                out_segs[m].append(splits[m].segments[si].rstrip())
                continue
            if len(v_toks) != len(positions):
                raise MvsaSyllabifyError(
                    _sync_mismatch_message(
                        l_count=len(positions),
                        voice=m,
                        voice_count=len(v_toks),
                        measure_index=si,
                    ),
                    line=start_line + order.index(m),
                )
            padded = _pad_voice_tokens(v_toks, expansions)
            out_segs[m].append(" ".join(padded))

    result: dict[str, str] = {}
    for m in order:
        anchors = list(splits[m].bar_anchors)
        result[m] = _join_bar_segments(
            out_segs[m],
            ref_bars,
            anchors,
            ref_leading,
        )
    return result, replacements


def _maat_in_blok(measure_index: int) -> str:
    """Menselijke plaatsaanduiding binnen één L/S/A/T/B-blok."""
    n = measure_index + 1
    return f"de {n}e maat van dit blok (L/S/A/T/B samen)"


def _sync_mismatch_message(
    *,
    l_count: int,
    voice: str,
    voice_count: int,
    measure_index: int,
) -> str:
    """Fouttekst wanneer L en een zangregel ongelijk aantal posities hebben."""
    plaats = _maat_in_blok(measure_index)
    return (
        f"Op de tekstregel (L) staan in {plaats} {l_count} posities, "
        f"op zangregel {voice}: {voice_count}. Die aantallen moeten gelijk "
        f"zijn. Syllabify zet alleen streepjes in de tekst; de noten op "
        f"S/A/T/B moeten daaronder blijven staan — daarom moet het eerst "
        f"kloppen."
    )


def _syllabify_position(
    pos: LPosition,
    *,
    unsyllabify: bool,
) -> tuple[list[LPosition], int]:
    if pos.recite:
        new_pos, n = _syllabify_recite(pos, unsyllabify=unsyllabify)
        return [new_pos], n
    if unsyllabify:
        return [pos], 0
    return _expand_non_recite(pos)


def _syllabify_recite(
    pos: LPosition,
    *,
    unsyllabify: bool,
) -> tuple[LPosition, int]:
    if not pos.syllables:
        return pos, 0
    words = _group_words(pos.syllables, pos.links, pos.hard_links)
    new_syllables: list[str] = []
    new_links: list[bool] = []
    new_hard: list[bool] = []
    replacements = 0
    for wi, (wsyl, wlinks, whard) in enumerate(words):
        parts, links, hard, n = _rewrite_word(
            wsyl, wlinks, whard, unsyllabify=unsyllabify
        )
        replacements += n
        if wi:
            new_links.append(False)
            new_hard.append(False)
        new_syllables.extend(parts)
        new_links.extend(links)
        new_hard.extend(hard)
    return (
        replace(
            pos,
            syllables=new_syllables,
            links=new_links,
            hard_links=new_hard,
        ),
        replacements,
    )


def _expand_non_recite(pos: LPosition) -> tuple[list[LPosition], int]:
    """Eén cadens-positie → hyphen-keten als het lemma meer lettergrepen heeft.

    Alleen het **begin** van een woord (niet ``continues_word``): anders wordt
    een al gedeelde vorm zoals ``ge`` + ``-neest`` (lemma ``ge-neest``) opnieuw
    door Pyphen op het stuk ``neest`` → ``nee-st`` gezet, met eindeloze
    dictionary-MISMATCH.
    """
    if len(pos.syllables) != 1:
        return [pos], 0
    if pos.continues_word:
        # Vervolgstuk van een al gesplitst woord — niet opnieuw hyphenëren.
        return [pos], 0
    surface = pos.syllables[0]
    if not any(ch.isalpha() for ch in surface):
        return [pos], 0
    if "-" in surface or HARD_HYPHEN in surface:
        # Al gedeeld binnen één token (zeldzaam); laat met rust.
        return [pos], 0
    hyp = hyphenate_dutch_word(surface)
    if hyp == surface:
        return [pos], 0
    parts, hard_flags = _split_hyphen_surface(hyp)
    if len(parts) <= 1:
        return [pos], 0

    out: list[LPosition] = []
    soft_added = 0
    for i, part in enumerate(parts):
        if i == 0:
            out.append(
                replace(
                    pos,
                    syllables=[part],
                    links=[],
                    hard_links=[],
                    elms=list(pos.elms) if pos.elms else ["~"],
                    marks_after=[],
                )
            )
        else:
            hard = hard_flags[i - 1]
            if not hard:
                soft_added += 1
            out.append(
                LPosition(
                    recite=False,
                    syllables=[part],
                    elms=[],
                    links=[],
                    hard_links=[],
                    continues_word=True,
                    continues_word_hard=hard,
                )
            )
    if pos.marks_after:
        out[-1] = replace(out[-1], marks_after=list(pos.marks_after))
    return out, soft_added


def _group_words(
    syllables: list[str],
    links: list[bool],
    hard_links: list[bool],
) -> list[tuple[list[str], list[bool], list[bool]]]:
    if not syllables:
        return []
    words: list[tuple[list[str], list[bool], list[bool]]] = []
    cur_s = [syllables[0]]
    cur_l: list[bool] = []
    cur_h: list[bool] = []
    for i, syl in enumerate(syllables[1:]):
        link = links[i] if i < len(links) else False
        hard = hard_links[i] if i < len(hard_links) else False
        if link:
            cur_s.append(syl)
            cur_l.append(True)
            cur_h.append(hard)
        else:
            words.append((cur_s, cur_l, cur_h))
            cur_s = [syl]
            cur_l = []
            cur_h = []
    words.append((cur_s, cur_l, cur_h))
    return words


def _rewrite_word(
    syllables: list[str],
    links: list[bool],
    hard_links: list[bool],
    *,
    unsyllabify: bool,
) -> tuple[list[str], list[bool], list[bool], int]:
    surface = _join_word_surface(syllables, links, hard_links)
    before = _count_soft_in_surface(surface)
    if unsyllabify:
        new_surface = _unsyllabify_preserving_hard(surface)
    else:
        new_surface = hyphenate_dutch_word(surface)
    after = _count_soft_in_surface(new_surface)
    parts, hard_flags = _split_hyphen_surface(new_surface)
    if not parts:
        return syllables, links, hard_links, 0
    new_links = [True] * (len(parts) - 1)
    n = abs(after - before)
    if n == 0 and (
        parts != syllables or hard_flags != list(hard_links)
    ):
        n = 1
    return parts, new_links, hard_flags, n


def _join_word_surface(
    syllables: list[str],
    links: list[bool],
    hard_links: list[bool],
) -> str:
    if not syllables:
        return ""
    out = syllables[0]
    for i, syl in enumerate(syllables[1:]):
        hard = i < len(hard_links) and hard_links[i]
        glue = HARD_HYPHEN if hard else "-"
        # links zouden True moeten zijn binnen een woord; forceer glue.
        out += glue + syl
    return out


def _unsyllabify_preserving_hard(surface: str) -> str:
    """Strip soft ``-``; hard ``=`` en lettertekst blijven."""
    if HARD_HYPHEN not in surface:
        return strip_soft_hyphens(surface)
    return HARD_HYPHEN.join(
        strip_soft_hyphens(part) for part in surface.split(HARD_HYPHEN)
    )


def _split_hyphen_surface(surface: str) -> tuple[list[str], list[bool]]:
    """Splits op soft ``-`` en hard ``=``; hard_flags[i] = link vóór parts[i+1]."""
    if not surface:
        return [], []
    parts: list[str] = []
    hard_flags: list[bool] = []
    buf: list[str] = []
    for ch in surface:
        if ch in "-=" and buf:
            parts.append("".join(buf))
            hard_flags.append(ch == HARD_HYPHEN)
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    elif not parts:
        parts.append("")
    return parts, hard_flags


def _count_soft_in_surface(surface: str) -> int:
    return surface.count("-")


def _lpos_lyrics_equal(a: LPosition, b: LPosition) -> bool:
    """True als lyrics/links/woorddoorloop gelijk zijn (ELM/marks mogen verschillen)."""
    return (
        a.recite == b.recite
        and a.syllables == b.syllables
        and a.links == b.links
        and a.hard_links == b.hard_links
        and a.continues_word == b.continues_word
        and a.continues_word_hard == b.continues_word_hard
    )


def _format_lpos_preserving_marks(pos: LPosition) -> str:
    before = "".join(f"[{m.raw}]" for m in pos.marks_before)
    after = "".join(f"[{m.raw}]" for m in pos.marks_after)
    # Marks vóór met spatie alleen als nodig voor leesbaarheid — canoniek
    # plakken zonder spatie: ``[cresc]heer_``.
    return f"{before}{_format_lpos(pos)}{after}"


def _join_l_tokens(tokens: list[str]) -> str:
    if not tokens:
        return ""
    parts: list[str] = [tokens[0]]
    for t in tokens[1:]:
        if t.startswith("-") or t.startswith("="):
            parts.append(t)
        else:
            parts.append(" ")
            parts.append(t)
    return "".join(parts)


def _pad_voice_tokens(tokens: list[str], expansions: list[int]) -> list[str]:
    out: list[str] = []
    for i, tok in enumerate(tokens):
        n = expansions[i] if i < len(expansions) else 1
        out.append(tok)
        for _ in range(max(0, n - 1)):
            out.append("-")
    return out


def resync_voice_tokens_to_l_count(
    tokens: list[str], target: int
) -> list[str]:
    """Maak stem-token-telling gelijk aan L-posities met alleen ``-``-houdtekens.

    Te veel tokens: verwijder pure ``-`` (van achteren). Te weinig: append ``-``.
    Pitch-tokens worden nooit verwijderd; lukt krimpen niet, blijft de rest staan.
    """
    out = list(tokens)
    while len(out) > target:
        removed = False
        for i in range(len(out) - 1, -1, -1):
            if out[i] == "-":
                del out[i]
                removed = True
                break
        if not removed:
            break
    while len(out) < target:
        out.append("-")
    return out


def resync_mvsa_voices_to_lyrics(text: str, *, align: bool = True) -> str:
    """Na L-herschrijving: per maat S/A/T/B-telling gelijk trekken aan L.

    YAML-frontmatter blijft onaangeroerd. Bij align-fout: tekst zonder align.
    """
    from .yaml_frontmatter import strip_yaml_frontmatter

    bom = ""
    if text.startswith("\ufeff"):
        bom = "\ufeff"
        text = text[1:]

    fm, body, _ = strip_yaml_frontmatter(text)
    new_body = _resync_mvsa_voices_body(body)
    if new_body == body:
        return bom + text

    if align:
        try:
            new_body = align_mvsa_text(new_body)
        except ValueError:
            pass

    if not fm:
        return bom + new_body

    if text.startswith("---"):
        close = text.find("\n---", 3)
        if close != -1:
            fm_bytes = text[: close + len("\n---")]
            rest = text[close + len("\n---") :]
            lead = rest[: len(rest) - len(rest.lstrip("\n"))]
            return bom + fm_bytes + lead + new_body

    return bom + new_body


def _resync_mvsa_voices_body(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    changed = False
    while i < len(lines):
        raw = lines[i].rstrip("\n\r")
        rid0 = parse_regelidentifier(raw.lstrip())
        if not rid0:
            out.append(lines[i])
            i += 1
            continue

        system_lines: list[tuple[str, str | None, str, str, str]] = []
        j = i
        while j < len(lines):
            r = lines[j].rstrip("\n\r")
            rid = parse_regelidentifier(r.lstrip())
            if not rid:
                break
            stripped = r.lstrip()
            lead = r[: len(r) - len(stripped)]
            content = stripped[rid.match_end :].lstrip()
            eol = lines[j][len(r) :] or "\n"
            system_lines.append((rid.stem_id, rid.ehm, content, eol, lead))
            j += 1

        order = [mk for mk, *_ in system_lines]
        contents = {mk: c for mk, _, c, _, _ in system_lines}
        if any(is_lyrics_stem(m) for m in order):
            new_contents = _resync_system_voices(contents, order)
            if new_contents != contents:
                changed = True
                contents = new_contents

        for mk, ehm, _, eol, lead in system_lines:
            label = f"{mk}{ehm}" if ehm else mk
            out.append(f"{lead}{label}: {contents[mk]}{eol}")
        i = j

    return "".join(out) if changed else text


def _resync_system_voices(
    contents: dict[str, str], order: list[str]
) -> dict[str, str]:
    l_markers = [m for m in order if is_lyrics_stem(m)]
    if len(l_markers) != 1:
        return contents
    l_marker = l_markers[0]
    splits = {m: _split_bars(contents[m]) for m in order}
    n_seg = len(splits[l_marker].segments)
    for m in order:
        if len(splits[m].segments) != n_seg:
            return contents

    out_segs: dict[str, list[str]] = {m: [] for m in order}
    any_change = False
    for si in range(n_seg):
        l_seg = splits[l_marker].segments[si]
        positions = parse_l_positions(l_seg)
        target = len(positions)
        out_segs[l_marker].append(splits[l_marker].segments[si].rstrip())
        for m in order:
            if m == l_marker:
                continue
            v_toks = _voice_tokens(splits[m].segments[si])
            if len(v_toks) == target:
                out_segs[m].append(splits[m].segments[si].rstrip())
                continue
            padded = resync_voice_tokens_to_l_count(v_toks, target)
            if padded != v_toks:
                any_change = True
            out_segs[m].append(" ".join(padded))

    if not any_change:
        return contents

    result: dict[str, str] = {l_marker: contents[l_marker]}
    ref_bars = splits[l_marker].bar_tokens
    ref_leading = splits[l_marker].leading_bar
    for m in order:
        if m == l_marker:
            continue
        result[m] = _join_bar_segments(
            out_segs[m],
            ref_bars,
            list(splits[m].bar_anchors),
            ref_leading,
        )
    return result


_MVSA_SUFFIX = ".mvsa"


def iter_mvsa_files(path: Path | str) -> list[Path]:
    """Geef ``.mvsa``-bestanden: één bestand, map, of catalogus-id."""
    from .input_paths import InputPathError, collect_input_files, looks_like_catalogus_id

    raw = path
    path = Path(path)
    try:
        return collect_input_files(raw, suffixes=(_MVSA_SUFFIX,))
    except InputPathError as exc:
        if looks_like_catalogus_id(raw) and not path.exists():
            raise ValueError(str(exc)) from exc
        if not path.exists():
            raise FileNotFoundError(str(path)) from exc
        if path.is_file():
            raise ValueError(f"verwacht een .mvsa-bestand, kreeg: {path}") from exc
        raise ValueError(str(exc)) from exc


def normalize_mvsa_output_extension(extension: str) -> str:
    """Normaliseer ``syl.mvsa`` / ``.syl.mvsa`` naar ``.syl.mvsa``."""
    raw = extension.strip()
    if not raw:
        raise ValueError("extensie mag niet leeg zijn")
    if not raw.startswith("."):
        raw = "." + raw
    if not raw.lower().endswith(_MVSA_SUFFIX):
        raise ValueError(
            f"extensie moet eindigen op {_MVSA_SUFFIX}, kreeg: {extension!r}"
        )
    return raw


def mvsa_output_path_for(source: Path, extension: str | None) -> Path:
    """Doelpad: zelfde bestand, of ``xyz.mvsa`` → ``xyz`` + genormaliseerde extensie."""
    if extension is None:
        return source
    ext = normalize_mvsa_output_extension(extension)
    name = source.name
    if not name.lower().endswith(_MVSA_SUFFIX):
        raise ValueError(f"bronbestand moet op {_MVSA_SUFFIX} eindigen: {source}")
    stem = name[: -len(_MVSA_SUFFIX)]
    return source.with_name(stem + ext)


def _join_bar_segments(
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
