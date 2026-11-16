"""Controleer gezongen VSA-body tegen de canonieke syllable-dictionary."""

from __future__ import annotations

import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .ast import ControlTokenNode, Document, ScopeNode, TextNode
from .monosyllable_exceptions import is_monosyllable_exception
from .syllabify import (
    HARD_HYPHEN,
    dutch_hyphen_positions,
    hyphenate_dutch_word,
)
from .syllable_dictionary import (
    SyllableEntry,
    activate_concrete_lyrics_lang,
    allowed_syllable_forms,
    canonical_syllable_form,
    clear_syllable_dictionary_cache,
    core_matches_lyrics_lang,
    dictionary_file_path,
    dictionary_path_label,
    ensure_lyrics_lang_for_cores,
    normalize_lyrics_lang_mode,
    parse_syllable_dictionary_text,
    syllable_lemma,
)

CODE_MISMATCH = "VSA-SYLLABLE-DICT-MISMATCH"
CODE_UNKNOWN = "VSA-SYLLABLE-DICT-UNKNOWN"
DOC_URL = "docs/formats/syllabificatie.md"

_TOKEN_RE = re.compile(r"\S+", re.UNICODE)
_EDGE_PUNCT = re.compile(r"^([^\w=]*)(.*?)([^\w=]*)$", re.UNICODE)

_HINT_TTY = (
    "Op een TTY: Enter/Spatie = voorstel; `+`/`=` = huidige vorm in lijst; "
    "Tab = overslaan; Esc = stop; of typ een andere hyphenvorm."
)

# Exitcode voor CLI-gates bij interactieve afbreking (Esc).
DICT_PROMPT_ABORT_RC = 2

# Interne actiecodes van de TTY-lezer (niet als hyphenvorm typen).
_ACTION_SKIP = "__skip__"
_ACTION_ABORT = "__abort__"
_ACTION_ACCEPT_CURRENT = "__accept_current__"


@dataclass(frozen=True)
class DictSyllableFinding:
    """Afwijking t.o.v. de canonieke woordenlijst."""

    code: str
    surface: str
    expected: str | None
    line: int
    column: int
    message_nl: str
    hint_nl: str


@dataclass
class DictionaryPromptResult:
    """Uitkomst van interactieve dictionary-correctie."""

    added_or_updated: list[str] = field(default_factory=list)
    # (surface_zoals_in_bron, canonieke_vorm_zonder_case)
    replacements: list[tuple[str, str]] = field(default_factory=list)
    aborted: bool = False


def format_clickable_location(
    path: Path | str | None,
    line: int,
    column: int,
    *,
    cwd: Path | str | None = None,
) -> str:
    """``pad:regel:kolom:`` — klikbaar in de VS Code / Cursor-terminal.

    Pad relatief t.o.v. ``cwd`` (default: werkmap) als het bestand daaronder
    valt — korter, en VS Code opent het vanuit de repo-root.
    """
    loc_line = line if line and line > 0 else 1
    loc_col = column if column and column > 0 else 1
    if path is None or str(path).strip() == "":
        return f":{loc_line}:{loc_col}:"
    resolved = Path(path).expanduser()
    try:
        resolved = resolved.resolve()
    except OSError:
        pass
    base = Path(cwd).resolve() if cwd is not None else Path.cwd()
    try:
        display = str(resolved.relative_to(base))
    except ValueError:
        display = str(resolved)
    return f"{display}:{loc_line}:{loc_col}:"


def bare_sung_text(document: Document) -> str:
    """Alleen gezongen lyrics uit de VSA-AST (geen directives/metadata).

    Neemt ``TextNode``- en ``ScopeNode``-tekst; maatstrepen/control tokens
    worden spaties. Soft ``-`` / hard ``=`` blijven staan.

    Een grens tussen opeenvolgende lyric-stukken (tekst↔scope of scope↔scope)
    zonder spatie telt als zing-deling: er komt een virtueel soft ``-`` tussen
    (zelfde betekenis als in de bron géén streepje naast ``{``/``}`` zetten).
    Zo matcht ``ver{/heer}{\\lijkt}`` de canonieke vorm ``ver-heer-lijkt``.
    """
    chunks: list[str] = []
    prev_lyric: str | None = None

    def _emit_lyric(piece: str) -> None:
        nonlocal prev_lyric
        if not piece:
            return
        if prev_lyric is not None:
            left = prev_lyric[-1]
            right = piece[0]
            if (
                not left.isspace()
                and not right.isspace()
                and left not in "-="
                and right not in "-="
            ):
                chunks.append("-")
        chunks.append(piece)
        prev_lyric = piece

    for node in getattr(document, "nodes", []):
        if isinstance(node, TextNode):
            _emit_lyric(node.text or "")
        elif isinstance(node, ScopeNode):
            _emit_lyric(node.text or "")
        elif isinstance(node, ControlTokenNode):
            chunks.append(" ")
            prev_lyric = None
    return "".join(chunks)


def iter_body_word_cores(bare: str) -> list[str]:
    """Woordkernen uit kale lyrics (leestekenrand weg; geen kale maatstrepen).

    Recite-haakjes ``(``/``)`` en ELMs (``_`` ``~`` ``.`` …) tellen niet mee
    voor de woordenlijst — zelfde idee als bij syllabify. ``Al-le-(lu-ja`` →
    kern ``Al-le-lu-ja``. HTML/``#``-commentaar hoort niet in ``bare``.
    """
    cores: list[str] = []
    for match in _TOKEN_RE.finditer(bare):
        m = _EDGE_PUNCT.match(match.group(0))
        if not m:
            continue
        core = _strip_lyric_markup(m.group(2))
        if not core or not any(ch.isalpha() for ch in core):
            continue
        cores.append(core)
    return cores


def _strip_recite_parens(text: str) -> str:
    """Haal recite-``(``/``)`` weg zodat soft ``-`` over de grens blijft."""
    if not text:
        return text
    return text.replace("(", "").replace(")", "")


