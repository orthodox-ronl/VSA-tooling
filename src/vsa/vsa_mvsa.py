"""VSA + template → schets-MVSA (T1–T7): mapper + emit + CLI-kern.

Canonieke implementatie van ``vsa mvsa``. Experimenteel onderzoekscript:
``examples/formule-tekst/scripts/fase_a_vsa_template.py`` (re-exports hieruit).

S in de afgeleide MVSA komt uit de VSA-noten (na geslaagde slot-match).
Overige stemmen uit de template (T2/T3). Schrijfoctaven: zie
``template_library.DEFAULT_VOICE_OCT`` (A=0 → F4, niet F5).
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from .music import Pitch
from .mvsa_align import align_mvsa_text
from .mvsa_normalize import (
    format_ehm,
    pitch_to_degree_and_chrom,
)
from .pitch_resolver import (
    PitchResolver,
    _pitch_to_midi,
    degree_to_pitch,
    pitch_in_do_octave,
)
from .template_instance import (
    MappedNote,
    TemplateInstanceError,
    degree_pitch,
    map_vsa_to_template,
    midi_of,
)
from .template_library import (
    DEFAULT_OCT_LINE,
    DEFAULT_TEMPO_TROPAAR_KONDAK,
    DEFAULT_VOICE_OCT,
    ResolvedTemplate,
    TemplateLibraryError,
    infer_template_id,
    load_resolved_template,
)
from .vsa_stanzas import ensure_stanza_stars, extract_stanza_notes
from .yaml_frontmatter import parse_vsa_frontmatter

# Schrijfoctaven synchroon met @oct-regel (T5 emit / Coria-MXL).
_VOICE_OCT = dict(DEFAULT_VOICE_OCT)

# Zichtbare banner bovenaan afgeleide MVSA (zelfde idee als MSCZ/MXL-import).
TEMPLATE_DERIVED_WARNING_BANNER = """\
#  ##########################################################################  #
#  #                                                                        #  #
#  #   WAARSCHUWING:                                                        #  #
#  #                                                                        #  #
#  #   DIT BESTAND IS AFGELEID UIT VSA + TEMPLATE EN IS EEN SCHETS.         #  #
#  #   CONTROLEER VÓÓR OPNAME IN DE CATALOGUS TEN MINSTE:                   #  #
#  #   - duren (halve noten ``_`` blijven eigen L-posities; recite = kwart) #  #
#  #   - melisma-ELMs (``{/&/fi~&~}`` vs ``{/&/fi_}`` → parser-verdubbeling)#  #
#  #   - recite-haakjes, woordstreepjes, A/T/B t.o.v. S                     #  #
#  #   - regels hieronder die met ``# WAARSCHUWING:`` beginnen              #  #
#  #                                                                        #  #
#  ##########################################################################  #\
"""


def format_emit_warnings(warnings: list[str]) -> list[str]:
    """Specifieke emit-waarschuwingen als commentaarregels."""
    if not warnings:
        return []
    lines = ["# --- specifieke waarschuwingen (emit) ---"]
    for w in warnings:
        lines.append(f"# WAARSCHUWING: {w}")
    lines.append("#")
    return lines


# Frontmatter-velden die in de afgeleide MVSA blijven (playback → @-regels).
# ``template`` = feitelijk gebruikte formule-id (T1/T6); niet playback.
# ``template_opgegeven`` = wat bij conversie werd gevraagd (alias), indien anders.
_EMIT_FRONTMATTER_KEYS = (
    "titel",
    "partituur",
    "toon",
    "taal",
    "bron",
    "soort",
    "gelegenheid",
    "zoektekst",
    "template",
    "template_opgegeven",
)


def clean_emit_frontmatter(
    meta: dict[str, Any],
    *,
    template_id: str | None = None,
    template_opgegeven: str | None = None,
) -> str:
    """YAML-frontmatter voor schets-MVSA: catalogusvelden + formule-id.

    Geen ``do`` / ``mode`` / ``tempo`` (playback staat in ``@``-regels).
    ``template`` = feitelijk gebruikte formule-id (na alias/``same_as``).
    ``template_opgegeven`` alleen als die afwijkt van ``template``.
    """
    if not meta and not template_id:
        return ""
    out: dict[str, Any] = {}
    src = meta or {}
    if src.get("titel") not in (None, ""):
        out["titel"] = src["titel"]
    elif src.get("title") not in (None, ""):
        out["titel"] = src["title"]
    skip = {"titel", "template", "template_opgegeven"}
    for key in _EMIT_FRONTMATTER_KEYS:
        if key in skip:
            continue
        val = src.get(key)
        if val is None or val == "":
            continue
        out[key] = val
    tid = str(template_id or src.get("template") or "").strip()
    if tid:
        out["template"] = tid
    asked = str(
        template_opgegeven
        if template_opgegeven is not None
        else (src.get("template_opgegeven") or "")
    ).strip()
    if asked and tid and asked != tid:
        out["template_opgegeven"] = asked
    if not out:
        return ""
    try:
        import yaml
    except ImportError:
        lines = ["---"]
        if out.get("titel"):
            lines.append(f"titel: {out['titel']}")
        if out.get("template"):
            lines.append(f"template: {out['template']}")
        if out.get("template_opgegeven"):
            lines.append(f"template_opgegeven: {out['template_opgegeven']}")
        lines.append("---")
        return "\n".join(lines) if len(lines) > 2 else ""
    dumped = yaml.safe_dump(
        out,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).rstrip()
    return f"---\n{dumped}\n---"


def cycle_length_for_emit(template: dict[str, Any]) -> int:
    """Aantal frasen in één template-cyclus (voor ``@sectie cyclus-1``)."""
    cycle = template.get("cycle")
    if isinstance(cycle, list) and cycle:
        return len(cycle)
    return 1


def emit_sections_enabled(template: dict[str, Any]) -> bool:
    """Drie ``@sectie``'s (cyclus-1 / herhaling / laatste); niet bij toon 3."""
    tone = template.get("tone")
    try:
        return int(tone) != 3
    except (TypeError, ValueError):
        return True


