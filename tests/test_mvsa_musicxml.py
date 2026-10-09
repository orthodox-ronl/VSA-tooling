"""Tests for mvsa → MusicXML export."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from vsa.mvsa_musicxml import (
    MvsaExportError,
    _resolve_slot,
    _voice_resolver,
    export_mvsa_to_musicxml,
)
from vsa.mvsa_parse import StickyContext, parse_l_positions, parse_mvsa
from vsa.mvsa_validate import MvsaValidationError
from vsa.pitch_resolver import PitchResolver

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "mvsa"
INTOCHT = EXAMPLES / "kleine-intocht-zondag-hemelum.mvsa"
INTOCHT_SCHETS = EXAMPLES / "test-kleine-intocht-zondag-hemelum.mvsa"
ALLELUIA = EXAMPLES / "alleluia-toon-8.mvsa"


def _part_pitches(xml: str, part_id: str) -> list[tuple[str, str, str]]:
    marker = f'<part id="{part_id}">'
    body = xml.split(marker)[1].split("</part>")[0]
    return re.findall(
        r"<step>(\w)</step>(?:<alter>(-?\d)</alter>)?<octave>(\d)</octave>",
        body,
    )


def _part_lyrics(xml: str, part_id: str) -> list[tuple[str, str]]:
    marker = f'<part id="{part_id}">'
    body = xml.split(marker)[1].split("</part>")[0]
    return re.findall(r"<syllabic>(\w+)</syllabic><text>([^<]*)</text>", body)


def _all_pitches(xml: str) -> dict[str, list[tuple[str, str, str]]]:
    return {pid: _part_pitches(xml, pid) for pid in ("P1", "P2", "P3", "P4")}


def test_parse_l_recite_parens_and_melisma():
    pos = parse_l_positions("(Al-le-lu-ia,) al-le lu_&-&-&_ i_")
    assert pos[0].recite is True
    assert pos[0].syllables == ["Al", "le", "lu", "ia,"]
    assert pos[0].elms == []
    assert any(len(p.elms) == 4 for p in pos)


def test_parse_l_hyphen_after_recite_is_word_link():
    alone = parse_l_positions("(Al-le-lu-ia, Al-le-lu-ia, Al)-")
    assert len(alone) == 1
    assert alone[0].recite is True
    assert alone[0].elms == []  # bare '-' after ) is not ELM

    dangling_in = parse_l_positions("(Al-le-lu-ia, Al-le-lu-ia, Al-)")
    assert dangling_in[0].elms == []
    assert dangling_in[0].syllables[-1] == "Al"

    cont = parse_l_positions("(Al-le-lu-ia, Al-le-lu-ia, Al)-le-lu_&-&-&_ i_ a__")
    assert cont[0].recite is True
    assert cont[0].syllables[-1] == "Al"
    assert cont[1].syllables == ["le"]
    assert cont[1].continues_word is True
    assert cont[2].syllables == ["lu"]
    assert cont[2].continues_word is True
    assert cont[2].elms == ["_", "-", "-", "_"]


def test_parse_l_recite_optional_elm():
    pos = parse_l_positions("(Zoon van God)_")
    assert pos[0].recite is True
    assert pos[0].syllables == ["Zoon", "van", "God"]
    assert pos[0].elms == ["_"]
    assert pos[0].links == [False, False]


def test_parse_l_punct_after_elm_and_hyphen_continue():
    pos = parse_l_positions("Komt_, Chris_-tus_,")
    assert pos[0].syllables == ["Komt,"]
    assert pos[1].syllables == ["Chris"]
    assert pos[2].syllables == ["tus,"]
    assert pos[2].continues_word is True


def test_parse_l_recite_spaces_between_words():
    pos = parse_l_positions("(laat ons aan-bid-den voor)")
    assert len(pos) == 1
    assert pos[0].recite is True
    assert pos[0].syllables == ["laat", "ons", "aan", "bid", "den", "voor"]
    assert pos[0].links == [False, False, True, True, False]


def test_resolve_scientific_ignores_oct():
    ctx = StickyContext(do="F4", mode="major", oct={"B": -1})
    resolver = _voice_resolver(ctx, "B")
    p = _resolve_slot("g3", resolver, ctx, "B")
    assert (p.step, p.octave, p.alter) == ("G", 3, 0.0)


def test_resolve_degree_octave_then_sharp():
    ctx = StickyContext(do="F4", mode="major")
    resolver = _voice_resolver(ctx, "T")
    p = _resolve_slot("so-#", resolver, ctx, "T")
    assert (p.step, p.octave, p.alter) == ("C", 4, 1.0)


def test_resolve_degree_sharp_then_octave():
    ctx = StickyContext(do="F4", mode="major")
    resolver = _voice_resolver(ctx, "T")
    p = _resolve_slot("so#-", resolver, ctx, "T")
    assert (p.step, p.octave, p.alter) == ("C", 4, 1.0)


def test_resolve_letter_do_octave():
    ctx = StickyContext(do="F4", mode="major", oct={"B": -1})
    resolver = _voice_resolver(ctx, "B")
    p = _resolve_slot("g", resolver, ctx, "B")
    assert (p.step, p.octave, p.alter) == ("G", 3, 0.0)


def test_resolve_hold_dash():
    ctx = StickyContext(do="G4", mode="major")
    resolver = PitchResolver.from_metadata({"do": "G4", "mode": "major"})
    first = _resolve_slot("d4", resolver, ctx, "T")
    held = _resolve_slot("-", resolver, ctx, "T", last_pitch=first)
    assert held == first


def test_absolute_note_syncs_ehm_cursor():
    """After ``a``, EHM ``/`` ``\\`` steps from la (A), not from stale do (F)."""
    ctx = StickyContext(do="F4", mode="major")
    resolver = _voice_resolver(ctx, "S")
    assert str(_resolve_slot("a", resolver, ctx, "S")) == "A4"
    assert (
        str(_resolve_slot("-", resolver, ctx, "S", last_pitch=resolver.current_pitch))
        == "A4"
    )
    assert str(_resolve_slot("/", resolver, ctx, "S")) == "Bb4"
    assert str(_resolve_slot("\\", resolver, ctx, "S")) == "A4"


def test_vredeslitanie_bar_anchor_ok():
    text = (EXAMPLES / "1a-vredeslitanie.mvsa").read_text(encoding="utf-8")
    from vsa.mvsa_validate import validate_mvsa_text

    assert validate_mvsa_text(text) == []


def test_export_vredeslitanie_emits_repeat_barlines():
    """``|:`` / ``:|`` → MusicXML forward/backward repeats (Coria speelt die af)."""
    text = (EXAMPLES / "1a-vredeslitanie.mvsa").read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(text, layout="playback")
    p1 = xml.split('<part id="P1">')[1].split("</part>")[0]
    assert 'location="left"' in p1
    assert 'direction="forward"' in p1
    assert 'direction="backward"' in p1
    assert "heavy-light" in p1
    assert re.search(
        r'<barline location="right">\s*<bar-style>light-heavy</bar-style>\s*'
        r'<repeat direction="backward"\s*/>\s*</barline>',
        p1,
    )
    # Leidende ``|:`` → geen lege voorafgaande maat; forward op de eerste inhoudsmaat.
    measures = re.findall(r"<measure\b[^>]*>.*?</measure>", p1, flags=re.S)
    assert len(measures) >= 2
    # De herhaal-blokmaat (met forward) bevat lyrics/noten, geen pure rust-maat ervoor.
    forward_ms = [m for m in measures if 'direction="forward"' in m]
    assert forward_ms
    assert all("<lyric>" in m or "<pitch>" in m for m in forward_ms)
    # Partituur: :| blijft light-heavy + backward (niet “opgewaardeerd” weg
    # door een volgende @tekst), zodat MuseScore de herhaalpunten toont.
    partituur = export_mvsa_to_musicxml(text, layout="partituur")
    assert 'direction="forward"' in partituur
    assert re.search(
        r'<barline location="right">\s*<bar-style>light-heavy</bar-style>\s*'
        r'<repeat direction="backward"\s*/>\s*</barline>',
        partituur,
    )


def test_leading_repeat_start_bar_on_first_content_measure():
    """``|: Heer … :|`` → start_bar, geen lege maat vóór de inhoud."""
    text = """\
