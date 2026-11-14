"""Controleer gezongen VSA-body tegen de canonieke syllable-dictionary."""

from __future__ import annotations

import re
import sys
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
    canonical_syllable_form,
    clear_syllable_dictionary_cache,
    dictionary_file_path,
    dictionary_path_label,
    load_syllable_dictionary,
    syllable_lemma,
)

CODE_MISMATCH = "VSA-SYLLABLE-DICT-MISMATCH"
CODE_UNKNOWN = "VSA-SYLLABLE-DICT-UNKNOWN"
DOC_URL = "docs/formats/syllabificatie.md"

_TOKEN_RE = re.compile(r"\S+", re.UNICODE)
_EDGE_PUNCT = re.compile(r"^([^\w=]*)(.*?)([^\w=]*)$", re.UNICODE)

_HINT_TTY = (
    "Op een TTY: Enter = voorgestelde actie; "
    "`a` = accepteer huidige vorm in de lijst; "
    "`v` = vervang in de bron; "
    "`s` = overslaan; of typ een andere hyphenvorm."
)


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
    """Woordkernen uit kale lyrics (leestekenrand weg; geen kale maatstrepen)."""
    cores: list[str] = []
    for match in _TOKEN_RE.finditer(bare):
        m = _EDGE_PUNCT.match(match.group(0))
        if not m:
            continue
        core = m.group(2)
        if not core or not any(ch.isalpha() for ch in core):
            continue
        cores.append(core)
    return cores


def iter_vsa_lyric_word_cores(document: Document) -> list[str]:
    """Canonieke lyrics-woorden uit een geparste VSA-body (geen frontmatter)."""
    return iter_body_word_cores(bare_sung_text(document))


def iter_mvsa_lyric_word_cores(source: str) -> list[str]:
    """Canonieke lyrics-woorden uit .mvsa: alleen L-regels, met soft ``-``/``=``.

    Geen ``@title`` / ``@do`` / zoektekst / commentaar / S/A/T/B-regels.
    """
    from .mvsa_parse import parse_mvsa
    from .mvsa_validate import is_lyrics_stem
    from .text_export import _first_lyrics_lpos, join_lyric_syllables

    doc = parse_mvsa(source)
    parts: list[str] = []
    open_word = False
    word_chunks: list[str] = []

    def flush() -> None:
        nonlocal parts, open_word
        word_chunks.extend(parts)
        parts = []
        open_word = False

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
                            continue
                        if open_word or lpos.continues_word:
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
    flush()
    cores: list[str] = []
    for chunk in word_chunks:
        cores.extend(iter_body_word_cores(chunk))
    return cores


def find_dictionary_syllable_issues(
    document: Document,
    *,
    source_text: str = "",
) -> list[DictSyllableFinding]:
    """Vergelijk VSA-lyrics (AST) met de canonieke lijst."""
    return find_dictionary_syllable_issues_from_cores(
        iter_vsa_lyric_word_cores(document),
        source_text=source_text,
    )


def find_dictionary_syllable_issues_from_cores(
    cores: list[str],
    *,
    source_text: str = "",
) -> list[DictSyllableFinding]:
    """Vergelijk gegeven lyrics-woordkernen met de canonieke lijst."""
    findings: list[DictSyllableFinding] = []
    seen: set[str] = set()
    for core in cores:
        key = syllable_lemma(core)
        if not key or key in seen:
            continue
        seen.add(key)
        expected = canonical_syllable_form(core)
        surface_norm = _normalize_form(core)
        line, column = _locate(source_text, core)

        if expected is not None:
            if surface_norm == expected:
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
                        f"(canonieke zing-deling)."
                    ),
                    hint_nl=(
                        f"Vervang in de bron door `{expected}` (lemma `{key}`), "
                        f"of accepteer bewust een andere vorm in "
                        f"`{dictionary_path_label()}`. {_HINT_TTY} "
                        f"Norm: {DOC_URL}."
                    ),
                )
            )
            continue

        if is_monosyllable_exception(core):
            continue
        if "-" not in core and HARD_HYPHEN not in core:
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
                    f"syllable-dictionary (voorstel: `{suggestion}`)."
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
) -> list[DictSyllableFinding]:
    """Dictionary-check op .mvsa: uitsluitend L-lyrics."""
    return find_dictionary_syllable_issues_from_cores(
        iter_mvsa_lyric_word_cores(source),
        source_text=source,
    )


def append_canonical_form(form: str) -> str:
    """Voeg een canonieke vorm toe; fout als lemma al een ándere vorm heeft."""
    return set_canonical_form(form, allow_replace=False)


