"""Structured mvsa parse with sticky directives (draft-v0).

Used by validate (sync) and MusicXML export. No blokhergebruik.
"""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from .mvsa_validate import (
    ALLOWED_DIRECTIVES,
    ALLOWED_MODES,
    ALLOWED_TALEN,
    ALLOWED_TAAL_ARGS,
    BLOK_ID_RE,
    DIRECTIVE_NAME_RE,
    DO_RE,
    HTML_COMMENT_RE,
    OCT_ASSIGN_RE,
    SECTIE_ID_RE,
    STICKY_DIRECTIVES,
    STRING_META_DIRECTIVES,
    TAAL_ASSIGN_RE,
    TEMPO_RE,
    MvsaDiagnostic,
    _BarSplit,
    _ELMS,
    _split_bars,
    _validate_directive_value,
    is_lyrics_stem,
    is_noop_separator_directive,
    looks_like_taal_assignments,
    normalize_directive_name,
    normalize_lyric_taal_key,
    parse_regelidentifier,
    parse_tekst_argument,
    resolve_stem_map_key,
    split_directive_assignments,
    stem_id_base,
)

DEGREE_NAMES = {
    "do": 0,
    "re": 1,
    "mi": 2,
    "fa": 3,
    "so": 4,
    "sol": 4,
    "la": 5,
    "si": 6,
    "ti": 6,
}

# Hoogte-tokens op stemregels (gedeeld door validate + MusicXML-export).
HEIGHT_DEGREE_RE = re.compile(
    r"^(#|b)?(do|re|mi|fa|sol|so|la|si|ti)"
    r"(?:([+-]\d*)(#|b)?|(#|b)([+-]\d*)?)?$",
    re.IGNORECASE,
)
HEIGHT_NOTE_RE = re.compile(
    r"^([a-gA-G])(bb|b|#)?(\d+)?([+-]\d*)?$",
)
HEIGHT_EHM_RE = re.compile(
    # Unidirectioneel: alleen /… of alleen \… (optioneel cijfer), of stay -/~.
    # Geen mix zoals \/ of /\ — dat is geen EHM.
    r"^[+#b♯♭]*(?:/+\d*|\\+\d*|[-~])$"
)
# ELM-duur op L; op stem alleen '-' / '~' (aanhouden), nooit '_' / '.' / …
_STEM_DURATION_ELMS = frozenset(e for e in _ELMS if e not in ("-", "~"))


def _is_syllable_char(c: str) -> bool:
    return c.isalpha() or c in "ëïöüáéíóúýčšžňĚĎŤ#№"


@dataclass
class StickyContext:
    do: str = "F4"
    mode: str = "major"
    oct: dict[str, int] = field(default_factory=dict)  # stem_id -> shift
    start: str | None = None  # raw @start rest
    # Passage-richting voor hulptekst: ``nl`` | ``ksl`` | None (auto).
    taal: str | None = None
    # Per lyrics-id → label (Coria) en/of richting ``nl``/``ksl``.
    taal_lyrics: dict[str, str] = field(default_factory=dict)

    def oct_for(self, marker: str) -> int:
        key = resolve_stem_map_key(self.oct, marker)
        return self.oct[key] if key is not None else 0

    def taal_for(self, marker: str) -> str | None:
        """Label/richting voor lyrics-marker; ``L``/``lyrics`` valt terug op sticky ``taal``."""
        key = normalize_lyric_taal_key(marker)
        found = resolve_stem_map_key(self.taal_lyrics, key)
        if found is not None:
            return self.taal_lyrics[found]
        if key.lower() in {"l", "lyrics"} or stem_id_base(key).lower() == "l":
            return self.taal
        return None


@dataclass
class LPosition:
    """One lengte-positie on a lyrics line."""

    recite: bool
    syllables: list[str]  # syllable texts (punct may be attached)
    elms: list[str]  # one ELM per slot; default "~" if implicit
    # For each syllable after the first: True = hyphen (same word), False = space (new word)
    links: list[bool] = field(default_factory=list)
    # Parallel to links: True = hard orthographic hyphen (bron ``=``), False = soft ``-``
    hard_links: list[bool] = field(default_factory=list)
    # True if this position continues a word started in the previous L-stuk (leading '-' / '=')
    continues_word: bool = False
    # True if that continuation was a hard ``=`` (not soft ``-``)
    continues_word_hard: bool = False