def section_id_for_phrase_index(
    index: int,
    phrase_ids: list[str],
    *,
    cycle_len: int,
    final_id: str = "laatste",
) -> str | None:
    """Sectie-id voor frase-index, of ``None`` als secties uit staan bij aanroep.

    - ``cyclus-1``: eerste cycle-lengte
    - ``herhaling``: daarna tot vóór ``final_id``
    - ``laatste``: frasen met id ``final_id`` (anders laatste frase)
    """
    n = len(phrase_ids)
    if n == 0 or index < 0 or index >= n:
        return None
    final_start = next(
        (i for i, pid in enumerate(phrase_ids) if pid == final_id),
        n - 1,
    )
    cl = max(1, int(cycle_len))
    if index < min(cl, final_start):
        return "cyclus-1"
    if index < final_start:
        return "herhaling"
    return "laatste"

@dataclass
class FileResult:
    file: str
    ok: bool
    phrases: int = 0
    phrase_ids: list[str] = field(default_factory=list)
    notes: int = 0
    s_identical: bool = False
    s_mismatch: int = 0
    optional_used: int = 0
    optional_skipped_phrases: int = 0
    anchors_shown: int = 0
    error: str = ""
    error_code: str = ""
    hint: str = ""
    issues: list[str] = field(default_factory=list)


def restore_vsa(raw: str) -> tuple[str, str]:
    fm_m = re.match(r"^(---\n.*?\n---\n)", raw, flags=re.S)
    fm = fm_m.group(1) if fm_m else ""
    rest = raw[len(fm) :]
    if "# === oorspronkelijke VSA" in rest:
        m = re.search(r"# === oorspronkelijke VSA[^\n]*\n(.*)\Z", rest, flags=re.S)
        if not m:
            raise ValueError("oorspronkelijke VSA-commentaar ontbreekt")
        lines = []
        for ln in m.group(1).splitlines():
            if ln.startswith("# "):
                lines.append(ln[2:])
            elif ln == "#":
                lines.append("")
            else:
                lines.append(ln)
        return fm, "\n".join(lines).strip() + "\n"
    if "# === nieuwe notatie" in rest or "# === afgeleide mvsa" in rest:
        body = re.split(r"\n# === ", rest, maxsplit=1)[0].strip() + "\n"
        return fm, body
    return fm, rest if rest.endswith("\n") else rest + "\n"


def pitch_token(p: Pitch) -> str:
    """Fallback wetenschappelijk a–g (tests/oude callers)."""
    alter = {0: "", 1: "#", -1: "b", 2: "##", -2: "bb"}.get(int(p.alter), "")
    if int(p.alter) == -1 and p.step == "B":
        return f"Bb{int(p.octave)}"
    return f"{p.step.lower()}{alter}{int(p.octave)}"


def elm_token(note: MappedNote) -> str:
    d = note.duration
    nt = getattr(d, "note_type", None) or getattr(d, "type", "quarter")
    dots = int(getattr(d, "dots", 0) or 0)
    if nt == "whole":
        base = "__"
    elif nt == "half":
        base = "_"
    elif nt == "eighth":
        base = "~"
    else:
        base = ""  # quarter = default
    if dots == 1:
        base = (base or "~") + "."
    elif dots >= 2:
        base = (base or "_") + ".."
    return base


def _voice_pitch_obj(note: MappedNote, voice: str, *, do: str, mode: str) -> Pitch:
    # T2: VSA-melodiepitch op melody_voice (default S); overige uit template.
    mv = getattr(note, "melody_voice", None) or "S"
    if voice == mv:
        return note.s_pitch
    pitches = note.template_event.get("pitches") or {}
    if voice not in pitches:
        # Ontbrekende stem: herhaal melodiepitch (beter dan crashen in schets).
        return note.s_pitch
    return degree_pitch(str(pitches[voice]), do, mode)


def _continues_word(prev_syl: str, cur_syl: str) -> bool:
    return prev_syl in ("begin", "middle") and cur_syl in ("middle", "end")