def _strip_lyric_markup(text: str) -> str:
    """Recite-haakjes + duur-/melisma-ELMs weg; soft ``-``/``=`` blijven."""
    if not text:
        return text
    # Soft ``-``/``=`` tussen letters blijft; ELM-``-`` alleen als hele suffix
    # zonder letter erbóór (zeldzaam buiten scopes).
    from .parser import ELM_VALUES

    s = _strip_recite_parens(text).replace("&", "")
    edge_elms = tuple(e for e in ELM_VALUES if e != "-")
    changed = True
    while changed and s:
        changed = False
        for elm in edge_elms:
            if s.endswith(elm):
                s = s[: -len(elm)]
                changed = True
                break
    return s


def _bare_dash_elm(elms: list[str] | None) -> bool:
    """True als de positie een kale ELM-``-`` heeft (vaak ``-(`` vóór recite)."""
    return bool(elms) and "-" in elms


def iter_vsa_lyric_word_cores(document: Document) -> list[str]:
    """Canonieke lyrics-woorden uit een geparste VSA-body (geen frontmatter)."""
    return iter_body_word_cores(bare_sung_text(document))


def iter_mvsa_lyric_word_cores(source: str) -> list[str]:
    """Canonieke lyrics-woorden uit .mvsa: alleen L-regels, met soft ``-``/``=``.

    Geen ``@title`` / ``@do`` / zoektekst / commentaar / S/A/T/B-regels.

    Recite-haakjes splitsen het woord niet voor de woordenlijst: ``Al-le-(lu-ja``
    hoort bij lemma ``alleluja`` (kern ``Al-le-lu-ja``), net zoals ELMs geen
    lettergreepgrenzen zijn. Parser leest ``-`` vóór ``(`` als ELM-duur; voor
    de dictionary telt dat als soft ``-`` het woord in de recite in.
    """
    from .mvsa_parse import LPosition, parse_mvsa
    from .mvsa_validate import is_lyrics_stem
    from .text_export import _first_lyrics_lpos, join_lyric_syllables

    doc = parse_mvsa(source)
    parts: list[str] = []
    open_word = False
    word_chunks: list[str] = []
    prev_lpos: LPosition | None = None

    def flush() -> None:
        nonlocal parts, open_word, prev_lpos
        word_chunks.extend(parts)
        parts = []
        open_word = False
        prev_lpos = None

    for section in doc.sections:
        first = _first_lyrics_lpos(section)
        if parts and not (first is not None and first.continues_word):
            flush()
        for system in section.systems:
            for measure in system.measures:
                for marker in system.markers:
                    if not is_lyrics_stem(marker):
                        continue
                    for lpos in measure.lyrics.get(marker) or []:
                        joined = join_lyric_syllables(
                            lpos.syllables, lpos.links, lpos.hard_links
                        )
                        if not joined:
                            prev_lpos = lpos
                            continue
                        # ``le-(lu…``: parser zet ELM ``-`` op ``le`` en
                        # ``continues_word=False`` op de recite. Voor de
                        # woordenlijst is dat soft ``-`` + haakje weg.
                        dash_into_recite = (
                            bool(parts)
                            and lpos.recite
                            and not lpos.continues_word
                            and not open_word
                            and prev_lpos is not None
                            and not prev_lpos.recite
                            and _bare_dash_elm(prev_lpos.elms)
                        )
                        if open_word or lpos.continues_word or dash_into_recite:
                            glue = (
                                HARD_HYPHEN
                                if lpos.continues_word_hard
                                else "-"
                            )
                            if parts:
                                parts[-1] = parts[-1] + glue + joined
                            else:
                                parts.append(joined)
                        else:
                            parts.append(joined)
                        open_word = False
                        prev_lpos = lpos
    flush()
    cores: list[str] = []
    for chunk in word_chunks:
        cores.extend(iter_body_word_cores(chunk))
    return cores


def find_dictionary_syllable_issues(
    document: Document,
    *,
    source_text: str = "",
    lyrics_lang: str | None = None,
) -> list[DictSyllableFinding]:
    """Vergelijk VSA-lyrics (AST) met de canonieke lijst."""
    return find_dictionary_syllable_issues_from_cores(
        iter_vsa_lyric_word_cores(document),
        source_text=source_text,
        lyrics_lang=lyrics_lang,
    )