def set_canonical_form(form: str, *, allow_replace: bool = True) -> str:
    """Zet of vervang de canonieke hyphenvorm; schrijf de lijst opnieuw gesorteerd."""
    normalized = _normalize_form(form)
    if not normalized or not any(ch.isalpha() for ch in normalized):
        raise ValueError(f"ongeldige hyphenvorm: {form!r}")
    key = syllable_lemma(normalized)
    existing = load_syllable_dictionary().get(key)
    if existing is not None and existing == normalized:
        return existing
    if existing is not None and not allow_replace:
        raise ValueError(
            f"lemma {key!r} staat al als {existing!r}, niet {normalized!r}"
        )

    path = dictionary_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        header, entries = _split_dictionary_text(
            path.read_text(encoding="utf-8")
        )
    else:
        header, entries = "", []

    by_lemma = {syllable_lemma(e): e for e in entries if syllable_lemma(e)}
    by_lemma[key] = normalized
    _write_sorted_dictionary(path, header, by_lemma)
    clear_syllable_dictionary_cache()
    return normalized


def rewrite_dictionary_sorted(path: Path | None = None) -> int:
    """Herschrijf de dictionary alfabetisch op lemma. Retourneert aantal entries."""
    target = path if path is not None else dictionary_file_path()
    if not target.is_file():
        return 0
    header, entries = _split_dictionary_text(target.read_text(encoding="utf-8"))
    by_lemma = {syllable_lemma(e): e for e in entries if syllable_lemma(e)}
    _write_sorted_dictionary(target, header, by_lemma)
    clear_syllable_dictionary_cache()
    return len(by_lemma)


