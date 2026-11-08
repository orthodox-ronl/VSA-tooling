"""VSA-tekst → noten per tekstfrase (`*` / `**` / `/` / `//` als frasegrens)."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from .ast import Document, PitchMarkerNode, PitchTransitionNode, ScopeNode, TextNode
from .bracket_directive import VALID_EHM_VALUES
from .dutch_syllables import recite_syllables
from .duration_model import elm_to_duration
from .music import Duration, Pitch
from .musicxml_renderer import _PUNCT_ONLY_RE
from .parser import Parser
from .pitch_resolver import PitchResolver
from .yaml_frontmatter import parse_vsa_frontmatter_with_body_offset

# Frasescheiders in extract_stanza_notes (losse tokens).
# `*` = frasescheiding; `**` = sterke scheiding vóór laatste (zangers).
# Losse `/` en `//` blijven EHM/maatstreep: leidende `//` op de laatste
# frase is bladconventie, géén extra split. Trailing `/`/`//` tellen wél
# mee in has_phrase_separators / ensure (zie mapping-vsa.md).
_STANZA_MARKERS = frozenset({"*", "**"})
_BARE_EHM_TOKENS = frozenset(
    v for v in VALID_EHM_VALUES if v and all(ch in "/\\-~#♯+b♭" for ch in v)
)
_BARE_EHM_SORTED = sorted(_BARE_EHM_TOKENS, key=len, reverse=True)
_PHRASE_SEP_TRAIL = re.compile(r"(?:\*\*|//|\*|/)\s*$")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def strip_html_comments(text: str) -> str:
    """Verwijder ``<!-- … -->`` (ook over regels) voor frase-telling."""
    return _HTML_COMMENT.sub("", text)


def fold_indent_continuations(lines: list[str]) -> list[str]:
    """Voeg ingesprongen vervolgregels samen met de vorige frase-regel.

    Conventie voor te lange frasen op papier: volgende delen op een nieuwe
    regel, maar ingesprongen — hoort bij dezelfde frase, geen nieuwe grens.
    """
    if not lines:
        return []
    out: list[str] = []
    for ln in lines:
        if out and ln[:1].isspace():
            prev = out[-1].rstrip()
            cont = ln.strip()
            out[-1] = f"{prev} {cont}" if cont else prev
        else:
            out.append(ln.rstrip())
    return out


def music_phrase_lines(body: str) -> list[str]:
    """Niet-lege muziekregels, HTML-commentaar weg, indent-wraps samengevoegd."""
    cleaned = strip_html_comments(body)
    raw = [
        ln
        for ln in cleaned.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    return fold_indent_continuations(raw)


def has_phrase_separators(body: str) -> bool:
    """True als de bron al `*` / `**` als frasescheiding gebruikt.

    Trailing `/` of `//` alleen is géén reden om ensure over te slaan:
    leidende `//` op de laatste frase is bladconventie. Zonder `*`/`**`
    blijft regel-per-frase (+ indent-wrap) de ensure-route.
    """
    cleaned = strip_html_comments(body)
    for ln in cleaned.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        for tok in s.split():
            if tok in _STANZA_MARKERS:
                return True
    return False


def ensure_stanza_stars(body: str) -> tuple[str, list[str]]:
    """Normaliseer naar `*`-frasen voor template-mapping indien nodig.

    - HTML-commentaar en ``#``-regels tellen niet mee.
    - Ingesprongen vervolgregels horen bij de vorige frase (print-wrap).
    - Zonder frasescheiders: één ``*`` per logische (niet-ingesprongen) regel.
    - Met scheiders: body ongewijzigd (``extract_stanza_notes`` splitst zelf).

    Returns ``(normalized_body, notes_for_report)``.
    """
    notes: list[str] = []
    if has_phrase_separators(body):
        return body, notes

    phrases = music_phrase_lines(body)
    if len(phrases) <= 1:
        notes.append("geen multi-regel frase-splits nodig")
        return body, notes

    notes.append(
        f"geen frasescheiding in bron → {len(phrases)} logische regels "
        f"genormaliseerd tot frasen met `*` (ingesprongen wraps samengevoegd)"
    )

    # Classificeer bronregels; voeg `*` toe op het laatste lid van elke
    # frase-groep (niet-ingesprongen start + indent-vervolgen), behalve de laatste groep.
    class _Item:
        __slots__ = ("kind", "raw", "group")

        def __init__(self, kind: str, raw: str, group: int | None = None) -> None:
            self.kind = kind
            self.raw = raw
            self.group = group

    items: list[_Item] = []
    in_comment = False
    group_id = -1
    for ln in body.splitlines():
        s = ln.strip()
        if in_comment:
            items.append(_Item("keep", ln))
            if "-->" in ln:
                in_comment = False
            continue
        if "<!--" in s:
            items.append(_Item("keep", ln))
            if "-->" not in s[s.find("<!--") + 4 :]:
                in_comment = True
            continue
        if not s or s.startswith("#"):
            items.append(_Item("keep", ln))
            continue
        if ln[:1].isspace() and group_id >= 0:
            items.append(_Item("music", ln, group_id))
            continue
        group_id += 1
        items.append(_Item("music", ln, group_id))

    n_groups = group_id + 1
    last_music_index: dict[int, int] = {}
    for i, it in enumerate(items):
        if it.kind == "music" and it.group is not None:
            last_music_index[it.group] = i

    rebuilt: list[str] = []
    for i, it in enumerate(items):
        if it.kind != "music" or it.group is None:
            rebuilt.append(it.raw)
            continue
        raw = it.raw.rstrip()
        is_group_end = last_music_index.get(it.group) == i
        is_last_group = it.group == n_groups - 1
        if is_group_end and not is_last_group and not _PHRASE_SEP_TRAIL.search(raw):
            rebuilt.append(raw + " *")
        else:
            rebuilt.append(raw)
    return "\n".join(rebuilt) + "\n", notes


@dataclass(frozen=True)
class VsaNote:
    lyric: str
    pitch: Pitch
    duration: Duration
    scoped: bool
    syllabic: str = "single"
    ehm: str = "~"
    elm: str = "~"
    line: int = 0
    column: int = 0


def _line_column(text: str, offset: int) -> tuple[int, int]:
    offset = max(0, min(offset, len(text)))
    before = text[:offset]
    line = before.count("\n") + 1
    last_nl = before.rfind("\n")
    column = offset + 1 if last_nl < 0 else offset - last_nl
    return line, column


def parse_vsa_source(text: str) -> tuple[dict, Document]:
    """Frontmatter + AST. Frontmatter-sleutels (do/mode) worden strings."""
    meta, body, _offset = parse_vsa_frontmatter_with_body_offset(text)
    flat = {str(k): str(v) for k, v in meta.items()}
    return flat, Parser(body).parse()


def extract_stanza_notes(
    text: str,
    *,
    metadata: dict[str, str] | None = None,
) -> list[list[VsaNote]]:
    """Eén lijst noten per VSA-regel (frase).

    Lettergrepen die in VSA aan elkaar geplakt zijn (``{En_}gel``,
    ``pro{fe_}{\\ten_}``) vormen één woord → begin/middle/end voor streepjes.
    Spaties (en strofe-markers) breken het woord.
    """
    file_meta, body, body_offset = parse_vsa_frontmatter_with_body_offset(text)
    meta = {str(k): str(v) for k, v in file_meta.items()}
    if metadata:
        meta.update(metadata)
    document = Parser(body).parse()
    resolver = PitchResolver.from_metadata(meta)
    duration_model = meta.get("duration-model", "default")
    for node in document.nodes:
        if isinstance(node, PitchMarkerNode):
            resolver.apply_start_marker(node.ehm)
            break
    stanzas: list[list[VsaNote]] = []
    current: list[VsaNote] = []
    word: list[VsaNote] = []

    def loc(body_pos: int | None) -> tuple[int, int]:
        if body_pos is None:
            return 0, 0
        return _line_column(text, body_offset + body_pos)

    def flush_word() -> None:
        if not word:
            return
        current.extend(_with_word_syllabics(word))
        word.clear()

    def close_stanza() -> None:
        flush_word()
        if current:
            stanzas.append(list(current))
            current.clear()

    def append_punct(token: str) -> None:
        """Leesteken plakt aan de laatste lettergreep met tekst."""
        target = word if word else current
        for i in range(len(target) - 1, -1, -1):
            if target[i].lyric:
                target[i] = replace(target[i], lyric=target[i].lyric + token)
                return

    for node in document.nodes:
        if isinstance(node, PitchMarkerNode):
            continue
        if isinstance(node, PitchTransitionNode):
            resolver.apply_start_marker(node.to_ehm)
            continue
        if isinstance(node, TextNode):
            _consume_text(
                node.text,
                resolver=resolver,
                duration_model=duration_model,
                word=word,
                flush_word=flush_word,
                close_stanza=close_stanza,
                append_punct=append_punct,
                text_start=node.start,
                loc=loc,
            )
            continue
        if isinstance(node, ScopeNode):
            hm = node.height_modifier or ["~"]
            lm = node.length_modifier or ["~"]
            if len(hm) > 1 and len(lm) == 1:
                lm = lm * len(hm)
            if len(lm) > 1 and len(hm) == 1:
                hm = hm * len(lm)
            n_pos = len(hm)
            line, column = loc(node.start)
            for i, (ehm, elm) in enumerate(zip(hm, lm)):
                pitch = resolver.resolve_ehm(ehm)
                dur = elm_to_duration(elm, model=duration_model)
                lyric = node.text if i == 0 else ""
                syllabic = "single"
                if n_pos > 1:
                    if i == 0:
                        syllabic = "begin"
                    elif i == n_pos - 1:
                        syllabic = "end"
                    else:
                        syllabic = "middle"
                word.append(
                    VsaNote(
                        lyric=lyric,
                        pitch=pitch,
                        duration=dur,
                        scoped=True,
                        syllabic=syllabic,
                        ehm=ehm,
                        elm=elm,
                        line=line,
                        column=column,
                    )
                )
            continue
    close_stanza()
    return stanzas


def _consume_text(
    text: str,
    *,
    resolver: PitchResolver,
    duration_model: str,
    word: list[VsaNote],
    flush_word,
    close_stanza,
    append_punct,
    text_start: int | None,
    loc,
) -> None:
    """Spaties breken woorden; tokens zonder voorafgaande spatie plakken aan het woord."""
    i = 0
    n = len(text)
    while i < n:
        if text[i].isspace():
            flush_word()
            i += 1
            continue
        j = i
        while j < n and not text[j].isspace():
            j += 1
        token = text[i:j]
        token_start = None if text_start is None else text_start + i
        i = j
        if token in _STANZA_MARKERS:
            flush_word()
            close_stanza()
            continue
        if token in _BARE_EHM_TOKENS:
            # Losse hoogtemarkering / barline (``//``, ``\``, …) — geen lyric.
            continue
        stripped = _strip_leading_ehm(token)
        if not stripped:
            continue
        if _PUNCT_ONLY_RE.match(stripped):
            append_punct(stripped)
            continue
        pitch = resolver.current_pitch
        dur = elm_to_duration("~", model=duration_model)
        line, column = loc(token_start)
        for lyric, _syllabic in recite_syllables(stripped):
            word.append(
                VsaNote(
                    lyric=lyric,
                    pitch=pitch,
                    duration=dur,
                    scoped=False,
                    line=line,
                    column=column,
                )
            )


def _strip_leading_ehm(token: str) -> str:
    """Haal een leidende kale EHM weg (``\\te`` → ``te``; ``//om`` → ``om``)."""
    for ehm in _BARE_EHM_SORTED:
        if token.startswith(ehm):
            return token[len(ehm) :]
    return token


def _with_word_syllabics(notes: list[VsaNote]) -> list[VsaNote]:
    """Zet begin/middle/end op lettergrepen mét tekst binnen één woord."""
    lyric_idxs = [i for i, note in enumerate(notes) if note.lyric]
    if len(lyric_idxs) <= 1:
        return list(notes)
    out = list(notes)
    n_lyric = len(lyric_idxs)
    for rank, idx in enumerate(lyric_idxs):
        if rank == 0:
            syl = "begin"
        elif rank == n_lyric - 1:
            syl = "end"
        else:
            syl = "middle"
        out[idx] = replace(out[idx], syllabic=syl)
    return out
