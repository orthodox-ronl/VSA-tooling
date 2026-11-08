"""Spike Score-IR → eigen SVG: Alleluia toon 8, S4 / S8 / S13 + één VSA-accent."""

from __future__ import annotations

import importlib.util
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from vsa.score_ir import export_mvsa_to_score_ir

ROOT = Path(__file__).resolve().parents[1]
SPIKE = ROOT / "examples" / "spikes" / "score-ir-svg"
# corib-bron: sopraan «le» is `so` = C5, boven de alt-G. examples/mvsa heeft `so-` (C4).
MVSA = ROOT / "examples" / "bug-cases" / "corib" / "alleluia-toon-8.mvsa"


def _render():
    spec = importlib.util.spec_from_file_location(
        "render_score_ir_svg",
        SPIKE / "render_score_ir_svg.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _classes(el: ET.Element) -> set[str]:
    return set((el.attrib.get("class") or "").split())


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def test_alleluia_toon_8_svg_shows_s4_s8_s13_and_one_accent() -> None:
    module = _render()
    doc = export_mvsa_to_score_ir(MVSA.read_text(encoding="utf-8"), title="Alleluia - Toon 8")
    svg = module.render_score_ir_svg(doc)

    assert 'width="100%"' in svg
    assert "viewBox=" in svg

    root = ET.fromstring(svg)
    sop = doc["measures"][0]["voices"]["S"]
    lyrics = doc["measures"][0]["lyrics"]

    notes = [el for el in root.iter() if "note" in _classes(el) and el.attrib.get("data-voice")]
    by_voice: dict[str, dict[int, str]] = {v: {} for v in "SATB"}
    for el in notes:
        voice = el.attrib["data-voice"]
        if "data-lyric-index" in el.attrib:
            by_voice[voice][int(el.attrib["data-lyric-index"])] = el.attrib["data-kind"]
        if el.attrib.get("data-kind") == "spacer":
            assert not any("notehead" in _classes(child) or "breve-head" in _classes(child) for child in el.iter())

    # S8: 1 – breve – spacers – 1, op elke stem dezelfde lyric-indexen.
    breve_at = next(i for i, ev in enumerate(sop) if (ev.get("print") or {}).get("breveHead"))
    spacer_at = [i for i, ev in enumerate(sop) if (ev.get("print") or {}).get("spacer")]
    assert spacer_at, "S8-spacers ontbreken in de bron-IR"
    edge_before = sop[breve_at - 1]["lyricIndex"]
    edge_after = next(
        ev["lyricIndex"]
        for ev in sop[spacer_at[-1] + 1 :]
        if ev.get("lyricIndex") is not None and not (ev.get("print") or {}).get("spacer")
    )
    for voice in "SATB":
        assert by_voice[voice][edge_before] == "note"
        assert by_voice[voice][sop[breve_at]["lyricIndex"]] == "breve"
        for ev in sop:
            if (ev.get("print") or {}).get("spacer"):
                assert by_voice[voice][ev["lyricIndex"]] == "spacer"
        assert by_voice[voice][edge_after] == "note"

    stems = [el for el in root.iter() if "stem" in _classes(el)]
    assert stems, "S4: verwachte stokken"
    for el in stems:
        voice = el.attrib["data-voice"]
        classes = _classes(el)
        if voice in {"S", "T"}:
            assert "stem-up" in classes and "stem-down" not in classes
        else:
            assert "stem-down" in classes and "stem-up" not in classes
    assert {el.attrib["data-voice"] for el in stems} == {"S", "A", "T", "B"}

    slurs = [el for el in root.iter() if "melisma-slur" in _classes(el)]
    assert {el.attrib["data-voice"] for el in slurs} == {"S", "A", "T", "B"}
    for el in slurs:
        assert int(el.attrib["data-from"]) > 0
        assert int(el.attrib["data-from"]) < int(el.attrib["data-to"])
    assert any("melisma-extend" in _classes(el) for el in root.iter())

    texts = [
        el.text or ""
        for el in root.iter()
        if _local(el.tag) == "text" and "lyric" in _classes(el)
    ]
    assert texts == ["".join(s["text"] for s in ly["syllables"]) for ly in lyrics]

    # Laatste «le» (na de recite) is C5 en staat boven de G van de alt.
    le_index = next(
        i
        for i, ly in enumerate(lyrics)
        if "".join(s["text"] for s in ly["syllables"]) == "le"
        and not any(
            (ev.get("print") or {}).get("spacer")
            for ev in sop
            if ev.get("lyricIndex") == i
        )
        and any(ev.get("lyricIndex") == i and ev["pitch"]["octave"] == 5 for ev in sop)
    )
    s_le = next(el for el in notes if el.attrib.get("data-voice") == "S" and el.attrib.get("data-lyric-index") == str(le_index))
    a_le = next(el for el in notes if el.attrib.get("data-voice") == "A" and el.attrib.get("data-lyric-index") == str(le_index))
    assert s_le.attrib["data-step"] == "C" and s_le.attrib["data-octave"] == "5"
    assert float(s_le.attrib["data-cy"]) < float(a_le.attrib["data-cy"])

    marks = [el for el in root.iter() if "vsa-mark" in _classes(el)]
    tokens = [el.attrib["data-ehm"] for el in marks]
    assert tokens == [token for _i, token, _glyph in module.soprano_vsa_tokens(doc)]
    assert "/" in tokens and "\\2" in tokens and tokens.count("-") >= 6