def _abc_body(pitch: Pitch) -> str:
    alter = int(pitch.alter)
    step = pitch.step
    if alter == -2:
        return f"{step.lower()}bb"
    if alter == -1:
        return "Bb" if step == "B" else f"{step.lower()}b"
    if alter == 1:
        return f"{step.lower()}#"
    if alter == 2:
        return f"{step.lower()}##"
    return step.lower()


def format_abc_writing_oct(pitch: Pitch, schrijf_do: Pitch) -> str:
    """a–g t.o.v. schrijf-do: ``f``, ``c``, ``f+``, ``Bb`` — geen ``f4``."""
    body = _abc_body(pitch)
    base = pitch_in_do_octave(
        schrijf_do, pitch.step, float(pitch.alter), oct_delta=0
    )
    delta = (_pitch_to_midi(pitch) - _pitch_to_midi(base)) // 12
    if delta == 0:
        return body
    if delta == 1:
        return f"{body}+"
    if delta == -1:
        return f"{body}-"
    if delta > 1:
        return f"{body}+{delta}"
    return f"{body}{delta}"


def _escape_lyric_punct(core_with_elm: str, punct: str) -> str:
    """Zinspunt ``.`` escapen (`\\.`) zodat het geen ELM-duur wordt."""
    if not punct:
        return core_with_elm
    out = []
    for ch in punct:
        if ch == ".":
            out.append("\\.")
        else:
            out.append(ch)
    return core_with_elm + "".join(out)


def _lyric_core_and_punct(lyric: str) -> tuple[str, str]:
    m = re.match(r"^(.*?)([.,;:!?…]+)?$", lyric, flags=re.UNICODE)
    if not m:
        return lyric, ""
    return m.group(1) or "", m.group(2) or ""


@dataclass
class _LAtom:
    text: str
    syllabic: str
    role: str


def _melisma_pitch_slot(
    pitches: list[Pitch],
    *,
    do_pitch: Pitch,
    intervals: list[int],
    schrijf_do: Pitch,
    prev_degree: int | None,
) -> tuple[str, int]:
    """Eén MVSA-hoogteslot; melisma → ``f&/&/`` (ag-vsa binnen ``&``)."""
    parts: list[str] = []
    deg = prev_degree
    for i, p in enumerate(pitches):
        if deg is None:
            parts.append(format_abc_writing_oct(p, schrijf_do))
        elif i > 0 and p == pitches[i - 1]:
            parts.append("-")
        else:
            parts.append(format_ehm(deg, p, do_pitch, intervals))
        deg, _ = pitch_to_degree_and_chrom(do_pitch, p, intervals)
    return "&".join(parts), deg  # type: ignore[return-value]


def _emit_voice_ag_vsa(
    note_groups: list[list[MappedNote]],
    voice: str,
    *,
    do: str,
    mode: str,
) -> str:
    """ag-vsa: eerste a–g t.o.v. @oct, daarna EHM, eindanker na ``|``."""
    resolver = PitchResolver.from_metadata({"do": do, "mode": mode})
    do_pitch = resolver._do
    intervals = resolver._intervals
    writing_oct = _VOICE_OCT.get(voice, 0)
    schrijf_do = degree_to_pitch(do_pitch, 7 * writing_oct, intervals)
    slots: list[str] = []
    prev_degree: int | None = None
    last_pitch: Pitch | None = None
    for group in note_groups:
        pitches = [_voice_pitch_obj(n, voice, do=do, mode=mode) for n in group]
        if (
            len(pitches) == 1
            and last_pitch is not None
            and pitches[0] == last_pitch
            and prev_degree is not None
        ):
            slots.append("-")
            last_pitch = pitches[0]
            continue
        slot, prev_degree = _melisma_pitch_slot(
            pitches,
            do_pitch=do_pitch,
            intervals=intervals,
            schrijf_do=schrijf_do,
            prev_degree=prev_degree,
        )
        slots.append(slot)
        last_pitch = pitches[-1]
    body = " ".join(slots)
    if last_pitch is None:
        return f"{body} |" if body else "|"
    return f"{body} |{format_abc_writing_oct(last_pitch, schrijf_do)}"


def _join_l_atoms(atoms: list[_LAtom]) -> str:
    """Lettergreepstreepjes; recite-atom heeft al ``(…)``; woord over grens → ``)-``."""
    if not atoms:
        return ""
    parts: list[str] = []
    i = 0
    while i < len(atoms):
        if atoms[i].role == "recite":
            # text is al "(Al-le-lu-ia)"; eventueel woord doorloop ná ')'
            # Alleen non-recite-vervolg (``)-mach_``). Een volgend recite-atom
            # niet met ``-(…`` plakken: dat maakt wees-``-`` vóór ``(`` en
            # breekt MVSA-SYNC na kolomalign (T5).
            recite_txt = atoms[i].text
            j = i + 1
            if (
                j < len(atoms)
                and atoms[j].role != "recite"
                and _continues_word(atoms[i].syllabic, atoms[j].syllabic)
            ):
                # Zeldzaam: syllabic op recite-stuk is 'single'; doorloop via
                # laatste lettergreep in de haakjes — gebruik cadence-syllabic.
                cont = [atoms[j]]
                k = j + 1
                while (
                    k < len(atoms)
                    and atoms[k].role != "recite"
                    and _continues_word(
                        atoms[k - 1].syllabic, atoms[k].syllabic
                    )
                ):
                    cont.append(atoms[k])
                    k += 1
                # "(…ver)-nie" — strip sluit-haakje, plak )-vervolg
                if recite_txt.endswith(")"):
                    parts.append(
                        f"{recite_txt[:-1]})-{_hyphen_join_texts(cont)}"
                    )
                else:
                    parts.append(f"{recite_txt}-{_hyphen_join_texts(cont)}")
                i = k
            else:
                parts.append(recite_txt)
                i = j
            continue
        j = i + 1
        while j < len(atoms) and atoms[j].role != "recite":
            j += 1
        parts.append(_hyphen_join_texts(atoms[i:j]))
        i = j
    return " ".join(parts)