def _is_woordstreepje(c: str) -> bool:
    """Zacht ``-`` of hard ``=`` vóór de volgende lettergreep."""
    return c in "-="


def _woordstreepje_is_hard(c: str) -> bool:
    return c == "="


@dataclass
class VoicePosition:
    """One lengte-positie on a stem line."""

    slots: list[str]  # pitch tokens per &-slot (may be "-" hold)


@dataclass
class MeasureBundle:
    """Aligned content for one measure across LSATB markers."""

    lyrics: dict[str, list[LPosition]]  # marker -> positions
    voices: dict[str, list[VoicePosition]]
    final_bar: str  # bare bar token
    # stem_id -> eindanker glued to this measure's bar (None = kale streep)
    bar_anchors: dict[str, str | None] = field(default_factory=dict)
    # Linker streep van deze maat (bv. leidende ``|:`` zonder lege voorafgaande maat)
    start_bar: str | None = None


@dataclass
class ParsedSystem:
    start_line: int
    markers: list[str]
    lines: dict[str, str]  # marker -> raw content
    line_nos: dict[str, int]
    ends_section: bool
    context: StickyContext
    measures: list[MeasureBundle] = field(default_factory=list)
    line_ehms: dict[str, str | None] = field(default_factory=dict)
    identities: list[str] = field(default_factory=list)
    # ``@tekst``-waarden die direct vóór dit systeem stonden (volgorde behouden).
    staff_texts: list[str] = field(default_factory=list)
    # ``@mscz-newline`` vóór dit systeem → MuseScore new-system bij MSCZ-export.
    mscz_newline: bool = False


@dataclass
class ParsedSection:
    id: str | None
    start_line: int
    systems: list[ParsedSystem] = field(default_factory=list)
    # ``blok`` | ``sectie`` | None (anonieme sectie)
    origin: str | None = None


@dataclass
class ParsedDocument:
    sections: list[ParsedSection]
    diagnostics: list[MvsaDiagnostic]
    title: str | None = None
    composer: str | None = None
    copyright: str | None = None
    bron: str | None = None
    ondertitel: str | None = None
    tekstdichter: str | None = None
    arrangeur: str | None = None
    vertaler: str | None = None
    tempo: int | None = None
    # Gereserveerd (nog niet in export).
    toon: str | None = None
    taal: str | None = None
    genre: str | None = None
    opmerkingen: str | None = None
    speelplan: list[str] | None = None
    speelplan_line: int | None = None


