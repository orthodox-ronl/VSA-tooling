"""Score-IR export (partituur profile)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vsa.score_ir import (
    SCORE_IR_FORMAT,
    SCORE_IR_PROFILE,
    SCORE_IR_VERSION,
    export_mvsa_path_to_score_ir,
    export_mvsa_to_score_ir,
)

ROOT = Path(__file__).resolve().parents[1]
VREDE = ROOT / "examples" / "mvsa" / "1a-vredeslitanie.mvsa"


def test_export_vredeslitanie_shape() -> None:
    text = VREDE.read_text(encoding="utf-8")
    doc = export_mvsa_to_score_ir(text)
    assert doc["format"] == SCORE_IR_FORMAT
    assert doc["version"] == SCORE_IR_VERSION
    assert doc["profile"] == SCORE_IR_PROFILE
    assert doc["pitchContext"]["do"] == "F4"
    assert doc["meta"]["title"]
    assert len(doc["measures"]) >= 2

    m1 = doc["measures"][0]
    assert m1["id"] == "m1"
    assert m1["cues"], "eerste maat hoort @tekst-cue te hebben"
    assert m1["cues"][0]["kind"] == "tekst"
    assert "Gezegend" in m1["cues"][0]["text"]
    assert m1["cues"][0]["anchor"] == "measure-start"
    assert m1["lyrics"], "lyrics op maat 1"
    for letter in ("S", "A", "T", "B"):
        assert letter in m1["voices"]
        assert m1["voices"][letter], f"stem {letter} leeg op m1"
        ev0 = m1["voices"][letter][0]
        assert "pitch" in ev0 and "step" in ev0["pitch"]
        assert ev0["duration"]["elm"]


def test_export_path_writes_json(tmp_path: Path) -> None:
    out = tmp_path / "out.score-ir.json"
    export_mvsa_path_to_score_ir(VREDE, out)
    raw = json.loads(out.read_text(encoding="utf-8"))
    assert raw["format"] == SCORE_IR_FORMAT
    assert raw["measures"][0]["cues"]


def test_unknown_section_raises() -> None:
    from vsa.mvsa_musicxml import MvsaExportError

    text = VREDE.read_text(encoding="utf-8")
    with pytest.raises(MvsaExportError, match="sectie"):
        export_mvsa_to_score_ir(text, section_id="bestaat-niet")


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


def test_score_ir_s8_recite_print_fields() -> None:
    """Lange recite (≥6): S8 1-(n-2)-1 met print.spacer / breveHead in IR."""
    doc = export_mvsa_to_score_ir(_S8_RECITE)
    m1 = doc["measures"][0]
    sop = m1["voices"]["S"]
    prints = [ev.get("print") or {} for ev in sop]
    assert any(p.get("breveHead") for p in prints), "||O||-midden ontbreekt"
    spacers = [p for p in prints if p.get("spacer")]
    assert spacers, "recite-spacers ontbreken in IR"
    assert all(p.get("stemless") for p in prints if p.get("spacer"))
    # Zichtbare randnoten: geen spacer/breveHead
    visible = [
        ev
        for ev in sop
        if not (ev.get("print") or {}).get("spacer")
        and not (ev.get("print") or {}).get("breveHead")
    ]
    assert len(visible) >= 2


_S8_SHORT_RECITE_PLUS_SAME = """\
@do F4
@mode major
@oct S=0 A=0 T=-1 B=-1

L: (Al-le-lu-ja, Al) -le -lu_ ||
S:  a                 a   /   ||
A:  f+                -   -   ||
T:  c                 c   /   ||
B:  f                 f   bb  ||
"""


def test_score_ir_s8_extends_short_recite_same_pitch() -> None:
    """Korte recite (5) + zelfde-toon-vervolg → S8 (zoals Alleluia toon 3)."""
    doc = export_mvsa_to_score_ir(_S8_SHORT_RECITE_PLUS_SAME)
    sop = doc["measures"][0]["voices"]["S"]
    prints = [ev.get("print") or {} for ev in sop]
    assert any(p.get("breveHead") for p in prints), "||O||-midden ontbreekt"
    assert any(p.get("spacer") for p in prints), "recite-spacers ontbreken"
    # Eerste zichtbare rand + breve + spacers + laatste rand, daarna melodie.
    assert sop[0].get("recite") is True
    assert (sop[1].get("print") or {}).get("breveHead") is True


def test_score_ir_short_recite_keeps_syllables() -> None:
    """Korte recite zonder verlenging: één noot per lettergreep (geen melisma-eat)."""
    text = """\
