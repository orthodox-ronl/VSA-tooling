"""Score-IR → partituur MusicXML (OSMD-brug)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from vsa.score_ir import export_mvsa_to_score_ir
from vsa.score_ir_musicxml import (
    ScoreIrMusicxmlError,
    export_score_ir_path_to_musicxml,
    score_ir_to_musicxml,
)

ROOT = Path(__file__).resolve().parents[1]
VREDE = ROOT / "examples" / "mvsa" / "1a-vredeslitanie.mvsa"


def test_score_ir_to_musicxml_has_cues_and_parts() -> None:
    doc = export_mvsa_to_score_ir(VREDE.read_text(encoding="utf-8"))
    xml = score_ir_to_musicxml(doc)
    assert 'score-partwise version="3.1"' in xml
    assert 'part id="P1"' in xml
    assert 'part id="P2"' in xml
    assert "Gezegend" in xml
    assert "<words" in xml
    assert "<lyric" in xml
    # OSMD: wrap op ``...`` als uitgangspunt; JS kan later tot 1 regel inklappen.
    assert "Gezegend\n..." in xml or "Gezegend\n…" in xml
    assert 'font-family="Source Sans 3"' in xml
    assert 'font-size="12"' in xml
    assert "default-x=" in xml
    assert "relative-x=" not in xml
    assert "osmdWidthFactor=" not in xml
    assert "senza-misura" in xml
    # Geen metronoom-glyph (OSMD negeert print-object=no); wel playback-tempo.
    assert "<metronome" not in xml
    assert 'sound tempo="' in xml


def test_export_path_roundtrip(tmp_path: Path) -> None:
    from vsa.score_ir import export_mvsa_path_to_score_ir

    ir = tmp_path / "x.score-ir.json"
    mxl = tmp_path / "x.musicxml"
    export_mvsa_path_to_score_ir(VREDE, ir)
    export_score_ir_path_to_musicxml(ir, mxl)
    text = mxl.read_text(encoding="utf-8")
    assert "Gezegend" in text


def test_rejects_wrong_format() -> None:
    with pytest.raises(ScoreIrMusicxmlError, match="format"):
        score_ir_to_musicxml({"format": "nope", "profile": "partituur"})


_S8_RECITE = """\
@do F4
@mode major
@oct S=0 A=0 T=-1 B=-1

L: (Al-le-lu-ia, al-le) ||
S:  Bb                 ||
A:  g                  ||
T:  d                  ||
B:  g                  ||
"""


def test_from_ir_tempo_from_mvsa_meta() -> None:
    text = (
        '@title "t"\n'
        "@tempo 160\n"
        "@do F4\n@mode major\n@oct S=0 A=0 T=-1 B=-1\n"
        "L: a ||\nS: c ||\nA: c ||\nT: c ||\nB: c ||\n"
    )
    doc = export_mvsa_to_score_ir(text)
    assert doc["meta"].get("tempo") == "160"
    xml = score_ir_to_musicxml(doc)
    assert 'sound tempo="160"' in xml


def test_from_ir_s8_emits_spacer_noteheads() -> None:
    """A1-marker: spacer → notehead none (+ stem none); midden → breve (S8).

    ``notehead none`` is het canonieke scherm-markercontract voor de OSMD-
    adapter (bibliotheek). OSMD zelf eert de tag niet als onzichtbare kop —
    zie docs/plans/osmd-s8-recite.md.
    """
    doc = export_mvsa_to_score_ir(_S8_RECITE)
    xml = score_ir_to_musicxml(doc)
    assert "<notehead>none</notehead>" in xml
    assert "<notehead>breve</notehead>" in xml
    assert "<type>breve</type>" not in xml
    assert "<stem>none</stem>" in xml
    # Minstens één spacer-noot: stem none + notehead none in dezelfde <note>.
    notes = re.findall(r"<note>(.*?)</note>", xml, flags=re.DOTALL)
    spacer_notes = [
        n
        for n in notes
        if "<notehead>none</notehead>" in n and "<stem>none</stem>" in n
    ]
    assert spacer_notes, "S8 A1-marker (stem none + notehead none) ontbreekt"
    assert any("<lyric" in n and "<text>" in n for n in spacer_notes), (
        "spacer-marker moet lyric behouden (geen print-object=no op hele note)"
    )
    assert all('print-object="no"' not in n for n in spacer_notes)


_S13_MELISMA = """\
@do F4
@mode major
@oct S=0 A=0 T=-1 B=-1