@do F4
@mode major
L: |: a_ b_ :|
S: |: do re :|
A: |: do re :|
T: |: do re :|
B: |: do re :|
"""
    doc = parse_mvsa(text)
    assert [d.severity for d in doc.diagnostics if d.severity == "error"] == []
    sys0 = doc.sections[0].systems[0]
    assert len(sys0.measures) == 1
    assert sys0.measures[0].start_bar == "|:"
    assert sys0.measures[0].final_bar == ":|"
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    p1 = xml.split('<part id="P1">')[1].split("</part>")[0]
    measures = re.findall(r"<measure\b[^>]*>.*?</measure>", p1, flags=re.S)
    assert len(measures) == 1
    assert 'direction="forward"' in measures[0]
    assert 'direction="backward"' in measures[0]


def test_export_section_end_with_repeat():
    """``:||`` = sectie-einde (light-light) én backward-repeat."""
    text = """\
@do F4
@mode major
L: a_ b_ :||
S: do re :||
A: do re :||
T: do re :||
B: do re :||
"""
    xml = export_mvsa_to_musicxml(text, layout="playback")
    assert re.search(
        r'<barline location="right">\s*<bar-style>light-light</bar-style>\s*'
        r'<repeat direction="backward"\s*/>\s*</barline>',
        xml,
    )


def test_satb_layout_preserves_repeat_barlines():
    """MSCZ↔MXL layout-pass mag ``<repeat>`` niet strippen."""
    from vsa.musicxml_satb_layout import (
        ensure_partituur_musicxml,
        ensure_playback_musicxml,
    )

    text = (EXAMPLES / "1a-vredeslitanie.mvsa").read_text(encoding="utf-8")
    playback = export_mvsa_to_musicxml(text, layout="playback")
    partituur = ensure_partituur_musicxml(playback)
    assert 'direction="forward"' in partituur
    assert 'direction="backward"' in partituur
    back = ensure_playback_musicxml(partituur)
    assert 'direction="forward"' in back
    assert 'direction="backward"' in back
    assert back.count('<part id="') == 4


def test_export_allows_eof_without_double_bar():
    """EOF sluit de sectie; export faalt niet alleen door ontbrekende ||."""
    xml = export_mvsa_to_musicxml(
        "@do F4\n@mode major\n@sectie x\nL: a_ |\nS: do |\nA: do |\nT: do |\nB: do |\n"
    )
    assert '<part id="P1">' in xml


def test_export_rejects_invalid():
    with pytest.raises(MvsaValidationError):
        export_mvsa_to_musicxml("@sectie x\nL: a_ b_ |\nS: do |\n")


def test_export_intocht_schets_a():
    text = INTOCHT_SCHETS.read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(text, section_id="schets-a-bladcijfer")
    assert xml.count("<part id=") == 4
    assert '<part id="P1">' in xml
    s = _part_pitches(xml, "P1")
    b = _part_pitches(xml, "P4")
    assert s[0] == ("B", "-1", "4")  # bb4
    assert b[0] == ("G", "", "3")  # g3
    assert xml.split('<part id="P1">')[1].split("</part>")[0].count("<measure") == 4
    lyrics = _part_lyrics(xml, "P1")
    assert ("single", "Komt,") in lyrics
    assert ("begin", "Chris") in lyrics
    assert ("end", "tus,") in lyrics
    # Recite (Zoon van God)_ → één noot per lettergreep (leesbaarheid R1–R2)
    assert ("single", "Zoon") in lyrics
    assert ("single", "van") in lyrics
    assert ("single", "God") in lyrics
    assert ("single", "Zoon van God") not in lyrics
    assert ("begin", "aan") in lyrics
    assert ("middle", "bid") in lyrics
    assert ("end", "den") in lyrics
    # Coria: lyrics op elke part
    for pid in ("P1", "P2", "P3", "P4"):
        assert ("single", "Komt,") in _part_lyrics(xml, pid)
    body = xml.split('<part id="P1">')[1].split("</part>")[0]
    assert 'lyric number="2"' not in body
    # Recite zonder ELM → kwart; (Zoon van God)_ → half
    assert body.count("<type>half</type>") >= 1
    assert "<part-name>Soprano</part-name>" in xml
    assert "<type>breve</type>" not in body


def test_playback_piano_midi_on_all_parts():
    """Canonieke Coria-MXL: piano op elke stempartij (checklist M8)."""
    text = INTOCHT_SCHETS.read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(text, section_id="schets-a-bladcijfer")
    root = ET.fromstring(xml.split('dtd">', 1)[-1])
    score_parts = root.findall(".//score-part")
    assert len(score_parts) == 4
    for i, sp in enumerate(score_parts, start=1):
        sound = sp.find("score-instrument/instrument-sound")
        assert sound is not None and sound.text == "keyboard.piano.grand"
        midi = sp.find("midi-instrument")
        assert midi is not None
        assert midi.findtext("midi-program") == "1"
        assert midi.findtext("midi-channel") == str(i)
    # Partituur-layout heeft geen MIDI (leesblad, geen Coria-playback).
    partituur = export_mvsa_to_musicxml(
        text, section_id="schets-a-bladcijfer", layout="partituur"
    )
    assert "midi-instrument" not in partituur
    assert "instrument-sound" not in partituur


def test_export_partituur_layout_two_staves():
    text = INTOCHT_SCHETS.read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(
        text, section_id="schets-a-bladcijfer", layout="partituur"
    )
    assert xml.count('<part id="') == 2
    assert "<part-name></part-name>" in xml
    assert "Soprano" not in xml
    # Lyrics alleen op SA (P1), niet op TB (P2)
    assert ("single", "Komt,") in _part_lyrics(xml, "P1")
    assert _part_lyrics(xml, "P2") == []
    p1 = xml.split('<part id="P1">')[1].split("</part>")[0]
    # Twee voices + stokrichting (geen akkoordstem)
    assert "<chord/>" not in p1
    assert "<voice>1</voice>" in p1
    assert "<voice>2</voice>" in p1
    assert "<stem>up</stem>" in p1
    assert "<stem>down</stem>" in p1
    assert "<backup>" in p1
    # Lange recite (≥6): 1-(n-2)-1 — stokloos midden + spacers (notehead none).
    # MusicXML: midden = metrische randduur (geen type=breve — MuseScore-breedte).
    # ||O||-kop + play=0 op spacers volgt in MSCZ-postprocess (S8/R3).
    assert "<stem>none</stem>" in p1
    assert "<notehead>none</notehead>" in p1
    assert '<note print-object="no"' not in p1
    assert "<type>breve</type>" not in p1
    # Eerste lettergreep van lange recite blijft zichtbare randnoot
    assert ("begin", "laat") in _part_lyrics(xml, "P1") or (
        "single",
        "laat",
    ) in _part_lyrics(xml, "P1")
    # Melisma lu: extender + slur-boog op eerste→laatste noot
    assert "<extend/>" in p1
    assert '<slur type="start"' in p1
    assert '<slur type="stop"' in p1
    # Sectie-einde || → dubbele maatstreep (ook als dit de laatste maat is)
    assert "light-light" in xml
    assert "light-heavy" not in xml


def test_export_playback_no_recite_collapse():
    """Coria/playback: elke recite-lettergreep een noot; geen breve-collapse."""
    text = INTOCHT_SCHETS.read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(text, section_id="schets-a-bladcijfer")
    body = xml.split('<part id="P1">')[1].split("</part>")[0]
    assert "<type>breve</type>" not in body
    assert '<note print-object="no"' not in body
    assert ("single", "Zoon") in _part_lyrics(xml, "P1")
    # Melisma-extend blijft; slurs/notations gaan eraf in Coria-sanitize.
    assert "<extend" in body


def test_export_alleluia_toon1_melisma_slur_and_collapse():
    """le.&.: S verschillend → slur; A zelfde hoogte → samentrekken tot kwart."""
    text = (EXAMPLES / "alleluia-toon-1.mvsa").read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    p1 = xml.split('<part id="P1">')[1].split("</part>")[0]
    assert "<stem>up</stem>" in p1
    assert "<stem>down</stem>" in p1
    assert "<backup>" in p1
    # S melisma f&g (of -&/): slur + extend
    assert "<text>le</text><extend/>" in p1
    assert '<slur type="start"' in p1
    assert '<slur type="stop"' in p1
    assert p1.count('<slur type="start"') == p1.count('<slur type="stop"')


def test_partituur_collapses_same_pitch_melisma():
    text = """\