def find_dictionary_syllable_issues_from_cores(
    cores: list[str],
    *,
    source_text: str = "",
    lyrics_lang: str | None = None,
) -> list[DictSyllableFinding]:
    """Vergelijk gegeven lyrics-woordkernen met de canonieke lijst.

    ``lyrics_lang``: ``auto`` (schrift-detectie), ``nl`` of ``ksl``.
    Zonder argument: actieve CLI-modus (default ``auto``).
    """
    if lyrics_lang is not None:
        mode = normalize_lyrics_lang_mode(lyrics_lang)
        if mode == "auto":
            lang = ensure_lyrics_lang_for_cores(cores)
        else:
            activate_concrete_lyrics_lang(mode)
            lang = mode
    else:
        lang = ensure_lyrics_lang_for_cores(cores)
    findings: list[DictSyllableFinding] = []
    # Per genormaliseerde oppervlaktevorm (niet alleen lemma): anders mist
    # een foute variant als elders in de bron al een toegestane vorm staat.
    seen: set[str] = set()
    for core in cores:
        if not core_matches_lyrics_lang(core, lang):
            continue
        key = syllable_lemma(core)
        if not key:
            continue
        surface_norm = _normalize_form(core)
        dedupe = f"{key}\0{surface_norm}"
        if dedupe in seen:
            continue
        seen.add(dedupe)
        allowed = allowed_syllable_forms(core)
        expected = canonical_syllable_form(core)
        line, column = _locate(source_text, core)

        if allowed is not None:
            if surface_norm in allowed:
                continue
            findings.append(
                DictSyllableFinding(
                    code=CODE_MISMATCH,
                    surface=core,
                    expected=expected,
                    line=line,
                    column=column,
                    message_nl=(
                        f"Woord `{core}` hoort als `{expected}` "
                        f"(canonieke zing-deling, {lang}"
                        + (
                            f"; ook toegestaan: "
                            + ", ".join(
                                sorted(f"`{a}`" for a in allowed if a != expected)
                            )
                            if expected is not None
                            and any(a != expected for a in allowed)
                            else ""
                        )
                        + ")."
                    ),
                    hint_nl=(
                        f"Vervang in de bron door `{expected}` (lemma `{key}`), "
                        f"of accepteer bewust een andere vorm in "
                        f"`{dictionary_path_label()}` (wordt ``+``-alternatief). "
                        f"{_HINT_TTY} Norm: {DOC_URL}."
                    ),
                )
            )
            continue

        if is_monosyllable_exception(core):
            continue
        if lang == "ksl":
            # Geen NL-Pyphen-voorstel op Cyrillisch.
            suggestion = surface_norm
        elif "-" not in core and HARD_HYPHEN not in core:
            if not dutch_hyphen_positions(_alpha_core(core)):
                continue
            suggestion = hyphenate_dutch_word(_alpha_core(core))
        else:
            suggestion = surface_norm

        findings.append(
            DictSyllableFinding(
                code=CODE_UNKNOWN,
                surface=core,
                expected=None,
                line=line,
                column=column,
                message_nl=(
                    f"Woord `{core}` staat niet in de canonieke "
                    f"syllable-dictionary ({lang}; voorstel: `{suggestion}`)."
                ),
                hint_nl=(
                    f"Voeg `{suggestion}` (of de huidige vorm) toe aan "
                    f"`{dictionary_path_label()}`, of vervang de bron. "
                    f"{_HINT_TTY} Norm: {DOC_URL}."
                ),
            )
        )
    return findings


def find_mvsa_dictionary_syllable_issues(
    source: str,
    *,
    lyrics_lang: str | None = None,
) -> list[DictSyllableFinding]:
    """Dictionary-check op .mvsa: uitsluitend L-lyrics."""
    return find_dictionary_syllable_issues_from_cores(
        iter_mvsa_lyric_word_cores(source),
        source_text=source,
        lyrics_lang=lyrics_lang,
    )


def append_canonical_form(form: str) -> str:
    """Voeg een canonieke vorm toe; fout als lemma al een ándere vorm heeft."""
    return set_canonical_form(form, allow_replace=False)


def set_canonical_form(form: str, *, allow_replace: bool = True) -> str:
    """Zet primaire vorm of voeg ``+``-alternatief toe; herschrijf gesorteerd.

    Bestaat het lemma al met een ándere primaire vorm: bij ``allow_replace``
    wordt ``form`` als toegestaan alternatief (``+``) toegevoegd — de primaire
    blijft staan. Zonder ``allow_replace`` is dat een fout.
    """
    normalized = _normalize_form(form)
    if not normalized or not any(ch.isalpha() for ch in normalized):
        raise ValueError(f"ongeldige hyphenvorm: {form!r}")
    # Schrijf naar de woordenlijst die bij het schrift van de vorm hoort.
    target_lang = "ksl" if core_matches_lyrics_lang(normalized, "ksl") else "nl"
    activate_concrete_lyrics_lang(target_lang)
    key = syllable_lemma(normalized)
    path = dictionary_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        header, by_lemma = parse_syllable_dictionary_text(
            path.read_text(encoding="utf-8"), source_name=path.name
        )
    else:
        header, by_lemma = "", {}

    existing = by_lemma.get(key)
    if existing is not None:
        if normalized in existing.allowed():
            return normalized
        if not allow_replace:
            raise ValueError(
                f"lemma {key!r} staat al als {existing.primary!r}, "
                f"niet {normalized!r}"
            )
        by_lemma[key] = SyllableEntry(
            existing.primary, existing.alts | {normalized}
        )
    else:
        by_lemma[key] = SyllableEntry(normalized, frozenset())

    _write_sorted_dictionary(path, header, by_lemma)
    clear_syllable_dictionary_cache()
    return normalized


def rewrite_dictionary_sorted(path: Path | None = None) -> int:
    """Herschrijf de dictionary alfabetisch op lemma. Retourneert aantal lemma's."""
    target = path if path is not None else dictionary_file_path()
    if not target.is_file():
        return 0
    header, by_lemma = parse_syllable_dictionary_text(
        target.read_text(encoding="utf-8"), source_name=target.name
    )
    _write_sorted_dictionary(target, header, by_lemma)
    clear_syllable_dictionary_cache()
    return len(by_lemma)


def _split_dictionary_text(text: str) -> tuple[str, list[str]]:
    """Scheid kopcommentaar van entry-regels (platte lijst; legacy helpers)."""
    header, by_lemma = parse_syllable_dictionary_text(text)
    flat: list[str] = []
    for lemma in sorted(by_lemma.keys()):
        entry = by_lemma[lemma]
        flat.append(entry.primary)
        for alt in sorted(entry.alts):
            flat.append(f"+{alt}")
    return header, flat


def _write_sorted_dictionary(
    path: Path,
    header: str,
    by_lemma: dict[str, str] | dict[str, SyllableEntry],
) -> None:
    """Schrijf header + entries gesorteerd op lemma (primair, dan ``+``-alts)."""
    lines: list[str] = []
    for lemma in sorted(by_lemma.keys()):
        value = by_lemma[lemma]
        if isinstance(value, SyllableEntry):
            lines.append(value.primary)
            for alt in sorted(value.alts):
                lines.append(f"+{alt}")
        else:
            lines.append(str(value))
    body = "".join(f"{form}\n" for form in lines)
    path.write_text(f"{header}{body}", encoding="utf-8", newline="\n")