def parse_mvsa(text: str) -> ParsedDocument:
    """Parse structure + sticky context + per-measure L/voice tokens."""
    diagnostics: list[MvsaDiagnostic] = []
    if text.startswith("\ufeff"):
        text = text[1:]
    cleaned = HTML_COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    lines = cleaned.splitlines()

    sections: list[ParsedSection] = []
    current: ParsedSection | None = None
    # (id, line, origin) — origin is ``blok`` | ``sectie``
    pending_sectie: tuple[str, int, str] | None = None
    pending_staff_texts: list[tuple[str, int]] = []  # (text, line_no)
    pending_mscz_newline: list[int] = []  # line numbers
    doc_meta: dict[str, str] = {}
    speelplan: list[str] | None = None
    speelplan_line: int | None = None
    ctx = StickyContext()
    i = 0
    n = len(lines)

    while i < n:
        stripped = lines[i].strip()
        line_no = i + 1

        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        if stripped.startswith("@"):
            name, _, rest = stripped[1:].partition(" ")
            name = normalize_directive_name(name.strip())
            rest = rest.strip()
            if is_noop_separator_directive(name, rest):
                pass  # optionele no-op; lege regel scheidt systemen al
            elif not name or not DIRECTIVE_NAME_RE.fullmatch(name):
                diagnostics.append(
                    MvsaDiagnostic(
                        "MVSA-DIRECTIVE",
                        f"ongeldige @-keyword {name!r} "
                        f"(verwacht [A-Za-z][A-Za-z-_]* of @---)",
                        line_no,
                        severity="warning",
                    )
                )
            elif name == "sectie":
                if not rest or not SECTIE_ID_RE.match(rest):
                    diagnostics.append(
                        MvsaDiagnostic(
                            "MVSA-SECTIE-ID",
                            f"ongeldige @sectie-id {rest!r}",
                            line_no,
                        )
                    )
                else:
                    # Nieuwe @sectie: laatste maatstreep van vorige sectie
                    # (ook |) is sectie-einde; geen MVSA-SECTIE-IMPLICIT.
                    pending_sectie = (rest, line_no, "sectie")
                    current = None
            elif name == "blok":
                if not rest or not BLOK_ID_RE.match(rest):
                    diagnostics.append(
                        MvsaDiagnostic(
                            "MVSA-BLOK-ID",
                            f"ongeldige @blok-id {rest!r} "
                            f"(verwacht [1-9][0-9]* of [a-z][a-z0-9_-]*)",
                            line_no,
                        )
                    )
                else:
                    # Speelblok ≠ sectie: geen ||-eis tussen @blok's (Coria-pauze).
                    pending_sectie = (rest, line_no, "blok")
                    current = None
            elif name == "speelplan":
                from .mvsa_speelplan import parse_speelplan_argument

                ids, err = parse_speelplan_argument(rest)
                if err:
                    diagnostics.append(
                        MvsaDiagnostic(
                            "MVSA-SPEELPLAN-SYNTAX",
                            f"ongeldig @speelplan: {err}",
                            line_no,
                        )
                    )
                elif speelplan is not None:
                    diagnostics.append(
                        MvsaDiagnostic(
                            "MVSA-SPEELPLAN-MULTI",
                            "meer dan één @speelplan in dit bestand",
                            line_no,
                        )
                    )
                else:
                    speelplan = ids
                    speelplan_line = line_no
            elif name in ALLOWED_DIRECTIVES:
                _validate_directive_value(name, rest, line_no, diagnostics)
                if name == "taal":
                    # Sticky: ``@taal nl|ksl|auto`` of ``@taal L=nl L1=ksl``.
                    # Quoted: document-meta (en sticky als de string ``nl``/``ksl`` is).
                    if rest in ALLOWED_TAAL_ARGS or looks_like_taal_assignments(
                        rest
                    ):
                        _apply_directive(ctx, name, rest)
                    else:
                        value = parse_tekst_argument(rest)
                        if value is not None:
                            doc_meta["taal"] = value
                            if value in ALLOWED_TALEN:
                                ctx.taal = value
                                ctx.taal_lyrics["L"] = value
                elif name in STICKY_DIRECTIVES:
                    _apply_directive(ctx, name, rest)
                elif name == "tekst":
                    value = parse_tekst_argument(rest)
                    if value is not None:
                        pending_staff_texts.append((value, line_no))
                elif name == "mscz-newline":
                    if not rest:
                        pending_mscz_newline.append(line_no)
                elif name == "tempo":
                    if rest and TEMPO_RE.fullmatch(rest):
                        doc_meta["tempo"] = rest
                elif name in STRING_META_DIRECTIVES:
                    value = parse_tekst_argument(rest)
                    if value is not None:
                        doc_meta[name] = value
            else:
                diagnostics.append(
                    MvsaDiagnostic(
                        "MVSA-DIRECTIVE",
                        f"onbekende @-keyword @{name} (experimenteel; "
                        f"nog niet in de specificatie)",
                        line_no,
                        severity="warning",
                    )
                )
            i += 1
            continue

        if not parse_regelidentifier(stripped):
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-LINE",
                    f"regel hoort commentaar, directive of regelidentifier te zijn: {stripped[:40]!r}",
                    line_no,
                )
            )
            i += 1
            continue

        system_lines: list[tuple[int, str, str, str | None, bool, str]] = []
        while i < n:
            s2 = lines[i].strip()
            # Lege regel = einde van dit LSATB-systeem (scheidt vscode-systemen).
            if not s2:
                break
            # #-commentaar mag tussen markers van hetzelfde systeem.
            if s2.startswith("#"):
                i += 1
                continue
            if s2.startswith("@"):
                break
            rid = parse_regelidentifier(s2)
            if not rid:
                break
            if rid.is_lyrics and rid.ehm is not None:
                diagnostics.append(
                    MvsaDiagnostic(
                        "MVSA-EHM-L",
                        f"lyrics-regelidentifier mag geen EHM bevatten: {rid.prefix!r}",
                        i + 1,
                    )
                )
            content = s2[rid.match_end :].lstrip()
            system_lines.append(
                (i + 1, rid.stem_id, content, rid.ehm, rid.is_lyrics, rid.identity)
            )
            i += 1

        if not system_lines:
            i += 1
            continue

        markers = [m for _, m, _, _, _, _ in system_lines]
        identities = [ident for *_, ident in system_lines]
        if len(markers) != len(set(markers)):
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-MARKER-DUP",
                    f"dubbele stemidentifier in LSATB-systeem: {markers}",
                    system_lines[0][0],
                )
            )

        line_map = {m: c for _, m, c, _, _, _ in system_lines}
        line_nos = {m: ln for ln, m, _, _, _, _ in system_lines}
        line_ehms = {m: ehm for _, m, _, ehm, _, _ in system_lines}
        ends, final_bars = _ends_section(system_lines, diagnostics)

        system = ParsedSystem(
            start_line=system_lines[0][0],
            markers=markers,
            lines=line_map,
            line_nos=line_nos,
            ends_section=ends,
            context=deepcopy(ctx),
            line_ehms=line_ehms,
            identities=identities,
            staff_texts=[t for t, _ in pending_staff_texts],
            mscz_newline=bool(pending_mscz_newline),
        )
        pending_staff_texts.clear()
        pending_mscz_newline.clear()
        system.measures = _build_measures(system, diagnostics)

        if current is None:
            if pending_sectie:
                sid, start, origin = pending_sectie
            else:
                sid, start, origin = None, system.start_line, None
            current = ParsedSection(id=sid, start_line=start, origin=origin)
            sections.append(current)
            pending_sectie = None
        elif pending_sectie is not None:
            sid, start, origin = pending_sectie
            current = ParsedSection(id=sid, start_line=start, origin=origin)
            sections.append(current)
            pending_sectie = None

        current.systems.append(system)
        if ends:
            current = None

    if pending_sectie is not None:
        sid, start, origin = pending_sectie
        label = "@blok" if origin == "blok" else "@sectie"
        diagnostics.append(
            MvsaDiagnostic(
                "MVSA-BLOK-EMPTY" if origin == "blok" else "MVSA-SECTIE-EMPTY",
                f"{label} {sid!r} zonder LSATB-systeem",
                start,
            )
        )
    for _, tekst_line in pending_staff_texts:
        diagnostics.append(
            MvsaDiagnostic(
                "MVSA-TEKST",
                "@tekst zonder volgend LSATB-systeem",
                tekst_line,
                severity="warning",
            )
        )
    for nl_line in pending_mscz_newline:
        diagnostics.append(
            MvsaDiagnostic(
                "MVSA-MSCZ-NEWLINE",
                "@mscz-newline zonder volgend LSATB-systeem",
                nl_line,
                severity="warning",
            )
        )
    # EOF (en later fence-:::): open sectie eindigt op de laatste maatstreep
    # van het laatste systeem (| of ||); geen MVSA-SECTIE-IMPLICIT.

    _validate_sync(sections, diagnostics)
    doc = ParsedDocument(
        sections=sections,
        diagnostics=diagnostics,
        title=doc_meta.get("title"),
        composer=doc_meta.get("composer"),
        copyright=doc_meta.get("copyright"),
        bron=doc_meta.get("bron"),
        ondertitel=doc_meta.get("ondertitel"),
        tekstdichter=doc_meta.get("tekstdichter"),
        arrangeur=doc_meta.get("arrangeur"),
        vertaler=doc_meta.get("vertaler"),
        tempo=int(doc_meta["tempo"]) if "tempo" in doc_meta else None,
        toon=doc_meta.get("toon"),
        taal=doc_meta.get("taal"),
        genre=doc_meta.get("genre"),
        opmerkingen=doc_meta.get("opmerkingen"),
        speelplan=speelplan,
        speelplan_line=speelplan_line,
    )
    from .mvsa_bar_anchors import collect_bar_anchor_diagnostics
    from .mvsa_speelplan import collect_speelplan_diagnostics

    diagnostics.extend(collect_bar_anchor_diagnostics(doc))
    diagnostics.extend(collect_speelplan_diagnostics(doc))
    return doc


