"""VSA→template-instance: VSA-S + template A/T/B (tropaar-toon-4 / Elia)."""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import render_vsa_template_musicxml as render  # noqa: E402
import yaml  # noqa: E402

from vsa.template_instance import TemplateInstanceError, map_stanza, map_vsa_to_template  # noqa: E402
from vsa.vsa_stanzas import extract_stanza_notes  # noqa: E402

LIBRARY = ROOT / "docs" / "specification-vsa-templates" / "library"
TEMPLATE_YAML = LIBRARY / "tropaar-toon-4" / "template.yaml"
ELIA_VSA = (
    LIBRARY
    / "tropaar-toon-4"
    / "examples"
    / "corpus"
    / "T4-06-profeet-elia.vsa"
)


def _template() -> dict:
    return yaml.safe_load(TEMPLATE_YAML.read_text(encoding="utf-8"))


def _elia_text() -> str:
    return ELIA_VSA.read_text(encoding="utf-8")


def test_elia_has_seven_stanzas() -> None:
    stanzas = extract_stanza_notes(_elia_text())
    assert len(stanzas) == 7
    assert [n.lyric for n in stanzas[0]] == [
        "Gij",
        "waart",
        "een",
        "En",
        "gel",
        "in",
        "het",
        "vlees",
    ]


def test_elia_r1_recite_then_cadence() -> None:
    doc = _template()
    stanzas = extract_stanza_notes(_elia_text())
    phrase = next(p for p in doc["phrases"] if p["id"] == "1")
    mapped = map_stanza(stanzas[0], phrase, do=doc["do"], mode=doc["mode"])
    roles = [n.template_event["role"] for n in mapped]
    lyrics = [n.lyric for n in mapped]
    assert lyrics[:3] == ["Gij", "waart", "een"]
    assert roles[:3] == ["recite", "recite", "recite"]
    assert lyrics[3:5] == ["En", "gel"]
    assert roles[3:5] == ["cadence", "cadence"]
    assert [str(n.s_pitch) for n in mapped[5:7]] == ["Bb4", "Bb4"]
    assert mapped[-1].lyric == "vlees"
    assert str(mapped[-1].s_pitch) == "A4"


def test_elia_r2_skips_optional_link_uses_e_st() -> None:
    doc = _template()
    stanzas = extract_stanza_notes(_elia_text())
    phrase = next(p for p in doc["phrases"] if p["id"] == "2")
    mapped = map_stanza(stanzas[1], phrase, do=doc["do"], mode=doc["mode"])
    assert mapped[0].lyric == "de"
    assert mapped[0].template_event.get("anchor") == "e.st."
    assert mapped[0].show_anchor
    assert not any(n.template_event.get("optional") for n in mapped)
    recite_lyrics = [
        n.lyric for n in mapped if n.template_event.get("role") == "recite"
    ]
    assert recite_lyrics == ["grond", "slag", "der", "pro"]
    assert all(n.duration.note_type == "quarter" for n in mapped if n.template_event.get("role") == "recite")
    assert mapped[-1].lyric == "ten"
    assert mapped[-1].template_event.get("role") == "cadence"


def test_elia_full_phrase_assignment() -> None:
    mapped = map_vsa_to_template(_template(), _elia_text())
    assert [pid for pid, _ in mapped] == [
        "1",
        "2",
        "1",
        "2",
        "1",
        "2",
        "laatste",
    ]
    assert [len(notes) for _, notes in mapped] == [8, 7, 11, 6, 16, 11, 19]
    for _, notes in mapped:
        for note in notes:
            if note.template_event.get("role") == "recite":
                assert note.duration.note_type == "quarter"


def test_elia_r3_voorloper_is_three_quarters() -> None:
    mapped = map_vsa_to_template(_template(), _elia_text())
    lyrics = [n.lyric for n in mapped[2][1]]
    assert lyrics[4:7] == ["Voor", "lo", "per"]
    assert all(n.duration.note_type == "quarter" for n in mapped[2][1][4:7])