def _hyphen_join_texts(atoms: list[_LAtom]) -> str:
    if not atoms:
        return ""
    out = atoms[0].text
    for prev, cur in zip(atoms, atoms[1:]):
        if _continues_word(prev.syllabic, cur.syllabic):
            out += f"-{cur.text}"
        else:
            out += f" {cur.text}"
    return out


def _note_groups(notes: list[MappedNote]) -> list[list[MappedNote]]:
    """Melisma: lege lyrics plakken aan vorige lettergreep (zelfde template-role).

    Lege noten met een *andere* role horen niet stil bij de vorige lettergreep
    (die bleven anders aan recite kleven en verdwenen bij recite-collapse →
    f-bb-bb i.p.v. f + g&a op fi). Ze starten een eigen groep en worden in
    ``_attach_leading_empties`` aan de volgende tekstlettergreep gehangen.
    """
    raw: list[list[MappedNote]] = []
    i = 0
    while i < len(notes):
        head = notes[i]
        head_role = head.template_event.get("role")
        group = [head]
        j = i + 1
        while j < len(notes) and not (notes[j].lyric or "").strip():
            if notes[j].template_event.get("role") != head_role:
                break
            group.append(notes[j])
            j += 1
        raw.append(group)
        i = j
    return _attach_leading_empties(raw)


def _attach_leading_empties(
    groups: list[list[MappedNote]],
) -> list[list[MappedNote]]:
    """Lege kop-groepen → melisma op de volgende tekstlettergreep (na de tekst)."""
    out: list[list[MappedNote]] = []
    i = 0
    while i < len(groups):
        g = groups[i]
        if any((n.lyric or "").strip() for n in g):
            out.append(g)
            i += 1
            continue
        # Lege groep: zoek volgende tekstgroep
        if i + 1 < len(groups) and any(
            (n.lyric or "").strip() for n in groups[i + 1]
        ):
            nxt = groups[i + 1]
            text_i = next(
                k for k, n in enumerate(nxt) if (n.lyric or "").strip()
            )
            head = nxt[text_i]
            trailing = nxt[text_i + 1 :]
            out.append([head] + g + trailing)
            i += 2
            continue
        i += 1
    return out

def _collapse_recite_groups(
    groups: list[list[MappedNote]],
) -> list[list[MappedNote]]:
    """Template-recite → één groep; daarna same-pitch/duur-runs → recite."""
    out: list[list[MappedNote]] = []
    i = 0
    while i < len(groups):
        role = str(groups[i][0].template_event.get("role") or "")
        if role != "recite":
            out.append(groups[i])
            i += 1
            continue
        merged: list[MappedNote] = []
        while i < len(groups) and str(
            groups[i][0].template_event.get("role") or ""
        ) == "recite":
            merged.extend(groups[i])
            i += 1
        out.append(merged)
    return _merge_same_pitch_duration_as_recite(out)


def _note_pitch_dur_key(note: MappedNote) -> tuple:
    d = note.duration
    nt = getattr(d, "note_type", None) or getattr(d, "type", "quarter")
    dots = int(getattr(d, "dots", 0) or 0)
    return (midi_of(note.s_pitch), nt, dots)


def _group_pitch_dur_key(group: list[MappedNote]) -> tuple | None:
    """Sleutel voor same-pitch-recite; None = niet samenvoegen (melisma/wissel)."""
    text = [n for n in group if (n.lyric or "").strip()]
    if not text:
        return None
    # Melisma (lege noten met andere toon) → geen same-pitch-run.
    pitches = [n.s_pitch for n in group]
    if any(p != pitches[0] for p in pitches[1:]):
        return None
    keys = {_note_pitch_dur_key(n) for n in text}
    if len(keys) != 1:
        return None
    return next(iter(keys))


def _as_recite_notes(notes: list[MappedNote]) -> list[MappedNote]:
    """Zet role op recite zodat L-haakjes + één stemsloot volgen."""
    out: list[MappedNote] = []
    for n in notes:
        ev = dict(n.template_event)
        ev["role"] = "recite"
        out.append(replace(n, template_event=ev))
    return out


def _is_default_quarter_key(key: tuple) -> bool:
    """MVSA-recite = standaardduur per lettergreep; ELM in ``(…)`` bestaat niet."""
    _midi, nt, dots = key
    return nt == "quarter" and dots == 0