L: a_&_ ||
S: g&g  ||
A: d&d  ||
T: bb&bb ||
B: g&g  ||
"""


def test_from_ir_s13_compact_melisma() -> None:
    doc = export_mvsa_to_score_ir(_S13_MELISMA)
    xml = score_ir_to_musicxml(doc)
    p1 = xml.split('<part id="P1">', 1)[1].split("</part>", 1)[0]
    # Eén maat: weinig <note> (SA = voice 1+2); same-pitch niet als hakwerk.
    notes = p1.count("<note>")
    assert notes <= 4, f"te veel noten in P1: {notes}"
    assert "<tie " not in p1 or p1.count("<tie ") == 0


_SPEELPLAN_VOLTA = """\
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


def test_score_ir_speelplan_volta_ab_ac() -> None:
    """Bladvorm volta in Score-IR → from-ir MusicXML (zelfde merken als partituur)."""
    doc = export_mvsa_to_score_ir(_SPEELPLAN_VOLTA)
    assert len(doc["measures"]) == 3
    m1, m2, m3 = doc["measures"]
    assert m1["bar"].get("left") == "repeat-start"
    assert m2["bar"]["right"] == "repeat-end"
    assert m2["ending"] == {"start": "1,2", "stop": "1,2"}
    assert m3["ending"] == {"start": "3", "stop": "3"}

    xml = score_ir_to_musicxml(doc)
    assert xml.count("<measure ") == 6  # 3 maten × 2 parts
    assert 'direction="forward"' in xml
    assert 'direction="backward"' in xml
    assert 'number="1,2"' in xml
    assert 'number="3"' in xml
    assert 'type="start"' in xml
    assert 'type="stop"' in xml
    p1 = xml.split('<part id="P1">', 1)[1].split("</part>", 1)[0]
    p2 = xml.split('<part id="P2">', 1)[1].split("</part>", 1)[0]
    assert "<ending " in p1
    assert "<ending " not in p2


def _three_blok_mvsa(speelplan: str) -> str:
    return f"""\
@do F4
@mode major
@speelplan {speelplan}

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


def test_score_ir_speelplan_simple_repeat() -> None:
    """``1,2,1,2,3`` → |: 1–2 :| + suffix 3 (geen volta)."""
    doc = export_mvsa_to_score_ir(_three_blok_mvsa("1, 2, 1, 2, 3"))
    assert len(doc["measures"]) == 3
    assert doc["measures"][0]["bar"].get("left") == "repeat-start"
    assert doc["measures"][1]["bar"]["right"] == "repeat-end"
    assert "ending" not in doc["measures"][1]
    xml = score_ir_to_musicxml(doc)
    assert 'direction="forward"' in xml
    assert 'direction="backward"' in xml
    assert "<ending " not in xml
    assert xml.count("<measure ") == 6


def test_score_ir_speelplan_ds_al_fine() -> None:
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
    doc = export_mvsa_to_score_ir(text)
    assert len(doc["measures"]) == 4
    assert doc["measures"][1]["navigation"] == ["segno"]
    assert doc["measures"][2]["navigation"] == ["fine"]
    assert doc["measures"][3]["navigation"] == ["ds_al_fine"]
    xml = score_ir_to_musicxml(doc)
    assert "<segno/>" in xml
    assert ">Fine</words>" in xml
    assert ">D.S. al Fine</words>" in xml
    assert 'dalsegno="segno"' in xml
    assert xml.count("<measure ") == 8


def test_score_ir_speelplan_ds_al_coda() -> None:
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
    doc = export_mvsa_to_score_ir(text)
    assert len(doc["measures"]) == 4
    assert doc["measures"][1]["navigation"] == ["segno", "to_coda"]
    assert doc["measures"][2]["navigation"] == ["ds_al_coda"]
    assert doc["measures"][3]["navigation"] == ["coda"]
    xml = score_ir_to_musicxml(doc)
    assert "<segno/>" in xml
    assert ">To Coda</words>" in xml
    assert ">D.S. al Coda</words>" in xml
    assert "<coda/>" in xml
    assert xml.count("<measure ") == 8


def test_score_ir_speelplan_dc_al_coda() -> None:
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
    doc = export_mvsa_to_score_ir(text)
    assert len(doc["measures"]) == 4
    assert "segno" not in doc["measures"][0].get("navigation", [])
    assert "to_coda" in doc["measures"][1]["navigation"]
    assert "dc_al_coda" in doc["measures"][2]["navigation"]
    assert "coda" in doc["measures"][3]["navigation"]
    xml = score_ir_to_musicxml(doc)
    assert "<segno/>" not in xml
    assert ">D.C. al Coda</words>" in xml
    assert 'dacapo="yes"' in xml
    assert "<ending " not in xml


def test_score_ir_speelplan_expand_fallback() -> None:
    """Onherleidbaar plan → uitgeschreven matenvolgorde, geen nav-tekens."""
    doc = export_mvsa_to_score_ir(_three_blok_mvsa("1, 3, 2, 1"))
    assert len(doc["measures"]) == 4
    assert all("ending" not in m for m in doc["measures"])
    assert all(not m.get("navigation") for m in doc["measures"])
    xml = score_ir_to_musicxml(doc)
    assert "<ending " not in xml
    assert "<segno/>" not in xml
    assert "<coda/>" not in xml
    assert xml.count("<measure ") == 8
    assert xml.count(">a</text>") == 2
    assert xml.count(">b</text>") == 1
    assert xml.count(">c</text>") == 1


_FS_SHARP_RUN = """\
@do F4
@mode major
@oct S=0 A=0 T=-1 B=-1