@do F4
@mode major

@sectie demo
L: le.&. ||
S: -&/ ||
A: -&- ||
T: -&/ ||
B: -&- ||
"""
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    p1 = xml.split('<part id="P1">')[1].split("</part>")[0]
    # Voice 2 (A): twee achtsten op dezelfde toon → één kwart
    # Zoek na backup de voice-2 noten
    after = p1.split("<backup>")[1]
    assert after.count("<voice>2</voice>") == 1
    assert "<type>quarter</type>" in after
    assert after.count("<type>eighth</type>") == 0
    # Voice 1 (S): twee verschillende hoogten → twee achtsten + slur
    before = p1.split("<backup>")[0]
    assert before.count("<voice>1</voice>") == 2
    assert before.count("<type>eighth</type>") == 2


def test_playback_collapses_same_pitch_melisma():
    """MXL/Coria: same-pitch binnen één lettergreep → één noot (niet heraanslaan)."""
    text = """\
@do F4
@mode major

@sectie demo
L: lu-&- ia_ ||
S: bb&bb a ||
A: d&d d ||
T: bb&bb a ||
B: g&g g ||
"""
    xml = export_mvsa_to_musicxml(text, layout="playback")
    p1 = xml.split('<part id="P1">')[1].split("</part>")[0]
    # bb&bb (twee kwarten) → één half; daarna a half
    assert p1.count("<type>half</type>") == 2
    assert p1.count("<type>quarter</type>") == 0
    assert "<text>lu</text>" in p1
    assert "<text>ia</text>" in p1


def test_playback_preserves_dotted_melisma_slots_trisagion_god():
    """``God_.&_.`` met g4&a4 → twee gepunte halven (niet half+kwart×2).

    Partituur/MSCZ mag I1 half+kwart met ties houden; playback niet splitten
    want Coria stript ties en zou dan heraanslaan.
    """
    from xml.etree import ElementTree as ET

    text = (EXAMPLES / "trisagion-8a-slav-hemelum.mvsa").read_text(
        encoding="utf-8-sig"
    )
    playback = export_mvsa_to_musicxml(text, layout="playback")
    root = ET.fromstring(playback)
    p1 = root.find("./part[@id='P1']")
    assert p1 is not None
    m1 = p1.find("./measure[@number='1']")
    assert m1 is not None
    god_notes: list[ET.Element] = []
    collecting = False
    for note in m1.findall("note"):
        lyric = note.find("lyric")
        if lyric is not None and (lyric.findtext("text") or "") == "God":
            collecting = True
            god_notes = [note]
            continue
        if collecting:
            if lyric is not None and lyric.findtext("text"):
                break
            god_notes.append(note)
    assert len(god_notes) == 2
    for note in god_notes:
        assert note.findtext("type") == "half"
        assert note.find("dot") is not None
        assert note.findtext("duration") == "12"

    partituur = export_mvsa_to_musicxml(text, layout="partituur")
    proot = ET.fromstring(partituur)
    # Stem SA voice 1 in partituur: God still I1-split with ties
    pp1 = proot.find("./part[@id='P1']")
    assert pp1 is not None
    m1p = pp1.find("./measure[@number='1']")
    assert m1p is not None
    body = ET.tostring(m1p, encoding="unicode")
    assert "<text>God</text>" in body
    assert 'type="start"' in body  # tie start (I1 pack)
    assert body.count("<type>quarter</type>") >= 1
    assert body.count("<type>half</type>") >= 2


def test_playback_ksl_svyaty_melisma_not_fake_quarter():
    """ksl ``Свя-тый_.&-&_.`` op T (d4&d4&d4): één noot van 7 tellen, niet type=quarter.

    Coria toont ``<type>``; duration=28 met type=quarter zag eruit als twee kwarten.
    """
    from xml.etree import ElementTree as ET

    text = (EXAMPLES / "trisagion-8a-slav-hemelum.mvsa").read_text(
        encoding="utf-8-sig"
    )
    playback = export_mvsa_to_musicxml(text, layout="playback")
    root = ET.fromstring(playback)
    p3 = root.find("./part[@id='P3']")
    assert p3 is not None
    found = False
    for measure in p3.findall("measure"):
        notes = [n for n in measure.findall("note") if n.find("rest") is None]
        texts = []
        for note in notes:
            lyr = note.find("lyric")
            texts.append(lyr.findtext("text") if lyr is not None else None)
        # De _.&-&_. -maat: alleen Свя + тый (daarna Bez in de volgende maat).
        if texts[:2] != ["Свя", "тый"]:
            continue
        if len(texts) >= 3 and texts[2]:
            continue  # Свя-тый_. Бо… of Креп…
        svya, tyj = notes[0], notes[1]
        assert svya.findtext("type") == "quarter"
        assert svya.findtext("duration") == "4"
        assert tyj.findtext("duration") == "28"
        assert tyj.findtext("type") == "whole"
        assert len(tyj.findall("dot")) == 2
        found = True
        break
    assert found, "ksl Свя-тый_.&-&_. measure not found on T (P3)"


def test_alleluia_toon1_playback_lu_bb_is_half():
    """Alleluia toon 1 maat 1: melisma ``lu`` op Bb&Bb → één Bb-halve."""
    text = (EXAMPLES / "alleluia-toon-1.mvsa").read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(text, layout="playback", section_id="1")
    p1 = xml.split('<part id="P1">')[1].split("</part>")[0]
    # Geen twee opeenvolgende Bb-kwarten meer voor lu
    assert "<text>lu</text>" in p1
    # Na collapse: één Bb half met lyric lu (extend niet nodig bij single packed)
    from xml.etree import ElementTree as ET

    root = ET.fromstring(f"<score>{p1}</score>")
    notes = []
    for note in root.iter("note"):
        pitch = note.find("pitch")
        if pitch is None:
            continue
        lyr = note.find("lyric")
        notes.append(
            (
                pitch.findtext("step"),
                pitch.findtext("alter"),
                note.findtext("type"),
                lyr.findtext("text") if lyr is not None else None,
            )
        )
    bb_lu = [
        n for n in notes if n[0] == "B" and n[1] == "-1" and n[3] == "lu"
    ]
    assert len(bb_lu) == 1
    assert bb_lu[0][2] == "half"


def test_partituur_long_same_pitch_melisma_never_emits_breve():
    """I1: geen breve. I2: acht kwarten → whole+whole met ties."""
    text = """\
