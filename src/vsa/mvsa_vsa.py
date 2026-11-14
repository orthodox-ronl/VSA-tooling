"""MVSA → VSA extractie (contract E1–E6).

Default: stem ``S`` → sibling ``{bron}.mvsa.vsa``. Elke maat = één strofe.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .derived_path import derived_output_path
from .mvsa_musicxml import _resolve_slot, writing_do_pitch
from .mvsa_parse import (
    LPosition,
    MeasureBundle,
    ParsedDocument,
    ParsedSystem,
    VoicePosition,
    parse_mvsa,
)
from .mvsa_validate import is_lyrics_stem, resolve_stem_map_key
from .music import Pitch
from .pitch_resolver import PitchResolver, pitch_to_degree_and_chrom
from .atomic_io import write_text
from .text_export import plain_text_from_mvsa
from .zoektekst import (
    LiteralZoektekst,
    _ZoektekstDumper,
    expected_zoektekst,
    format_zoektekst,
)


class MvsaVsaError(ValueError):
    """Conversiefout MVSA → VSA (leesbare Nederlandse melding)."""

    def __init__(self, message: str, *, hint: str | None = None):
        super().__init__(message)
        self.message_nl = message
        self.hint = hint


def default_mvsa_vsa_output(
    source: Path | str,
    *,
    voice_label: str | None = None,
) -> Path:
    """Sibling-pad volgens E2.

    - Zonder ``voice_label`` (één stem, default of ``--voice x``):
      ``lied.mvsa.vsa``.
    - Met ``voice_label`` (alleen bij ``--voice all``): ``lied.mvsa.x.vsa``
      (stem-id lowercase).
    """
    src = Path(source)
    if voice_label is None:
        return derived_output_path(src, ".vsa")
    stem = voice_label.strip().lower()
    if not stem:
        return derived_output_path(src, ".vsa")
    return src.with_name(f"{src.name}.{stem}.vsa")


def degree_delta_to_ehm(
    steps: int, chrom: float = 0.0, *, stacked: bool = False
) -> str:
    """Encode ladder-stappen (+ chromatische prefix) als EHM-string.

    ``stacked=True``: alleen ``/``/``\\``-stapels (geen ``/4``) — nodig in
    openingsmarkers die de VSA-parser niet als ``#/4`` accepteert.
    """
    prefix = ""
    if chrom >= 0.5:
        prefix = "#"
    elif chrom <= -0.5:
        prefix = "b"
    if steps == 0:
        return f"{prefix}-" if prefix else "-"
    abs_s = abs(steps)
    slash = "/" if steps > 0 else "\\"
    if abs_s == 1:
        body = slash
    elif abs_s == 2 or stacked or abs_s <= 4:
        body = slash * abs_s
    else:
        body = f"{slash}{abs_s}"
    return prefix + body


def start_marker_for_degree(degree: int, chrom: float = 0.0) -> str:
    """Openingsmarker ``[…:]`` voor absolute ladderpositie t.o.v. schrijf-do."""
    ehm = degree_delta_to_ehm(degree, chrom, stacked=True)
    if ehm in ("-", "~"):
        return "[:]"
    return f"[{ehm}:]"


def _pick_lyrics_marker(system: ParsedSystem) -> str | None:
    for m in system.markers:
        if is_lyrics_stem(m):
            return m
    for m in system.markers:
        if m.upper().startswith("L"):
            return m
    return None


def _resolve_voice_marker(system: ParsedSystem, voice: str) -> str | None:
    want = voice.strip()
    if not want:
        return None
    markers = [m for m in system.markers if not is_lyrics_stem(m)]
    mapping = {m: m for m in markers}
    found = resolve_stem_map_key(mapping, want)
    if found is not None:
        return found
    lower = {m.lower(): m for m in markers}
    return lower.get(want.lower())


def _list_voice_markers(doc: ParsedDocument) -> list[str]:
    seen: list[str] = []
    for section in doc.sections:
        for system in section.systems:
            for m in system.markers:
                if is_lyrics_stem(m):
                    continue
                if m not in seen:
                    seen.append(m)
    return seen


def _normalize_elm_token(elm: str) -> list[str]:
    """Split odd combos (``-.``) and drop empty."""
    if not elm:
        return []
    if elm == "-.":
        # Hyphen-residue + stippeltje → alleen duur ``.``
        return ["."]
    return [elm]


def _normalized_elms(elms: list[str]) -> list[str]:
    """Normaliseer ELM-tokens (o.a. ``-.`` → ``.``); behoud ``~``."""
    out: list[str] = []
    for raw in elms:
        for e in _normalize_elm_token(raw):
            if e:
                out.append(e)
    return out


def _meaningful_elms(elms: list[str]) -> list[str]:
    """Duur-ELMs zonder default ``~`` (één toon / kale tekst)."""
    return [e for e in _normalized_elms(elms) if e != "~"]


def _format_lyric_with_elms(
    syl: str, elms: list[str], *, melisma: bool
) -> str:
    """Lettergreep + duurmarkering; bij melisma ELMs met ``&`` (E4).

    Eenstemmig: ``~`` weglaten. Melisma: ``~`` behouden wanneer er ook
    niet-default duuren zijn (anders mismatch hoogte/lengte, bijv.
    ``_&~`` → ``hoor_&~``). Uitsluitend-``~``-melisma → geen duurtekst
    (zoals ``ver~&~`` → ``ver`` bij ``{/&/ver}``).
    """
    text = (syl or "").strip()
    if melisma:
        chain = _normalized_elms(elms)
        if not chain or all(e == "~" for e in chain):
            return text
        body = chain[0] + "".join(f"&{e}" for e in chain[1:])
        return f"{text}{body}"
    cleaned = _meaningful_elms(elms)
    if not cleaned:
        return text
    # Eén toon: eerste betekenisvolle ELM (meestal ``_`` / ``.`` / ``-``).
    return f"{text}{cleaned[0]}"


def _scope(ehm_chain: str, text: str) -> str:
    if not text:
        return f"{{{ehm_chain}}}"
    return f"{{{ehm_chain}{text}}}"


def _lyric_has_duration_mark(text: str) -> bool:
    """True als de lyric-tekst een VSA-duurmarker bevat (``_``/``.``/``-``/``~``)."""
    if not text:
        return False
    # Duur zit achter de lettergreep; leesteken mag volgen (``Heer,_``).
    for i, ch in enumerate(text):
        if ch in "_~.":
            return True
        if ch == "-" and i > 0:
            # Soft hyphen in lettergreep ≠ duur-``-``; duur-``-`` komt na letters.
            # Echte duur-ELM ``-`` / ``-.`` staat typisch na de syllabe-kern.
            rest = text[i:]
            if rest == "-" or rest.startswith("-.") or rest.startswith("-&"):
                return True
    return False


@dataclass
class _NoteEvent:
    pitch: Pitch
    text: str
    continues_word: bool
    hard_link: bool


def _events_for_measure(
    bundle: MeasureBundle,
    *,
    lyrics_marker: str | None,
    voice_marker: str,
    resolver: PitchResolver,
    ctx,
    line_no: int,
) -> list[_NoteEvent]:
    lpos_list = (
        bundle.lyrics.get(lyrics_marker, []) if lyrics_marker else []
    )
    vpos_list = bundle.voices.get(voice_marker, [])
    n = max(len(lpos_list), len(vpos_list))
    events: list[_NoteEvent] = []
    last_pitch = resolver.current_pitch

    for i in range(n):
        lpos: LPosition | None = lpos_list[i] if i < len(lpos_list) else None
        vpos: VoicePosition | None = vpos_list[i] if i < len(vpos_list) else None
        slots = list(vpos.slots) if vpos else ["-"]
        pitches: list[Pitch] = []
        for slot in slots:
            p = _resolve_slot(
                slot,
                resolver,
                ctx,
                voice_marker[0] if voice_marker else "S",
                last_pitch=last_pitch,
                line=line_no,
                marker=voice_marker,
            )
            if p is None:
                continue
            pitches.append(p)
            last_pitch = p

        if not pitches:
            continue

        syllables = list(lpos.syllables) if lpos and lpos.syllables else [""]
        elms = list(lpos.elms) if lpos else []
        links = list(lpos.links) if lpos else []
        hard_links = list(lpos.hard_links) if lpos else []
        continues = bool(lpos.continues_word) if lpos else False
        continues_hard = bool(lpos.continues_word_hard) if lpos else False

        if len(syllables) == 1 and len(pitches) >= 1:
            melisma = len(pitches) > 1
            text = _format_lyric_with_elms(
                syllables[0], elms, melisma=melisma
            )
            events.append(
                _NoteEvent(
                    pitch=pitches[0],
                    text=text,
                    continues_word=continues,
                    hard_link=continues_hard,
                )
            )
            for extra in pitches[1:]:
                events.append(
                    _NoteEvent(
                        pitch=extra,
                        text="",
                        continues_word=True,
                        hard_link=False,
                    )
                )
            continue

        # Meerdere lettergrepen in één L-positie: zip met pitches.
        for si, syl in enumerate(syllables):
            pitch = pitches[min(si, len(pitches) - 1)]
            if len(syllables) == len(elms):
                syl_elms = [elms[si]]
            elif si == 0:
                syl_elms = elms
            else:
                syl_elms = [elms[si]] if si < len(elms) else []
            cont = continues if si == 0 else True
            hard = continues_hard if si == 0 else (
                hard_links[si - 1] if si - 1 < len(hard_links) else False
            )
            if si > 0 and si - 1 < len(links) and not links[si - 1]:
                cont = False
                hard = False
            events.append(
                _NoteEvent(
                    pitch=pitch,
                    text=_format_lyric_with_elms(
                        syl, syl_elms, melisma=False
                    ),
                    continues_word=cont,
                    hard_link=hard,
                )
            )
    return events


def _group_melisma(events: list[_NoteEvent]) -> list[list[_NoteEvent]]:
    """Groepeer melisma: lege tekst na een lettergreep hoort bij die lettergreep."""
    if not events:
        return []
    groups: list[list[_NoteEvent]] = []
    current: list[_NoteEvent] = [events[0]]
    for ev in events[1:]:
        if ev.text == "" and current:
            current.append(ev)
        else:
            groups.append(current)
            current = [ev]
    groups.append(current)
    return groups


def _melisma_ehm_chain(
    group: list[_NoteEvent],
    *,
    resolver_do: Pitch,
    intervals: list[int],
    prev_degree: int,
) -> tuple[str, int, float]:
    """EHM of EHM&EHM… voor één lettergreep (mogelijk melisma); eind-degree."""
    head = group[0]
    deg, ch = pitch_to_degree_and_chrom(resolver_do, head.pitch, intervals)
    chain = degree_delta_to_ehm(deg - prev_degree, ch)
    cursor = deg
    for extra in group[1:]:
        ed, ec = pitch_to_degree_and_chrom(resolver_do, extra.pitch, intervals)
        chain += "&" + degree_delta_to_ehm(ed - cursor, ec)
        cursor, ch = ed, ec
    return chain, cursor, ch


def _emit_phrase(
    groups: list[list[_NoteEvent]],
    *,
    resolver_do: Pitch,
    intervals: list[int],
    prev_degree: int | None,
    is_first_phrase: bool,
) -> tuple[str, int]:
    """Bouw één strofe-tekst; return (text, last_degree)."""
    tokens: list[str] = []
    degree = prev_degree

    for gi, group in enumerate(groups):
        head = group[0]
        deg0, ch0 = pitch_to_degree_and_chrom(
            resolver_do, head.pitch, intervals
        )

        if degree is None:
            # Openingsmarker + eerste lettergreep als kale tekst (E4).
            tokens.append(start_marker_for_degree(deg0, ch0))
            if head.text:
                tokens.append(" ")
                tokens.append(head.text)
            degree = deg0
            if len(group) > 1:
                cursor = deg0
                chain_bits: list[str] = []
                for extra in group[1:]:
                    ed, ec = pitch_to_degree_and_chrom(
                        resolver_do, extra.pitch, intervals
                    )
                    chain_bits.append(degree_delta_to_ehm(ed - cursor, ec))
                    cursor, ch0 = ed, ec
                if chain_bits:
                    if tokens and tokens[-1] == head.text:
                        tokens.pop()
                        if tokens and tokens[-1] == " ":
                            tokens.pop()
                    full = "-&" + "&".join(chain_bits)
                    tokens.append(" ")
                    tokens.append(_scope(full, head.text))
                degree = cursor
            continue

        chain, degree, _ch = _melisma_ehm_chain(
            group,
            resolver_do=resolver_do,
            intervals=intervals,
            prev_degree=degree,
        )
        # Zelfde toon zonder melisma → kale tekst (geen ``{-…}``, E4).
        # Wel scope als er een duur-ELM op de lettergreep staat (``{hoor_}``),
        # anders lekt ``_``/``.`` in zoektekst als kale ``hoor_``.
        if chain in ("-", "~") and len(group) == 1:
            if _lyric_has_duration_mark(head.text):
                piece = _scope("", head.text)
            else:
                piece = head.text
        else:
            piece = _scope(chain, head.text)
        if head.continues_word and tokens:
            # Soft lettergreepstreepje behouden (MVSA ``ge-bed`` → ``ge-bed``).
            # Geen brugstreepje vóór/na scopes (syllabificatie.md:
            # ``ver{/hoor}``, niet ``ver-{/hoor}``).
            if not head.hard_link:
                prev = tokens[-1]
                next_is_scope = piece.startswith("{")
                prev_is_scope = prev.endswith("}")
                if (
                    prev
                    and prev not in (" ",)
                    and not prev.endswith("-")
                    and not next_is_scope
                    and not prev_is_scope
                ):
                    tokens.append("-")
            tokens.append(piece)
        else:
            if tokens:
                tokens.append(" ")
            tokens.append(piece)

    body = "".join(tokens)
    while "  " in body:
        body = body.replace("  ", " ")
    _ = is_first_phrase  # openingsmarker zit al in tokens bij degree is None
    return body.strip(), degree if degree is not None else 0


def _title_from_comment_header(text: str) -> str | None:
    """Eerste ``# Titel``-regel (geen ``#maat`` / waarschuwing) als titel."""
    for raw in text.splitlines():
        s = raw.strip()
        if not s.startswith("#"):
            if s and not s.startswith("---"):
                break
            continue
        body = s.lstrip("#").strip()
        if not body:
            continue
        low = body.lower()
        if low.startswith("maat ") or low.startswith("maat\t"):
            continue
        if "waarschuwing" in low:
            continue
        if body.startswith("vsa-") or body.startswith("Imported:"):
            continue
        if set(body) <= {"#", "=", "-", " "}:
            continue
        return body
    return None


