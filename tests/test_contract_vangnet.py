"""Vangnet (migratiestap 5): golden- en contracttests per contract-id.

Elke test noemt zijn contract-id in naam en docstring. Bronnen:
``docs/formats/canonical-checklists.md`` (K, M, S) en
``docs/formats/mscz-leesbaarheid.md`` (R). Een bekend regressiegeval faalt
in precies één test hieronder.

Dekking
-------
- M5a  same-pitch melisma (MXL playback): collapse tot één noot, lange keten I2-ties
- K2   sync tekst ↔ toon: twee lettergrepen same-pitch blijven twee noten
- K3   melisma-lyrics: lyric op eerste noot, ``<extend/>``, geen lyric op vervolgnoot
- M10  recite-playback: elke lettergreep een klinkende noot, geen breve
- S2   partituur: twee balken (SA in G-sleutel, TB in F-sleutel)
- S4   partituur: stokrichting S/T omhoog, A/B omlaag
- S13/R7  MSCZ-postprocess: same-pitch Tie-keten wordt één compacte noot
"""

from __future__ import annotations

from xml.etree import ElementTree as ET

from vsa.mscz_partituur import _collapse_same_pitch_tie_runs
from vsa.mvsa_musicxml import export_mvsa_to_musicxml

_HEAD = "@do F4\n@mode major\n@oct S=0 A=0 T=-1 B=-1\n@sectie x\n"


def _root(xml: str) -> ET.Element:
    root = ET.fromstring(xml)
    for el in root.iter():
        el.tag = el.tag.rsplit("}", 1)[-1]
    return root


def _part(xml: str, part_id: str) -> ET.Element:
    for part in _root(xml).findall("part"):
        if part.get("id") == part_id:
            return part
    raise AssertionError(f"part {part_id} ontbreekt")


def _notes(part: ET.Element) -> list[dict]:
    out = []
    for note in part.iter("note"):
        pitch = note.find("pitch")
        lyric = note.find("lyric")
        out.append(
            {
                "step": None if pitch is None else pitch.findtext("step"),
                "type": note.findtext("type"),
                "duration": note.findtext("duration"),
                "lyric": None if lyric is None else lyric.findtext("text"),
                "extend": lyric is not None and lyric.find("extend") is not None,
                "voice": note.findtext("voice"),
                "stem": note.findtext("stem"),
            }
        )
    return out


# --- M5a ---------------------------------------------------------------------


def test_M5a_same_pitch_melisma_collapses_to_one_note_in_playback():
    """M5a: twee halve noten same-pitch in één lettergreep → één hele noot."""
    src = _HEAD + "L: lu_&_ ||\nS: g&g ||\nA: d&d ||\nT: bb&bb ||\nB: g&g ||\n"
    notes = _notes(_part(export_mvsa_to_musicxml(src, layout="playback"), "P1"))
    assert len(notes) == 1
    assert notes[0]["type"] == "whole"
    assert notes[0]["lyric"] == "lu"


def test_M5a_long_same_pitch_melisma_uses_tie_chain_never_breve():
    """M5a/I2: acht kwarten same-pitch → whole+whole met ties, nooit breve of 32 div."""
    src = (
        "@do F4\n@mode major\n@sectie x\n"
        "L: a_&_&_&_&_&_&_&_ ||\n"
        "S: g&g&g&g&g&g&g&g ||\nA: d&d&d&d&d&d&d&d ||\n"
        "T: bb&bb&bb&bb&bb&bb&bb&bb ||\nB: g&g&g&g&g&g&g&g ||\n"
    )
    xml = export_mvsa_to_musicxml(src, layout="partituur")
    assert "<type>breve</type>" not in xml
    assert "<duration>32</duration>" not in xml
    assert '<tie type="start"/>' in xml
    assert xml.count("<type>whole</type>") >= 2


# --- K2 / K3 -----------------------------------------------------------------


def test_K2_two_syllables_on_same_pitch_stay_two_notes():
    """K2: twee lettergrepen op dezelfde toon worden nooit samengetrokken."""
    src = _HEAD + "L: lu li ||\nS: g g ||\nA: d d ||\nT: bb bb ||\nB: g g ||\n"
    for layout in ("playback", "partituur"):
        notes = _notes(_part(export_mvsa_to_musicxml(src, layout=layout), "P1"))
        sung = [n for n in notes if n["lyric"]]
        assert [n["lyric"] for n in sung] == ["lu", "li"], layout