@do F4
@mode major
@sectie x
L: a_&_&_&_&_&_&_&_ ||
S: g&g&g&g&g&g&g&g ||
A: d&d&d&d&d&d&d&d ||
T: bb&bb&bb&bb&bb&bb&bb&bb ||
B: g&g&g&g&g&g&g&g ||
"""
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert "<type>breve</type>" not in xml
    assert "<duration>32</duration>" not in xml
    assert "<duration>12</duration>" not in xml
    # I2: tie-keten, geen slur (pure same-pitch)
    assert '<tie type="start"/>' in xml
    assert '<tied type="start"/>' in xml
    assert xml.count("<type>whole</type>") >= 2
    p1 = xml.split('<part id="P1">')[1].split("</part>")[0]
    before = p1.split("<backup>")[0]
    assert '<slur type="start"' not in before


def test_playback_long_same_pitch_hold_uses_tie_chain_not_fake_quarter():
    """Acht kwarten same-pitch: geen type=quarter + duration=32 (MuseScore-chops).

    Playback prefereert één noot ≤ 28; overflow → I2 whole+whole.
    ``finalize_coria_musicxml`` stript ``<tie>`` (Coria); MuseScore speelt
    dan wel heraanslag op de whole-grenzen, maar niet elke kwart.
    """
    text = """\
@do F4
@mode major
@sectie x
L: a_&_&_&_&_&_&_&_ ||
S: g&g&g&g&g&g&g&g ||
A: d&d&d&d&d&d&d&d ||
T: c&c&c&c&c&c&c&c ||
B: g&g&g&g&g&g&g&g ||
"""
    xml = export_mvsa_to_musicxml(text, layout="playback")
    assert "<type>breve</type>" not in xml
    # Geen mismatch: duration=32 bij type=quarter zou MuseScore elke kwart
    # opnieuw aanslaan (bas-F “op tel 2” in gemengde piano-preview).
    assert "<duration>32</duration>" not in xml
    p3 = xml.split('<part id="P3">')[1].split("</part>")[0]
    assert p3.count("<type>whole</type>") == 4
    assert p3.count("<duration>16</duration>") == 4
    assert "<type>quarter</type>" not in p3
    # Partituur-export behoudt wel ties (geen Coria-sanitize).
    partituur = export_mvsa_to_musicxml(text, layout="partituur")
    assert '<tie type="start"/>' in partituur
    assert '<tied type="start"/>' in partituur


def test_alleluia_toon_2_partituur_no_breve_type():
    text = (EXAMPLES / "alleluia-toon-2.mvsa").read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert "<type>breve</type>" not in xml


def test_alleluia_toon_2_tb_same_pitch_uses_ties_not_choppy_untied():
    """I2: T/B long same-pitch holds → ties; stem duration sums stay equal."""
    text = (EXAMPLES / "alleluia-toon-2.mvsa").read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert '<tie type="start"/>' in xml
    assert '<tied type="start"/>' in xml
    p2 = xml.split('<part id="P2">')[1].split("</part>")[0]
    # Bass staff: both voices same total duration
    for v in (1, 2):
        notes = [
            n
            for n in re.findall(r"<note>(.*?)</note>", p2, re.S)
            if f"<voice>{v}</voice>" in n
        ]
        assert sum(int(re.search(r"<duration>(\d+)</duration>", n).group(1)) for n in notes) == sum(
            int(re.search(r"<duration>(\d+)</duration>", n).group(1))
            for n in re.findall(r"<note>(.*?)</note>", p2, re.S)
            if "<voice>1</voice>" in n
        )


def test_playback_partituur_layout_roundtrip_transform():
    from vsa.musicxml_satb_layout import (
        ensure_partituur_musicxml,
        ensure_playback_musicxml,
    )

    text = INTOCHT_SCHETS.read_text(encoding="utf-8")
    playback = export_mvsa_to_musicxml(text, section_id="schets-a-bladcijfer")
    partituur = ensure_partituur_musicxml(playback)
    assert partituur.count('<part id="') == 2
    assert "Soprano" not in partituur
    back = ensure_playback_musicxml(partituur)
    assert back.count('<part id="') == 4
    assert "<part-name>Soprano</part-name>" in back
    assert ("single", "Komt,") in _part_lyrics(back, "P1")
    assert ("single", "Komt,") in _part_lyrics(back, "P4")
    root = ET.fromstring(back.split('dtd">', 1)[-1])
    sounds = [
        el.text
        for el in root.findall(".//score-instrument/instrument-sound")
    ]
    assert sounds == ["keyboard.piano.grand"] * 4
    channels = [
        el.text for el in root.findall(".//midi-instrument/midi-channel")
    ]
    assert channels == ["1", "2", "3", "4"]


def test_export_alleluia_so_sharp():
    text = (EXAMPLES / "test-alleluia-toon-8.mvsa").read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(text, section_id="schets1-doremi")
    tenor = _part_pitches(xml, "P3")
    assert tenor[-1] == ("C", "1", "4")  # so-#


def test_export_unknown_section():
    text = INTOCHT_SCHETS.read_text(encoding="utf-8")
    with pytest.raises(MvsaExportError, match="sectie"):
        export_mvsa_to_musicxml(text, section_id="bestaat-niet")


def test_export_unknown_height_token_has_line():
    """Export-fout noemt regelnummer (niet alleen bestandsnaam via CLI)."""
    text = """\
