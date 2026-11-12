"""VSA→template-instance: VSA-melodie → template-events; overige stemmen synchroon (T2)."""

from __future__ import annotations

import re
from contextvars import ContextVar
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from .music import Duration, Pitch
from .pitch_resolver import ALLOWED_MODES, PitchResolver, degree_to_pitch
from .template_mapping import (
    TemplateMappingError,
    assign_stanzas_to_phrases,
    select_mapping_plan,
)
from .vsa_stanzas import VsaNote, extract_stanza_notes
from .yaml_frontmatter import frontmatter_to_block_metadata, parse_vsa_frontmatter

_DEGREE_RE = re.compile(r"^(#|b)?(do|re|mi|fa|sol|la|ti)([+-][1-3])?$")
_DEGREE_ORDER = ("do", "re", "mi", "fa", "sol", "la", "ti")
_STEP_SEMI = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

CODE_PITCH_MISMATCH = "VSA-TEMPLATE-PITCH-MISMATCH"
CODE_REQUIRED_SKIPPED = "VSA-TEMPLATE-REQUIRED-SLOT-SKIPPED"
CODE_REQUIRED_UNUSED = "VSA-TEMPLATE-REQUIRED-SLOT-UNUSED"
CODE_MODE_MISMATCH = "VSA-TEMPLATE-MODE-MISMATCH"
CODE_DO_MISMATCH = "VSA-TEMPLATE-DO-MISMATCH"
CODE_TEXT_MAPPING = "VSA-TEMPLATE-TEXT-MAPPING"
CODE_CADENCE_PATH = "VSA-TEMPLATE-CADENCE-PATH"
CODE_MELODY_VOICE = "VSA-TEMPLATE-MELODY-VOICE"

CANON_ANCHORS = ("e.st.", "l.st.", "vl.st.", "l.lgr.")
MELODY_VOICES = frozenset({"S", "A", "T", "B"})

# Actieve melodiestem tijdens mapping (T2); default S.
_melody_voice_var: ContextVar[str] = ContextVar("vsa_template_melody_voice", default="S")


def get_melody_voice() -> str:
    return _melody_voice_var.get()


def _is_long_template_duration(token: str) -> bool:
    """Half/heel (eventueel gestippeld) — geen default-kwart ``~``/leeg."""
    base = str(token or "").rstrip(".")
    return base in {"_", "__"}


def _duration_from_template_token(token: str) -> Duration:
    raw = str(token or "")
    dots = raw.count(".")
    base = raw.rstrip(".")
    if base == "__":
        return Duration(note_type="whole", dots=min(dots, 2))
    if base == "_":
        return Duration(note_type="half", dots=min(dots, 2))
    return Duration(note_type="quarter", dots=0)


def melody_degree(event: dict[str, Any], *, melody_voice: str | None = None) -> str:
    """Template-laddergraad van de VSA-melodiestem op dit event (T2)."""
    voice = melody_voice if melody_voice is not None else get_melody_voice()
    pitches = event.get("pitches") or {}
    if voice not in pitches:
        raise TemplateInstanceError(
            f"template-event mist pitches.{voice} (melody_voice={voice!r})",
            code=CODE_MELODY_VOICE,
            hint_nl=(
                "Elk event moet een laddergraad hebben voor de gekozen melodiestem "
                "(default S). Of kies --melody die wél in pitches staat."
            ),
        )
    return str(pitches[voice])