def test_elia_instance_mscx_has_lyrics_no_repeats_with_recite_breve() -> None:
    doc = _template()
    mapped = map_vsa_to_template(doc, _elia_text())
    mscx = render.render_instance_mscx(doc, mapped, title="Profeet Elia")
    staff1 = re.search(r'<Staff id="1">(.*?)</Staff>', mscx, re.DOTALL)
    assert staff1
    body = staff1.group(1)
    # Één maat per strofe; geen verborgen binnen-strofe-maatstrepen.
    n_meas = body.count("<Measure len=")
    assert n_meas == 7
    assert "<subtype>normal</subtype><visible>0</visible>" not in body
    assert "<startRepeat/>" not in mscx
    # Recite-print: body onder ||O||, laatste recite-lettergreep eigen noot.
    assert "<headType>breve</headType>" in mscx
    assert "<text>Gij</text>" in mscx
    assert "<text>waart</text>" in mscx
    assert "<position>left</position>" not in mscx
    assert "<align>left,baseline</align>" not in mscx
    assert "<text>een</text>" in mscx
    assert "<Lyrics>" in mscx
    assert f"<lyricsOddFontFace>{render.LYRIC_FONT}</lyricsOddFontFace>" in mscx
    assert f"<family>{render.LYRIC_FONT}</family>" in mscx
    assert f"<minNoteDistance>{render.INSTANCE_MIN_NOTE_DISTANCE}</minNoteDistance>" in mscx
    assert "<LayoutBreak>" not in mscx  # instance: MuseScore pakt systemen zelf
    # Geen formule-labels / ankers / cycle-frames in instance-MSCZ.
    assert "l. st" not in mscx
    assert "l.st." not in mscx
    assert "↓" not in mscx
    assert "<HBox>" not in mscx
    # Alleen titel-VBox, geen cycle-VBox met frase-volgorde.
    assert body.count("<VBox>") == 1
    # Geen [1] / [laatste] staff text (rectangle frase-id).
    assert not re.search(
        r"<StaffText>.*?rectangle.*?<text>(1|2|laatste)</text>",
        mscx,
        re.DOTALL,
    )
    assert "<showTimeSig>0</showTimeSig>" in mscx
    assert "<genCourtesyTimesig>0</genCourtesyTimesig>" in mscx
    assert f"<measureSpacing>{render.INSTANCE_MEASURE_SPACING}</measureSpacing>" in mscx
    assert "<stretch>0.85</stretch>" in mscx
    # SA/TB als akkoord (één stem) → geen tweede <voice> met alleen A/B.
    assert body.count("<voice>") == n_meas
    # Melisma-slurs ook op SA-balk (niet alleen TB).
    assert body.count('Spanner type="Slur"') >= 2


def test_collapse_recite_for_print_elia_r1() -> None:
    doc = _template()
    mapped = map_vsa_to_template(doc, _elia_text())
    events = render.collapse_recite_for_print(
        render.mapped_notes_to_events(mapped[0][1], doc["do"], doc["mode"])
    )
    assert events[0]["recite"] is True
    assert events[0]["ntype"] == "half"
    assert events[0]["dots"] == 0
    assert events[0]["lyric"] == "Gij"
    assert events[0].get("lyric_align") is None
    assert events[0].get("lyric_ticks", 0) == 0
    assert events[1].get("spacer") is True
    assert events[1]["lyric"] == "waart"
    slot = next(e for e in events[1:] if not e.get("rest") and not e.get("spacer"))
    assert slot["lyric"] == "een"
    assert slot["ntype"] == "quarter"
    assert slot["recite"] is False


def test_collapse_recite_keeps_ni_and_ter_quarter() -> None:
    """``…pries-ter {Ni_}ko{\\laas_}`` → ter kwart, Ni eigen noot, niet onder ||O||."""
    doc = _template()
    text = (
        Path("docs/specification-vsa-templates/library/tropaar-toon-4")
        / "examples/corpus/T4-11-nicolaas-van-myra.vsa"
    ).read_text(encoding="utf-8")
    mapped = map_vsa_to_template(doc, text)
    pid, notes = next(
        (p, n) for p, n in mapped if any(x.lyric == "Ni" for x in n)
    )
    assert pid == "2"
    events = render.collapse_recite_for_print(
        render.mapped_notes_to_events(notes, doc["do"], doc["mode"])
    )
    lyrics = [
        (e.get("lyric"), e.get("recite"), e.get("ntype"))
        for e in events
        if not e.get("rest") and not e.get("spacer")
    ]
    assert lyrics[0][0] == "Va"
    assert lyrics[0][1] is False  # scope {/Va} — eigen noot, geen breve
    assert ("ter", False, "quarter") in lyrics
    assert ("Ni", False, "half") in lyrics
    assert ("ko", False, "quarter") in lyrics


def test_collapse_recite_for_print_single_syllable() -> None:
    events = [
        {
            "pitches": {"S": ("A", 0, 4)},
            "dur": 4,
            "ntype": "quarter",
            "dots": 0,
            "optional": False,
            "recite": True,
            "lyric": "de",
            "syllabic": "single",
        }
    ]
    out = render.collapse_recite_for_print(events)
    assert len(out) == 1
    assert out[0]["recite"] is False
    assert out[0]["lyric"] == "de"