@do F4
@mode major

@sectie demo
L: a_ b_ ||
S: do x ||
A: do - ||
T: do - ||
B: do - ||
"""
    # Bypass validate: force resolve path by using a token validate also rejects.
    # Export raises MvsaValidationError first when parse diagnostics have errors.
    with pytest.raises(MvsaValidationError) as caught:
        export_mvsa_to_musicxml(text)
    hoogte = [d for d in caught.value.diagnostics if d.code == "MVSA-HOOGTE"]
    assert hoogte
    assert hoogte[0].line == 6
    assert "x" in hoogte[0].message


def test_resolve_slot_unknown_includes_line():
    resolver = PitchResolver.from_metadata({"do": "F4", "mode": "major"})
    ctx = StickyContext(do="F4", mode="major")
    with pytest.raises(MvsaExportError) as caught:
        _resolve_slot("_", resolver, ctx, "S", line=13, marker="S")
    assert caught.value.line == 13
    assert "'_'" in str(caught.value)
    assert str(caught.value).startswith("S:")


def test_parse_sticky_oct():
    doc = parse_mvsa(
        "@do G4\n@mode major\n@oct T=-1 B=-1\n"
        "@sectie x\nL: a_ ||\nS: g4 ||\nA: e4 ||\nT: d ||\nB: g ||\n"
    )
    assert doc.sections[0].systems[0].context.oct == {"T": -1, "B": -1}


def test_line_ehm_is_beginanker():
    """``S-:`` applies the same start as ``@start S=-``."""
    with_label = export_mvsa_to_musicxml(
        "@do F4\n@mode major\n"
        "@sectie x\nL: a_ ||\nS-: / ||\nA-: - ||\nT-: - ||\nB-: - ||\n"
    )
    with_start = export_mvsa_to_musicxml(
        "@do F4\n@mode major\n@start S=- A=- T=- B=-\n"
        "@sectie x\nL: a_ ||\nS: / ||\nA: - ||\nT: - ||\nB: - ||\n"
    )
    assert _all_pitches(with_label) == _all_pitches(with_start)


def test_vsa_mode_beginanker_uses_schrijf_do():
    """``@oct`` shifts writing do; begin-EHM and EHM tokens count from there."""
    xml = export_mvsa_to_musicxml(
        "@do F4\n@mode major\n@oct T=-1 B=-1\n"
        "@sectie x\nL: a_ b_ ||\n"
        "S-: - / ||/\n"
        "A-: - - ||-\n"
        "T-: - / ||/\n"
        "B-: - - ||-\n"
    )
    pitches = _all_pitches(xml)
    # S writing do F4; T/B writing do F3
    assert pitches["P1"][0] == ("F", "", "4")  # S start
    assert pitches["P3"][0] == ("F", "", "3")  # T start on schrijf-do
    assert pitches["P4"][0] == ("F", "", "3")  # B start on schrijf-do
    assert pitches["P3"][1] == ("G", "", "3")  # T /


def test_alleluia_toon_1_tenor_not_c5():
    """Regression: eindblokken must respect @oct (tenor around C4, not C5)."""
    text = (EXAMPLES / "alleluia-toon-1.mvsa").read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(text, section_id="2")
    t = _part_pitches(xml, "P3")
    assert t
    assert all(int(oct_) <= 4 for _s, _a, oct_ in t)
    assert t[0] == ("C", "", "4")


def test_ag_without_digit_uses_do_octave():
    """a–g zonder cijfer deelt het do-octaaf: bij F4 is ``c`` = C5 (= so)."""
    xml = export_mvsa_to_musicxml(
        "@do F4\n@mode major\n"
        "@sectie x\nL: a_ b_ c_ ||\n"
        "S: Bb c a ||\n"
        "A: g g e ||\n"
        "T: d c a- ||\n"
        "B: g- e- f- ||\n"
    )
    assert _part_pitches(xml, "P1") == [
        ("B", "-1", "4"),
        ("C", "", "5"),
        ("A", "", "4"),
    ]
    # Met wetenschappelijk cijfer blijft c4 = C4.
    xml4 = export_mvsa_to_musicxml(
        "@do F4\n@mode major\n"
        "@sectie x\nL: a_ ||\nS: c4 ||\nA: g4 ||\nT: d4 ||\nB: g3 ||\n"
    )
    assert _part_pitches(xml4, "P1") == [("C", "", "4")]


def test_alleluia_toon_8_schets3_oct_ag_so_is_c5():
    """Referentieschets: na recite op Bb volgt ``c`` op C5 (niet C4)."""
    text = (EXAMPLES / "test-alleluia-toon-8.mvsa").read_text(encoding="utf-8")
    xml = export_mvsa_to_musicxml(
        text, layout="playback", section_id="schets3-oct-ag"
    )
    s = _part_pitches(xml, "P1")
    assert s[0] == ("B", "-1", "4")  # Bb recite
    assert s[9] == ("C", "", "5")  # c na recite


def test_export_allows_non_satb_stem_id_playback():
    xml = export_mvsa_to_musicxml(
        "@do F4\n@mode major\n@sectie x\nL: a_ ||\ncantus: c4 ||\n",
        layout="playback",
    )
    assert "<part-name>cantus</part-name>" in xml


def test_export_rejects_non_satb_stem_id_partituur():
    with pytest.raises(MvsaExportError, match="cantus"):
        export_mvsa_to_musicxml(
            "@do F4\n@mode major\n@sectie x\nL: a_ ||\ncantus: c4 ||\n",
            layout="partituur",
        )


def test_tekst_attaches_to_next_system_in_musicxml():
    text = """\