class TemplateInstanceError(Exception):
    """VSA-regel past niet op de template-frase (rijke diagnostiek, vgl. vsa validate)."""

    def __init__(
        self,
        message_nl: str,
        *,
        code: str = "VSA-TEMPLATE-MAPPING",
        hint_nl: str = "",
        source: str = "",
        line: int = 0,
        column: int = 0,
        phrase_id: str = "",
        lyric: str = "",
        note_index: int | None = None,
    ) -> None:
        super().__init__(message_nl)
        self.code = code
        self.message_nl = message_nl
        self.hint_nl = hint_nl
        self.source = source
        self.line = line
        self.column = column
        self.phrase_id = phrase_id
        self.lyric = lyric
        self.note_index = note_index

    def location_label(self) -> str:
        name = Path(self.source).name if self.source else ""
        if name and self.line > 0:
            col = self.column if self.column > 0 else 1
            return f"{name}:{self.line}:{col}"
        if name:
            return name
        parts: list[str] = []
        if self.phrase_id:
            parts.append(f"frase {self.phrase_id!r}")
        if self.note_index is not None:
            parts.append(f"syllabe {self.note_index + 1}")
        if self.lyric:
            parts.append(f"lyric {self.lyric!r}")
        return ", ".join(parts) if parts else "(mapping)"

    def format_compact(self) -> str:
        """Korte regel zoals `vsa validate --summary`."""
        return f"{self.location_label()}: {self.code}"

    def format_lines(self, *, summary: bool = False, source_line: str | None = None) -> list[str]:
        """Uitgebreide of compacte weergave (zelfde geest als `format_validation_message`)."""
        if summary:
            return [self.format_compact()]
        lines = [
            self.location_label(),
            f"ERROR: {self.code}: {self.message_nl}",
        ]
        if source_line is not None and self.column > 0:
            lines.append(source_line)
            lines.append(" " * max(0, self.column - 1) + "^")
        if self.hint_nl:
            lines.append(f"Hint: {self.hint_nl}")
        return lines


@dataclass(frozen=True)
class MappedNote:
    lyric: str
    duration: Duration
    s_pitch: Pitch  # VSA-melodiepitch (ook als melody_voice ≠ S; historische naam)
    template_event: dict[str, Any]
    syllabic: str = "single"
    show_anchor: bool = False
    melody_voice: str = "S"  # T2: welke MVSA-stem de VSA-pitch krijgt
    # 1-based bronregel in de VSA (0 = onbekend). Print-wraps → meerdere
    # maten bij emit (T6); template-mapping blijft één frase.
    source_line: int = 0


def midi_of(pitch: Pitch) -> int:
    return 12 * (pitch.octave + 1) + _STEP_SEMI[pitch.step] + int(pitch.alter)


def degree_pitch(degree: str, do: str, mode: str) -> Pitch:
    match = _DEGREE_RE.match(degree)
    if not match:
        raise TemplateInstanceError(
            f"ongeldige laddergraad: {degree!r}",
            code="VSA-TEMPLATE-BAD-DEGREE",
            hint_nl="Gebruik een laddergraad zoals mi, #do of sol-1 in template.yaml.",
        )
    chrom, name, oct_off = match.group(1), match.group(2), match.group(3)
    resolver = PitchResolver.from_metadata({"do": do, "mode": mode})
    idx = _DEGREE_ORDER.index(name)
    shift = int(oct_off) if oct_off else 0
    pitch = degree_to_pitch(resolver._do, idx + 7 * shift, resolver._intervals)
    if chrom == "#":
        return Pitch(step=pitch.step, octave=pitch.octave, alter=pitch.alter + 1)
    if chrom == "b":
        return Pitch(step=pitch.step, octave=pitch.octave, alter=pitch.alter - 1)
    return pitch


def pitches_match(vsa: Pitch, degree: str, do: str, mode: str) -> bool:
    return midi_of(vsa) == midi_of(degree_pitch(degree, do, mode))


def split_phrase_events(
    events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None, list[dict[str, Any]]]:
    recite_at = next((i for i, ev in enumerate(events) if ev.get("role") == "recite"), None)
    if recite_at is None:
        return list(events), None, []
    return events[:recite_at], events[recite_at], events[recite_at + 1 :]


def normalize_anchor(value: str) -> str:
    """Canoniek anker: spaties weg, sluitende punt. ``e. st.`` → ``e.st.``."""
    compact = "".join(str(value).split())
    if compact and not compact.endswith("."):
        compact += "."
    return compact


def _norm_event(event: dict[str, Any]) -> dict[str, Any]:
    if "anchor" not in event:
        return event
    out = dict(event)
    out["anchor"] = normalize_anchor(str(event["anchor"]))
    return out