def _merge_same_pitch_duration_as_recite(
    groups: list[list[MappedNote]],
) -> list[list[MappedNote]]:
    """Opeenvolgende **kwart**lettergrepen opzelfde S-toon → één recite.

    Alleen default-kwart (geen ``_``/``_.``/…): in MVSA tellen ELMs binnen
    ``(…)`` niet — ``(Ljoe_-bov_)`` zou twee halve noten kwijtraken. Halve
    noten blijven dus eigen L-posities (``Ljoe_-bov_``).

    Dekt template-recite én open/cadens-runs (``van hun eer-…-ge``), en trekt
    een cadenslettergreep vóór recite mee (``heb``+``ben…`` → ``(heb-ben …)``).
    """
    out: list[list[MappedNote]] = []
    i = 0
    while i < len(groups):
        key = _group_pitch_dur_key(groups[i])
        if key is None or not _is_default_quarter_key(key):
            out.append(groups[i])
            i += 1
            continue
        run = [groups[i]]
        j = i + 1
        while j < len(groups) and _group_pitch_dur_key(groups[j]) == key:
            # Cadens + cadens op dezelfde kwart → géén recite-run.
            # Anders verdwijnt de inzet-hold (``e- -`` / ``ken-de`` / ``de wach``)
            # in ``(…)`` of raakt align een lettergreep kwijt.
            prev_role = str(run[-1][0].template_event.get("role") or "")
            next_role = str(groups[j][0].template_event.get("role") or "")
            if prev_role == "cadence" and next_role == "cadence":
                break
            run.append(groups[j])
            j += 1
        flat = [n for g in run for n in g]
        text_n = sum(1 for n in flat if (n.lyric or "").strip())
        had_recite = any(
            str(n.template_event.get("role") or "") == "recite" for n in flat
        )
        if text_n >= 2 or had_recite:
            out.append(_as_recite_notes(flat))
        else:
            out.append(groups[i])
            j = i + 1
        i = j
    return out


def collect_emit_warnings(
    phrase_id: str,
    notes: list[MappedNote],
    *,
    index: int,
) -> list[str]:
    """Detecteer bekende VSA/template-valkuilen die de emit niet stil mag ‘fixen’."""
    warnings: list[str] = []
    i = 0
    while i < len(notes):
        n = notes[i]
        if not (n.lyric or "").strip():
            i += 1
            continue
        melisma = [n]
        j = i + 1
        while j < len(notes) and not (notes[j].lyric or "").strip():
            melisma.append(notes[j])
            j += 1
        if len(melisma) >= 2:
            elms = [elm_token(x) or "~" for x in melisma]
            # Alleen hinten bij verdachte verdubbeling: zelfde niet-default ELM
            # op alle slots. Expliciet ``_&_`` in de VSA is geldig — controleer
            # of de bron niet ``{/&/…_}`` (één _) was (parser kopieert dan _).
            if len(set(elms)) == 1 and elms[0] not in ("", "~"):
                warnings.append(
                    f"frase {index}/{phrase_id!r}: melisma op {n.lyric!r} heeft "
                    f"{len(melisma)}× ELM {elms[0]!r}. Klopt dat met de bron-VSA? "
                    f"Expliciet `_&_` (enz.) is ok; één `_` bij `/&/` wordt door de "
                    f"parser verdubbeld (vaak bedoeld als ~&~)."
                )
        i = j
    return warnings


def _format_syllable_l(
    note: MappedNote,
    *,
    melisma_elms: list[str] | None = None,
    include_elm: bool = True,
) -> str:
    lyric = (note.lyric or "").strip() or "-"
    core, punct = _lyric_core_and_punct(lyric)
    elm = elm_token(note) if include_elm else ""
    if melisma_elms:
        body = core + (elm or "~") + "".join(f"&{e}" for e in melisma_elms)
    elif elm:
        body = f"{core}{elm}"
    else:
        body = core
    return _escape_lyric_punct(body, punct)


def _recite_l_text(notes: list[MappedNote]) -> str:
    """``(Al-le-lu-ia)`` — geen ELM in de haakjes (MVSA negeert die); alleen tekst."""
    bits: list[_LAtom] = []
    for n in notes:
        if not (n.lyric or "").strip():
            continue
        text = _format_syllable_l(n, include_elm=False)
        bits.append(_LAtom(text=text, syllabic=n.syllabic or "single", role="recite"))
    inner = _hyphen_join_texts(bits) if bits else "-"
    return f"({inner})"