@do F4
@mode major
@oct S=0 A=0 T=-1 B=-1

L: (Al-le-lu) -ja ||
S:  Bb         /  ||
A:  g          -  ||
T:  d          \\  ||
B:  g          \\2 ||
"""
    doc = export_mvsa_to_score_ir(text)
    sop = doc["measures"][0]["voices"]["S"]
    recite_evs = [ev for ev in sop if ev.get("recite")]
    assert len(recite_evs) == 3, f"verwacht 3 recite-noten, kreeg {len(recite_evs)}"
    assert not any((ev.get("print") or {}).get("breveHead") for ev in sop)


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


def test_score_ir_s13_same_pitch_compact() -> None:
    """Same-pitch melisma → één compacte (gestipte) noot in Score-IR (OSMD-eindvorm)."""
    doc = export_mvsa_to_score_ir(_S13_MELISMA)
    sop = doc["measures"][0]["voices"]["S"]
    sounding = [ev for ev in sop if ev.get("pitch")]
    assert len(sounding) == 1, f"verwacht 1 noot, kreeg {len(sounding)}"
    # half + half = whole, of gestipte vorm via elm
    assert sounding[0]["duration"]["elm"] in {"__", "_.", "_"}


def test_score_ir_s13_dotted_whole_elm() -> None:
    """S13: whole+half same-pitch → ELM ``__.`` (niet stil ``~`` / gevulde kwart)."""
    text = """\
@do F4
@mode major
@oct S=0 A=-1 T=-1 B=-1

L: a__&_ ||
S: g&-   ||
A: d&-   ||
T: -&-   ||
B: g&-   ||
"""
    doc = export_mvsa_to_score_ir(text)
    for voice in ("S", "A", "T", "B"):
        sounding = [
            ev for ev in doc["measures"][0]["voices"][voice] if ev.get("pitch")
        ]
        assert len(sounding) == 1, f"{voice}: {sounding}"
        assert sounding[0]["duration"]["elm"] == "__.", (
            f"{voice}: verwacht ``__.``, kreeg {sounding[0]['duration']}"
        )


def test_score_ir_lyric_index_follows_voice_not_s_event_index() -> None:
    """lyricIndex = n-de lyric-noot per stem; S-event-index faalt na S13-collapse.

    Regressie alleluia-toon-2: T korter dan S → «lu»/«ja» kregen verkeerde index.
    """
    path = ROOT / "examples" / "bug-cases" / "corib" / "alleluia-toon-2.mvsa"
    doc = export_mvsa_to_score_ir(path.read_text(encoding="utf-8"))
    m0 = doc["measures"][0]
    texts = [
        "".join(s["text"] for s in ly.get("syllables", []))
        for ly in m0["lyrics"]
    ]
    assert "lu" in texts and texts.count("lu") >= 2

    ten = m0["voices"]["T"]
    assert len(ten) < len(m0["voices"]["S"]), "preconditie: T korter na S13"

    for voice in ("S", "A", "T", "B"):
        idxs = [
            ev["lyricIndex"]
            for ev in m0["voices"][voice]
            if ev.get("lyricIndex") is not None
        ]
        assert idxs == list(range(len(texts))), f"{voice}: lyricIndex {idxs}"

    last_lu = max(i for i, t in enumerate(texts) if t == "lu")
    t_lu = next(ev for ev in ten if ev.get("lyricIndex") == last_lu)
    assert t_lu["duration"]["elm"] == "__.", (
        f"T laatste «lu» moet ``__.`` zijn, kreeg {t_lu['duration']}"
    )


def test_score_ir_s13_pitch_change_melisma_closes_slur() -> None:
    """S13/S2: melisma met toonwissel + trailing hold → slurStart én slurStop (K3).

    Regressie cherubijnenhymne (alt/bas ``d4&c4&-``): open slur liep door
    over volgende lettergrepen/maten.
    """
    text = """\