def test_collapse_recite_for_print_two_syllables_stay_separate() -> None:
    """Nicolaas: „Als de …“ — te kort voor ||O||; aparte noten."""
    events = [
        {
            "pitches": {"S": ("A", 0, 4)},
            "dur": 4,
            "ntype": "quarter",
            "dots": 0,
            "optional": False,
            "recite": True,
            "lyric": "Als",
            "syllabic": "single",
        },
        {
            "pitches": {"S": ("A", 0, 4)},
            "dur": 4,
            "ntype": "quarter",
            "dots": 0,
            "optional": False,
            "recite": True,
            "lyric": "de",
            "syllabic": "single",
        },
    ]
    out = render.collapse_recite_for_print(events)
    assert len(out) == 2
    assert all(e["recite"] is False for e in out)
    assert [e["lyric"] for e in out] == ["Als", "de"]


def test_collapse_recite_scopes_stay_own_notes() -> None:
    """``{/en} het … zacht{moe_}dig{\\heid_}`` — scopes eigen noten; zacht = slotkwart."""
    doc = _template()
    text = (
        Path("docs/specification-vsa-templates/library/tropaar-toon-4")
        / "examples/corpus/T4-11-nicolaas-van-myra.vsa"
    ).read_text(encoding="utf-8")
    mapped = map_vsa_to_template(doc, text)
    notes = next(
        n for p, n in mapped if any(x.lyric == "moe" for x in n)
    )
    events = render.collapse_recite_for_print(
        render.mapped_notes_to_events(notes, doc["do"], doc["mode"])
    )
    lyrics = [
        (e.get("lyric"), e.get("recite"), e.get("ntype"))
        for e in events
        if not e.get("rest") and not e.get("spacer")
    ]
    assert lyrics[0] == ("en", False, "quarter")
    assert lyrics[1] == ("het", True, "half")
    spacer_lyrics = [e.get("lyric") for e in events if e.get("spacer")]
    assert "voor" in spacer_lyrics
    assert "zacht" not in spacer_lyrics
    assert ("zacht", False, "quarter") in lyrics
    assert ("moe", False, "half") in lyrics
    assert ("dig", False, "quarter") in lyrics
    assert ("heid", False, "half") in lyrics


def test_instance_recite_mscx_no_dots_has_hidden_spacers() -> None:
    doc = _template()
    mapped = map_vsa_to_template(doc, _elia_text())
    mscx = render.render_instance_mscx(doc, mapped, title="Elia")
    # Recite-chord: breve-kop, geen <dots> vóór durationType van die chord.
    for m in re.finditer(
        r"<Chord>(.*?)<headType>breve</headType>.*?</Chord>",
        mscx,
        re.DOTALL,
    ):
        chunk = m.group(1)
        assert "<dots>" not in chunk
        assert "<durationType>half</durationType>" in chunk
    assert "<play>0</play>" in mscx
    assert "<position>left</position>" not in mscx
    assert "<align>left,baseline</align>" not in mscx
    assert "durationType>longa</durationType>" not in mscx


def test_elia_instance_hyphens_and_melisma_slurs() -> None:
    doc = _template()
    mapped = map_vsa_to_template(doc, _elia_text())
    mscx = render.render_instance_mscx(doc, mapped, title="Elia instance")
    # Recite-collapse: eerste lettergreep op ||O||; rest op spacers; cadens eigen noten.
    assert "<text>grond-</text>" in mscx or "<text>grond</text>" in mscx
    assert "<text>slag</text>" in mscx or "<text>slag-</text>" in mscx
    assert "<text>der</text>" in mscx
    assert "<text>pro-</text>" in mscx
    assert "<text>fe-</text>" in mscx
    assert "<text>ten</text>" in mscx
    # Melisma-lettergrepen houden ook een streepje (li-, e-).
    assert "<text>li-</text>" in mscx or "<text>e-</text>" in mscx
    assert 'Spanner type="Slur"' in mscx
    assert "<ticks>" in mscx
    assert "<headType>breve</headType>" in mscx
    assert "<align>left,baseline</align>" not in mscx
    assert "<text>En-</text>" in mscx
    assert "<text>gel</text>" in mscx

def test_elia_glued_words_get_syllabic() -> None:
    stanzas = extract_stanza_notes(_elia_text())
    assert [(n.lyric, n.syllabic) for n in stanzas[0] if n.lyric][3:5] == [
        ("En", "begin"),
        ("gel", "end"),
    ]
    assert [(n.lyric, n.syllabic) for n in stanzas[1] if n.lyric][4:7] == [
        ("pro", "begin"),
        ("fe", "middle"),
        ("ten", "end"),
    ]


