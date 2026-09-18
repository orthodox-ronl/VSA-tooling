"""
Renders a validated VSA :class:`~vsa.ast.Document` to a MusicXML
``<score-partwise>`` string.

Pipeline (spec §8.2):

1. Read ``do``, ``mode``, ``tempo`` from block metadata.
2. Build a :class:`~vsa.pitch_resolver.PitchResolver` for the scale.
3. Walk the AST nodes in order:

   - :class:`~vsa.ast.PitchMarkerNode` (first) → set starting scale degree.
   - :class:`~vsa.ast.ScopeNode` → expand to notes with pitch + duration.
   - :class:`~vsa.ast.ControlTokenNode` → emit barline / end measure.
   - :class:`~vsa.ast.TextNode` → scanned for inline barline markers
     (``//``, ``/``, ``*``); remaining words become reciting-tone notes.

4. Emit ``<score-partwise>`` XML via :mod:`xml.etree.ElementTree`.

Barline recognition
-------------------
Both formal control tokens (``ControlTokenNode``) and inline text markers
(``//``, ``/``, ``*`` in ``TextNode`` content) produce barlines. This
supports the legacy ``//`` and ``*`` notation used in practice ``.vsa``
files before the bracketed ``[/]`` / ``[*]`` syntax was introduced.

Unscopped text → reciting notes
---------------------------------
Whitespace-separated tokens in ``TextNode`` content that are not barline
markers become reciting-tone notes on the current pitch.  Configure via
the ``reciting-mode`` metadata parameter (see §8.2.7 in the spec).

Hyphens within a token (``mel-se``) split into separate quarter notes with
MusicXML ``syllabic`` begin/middle/end and a trailing hyphen on the lyric
text where conventional (``mel-`` + ``se``).

Export profiles
---------------
Two profiles are available via ``musicxml-profile`` metadata (default:
``playback``).  See spec §8.2.11 and ``docs/guides/musicxml-export.md``.

Control-token mapping (configurable)
-------------------------------------
The default mapping for formal ``ControlTokenNode`` tokens is::

    "[*]"  → barline  (single)
    "[/]"  → barline  (single)
    "[/?]" → barline  (single)
    "[*?]" → barline  (single)

Pass a custom ``token_map`` dict to :class:`MusicXMLRenderer` to override.
The inline text patterns ``//``, ``/``, ``*`` are always recognised
regardless of this mapping.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import date
from typing import Any

from .ast import ControlTokenNode, Document, PitchMarkerNode, ScopeNode, TextNode
from .duration_model import UnknownELM, elm_to_duration
from .music import Duration, Pitch
from .pitch_resolver import PitchResolver, key_fifths

# Number of MusicXML divisions per quarter note.
_DIVISIONS = 4

# Default control-token → barline style mapping (formal bracket notation).
_DEFAULT_TOKEN_MAP: dict[str, str] = {
    "[*]":  "barline",
    "[/]":  "barline",
    "[/?]": "barline",
    "[*?]": "barline",
}

# Inline text patterns recognised inside TextNode content (legacy notation).
_TEXT_BARLINE_PATTERNS: dict[str, str] = {
    "//": "double-barline",
    "/":  "barline",
    "*":  "barline",
}

# How many consecutive whitespace tokens trigger whole-note reciting mode
# (only when reciting-mode is "whole").
_RECITING_WHOLE_THRESHOLD = 4

# reciting-mode metadata values
RECITING_MODE_QUARTERS = "quarters"
RECITING_MODE_WHOLE = "whole"

# MusicXML export profiles (see spec §8.2.11).
MUSICXML_PROFILE_PLAYBACK = "playback"
MUSICXML_PROFILE_ENGRAVING = "engraving"

# Note types that may be beamed when consecutive in a measure (playback profile).
_BEAMABLE_TYPES = frozenset({"16th", "eighth"})

# Tokens that contain no word characters (letters / digits) are treated as
# punctuation and attached to the preceding word rather than producing their
# own note.  Barline markers (*  /  //) are already checked first, so they
# are not caught here.
_PUNCT_ONLY_RE = re.compile(r"^\W+$")


class MusicXMLExportError(ValueError):
    """Raised when the document cannot be exported to MusicXML."""


class MusicXMLRenderer:
    """Renders a :class:`~vsa.ast.Document` to a MusicXML string.

    :param metadata: Effective block metadata (``do``, ``mode``, ``tempo``,
        ``duration-model``, optionally ``meter``, ``identificatie.*``,
        ``typografie.*`` keys).
    :param token_map: Maps formal ``ControlTokenNode`` token strings to
        barline action strings.  Supported actions: ``"barline"`` (single),
        ``"double-barline"``.
    :param explicit_keys: Set of metadata keys that were explicitly provided
        (not just default values).  When given, the tempo direction is only
        emitted if ``"tempo"`` is in this set.  Pass ``None`` (default) to
        always emit the tempo direction.
    """

    def __init__(
        self,
        metadata: dict[str, str] | None = None,
        token_map: dict[str, str] | None = None,
        explicit_keys: set[str] | None = None,
    ):
        self._meta = metadata or {}
        self._token_map = token_map if token_map is not None else dict(_DEFAULT_TOKEN_MAP)
        self._explicit_keys = explicit_keys

    @property
    def _profile(self) -> str:
        return self._meta.get("musicxml-profile", MUSICXML_PROFILE_PLAYBACK)

    @property
    def _is_playback(self) -> bool:
        return self._profile == MUSICXML_PROFILE_PLAYBACK

    # ── Public API ──────────────────────────────────────────────────────────

    def render(self, document: Document) -> str:
        """Return a MusicXML string for *document*."""
        root = self._build_score(document)
        ET.indent(root, space="  ")
        xml_bytes = ET.tostring(root, encoding="unicode", xml_declaration=False)
        header = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE score-partwise PUBLIC\n'
            '  "-//Recordare//DTD MusicXML 4.0 Partwise//EN"\n'
            '  "http://www.musicxml.org/dtds/partwise.dtd">\n'
        )
        return header + xml_bytes + "\n"

    # ── Score construction ──────────────────────────────────────────────────

    def _build_score(self, document: Document) -> ET.Element:
        score = ET.Element("score-partwise", version="4.0")

        self._add_work(score)
        self._add_identification(score)
        if not self._is_playback:
            self._add_defaults(score)
        self._add_part_list(score)

        part = ET.SubElement(score, "part", id="P1")
        self._fill_part(part, document)

        return score

    def _add_defaults(self, score: ET.Element) -> None:
        """Add page and system layout defaults to reduce inter-system spacing."""
        defaults = ET.SubElement(score, "defaults")

        scaling = ET.SubElement(defaults, "scaling")
        ET.SubElement(scaling, "millimeters").text = "6.99"
        ET.SubElement(scaling, "tenths").text = "40"

        page_layout = ET.SubElement(defaults, "page-layout")
        ET.SubElement(page_layout, "page-height").text = "1683"
        ET.SubElement(page_layout, "page-width").text = "1190"
        page_margins = ET.SubElement(page_layout, "page-margins", type="both")
        ET.SubElement(page_margins, "left-margin").text = "56"
        ET.SubElement(page_margins, "right-margin").text = "56"
        ET.SubElement(page_margins, "top-margin").text = "56"
        ET.SubElement(page_margins, "bottom-margin").text = "113"

        system_layout = ET.SubElement(defaults, "system-layout")
        sys_margins = ET.SubElement(system_layout, "system-margins")
        ET.SubElement(sys_margins, "left-margin").text = "0"
        ET.SubElement(sys_margins, "right-margin").text = "0"
        ET.SubElement(system_layout, "system-distance").text = "40"
        ET.SubElement(system_layout, "top-system-distance").text = "40"

        staff_layout = ET.SubElement(defaults, "staff-layout")
        ET.SubElement(staff_layout, "staff-distance").text = "55"

        self._add_typography_fonts(defaults)

    def _add_typography_fonts(self, defaults: ET.Element) -> None:
        """Emit MusicXML font defaults from ``typografie.*`` metadata."""
        _FONT_SPECS = (
            ("lyric-font", "typografie.lyric-font", "typografie.lyric-size"),
            ("music-font", "typografie.music-font", "typografie.music-size"),
            ("word-font", "typografie.word-font", "typografie.word-size"),
        )
        for tag, family_key, size_key in _FONT_SPECS:
            family = self._meta.get(family_key, "").strip()
            size = self._meta.get(size_key, "").strip()
            if not family and not size:
                continue
            attrs: dict[str, str] = {}
            if family:
                attrs["font-family"] = family
            if size:
                attrs["font-size"] = size
            ET.SubElement(defaults, tag, **attrs)

    def _add_work(self, score: ET.Element) -> None:
        title = self._meta.get("identificatie.title", "")
        if title:
            work = ET.SubElement(score, "work")
            ET.SubElement(work, "work-title").text = title

        subtitle = self._meta.get("identificatie.subtitle", "")
        if subtitle:
            ET.SubElement(score, "movement-title").text = subtitle

    def _add_identification(self, score: ET.Element) -> None:
        ident = ET.SubElement(score, "identification")

        for key, mxml_type in [
            ("identificatie.composer", "composer"),
            ("identificatie.lyricist", "lyricist"),
        ]:
            value = self._meta.get(key, "")
            if value:
                ET.SubElement(ident, "creator", type=mxml_type).text = value

        rights = self._meta.get("identificatie.rights", "")
        if rights:
            ET.SubElement(ident, "rights").text = rights

        encoding = ET.SubElement(ident, "encoding")
        ET.SubElement(encoding, "software").text = "vsa-tool"
        ET.SubElement(encoding, "encoding-date").text = str(date.today())

        if self._is_playback:
            for element, attribute in (
                ("accidental", None),
                ("beam", None),
                ("print", "new-page"),
                ("print", "new-system"),
                ("stem", None),
            ):
                attrs: dict[str, str] = {"element": element, "type": "yes"}
                if element == "print":
                    attrs["type"] = "no"
                    if attribute:
                        attrs["attribute"] = attribute
                ET.SubElement(encoding, "supports", **attrs)

        # Liturgical tone stored as miscellaneous
        tone = self._meta.get("identificatie.tone", self._meta.get("tone", ""))
        if tone:
            misc = ET.SubElement(ident, "miscellaneous")
            ET.SubElement(misc, "miscellaneous-field", name="tone").text = str(tone)

    def _add_part_list(self, score: ET.Element) -> None:
        part_list = ET.SubElement(score, "part-list")
        score_part = ET.SubElement(part_list, "score-part", id="P1")
        part_name = self._meta.get("part-name", "Vocal").strip() or "Vocal"
        ET.SubElement(score_part, "part-name").text = part_name

        if not self._is_playback:
            return

        instrument_id = "P1-I1"
        midi_sound = self._meta.get("midi-sound", "keyboard.piano.grand").strip()
        midi_channel = self._meta.get("midi-channel", "1").strip() or "1"
        midi_program = self._meta.get("midi-program", "1").strip() or "1"
        midi_volume = self._meta.get("midi-volume", "78.7402").strip() or "78.7402"
        midi_pan = self._meta.get("midi-pan", "0").strip() or "0"

        score_instrument = ET.SubElement(
            score_part, "score-instrument", id=instrument_id
        )
        ET.SubElement(score_instrument, "instrument-name")
        if midi_sound:
            ET.SubElement(score_instrument, "instrument-sound").text = midi_sound

        ET.SubElement(score_part, "midi-device", id=instrument_id, port="1")

        midi_instrument = ET.SubElement(score_part, "midi-instrument", id=instrument_id)
        ET.SubElement(midi_instrument, "midi-channel").text = midi_channel
        ET.SubElement(midi_instrument, "midi-program").text = midi_program
        ET.SubElement(midi_instrument, "volume").text = midi_volume
        ET.SubElement(midi_instrument, "pan").text = midi_pan

    # ── Part / measure filling ───────────────────────────────────────────────

    def _fill_part(self, part: ET.Element, document: Document) -> None:
        do_str = self._meta.get("do", "F4")
        mode = self._meta.get("mode", "major")
        tempo_str = self._meta.get("tempo", "120")
        duration_model = self._meta.get("duration-model", "default")
        meter_str = self._meta.get("meter", "")
        reciting_mode = self._meta.get("reciting-mode", RECITING_MODE_QUARTERS)
        language = self._meta.get(
            "identificatie.language", self._meta.get("language", "")
        )

        try:
            resolver = PitchResolver.from_metadata({"do": do_str, "mode": mode})
        except Exception as exc:
            raise MusicXMLExportError(str(exc)) from exc

        # Apply the first pitch marker to set the starting degree.
        for node in document.nodes:
            if isinstance(node, PitchMarkerNode):
                resolver.apply_start_marker(node.ehm)
                break

        # ── Collect events ───────────────────────────────────────────────────
        # Flat sequence of {"type": "note"|"barline", ...} dicts.
        _Note = dict[str, Any]
        events: list[_Note] = []

        # Unscopped whitespace tokens accumulated between barlines / scopes.
        pending_tokens: list[str] = []

        def flush_pending_words() -> None:
            """Emit reciting-tone note(s) for buffered unscopped text."""
            if not pending_tokens:
                return
            reciting_pitch = resolver.current_pitch  # last sounding, incl. alter

            if (
                reciting_mode == RECITING_MODE_WHOLE
                and len(pending_tokens) >= _RECITING_WHOLE_THRESHOLD
            ):
                events.append({
                    "type": "note",
                    "pitch": reciting_pitch,
                    "duration": Duration(note_type="whole"),
                    "text": " ".join(pending_tokens),
                    "syllabic": "single",
                    "is_melisma": False,
                })
            else:
                for text, syllabic in _syllables_from_tokens(pending_tokens):
                    events.append({
                        "type": "note",
                        "pitch": reciting_pitch,
                        "duration": Duration(note_type="quarter"),
                        "text": text,
                        "syllabic": syllabic,
                        "is_melisma": False,
                    })
            pending_tokens.clear()

        for node in document.nodes:
            if isinstance(node, PitchMarkerNode):
                continue  # already handled above

            if isinstance(node, TextNode):
                # Split text by whitespace; classify each token.
                for token in node.text.split():
                    if token in _TEXT_BARLINE_PATTERNS:
                        flush_pending_words()
                        events.append({
                            "type": "barline",
                            "action": _TEXT_BARLINE_PATTERNS[token],
                        })
                    elif _PUNCT_ONLY_RE.match(token):
                        # Pure punctuation: attach to the preceding token
                        # rather than generating a standalone reciting note.
                        if pending_tokens:
                            pending_tokens[-1] += token
                        elif events and events[-1]["type"] == "note":
                            events[-1]["text"] += token
                        # else: punctuation at start of measure — discard
                    else:
                        pending_tokens.append(token)
                continue

            if isinstance(node, ControlTokenNode):
                flush_pending_words()
                action = self._token_map.get(node.token, "barline")
                events.append({"type": "barline", "action": action})
                continue

            if isinstance(node, ScopeNode):
                flush_pending_words()

                hm = node.height_modifier or ["~"]
                lm = node.length_modifier or ["~"]

                if len(hm) > 1 and len(lm) == 1:
                    lm = lm * len(hm)
                if len(lm) > 1 and len(hm) == 1:
                    hm = hm * len(lm)

                n_positions = len(hm)
                is_melisma = n_positions > 1

                for i, (ehm, elm) in enumerate(zip(hm, lm)):
                    pitch = resolver.resolve_ehm(ehm)
                    try:
                        duration = elm_to_duration(elm, model=duration_model)
                    except UnknownELM as exc:
                        raise MusicXMLExportError(str(exc)) from exc

                    events.append({
                        "type": "note",
                        "pitch": pitch,
                        "duration": duration,
                        # Text only on the first note of a melisma.
                        "text": node.text if (not is_melisma or i == 0) else "",
                        "is_melisma": is_melisma,
                        "melisma_first": is_melisma and i == 0,
                        "melisma_middle": is_melisma and 0 < i < n_positions - 1,
                        "melisma_last": is_melisma and i == n_positions - 1,
                    })

        flush_pending_words()  # flush any trailing unscopped words

        # ── Split events into measures at barline events ──────────────────────
        # Each entry: (notes, right_barline) where right_barline is one of
        # "regular", "light-light" (double), "light-heavy" (final).
        measures: list[tuple[list[_Note], str]] = []
        current: list[_Note] = []

        def _close_measure(bar_style: str) -> None:
            nonlocal current
            if current:
                measures.append((current, bar_style))
                current = []
            elif measures and bar_style == "light-light":
                # Double barline with no pending notes: upgrade previous measure.
                prev_notes, _prev_style = measures[-1]
                measures[-1] = (prev_notes, "light-light")

        for ev in events:
            if ev["type"] == "barline":
                if ev["action"] == "double-barline":
                    _close_measure("light-light")
                else:
                    _close_measure("regular")
            else:
                current.append(ev)

        if current:
            measures.append((current, "light-heavy"))
        elif measures:
            # Trailing barline with no notes: mark previous as final.
            prev_notes, prev_style = measures[-1]
            if prev_style != "light-heavy":
                measures[-1] = (prev_notes, "light-heavy")

        if not measures:
            measures = [([], "light-heavy")]

        fifths = key_fifths(resolver._do, mode)

        # ── Emit measures ─────────────────────────────────────────────────────
        for measure_idx, (notes, bar_style) in enumerate(measures):
            m = ET.SubElement(part, "measure", number=str(measure_idx + 1))

            if measure_idx == 0:
                self._add_attributes(m, resolver, mode, meter_str)
                self._add_tempo_direction(m, tempo_str)

            # Maatgebonden voortekens: hersteltekens (natural) na kruis/mol.
            measure_alters: dict[str, int] = {}
            note_events = _assign_beams(notes) if self._is_playback else notes
            for ev in note_events:
                self._add_note(m, ev, language, fifths=fifths, measure_alters=measure_alters)

            if bar_style != "regular" or not self._is_playback:
                bl = ET.SubElement(m, "barline", location="right")
                ET.SubElement(bl, "bar-style").text = bar_style

    def _add_attributes(
        self,
        measure: ET.Element,
        resolver: PitchResolver,
        mode: str,
        meter_str: str,
    ) -> None:
        attrs = ET.SubElement(measure, "attributes")
        ET.SubElement(attrs, "divisions").text = str(_DIVISIONS)

        key_el = ET.SubElement(attrs, "key")
        fifths = key_fifths(resolver._do, mode)
        ET.SubElement(key_el, "fifths").text = str(fifths)

        if meter_str:
            try:
                beats, beat_type = meter_str.split("/")
                time_el = ET.SubElement(attrs, "time")
                ET.SubElement(time_el, "beats").text = beats.strip()
                ET.SubElement(time_el, "beat-type").text = beat_type.strip()
            except ValueError:
                pass  # ignore malformed meter

        clef = ET.SubElement(attrs, "clef")
        ET.SubElement(clef, "sign").text = "G"
        ET.SubElement(clef, "line").text = "2"

    def _add_tempo_direction(self, measure: ET.Element, tempo_str: str) -> None:
        # Only emit a visible tempo mark when tempo was explicitly specified.
        # When explicit_keys is None (untracked callers) we always emit.
        if self._explicit_keys is not None and "tempo" not in self._explicit_keys:
            return

        try:
            bpm = int(float(tempo_str))
        except (ValueError, TypeError):
            bpm = 120

        direction = ET.SubElement(measure, "direction", placement="above")
        dt = ET.SubElement(direction, "direction-type")
        metro = ET.SubElement(dt, "metronome", parentheses="no")
        ET.SubElement(metro, "beat-unit").text = "quarter"
        ET.SubElement(metro, "per-minute").text = str(bpm)
        ET.SubElement(direction, "sound", tempo=str(bpm))

    def _add_note(
        self,
        measure: ET.Element,
        ev: dict[str, Any],
        language: str,
        *,
        fifths: int = 0,
        measure_alters: dict[str, int] | None = None,
    ) -> None:
        note_el = ET.SubElement(measure, "note")

        pitch: Pitch = ev["pitch"]
        duration: Duration = ev["duration"]

        p_el = ET.SubElement(note_el, "pitch")
        ET.SubElement(p_el, "step").text = pitch.step
        if pitch.alter != 0.0:
            ET.SubElement(p_el, "alter").text = _format_alter(pitch.alter)
        ET.SubElement(p_el, "octave").text = str(pitch.octave)

        ET.SubElement(note_el, "duration").text = str(duration.divisions_value)

        if self._is_playback:
            ET.SubElement(note_el, "voice").text = "1"
            ET.SubElement(note_el, "type").text = duration.note_type
            for _ in range(duration.dots):
                ET.SubElement(note_el, "dot")
        else:
            ET.SubElement(note_el, "type").text = duration.note_type
            for _ in range(duration.dots):
                ET.SubElement(note_el, "dot")

        # Zichtbaar voorteken / herstelteken t.o.v. toonsoort + eerdere noten
        # in dezelfde maat (MusicXML <accidental>, o.a. natural na kruis/mol).
        if measure_alters is not None:
            accidental_name = _visible_accidental(
                pitch.step, pitch.alter, fifths, measure_alters
            )
            if accidental_name is not None:
                ET.SubElement(note_el, "accidental").text = accidental_name

        if self._is_playback:
            ET.SubElement(note_el, "stem").text = "up"
            for beam_number, beam_type in ev.get("beams", []):
                ET.SubElement(note_el, "beam", number=str(beam_number)).text = beam_type

        melisma_first = ev.get("melisma_first", False)
        melisma_middle = ev.get("melisma_middle", False)
        melisma_last = ev.get("melisma_last", False)

        # Slur arc spanning the full melisma (start on first, stop on last note).
        if melisma_first or melisma_last:
            notations = ET.SubElement(note_el, "notations")
            if melisma_first:
                slur_attrs: dict[str, str] = {
                    "type": "start",
                    "number": "1",
                    "placement": "above",
                }
                if self._is_playback:
                    slur_attrs["orientation"] = "over"
                ET.SubElement(notations, "slur", **slur_attrs)
            if melisma_last:
                ET.SubElement(notations, "slur", type="stop", number="1")

        # Lyric
        text = ev.get("text", "")

        if melisma_first and text:
            lyric_attrs: dict[str, str] = {"number": "1"}
            if language and not self._is_playback:
                lyric_attrs["xml:lang"] = language
            lyric = ET.SubElement(note_el, "lyric", **lyric_attrs)
            ET.SubElement(lyric, "syllabic").text = "single"
            ET.SubElement(lyric, "text").text = text
            if self._is_playback:
                ET.SubElement(lyric, "extend")
            else:
                ET.SubElement(lyric, "extend", type="start")

        elif melisma_middle and not self._is_playback:
            lyric = ET.SubElement(note_el, "lyric", number="1")
            ET.SubElement(lyric, "extend", type="continue")

        elif melisma_last and not self._is_playback:
            lyric = ET.SubElement(note_el, "lyric", number="1")
            ET.SubElement(lyric, "extend", type="stop")

        elif text:
            lyric_attrs = {"number": "1"}
            if language and not self._is_playback:
                lyric_attrs["xml:lang"] = language
            lyric = ET.SubElement(note_el, "lyric", **lyric_attrs)
            ET.SubElement(lyric, "syllabic").text = ev.get("syllabic", "single")
            ET.SubElement(lyric, "text").text = text
            if ev.get("extend"):
                ET.SubElement(lyric, "extend")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _syllables_from_token(token: str) -> list[tuple[str, str]]:
    """Split one unscopped token into (lyric text, syllabic) pairs.

    A hyphen divides syllables: ``mel-se`` → ``("mel-", "begin")`` +
    ``("se", "end")``.  Tokens without a hyphen stay ``("word", "single")``.
    """
    parts = [part for part in token.split("-") if part]
    if len(parts) <= 1:
        return [(token, "single")]
    result: list[tuple[str, str]] = []
    for i, part in enumerate(parts):
        if i == 0:
            result.append((part + "-", "begin"))
        elif i == len(parts) - 1:
            result.append((part, "end"))
        else:
            result.append((part + "-", "middle"))
    return result


def _syllables_from_tokens(tokens: list[str]) -> list[tuple[str, str]]:
    """Expand whitespace tokens into a flat syllable list."""
    syllables: list[tuple[str, str]] = []
    for token in tokens:
        syllables.extend(_syllables_from_token(token))
    return syllables


def _format_alter(alter: float) -> str:
    """Format an alter value: integers without decimal point."""
    return str(int(alter)) if alter == int(alter) else f"{alter:.1f}"


# Circle-of-fifths order: sharps FCGDAEB, flats BEADGCF.
_SHARP_ORDER = ("F", "C", "G", "D", "A", "E", "B")

_ALTER_ACCIDENTAL_MUSICXML: dict[int, str] = {
    0: "natural",
    1: "sharp",
    -1: "flat",
    2: "double-sharp",
    -2: "double-flat",
}


def _key_alter_for_step(step: str, fifths: int) -> int:
    """Alter implied by the key signature for a diatonic step (0 if none)."""
    if fifths > 0:
        return 1 if step in _SHARP_ORDER[:fifths] else 0
    if fifths < 0:
        flat_order = tuple(reversed(_SHARP_ORDER))
        return -1 if step in flat_order[:(-fifths)] else 0
    return 0


def _alter_as_int(alter: float) -> int:
    """Convert a Pitch.alter float to the nearest MusicXML integer alter."""
    return int(alter) if alter == int(alter) else int(round(alter))


def _visible_accidental(
    step: str,
    alter: float,
    fifths: int,
    measure_alters: dict[str, int],
) -> str | None:
    """Return MusicXML accidental name if a visible sign is required.

    Tracks measure-local accidentals so a return to the key-signature pitch
    after a sharp/flat emits ``natural`` (herstelteken) on the same step.
    Updates *measure_alters* when a new alter becomes active for *step*.
    """
    sounding = _alter_as_int(alter)
    written = measure_alters.get(step, _key_alter_for_step(step, fifths))
    if sounding == written:
        return None
    measure_alters[step] = sounding
    return _ALTER_ACCIDENTAL_MUSICXML.get(sounding)


def _assign_beams(notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a shallow copy of *notes* with ``beams`` filled for playback export."""
    result = [dict(note) for note in notes]
    index = 0
    while index < len(result):
        note_type = result[index]["duration"].note_type
        if note_type not in _BEAMABLE_TYPES:
            index += 1
            continue

        group_start = index
        while (
            index < len(result)
            and result[index]["duration"].note_type in _BEAMABLE_TYPES
        ):
            index += 1
        group_end = index
        if group_end - group_start < 2:
            continue

        for pos, note_idx in enumerate(range(group_start, group_end)):
            if pos == 0:
                beam_pos = "begin"
            elif pos == group_end - group_start - 1:
                beam_pos = "end"
            else:
                beam_pos = "continue"

            beams: list[tuple[int, str]] = [(1, beam_pos)]
            if result[note_idx]["duration"].note_type == "16th":
                beams.append((2, beam_pos))
            result[note_idx]["beams"] = beams

    return result