def _group_l_atom(group: list[MappedNote]) -> _LAtom:
    text_notes = [n for n in group if (n.lyric or "").strip()]
    head = text_notes[0] if text_notes else group[0]
    role = str(head.template_event.get("role") or "")
    if role == "recite":
        last_syl = "single"
        for n in reversed(group):
            if (n.lyric or "").strip():
                last_syl = n.syllabic or "single"
                break
        return _LAtom(
            text=_recite_l_text(group),
            syllabic=last_syl,
            role="recite",
        )
    melisma_elms: list[str] = []
    if text_notes:
        idx = group.index(text_notes[0])
        for n in group[idx + 1 :]:
            if (n.lyric or "").strip():
                break
            melisma_elms.append(elm_token(n) or "~")
        text = _format_syllable_l(
            text_notes[0], melisma_elms=melisma_elms or None
        )
        extra = text_notes[1:]
        if extra:
            bits = [
                _LAtom(
                    text=text,
                    syllabic=text_notes[0].syllabic or "single",
                    role=role,
                )
            ]
            for n in extra:
                bits.append(
                    _LAtom(
                        text=_format_syllable_l(n),
                        syllabic=n.syllabic or "single",
                        role=role,
                    )
                )
            text = _hyphen_join_texts(bits)
    else:
        text = "-"
    return _LAtom(text=text, syllabic=head.syllabic or "single", role=role)


def _stem_groups_from_l_groups(
    groups: list[list[MappedNote]],
) -> list[list[MappedNote]]:
    """Recite → één toon (+ eventuele same-role melisma); anders hele groep."""
    stem_groups: list[list[MappedNote]] = []
    for g in groups:
        text_notes = [n for n in g if (n.lyric or "").strip()]
        head = text_notes[0] if text_notes else g[0]
        role = str(head.template_event.get("role") or "")
        if role == "recite":
            # Eerste tekstnoot + same-role lege melisma direct erna
            chunk = [head]
            idx = g.index(head)
            for n in g[idx + 1 :]:
                if (n.lyric or "").strip():
                    break
                if n.template_event.get("role") == "recite":
                    chunk.append(n)
                else:
                    break
            stem_groups.append(chunk)
        else:
            # Tekstkop + volgende lege melisma-noten (ook andere role = herplaatst)
            if not text_notes:
                stem_groups.append(g)
                continue
            idx = g.index(text_notes[0])
            chunk = [text_notes[0]]
            for n in g[idx + 1 :]:
                if (n.lyric or "").strip():
                    break
                chunk.append(n)
            # Overige tekstnoten in groep: aparte slots
            stem_groups.append(chunk)
            for n in text_notes[1:]:
                stem_groups.append([n])
    return stem_groups


def emit_mvsa_block(
    phrase_id: str,
    notes: list[MappedNote],
    *,
    do: str,
    mode: str,
    index: int,
    total: int,
    warnings: list[str] | None = None,
) -> str:
    """Schrijf één systeem (L + SATB), zonder ``@blok`` / speelplan.

    Optioneel: append detectie-waarschuwingen aan ``warnings``.
    ``phrase_id`` / ``total`` blijven voor waarschuwingsteksten (T6).
    """
    _ = total
    if warnings is not None:
        warnings.extend(
            collect_emit_warnings(phrase_id, notes, index=index)
        )
    groups = _collapse_recite_groups(_note_groups(notes))
    atoms = [_group_l_atom(g) for g in groups]
    l_line = _join_l_atoms(atoms)
    stem_groups = _stem_groups_from_l_groups(groups)
    block = "\n".join(
        [
            f"L: {l_line} |",
            f"S: {_emit_voice_ag_vsa(stem_groups, 'S', do=do, mode=mode)}",
            f"A: {_emit_voice_ag_vsa(stem_groups, 'A', do=do, mode=mode)}",
            f"T: {_emit_voice_ag_vsa(stem_groups, 'T', do=do, mode=mode)}",
            f"B: {_emit_voice_ag_vsa(stem_groups, 'B', do=do, mode=mode)}",
        ]
    )
    # Kolom-align binnen dit systeem (L/S/A/T/B).
    aligned = align_mvsa_text(
        "\n".join(
            [
                "@do F4",
                "@mode major",
                DEFAULT_OCT_LINE,
                "",
                block,
            ]
        )
    )
    # Strip de tijdelijke header terug naar alleen L/S/A/T/B.
    lines = aligned.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith("L:"))
    return "\n".join(lines[start:])


def emit_mapped_document(
    mapped: list[tuple[str, list[MappedNote]]],
    *,
    do: str,
    mode: str,
    title: str,
    source_path: str,
    template_path: str,
    frontmatter: str = "",
    vsa_body_comment: str = "",
    tempo: int | None = DEFAULT_TEMPO_TROPAAR_KONDAK,
    oct_line: str = DEFAULT_OCT_LINE,
    cycle_len: int = 1,
    with_sections: bool = True,
    final_id: str = "laatste",
) -> tuple[str, list[str]]:
    """Volledige MVSA-tekst (T6): commentaar + @-kop + systemen, geen speelplan.

    Secties ``cyclus-1`` / ``herhaling`` / ``laatste`` wanneer
    ``with_sections`` (standaard; uit voor toon 3).
    """
    warnings: list[str] = []
    n = len(mapped)
    phrase_ids = [pid for pid, _ in mapped]
    systems = [
        emit_mvsa_block(
            pid,
            notes,
            do=do,
            mode=mode,
            index=i,
            total=n,
            warnings=warnings,
        )
        for i, (pid, notes) in enumerate(mapped, start=1)
    ]
    parts: list[str] = []
    if frontmatter.strip():
        parts.append(frontmatter.rstrip())
        parts.append("")
    if vsa_body_comment.strip():
        parts.append("# === oorspronkelijke VSA (commentaar) ===")
        parts.append(vsa_body_comment.rstrip())
        parts.append("")
    parts.append("# === afgeleide mvsa (VSA + template) ===")
    parts.append(f"# bron: {source_path}")
    parts.append(f"# template: {template_path}")
    parts.append("# Notatie: ag-vsa; recite = template-kwart óf same-pitch-kwart-run.")
    parts.extend(TEMPLATE_DERIVED_WARNING_BANNER.splitlines())
    parts.extend(format_emit_warnings(warnings))
    if title:
        parts.append(f'@title "{title}"')
    parts.append(f"@do {do}")
    parts.append(f"@mode {mode}")
    if tempo is not None:
        parts.append(f"@tempo {tempo}")
    parts.append(oct_line)
    parts.append("")

    prev_section: str | None = None
    for i, system in enumerate(systems):
        if with_sections:
            sec = section_id_for_phrase_index(
                i,
                phrase_ids,
                cycle_len=cycle_len,
                final_id=final_id,
            )
            if sec and sec != prev_section:
                parts.append(f"@sectie {sec}")
                prev_section = sec
        parts.append(system)
        parts.append("")
    return "\n".join(parts).rstrip() + "\n", warnings