def replace_sung_token_in_text(text: str, surface: str, new_form: str) -> str:
    """Vervang woordkernen met hetzelfde lemma; behoud lettercase per treffer.

    Platte tokens (``eeuw-en``) én scope-bruggen (``{`` + EHM + ``eeuw}{en}``
    → lettergrepen ``eeu`` / ``wen`` in dezelfde scopes) worden herschreven.
    """
    from .syllabify import _transfer_letter_case

    key = syllable_lemma(surface)
    if not key:
        return text
    target = _normalize_form(new_form)

    def _repl(match: re.Match[str]) -> str:
        token = match.group(0)
        edges = _EDGE_PUNCT.match(token)
        if not edges:
            return token
        prefix, core, suffix = edges.group(1), edges.group(2), edges.group(3)
        if not core or syllable_lemma(core) != key:
            return token
        if _normalize_form(core) == target:
            return token
        return f"{prefix}{_transfer_letter_case(core, target)}{suffix}"

    new = _TOKEN_RE.sub(_repl, text)
    return _replace_lemma_in_scope_bridged_words(new, key, target)


def _replace_lemma_in_scope_bridged_words(
    text: str, lemma_key: str, target_form: str
) -> str:
    """Herschrijf woorden die over scopegrenzen lopen (geen plat ``eeuw-en``-token)."""
    if not text.strip() or "{" not in text:
        return text
    try:
        from .parser import Parser
        from .syllabify import (
            _atoms_from_document,
            _group_runs,
            _transfer_letter_case,
        )
    except Exception:
        return text

    try:
        document = Parser(text).parse()
    except Exception:
        return text

    try:
        atoms = _atoms_from_document(text, document)
    except Exception:
        return text

    target_syllables = [
        s
        for s in re.split(r"[-|=]+", target_form)
        if s and any(ch.isalpha() for ch in s)
    ]
    if not target_syllables:
        return text

    out: list[str] = []
    changed_any = False
    for kind, group in _group_runs(atoms):
        if kind == "sep":
            out.extend(atom.source for atom in group)
            continue
        # Word-run: letters per text/scope-atom (virtuele ``-`` op scopegrenzen).
        pieces: list[str] = []
        letter_atoms: list = []
        for atom in group:
            if atom.kind == "scope":
                plain = (atom.plain or "").replace("-", "").replace("=", "")
            elif atom.kind == "text":
                edges = _EDGE_PUNCT.match(atom.source)
                core = edges.group(2) if edges else atom.source
                plain = core.replace("-", "").replace("=", "")
            else:
                continue
            if not plain or not any(ch.isalpha() for ch in plain):
                continue
            letter_atoms.append(atom)
            pieces.append(plain)
        if len(letter_atoms) < 2:
            # Geen scope-brug; platte replace dekt dit al.
            out.extend(atom.source for atom in group)
            continue
        joined_plain = "".join(pieces)
        if syllable_lemma(joined_plain) != lemma_key:
            out.extend(atom.source for atom in group)
            continue
        if syllable_lemma(target_form) != lemma_key:
            out.extend(atom.source for atom in group)
            continue
        assignments = _assign_syllables_to_parts(
            len(letter_atoms), target_syllables
        )
        if assignments is None:
            out.extend(atom.source for atom in group)
            continue
        letter_i = 0
        new_group: list[str] = []
        abort_run = False
        for atom in group:
            if letter_i < len(letter_atoms) and atom is letter_atoms[letter_i]:
                syls = assignments[letter_i]
                new_core = _transfer_letter_case(
                    pieces[letter_i],
                    syls[0] if len(syls) == 1 else "-".join(syls),
                )
                if atom.kind == "scope":
                    if len(syls) != 1:
                        # Geen soft ``-`` in scope-inhoud.
                        abort_run = True
                        break
                    new_group.append(
                        _rebuild_scope_source(
                            atom.source, pieces[letter_i], new_core
                        )
                    )
                else:
                    edges = _EDGE_PUNCT.match(atom.source)
                    if edges:
                        pre, _core, suf = (
                            edges.group(1),
                            edges.group(2),
                            edges.group(3),
                        )
                        new_group.append(f"{pre}{new_core}{suf}")
                    else:
                        new_group.append(new_core)
                letter_i += 1
            else:
                new_group.append(atom.source)
        if abort_run or not new_group:
            out.extend(atom.source for atom in group)
        else:
            out.extend(new_group)
            changed_any = True

    return "".join(out) if (changed_any or out) else text


def _assign_syllables_to_parts(
    n_parts: int, syllables: list[str]
) -> list[list[str]] | None:
    """Verdeel canonieke lettergrepen over N text/scope-delen.

    - N == aantal lettergrepen → 1:1
    - N < lettergrepen → eerste N-1 delen één lettergreep; laatste de rest
      (met soft ``-``; dat deel moet text zijn — caller weigert multi-syl scope)
    - N > lettergrepen → niet veilig herverdelen
    """
    n_syl = len(syllables)
    if n_parts <= 0 or n_syl <= 0:
        return None
    if n_parts == n_syl:
        return [[s] for s in syllables]
    if n_parts < n_syl:
        out = [[syllables[i]] for i in range(n_parts - 1)]
        out.append(syllables[n_parts - 1 :])
        return out
    return None


def _rebuild_scope_source(source: str, old_plain: str, new_plain: str) -> str:
    """Vervang het zangelement in ``{…}``; behoud EHM/ELM."""
    if not source.startswith("{") or not source.endswith("}"):
        return source
    inner = source[1:-1]
    # Exacte plain eerst; anders casefold.
    idx = inner.find(old_plain)
    if idx < 0:
        low = inner.casefold()
        key = old_plain.casefold()
        idx = low.find(key)
        if idx < 0:
            return source
        return "{" + inner[:idx] + new_plain + inner[idx + len(old_plain) :] + "}"
    return "{" + inner[:idx] + new_plain + inner[idx + len(old_plain) :] + "}"