def _apply_directive(ctx: StickyContext, name: str, rest: str) -> None:
    if name == "do" and rest and DO_RE.match(rest):
        ctx.do = rest[0].upper() + rest[1:]
    elif name == "mode" and rest in ALLOWED_MODES:
        ctx.mode = rest
    elif name == "oct" and rest:
        for part in split_directive_assignments(rest):
            m = OCT_ASSIGN_RE.match(part)
            if m:
                ctx.oct[m.group(1)] = int(m.group(2))
    elif name == "start":
        ctx.start = rest or None
    elif name == "taal":
        if rest == "auto":
            ctx.taal = None
            ctx.taal_lyrics.pop("L", None)
        elif rest in ALLOWED_TALEN:
            ctx.taal = rest
            ctx.taal_lyrics["L"] = rest
        elif looks_like_taal_assignments(rest):
            for part in split_directive_assignments(rest):
                m = TAAL_ASSIGN_RE.match(part)
                if not m:
                    continue
                key = normalize_lyric_taal_key(m.group(1))
                value = m.group(2)
                if not is_lyrics_stem(key):
                    continue
                ctx.taal_lyrics[key] = value
                # Eerste lyrics-laag / ``L``: ook sticky richting als nl|ksl.
                if key.lower() in {"l", "lyrics"} and value.lower() in ALLOWED_TALEN:
                    ctx.taal = value.lower()
                elif (
                    not any(k.lower() in {"l", "lyrics"} for k in ctx.taal_lyrics)
                    and value.lower() in ALLOWED_TALEN
                    and ctx.taal is None
                ):
                    # Alleen lyrics-ids zoals Lap: eerste nl|ksl-waarde → sticky.
                    ctx.taal = value.lower()