def _split_dictionary_text(text: str) -> tuple[str, list[str]]:
    """Scheid kopcommentaar van entry-regels."""
    lines = text.splitlines()
    header_lines: list[str] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped or stripped.startswith("#"):
            header_lines.append(lines[i])
            i += 1
            continue
        break
    entries: list[str] = []
    for line in lines[i:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.append(_normalize_form(stripped))
    header = "\n".join(header_lines)
    if header_lines:
        header += "\n"
    return header, entries


def _write_sorted_dictionary(
    path: Path,
    header: str,
    by_lemma: dict[str, str],
) -> None:
    """Schrijf header + entries gesorteerd op lemma (dan op hyphenvorm)."""
    ordered = [
        by_lemma[lemma]
        for lemma in sorted(by_lemma.keys(), key=lambda k: (k, by_lemma[k]))
    ]
    body = "".join(f"{form}\n" for form in ordered)
    path.write_text(f"{header}{body}", encoding="utf-8", newline="\n")


def replace_sung_token_in_text(text: str, surface: str, new_form: str) -> str:
    """Vervang woordkernen met hetzelfde lemma; behoud lettercase per treffer."""
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
        return f"{prefix}{_transfer_letter_case(core, target)}{suffix}"

    return _TOKEN_RE.sub(_repl, text)


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
) -> DictionaryPromptResult:
    """Interactieve correctie voor MISMATCH en UNKNOWN op een TTY.

    ``source_id``: catalogus-/stuk-id (één keer vóór de vragen), handig bij
    batch-validate/syllabify.
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

    for finding in actionable:
        if finding.code == CODE_MISMATCH:
            _prompt_mismatch(finding, result, stdin=stdin, stdout=stdout)
        elif finding.code == CODE_UNKNOWN:
            _prompt_unknown(finding, result, stdin=stdin, stdout=stdout)
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
) -> None:
    expected = finding.expected or ""
    surface_norm = _normalize_form(finding.surface)
    from .syllabify import _transfer_letter_case

    cased = _transfer_letter_case(finding.surface, expected)
    print(finding.message_nl, file=stdout)
    print(
        f"[Enter] = vervang in bron: `{finding.surface}` → `{cased}`",
        file=stdout,
    )
    print(
        f"[a] = accepteer huidige vorm `{surface_norm}` als canon "
        f"(overschrijft de lijst)",
        file=stdout,
    )
    print("[s] = overslaan", file=stdout)
    print(
        "of typ een andere hyphenvorm (wordt canon én vervangt de bron)",
        file=stdout,
    )
    print("> ", end="", file=stdout, flush=True)
    choice = _read_choice(stdin)
    if choice in {"", "v"}:
        result.replacements.append((finding.surface, expected))
        print(f"Bron: `{finding.surface}` → `{cased}`", file=stdout)
        return
    if choice == "s":
        print("Overgeslagen.", file=stdout)
        return
    if choice == "a":
        try:
            written = set_canonical_form(surface_norm, allow_replace=True)
        except ValueError as exc:
            print(f"Niet aangepast: {exc}", file=stdout)
            return
        result.added_or_updated.append(written)
        print(f"Lijst bijgewerkt: {written}", file=stdout)
        return
    try:
        written = set_canonical_form(choice, allow_replace=True)
    except ValueError as exc:
        print(f"Niet aangepast: {exc}", file=stdout)
        return
    result.added_or_updated.append(written)
    result.replacements.append((finding.surface, written))
    print(
        f"Lijst: {written}; bron: `{finding.surface}` → "
        f"`{_transfer_letter_case(finding.surface, written)}`",
        file=stdout,
    )


def _prompt_unknown(
    finding: DictSyllableFinding,
    result: DictionaryPromptResult,
    *,
    stdin,
    stdout,
) -> None:
    surface_norm = _normalize_form(finding.surface)
    has_hyphen = "-" in finding.surface or HARD_HYPHEN in finding.surface
    suggestion = (
        surface_norm
        if has_hyphen
        else _normalize_form(hyphenate_dutch_word(_alpha_core(finding.surface)))
    )
    if not suggestion:
        suggestion = surface_norm

    print(
        f"Onbekend woord `{finding.surface}` — niet in "
        f"{dictionary_path_label()}.",
        file=stdout,
    )
    print(
        f"[Enter] = voeg `{suggestion}` toe aan de canonieke lijst",
        file=stdout,
    )
    if not has_hyphen and suggestion != surface_norm:
        from .syllabify import _transfer_letter_case

        cased = _transfer_letter_case(finding.surface, suggestion)
        print(
            f"[v] = vervang in bron naar `{cased}` én voeg toe aan de lijst",
            file=stdout,
        )
    print("[s] = overslaan", file=stdout)
    print("of typ een andere hyphenvorm", file=stdout)
    print("> ", end="", file=stdout, flush=True)
    choice = _read_choice(stdin)
    if choice == "s":
        print("Overgeslagen.", file=stdout)
        return
    if choice == "v" and not has_hyphen and suggestion != surface_norm:
        try:
            written = set_canonical_form(suggestion, allow_replace=True)
        except ValueError as exc:
            print(f"Niet toegevoegd: {exc}", file=stdout)
            return
        result.added_or_updated.append(written)
        result.replacements.append((finding.surface, written))
        print(f"Toegevoegd + bron vervangen: {written}", file=stdout)
        return
    form = suggestion if choice in {"", "a"} else choice
    try:
        written = set_canonical_form(form, allow_replace=True)
    except ValueError as exc:
        print(f"Niet toegevoegd: {exc}", file=stdout)
        return
    result.added_or_updated.append(written)
    print(f"Toegevoegd: {written}", file=stdout)


def _read_choice(stdin) -> str:
    raw_line = stdin.readline()
    if raw_line == "":
        return ""
    return raw_line.strip()


def _normalize_form(word: str) -> str:
    m = _EDGE_PUNCT.match(word.strip())
    core = m.group(2) if m else word.strip()
    return core.casefold()


def _alpha_core(word: str) -> str:
    m = _EDGE_PUNCT.match(word)
    return m.group(2) if m else word


def _lyrics_locate_region(source_text: str) -> tuple[str, int]:
    """Alleen notatie-body (geen YAML-frontmatter / HTML-commentaren).

    Retourneert ``(zoektekst_voor_locate, regel-offset)`` zodat gemelde
    regelnummers blijven kloppen t.o.v. het aangeleverde ``source_text``.
    """
    if not source_text:
        return "", 0
    text = source_text
    line_base = 0
    stripped = text.lstrip("\ufeff")
    bom_lines = source_text[: len(source_text) - len(stripped)].count("\n")
    if stripped.lstrip().startswith("---"):
        from .yaml_frontmatter import strip_yaml_frontmatter

        _meta, body, fm_base = strip_yaml_frontmatter(stripped)
        text = body
        line_base = bom_lines + fm_base
    from .vsa_comments import strip_vsa_html_comments_with_offset_map

    cleaned, _ = strip_vsa_html_comments_with_offset_map(text)
    return cleaned, line_base


def _locate(source_text: str, surface: str) -> tuple[int, int]:
    """Zoek positie in **lyrics-body**, nooit in ``zoektekst``/frontmatter/comments."""
    if not source_text:
        return 1, 1
    body, line_base = _lyrics_locate_region(source_text)
    if not body:
        return max(1, line_base + 1), 1

    idx = body.find(surface)
    if idx < 0:
        # Alleen lettergreepachtige tokens in de body — geen YAML-keys/waarden.
        plain = syllable_lemma(surface)
        for match in re.finditer(r"[\w=\-]+", body, re.UNICODE):
            token = match.group(0)
            # Skip pure metadata-achtige tokens zonder letters.
            if not any(ch.isalpha() for ch in token):
                continue
            if syllable_lemma(token) == plain:
                idx = match.start()
                break
    if idx < 0:
        return max(1, line_base + 1), 1
    before = body[:idx]
    line = before.count("\n") + 1 + line_base
    last_nl = before.rfind("\n")
    col = (idx + 1) if last_nl == -1 else (idx - last_nl)
    return line, col