def flatten_phrase_events(
    events: list[dict[str, Any]] | None,
    *,
    of_index: int = 0,
) -> list[dict[str, Any]]:
    """Lineaire eventlijst; bij ``of`` het gekozen pad (default: eerste).

    Formuleblad toont pad 0. Instance-mapping kiest via
    ``expand_of_candidates`` het pad dat bij de VSA-hoogten past.
    """
    out: list[dict[str, Any]] = []
    for item in events or []:
        if isinstance(item, dict) and "of" in item:
            branches = item.get("of") or []
            if not branches:
                continue
            chosen = branches[of_index] if of_index < len(branches) else branches[0]
            nested = chosen.get("events", []) if isinstance(chosen, dict) else chosen
            out.extend(flatten_phrase_events(list(nested), of_index=0))
        elif isinstance(item, dict):
            out.append(_norm_event(item))
    return out


def expand_of_candidates(events: list[dict[str, Any]] | None) -> list[list[dict[str, Any]]]:
    """Alle lineaire realisaties van een frase (cartesisch product van ``of``)."""
    from itertools import product

    segments: list[list[list[dict[str, Any]]]] = []
    current: list[dict[str, Any]] = []

    def flush_flat() -> None:
        nonlocal current
        if current:
            segments.append([current])
            current = []

    for item in events or []:
        if isinstance(item, dict) and "of" in item:
            flush_flat()
            branches: list[list[dict[str, Any]]] = []
            for raw in item.get("of") or []:
                nested = raw.get("events", []) if isinstance(raw, dict) else raw
                branches.append(flatten_phrase_events(list(nested)))
            if len(branches) < 2:
                raise TemplateInstanceError(
                    "of-groep heeft minstens twee cadenspaden nodig",
                    code="VSA-TEMPLATE-OF",
                    hint_nl="Zet minstens twee `events:`-lijsten onder `of`.",
                )
            segments.append(branches)
        elif isinstance(item, dict):
            current.append(_norm_event(item))
    flush_flat()
    if not segments:
        return [[]]
    out: list[list[dict[str, Any]]] = []
    for combo in product(*segments):
        merged: list[dict[str, Any]] = []
        for part in combo:
            merged.extend(part)
        out.append(merged)
    return out


def map_stanza(
    notes: list[VsaNote],
    phrase: dict[str, Any],
    *,
    do: str,
    mode: str,
    source: str = "",
    melody_voice: str | None = None,
) -> list[MappedNote]:
    """Koppel één VSA-regel aan de events van één template-frase (H1, H4–H8).

    Bij ``of``: eerste pad dat de VSA-hoogten accepteert wint; geen pad →
    hoogte-mismatch (geen stille keuze).

    ``melody_voice`` (T2): optioneel; anders actieve context / default ``S``.
    """
    token = None
    if melody_voice is not None:
        voice = str(melody_voice).upper()
        if voice not in MELODY_VOICES:
            raise TemplateInstanceError(
                f"ongeldige melody_voice {melody_voice!r}",
                code=CODE_MELODY_VOICE,
                hint_nl=f"Gebruik een van: {', '.join(sorted(MELODY_VOICES))}.",
                source=source,
            )
        token = _melody_voice_var.set(voice)
    try:
        phrase_id = str(phrase.get("id", "?"))
        raw_events = list(phrase.get("events") or [])
        candidates = expand_of_candidates(raw_events)
        if len(candidates) == 1:
            return _map_stanza_linear(
                notes,
                candidates[0],
                phrase_id=phrase_id,
                do=do,
                mode=mode,
                source=source,
            )
        last_error: TemplateInstanceError | None = None
        retry_codes = {
            CODE_PITCH_MISMATCH,
            CODE_REQUIRED_SKIPPED,
            CODE_REQUIRED_UNUSED,
        }
        for cand in candidates:
            try:
                return _map_stanza_linear(
                    notes,
                    cand,
                    phrase_id=phrase_id,
                    do=do,
                    mode=mode,
                    source=source,
                )
            except TemplateInstanceError as exc:
                last_error = exc
                if exc.code not in retry_codes:
                    raise
        assert last_error is not None
        last_error.hint_nl = (
            (last_error.hint_nl + " ") if last_error.hint_nl else ""
        ) + (
            "Deze frase heeft meerdere cadenspaden (`of`); geen pad past bij de "
            "VSA-hoogten. Pas de VSA aan of voeg het ontbrekende pad toe in de template."
        )
        last_error.code = (
            CODE_CADENCE_PATH
            if last_error.code == CODE_PITCH_MISMATCH
            else last_error.code
        )
        raise last_error
    finally:
        if token is not None:
            _melody_voice_var.reset(token)