@do F4
@mode major
@sectie demo
@tekst "P: eerste cue"
L: a_ |
S: do |
A: do |
T: do |
B: do |
@tekst "P: tweede cue"
L: b_ ||
S: re ||
A: re ||
T: re ||
B: re ||
"""
    doc = parse_mvsa(text)
    assert [d.severity for d in doc.diagnostics if d.severity == "error"] == []
    assert doc.sections[0].systems[0].staff_texts == ["P: eerste cue"]
    assert doc.sections[0].systems[1].staff_texts == ["P: tweede cue"]

    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert 'words justify="left" default-x="0">P: eerste cue</words>' in xml
    assert 'words justify="left" default-x="0">P: tweede cue</words>' in xml
    # Geen verplichte MuseScore-systeembreuk vanuit @tekst.
    assert '<print new-system="yes"/>' not in xml
    # Mid-flow cue: dubbele streep + width; geen spacermaat / geen HBox.
    assert '<note print-object="no"' not in xml
    assert xml.count("<bar-style>light-light</bar-style>") >= 1
    # Alleen op de bovenste balk (P1), niet op TB (P2).
    p1 = xml.split('<part id="P1">')[1].split("</part>")[0]
    p2 = xml.split('<part id="P2">')[1].split("</part>")[0]
    assert "eerste cue" in p1 and "tweede cue" in p1
    assert "cue" not in p2
    assert "width=" in p1


def test_tekst_first_measure_has_no_cue_spacer():
    """Eerste maat begint een MuseScore-systeem → geen spacer vóór @tekst."""
    text = """\
@do F4
@mode major
@sectie demo
@tekst "P: alleen start"
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
"""
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert "alleen start" in xml
    assert '<note print-object="no"' not in xml
    assert '<print new-system="yes"/>' not in xml


def test_playback_inserts_pauze_after_double_bar_with_cue():
    text = """\
@do F4
@mode major
@sectie demo
@tekst "P: eerste"
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
@tekst "P: tweede"
L: b_ ||
S: re ||
A: re ||
T: re ||
B: re ||
"""
    xml = export_mvsa_to_musicxml(text, layout="playback")
    p1 = xml.split('<part id="P1">')[1].split("</part>")[0]
    assert "[PAUZE]" in p1
    # Geen @tekst-spacer op playback-pad.
    assert '<note print-object="no"' not in xml
    # Cue van de volgende maat staat op de pauzemaat.
    assert p1.index("P: tweede") < p1.index("[PAUZE]")
    # Één pauze (|| + @tekst mogen niet dubbel pauzeren).
    assert p1.count("[PAUZE]") == 1


def test_playback_inserts_pauze_before_midflow_tekst():
    """Mid-flow ``@tekst`` zonder ``||`` → zelfde ``[PAUZE]`` als sectie-einde."""
    text = """\
@do F4
@mode major
@tekst "P: eerste"
L: a_ |
S: do |
A: do |
T: do |
B: do |
@tekst "P: tweede"
L: b_ ||
S: re ||
A: re ||
T: re ||
B: re ||
"""
    xml = export_mvsa_to_musicxml(text, layout="playback")
    p1 = xml.split('<part id="P1">')[1].split("</part>")[0]
    assert p1.count("[PAUZE]") == 1
    assert p1.index("P: tweede") < p1.index("[PAUZE]")
    # Eerste cue: geen leidende pauze vóór maat 1.
    first_meas = p1.split("</measure>")[0]
    assert "[PAUZE]" not in first_meas
    assert "P: eerste" in first_meas


def test_playback_tekst_pauze_keeps_repeat_end():
    """``:|`` vóór mid-flow ``@tekst``: pauze én backward-repeat blijven."""
    text = """\
@do F4
@mode major
L: a_ |: b_ :|
S: do |: re :|
A: do |: re :|
T: do |: re :|
B: do |: re :|
@tekst "P: na herhaling"
L: c_ ||
S: mi ||
A: mi ||
T: mi ||
B: mi ||
"""
    xml = export_mvsa_to_musicxml(text, layout="playback")
    p1 = xml.split('<part id="P1">')[1].split("</part>")[0]
    assert "[PAUZE]" in p1
    assert 'direction="backward"' in p1
    assert 'direction="forward"' in p1
    assert p1.index("P: na herhaling") < p1.index("[PAUZE]")


def test_parse_tekst_escapes():
    from vsa.mvsa_validate import parse_tekst_argument

    assert parse_tekst_argument(r'"zeg \"hallo\""') == 'zeg "hallo"'
    assert parse_tekst_argument(r'"a\\b"') == "a\\b"
    assert parse_tekst_argument("niet-quoted") is None
    assert parse_tekst_argument('"open') is None


def test_title_composer_copyright_in_musicxml():
    text = """\
@title "(1a) Vredeslitanie"
@ondertitel "Litanie van de vrede"
@composer "Archimandriet Feofan"
@tekstdichter "tekst: liturgikon"
@arrangeur "bew. Hemelum"
@vertaler "NL-redactie"
@bron "Liturgikon, p.147-149"
@copyright "CC BY-SA 4.0 — test"
@tempo 72
@toon "1"
@taal "nl"
@do F4
@mode major
@sectie demo
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
"""
    doc = parse_mvsa(text)
    assert doc.title == "(1a) Vredeslitanie"
    assert doc.ondertitel == "Litanie van de vrede"
    assert doc.composer == "Archimandriet Feofan"
    assert doc.tekstdichter == "tekst: liturgikon"
    assert doc.arrangeur == "bew. Hemelum"
    assert doc.vertaler == "NL-redactie"
    assert doc.bron == "Liturgikon, p.147-149"
    assert doc.copyright == "CC BY-SA 4.0 — test"
    assert doc.tempo == 72
    assert doc.toon == "1"
    assert doc.taal == "nl"
    xml = export_mvsa_to_musicxml(text, title="bestandsnaam", layout="partituur")
    assert "<work-title>(1a) Vredeslitanie</work-title>" in xml
    assert "<movement-title>Litanie van de vrede</movement-title>" in xml
    assert "bestandsnaam" not in xml
    assert '<creator type="composer">Archimandriet Feofan</creator>' in xml
    assert '<creator type="lyricist">tekst: liturgikon</creator>' in xml
    assert '<creator type="arranger">bew. Hemelum</creator>' in xml
    assert '<creator type="translator">NL-redactie</creator>' in xml
    assert "<source>Liturgikon, p.147-149</source>" in xml
    assert "CC BY-SA 4.0 — test" in xml
    assert "<per-minute>72</per-minute>" in xml
    assert 'sound tempo="72"' in xml
    assert '<direction placement="above" print-object="no">' in xml
    assert xml.count("<per-minute>72</per-minute>") == 1
    assert 'miscellaneous-field name="tone">1</miscellaneous-field>' in xml
    playback = export_mvsa_to_musicxml(text, title="bestandsnaam", layout="playback")
    # Playback: geen <source> naast <encoding> (Coria); bron in miscellaneous-field.
    assert "<source>" not in playback
    assert 'miscellaneous-field name="bron">Liturgikon, p.147-149</miscellaneous-field>' in playback
    assert 'miscellaneous-field name="tone">1</miscellaneous-field>' in playback
    assert "<per-minute>72</per-minute>" in playback
    assert 'sound tempo="72"' in playback
    # Coria-sanitize stript layout-attrs (o.a. print-object); playback is audio.
    assert playback.count("<per-minute>72</per-minute>") == 1


def test_tempo_before_system_last_pending_wins_and_default_130():
    """Meerdere ``@tempo`` vóór hetzelfde systeem: laatste pending wint.

    Document-meta ``doc.tempo`` = eerste ``@tempo`` in het bestand (starttempo).
    """
    with_tempo = """\
