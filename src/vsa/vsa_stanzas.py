"""VSA-tekst → noten per tekstregel (`*` / `**` als frasegrens)."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .ast import Document, PitchMarkerNode, ScopeNode, TextNode
from .bracket_directive import VALID_EHM_VALUES
from .dutch_syllables import recite_syllables
from .duration_model import elm_to_duration
from .music import Duration, Pitch
from .musicxml_renderer import _PUNCT_ONLY_RE
from .parser import Parser
from .pitch_resolver import PitchResolver
from .yaml_frontmatter import parse_vsa_frontmatter_with_body_offset

_STANZA_MARKERS = frozenset({"*", "**"})
# Losse EHM/barline-tokens in platte tekst zijn geen gezongen woorden.
_BARE_EHM_TOKENS = frozenset(
    v for v in VALID_EHM_VALUES if v and all(ch in "/\\-~#♯+b♭" for ch in v)
)
_BARE_EHM_SORTED = sorted(_BARE_EHM_TOKENS, key=len, reverse=True)


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
