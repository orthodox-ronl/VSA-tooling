"""Kuiser Q1 — YAML-frontmatter (docs/formats/kuiser.md)."""

from __future__ import annotations

from vsa.mvsa_kuiser import kuiser_mvsa_text
from vsa.mvsa_kuiser_q1 import apply_q1
from vsa.mvsa_kuiser_q23 import apply_q2_q3
from vsa.yaml_frontmatter import strip_yaml_frontmatter


_BODY = """\
@do F4
@mode major
@sectie a
L: ja ja ||
S: fa so ||
A: re re ||
T: la- so- ||
B: re re ||
"""


def test_q1_fills_fm_from_at_and_path():
    after_q23 = apply_q2_q3(
        _BODY, source_path="stichier-heer-ik-roep-toon-1-groningen.mvsa"
    )
    out = apply_q1(
        after_q23,
        source_path="stichier-heer-ik-roep-toon-1-groningen.mvsa",
    )
    fm, body, _ = strip_yaml_frontmatter(out)
    assert fm["titel"] == "Heer ik roep (Toon 1)"
    assert fm["taal"] == "nl"
    assert fm["soort"] == "stichier"
    assert fm["toon"] == 1
    assert fm["do"] == "F4"
    assert fm["mode"] == "major"
    assert fm["tempo"] == 181
    assert fm["bron"]["bewerking"] == "groningen"
    assert "uitgangspunt" not in fm.get("bron", {})
    assert "ja" in fm["zoektekst"].lower()
    assert "@do F4" in body
    assert "#maat 1" in body


def test_q1_at_wins_over_yaml_titel_do_tempo():
    text = """\
---
titel: Oude titel
taal: nl
do: C4
mode: major
tempo: 130
---
@title "Nieuwe titel"
@do G4
@mode minor
@tempo 72
@sectie a
L: ja ||
S: so ||
A: mi ||
T: do ||
B: do ||
"""
    after = apply_q2_q3(text)
    out = apply_q1(after)
    fm, _, _ = strip_yaml_frontmatter(out)
    assert fm["titel"] == "Nieuwe titel"
    assert fm["do"] == "G4"
    assert fm["mode"] == "minor"
    assert fm["tempo"] == 72


def test_q1_keeps_bron_uitgangspunt():
    text = """\
---
bron:
  uitgangspunt: handschrift X
  bewerking: oud
---
@do F4
@mode major
@sectie a
L: ja ||
S: fa ||
A: re ||
T: la- ||
B: re ||
"""
    after = apply_q2_q3(
        text, source_path="stichier-amen-toon-2-hemelum.mvsa"
    )
    out = apply_q1(
        after, source_path="stichier-amen-toon-2-hemelum.mvsa"
    )
    fm, _, _ = strip_yaml_frontmatter(out)
    assert fm["bron"]["uitgangspunt"] == "handschrift X"
    # Bestaande bewerking blijft; pad vult alleen als ontbreekt.
    assert fm["bron"]["bewerking"] == "oud"


def test_q1_idempotent_via_full_kuiser():
    path = "alleluia-toon-8-groningen.mvsa"
    once = kuiser_mvsa_text(_BODY, source_path=path).text
    twice = kuiser_mvsa_text(once, source_path=path).text
    assert once == twice
    fm, _, _ = strip_yaml_frontmatter(once)
    assert fm["soort"] == "alleluia"
    assert fm["toon"] == 8
    assert fm["tempo"] == 131
    assert fm["bron"]["bewerking"] == "groningen"