def _ends_section(
    system_lines: list[tuple], diagnostics: list[MvsaDiagnostic]
) -> tuple[bool, list[str | None]]:
    endings: list[str | None] = []
    for item in system_lines:
        line_no, marker, content = item[0], item[1], item[2]
        bars = _split_bars(content)
        if not bars.bar_tokens:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-BAR",
                    f"{marker}: regel eindigt niet op een maat-/sectiestreep",
                    line_no,
                )
            )
            endings.append(None)
            continue
        if bars.trailing_text:
            diagnostics.append(
                MvsaDiagnostic(
                    "MVSA-BAR",
                    f"{marker}: tekst na laatste maatstreep: {bars.trailing_text!r}",
                    line_no,
                )
            )
        endings.append(bars.final_bar)
    if not endings or any(e is None for e in endings):
        return False, endings
    if len(set(endings)) != 1:
        diagnostics.append(
            MvsaDiagnostic(
                "MVSA-BAR-SYNC",
                f"LSATB-regels eindigen niet met dezelfde streep: {endings}",
                system_lines[0][0],
            )
        )
    final = endings[0]
    return final in ("||", ":||"), endings


def _build_measures(
    system: ParsedSystem, diagnostics: list[MvsaDiagnostic]
) -> list[MeasureBundle]:
    splits: dict[str, _BarSplit] = {
        m: _split_bars(content) for m, content in system.lines.items()
    }
    counts = {m: len(sp.bar_tokens) for m, sp in splits.items()}
    if len(set(counts.values())) != 1:
        diagnostics.append(
            MvsaDiagnostic(
                "MVSA-MEASURE-COUNT",
                f"ongelijk aantal maatstrepen in systeem: {counts}",
                system.start_line,
            )
        )
        return []

    n = next(iter(counts.values()))
    leadings = {m: sp.leading_bar for m, sp in splits.items()}
    if len(set(leadings.values())) != 1:
        diagnostics.append(
            MvsaDiagnostic(
                "MVSA-MEASURE-COUNT",
                f"ongelijke leidende maatstreep in systeem: {leadings}",
                system.start_line,
            )
        )
        return []
    leading_bar = next(iter(leadings.values()))
    bundles: list[MeasureBundle] = []
    for mi in range(n):
        lyrics: dict[str, list[LPosition]] = {}
        voices: dict[str, list[VoicePosition]] = {}
        final_bar = next(iter(splits.values())).bar_tokens[mi]
        anchors: dict[str, str | None] = {}
        for marker, sp in splits.items():
            seg = sp.segments[mi]
            if is_lyrics_stem(marker):
                lyrics[marker] = parse_l_positions(seg)
            else:
                voices[marker] = parse_voice_positions(seg)
            if mi < len(sp.bar_anchors):
                anchors[marker] = sp.bar_anchors[mi]
            else:
                anchors[marker] = None
        bundles.append(
            MeasureBundle(
                lyrics=lyrics,
                voices=voices,
                final_bar=final_bar,
                bar_anchors=anchors,
                start_bar=leading_bar if mi == 0 else None,
            )
        )
    return bundles