def test_elia_instance_instance_layout_packs_systems() -> None:
    doc = _template()
    mapped = map_vsa_to_template(doc, _elia_text())
    mscx = render.render_instance_mscx(doc, mapped, title="Elia instance")
    assert f"<minNoteDistance>{render.INSTANCE_MIN_NOTE_DISTANCE}</minNoteDistance>" in mscx
    assert "<lastSystemFillLimit>0</lastSystemFillLimit>" in mscx
    staff1 = re.search(r'<Staff id="1">(.*?)</Staff>', mscx, re.DOTALL)
    assert staff1
    body = staff1.group(1)
    n_meas = body.count("<Measure len=")
    n_breaks = body.count("<LayoutBreak>")
    assert n_meas == 7
    assert "<subtype>normal</subtype><visible>0</visible>" not in body
    assert n_breaks == 0


def test_elia_instance_elia_a_is_half() -> None:
    """VSA ``{\\a_}`` → half op laatste cadens van frase 2."""
    mapped = map_vsa_to_template(_template(), _elia_text())
    lyrics = [(n.lyric, n.duration.note_type) for n in mapped[3][1]]
    assert ("a", "half") in lyrics


def test_elia_instance_musicxml_coria_nonempty() -> None:
    doc = _template()
    mapped = map_vsa_to_template(doc, _elia_text())
    xml = render.render_instance_musicxml(doc, mapped, title="Elia instance")
    assert len(xml) > 1000
    assert "<score-partwise" in xml
    assert "<lyric" in xml
    assert 'slur type="start"' in xml
    assert "<text>Voor-</text>" in xml or ">Voor-</text>" in xml or (
        "<syllabic>begin</syllabic><text>Voor</text>" in xml.replace("\n", "")
    )
    assert "<text>En-</text>" not in xml  # streepje komt uit syllabic, niet uit text
    assert "<syllabic>begin</syllabic><text>En</text>" in xml.replace("\n", "")
    assert "<syllabic>begin</syllabic><text>pro</text>" in xml.replace("\n", "")
    assert "<!DOCTYPE" not in xml
    assert "<extend type=\"stop\"/>" not in xml
    assert "<extend type=\"continue\"/>" not in xml
    # Vier aparte parts voor solo-oefenen in Coria.
    assert "<part-name>Soprano</part-name>" in xml
    assert "<part-name>Alto</part-name>" in xml
    assert "<part-name>Tenor</part-name>" in xml
    assert "<part-name>Bass</part-name>" in xml
    assert 'id="P4"' in xml
    # Tenor: F-sleutel; geen geforceerde stokrichting (auto naar midden).
    tenor = re.search(r'<part id="P3">(.*?)</part>', xml, re.DOTALL)
    assert tenor
    assert "<sign>F</sign>" in tenor.group(1)
    assert "clef-octave-change" not in tenor.group(1)
    assert "<stem>up</stem>" not in tenor.group(1)
    assert "<stem>down</stem>" not in tenor.group(1)
    # Één maat per strofe (7), geen splits binnen een frase.
    sop = re.search(r'<part id="P1">(.*?)</part>', xml, re.DOTALL)
    assert sop
    assert sop.group(1).count("<measure number=") == 7
    # #do (alt) = F# met alter én accidental (Coria).
    assert "<step>F</step><alter>1</alter>" in xml.replace("\n", "")
    assert "<accidental>sharp</accidental>" in xml
    # Bb in F-dur: alter blijft, géén overbodige <accidental>flat>.
    assert "<accidental>flat</accidental>" not in xml
    # Lyrics op elke stem (Coria solo/mute).
    for pid in ("P1", "P2", "P3", "P4"):
        part = re.search(rf'<part id="{pid}">(.*?)</part>', xml, re.DOTALL)
        assert part, pid
        assert "<lyric" in part.group(1), pid
        assert "<text>Voor</text>" in part.group(1), pid
    path_mxl = (
        LIBRARY
        / "tropaar-toon-4"
        / "examples"
        / "corpus"
        / "T4-06-profeet-elia.mxl"
    )
    assert path_mxl.is_file() and path_mxl.stat().st_size > 0