def apply_replacements_to_file(
    path: Path,
    replacements: list[tuple[str, str]],
) -> bool:
    """Pas lemma-vervangingen toe op een bestand. True als er geschreven is.

    Bij ``.vsa`` / YAML-frontmatter: alleen de body (niet ``zoektekst``).
    """
    if not replacements or not path.is_file():
        return False
    raw = path.read_text(encoding="utf-8")
    new = apply_replacements_to_source(raw, replacements)
    if new == raw:
        return False
    path.write_text(new, encoding="utf-8")
    return True


def apply_replacements_to_text(
    text: str,
    replacements: list[tuple[str, str]],
) -> str:
    """Vervang in de hele string (bij VSA-bron: gebruik ``apply_replacements_to_source``)."""
    new = text
    for surface, form in replacements:
        new = replace_sung_token_in_text(new, surface, form)
    return new


def apply_replacements_to_source(
    text: str,
    replacements: list[tuple[str, str]],
) -> str:
    """Vervang alleen in de notatie-body; YAML-frontmatter (``zoektekst``) blijft.

    Soft ``-`` hoort in de gezongen bron, niet in ``zoektekst`` (die is juist
    zonder zachte streepjes; hard ``=`` → zichtbaar ``-`` via zoektekst-extractie).
    """
    if not replacements:
        return text
    from .yaml_frontmatter import parse_vsa_frontmatter_with_body_offset

    _meta, body, offset = parse_vsa_frontmatter_with_body_offset(text)
    if offset <= 0:
        return apply_replacements_to_text(text, replacements)
    new_body = apply_replacements_to_text(body, replacements)
    if new_body == body:
        return text
    return text[:offset] + new_body


def prompt_dictionary_fixes(
    findings: list[DictSyllableFinding],
    *,
    stdin=None,
    stdout=None,
    source_id: str | None = None,
    source_path: Path | str | None = None,
) -> DictionaryPromptResult:
    """Interactieve correctie voor MISMATCH en UNKNOWN op een TTY.

    ``source_id``: catalogus-/stuk-id (één keer vóór de vragen).
    ``source_path``: bestandspad voor klikbare ``pad:regel:kolom:``-regels
    (relatief t.o.v. de werkmap indien mogelijk).
    ``finding.line``/``column`` moeten al bestand-absoluut zijn (1-based).
    Bij Esc, Ctrl+C of EOF: ``result.aborted`` en stop verdere vragen
    (geen verdere findings meer).
    """
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    result = DictionaryPromptResult()
    if not hasattr(stdin, "isatty") or not stdin.isatty():
        return result

    actionable = [
        f for f in findings if f.code in {CODE_MISMATCH, CODE_UNKNOWN}
    ]
    if not actionable:
        return result

    label = (source_id or "").strip()
    if label:
        print(f"--- {label} ---", file=stdout)

    try:
        for finding in actionable:
            loc = format_clickable_location(
                source_path, finding.line, finding.column
            )
            if finding.code == CODE_MISMATCH:
                aborted = _prompt_mismatch(
                    finding,
                    result,
                    stdin=stdin,
                    stdout=stdout,
                    location=loc,
                )
            elif finding.code == CODE_UNKNOWN:
                aborted = _prompt_unknown(
                    finding,
                    result,
                    stdin=stdin,
                    stdout=stdout,
                    location=loc,
                )
            else:
                aborted = False
            if aborted or result.aborted:
                result.aborted = True
                return result
    except KeyboardInterrupt:
        print(file=stdout)
        return _mark_aborted(result, stdout)
    return result


def prompt_unknown_forms(
    findings: list[DictSyllableFinding],
    *,
    stdin=None,
    stdout=None,
) -> list[str]:
    """Compat: alleen UNKNOWN → lijst; gebruik ``prompt_dictionary_fixes``."""
    only_unknown = [f for f in findings if f.code == CODE_UNKNOWN]
    return prompt_dictionary_fixes(
        only_unknown, stdin=stdin, stdout=stdout
    ).added_or_updated


def is_interactive_stdin(stdin=None) -> bool:
    stdin = stdin or sys.stdin
    return bool(hasattr(stdin, "isatty") and stdin.isatty())


def _prompt_mismatch(
    finding: DictSyllableFinding,
    result: DictionaryPromptResult,
    *,
    stdin,
    stdout,
    location: str = "",
) -> bool:
    """True als de gebruiker de hele check afbreekt."""
    expected = finding.expected or ""
    surface_norm = _normalize_form(finding.surface)
    from .syllabify import _transfer_letter_case

    cased = _transfer_letter_case(finding.surface, expected)
    if location:
        print(location, file=stdout)
    print(finding.message_nl, file=stdout)
    print(
        f"[Enter/Spatie]: corrigeer de bron (`{finding.surface}` → `{cased}`)",
        file=stdout,
    )
    print(
        "[+/=]: huidige vorm in lijst, [Tab]: overslaan, [Esc]: stoppen",
        file=stdout,
    )
    print(
        "of typ een andere hyphenvorm (wordt canon én vervangt de bron): ",
        end="",
        file=stdout,
        flush=True,
    )
    choice = _read_prompt_action(stdin, stdout)
    if choice == _ACTION_ABORT:
        return _mark_aborted(result, stdout)
    if choice == _ACTION_SKIP:
        print("Overgeslagen.", file=stdout)
        return False
    if choice == "" or choice == "v":
        result.replacements.append((finding.surface, expected))
        print(f"Bron: `{finding.surface}` → `{cased}`", file=stdout)
        return False
    if choice == _ACTION_ACCEPT_CURRENT:
        try:
            written = set_canonical_form(surface_norm, allow_replace=True)
        except ValueError as exc:
            print(f"Niet aangepast: {exc}", file=stdout)
            return False
        result.added_or_updated.append(written)
        print(f"Lijst bijgewerkt: {written}", file=stdout)
        return False
    try:
        written = set_canonical_form(choice, allow_replace=True)
    except ValueError as exc:
        print(f"Niet aangepast: {exc}", file=stdout)
        return False
    result.added_or_updated.append(written)
    result.replacements.append((finding.surface, written))
    print(
        f"Lijst: {written}; bron: `{finding.surface}` → "
        f"`{_transfer_letter_case(finding.surface, written)}`",
        file=stdout,
    )
    return False