def _validate_sync(
    sections: list[ParsedSection], diagnostics: list[MvsaDiagnostic]
) -> None:
    for section in sections:
        if not section.systems:
            continue
        expected = section.systems[0].identities or section.systems[0].markers
        for system in section.systems:
            got = system.identities or system.markers
            if got != expected:
                diagnostics.append(
                    MvsaDiagnostic(
                        "MVSA-MARKERS",
                        f"regelidentifier-volgorde wijkt af: verwacht {expected}, kreeg {got}",
                        system.start_line,
                    )
                )
            if not system.measures:
                continue
            # Prefer primary L as reference
            ref = next(
                (m for m in system.markers if is_lyrics_stem(m)),
                system.markers[0],
            )
            for mi, bundle in enumerate(system.measures):
                ref_slots = _slot_seq(bundle, ref)
                for marker in system.markers:
                    if marker == ref:
                        continue
                    other = _slot_seq(bundle, marker)
                    if other != ref_slots:
                        diagnostics.append(
                            MvsaDiagnostic(
                                "MVSA-SYNC",
                                f"maat {mi + 1}: {marker} slots {other} ≠ {ref} slots {ref_slots}",
                                system.line_nos.get(marker, system.start_line),
                            )
                        )
                _validate_voice_height_tokens(system, mi, bundle, diagnostics)


def _validate_voice_height_tokens(
    system: ParsedSystem,
    measure_index: int,
    bundle: MeasureBundle,
    diagnostics: list[MvsaDiagnostic],
) -> None:
    for marker, positions in bundle.voices.items():
        line_no = system.line_nos.get(marker, system.start_line)
        for pi, vpos in enumerate(positions):
            for si, slot in enumerate(vpos.slots):
                if is_valid_height_slot(slot):
                    continue
                diagnostics.append(
                    MvsaDiagnostic(
                        "MVSA-HOOGTE",
                        f"{marker}: onbekende hoogte-token {slot!r} "
                        f"(maat {measure_index + 1}, positie {pi + 1}, slot {si + 1})",
                        line_no,
                    )
                )


def is_valid_height_slot(token: str) -> bool:
    """True if ``token`` is a stem height slot (EHM, absolute, hold), not an L-ELM."""
    tok = token.strip()
    if not tok:
        return False
    if tok in ("-", "~"):
        return True
    if tok in _STEM_DURATION_ELMS:
        return False
    if HEIGHT_NOTE_RE.fullmatch(tok) and not HEIGHT_DEGREE_RE.fullmatch(tok):
        return True
    if HEIGHT_DEGREE_RE.fullmatch(tok):
        return True
    if HEIGHT_EHM_RE.fullmatch(tok):
        return True
    try:
        from .pitch_resolver import parse_pitch_string

        candidate = tok[0].upper() + tok[1:] if tok[0].islower() else tok
        parse_pitch_string(candidate)
        return True
    except ValueError:
        return False


def _slot_seq(bundle: MeasureBundle, marker: str) -> list[int]:
    if marker in bundle.lyrics:
        return [max(1, len(p.elms)) for p in bundle.lyrics[marker]]
    if marker in bundle.voices:
        return [max(1, len(p.slots)) for p in bundle.voices[marker]]
    return []


# ---------------------------------------------------------------------------
# L / voice tokenizers
# ---------------------------------------------------------------------------


def parse_voice_positions(measure: str) -> list[VoicePosition]:
    out: list[VoicePosition] = []
    for token in measure.split():
        if not token:
            continue
        # Strip trailing ELMs glued to pitch (intocht: a4_, g4__)
        core = _strip_trailing_elms(token)
        parts = core.split("&") if core else token.split("&")
        # If whole token was ELM-only after strip failure, keep raw split
        if not parts or parts == [""]:
            parts = token.split("&")
        out.append(VoicePosition(slots=[p for p in parts if p != ""]))
    return out