def test_K3_melisma_puts_lyric_and_extend_on_first_note_only():
    """K3: bij toonwissel staat de lyric op de eerste noot met ``<extend/>``."""
    src = _HEAD + "L: lu_&_ ||\nS: g&a ||\nA: d&e ||\nT: bb&c ||\nB: g&f ||\n"
    for layout in ("playback", "partituur"):
        notes = _notes(_part(export_mvsa_to_musicxml(src, layout=layout), "P1"))
        first, second = notes[0], notes[1]
        assert first["lyric"] == "lu" and first["extend"], layout
        assert second["lyric"] is None, layout


# --- M10 ---------------------------------------------------------------------

_RECITE = (
    _HEAD.replace("@sectie x\n", "")
    + "L: Die he_-mel,_ (aar-de en zee) heeft ge-maakt,_ ||\n"
    + "S: -   g4  a4     f4             g4    a4 Bb4     ||\n"
    + "A: -   e4  f4     -              -     -  -       ||\n"
    + "T: -   c4  -      a3             Bb3   c4 d4      ||\n"
    + "B: -   c3  f3     -              -     -  Bb2     ||\n"
)


def test_M10_recite_playback_has_one_sounding_note_per_syllable():
    """M10: ``(aar-de en zee)`` klinkt als vier kwarten; geen print-collapse/breve."""
    xml = export_mvsa_to_musicxml(_RECITE, layout="playback")
    assert "<type>breve</type>" not in xml
    by_lyric = {n["lyric"]: n for n in _notes(_part(xml, "P1")) if n["lyric"]}
    for syllable in ("aar", "de", "en", "zee"):
        assert syllable in by_lyric, syllable
        assert by_lyric[syllable]["type"] == "quarter", syllable
        assert by_lyric[syllable]["step"] == "F", syllable


# --- S2 / S4 -----------------------------------------------------------------

_SATB = _HEAD + "L: lu li ||\nS: g g ||\nA: d d ||\nT: bb bb ||\nB: g g ||\n"


def test_S2_partituur_has_two_staves_sa_g_clef_and_tb_f_clef():
    """S2: balk 1 = SA in G-sleutel, balk 2 = TB in F-sleutel, geen derde balk."""
    xml = export_mvsa_to_musicxml(_SATB, layout="partituur")
    parts = _root(xml).findall("part")
    assert [p.get("id") for p in parts] == ["P1", "P2"]
    signs = [p.findtext("measure/attributes/clef/sign") for p in parts]
    assert signs == ["G", "F"]


def test_S4_partituur_stems_s_and_t_up_a_and_b_down():
    """S4: voice 1 (S, T) stok omhoog; voice 2 (A, B) stok omlaag."""
    xml = export_mvsa_to_musicxml(_SATB, layout="partituur")
    for part_id in ("P1", "P2"):
        notes = _notes(_part(xml, part_id))
        v1 = {n["stem"] for n in notes if n["voice"] == "1"}
        v2 = {n["stem"] for n in notes if n["voice"] == "2"}
        assert v1 == {"up"}, part_id
        assert v2 == {"down"}, part_id


# --- S13 / R7 (MSCZ) ---------------------------------------------------------


def _chord(duration: str, *, tie: str, pitch: int = 67, tpc: int = 15) -> str:
    spanner = {
        "next": '<Spanner type="Tie"><next><location><fractions>1/4</fractions>'
        "</location></next></Spanner>",
        "prev": '<Spanner type="Tie"><prev><location><fractions>-1/2</fractions>'
        "</location></prev></Spanner>",
    }[tie]
    return (
        f"<Chord><durationType>{duration}</durationType>"
        f"<Note>{spanner}<pitch>{pitch}</pitch><tpc>{tpc}</tpc></Note></Chord>"
    )


def test_S13_R7_mscz_same_pitch_tie_chain_becomes_one_compact_note():
    """S13/R7: half + kwart same-pitch (Tie-keten) → één gestipte halve, geen Tie."""
    voice = f"<voice>{_chord('half', tie='next')}{_chord('quarter', tie='prev')}</voice>"
    fixed = _collapse_same_pitch_tie_runs(voice)
    assert fixed.count("<Chord") == 1
    assert "<durationType>half</durationType>" in fixed
    assert "<dots>1</dots>" in fixed or "<dots/>" in fixed
    assert 'type="Tie"' not in fixed


def test_S13_R7_mscz_different_pitch_is_never_collapsed():
    """S13/R7: andere toonhoogte blijft staan (alleen same-pitch wordt samengetrokken)."""
    voice = (
        f"<voice>{_chord('half', tie='next', pitch=67)}"
        f"{_chord('quarter', tie='prev', pitch=69, tpc=17)}</voice>"
    )
    assert _collapse_same_pitch_tie_runs(voice).count("<Chord") == 2