@tempo 60
@tempo 90
@do F4
@mode major
@sectie demo
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
"""
    doc = parse_mvsa(with_tempo)
    assert doc.tempo == 60
    assert doc.sections[0].systems[0].tempo == 90
    xml = export_mvsa_to_musicxml(with_tempo, title="x", layout="partituur")
    assert "<per-minute>90</per-minute>" in xml
    assert "<per-minute>60</per-minute>" not in xml

    without = """\
@do F4
@mode major
@sectie demo
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
"""
    assert parse_mvsa(without).tempo is None
    bare = export_mvsa_to_musicxml(without, title="x", layout="playback")
    assert "<per-minute>130</per-minute>" in bare
    assert 'sound tempo="130"' in bare
    assert bare.count("<per-minute>130</per-minute>") == 1


def test_mid_score_tempo_emits_two_sound_tempos():
    """``@tempo`` vóór een later systeem → tweede ``sound tempo`` op die maat."""
    text = """\
@tempo 60
@do F4
@mode major
@sectie a
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
@tempo 90
@sectie b
L: b_ ||
S: re ||
A: re ||
T: re ||
B: re ||
"""
    doc = parse_mvsa(text)
    assert doc.tempo == 60
    assert doc.sections[0].systems[0].tempo == 60
    assert doc.sections[1].systems[0].tempo == 90

    for layout in ("partituur", "playback"):
        xml = export_mvsa_to_musicxml(text, title="x", layout=layout)
        assert xml.count("<per-minute>60</per-minute>") == 1
        assert xml.count("<per-minute>90</per-minute>") == 1
        assert 'sound tempo="60"' in xml
        assert 'sound tempo="90"' in xml
        # Eerste tempo vóór tweede in de score (bovenste part).
        assert xml.index('sound tempo="60"') < xml.index('sound tempo="90"')


def test_orphan_tempo_warns():
    text = """\
@do F4
@mode major
@sectie demo
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
@tempo 72
"""
    doc = parse_mvsa(text)
    assert any(
        d.code == "MVSA-TEMPO" and "zonder volgend" in d.message
        for d in doc.diagnostics
    )


def test_toon_alone_emits_identification_misc():
    text = """\
@toon "8"
@do F4
@mode major
@sectie demo
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
"""
    doc = parse_mvsa(text)
    assert doc.toon == "8"
    xml = export_mvsa_to_musicxml(text, title="x", layout="partituur")
    assert 'miscellaneous-field name="tone">8</miscellaneous-field>' in xml


def test_bron_optional_colon_accepted():
    """``@bron: "…"`` is equivalent to ``@bron "…"`` (YAML-achtige schrijfwijze)."""
    text = """\
@bron: "koormap Hemelum"
@do F4
@mode major
@sectie demo
L: a_ ||
S: do ||
A: do ||
T: do ||
B: do ||
"""
    doc = parse_mvsa(text)
    assert doc.bron == "koormap Hemelum"
    assert not [
        d for d in doc.diagnostics if d.code == "MVSA-DIRECTIVE" and "bron" in d.message
    ]
    partituur = export_mvsa_to_musicxml(text, layout="partituur")
    assert "<source>koormap Hemelum</source>" in partituur
    playback = export_mvsa_to_musicxml(text, layout="playback")
    assert "<source>" not in playback
    assert 'miscellaneous-field name="bron">koormap Hemelum</miscellaneous-field>' in playback


def test_mscz_newline_emits_new_system():
    text = """\
@do F4
@mode major
@sectie demo
L: a_ |
S: do |
A: do |
T: do |
B: do |
@mscz-newline
@tekst "P: cue op nieuw systeem"
L: b_ ||
S: re ||
A: re ||
T: re ||
B: re ||
"""
    doc = parse_mvsa(text)
    assert doc.sections[0].systems[0].mscz_newline is False
    assert doc.sections[0].systems[1].mscz_newline is True
    assert doc.sections[0].systems[1].staff_texts == ["P: cue op nieuw systeem"]

    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert xml.count('<print new-system="yes"/>') == 1
    # Met new-system geen cue-spacer nodig vóór de tweede maat.
    assert '<note print-object="no"' not in xml
    p1 = xml.split('<part id="P1">')[1].split("</part>")[0]
    measures = p1.split("<measure ")
    # [1]=eerste maat, [2]=tweede maat met new-system + cue
    assert "new-system" in measures[2]
    assert "P: cue op nieuw systeem" in measures[2]



def test_tekst_wraps_at_ellipsis_and_sets_width():
    from vsa.mvsa_musicxml import wrap_tekst_at_ellipsis, estimate_cue_width_tenths

    wrapped = wrap_tekst_at_ellipsis(
        "P: Onze Alheilige ... ons leven aan"
    )
    assert wrapped == "P: Onze Alheilige\n... ons leven aan"
    text = """\
@do F4
@mode major
@sectie demo
@tekst "P: Onze Alheilige ... ons leven aan"
L: a_ |
S: do |
A: do |
T: do |
B: do |
@tekst "P: kort"
L: b_ ||
S: re ||
A: re ||
T: re ||
B: re ||
"""
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert "P: Onze Alheilige" in xml
    assert "... ons leven aan" in xml
    assert "width=" in xml
    assert estimate_cue_width_tenths([wrapped]) >= 80


_SPEELPLAN_DEMO = """\
@do F4
@mode major
@speelplan 1, 2, 1, 2, 1, 3