def _strip_trailing_elms(token: str) -> str:
    """Remove trailing ELM suffixes from a pitch token (``a4_``, ``si-__``)."""
    # Melisma tokens: strip ELM only from the last slot piece after &
    if "&" in token:
        head, _, last = token.rpartition("&")
        return f"{head}&{_strip_trailing_elms(last)}" if head else _strip_one(token)
    return _strip_one(token)


def _strip_one(token: str) -> str:
    s = token
    while s:
        matched = False
        for e in _ELMS:
            if s.endswith(e) and len(s) > len(e):
                # EHM ``+-`` / ``#-`` / ``b-``: trailing ``-``/``~`` is stay, not
                # ELM-duur (anders blijft alleen ``+``/``#`` over → validate-fout).
                if e in ("-", "~") and HEIGHT_EHM_RE.fullmatch(s):
                    break
                # Don't strip octave suffix "-" from degrees/names: ``si-``, ``g-``
                # ELM "-" at end of ``si-`` is ambiguous; prefer pitch+oct over ELM
                # when remainder looks like a pitch. Strip ``_`` ``__`` ``_.`` etc.
                if e == "-" and _looks_like_pitch_prefix(s[: -len(e)]):
                    break
                if e == "~" and _looks_like_pitch_prefix(s[: -len(e)]):
                    break
                s = s[: -len(e)]
                matched = True
                break
        if not matched:
            break
    return s or token


def _looks_like_pitch_prefix(s: str) -> bool:
    if not s:
        return False
    low = s.lower()
    for name in DEGREE_NAMES:
        if low == name or low.startswith(name):
            return True
    if re.match(r"^[a-gA-G](#|b|bb)?\d*$", s):
        return True
    return False


def parse_l_positions(measure: str) -> list[LPosition]:
    """Parse L measure into positions with syllables + ELMs.

    Reciteertoon: ``( … )`` met optionele ELM direct na ``)``. Binnen de
    haakjes scheiden spaties woorden en ``-`` lettergrepen. Zonder ELM na
    ``)`` is de duur de recite-standaard (export: breve). ``~`` op L is alleen
    nog ELM-duur, nooit recite-marker.
    """
    s = measure.strip()
    if not s:
        return []
    positions: list[LPosition] = []
    i = 0
    n = len(s)

    while i < n:
        if s[i].isspace():
            i += 1
            continue
        if s[i] in ",;:!?":
            i += 1
            continue
        if s[i] == ".":
            is_elm_dot = any(
                s.startswith(e, i) and e in (".", "..", "_.", "-.", "~.") for e in _ELMS
            )
            if not is_elm_dot:
                i += 1
                continue

        if s[i] == "(":
            close = s.find(")", i + 1)
            if close < 0:
                close = n
            interior = s[i + 1 : close]
            i = close + 1 if close < n and s[close] == ")" else n
            syllables, links, hard_links = _parse_recite_interior(interior)
            # After ')': duration ELMs only — bare '-' is woordstreepje, not ELM.
            elm_list, i = _read_elms(s, i, allow_bare_dash=False)
            positions.append(
                LPosition(
                    recite=True,
                    syllables=syllables,
                    elms=elm_list,
                    links=links,
                    hard_links=hard_links,
                    continues_word=False,
                )
            )
            continue

        # Stray woordstreepje (not before a letter): skip
        if _is_woordstreepje(s[i]) and not (
            i + 1 < n and _is_syllable_char(s[i + 1])
        ):
            i += 1
            continue

        continues_word = False
        continues_word_hard = False
        if _is_woordstreepje(s[i]) and i + 1 < n and _is_syllable_char(s[i + 1]):
            continues_word = True
            continues_word_hard = _woordstreepje_is_hard(s[i])
            i += 1

        # Leading ELM vóór de lettergreep (bijv. ``~Al``, ``_Geest``).
        progress_at = i
        leading_elms, i = _read_elms(s, i)

        syllables: list[str] = []
        links: list[bool] = []
        hard_links: list[bool] = []
        elms: list[str] = []
        pending_link: bool | None = None
        pending_hard: bool = False
        used_leading = False

        while True:
            if i >= n:
                break

            start = i
            while i < n and (_is_syllable_char(s[i]) or s[i] in "'’ʹ"):
                i += 1
            syll = s[start:i]
            if not syll:
                break
            while i < n and s[i] in ",;:!?":
                syll += s[i]
                i += 1

            piece_elms, i = _read_elms(s, i)

            if syllables:
                links.append(True if pending_link is None else pending_link)
                hard_links.append(
                    pending_hard if pending_link is not False else False
                )
            syllables.append(syll)
            pending_link = None
            pending_hard = False

            if piece_elms:
                elms.extend(piece_elms)
            elif not used_leading and leading_elms:
                elms.extend(leading_elms)
                used_leading = True
            else:
                elms.append("~")

            while i < n and s[i] in ",;:!?":
                syllables[-1] += s[i]
                i += 1

            if (
                i < n
                and _is_woordstreepje(s[i])
                and i + 1 < n
                and _is_syllable_char(s[i + 1])
            ):
                pending_hard = _woordstreepje_is_hard(s[i])
                i += 1
                pending_link = True
                positions.append(
                    LPosition(
                        recite=False,
                        syllables=syllables,
                        elms=elms if elms else ["~"],
                        links=links,
                        hard_links=hard_links,
                        continues_word=continues_word,
                        continues_word_hard=continues_word_hard,
                    )
                )
                syllables = []
                links = []
                hard_links = []
                elms = []
                continues_word = True
                continues_word_hard = pending_hard
                continue

            break

        if elms or syllables:
            if not elms:
                elms = ["~"]
            positions.append(
                LPosition(
                    recite=False,
                    syllables=syllables,
                    elms=elms,
                    links=links,
                    hard_links=hard_links,
                    continues_word=continues_word,
                    continues_word_hard=continues_word_hard,
                )
            )
        elif i == progress_at:
            # Onverwacht teken (geen ELM, geen lettergreep): voorkom oneindige lus.
            i += 1

    return positions