def analyze_mapped(
    mapped: list[tuple[str, list[MappedNote]]],
    vsa_text: str,
    *,
    do: str,
    mode: str,
) -> tuple[list[str], FileResult]:
    stanzas = extract_stanza_notes(vsa_text, metadata={"do": do, "mode": mode})
    lines: list[str] = []
    s_mis = 0
    total_notes = 0
    opt_used = 0
    opt_skip_ph = 0
    anchors = 0
    for (pid, notes), stanza in zip(mapped, stanzas, strict=True):
        lines.append(f"### Frase → template `{pid}` ({len(notes)} noten)")
        vsa_pitches = [str(n.pitch) for n in stanza]
        der_pitches = [str(n.s_pitch) for n in notes]
        lines.append(f"- VSA S ({len(vsa_pitches)}): {' '.join(vsa_pitches)}")
        lines.append(f"- MVSA S ({len(der_pitches)}): {' '.join(der_pitches)}")
        if vsa_pitches == der_pitches:
            lines.append("- S-hoogtes: IDENTIEK (verwacht: S komt uit VSA na slot-match)")
        else:
            # kan gebeuren bij melisma-split vs lyric merge
            lines.append("- S-hoogtes: VERSCHIL in lengte/volgorde t.o.v. extract_stanza_notes")
            for i, (a, b) in enumerate(zip(vsa_pitches, der_pitches)):
                if a != b:
                    s_mis += 1
                    if s_mis <= 8:
                        lines.append(f"  [{i}] VSA={a} MVSA={b}")
            s_mis += abs(len(vsa_pitches) - len(der_pitches))
        roles = [n.template_event.get("role") for n in notes]
        lines.append(f"- roles: {roles}")
        used_opt = [n for n in notes if n.template_event.get("optional")]
        if used_opt:
            opt_used += len(used_opt)
            lines.append(f"- optional slots GEBRUIKT: {len(used_opt)}")
        else:
            # phrase 2 often skips — detect if phrase has optional in template
            if pid == "2":
                opt_skip_ph += 1
                lines.append("- optional link: overgeslagen (geen optional in instance)")
        for n in notes:
            if n.show_anchor and n.template_event.get("anchor"):
                anchors += 1
                lines.append(
                    f"- anker {n.template_event.get('anchor')} op {n.lyric!r} "
                    f"(S={n.s_pitch})"
                )
        total_notes += len(notes)
        lines.append("")

    identical = s_mis == 0 and total_notes > 0
    # also require equal counts
    if sum(len(s) for s in stanzas) != total_notes:
        identical = False
    fr = FileResult(
        file="",
        ok=True,
        phrases=len(mapped),
        phrase_ids=[p for p, _ in mapped],
        notes=total_notes,
        s_identical=identical,
        s_mismatch=s_mis,
        optional_used=opt_used,
        optional_skipped_phrases=opt_skip_ph,
        anchors_shown=anchors,
    )
    return lines, fr


@dataclass
class VsaMvsaResult:
    """Resultaat van ``convert_vsa_to_mvsa`` (T1–T7)."""

    text: str
    warnings: list[str]
    resolved: ResolvedTemplate
    phrase_ids: list[str]
    source_path: Path
    output_path: Path | None = None


def _tempo_from_meta(meta: dict[str, Any]) -> int:
    """VSA-frontmatter-tempo wordt genegeerd voor tropaar/kondak-schetsen.

    Canonieke default: ``DEFAULT_TEMPO_TROPAAR_KONDAK`` (180). Alleen
    expliciet ``convert_vsa_to_mvsa(..., tempo=…)`` / ``--tempo`` wijkt af.
    ``meta`` blijft in de signatuur voor call-site-compatibiliteit.
    """
    del meta
    return DEFAULT_TEMPO_TROPAAR_KONDAK


