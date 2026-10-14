"""L-uitvoeraanwijzingen: cesuur, dynamiek, adem, fermata, cresc/dim."""

from __future__ import annotations

import re

from vsa.mvsa_musicxml import export_mvsa_to_musicxml
from vsa.mvsa_normalize import normalize_mvsa_text
from vsa.mvsa_parse import parse_l_positions
from vsa.mvsa_validate import validate_mvsa_text

_MINIMAL = """\
@do F4
@mode major
@sectie x
L: {l}
S: {s}
A: {a}
T: {t}
B: {b}
"""


def _doc(l: str, s: str, a: str | None = None, t: str | None = None, b: str | None = None) -> str:
    a = a if a is not None else s
    t = t if t is not None else s
    b = b if b is not None else s
    return _MINIMAL.format(l=l, s=s, a=a, t=t, b=b)


def test_parse_caesura_after_syllable():
    pos = parse_l_positions("hei_-lig[//]")
    assert len(pos) == 2
    assert pos[0].syllables == ["hei"]
    assert pos[0].marks_after == []
    assert pos[1].syllables == ["lig"]
    assert len(pos[1].marks_after) == 1
    assert pos[1].marks_after[0].kind == "caesura"
    assert pos[1].marks_after[0].raw == "//"


def test_parse_caesura_after_punct_and_melisma():
    pos = parse_l_positions("Heer,_[//]")
    assert len(pos) == 1
    assert pos[0].syllables == ["Heer,"]
    assert pos[0].marks_after[0].kind == "caesura"

    pos2 = parse_l_positions("tus_&_&_[//]")
    assert len(pos2) == 1
    assert pos2[0].elms == ["_", "_", "_"]
    assert pos2[0].marks_after[0].kind == "caesura"


def test_parse_caesura_does_not_add_slot():
    bare = parse_l_positions("hei_-lig")
    marked = parse_l_positions("hei_-lig[//]")
    assert [len(p.elms) for p in bare] == [len(p.elms) for p in marked]


def test_parse_dynamics_before_syllable():
    pos = parse_l_positions("[mf]Heer_")
    assert len(pos) == 1
    assert pos[0].syllables == ["Heer"]
    assert len(pos[0].marks_before) == 1
    assert pos[0].marks_before[0].kind == "dyn_mf"
    assert pos[0].marks_before[0].raw == "mf"


def test_parse_dynamics_between_syllables():
    pos = parse_l_positions("a_[f]b_")
    assert len(pos) == 2
    assert pos[0].marks_before == []
    assert pos[1].marks_before[0].raw == "f"


def test_parse_dynamics_does_not_add_slot():
    bare = parse_l_positions("Heer_ is_")
    marked = parse_l_positions("[mf]Heer_ is_")
    assert [len(p.elms) for p in bare] == [len(p.elms) for p in marked]


def test_validate_unknown_mark():
    text = _doc("a_[xyz] ||", "do ||")
    errs = [d for d in validate_mvsa_text(text) if d.code == "MVSA-MARK"]
    assert errs
    assert "xyz" in errs[0].message


def test_validate_orphan_caesura():
    text = _doc("[//]a_ ||", "do ||")
    errs = [d for d in validate_mvsa_text(text) if d.code == "MVSA-MARK"]
    assert errs
    assert "zonder voorafgaande" in errs[0].message


def test_validate_orphan_dynamics():
    text = _doc("a_[mf] ||", "do ||")
    errs = [d for d in validate_mvsa_text(text) if d.code == "MVSA-MARK"]
    assert errs
    assert "zonder volgende" in errs[0].message


def test_parse_cresc_span():
    pos = parse_l_positions("[cresc]a_ b_[/cresc]")
    assert len(pos) == 2
    assert pos[0].marks_before[0].kind == "cresc"
    assert pos[0].marks_before[0].span_role == "start"
    assert pos[1].marks_after[0].kind == "cresc"
    assert pos[1].marks_after[0].span_role == "stop"


def test_parse_dim_span():
    pos = parse_l_positions("[dim]a_ b_[/dim]")
    assert pos[0].marks_before[0].kind == "dim"
    assert pos[1].marks_after[0].kind == "dim"


def test_validate_open_cresc_without_stop():
    text = _doc("[cresc]a_ b_ ||", "do re ||")
    errs = [d for d in validate_mvsa_text(text) if d.code == "MVSA-MARK"]
    assert errs
    assert "zonder stop" in errs[0].message


def test_validate_orphan_cresc_stop():
    text = _doc("a_[/cresc] ||", "do ||")
    errs = [d for d in validate_mvsa_text(text) if d.code == "MVSA-MARK"]
    assert errs
    assert "zonder passende start" in errs[0].message


def test_validate_nested_wedges():
    text = _doc("[cresc]a_ [dim]b_ c_[/dim] d_[/cresc] ||", "do re mi fa ||")
    errs = [d for d in validate_mvsa_text(text) if d.code == "MVSA-MARK"]
    assert errs
    assert "geneste" in errs[0].message