L: a_ b_ c_ ||
S: Bb4 Bb4 Bb4 ||
A: f#4 f#4 f#4 ||
T: d4 d4 d4 ||
B: g3 g3 g3 ||
"""


def test_partituur_accidental_once_per_measure() -> None:
    """F#: <alter> op elke noot; <accidental> alleen op eerste in de maat.

    Via partituur-emit (niet from-IR): Score-IR trekt same-pitch samen tot
    één noot, waardoor die keten geen herhaalde F# meer heeft.
    """
    import xml.etree.ElementTree as ET

    from vsa.mvsa_musicxml import export_mvsa_to_musicxml

    xml = export_mvsa_to_musicxml(_FS_SHARP_RUN, layout="partituur")
    root = ET.fromstring(xml)
    p1 = root.find("part")
    assert p1 is not None
    measure = p1.find("measure")
    assert measure is not None
    f_sharps = [
        n
        for n in measure.findall("note")
        if (n.findtext("pitch/step") == "F" and n.findtext("pitch/alter") == "1")
    ]
    assert len(f_sharps) == 3
    assert f_sharps[0].findtext("accidental") == "sharp"
    assert f_sharps[1].find("accidental") is None
    assert f_sharps[2].find("accidental") is None


def test_from_ir_accidental_resets_each_measure() -> None:
    """Na maatstreep opnieuw een zichtbaar kruis (from-IR / Score-IR)."""
    import xml.etree.ElementTree as ET

    text = """\
@do F4
@mode major
@oct S=0 A=0 T=-1 B=-1

L: a_ | b_ ||
S: Bb4 | Bb4 ||
A: f#4 | f#4 ||
T: d4 | d4 ||
B: g3 | g3 ||
"""
    doc = export_mvsa_to_score_ir(text)
    xml = score_ir_to_musicxml(doc)
    root = ET.fromstring(xml)
    p1 = root.find("part")
    assert p1 is not None
    measures = p1.findall("measure")
    assert len(measures) >= 2
    for mi in (0, 1):
        f_sharps = [
            n
            for n in measures[mi].findall("note")
            if (n.findtext("pitch/step") == "F" and n.findtext("pitch/alter") == "1")
        ]
        assert len(f_sharps) == 1
        assert f_sharps[0].findtext("accidental") == "sharp"
