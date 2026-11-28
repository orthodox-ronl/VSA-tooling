from vsa.beginnoten import (
    Beginnoot,
    beginnoot_uit_vsa,
    beginnoten_uit_musicxml,
    laddergraad,
    notennaam,
)


def _noot(voice, step, octave, alter=0):
    a = f"<alter>{alter}</alter>" if alter else ""
    return (
        f"<note><pitch><step>{step}</step>{a}<octave>{octave}</octave></pitch>"
        f"<voice>{voice}</voice></note>"
    )


def _stuk(fifths, boven, onder):
    key = f"<attributes><key><fifths>{fifths}</fifths></key></attributes>"
    return (
        f"<score-partwise><part id='P1'><measure>{key}{boven}</measure></part>"
        f"<part id='P2'><measure>{onder}</measure></part></score-partwise>"
    )


def test_satb_met_graad_en_naam(tmp_path):
    rust = "<note><rest/><voice>1</voice></note>"
    pad = tmp_path / "a.from-ir.musicxml"
    pad.write_text(
        _stuk(-1, rust + _noot(1, "A", 4) + _noot(2, "F", 4),
              _noot(1, "C", 4) + _noot(2, "F", 3)),
        encoding="utf-8",
    )
    noten = beginnoten_uit_musicxml(pad)
    assert [n.stem for n in noten] == ["S", "A", "T", "B"]
    assert [n.graad for n in noten] == ["mi", "do", "so", "do"]
    assert [n.naam for n in noten] == ["A", "F", "C", "F"]


def test_andere_opbouw_geeft_none(tmp_path):
    pad = tmp_path / "a.from-ir.musicxml"
    pad.write_text(_stuk(0, _noot(1, "C", 4), _noot(1, "C", 3)), encoding="utf-8")
    assert beginnoten_uit_musicxml(pad) is None


def test_namen_en_chromatische_graden():
    assert [notennaam(*n) for n in (("B", -1), ("E", -1), ("A", -1), ("D", -1),
                                    ("F", 1), ("B", 0), ("E", -2))] == [
        "Bes", "Es", "As", "Des", "Fis", "B", "Eses"]
    assert laddergraad("E", -1, "F", 0) == "bti"
    assert laddergraad("B", 0, "F", 0) == "#fa"
    assert laddergraad("B", -1, "E", -1) == "so"


def test_melodie_uit_vsa(tmp_path):
    pad = tmp_path / "a.vsa"
    pad.write_text("---\ndo: Eb4\n---\n\\==ligt{Heer}\n", encoding="utf-8")
    assert beginnoot_uit_vsa(pad) == [Beginnoot("", "Es", "do")]