@blok 1
L: a_ |
S: do |
A: do |
T: do |
B: do |

@blok 2
L: b_ |
S: re |
A: re |
T: re |
B: re |

@blok 3
L: c_ ||
S: mi ||
A: mi ||
T: mi ||
B: mi ||
"""


def test_speelplan_playback_expands_measures():
    xml = export_mvsa_to_musicxml(_SPEELPLAN_DEMO, layout="playback")
    # 6 blokken × 1 maat (+ possible [PAUZE] after ||).
    assert xml.count("<measure ") >= 6
    # Lyrics op alle 4 stemmen → 3×4 / 2×4 / 1×4.
    assert xml.count(">a</text>") == 12
    assert xml.count(">b</text>") == 8
    assert xml.count(">c</text>") == 4


def test_speelplan_playback_coda_shape_expands_no_jumps():
    """Playback blijft expand: geen Segno/Coda-markers bij coda-vormig plan."""
    text = """\
@do F4
@mode major
@speelplan 1, 2, 3, 2, 4

@blok 1
L: a_ |
S: do |
A: do |
T: do |
B: do |

@blok 2
L: b_ |
S: re |
A: re |
T: re |
B: re |

@blok 3
L: c_ |
S: mi |
A: mi |
T: mi |
B: mi |

@blok 4
L: d_ ||
S: fa ||
A: fa ||
T: fa ||
B: fa ||
"""
    xml = export_mvsa_to_musicxml(text, layout="playback")
    assert "<segno/>" not in xml
    assert "<coda/>" not in xml
    assert "To Coda" not in xml
    assert "D.S. al Coda" not in xml
    # Uitgeschreven: ≥5 plan-slots (parts × maten; eventueel [PAUZE] na ||).
    assert xml.count("<measure ") >= 10


def test_speelplan_partituur_volta_ab_ac():
    """``1,2,1,2,1,3`` → |: 1 |1,2. 2 :| 3. 3 (geen blok-ids, geen Speel:)."""
    xml = export_mvsa_to_musicxml(_SPEELPLAN_DEMO, layout="partituur")
    assert "Speel: 1-2-1-2-1-3" not in xml
    # Geen losse blok-id staff text (alleen lyrics a/b/c).
    assert ">1</text>" not in xml
    assert ">2</text>" not in xml
    assert ">3</text>" not in xml
    # Bladvorm: drie maten × 2 parts (geen expansie).
    assert xml.count("<measure ") == 6
    assert 'direction="forward"' in xml
    assert 'direction="backward"' in xml
    assert 'number="1,2"' in xml
    assert 'number="3"' in xml
    assert 'type="start"' in xml
    assert 'type="stop"' in xml
    assert ">a</text>" in xml
    assert ">b</text>" in xml
    assert ">c</text>" in xml


def test_speelplan_partituur_ds_al_fine_trisagion_shape():
    """``A B C D B C`` → segno op B, Fine op C, D.S. al Fine na D."""
    text = """\
@do F4
@mode major
@speelplan nls-1, nls-2, ksl, doxologie, nls-2, ksl

@blok nls-1
L: a_ |
S: do |
A: do |
T: do |
B: do |

@blok nls-2
L: b_ |
S: re |
A: re |
T: re |
B: re |

@blok ksl
L: c_ |
S: mi |
A: mi |
T: mi |
B: mi |

@blok doxologie
L: d_ ||
S: fa ||
A: fa ||
T: fa ||
B: fa ||
"""
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert "Speel:" not in xml
    assert "<segno/>" in xml
    assert ">Fine</words>" in xml
    assert ">D.S. al Fine</words>" in xml
    assert 'dalsegno="segno"' in xml
    # Compact: 4 blokken × 1 maat × 2 parts, geen expansie.
    assert xml.count("<measure ") == 8


def test_speelplan_partituur_ds_al_coda():
    """``1,2,3,2,4`` → Segno@2, To Coda@2, D.S. al Coda@3, Coda@4."""
    text = """\
@do F4
@mode major
@speelplan 1, 2, 3, 2, 4

@blok 1
L: a_ |
S: do |
A: do |
T: do |
B: do |

@blok 2
L: b_ |
S: re |
A: re |
T: re |
B: re |

@blok 3
L: c_ |
S: mi |
A: mi |
T: mi |
B: mi |

@blok 4
L: d_ ||
S: fa ||
A: fa ||
T: fa ||
B: fa ||
"""
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert "Speel:" not in xml
    assert "<segno/>" in xml
    assert ">To Coda</words>" in xml
    assert 'tocoda="coda"' in xml
    assert "<coda/>" in xml
    assert 'coda="coda"' in xml
    assert ">D.S. al Coda</words>" in xml
    assert 'dalsegno="segno"' in xml
    assert ">Fine</words>" not in xml
    # Compact: 4 blokken × 1 maat × 2 parts, geen expansie.
    assert xml.count("<measure ") == 8


def test_speelplan_partituur_dc_al_coda():
    """Vier bladblokken: D.C. al Coda (niet volta ``(a,b)×1+(a,c)``)."""
    text = """\
@do F4
@mode major
@speelplan intro, mid, bridge, intro, mid, coda

@blok intro
L: a_ |
S: do |
A: do |
T: do |
B: do |

@blok mid
L: b_ |
S: re |
A: re |
T: re |
B: re |

@blok bridge
L: c_ |
S: mi |
A: mi |
T: mi |
B: mi |

@blok coda
L: d_ ||
S: fa ||
A: fa ||
T: fa ||
B: fa ||
"""
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert "<segno/>" not in xml
    assert ">To Coda</words>" in xml
    assert ">D.C. al Coda</words>" in xml
    assert 'dacapo="yes"' in xml
    assert "<coda/>" in xml
    assert "<ending " not in xml
    # Compact: 4 blokken × 1 maat × 2 parts.
    assert xml.count("<measure ") == 8


def test_speelplan_partituur_expand_fallback():
    """Onherleidbaar plan → uitgeschreven bladvorm (klinkende volgorde)."""
    text = """\
@do F4
@mode major
@speelplan 1, 3, 2, 1

@blok 1
L: a_ |
S: do |
A: do |
T: do |
B: do |

@blok 2
L: b_ |
S: re |
A: re |
T: re |
B: re |

@blok 3
L: c_ ||
S: mi ||
A: mi ||
T: mi ||
B: mi ||
"""
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert "<ending " not in xml
    assert "<segno/>" not in xml
    assert "<coda/>" not in xml
    # 1,3,2,1 → vier maten × 2 parts
    assert xml.count("<measure ") == 8
    # Lyrics alleen op SA (P1): a,c,b,a
    assert xml.count(">a</text>") == 2
    assert xml.count(">b</text>") == 1
    assert xml.count(">c</text>") == 1