@do F4
@mode major
@oct S=0 A=-1 T=-1 B=-2

L: uit~&~&~ ||
S: g4&f4&e4 ||
A: d4&c4&-  ||
B: Bb2&c3&- ||
"""
    doc = export_mvsa_to_score_ir(text)
    for voice in ("S", "A", "B"):
        evs = doc["measures"][0]["voices"][voice]
        starts = [
            i
            for i, ev in enumerate(evs)
            if (ev.get("melisma") or {}).get("slurStart")
        ]
        stops = [
            i
            for i, ev in enumerate(evs)
            if (ev.get("melisma") or {}).get("slurStop")
        ]
        assert starts and stops, f"{voice}: melisma-slur ontbreekt ({starts=}, {stops=})"
        assert len(starts) == len(stops) == 1, f"{voice}: {starts=} {stops=}"
        assert starts[0] < stops[0], f"{voice}: slur volgorde {starts[0]}≥{stops[0]}"


def test_score_ir_k2_hyphen_syllables_not_merged_as_melisma() -> None:
    """K2/L3/M5a: twee lettergrepen same-pitch in één maat blijven twee noten.

    ``-beel_-den~`` met ``f4 -`` mag niet tot één noot + weggegooid «den».
    """
    text = """\
@do F4
@mode major
@oct S=0 A=-1 T=-1 B=-2

L: -beel_-den~ ||
S: f4     -    ||
A: -      -    ||
B: f2     -    ||
"""
    doc = export_mvsa_to_score_ir(text)
    m0 = doc["measures"][0]
    texts = [
        "".join(s["text"] for s in ly.get("syllables", []))
        for ly in m0["lyrics"]
    ]
    assert "beel" in texts and "den" in texts, f"lettergrepen kwijt: {texts}"
    sop = [ev for ev in m0["voices"]["S"] if ev.get("pitch")]
    assert len(sop) == 2, f"S: verwacht 2 noten, kreeg {len(sop)}"
    assert not any(
        (ev.get("melisma") or {}).get("slurStart") for ev in m0["voices"]["S"]
    ), "hyphen-lettergrepen mogen geen melisma-slur krijgen (L3/S2)"


def test_score_ir_s8_keeps_all_lyrics_no_phrase_slur() -> None:
    """S8-spacers behouden lettergrepen; geen slur van eerste naar laatste noot."""
    # Minimaal: lange recite + aparte cadens-noot (andere toon).
    text = """\
@do F4
@mode major
@oct S=0 A=0 T=-1 B=-1

L: (Al-le-lu-ia, al-le) -ia ||
S:  Bb                  /   ||
A:  g                   -   ||
T:  d                   \\   ||
B:  g                   \\2  ||
"""
    doc = export_mvsa_to_score_ir(text)
    m1 = doc["measures"][0]
    texts = [
        "".join(s["text"] for s in ly.get("syllables", []))
        for ly in m1["lyrics"]
    ]
    joined = " ".join(texts)
    assert "Al" in joined and "le" in joined and "lu" in joined
    assert len(m1["lyrics"]) >= 6, f"te weinig lyric-posities: {texts}"
    sop = m1["voices"]["S"]
    starts = [
        i for i, ev in enumerate(sop) if (ev.get("melisma") or {}).get("slurStart")
    ]
    stops = [
        i for i, ev in enumerate(sop) if (ev.get("melisma") or {}).get("slurStop")
    ]
    if starts and stops:
        assert not (starts == [0] and stops == [len(sop) - 1]), (
            "frase-slur over hele maat (S8+cadens) mag niet"
        )


def test_serialize_rest_event() -> None:
    """Rusten (pitch=None) horen als rest:true in Score-IR, geen crash."""
    from vsa.music import Duration
    from vsa.mvsa_musicxml import NoteEvent
    from vsa.score_ir import _serialize_voice_event

    ev = NoteEvent(
        pitch=None,
        duration=Duration(note_type="whole", dots=0, divisions=4),
        lyrics=[],
    )
    out = _serialize_voice_event(ev, lyric_index=None)
    assert out.get("rest") is True
    assert "pitch" not in out
    assert out["duration"]["elm"] == "__"