def _map_stanza_linear(
    notes: list[VsaNote],
    events: list[dict[str, Any]],
    *,
    phrase_id: str,
    do: str,
    mode: str,
    source: str = "",
) -> list[MappedNote]:
    if not notes:
        raise TemplateInstanceError(
            f"lege VSA-regel voor frase {phrase_id!r}",
            code="VSA-TEMPLATE-EMPTY-STANZA",
            hint_nl="Voeg gezongen tekst toe of verwijder de lege frase uit de toewijzing.",
            source=source,
            phrase_id=phrase_id,
        )
    if not events:
        raise TemplateInstanceError(
            f"frase {phrase_id!r} heeft geen events",
            code="VSA-TEMPLATE-EMPTY-PHRASE",
            hint_nl="Vul events in template.yaml voor deze frase.",
            source=source,
            phrase_id=phrase_id,
        )
    prefix, recite, tail = split_phrase_events(events)
    index = 0
    out: list[MappedNote] = []

    for i, event in enumerate(prefix):
        index = _take_prefix_event(
            notes,
            index,
            event,
            out,
            do,
            mode,
            later_prefix=prefix[i + 1 :],
            recite=recite,
        )

    if recite is not None:
        index = _consume_recite(notes, index, recite, out, do, mode)

    last_degree: str | None = None
    if out:
        last_degree = melody_degree(out[-1].template_event)

    _map_tail(
        notes,
        index,
        tail,
        out,
        do,
        mode,
        phrase_id=phrase_id,
        source=source,
        last_consumed_degree=last_degree,
    )
    return out


def _vsa_frontmatter_do_mode(vsa_text: str) -> tuple[str | None, str | None]:
    frontmatter, _ = parse_vsa_frontmatter(vsa_text)
    flat = frontmatter_to_block_metadata(frontmatter)
    do = flat.get("do")
    mode = flat.get("mode")
    return do, mode


def map_vsa_to_template(
    template: dict[str, Any],
    vsa_text: str,
    *,
    source: str = "",
    melody_voice: str = "S",
) -> list[tuple[str, list[MappedNote]]]:
    """Volledige instance-mapping: tekstregels → (frase-id, mapped notes).

    ``melody_voice`` (T2): template-``pitches``-sleutel + MVSA-stem voor de
    VSA-melodie; default ``S``.
    """
    voice = str(melody_voice or "S").upper()
    if voice not in MELODY_VOICES:
        raise TemplateInstanceError(
            f"ongeldige melody_voice {melody_voice!r}",
            code=CODE_MELODY_VOICE,
            hint_nl=f"Gebruik een van: {', '.join(sorted(MELODY_VOICES))}.",
            source=source,
        )
    do = str(template["do"])
    mode = str(template.get("mode", "major"))
    vsa_do, vsa_mode = _vsa_frontmatter_do_mode(vsa_text)
    if vsa_mode and vsa_mode != mode:
        raise TemplateInstanceError(
            f"mode in VSA ({vsa_mode!r}) wijkt af van template ({mode!r})",
            code=CODE_MODE_MISMATCH,
            hint_nl=(
                "Zet `mode` in de VSA-frontmatter gelijk aan template.yaml "
                f"(toegestaan: {', '.join(sorted(ALLOWED_MODES))})."
            ),
            source=source,
        )
    if vsa_do and vsa_do != do:
        raise TemplateInstanceError(
            f"do in VSA ({vsa_do!r}) wijkt af van template ({do!r})",
            code=CODE_DO_MISMATCH,
            hint_nl="Gebruik dezelfde do-context als de template (bijv. F4).",
            source=source,
        )
    stanzas = extract_stanza_notes(vsa_text, metadata={"do": do, "mode": mode})
    try:
        plan = select_mapping_plan(template, len(stanzas))
        phrase_ids = assign_stanzas_to_phrases(
            plan, len(stanzas), phrase_id_set={str(p["id"]) for p in template["phrases"]}
        )
    except TemplateMappingError as exc:
        raise TemplateInstanceError(
            str(exc),
            code=CODE_TEXT_MAPPING,
            hint_nl=(
                "Het aantal VSA-frasen moet passen bij sequence / text_mapping / "
                "mapping_plans van de template. Bij een speelplan dat op "
                "«laatste» eindigt (bijv. toon 3): de eerste frasen volgen het "
                "prefix; de allerlaatste frase altijd «laatste»; meer frasen "
                "dan het speelplan is een harde fout. Tel frasen via `*`/`/` of "
                "sterke `**`/`//` (spaties optioneel; ook na een punt: `.*`). "
                "EHMs in scopes tellen niet mee. Zonder `*`/`**` telt elke "
                "niet-ingesprongen regel als frase. Ingesprongen vervolgregels "
                "horen bij dezelfde frase (print-wrap)."
            ),
            source=source,
        ) from exc
    by_id = {str(p["id"]): p for p in template["phrases"]}
    token = _melody_voice_var.set(voice)
    try:
        mapped: list[tuple[str, list[MappedNote]]] = []
        for pid, notes in zip(phrase_ids, stanzas, strict=True):
            if pid not in by_id:
                raise TemplateInstanceError(
                    f"onbekende frase-id {pid!r}",
                    code="VSA-TEMPLATE-UNKNOWN-PHRASE",
                    hint_nl="Controleer cycle/final in template.yaml t.o.v. het aantal VSA-regels.",
                    source=source,
                    phrase_id=pid,
                )
            mapped.append(
                (pid, map_stanza(notes, by_id[pid], do=do, mode=mode, source=source))
            )
        return mapped
    finally:
        _melody_voice_var.reset(token)