def _copy_useful_frontmatter(src: dict[str, Any]) -> dict[str, Any]:
    # zoektekst niet overnemen: altijd opnieuw uit de VSA-body (E5 / zoektekst.md).
    keep = (
        "titel",
        "taal",
        "soort",
        "toon",
        "formule",
        "partituur",
        "bron",
        "gelegenheid",
    )
    out: dict[str, Any] = {}
    for key in keep:
        if key not in src:
            continue
        val = src[key]
        if val is None or val == "" or val == {} or val == []:
            continue
        out[key] = val
    return out


_SOORT_NAME_PREFIXES = (
    "kondak",
    "tropaar",
    "stichier",
    "vers",
    "prokimen",
    "derde-antifoon",
    "eerste-antifoon",
    "tweede-antifoon",
)


def _soort_toon_from_source_name(source_name: str) -> dict[str, Any]:
    """Leid ``soort`` / ``toon`` af uit bestandsnaam (catalogus-conventie).

    Voorbeeld: ``stichier-heer-ik-roep-toon-1-groningen.mvsa`` →
    ``soort: stichier``, ``toon: 1``.
    """
    stem = Path(source_name).name
    for suf in (".mvsa", ".vsa", ".mscz", ".mxl"):
        if stem.lower().endswith(suf):
            stem = stem[: -len(suf)]
            break
    lower = stem.lower()
    out: dict[str, Any] = {}
    for prefix in _SOORT_NAME_PREFIXES:
        if lower == prefix or lower.startswith(prefix + "-"):
            out["soort"] = prefix
            break
    m = re.search(r"(?:^|-)toon-([1-8])(?:-|$)", lower)
    if m:
        out["toon"] = int(m.group(1))
    return out