def _prompt_unknown(
    finding: DictSyllableFinding,
    result: DictionaryPromptResult,
    *,
    stdin,
    stdout,
    location: str = "",
) -> bool:
    """True als de gebruiker de hele check afbreekt."""
    surface_norm = _normalize_form(finding.surface)
    has_hyphen = "-" in finding.surface or HARD_HYPHEN in finding.surface
    suggestion = (
        surface_norm
        if has_hyphen
        else _normalize_form(hyphenate_dutch_word(_alpha_core(finding.surface)))
    )
    if not suggestion:
        suggestion = surface_norm

    if location:
        print(location, file=stdout)
    print(
        f"Onbekend woord `{finding.surface}` — niet in "
        f"{dictionary_path_label()}.",
        file=stdout,
    )
    default_hint = f"voeg `{suggestion}` toe"
    if not has_hyphen and suggestion != surface_norm:
        from .syllabify import _transfer_letter_case

        cased = _transfer_letter_case(finding.surface, suggestion)
        default_hint = f"voeg `{suggestion}` toe (bron → `{cased}` met v)"
    print(f"[Enter/Spatie]: {default_hint}", file=stdout)
    print(
        "[+/=]: huidige vorm in lijst, [Tab]: overslaan, [Esc]: stoppen",
        file=stdout,
    )
    print(
        "of typ een andere hyphenvorm (wordt canon én vervangt de bron): ",
        end="",
        file=stdout,
        flush=True,
    )
    choice = _read_prompt_action(stdin, stdout)
    if choice == _ACTION_ABORT:
        return _mark_aborted(result, stdout)
    if choice == _ACTION_SKIP:
        print("Overgeslagen.", file=stdout)
        return False
    if choice == _ACTION_ACCEPT_CURRENT:
        try:
            written = set_canonical_form(surface_norm, allow_replace=True)
        except ValueError as exc:
            print(f"Niet toegevoegd: {exc}", file=stdout)
            return False
        result.added_or_updated.append(written)
        print(f"Toegevoegd: {written}", file=stdout)
        return False
    if choice == "v" and not has_hyphen and suggestion != surface_norm:
        try:
            written = set_canonical_form(suggestion, allow_replace=True)
        except ValueError as exc:
            print(f"Niet toegevoegd: {exc}", file=stdout)
            return False
        result.added_or_updated.append(written)
        result.replacements.append((finding.surface, written))
        print(f"Toegevoegd + bron vervangen: {written}", file=stdout)
        return False
    form = suggestion if choice == "" else choice
    try:
        written = set_canonical_form(form, allow_replace=True)
    except ValueError as exc:
        print(f"Niet toegevoegd: {exc}", file=stdout)
        return False
    result.added_or_updated.append(written)
    if choice == "" and not has_hyphen and suggestion != surface_norm:
        # Enter op UNKNOWN zonder streepjes: alleen lijst (geen stille bronfix).
        pass
    print(f"Toegevoegd: {written}", file=stdout)
    return False


def _can_raw_keys(stdin) -> bool:
    """True als we Esc/Tab/Spatie zonder Enter kunnen lezen (echte terminal)."""
    if stdin is not sys.stdin:
        return False
    if not hasattr(stdin, "isatty") or not stdin.isatty():
        return False
    try:
        stdin.fileno()
    except (AttributeError, OSError, ValueError):
        return False
    return True


def _read_prompt_action(stdin, stdout) -> str:
    """Lees TTY-actie: default / skip / abort / accept-current / hyphenvorm.

    Op een echte terminal: eerste toets beslist (Enter/Spatie/Tab/Esc/+/ =),
    anders vrije hyphenvorm tot Enter. In tests (namaak-TTY): regelmodus.
    """
    if _can_raw_keys(stdin):
        return _read_prompt_action_raw(stdin, stdout)
    return _read_prompt_action_line(stdin)


def _read_prompt_action_line(stdin) -> str:
    """Regelmodus (tests): Enter/Spatie, Tab, Esc/q, +/=, of hyphenvorm."""
    try:
        raw_line = stdin.readline()
    except KeyboardInterrupt:
        return _ACTION_ABORT
    if raw_line == "":
        return _ACTION_ABORT
    # Behoud Tab als enige teken vóór strip van overige whitespace.
    if raw_line[:1] == "\t":
        return _ACTION_SKIP
    stripped = raw_line.strip()
    if stripped == "":
        return ""
    if stripped == "\x1b" or stripped.casefold() in {"q", "quit", "abort", "esc"}:
        return _ACTION_ABORT
    if stripped in {"+", "=", "a"}:
        return _ACTION_ACCEPT_CURRENT
    if stripped == "s":
        return _ACTION_SKIP
    return stripped


def _read_prompt_action_raw(stdin, stdout) -> str:
    """Single-key modus (Windows ``msvcrt`` of Unix cbreak)."""
    try:
        if sys.platform == "win32":
            return _read_prompt_action_win(stdout)
        return _read_prompt_action_posix(stdin, stdout)
    except KeyboardInterrupt:
        print(file=stdout)
        return _ACTION_ABORT