def _prefix_unscoped_is_open_run(
    notes: list[VsaNote],
    index: int,
    event: dict[str, Any],
    later_prefix: list[dict[str, Any]],
    do: str,
    mode: str,
) -> bool:
    """True als ongemarkeerde open-aanloop gevolgd wordt door scoped latere opens.

    Groningen: ``o Ge{/bie}{/der}`` — o/Ge ongemarkeerd op do, daarna scoped re/mi.
    Elia: ongemarkeerde recite op open-toon zonder latere prefix-scopes → False (H1).
    """
    if not later_prefix:
        return False
    open_deg = melody_degree(event)
    j = index
    while (
        j < len(notes)
        and not notes[j].scoped
        and pitches_match(notes[j].pitch, open_deg, do, mode)
    ):
        j += 1
    if j >= len(notes) or not notes[j].scoped:
        return False
    return any(
        pitches_match(notes[j].pitch, melody_degree(ev), do, mode)
        for ev in later_prefix
    )


def _take_prefix_event(
    notes: list[VsaNote],
    index: int,
    event: dict[str, Any],
    out: list[MappedNote],
    do: str,
    mode: str,
    *,
    later_prefix: list[dict[str, Any]] | None = None,
    recite: dict[str, Any] | None = None,
) -> int:
    del recite  # API-symmetrie met aanroeper; open-run kijkt naar later_prefix.
    if index >= len(notes):
        return index
    matches = pitches_match(notes[index].pitch, melody_degree(event), do, mode)
    if not matches:
        return index
    note = notes[index]
    degree = melody_degree(event)
    role = str(event.get("role") or "")
    # Holds alleen op open/link — niet op e.st.-cadens (anders verdwijnt recite).
    allow_holds = role in ("open", "link")
    if note.scoped:
        _append_mapped(out, note, event, prefer_scoped_anchor=True)
        index += 1
        if allow_holds:
            while (
                index < len(notes)
                and not notes[index].scoped
                and pitches_match(notes[index].pitch, degree, do, mode)
            ):
                _append_mapped(out, notes[index], event, prefer_scoped_anchor=True)
                index += 1
        return index
    # H1: ongemarkeerd hoort bij recite — behalve open-aanloop vóór latere scopes.
    if _prefix_unscoped_is_open_run(
        notes, index, event, later_prefix or [], do, mode
    ):
        _append_mapped(out, note, event, prefer_scoped_anchor=True)
        index += 1
        while (
            index < len(notes)
            and not notes[index].scoped
            and pitches_match(notes[index].pitch, degree, do, mode)
        ):
            _append_mapped(out, notes[index], event, prefer_scoped_anchor=True)
            index += 1
        return index
    return index