def test_elia_instance_musicxml_alto_fs_has_accidental() -> None:
    """Laatste A van [1] is #do → F#; zonder accidental speelt Coria F."""
    doc = _template()
    mapped = map_vsa_to_template(doc, _elia_text())
    events = render.prepare_instance_events(
        render.mapped_notes_to_events(mapped[0][1], doc["do"], doc["mode"])
    )
    last_a = events[-1]["pitches"]["A"]
    assert last_a == ("F", 1, 4)
    xml = render.render_instance_musicxml(doc, mapped, title="Elia instance")
    # Alto-part (P2) moet F# met accidental bevatten.
    alto = re.search(r'<part id="P2">(.*?)</part>', xml, re.DOTALL)
    assert alto
    assert "<accidental>sharp</accidental>" in alto.group(1)
    assert re.search(
        r"<step>F</step>\s*<alter>1</alter>\s*<octave>4</octave>",
        alto.group(1),
    )


def test_elia_instance_visible_barline_per_stanza() -> None:
    doc = _template()
    mapped = map_vsa_to_template(doc, _elia_text())
    mscx = render.render_instance_mscx(doc, mapped, title="Elia instance")
    staff1 = re.search(r'<Staff id="1">(.*?)</Staff>', mscx, re.DOTALL)
    assert staff1
    body = staff1.group(1)
    n_meas = body.count("<Measure len=")
    assert n_meas == 7
    assert "<subtype>normal</subtype><visible>0</visible>" not in body
    lens = re.findall(r'<Measure len="([^"]+)">', body)
    assert all("/" in x for x in lens)


def test_pitch_mismatch_in_laatste_raises() -> None:
    """mi–fa–sol past op geen ``of:``-cadens → cadenspad-fout met bronlocatie."""
    from vsa.template_instance import CODE_CADENCE_PATH

    doc = _template()
    phrase = next(p for p in doc["phrases"] if p["id"] == "laatste")
    # Schep = fa, daarna nog een stijging (sol): geen pad is mi–fa–sol.
    text = (
        "---\ndo: F4\nmode: major\n---\n\n"
        "// Ver-vul-ling van het Heils-plan van de {-&/Schep_}{/per_}. [//:]\n"
    )
    stanzas = extract_stanza_notes(text)
    with pytest.raises(TemplateInstanceError) as caught:
        map_stanza(
            stanzas[0],
            phrase,
            do=doc["do"],
            mode=doc["mode"],
            source="demo.vsa",
        )
    err = caught.value
    assert err.code == CODE_CADENCE_PATH
    assert err.hint_nl
    assert "cadenspad" in err.hint_nl
    assert err.line >= 6  # na frontmatter
    assert err.column >= 1
    assert "demo.vsa" in err.format_compact()
    assert f"demo.vsa:{err.line}:{err.column}" == err.location_label()
    lines = err.format_lines()
    assert lines[0] == err.location_label()
    assert lines[1].startswith(f"ERROR: {CODE_CADENCE_PATH}:")
    assert any(line.startswith("Hint:") for line in lines)


def test_vsa_note_line_column_elia_en() -> None:
    """Scoped `{En_}` in elia.vsa heeft bronregel/kolom in het volledige bestand."""
    text = _elia_text()
    stanzas = extract_stanza_notes(text)
    en = next(n for n in stanzas[0] if n.lyric == "En")
    assert en.line == 12
    assert en.column >= 1
    # Kolom wijst naar de `{` van `{En_}`.
    line = text.splitlines()[en.line - 1]
    assert line[en.column - 1] == "{"
    assert "En_" in line[en.column - 1 :]


def test_h5_vsa_duration_overrides_template_elm() -> None:
    """H5: VSA `_` (half) wint van template-cadens `~`; A/T/B delen die duur."""
    doc = _template()
    mapped = map_vsa_to_template(doc, _elia_text())
    en = next(n for n in mapped[0][1] if n.lyric == "En")
    assert en.duration.note_type == "half"
    assert en.template_event.get("duration") == "~"
    events = render.mapped_notes_to_events(mapped[0][1], doc["do"], doc["mode"])
    en_ev = next(ev for ev in events if ev.get("lyric") == "En")
    assert en_ev["ntype"] == "half"
    assert en_ev["dur"] == 8
    # Zelfde event = één ritme voor S/A/T/B (parallel).
    assert set(en_ev["pitches"]) == {"S", "A", "T", "B"}


def test_h5_split_same_slot_keeps_per_syllable_duration() -> None:
    """H5 split: twee VSA-syllaben op zelfde graad → twee events, elk eigen VSA-duur."""
    doc = _template()
    mapped = map_vsa_to_template(doc, _elia_text())
    # {En_}gel: En half, gel quarter (ongemarkerd, zelfde mi).
    notes = [n for n in mapped[0][1] if n.lyric in ("En", "gel")]
    assert [n.lyric for n in notes] == ["En", "gel"]
    assert notes[0].duration.note_type == "half"
    assert notes[1].duration.note_type == "quarter"
    events = render.mapped_notes_to_events(notes, doc["do"], doc["mode"])
    assert [e["ntype"] for e in events] == ["half", "quarter"]