def _parse_recite_interior(
    interior: str,
) -> tuple[list[str], list[bool], list[bool]]:
    """Syllables + links inside ``( … )`` (space = word, ``-``/``=`` = hyphen)."""
    s = interior.strip()
    if not s:
        return [], [], []
    syllables: list[str] = []
    links: list[bool] = []
    hard_links: list[bool] = []
    i = 0
    n = len(s)
    pending_link: bool | None = None
    pending_hard = False
    while i < n:
        if s[i].isspace():
            if syllables:
                pending_link = False
                pending_hard = False
            i += 1
            continue
        if _is_woordstreepje(s[i]) and i + 1 < n and _is_syllable_char(s[i + 1]):
            pending_link = True
            pending_hard = _woordstreepje_is_hard(s[i])
            i += 1
            continue
        if s[i] in ",;:!?" and not syllables:
            i += 1
            continue
        start = i
        while i < n and (_is_syllable_char(s[i]) or s[i] in "'’ʹ"):
            i += 1
        syll = s[start:i]
        if not syll:
            i += 1
            continue
        while i < n and s[i] in ",;:!?":
            syll += s[i]
            i += 1
        if syllables:
            link = True if pending_link is None else pending_link
            links.append(link)
            hard_links.append(pending_hard if link else False)
        syllables.append(syll)
        pending_link = None
        pending_hard = False
        if (
            i < n
            and _is_woordstreepje(s[i])
            and i + 1 < n
            and _is_syllable_char(s[i + 1])
        ):
            pending_link = True
            pending_hard = _woordstreepje_is_hard(s[i])
            i += 1
    return syllables, links, hard_links


def _read_elms(
    s: str, i: int, *, allow_bare_dash: bool = True
) -> tuple[list[str], int]:
    """Read one melisma-chain of ELMs at ``i``; return (elms, new_index).

    After a recite ``)``, pass ``allow_bare_dash=False`` so ``)-lu`` is a
    woordstreepje (not ELM ``-``). Meaningful durations use ``_``, ``~``,
    ``.``, ``-.``, …
    """
    n = len(s)
    piece_elms: list[str] = []
    while True:
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
        i += len(elm)
        piece_elms.append(elm)
        if i < n and s[i] == "&":
            i += 1
            continue
        break
    return piece_elms, i
