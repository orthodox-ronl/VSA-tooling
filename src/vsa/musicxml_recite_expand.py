"""Feathered recite (partituur ``||O||``) → één kwart per lettergreep (M10).

Port van VSA-demo ``export_mscz_coria_mxl.expand_recite_notes`` voor gebruik
in ``mscz mxl`` / ``normalize_playback_musicxml``.
"""

from __future__ import annotations

import copy
from xml.etree import ElementTree as ET

from .musicxml_satb_layout import local
from .syllabify import hyphenate_dutch_word


def _text(el: ET.Element | None) -> str:
    return (el.text or "").strip() if el is not None else ""


def _child(el: ET.Element, name: str) -> ET.Element | None:
    for c in el:
        if local(c.tag) == name:
            return c
    return None


def _children(el: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in el if local(c.tag) == name]


def _music_parts(root: ET.Element) -> list[ET.Element]:
    return [el for el in root if local(el.tag) == "part"]


def _is_rest(note: ET.Element) -> bool:
    return _child(note, "rest") is not None


def _is_chord(note: ET.Element) -> bool:
    return _child(note, "chord") is not None


def _lyric_elements(note: ET.Element) -> list[ET.Element]:
    return _children(note, "lyric")


def _syllables_from_lyric_text(raw: str) -> list[tuple[str, str]]:
    """Split lyric text to (syllable, syllabic) pairs."""
    tokens: list[str] = []
    for word in raw.split():
        word = word.strip()
        if not word:
            continue
        if "-" in word:
            tokens.extend(p for p in word.split("-") if p)
        else:
            hyphenated = hyphenate_dutch_word(word)
            parts = [p for p in hyphenated.split("-") if p]
            tokens.extend(parts if parts else [word])
    n = len(tokens)
    out: list[tuple[str, str]] = []
    for i, tok in enumerate(tokens):
        if n <= 1:
            syll = "single"
        elif i == 0:
            syll = "begin"
        elif i == n - 1:
            syll = "end"
        else:
            syll = "middle"
        out.append((tok, syll))
    return out


def _is_feathered_recite(note: ET.Element) -> bool:
    """Basispartituur ``||O||`` na MuseScore: breve-kop, long/maxima, of stokloos."""
    nh = _child(note, "notehead")
    if nh is not None and _text(nh).lower() == "breve":
        return True
    ntype = _child(note, "type")
    type_s = _text(ntype) if ntype is not None else ""
    if type_s in {"long", "breve", "maxima"}:
        return True
    stem = _child(note, "stem")
    stem_none = stem is not None and _text(stem) == "none"
    lyrics = _lyric_elements(note)
    joined = (
        " ".join(_text(_child(ly, "text")) for ly in lyrics).strip() if lyrics else ""
    )
    multi = bool(joined) and (
        " " in joined or len(_syllables_from_lyric_text(joined)) > 1
    )
    if stem_none and type_s in {"half", "whole", "breve", "long"}:
        return True
    if multi and type_s in {"half", "whole", "breve", "long", "maxima"}:
        return True
    return False


def _quarter_duration(divisions: int) -> int:
    return max(1, divisions)


def _make_quarter_note(
    template: ET.Element,
    *,
    syl_text: str | None,
    syllabic: str,
    divisions: int,
) -> ET.Element:
    n = copy.deepcopy(template)
    for el in list(n):
        tag = local(el.tag)
        if tag in {"notehead", "dot", "time-modification", "beam", "notations"}:
            n.remove(el)
        elif tag == "lyric":
            n.remove(el)
        elif tag == "stem":
            el.text = "up"
        elif tag == "type":
            el.text = "quarter"
        elif tag == "duration":
            el.text = str(_quarter_duration(divisions))
    dur = _child(n, "duration")
    if dur is None:
        dur = ET.Element("duration")
        pitch = _child(n, "pitch")
        idx = list(n).index(pitch) + 1 if pitch is not None else 0
        n.insert(idx, dur)
    dur.text = str(_quarter_duration(divisions))
    typ = _child(n, "type")
    if typ is None:
        typ = ET.Element("type")
        n.append(typ)
    typ.text = "quarter"
    stem = _child(n, "stem")
    if stem is None:
        stem = ET.SubElement(n, "stem")
    stem.text = "up"
    if syl_text:
        ly = ET.SubElement(n, "lyric", number="1")
        ET.SubElement(ly, "syllabic").text = syllabic
        ET.SubElement(ly, "text").text = syl_text
    return n


def expand_recite_notes(root: ET.Element) -> int:
    """Feathered partituur notes → one quarter per syllable (Coria playback)."""
    expanded = 0
    for part in _music_parts(root):
        divisions = 1
        for measure in _children(part, "measure"):
            attrs = _child(measure, "attributes")
            if attrs is not None:
                div = _child(attrs, "divisions")
                if div is not None and _text(div).isdigit():
                    divisions = int(_text(div))
            q = _quarter_duration(divisions)
            new_children: list[ET.Element] = []
            changed = False
            for el in list(measure):
                if local(el.tag) != "note" or _is_rest(el) or _is_chord(el):
                    new_children.append(el)
                    continue
                if not _is_feathered_recite(el):
                    new_children.append(el)
                    continue
                lyrics = _lyric_elements(el)
                raw = " ".join(_text(_child(ly, "text")) for ly in lyrics).strip()
                dur_el = _child(el, "duration")
                dur = (
                    int(_text(dur_el))
                    if dur_el is not None and _text(dur_el).isdigit()
                    else q
                )
                n_by_dur = max(1, dur // q)
                if raw:
                    syllables = _syllables_from_lyric_text(raw)
                    if len(syllables) <= 1:
                        syllables = [(raw, "single")]
                else:
                    syllables = [(None, "single")] * n_by_dur
                for syl_text, syllabic in syllables:
                    new_children.append(
                        _make_quarter_note(
                            el,
                            syl_text=syl_text,
                            syllabic=syllabic,
                            divisions=divisions,
                        )
                    )
                expanded += 1
                changed = True
            if changed:
                for c in list(measure):
                    measure.remove(c)
                for c in new_children:
                    measure.append(c)
    return expanded