def _consume_recite(
    notes: list[VsaNote],
    index: int,
    recite: dict[str, Any],
    out: list[MappedNote],
    do: str,
    mode: str,
) -> int:
    """H1: recite-toon; scoped mag starten/meedoen tot na ongemarkeerde recite cadens begint.

    Groningen ``{\\zijt} Gij uit het``: scoped do opent recite, daarna ongemarkeerd.
    Elia: na ongemarkeerde recite stopt scoped (zelfde toon) → cadens (H2).
    """
    took_unscoped = False
    while index < len(notes):
        note = notes[index]
        if not pitches_match(note.pitch, melody_degree(recite), do, mode):
            break
        if note.scoped and took_unscoped:
            break
        _append_mapped(out, note, recite, prefer_scoped_anchor=True)
        if not note.scoped:
            took_unscoped = True
        index += 1
    return index


def _append_mapped(
    out: list[MappedNote],
    note: VsaNote,
    event: dict[str, Any],
    *,
    prefer_scoped_anchor: bool,
) -> None:
    """Voeg mapped noot toe; bij e.st./l.st./vl.st. wint een scoped VSA-noot (nadruk)."""
    anchor = event.get("anchor")
    stress = anchor in ("e.st.", "l.st.", "vl.st.")
    if not stress or not prefer_scoped_anchor:
        show = bool(anchor) and not any(
            n.template_event is event and n.show_anchor for n in out
        )
        out.append(_assign(note, event, show_anchor=show))
        return
    if note.scoped:
        for i, existing in enumerate(out):
            if existing.template_event is event and existing.show_anchor:
                out[i] = replace(existing, show_anchor=False)
        out.append(_assign(note, event, show_anchor=True))
        return
    show = not any(n.template_event is event and n.show_anchor for n in out)
    out.append(_assign(note, event, show_anchor=show))


def _slot_label(event: dict[str, Any]) -> str:
    try:
        degree = melody_degree(event)
    except TemplateInstanceError:
        degree = str(event.get("pitches", {}).get("S", "?"))
    bits = [degree]
    if event.get("anchor"):
        bits.append(str(event["anchor"]))
    if event.get("optional"):
        bits.append("optional")
    return "/".join(bits)