def test_pitch_mismatch_past_tail_raises() -> None:
    doc = _template()
    phrase = next(p for p in doc["phrases"] if p["id"] == "laatste")
    # Cadens al klaar (mi–re–mi), daarna nog een scoped fa.
    text = (
        "---\ndo: F4\nmode: major\n---\n\n"
        "// xxx {-&\\a_&_}{/b_}{\\c_}{/extra_}. [//:]\n"
    )
    stanzas = extract_stanza_notes(text)
    with pytest.raises(TemplateInstanceError, match="hoogte-mismatch"):
        map_stanza(stanzas[0], phrase, do=doc["do"], mode=doc["mode"])


def test_required_other_pitch_skip_raises() -> None:
    """Sprong over verplichte andere toon (fa→…→mi met re ertussen) → fout."""
    phrase = {
        "id": "cad",
        "events": [
            {"role": "recite", "pitches": {"S": "mi", "A": "do", "T": "sol-1", "B": "do-1"}},
            {"role": "cadence", "pitches": {"S": "fa", "A": "re", "T": "la-1", "B": "re-1"}},
            {"role": "cadence", "pitches": {"S": "re", "A": "ti-1", "T": "sol-1", "B": "sol-2"}},
            {"role": "cadence", "pitches": {"S": "mi", "A": "do", "T": "sol-1", "B": "do-1"}},
        ],
    }
    # {/a}=fa, then {\b}=mi: slaat verplicht re over.
    text = "---\ndo: F4\nmode: major\n---\n\n// x {/a_}{\\b_}. [//:]\n"
    stanzas = extract_stanza_notes(text)
    with pytest.raises(TemplateInstanceError) as caught:
        map_stanza(stanzas[0], phrase, do="F4", mode="major", source="x.vsa")
    err = caught.value
    assert err.code == "VSA-TEMPLATE-REQUIRED-SLOT-SKIPPED"
    assert "re" in err.message_nl
    assert "optional: true" in err.hint_nl
    assert err.format_compact().endswith("VSA-TEMPLATE-REQUIRED-SLOT-SKIPPED")


def test_optional_other_pitch_skip_ok() -> None:
    phrase = {
        "id": "cad",
        "events": [
            {"role": "recite", "pitches": {"S": "mi", "A": "do", "T": "sol-1", "B": "do-1"}},
            {"role": "cadence", "pitches": {"S": "fa", "A": "re", "T": "la-1", "B": "re-1"}},
            {
                "role": "cadence",
                "optional": True,
                "pitches": {"S": "re", "A": "ti-1", "T": "sol-1", "B": "sol-2"},
            },
            {"role": "cadence", "pitches": {"S": "mi", "A": "do", "T": "sol-1", "B": "do-1"}},
        ],
    }
    text = "---\ndo: F4\nmode: major\n---\n\n// x {/a_}{\\b_}. [//:]\n"
    stanzas = extract_stanza_notes(text)
    mapped = map_stanza(stanzas[0], phrase, do="F4", mode="major")
    degrees = [
        n.template_event["pitches"]["S"]
        for n in mapped
        if n.template_event.get("role") == "cadence"
    ]
    assert degrees == ["fa", "mi"]
    assert not any(n.template_event.get("optional") for n in mapped)