def _vsa_body_as_comment(body: str) -> str:
    lines: list[str] = []
    for ln in body.strip().splitlines():
        if not ln.strip():
            lines.append("#")
        elif ln.startswith("#"):
            lines.append(f"# {ln}")
        else:
            lines.append(f"# {ln}")
    return "\n".join(lines)


def convert_vsa_to_mvsa(
    source: Path | str,
    *,
    template: str | None = None,
    library_root: Path | None = None,
    melody_voice: str = "S",
    output: Path | str | None = None,
    write: bool = False,
    include_frontmatter: bool = True,
    include_vsa_comment: bool = True,
    tempo: int | None = None,
) -> VsaMvsaResult:
    """VSA + library-template → schets-MVSA-tekst (T1–T7).

    ``template``: canonieke id of playbook-alias. Zonder ``--template``:
    afleiden uit frontmatter/pad (``infer_template_id``), anders Hemelum
    toon 4. ``same_as``/``aliases.yaml`` worden opgelost.
    """
    src = Path(source)
    if not src.is_file():
        raise FileNotFoundError(f"VSA-bron niet gevonden: {src}")
    if src.suffix.lower() != ".vsa":
        raise TemplateLibraryError(
            f"verwacht .vsa, kreeg {src.suffix!r}",
            code="VSA-MVSA-EXT",
        )

    raw = src.read_text(encoding="utf-8")
    fm, body = restore_vsa(raw)
    meta, _ = parse_vsa_frontmatter(fm + body)
    norm_body, _ = ensure_stanza_stars(body)
    vsa_text = fm + norm_body

    tpl_name = template
    if tpl_name is None or not str(tpl_name).strip():
        # Frontmatter ``template:`` wint; anders soort/toon/bron uit meta/pad.
        fm_tpl = meta.get("template")
        if fm_tpl not in (None, ""):
            tpl_name = str(fm_tpl)
        else:
            bron_u = None
            bron = meta.get("bron")
            if isinstance(bron, dict):
                bron_u = bron.get("uitgangspunt")
            elif isinstance(bron, str):
                bron_u = bron
            tpl_name = infer_template_id(
                soort=meta.get("soort") or meta.get("genre"),
                toon=meta.get("toon") or meta.get("tone"),
                bron=str(bron_u).lower() if bron_u else None,
                path=src,
                library_root=library_root,
            )

    resolved = load_resolved_template(tpl_name, library_root=library_root)

    mapped = map_vsa_to_template(
        resolved.doc,
        vsa_text,
        source=src.name,
        melody_voice=melody_voice,
    )

    title = meta.get("title") or meta.get("titel") or src.stem
    if tempo is None:
        tempo_i = _tempo_from_meta(meta)
    else:
        tempo_i = int(tempo)

    if resolved.formula_id != resolved.canonical_id:
        tpl_label = (
            f"{resolved.path.parent.name}/template.yaml "
            f"({resolved.canonical_id} -> formule {resolved.formula_id})"
        )
    else:
        tpl_label = (
            f"{resolved.path.parent.name}/template.yaml "
            f"({resolved.canonical_id})"
        )

    vo = resolved.doc.get("voice_oct") or DEFAULT_VOICE_OCT
    oct_vals = {
        "S": int(vo.get("S", 0)),
        "A": int(vo.get("A", 0)),
        "T": int(vo.get("T", -1)),
        "B": int(vo.get("B", -1)),
    }
    oct_line = (
        f"@oct S={oct_vals['S']} A={oct_vals['A']} "
        f"T={oct_vals['T']} B={oct_vals['B']}"
    )
    # Schrijfoctaven voor ag-vsa-tokens (T5) volgen template voice_oct.
    _VOICE_OCT.clear()
    _VOICE_OCT.update(oct_vals)

    # resolved.doc is al de formule (same_as samengevoegd) — cycle/tone/final.
    formula = resolved.doc
    fm_out = ""
    if include_frontmatter:
        # Feitelijk = formule met frasen; opgegeven = ruwe CLI/FM/infer-string.
        asked = resolved.requested_raw or tpl_name
        fm_out = clean_emit_frontmatter(
            meta,
            template_id=resolved.formula_id,
            template_opgegeven=str(asked) if asked else None,
        )
    text, warnings = emit_mapped_document(
        mapped,
        do=str(formula["do"]),
        mode=str(formula.get("mode", "major")),
        title=str(title),
        source_path=str(src).replace("\\", "/"),
        template_path=tpl_label,
        frontmatter=fm_out,
        vsa_body_comment=(
            _vsa_body_as_comment(body) if include_vsa_comment else ""
        ),
        tempo=tempo_i,
        oct_line=oct_line,
        cycle_len=cycle_length_for_emit(formula),
        with_sections=emit_sections_enabled(formula),
        final_id=str(formula.get("final") or "laatste"),
    )

    out_path: Path | None = None
    if output is not None:
        out_path = Path(output)
    elif write:
        out_path = src.with_suffix(".mvsa")

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8", newline="\n")

    return VsaMvsaResult(
        text=text,
        warnings=warnings,
        resolved=resolved,
        phrase_ids=[pid for pid, _ in mapped],
        source_path=src,
        output_path=out_path,
    )