def _map_tail(
    notes: list[VsaNote],
    index: int,
    tail: list[dict[str, Any]],
    out: list[MappedNote],
    do: str,
    mode: str,
    *,
    phrase_id: str,
    source: str = "",
    last_consumed_degree: str | None = None,
) -> None:
    event_i = 0
    llgr_from: int | None = next(
        (i for i, ev in enumerate(tail) if ev.get("anchor") == "l.lgr."),
        None,
    )

    def _pitch_mismatch(note: VsaNote, note_i: int, *, remaining: list[dict[str, Any]]) -> TemplateInstanceError:
        got = f"{note.pitch}"
        expected = [
            melody_degree(ev)
            for ev in remaining
            if not ev.get("optional")
        ]
        lyric = note.lyric or "(melisma)"
        expected_txt = ", ".join(expected) if expected else "—"
        return TemplateInstanceError(
            (
                f"hoogte-mismatch op lettergreep {lyric!r} (klinkend {got}).\n"
                f"Geen passend slot meer in de melodiestem van de formule "
                f"(verwacht o.a. {expected_txt})."
            ),
            code=CODE_PITCH_MISMATCH,
            hint_nl=(
                "Pas de VSA-hoogtemarkeringen aan zodat ze de verplichte "
                "cadensgraden van de template volgen, of kies een andere "
                "frase/cadenspad."
            ),
            source=source,
            line=note.line,
            column=note.column,
            phrase_id=phrase_id,
            lyric=lyric,
            note_index=note_i,
        )

    def _required_skipped(
        note: VsaNote,
        note_i: int,
        *,
        skipped: list[dict[str, Any]],
        matched: dict[str, Any],
    ) -> TemplateInstanceError:
        lyric = note.lyric or "(melisma)"
        skipped_txt = ", ".join(_slot_label(ev) for ev in skipped)
        return TemplateInstanceError(
            f"verplicht template-slot overgeslagen: VSA {lyric!r} = {note.pitch} "
            f"koppelt aan later slot {_slot_label(matched)}, maar slaat verplicht(e) "
            f"tussenslot(s) over ({skipped_txt})",
            code=CODE_REQUIRED_SKIPPED,
            hint_nl=(
                "Neem de overgeslagen toon(en) mee in de VSA (eigen syllabe of hold), "
                "óf markeer die template-events als optional: true als ze op het blad "
                "tussen haakjes staan."
            ),
            source=source,
            line=note.line,
            column=note.column,
            phrase_id=phrase_id,
            lyric=lyric,
            note_index=note_i,
        )

    # last_consumed_degree: doorgegeven (bijv. recite-S) of bijgewerkt in de loop.

    while index < len(notes):
        note = notes[index]
        if event_i >= len(tail):
            if not out:
                raise TemplateInstanceError(
                    f"cadensnoten zonder template-tail in frase {phrase_id!r}",
                    code="VSA-TEMPLATE-NO-TAIL",
                    hint_nl="Controleer of de frase cadence-events na recite heeft.",
                    source=source,
                    line=note.line,
                    column=note.column,
                    phrase_id=phrase_id,
                    lyric=note.lyric or "",
                    note_index=index,
                )
            last = out[-1].template_event
            if pitches_match(note.pitch, melody_degree(last), do, mode):
                # H6: extra syllabe opzelfde slot-akkoord.
                _append_mapped(out, note, last, prefer_scoped_anchor=True)
                index += 1
                continue
            raise _pitch_mismatch(note, index, remaining=[])
        try:
            matched = _next_matching_event(
                note,
                tail,
                event_i,
                do,
                mode,
                last_consumed_degree=last_consumed_degree,
            )
        except _RequiredSkip as exc:
            raise _required_skipped(
                note, index, skipped=exc.skipped, matched=exc.matched
            ) from None
        if matched is None:
            raise _pitch_mismatch(note, index, remaining=tail[event_i:])
        event_i = matched
        event = tail[event_i]
        _append_mapped(out, note, event, prefer_scoped_anchor=True)
        last_consumed_degree = melody_degree(event)
        index += 1
        # Ondergevulde zelfde-S-run met half/heel: volgende VSA-syllabe is al
        # een andere graad (bijv. le_ → na_ @l.st.). Vul tussenliggende
        # half-slots als leeg melisma (le_&_na_), i.p.v. stil H4/H7-weglaten.
        if index < len(notes) and not pitches_match(
            notes[index].pitch, last_consumed_degree, do, mode
        ):
            while event_i + 1 < len(tail):
                nxt = tail[event_i + 1]
                nxt_deg = melody_degree(nxt)
                if nxt_deg != last_consumed_degree:
                    break
                if pitches_match(notes[index].pitch, nxt_deg, do, mode):
                    break
                dur_tok = str(nxt.get("duration") or "")
                if not _is_long_template_duration(dur_tok):
                    break
                if nxt.get("anchor") in ("l.st.", "vl.st.", "e.st."):
                    break
                event_i += 1
                prev_line = out[-1].source_line if out else 0
                out.append(
                    MappedNote(
                        lyric="",
                        duration=_duration_from_template_token(dur_tok),
                        s_pitch=degree_pitch(nxt_deg, do, mode),
                        template_event=nxt,
                        syllabic="end",
                        show_anchor=False,
                        melody_voice=get_melody_voice(),
                        source_line=prev_line,
                    )
                )
        if index < len(notes) and pitches_match(
            notes[index].pitch, melody_degree(event), do, mode
        ):
            # Zelfde graad: liever volgend zelfde-melodie-slot vullen (l.st. e.d.)
            # dan eindeloos H6-holden op het eerste slot.
            if event_i + 1 < len(tail) and pitches_match(
                notes[index].pitch, melody_degree(tail[event_i + 1]), do, mode
            ):
                event_i += 1
                continue
            # H6: geen volgend zelfde-melodie-slot → hold; event_i blijft staan.
            continue
        event_i += 1

    if index >= len(notes) and llgr_from is not None and event_i <= llgr_from:
        event_i = llgr_from
    if notes and event_i < len(tail) and llgr_from is not None and event_i >= llgr_from:
        last_lyric_used = True
        for extra in tail[event_i:]:
            s_pitch = degree_pitch(melody_degree(extra), do, mode)
            prev_line = (
                out[-1].source_line
                if out
                else int(notes[-1].line or 0)
            )
            out.append(
                MappedNote(
                    lyric="" if last_lyric_used else notes[-1].lyric,
                    duration=Duration(note_type="quarter"),
                    s_pitch=s_pitch,
                    template_event=extra,
                    syllabic="end" if last_lyric_used else "single",
                    show_anchor=extra.get("anchor") == "l.lgr.",
                    melody_voice=get_melody_voice(),
                    source_line=prev_line,
                )
            )
            last_lyric_used = True
        event_i = len(tail)

    # H7: resterende verplichte slots → fout; alleen optional mag stil weg (H4).
    remaining_required = [ev for ev in tail[event_i:] if not ev.get("optional")]
    if remaining_required:
        unused_txt = ", ".join(_slot_label(ev) for ev in remaining_required)
        raise TemplateInstanceError(
            f"verplicht(e) template-slot(s) niet aangedaan in frase {phrase_id!r}: "
            f"{unused_txt}",
            code=CODE_REQUIRED_UNUSED,
            hint_nl=(
                "Breid de VSA-cadens uit zodat elke verplichte laddergraad voorkomt "
                "(syllabe, hold H6, of l.lgr.-melisma H8), of zet optionele slots op "
                "optional: true in de template. Controleer ook of de frasegrenzen "
                "kloppen: een te korte «frase» door een harde regeleinde i.p.v. "
                "ingesprongen wrap (of een ontbrekende `*`) geeft vaak precies deze fout."
            ),
            source=source,
            line=notes[-1].line if notes else 0,
            column=notes[-1].column if notes else 0,
            phrase_id=phrase_id,
            lyric=notes[-1].lyric if notes else "",
            note_index=len(notes) - 1 if notes else None,
        )


