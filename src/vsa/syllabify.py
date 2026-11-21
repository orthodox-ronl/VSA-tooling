"""Lettergreepstreepjes in VSA-brontekst (TextNode + grenzen met scopes)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .ast import ScopeNode, TextNode
from .parser import Parser
from .vsa_comments import is_vsa_comment_only_line
from .yaml_frontmatter import parse_vsa_frontmatter_with_body_offset

_BARLINE_TOKENS = frozenset({"/", "//", "*"})
_TOKEN_RE = re.compile(r"\S+|\s+", re.UNICODE)
_WORD_CORE_RE = re.compile(r"^(\W*)(.*?)(\W*)$", re.UNICODE)
_VSA_SUFFIX = ".vsa"


@dataclass(frozen=True)
class SyllabifyResult:
    """Resultaat van ``syllabify_vsa_source`` / ``unsyllabify_vsa_source``."""

    text: str
    changed: bool
    replacements: int


@dataclass(frozen=True)
class _Atom:
    """Bronfragment: platte tekst, scope, of scheiding (spatie/barline/marker)."""

    kind: str  # 'text' | 'scope' | 'sep'
    source: str
    plain: str = ""


@dataclass(frozen=True)
class _ContentPart:
    """Bijdrage aan één woord (scope of tekstkern, zonder brugstreepjes)."""

    kind: str  # 'text' | 'scope'
    source: str
    plain: str
    prefix: str = ""
    core: str = ""
    suffix: str = ""


@lru_cache(maxsize=1)
def _dutch_dic():
    import pyphen

    return pyphen.Pyphen(lang="nl_NL")


# Hard orthografisch streepje in bronnotatie (``mede=eeuwige`` → lezersvorm ``mede-eeuwige``).
HARD_HYPHEN = "="


def hyphenate_dutch_word(word: str, *, allow_pyphen: bool | None = None) -> str:
    """Voeg lettergreepstreepjes toe (canonieke lijst, anders Pyphen ``nl_NL``).

    Bestaande zachte ``-`` blijven leidend (geen her-hyphenatie), behalve als
    de canonieke dictionary een andere vorm voor het lemma heeft — dan wint
    de dictionary. Hard ``=`` splitst het woord in delen die elk apart
    gehypheneerd worden.

    Leidende/sluitende leestekens (``,`` ``.`` enz.) horen niet in de
    Pyphen-kern: anders wordt ``Geest,`` ten onrechte ``Gees-t,``.

    Bij ``--lyrics-lang auto``: dictionary wisselt per woord (Latijn→nl,
    Cyrillisch→ksl). Bij force ``nl``/``ksl``: andere schrift ongemoeid.
    Cyrillisch zonder dictionary-treffer: geen NL-Pyphen.
    """
    if not word:
        return word
    if not any(ch.isalpha() for ch in word):
        return word
    m = _WORD_CORE_RE.match(word)
    prefix, core, suffix = (m.group(1), m.group(2), m.group(3)) if m else ("", word, "")
    if not core or not any(ch.isalpha() for ch in core):
        return word
    from .syllable_dictionary import (
        activate_concrete_lyrics_lang,
        allowed_syllable_forms,
        canonical_syllable_form,
        core_matches_lyrics_lang,
        get_lyrics_lang_mode,
        lyrics_lang_for_core,
    )

    mode = get_lyrics_lang_mode()
    word_lang = lyrics_lang_for_core(core)
    if mode in ("nl", "ksl") and not core_matches_lyrics_lang(core, mode):
        return word
    activate_concrete_lyrics_lang(word_lang)

    surface = core.casefold()
    forms = allowed_syllable_forms(core)
    if forms is not None and surface in forms:
        # Al een toegestane vorm (primair of ``+``-alternatief): behouden.
        return word
    canonical = canonical_syllable_form(core)
    if canonical is not None:
        if canonical.casefold() != surface:
            return f"{prefix}{_transfer_letter_case(core, canonical)}{suffix}"
        return word
    if HARD_HYPHEN in core:
        return f"{prefix}{HARD_HYPHEN.join(hyphenate_dutch_word(part) if part else part for part in core.split(HARD_HYPHEN))}{suffix}"
    if "-" in core:
        return word
    if word_lang == "ksl":
        # Geen Nederlandse Pyphen op Cyrillisch.
        return word
    from .syllable_dict_check import is_interactive_stdin

    if allow_pyphen is None:
        allow_pyphen = is_interactive_stdin()
    if not allow_pyphen:
        return word
    return f"{prefix}{pyphen_hyphenate_core(core)}{suffix}"


def pyphen_hyphenate_core(core: str) -> str:
    """Pyphen ``nl_NL`` op de woordkern (voor TTY-syllabify en UNKNOWN-voorstellen)."""
    if not core or not any(ch.isalpha() for ch in core):
        return core
    if "-" in core or HARD_HYPHEN in core:
        return core
    return _dutch_dic().inserted(core)


def _transfer_letter_case(source: str, hyphenated: str) -> str:
    """Kopieer lettercase van *source* naar de hyphenvorm (streepjes negeren)."""
    letters = [ch for ch in source if ch.isalpha()]
    out: list[str] = []
    index = 0
    for ch in hyphenated:
        if ch.isalpha() and index < len(letters):
            src = letters[index]
            index += 1
            out.append(ch.upper() if src.isupper() else ch.lower())
        else:
            out.append(ch)
    return "".join(out)


def dutch_hyphen_positions(word: str) -> list[int]:
    """Pyphen-breekposities (index vóór het teken waar ``-`` komt)."""
    if not word or "-" in word or HARD_HYPHEN in word:
        return []
    if not any(ch.isalpha() for ch in word):
        return []
    return list(_dutch_dic().positions(word))


def strip_soft_hyphens(word: str) -> str:
    """Verwijder alleen zachte lettergreepstreepjes; hard ``=`` blijft staan."""
    if not word or "-" not in word:
        return word
    return word.replace("-", "")


def dehyphenate_dutch_word(word: str) -> str:
    """Lezers-/zoekvorm: zachte ``-`` weg, hard ``=`` wordt ``-``."""
    if not word:
        return word
    return strip_soft_hyphens(word).replace(HARD_HYPHEN, "-")


def display_lyric_text(text: str, *, strip_soft: bool = False) -> str:
    """Bronlyric → weergave.

    Hard ``=`` wordt altijd een zichtbaar streepje. Soft ``-`` (zing-deling)
    blijft staan tenzij ``strip_soft=True`` — dan zelfde lezersvorm als
    :func:`dehyphenate_dutch_word` (o.a. standaard ``.vsa.svg`` / lyrics).
    """
    if not text:
        return text
    if strip_soft:
        return dehyphenate_dutch_word(text)
    if HARD_HYPHEN not in text:
        return text
    return text.replace(HARD_HYPHEN, "-")


def syllabify_plain_text(text: str) -> str:
    """Hypheneer woorden in platte tekst; whitespace en barlines blijven staan."""
    return _map_plain_tokens(text, hyphenate_dutch_word)


def unsyllabify_plain_text(text: str) -> str:
    """Verwijder lettergreepstreepjes in platte tekst; barlines en hard ``=`` blijven."""
    return _map_plain_tokens(text, strip_soft_hyphens)


def syllabify_vsa_body(body: str) -> SyllabifyResult:
    """Hypheneer woorden in een VSA-body, inclusief streepjes op scope-grenzen."""
    return _transform_vsa_body(body, unsyllabify=False)


def unsyllabify_vsa_body(body: str) -> SyllabifyResult:
    """Verwijder lettergreepstreepjes, inclusief brugstreepjes rond scopes."""
    return _transform_vsa_body(body, unsyllabify=True)


def syllabify_vsa_source(text: str) -> SyllabifyResult:
    """Hypheneer VSA-brontekst; YAML-frontmatter blijft onaangeroerd."""
    from .syllable_dictionary import prepare_lyrics_lang_for_source

    prepare_lyrics_lang_for_source(text)
    return _transform_vsa_source(text, syllabify_vsa_body)


def unsyllabify_vsa_source(text: str) -> SyllabifyResult:
    """Verwijder lettergreepstreepjes uit VSA-brontekst; scope-inhoud blijft intact."""
    return _transform_vsa_source(text, unsyllabify_vsa_body)


def transform_vsa_source(text: str, *, unsyllabify: bool = False) -> SyllabifyResult:
    """Syllabify of unsyllabify afhankelijk van ``unsyllabify``."""
    if unsyllabify:
        return unsyllabify_vsa_source(text)
    return syllabify_vsa_source(text)


def iter_vsa_files(path: Path | str) -> list[Path]:
    """Geef `.vsa`-bestanden: één bestand, map, of catalogus-id."""
    from .input_paths import InputPathError, collect_input_files, looks_like_catalogus_id

    raw = path
    path = Path(path)
    try:
        return collect_input_files(raw, suffixes=(_VSA_SUFFIX,))
    except InputPathError as exc:
        if looks_like_catalogus_id(raw) and not path.exists():
            raise ValueError(str(exc)) from exc
        if not path.exists():
            raise FileNotFoundError(str(path)) from exc
        if path.is_file():
            raise ValueError(f"verwacht een .vsa-bestand, kreeg: {path}") from exc
        raise ValueError(str(exc)) from exc


def normalize_output_extension(extension: str) -> str:
    """Normaliseer ``syl.vsa`` / ``.syl.vsa`` naar ``.syl.vsa``."""
    raw = extension.strip()
    if not raw:
        raise ValueError("extensie mag niet leeg zijn")
    if not raw.startswith("."):
        raw = "." + raw
    if not raw.lower().endswith(_VSA_SUFFIX):
        raise ValueError(
            f"extensie moet eindigen op {_VSA_SUFFIX}, kreeg: {extension!r}"
        )
    return raw


def output_path_for(source: Path, extension: str | None) -> Path:
    """Doelpad: zelfde bestand, of ``xyz.vsa`` → ``xyz`` + genormaliseerde extensie."""
    if extension is None:
        return source
    ext = normalize_output_extension(extension)
    name = source.name
    if not name.lower().endswith(_VSA_SUFFIX):
        raise ValueError(f"bronbestand moet op {_VSA_SUFFIX} eindigen: {source}")
    stem = name[: -len(_VSA_SUFFIX)]
    return source.with_name(stem + ext)


def _map_plain_tokens(text: str, word_fn) -> str:
    if not text:
        return text
    parts: list[str] = []
    for match in _TOKEN_RE.finditer(text):
        token = match.group(0)
        if token.isspace() or token in _BARLINE_TOKENS:
            parts.append(token)
            continue
        parts.append(_map_token_core(token, word_fn))
    return "".join(parts)


def _map_token_core(token: str, word_fn) -> str:
    match = _WORD_CORE_RE.match(token)
    if not match:
        return token
    prefix, core, suffix = match.group(1), match.group(2), match.group(3)
    if not core:
        return token
    return f"{prefix}{word_fn(core)}{suffix}"


def _transform_vsa_source(text: str, body_fn) -> SyllabifyResult:
    _meta, body, body_offset = parse_vsa_frontmatter_with_body_offset(text)
    result = body_fn(body)
    if not result.changed:
        return SyllabifyResult(text=text, changed=False, replacements=0)
    return SyllabifyResult(
        text=text[:body_offset] + result.text,
        changed=True,
        replacements=result.replacements,
    )


def _transform_vsa_body(body: str, *, unsyllabify: bool) -> SyllabifyResult:
    document = Parser(body).parse()
    atoms = _atoms_from_document(body, document)
    pieces: list[str] = []
    replacements = 0

    for kind, group in _group_runs(atoms):
        if kind == "sep":
            pieces.append("".join(atom.source for atom in group))
            continue
        new_run, n = _transform_word_run(group, unsyllabify=unsyllabify)
        replacements += n
        pieces.append(new_run)

    new_body = "".join(pieces)
    return SyllabifyResult(
        text=new_body,
        changed=new_body != body,
        replacements=replacements,
    )


def _atoms_from_document(body: str, document) -> list[_Atom]:
    atoms: list[_Atom] = []
    cursor = 0

    for node in document.nodes:
        if node.start is None or node.end is None:
            continue
        if node.start < cursor:
            raise ValueError(
                f"Overlappende AST-offsets bij {node.start} (cursor={cursor})"
            )
        if node.start > cursor:
            atoms.extend(_atoms_from_text_segment(body[cursor : node.start]))

        if isinstance(node, ScopeNode):
            atoms.append(
                _Atom("scope", body[node.start : node.end], plain=node.text)
            )
        elif isinstance(node, TextNode):
            atoms.extend(_atoms_from_text_segment(body[node.start : node.end]))
        else:
            atoms.append(_Atom("sep", body[node.start : node.end]))
        cursor = node.end

    if cursor < len(body):
        atoms.extend(_atoms_from_text_segment(body[cursor:]))
    return atoms


def _atoms_from_text_segment(segment: str) -> list[_Atom]:
    if not segment:
        return []
    if "<!--" in segment:
        return _atoms_from_text_with_comments(segment)
    return _atoms_from_plain_text(segment)


def _atoms_from_plain_text(segment: str) -> list[_Atom]:
    atoms: list[_Atom] = []
    for match in _TOKEN_RE.finditer(segment):
        token = match.group(0)
        if token.isspace() or token in _BARLINE_TOKENS:
            atoms.append(_Atom("sep", token))
        else:
            atoms.append(_Atom("text", token))
    return atoms


def _atoms_from_text_with_comments(segment: str) -> list[_Atom]:
    atoms: list[_Atom] = []
    index = 0
    length = len(segment)
    plain_parts: list[str] = []

    def flush_plain() -> None:
        if not plain_parts:
            return
        atoms.extend(_atoms_from_plain_text("".join(plain_parts)))
        plain_parts.clear()

    while index < length:
        line_start = index
        line_end = index
        while line_end < length and segment[line_end] not in "\r\n":
            line_end += 1

        if line_end < length:
            if segment[line_end : line_end + 2] == "\r\n":
                line_ending = "\r\n"
                next_index = line_end + 2
            else:
                line_ending = segment[line_end]
                next_index = line_end + 1
        else:
            line_ending = ""
            next_index = line_end

        line_content = segment[line_start:line_end]
        if is_vsa_comment_only_line(line_content, line_ending):
            flush_plain()
            atoms.append(_Atom("sep", line_content + line_ending))
            index = next_index
            continue

        from .syllable_dict_check import _is_non_lyric_report_line

        if _is_non_lyric_report_line(line_content.lstrip()):
            flush_plain()
            atoms.append(_Atom("sep", line_content + line_ending))
            index = next_index
            continue

        content_index = 0
        while content_index < len(line_content):
            if line_content[content_index : content_index + 4] == "<!--":
                comment_end = line_content.find("-->", content_index)
                if comment_end >= 0:
                    flush_plain()
                    atoms.append(
                        _Atom("sep", line_content[content_index : comment_end + 3])
                    )
                    content_index = comment_end + 3
                    continue
            plain_parts.append(line_content[content_index])
            content_index += 1

        flush_plain()
        if line_ending:
            atoms.append(_Atom("sep", line_ending))
        index = next_index

    return atoms


def _group_runs(atoms: list[_Atom]):
    current: list[_Atom] = []
    for atom in atoms:
        if atom.kind == "sep":
            if current:
                yield "word", current
                current = []
            yield "sep", [atom]
        else:
            current.append(atom)
    if current:
        yield "word", current


def _transform_word_run(
    atoms: list[_Atom], *, unsyllabify: bool
) -> tuple[str, int]:
    original = "".join(atom.source for atom in atoms)
    if unsyllabify:
        new = _unsyllabify_word_run(atoms)
    else:
        new = _syllabify_word_run(atoms)
    return new, _count_hyphen_delta(original, new)


def _content_parts(atoms: list[_Atom]) -> list[_ContentPart]:
    parts: list[_ContentPart] = []
    for atom in atoms:
        if atom.kind == "scope":
            parts.append(_ContentPart("scope", atom.source, atom.plain))
            continue
        parsed = _parse_text_part(atom.source)
        if parsed is not None:
            parts.append(parsed)
    return parts


def _parse_text_part(source: str) -> _ContentPart | None:
    """Tekstatom zonder brugstreepjes; ``None`` als het atom alleen ``-`` is.

    Leidende/sluitende soft ``-`` (brug naar een scope) horen niet in de kern:
    een scope-accolade is zelf al lettergreep-/woordgrens.
    """
    if source == "-":
        return None

    match = _WORD_CORE_RE.match(source)
    if not match:
        return _ContentPart("text", source, source.replace("-", ""), core=source)

    prefix, core, suffix = match.group(1), match.group(2), match.group(3)

    while prefix.startswith("-"):
        prefix = prefix[1:]
    if suffix and set(suffix) == {"-"}:
        suffix = ""
    # Brugstreepjes vastgeplakt aan platte tekst (``ver-`` vóór ``{…}``).
    while core.startswith("-"):
        core = core[1:]
    while core.endswith("-"):
        core = core[:-1]

    if not core and not prefix and not suffix:
        return None

    plain = core.replace("-", "")
    return _ContentPart("text", source, plain, prefix=prefix, core=core, suffix=suffix)


def _syllabify_word_run(atoms: list[_Atom]) -> str:
    parts = _content_parts(atoms)
    if not parts:
        return "".join(atom.source for atom in atoms)

    if len(parts) == 1 and parts[0].kind == "text":
        part = parts[0]
        return f"{part.prefix}{hyphenate_dutch_word(part.core)}{part.suffix}"

    plain = "".join(part.plain for part in parts)
    if not plain or not any(ch.isalpha() for ch in plain):
        return "".join(atom.source for atom in atoms)

    # Canonieke deling; herverdeel letters zodat elke scope precies één
    # lettergreep heeft. Geen soft ``-`` naast ``{``/``}``.
    form = hyphenate_dutch_word(plain)
    cased = _transfer_letter_case(plain, form)
    syllables = [s for s in re.split(r"[-|=]+", cased) if s]
    if not syllables:
        return "".join(atom.source for atom in atoms)
    if sum(len(s) for s in syllables) != len(plain.replace("=", "")):
        # Onverwachte hard-``=``/telling: val terug op oude tekst-only hyphenatie.
        positions = _break_positions_in_plain(plain, form)
        if not positions:
            positions = set(dutch_hyphen_positions(plain))
        return _render_syllabified_parts_text_only(parts, positions)
    return _render_scope_aware_syllables(parts, syllables)


def _break_positions_in_plain(plain: str, hyphenated: str) -> set[int]:
    """Breekpunten in *plain* (zonder ``-``/``=``) afgeleid van een hyphenvorm."""
    positions: set[int] = set()
    plain_i = 0
    for ch in hyphenated:
        if ch in "-=":
            if 0 < plain_i < len(plain):
                positions.add(plain_i)
            continue
        if plain_i < len(plain):
            plain_i += 1
    return positions


def _render_scope_aware_syllables(
    parts: list[_ContentPart], syllables: list[str]
) -> str:
    """Herverdeel lettergrepen: elke scope = één lettergreep; rest in platte tekst.

    Geen soft ``-`` naast scope-accolades. Voorbeeld:
    ``{/sche_}pping`` → ``{/schep_}ping``; ``{/Adam}`` → ``{/A}dam``.
    """
    n = len(syllables)
    # Karakter-ranges per part in de aaneengesloten plain (zonder soft ``-``/``=``).
    part_ranges: list[tuple[int, int]] = []
    offset = 0
    for part in parts:
        plen = len(part.plain.replace("=", ""))
        part_ranges.append((offset, offset + plen))
        offset += plen

    syl_starts: list[int] = []
    offset = 0
    for syl in syllables:
        syl_starts.append(offset)
        offset += len(syl)

    def _syl_at(char_index: int) -> int:
        for i in range(n - 1, -1, -1):
            if char_index >= syl_starts[i]:
                return i
        return 0

    # Elke scope claimt precies één lettergreep (op volgorde, uniek).
    scope_owner: dict[int, int] = {}  # syllable index → part index
    used: set[int] = set()
    for part_index, part in enumerate(parts):
        if part.kind != "scope" or not part.plain.replace("=", ""):
            continue
        start, _end = part_ranges[part_index]
        preferred = _syl_at(start)
        while preferred < n and preferred in used:
            preferred += 1
        if preferred >= n or preferred in used:
            # Kan niet veilig herverdelen → tekst-only fallback.
            positions = set()
            off = 0
            for syl in syllables[:-1]:
                off += len(syl)
                positions.add(off)
            return _render_syllabified_parts_text_only(parts, positions)
        used.add(preferred)
        scope_owner[preferred] = part_index

    # Leestekens op vaste offsets in de letterstroom (die niet verschuift),
    # zodat ``{/Adam},`` → ``{/A}dam,`` en ``zie,{/daar}`` de komma houdt.
    inserts_before: dict[int, str] = {}
    inserts_after: dict[int, str] = {}

    def _add_insert(bucket: dict[int, str], at: int, frag: str) -> None:
        if frag:
            bucket[at] = bucket.get(at, "") + frag

    for part, (start, end) in zip(parts, part_ranges):
        if part.kind != "text":
            continue
        letter = bool(part.plain.replace("=", "")) and any(
            ch.isalpha() for ch in part.plain
        )
        if letter:
            _add_insert(inserts_before, start, part.prefix)
            _add_insert(inserts_after, end, part.suffix)
        else:
            _add_insert(
                inserts_before, start, f"{part.prefix}{part.core}{part.suffix}"
            )

    out: list[str] = []
    char_i = 0

    def _flush_through(new_i: int) -> None:
        """Schrijf inserts op offsets (char_i, new_i]; daarna after/before op new_i."""
        nonlocal char_i
        if new_i < char_i:
            return
        for at in range(char_i + 1, new_i + 1):
            if at in inserts_after:
                out.append(inserts_after.pop(at))
            if at in inserts_before:
                out.append(inserts_before.pop(at))
        char_i = new_i

    if 0 in inserts_before:
        out.append(inserts_before.pop(0))
    if 0 in inserts_after:
        out.append(inserts_after.pop(0))

    index = 0
    while index < n:
        if index in scope_owner:
            part = parts[scope_owner[index]]
            out.append(
                _rebuild_scope_source(
                    part.source, part.plain.replace("=", ""), syllables[index]
                )
            )
            _flush_through(char_i + len(syllables[index]))
            index += 1
            continue
        run: list[str] = []
        advance = 0
        while index < n and index not in scope_owner:
            run.append(syllables[index])
            advance += len(syllables[index])
            index += 1
        out.append("-".join(run))
        _flush_through(char_i + advance)

    for at in sorted(set(inserts_before) | set(inserts_after)):
        if at in inserts_after:
            out.append(inserts_after.pop(at))
        if at in inserts_before:
            out.append(inserts_before.pop(at))
    return "".join(out)


def _rebuild_scope_source(source: str, old_plain: str, new_plain: str) -> str:
    """Vervang zangelement in ``{…}``; behoud EHM/ELM."""
    if not source.startswith("{") or not source.endswith("}"):
        return source
    inner = source[1:-1]
    idx = inner.find(old_plain)
    if idx < 0:
        low = inner.casefold()
        key = old_plain.casefold()
        idx = low.find(key)
        if idx < 0:
            return source
        return "{" + inner[:idx] + new_plain + inner[idx + len(key) :] + "}"
    return "{" + inner[:idx] + new_plain + inner[idx + len(old_plain) :] + "}"


def _render_syllabified_parts_text_only(
    parts: list[_ContentPart], positions: set[int]
) -> str:
    """Fallback: streepjes alleen in platte tekst; scopes ongewijzigd."""
    out: list[str] = []
    offset = 0
    last_index = len(parts) - 1

    for index, part in enumerate(parts):
        start = offset
        end = offset + len(part.plain)

        if part.kind == "scope":
            out.append(part.source)
        else:
            internal = sorted(p - start for p in positions if start < p < end)
            chunk = _insert_hyphens(part.plain, internal)
            out.append(f"{part.prefix}{chunk}{part.suffix}")

        if index < last_index and end in positions:
            nxt = parts[index + 1]
            if part.kind == "scope" or nxt.kind == "scope":
                pass
            else:
                out.append("-")

        offset = end

    return "".join(out)


def _insert_hyphens(text: str, positions: list[int]) -> str:
    if not positions:
        return text
    pieces: list[str] = []
    prev = 0
    for pos in positions:
        pieces.append(text[prev:pos])
        prev = pos
    pieces.append(text[prev:])
    return "-".join(pieces)


def _unsyllabify_word_run(atoms: list[_Atom]) -> str:
    parts = _content_parts(atoms)
    if not parts:
        return "".join(atom.source for atom in atoms)

    out: list[str] = []
    for part in parts:
        if part.kind == "scope":
            out.append(part.source)
        else:
            out.append(f"{part.prefix}{strip_soft_hyphens(part.core)}{part.suffix}")
    return "".join(out)


def _count_hyphen_delta(before: str, after: str) -> int:
    if before == after:
        return 0
    return abs(after.count("-") - before.count("-"))