def test_h7_skips_same_pitch_cadence_after_recite() -> None:
    """Na recite-fa mag cadens-fa-run weg als VSA meteen naar slot-mi gaat."""
    phrase = {
        "id": "2",
        "events": [
            {
                "role": "cadence",
                "anchor": "e.st.",
                "pitches": {"S": "fa", "A": "re", "T": "la-1", "B": "re-1"},
            },
            {"role": "recite", "pitches": {"S": "fa", "A": "re", "T": "la-1", "B": "re-1"}},
            {"role": "cadence", "pitches": {"S": "fa", "A": "re", "T": "la-1", "B": "re-1"}},
            {
                "role": "cadence",
                "anchor": "l.st.",
                "pitches": {"S": "fa", "A": "re", "T": "sol-1", "B": "sol-2"},
            },
            {"role": "cadence", "pitches": {"S": "mi", "A": "do", "T": "sol-1", "B": "do-1"}},
        ],
    }
    # {/de} = e.st. fa; recite; {\\we_} = mi (slaat fa-cadens over).
    text = "---\ndo: F4\nmode: major\n---\n\n{/de} grond {\\we_}. [//:]\n"
    stanzas = extract_stanza_notes(text)
    mapped = map_stanza(stanzas[0], phrase, do="F4", mode="major")
    assert [n.lyric for n in mapped] == ["de", "grond", "we."]
    assert mapped[-1].template_event["pitches"]["S"] == "mi"

    phrase = {
        "id": "cad",
        "events": [
            {"role": "recite", "pitches": {"S": "mi", "A": "do", "T": "sol-1", "B": "do-1"}},
            {"role": "cadence", "pitches": {"S": "mi", "A": "do", "T": "sol-1", "B": "do-1"}},
            {"role": "cadence", "pitches": {"S": "fa", "A": "re", "T": "la-1", "B": "re-1"}},
        ],
    }
    # Alleen recite + één cadens-mi; verplicht fa blijft liggen.
    text = "---\ndo: F4\nmode: major\n---\n\n// a b {~c_}. [//:]\n"
    stanzas = extract_stanza_notes(text)
    with pytest.raises(TemplateInstanceError) as caught:
        map_stanza(stanzas[0], phrase, do="F4", mode="major")
    assert caught.value.code == "VSA-TEMPLATE-REQUIRED-SLOT-UNUSED"
    assert "fa" in caught.value.message_nl


def test_elia_instance_s_from_vsa_atb_from_template() -> None:
    doc = _template()
    mapped = map_vsa_to_template(doc, _elia_text())
    events = render.mapped_notes_to_events(mapped[0][1], doc["do"], doc["mode"])
    # Recite A/T/B = do / sol-1 / do-1 → F4 / C4 / F3
    assert events[0]["pitches"]["S"] == ("A", 0, 4)
    assert events[0]["pitches"]["A"] == ("F", 0, 4)
    assert events[0]["pitches"]["T"] == ("C", 0, 4)
    assert events[0]["pitches"]["B"] == ("F", 0, 3)
    # {/in} = fa → A/T/B re / la-1 / re-1
    in_ev = next(ev for ev in events if ev.get("lyric") == "in")
    assert in_ev["pitches"]["S"] == ("B", -1, 4)
    assert in_ev["pitches"]["A"] == ("G", 0, 4)


def test_elia_instance_mscz_written() -> None:
    path = (
        LIBRARY
        / "tropaar-toon-4"
        / "examples"
        / "corpus"
        / "T4-06-profeet-elia.mscz"
    )
    assert path.is_file(), "run: python scripts\\render_tropaar_toon4_corpus.py"
    with zipfile.ZipFile(path) as archive:
        assert "score_style.mss" in archive.namelist()
        mscx = archive.read("score.mscx").decode("utf-8")
        mss = archive.read("score_style.mss").decode("utf-8")
    assert "<Lyrics>" in mscx
    assert "Profeet Elia" in mscx
    assert "T4-06 —" not in mscx
    assert "<maxPageFillSpread>0</maxPageFillSpread>" in mscx
    assert "<maxSystemDistance>9.64</maxSystemDistance>" in mscx
    assert "<maxSystemSpread>9.64</maxSystemSpread>" in mscx
    assert "<minSystemDistance>9.64</minSystemDistance>" in mscx
    assert "<staffDistance>5</staffDistance>" in mscx or "<staffDistance>5.0</staffDistance>" in mscx
    assert "<frameSystemDistance>4</frameSystemDistance>" in mscx or "<frameSystemDistance>4.0</frameSystemDistance>" in mscx
    assert f"<height>{render.TITLE_VBOX_HEIGHT_SP:g}</height>" in mscx
    assert "<maxSystemDistance>9.64</maxSystemDistance>" in mss
    assert "<enableVerticalSpread>0</enableVerticalSpread>" in mss
    assert "<enableIndentationOnFirstSystem>0</enableIndentationOnFirstSystem>" in mss
    assert "<frameSystemDistance>4</frameSystemDistance>" in mss or "<frameSystemDistance>4.0</frameSystemDistance>" in mss


def _satb(s: str, a: str = "do", t: str = "sol-1", b: str = "do-1") -> dict:
    return {"S": s, "A": a, "T": t, "B": b}