class _RequiredSkip(Exception):
    """Interne sentinel: match gevonden na verplichte tussenslots."""

    def __init__(self, skipped: list[dict[str, Any]], matched: dict[str, Any]) -> None:
        self.skipped = skipped
        self.matched = matched


def _may_skip_intermediate(
    event: dict[str, Any],
    *,
    last_consumed_degree: str | None,
) -> bool:
    """H4/H7: optional altijd; zelfde melodie-graad als laatst = rest ondergevulde run."""
    if event.get("optional"):
        return True
    try:
        degree = melody_degree(event)
    except TemplateInstanceError:
        return False
    return bool(last_consumed_degree) and degree == last_consumed_degree


def _next_matching_event(
    note: VsaNote,
    tail: list[dict[str, Any]],
    start: int,
    do: str,
    mode: str,
    *,
    last_consumed_degree: str | None = None,
) -> int | None:
    """Zoek slot vanaf ``start``. Andere toon overslaan alleen als optional (H4/H7)."""
    for i in range(start, len(tail)):
        if pitches_match(note.pitch, melody_degree(tail[i]), do, mode):
            skipped = tail[start:i]
            blocked = [
                ev
                for ev in skipped
                if not _may_skip_intermediate(
                    ev, last_consumed_degree=last_consumed_degree
                )
            ]
            if blocked:
                raise _RequiredSkip(skipped=blocked, matched=tail[i])
            return i
    return None


def _assign(note: VsaNote, event: dict[str, Any], *, show_anchor: bool) -> MappedNote:
    # H5: VSA-ELM bepaalt de werkelijke duur (template-duration ≈ formuleblad).
    # EHM/toonhoogte moet wél exact matchen (H9) — dat gebeurt vóór _assign.
    # Recite-instance: kwart per ongemarkeerde syllabe (print-collapse elders).
    duration = note.duration
    if event.get("role") == "recite":
        duration = Duration(note_type="quarter")
    return MappedNote(
        lyric=note.lyric,
        duration=duration,
        s_pitch=note.pitch,
        template_event=event,
        syllabic=note.syllabic,
        show_anchor=show_anchor and bool(event.get("anchor")),
        melody_voice=get_melody_voice(),
        source_line=int(note.line or 0),
    )