def _dump_vsa_frontmatter(meta: dict[str, Any]) -> str:
    """YAML-kop met ``zoektekst: |-`` (literal) wanneer aanwezig."""
    dumped = yaml.dump(
        meta,
        Dumper=_ZoektekstDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=88,
    )
    if not dumped.endswith("\n"):
        dumped += "\n"
    return dumped


def convert_mvsa_to_vsa_text(
    text: str,
    *,
    source_name: str,
    voice: str = "S",
) -> str:
    """Converteer MVSA-brontekst → VSA-brontekst (E3–E5)."""
    doc = parse_mvsa(text)
    errors = [d for d in doc.diagnostics if d.severity == "error"]
    if errors:
        msg = "; ".join(f"regel {d.line}: {d.message}" for d in errors[:5])
        raise MvsaVsaError(
            f"MVSA is niet geldig genoeg om te converteren ({msg}).",
            hint="Repareer eerst met: mvsa validate",
        )

    voices = _list_voice_markers(doc)
    if not voices:
        raise MvsaVsaError(
            "Geen stemregels gevonden in de MVSA.",
            hint="Verwacht minstens één stem (bijv. S: …).",
        )

    voice_key = voice.strip() or "S"
    # Controleer dat de stem ergens voorkomt.
    probe = {m: m for m in voices}
    resolved = resolve_stem_map_key(probe, voice_key)
    if resolved is None:
        lower = {m.lower(): m for m in voices}
        resolved = lower.get(voice_key.lower())
    if resolved is None:
        raise MvsaVsaError(
            f"Stem {voice_key!r} komt niet voor in dit bestand.",
            hint=f"Beschikbare stemmen: {', '.join(voices)}",
        )
    voice_id = resolved

    phrases: list[str] = []
    prev_degree: int | None = None
    last_ctx = None
    carry_pitch: Pitch | None = None

    for section in doc.sections:
        for system in section.systems:
            lyrics_m = _pick_lyrics_marker(system)
            voice_m = _resolve_voice_marker(system, voice_id)
            if voice_m is None:
                continue
            ctx = system.context
            last_ctx = ctx
            resolver = PitchResolver.from_metadata(
                {
                    "do": str(writing_do_pitch(ctx, voice_m)),
                    "mode": ctx.mode,
                }
            )
            if carry_pitch is not None:
                resolver.set_absolute_pitch(carry_pitch)
            line_ehms = getattr(system, "line_ehms", {}) or {}
            if voice_m in line_ehms and line_ehms[voice_m]:
                from .mvsa_musicxml import _apply_line_ehm

                _apply_line_ehm(resolver, line_ehms[voice_m])
            schrijf_do = writing_do_pitch(ctx, voice_m)
            intervals = resolver._intervals
            line_no = system.line_nos.get(voice_m, system.start_line)

            for bundle in system.measures:
                events = _events_for_measure(
                    bundle,
                    lyrics_marker=lyrics_m,
                    voice_marker=voice_m,
                    resolver=resolver,
                    ctx=ctx,
                    line_no=line_no,
                )
                if not events:
                    continue
                groups = _group_melisma(events)
                is_first = not phrases
                phrase, prev_degree = _emit_phrase(
                    groups,
                    resolver_do=schrijf_do,
                    intervals=intervals,
                    prev_degree=prev_degree,
                    is_first_phrase=is_first,
                )
                if phrase:
                    phrases.append(phrase)
                carry_pitch = resolver.current_pitch

    if not phrases:
        raise MvsaVsaError(
            f"Geen maten met stem {voice_id!r} gevonden om te converteren."
        )

    body_parts: list[str] = []
    for i, phrase in enumerate(phrases):
        if i == 0:
            body_parts.append(phrase)
        else:
            body_parts.append(f" *\n{phrase}")
    body = "".join(body_parts).rstrip()
    if not body.endswith("[:]"):
        body = f"{body} [:]"
    # Geen lege regels in de VSA-body.
    body = "\n".join(ln for ln in body.splitlines() if ln.strip())

    fm: dict[str, Any] = {}
    if doc.frontmatter:
        fm.update(_copy_useful_frontmatter(doc.frontmatter))
    if "titel" not in fm and doc.title:
        fm["titel"] = doc.title
    if "titel" not in fm:
        comment_title = _title_from_comment_header(text)
        if comment_title:
            fm["titel"] = comment_title
    # Ontbrekende soort/toon: uit bestandsnaam (E5), bron-YAML wint.
    for key, val in _soort_toon_from_source_name(source_name).items():
        fm.setdefault(key, val)
    if last_ctx is not None:
        fm.setdefault("do", last_ctx.do)
        fm.setdefault("mode", last_ctx.mode)
    if doc.tempo is not None:
        fm.setdefault("tempo", doc.tempo)

    fm["herkomst"] = {
        "generator": "mvsa-vsa",
        "bron": Path(source_name).name,
        "stem": voice_id,
        "contract": "E1-E6",
    }

    # Zoektekst: |- , één frase per regel (zoektekst.md). Bij voorkeur uit de
    # VSA-body (*-strofen); anders L-extractie uit de MVSA.
    try:
        zt = expected_zoektekst(f"---\n---\n\n{body}\n", kind="vsa")
    except Exception:
        zt = format_zoektekst(plain_text_from_mvsa(text))
    if zt:
        fm["zoektekst"] = LiteralZoektekst(zt)

    ordered: dict[str, Any] = {}
    for key in (
        "titel",
        "taal",
        "soort",
        "toon",
        "formule",
        "partituur",
        "bron",
        "gelegenheid",
        "zoektekst",
        "do",
        "mode",
        "tempo",
        "herkomst",
    ):
        if key in fm:
            ordered[key] = fm[key]
    for key, val in fm.items():
        if key not in ordered:
            ordered[key] = val

    return f"---\n{_dump_vsa_frontmatter(ordered)}---\n\n{body}\n"


def convert_mvsa_to_vsa(
    source: Path | str,
    output: Path | str | None = None,
    *,
    voice: str = "S",
) -> Path:
    """Lees ``source``, schrijf VSA naar ``output`` (default ``.mvsa.vsa``)."""
    src = Path(source)
    text = src.read_text(encoding="utf-8")
    out = Path(output) if output else default_mvsa_vsa_output(src)
    vsa_text = convert_mvsa_to_vsa_text(
        text, source_name=src.name, voice=voice
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    write_text(out, vsa_text, encoding="utf-8", newline="\n")
    return out


def convert_mvsa_path_all_voices(
    source: Path | str,
    *,
    voices: list[str] | None = None,
) -> list[Path]:
    """Schrijf ``.mvsa.{stem}.vsa`` voor elke stem (E2; ook ``.mvsa.s.vsa``)."""
    src = Path(source)
    doc = parse_mvsa(src.read_text(encoding="utf-8"))
    available = _list_voice_markers(doc)
    targets = voices if voices is not None else available
    written: list[Path] = []
    for voice in targets:
        out = default_mvsa_vsa_output(src, voice_label=voice)
        written.append(convert_mvsa_to_vsa(src, out, voice=voice))
    return written