def test_of_chooses_fa_cadence_path() -> None:
    """VSA mi–fa–mi kiest het fa-pad; het re-pad wordt niet stil gebruikt."""
    from vsa.template_instance import CODE_CADENCE_PATH

    phrase = {
        "id": "laatste",
        "events": [
            {"role": "recite", "pitches": _satb("mi")},
            {
                "of": [
                    {
                        "id": "re-close",
                        "events": [
                            {"role": "cadence", "duration": "_", "pitches": _satb("re", "ti-1", "sol-1", "sol-2")},
                            {"role": "cadence", "duration": "__", "pitches": _satb("mi")},
                        ],
                    },
                    {
                        "id": "fa-close",
                        "events": [
                            {"role": "cadence", "duration": "_", "pitches": _satb("fa", "re", "la-1", "re-1")},
                            {"role": "cadence", "duration": "__", "pitches": _satb("mi")},
                        ],
                    },
                ]
            },
        ],
    }
    text = "---\ndo: F4\nmode: major\n---\n\n// x {/a_}{\\b_}. [//:]\n"
    stanzas = extract_stanza_notes(text)
    mapped = map_stanza(stanzas[0], phrase, do="F4", mode="major")
    degrees = [n.template_event["pitches"]["S"] for n in mapped if n.template_event.get("role") == "cadence"]
    assert degrees == ["fa", "mi"]

    bad = "---\ndo: F4\nmode: major\n---\n\n// x {/a_}{/z_}. [//:]\n"
    stanzas_bad = extract_stanza_notes(bad)
    with pytest.raises(TemplateInstanceError) as caught:
        map_stanza(stanzas_bad[0], phrase, do="F4", mode="major", source="x.vsa")
    assert caught.value.code in {CODE_CADENCE_PATH, "VSA-TEMPLATE-PITCH-MISMATCH"}
    assert "cadenspad" in caught.value.hint_nl


def test_h8_llgr_attaches_remaining_to_last_syllable() -> None:
    phrase = {
        "id": "slot",
        "events": [
            {"role": "recite", "pitches": _satb("mi")},
            {"role": "cadence", "duration": "_", "pitches": _satb("fa", "re", "la-1", "re-1")},
            {
                "role": "cadence",
                "duration": "_",
                "anchor": "l.lgr.",
                "pitches": _satb("re", "ti-1", "sol-1", "sol-2"),
            },
            {"role": "cadence", "duration": "__", "pitches": _satb("mi")},
        ],
    }
    text = "---\ndo: F4\nmode: major\n---\n\n// x {/a_}. [//:]\n"
    mapped = map_stanza(extract_stanza_notes(text)[0], phrase, do="F4", mode="major")
    degrees = [n.template_event["pitches"]["S"] for n in mapped]
    assert degrees[-3:] == ["fa", "re", "mi"]
    assert mapped[-2].lyric == ""
    assert mapped[-1].lyric == ""
    assert mapped[-2].template_event.get("anchor") == "l.lgr."


def test_normalize_anchor_strips_spaces() -> None:
    from vsa.template_instance import normalize_anchor

    assert normalize_anchor("e. st.") == "e.st."
    assert normalize_anchor("l.st") == "l.st."
    assert normalize_anchor("l. lgr.") == "l.lgr."


def test_mode_mismatch_between_vsa_and_template_raises() -> None:
    doc = _template()
    text = "---\ndo: F4\nmode: minor\n---\n\nGij waart een {En_}gel.\n"
    with pytest.raises(TemplateInstanceError) as caught:
        map_vsa_to_template(doc, text, source="elia.vsa")
    assert caught.value.code == "VSA-TEMPLATE-MODE-MISMATCH"


def test_sequence_form_rejects_wrong_stanza_count() -> None:
    path = LIBRARY / "tropaar-toon-3" / "template.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    text = "---\ndo: G4\nmode: major\n---\n\n// aa {/b_}. [//:]\n"
    with pytest.raises(TemplateInstanceError) as caught:
        map_vsa_to_template(doc, text, source="seq.vsa")
    assert caught.value.code == "VSA-TEMPLATE-TEXT-MAPPING"


def test_tropaar_toon4_tenor_opening_is_c4() -> None:
    """sol-1 t.o.v. do:F4 = C4 (niet C3)."""
    from vsa.template_instance import degree_pitch

    doc = _template()
    opening = doc["phrases"][0]["events"][0]["pitches"]["T"]
    assert opening == "sol-1"
    pitch = degree_pitch(opening, doc["do"], doc["mode"])
    assert (pitch.step, pitch.octave, int(pitch.alter)) == ("C", 4, 0)


def test_open_skipped_when_vsa_starts_unscoped() -> None:
    """H1: open blijft in YAML; instance krijgt geen dubbele noot."""
    phrase = next(p for p in _template()["phrases"] if p["id"] == "1")
    assert phrase["events"][0]["role"] == "open"
    assert phrase["events"][1]["role"] == "recite"
    mapped = map_vsa_to_template(_template(), _elia_text())
    roles = [n.template_event["role"] for n in mapped[0][1]]
    assert roles[0] == "recite"
    assert "open" not in roles