def _read_prompt_action_win(stdout) -> str:
    import msvcrt

    while True:
        ch = msvcrt.getwch()
        if ch in {"\x03"}:  # Ctrl+C
            print(file=stdout)
            return _ACTION_ABORT
        if ch in {"\r", "\n", " "}:
            print(file=stdout)
            return ""
        if ch == "\t":
            print(file=stdout)
            return _ACTION_SKIP
        if ch == "\x1b":
            print(file=stdout)
            return _ACTION_ABORT
        if ch in {"\x00", "\xe0"}:
            # Functietoets / pijltje — negeer scancode.
            msvcrt.getwch()
            continue
        if ch in {"+", "="}:
            print(ch, file=stdout)
            return _ACTION_ACCEPT_CURRENT
        if ch in {"\b", "\x08"}:
            continue
        # Vrije hyphenvorm: echo + verdere tekens tot Enter.
        buf = [ch]
        print(ch, end="", file=stdout, flush=True)
        while True:
            nxt = msvcrt.getwch()
            if nxt in {"\x03"}:
                print(file=stdout)
                return _ACTION_ABORT
            if nxt in {"\r", "\n"}:
                print(file=stdout)
                return "".join(buf).strip() or _ACTION_ABORT
            if nxt == "\x1b":
                print(file=stdout)
                return _ACTION_ABORT
            if nxt in {"\b", "\x08"}:
                if buf:
                    buf.pop()
                    print("\b \b", end="", file=stdout, flush=True)
                continue
            if nxt in {"\x00", "\xe0"}:
                msvcrt.getwch()
                continue
            buf.append(nxt)
            print(nxt, end="", file=stdout, flush=True)


def _read_prompt_action_posix(stdin, stdout) -> str:
    import termios
    import tty

    fd = stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            ch = stdin.read(1)
            if ch == "":
                return _ACTION_ABORT
            if ch in {"\x03"}:  # Ctrl+C
                print(file=stdout)
                return _ACTION_ABORT
            if ch in {"\r", "\n", " "}:
                print(file=stdout)
                return ""
            if ch == "\t":
                print(file=stdout)
                return _ACTION_SKIP
            if ch == "\x1b":
                print(file=stdout)
                return _ACTION_ABORT
            if ch in {"+", "="}:
                print(ch, file=stdout)
                return _ACTION_ACCEPT_CURRENT
            buf = [ch]
            print(ch, end="", file=stdout, flush=True)
            while True:
                nxt = stdin.read(1)
                if nxt == "":
                    return "".join(buf).strip() or _ACTION_ABORT
                if nxt in {"\x03"}:
                    print(file=stdout)
                    return _ACTION_ABORT
                if nxt in {"\r", "\n"}:
                    print(file=stdout)
                    return "".join(buf).strip() or _ACTION_ABORT
                if nxt == "\x1b":
                    print(file=stdout)
                    return _ACTION_ABORT
                if nxt in {"\x7f", "\b"}:
                    if buf:
                        buf.pop()
                        print("\b \b", end="", file=stdout, flush=True)
                    continue
                buf.append(nxt)
                print(nxt, end="", file=stdout, flush=True)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _mark_aborted(result: DictionaryPromptResult, stdout) -> bool:
    result.aborted = True
    print(
        "Check afgebroken — geen verdere woorden/bestanden in deze run.",
        file=stdout,
    )
    return True



def _normalize_form(word: str) -> str:
    m = _EDGE_PUNCT.match(word.strip())
    core = m.group(2) if m else word.strip()
    return core.casefold()


def _alpha_core(word: str) -> str:
    m = _EDGE_PUNCT.match(word)
    return m.group(2) if m else word


def _frontmatter_body(source_text: str) -> tuple[str, int]:
    """Body na YAML-frontmatter + aantal regels vóór de body (1-based offset)."""
    if not source_text:
        return "", 0
    stripped = source_text.lstrip("\ufeff")
    bom_lines = source_text[: len(source_text) - len(stripped)].count("\n")
    if stripped.lstrip().startswith("---"):
        from .yaml_frontmatter import strip_yaml_frontmatter

        _meta, body, fm_base = strip_yaml_frontmatter(stripped)
        return body, bom_lines + fm_base
    return stripped, bom_lines


def _lyrics_locate_region(source_text: str) -> tuple[str, int]:
    """Gestripte body (geen frontmatter/commentaren) + frontmatter-regeloffset.

    Let op: commentaarstrip verschuift regels — gebruik ``_locate`` (met
    offset-map) voor bestand-absolute posities, niet alleen deze helper.
    """
    body, line_base = _frontmatter_body(source_text)
    if not body:
        return "", line_base
    from .vsa_comments import strip_vsa_html_comments_with_offset_map

    cleaned, _ = strip_vsa_html_comments_with_offset_map(body)
    return cleaned, line_base


def _surface_match_starts_at(text: str, start: int) -> bool:
    """True als ``start`` geen midden van een langer hyphen-/woordstuk is.

    Voorkomt dat ``lu-ja`` matcht binnen ``Al-le-lu-ja`` (vorige char is ``-``).
    """
    if start <= 0:
        return True
    prev = text[start - 1]
    return not (prev.isalnum() or prev in "-=")


def _find_surface_offset(text: str, surface: str) -> int:
    """Eerste veilige offset van ``surface`` in ``text``, of ``-1``."""
    if not surface or not text:
        return -1
    start = 0
    while True:
        idx = text.find(surface, start)
        if idx < 0:
            break
        if _surface_match_starts_at(text, idx):
            return idx
        start = idx + 1
    # Zelfde hyphenvorm (niet eeu-wen als we eeuw-en zoeken — dat is lemma-ruis).
    want = _normalize_form(surface)
    plain = syllable_lemma(surface)
    if not plain or not want:
        return -1
    for match in re.finditer(r"[\w=\-]+", text, re.UNICODE):
        token = match.group(0)
        if not any(ch.isalpha() for ch in token):
            continue
        if syllable_lemma(token) != plain:
            continue
        if _normalize_form(token) != want:
            continue
        if not _surface_match_starts_at(text, match.start()):
            continue
        return match.start()
    return -1