def test_validate_ok_cresc_span():
    text = _doc("[cresc]a_ b_[/cresc] ||", "do re ||")
    errs = [d for d in validate_mvsa_text(text) if d.severity == "error"]
    assert errs == []


def test_normalize_decresc_alias():
    text = _doc("[decresc]a_ b_[/decresc] ||", "do re ||")
    out = normalize_mvsa_text(text, align=False)
    assert "[dim]" in out
    assert "[/dim]" in out
    assert "[decresc]" not in out
    assert "[/decresc]" not in out


def test_validate_ok_with_caesura():
    text = _doc("a_[//] ||", "do ||")
    errs = [d for d in validate_mvsa_text(text) if d.severity == "error"]
    assert errs == []


def test_validate_ok_with_dynamics():
    text = _doc("[mf]a_ ||", "do ||")
    errs = [d for d in validate_mvsa_text(text) if d.severity == "error"]
    assert errs == []


def test_export_caesura_in_partituur():
    text = _doc("a_[//] ||", "do ||")
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert "<caesura/>" in xml
    assert "[//]" not in xml
    assert re.search(r"<text>a</text>", xml)


def test_export_playback_caesura_becomes_rest():
    text = _doc("a_[//] b_ ||", "do re ||")
    xml = export_mvsa_to_musicxml(text, layout="playback")
    assert "<rest" in xml
    assert xml.count("<rest") >= 4


def _dynamics_count(xml: str, name: str) -> int:
    """Tel ``<dynamics><name/></dynamics>`` (met of zonder spatie in lege tag)."""
    return len(re.findall(rf"<dynamics><{name}\s*/></dynamics>", xml))


def test_export_dynamics_partituur_soprano_only():
    text = _doc("[mf]a_ ||", "do ||")
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert _dynamics_count(xml, "mf") >= 1
    assert "[mf]" not in xml
    # één keer op het blad (sopraan), niet per stem
    assert _dynamics_count(xml, "mf") == 1


def test_export_dynamics_playback_all_parts():
    text = _doc("[p]a_ ||", "do ||")
    xml = export_mvsa_to_musicxml(text, layout="playback")
    assert _dynamics_count(xml, "p") == 4


def test_parse_breath_and_fermata():
    pos = parse_l_positions("a_[adem]")
    assert pos[0].marks_after[0].kind == "breath"
    pos2 = parse_l_positions("a_[ferm]")
    assert pos2[0].marks_after[0].kind == "fermata"


def test_export_breath_and_fermata_partituur():
    text = _doc("a_[adem] b_[ferm] ||", "do re ||")
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert "<breath-mark/>" in xml or "<breath-mark />" in xml
    assert '<fermata type="upright"/>' in xml or 'type="upright"' in xml
    assert "[adem]" not in xml
    assert "[ferm]" not in xml


def test_export_playback_strips_breath_fermata_notations():
    """Coria sanitize stript <notations>; geen beloofde speelduur voor adem/ferm."""
    text = _doc("a_[adem] b_[ferm] ||", "do re ||")
    xml = export_mvsa_to_musicxml(text, layout="playback")
    assert "breath-mark" not in xml
    assert "fermata" not in xml


def _wedge_count(xml: str, wedge_type: str) -> int:
    return len(re.findall(rf'<wedge type="{wedge_type}"', xml))


def test_export_cresc_partituur_soprano_only():
    text = _doc("[cresc]a_ b_[/cresc] ||", "do re ||")
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert _wedge_count(xml, "crescendo") == 1
    assert _wedge_count(xml, "stop") == 1
    assert "[cresc]" not in xml
    assert "[/cresc]" not in xml


def test_export_dim_playback_all_parts():
    text = _doc("[dim]a_ b_[/dim] ||", "do re ||")
    xml = export_mvsa_to_musicxml(text, layout="playback")
    assert _wedge_count(xml, "diminuendo") == 4
    assert _wedge_count(xml, "stop") == 4


def test_parse_rit_atempo():
    pos = parse_l_positions("[rit]a_ [atempo]b_")
    assert pos[0].marks_before[0].kind == "rit"
    assert pos[1].marks_before[0].kind == "atempo"


def test_validate_ok_rit_atempo():
    text = _doc("[rit]a_ [atempo]b_ ||", "do re ||")
    errs = [d for d in validate_mvsa_text(text) if d.severity == "error"]
    assert errs == []


def test_export_rit_atempo_partituur():
    text = _doc("[rit]a_ [atempo]b_ ||", "do re ||")
    xml = export_mvsa_to_musicxml(text, layout="partituur")
    assert "<words>rit.</words>" in xml
    assert "<words>a tempo</words>" in xml
    assert "[rit]" not in xml
    assert "[atempo]" not in xml
    # zichtbaar op sopraan, niet per stem
    assert xml.count("<words>rit.</words>") == 1


def test_export_rit_playback_all_parts():
    text = _doc("[rit]a_ ||", "do ||")
    xml = export_mvsa_to_musicxml(text, layout="playback")
    assert xml.count("<words>rit.</words>") == 4