def _find_syllable_chain_offset(text: str, surface: str) -> int:
    """Offset van een hyphen-kern waarvan de delen in volgorde in ``text`` staan.

    Tussen lettergrepen mag VSA-notatie staan (``{}`` ``\\`` ELMs), maar geen
    spatie — anders is het een ander woord.
    """
    parts = [
        p
        for p in re.split(r"[-|=]+", surface)
        if p and any(ch.isalpha() for ch in p)
    ]
    if not parts:
        return -1
    if len(parts) == 1:
        return _find_surface_offset(text, parts[0])
    # Non-space, non-letter bridge (scopes/ELMs/EHM), case-insensitive letters.
    bridge = r"[^\sA-Za-zÀ-ÖØ-öø-ÿ]*?"
    pattern = re.escape(parts[0]) + "".join(
        bridge + re.escape(p) for p in parts[1:]
    )
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match is None:
        return -1
    if not _surface_match_starts_at(text, match.start()):
        # Mid-woord-treffer: zoek verder.
        start = match.start() + 1
        while start < len(text):
            match = re.search(pattern, text[start:], flags=re.IGNORECASE)
            if match is None:
                return -1
            abs_start = start + match.start()
            if _surface_match_starts_at(text, abs_start):
                return abs_start
            start = abs_start + 1
        return -1
    return match.start()


def _offset_to_line_column(text: str, offset: int, *, line_base: int = 0) -> tuple[int, int]:
    """1-based regel/kolom in ``text``; ``line_base`` telt eerdere bronregels mee."""
    safe = max(0, min(len(text), offset))
    before = text[:safe]
    line = before.count("\n") + 1 + line_base
    last_nl = before.rfind("\n")
    col = (safe + 1) if last_nl < 0 else (safe - last_nl)
    return line, max(1, col)


def _locate(source_text: str, surface: str) -> tuple[int, int]:
    """Zoek positie in bronlyrics — nooit in YAML, HTML- of ``#``-commentaar.

    Zoekt in de tekst ná strip van commentaar (daar horen geen lyrics), maar
    mapt de treffer terug via de offset-map zodat regelnummers bestand-absoluut
    blijven. Synthetic kernen (scope-brug ``U-roep``) zoeken op lettergrepen.
    """
    if not source_text:
        return 1, 1
    body, line_base = _frontmatter_body(source_text)
    if not body:
        return max(1, line_base + 1), 1

    from .vsa_comments import (
        semantic_offset_to_source,
        strip_vsa_html_comments_with_offset_map,
    )

    cleaned, offset_map = strip_vsa_html_comments_with_offset_map(body)
    if not cleaned.strip():
        return max(1, line_base + 1), 1

    # Bij .mvsa: bij voorkeur alleen op L-regels zoeken (geen @oct/@title).
    search_text, search_to_cleaned = _prefer_mvsa_lyrics_search_view(cleaned)

    # Eerst scope-brug/keten (``{\eeuw}{\en}``), dan exacte plat-token —
    # anders vindt lemma-ruis het al-correcte ``eeu-wen`` vóór de foute vorm.
    idx_in_search = _find_syllable_chain_offset(search_text, surface)
    if idx_in_search < 0:
        idx_in_search = _find_surface_offset(search_text, surface)
    if idx_in_search < 0:
        # Laatste redmiddel: eerste niet-lege lyrics-regel in cleaned (nooit commentaar).
        idx_cleaned = next(
            (i for i, ch in enumerate(cleaned) if not ch.isspace()), 0
        )
    else:
        idx_cleaned = search_to_cleaned(idx_in_search)

    idx_body = semantic_offset_to_source(offset_map, idx_cleaned)
    line, column = _offset_to_line_column(body, idx_body, line_base=line_base)
    # Hard guard: nooit een commentaarregel rapporteren.
    rows = source_text.splitlines()
    if 1 <= line <= len(rows):
        stripped = rows[line - 1].lstrip()
        if stripped.startswith("<!--") or stripped.startswith("#"):
            for i, row in enumerate(rows[line:], start=line + 1):
                s = row.lstrip()
                if not s or s.startswith("<!--") or s.startswith("#") or s.startswith("-->"):
                    continue
                if s.startswith("---"):
                    continue
                return i, 1
    return line, column


def _prefer_mvsa_lyrics_search_view(
    cleaned_body: str,
) -> tuple[str, Callable[[int], int]]:
    """Voor MVSA: zoekview met alleen L-regelinhoud; anders hele cleaned body.

    Retourneert ``(search_text, map_search_offset_to_cleaned)``.
    """
    # Heuristiek: minstens één lyrics-regel ``L:`` / ``L1:`` / …
    lyric_line_re = re.compile(
        r"^([ \t]*)(L\d*)([+]?):([ \t]*)(.*?)(\r\n|\n|\r|$)",
        re.MULTILINE,
    )
    matches = list(lyric_line_re.finditer(cleaned_body))
    if not matches:
        return cleaned_body, (lambda i: i)

    parts: list[str] = []
    # search_offset → cleaned_offset
    spans: list[tuple[int, int, int]] = []  # search_start, cleaned_start, length
    search_pos = 0
    for match in matches:
        content = match.group(5)
        if not content:
            continue
        cleaned_start = match.start(5)
        parts.append(content)
        spans.append((search_pos, cleaned_start, len(content)))
        search_pos += len(content)
        # Scheiding zodat tokens van opeenvolgende L-regels niet plakken.
        parts.append("\n")
        search_pos += 1

    if not spans:
        return cleaned_body, (lambda i: i)

    search_text = "".join(parts)

    def _map(search_offset: int) -> int:
        for s_start, c_start, length in spans:
            if s_start <= search_offset < s_start + length:
                return c_start + (search_offset - s_start)
        # Fallback: laatste span (incl. newline-separator erna)
        s_start, c_start, length = spans[-1]
        return c_start + min(length, max(0, search_offset - s_start))

    return search_text, _map
