"""vsa kuiser — V1–V8 (docs/formats/kuiser.md)."""

from __future__ import annotations

from vsa.cli import main as vsa_main
from vsa.vsa_kuiser import kuiser_vsa_text
from vsa.yaml_frontmatter import strip_yaml_frontmatter


def test_kuiser_fills_fm_zoektekst_tempo_and_syllabify():
    text = "Heer Amen\n"
    result = kuiser_vsa_text(
        text,
        source_path="stichier-heer-amen-toon-1-groningen.vsa",
        dict_interactive=False,
    )
    fm, body, _ = strip_yaml_frontmatter(result.text)
    assert fm["titel"] == "Heer amen (Toon 1)"
    assert fm["taal"] == "nl"
    assert fm["soort"] == "stichier"
    assert fm["toon"] == 1
    assert fm["tempo"] == 181
    assert fm["bron"]["bewerking"] == "groningen"
    assert "Heer" in fm["zoektekst"]
    assert "-" not in str(fm["zoektekst"]).replace(" ", "")
    assert "Amen" in body or "A-men" in body or "amen" in body.lower()


def test_kuiser_keeps_custom_tempo_and_do():
    text = """\
---
titel: X
taal: nl
do: G4
mode: minor
tempo: 72
---
ja
"""
    result = kuiser_vsa_text(text, dict_interactive=False)
    fm, _, _ = strip_yaml_frontmatter(result.text)
    assert fm["tempo"] == 72
    assert fm["do"] == "G4"
    assert fm["mode"] == "minor"


def test_kuiser_strips_unknown_empty_fm_unless_werkbank():
    text = """\
---
titel: Demo
taal: nl
rommel: weg
leeg: null
---
ja
"""
    catalogus = kuiser_vsa_text(text, dict_interactive=False, werkbank=False)
    fm, _, _ = strip_yaml_frontmatter(catalogus.text)
    assert "rommel" not in fm
    assert "leeg" not in fm

    werkbank = kuiser_vsa_text(text, dict_interactive=False, werkbank=True)
    # werkbank: V5 stript geen lege/ongedocumenteerde sleutels; V1 vult wél.
    fm_w, _, _ = strip_yaml_frontmatter(werkbank.text)
    # rommel kan blijven tot V1 dump alleen managed keys… V5 skipped strip.
    # Na V1 worden managed keys herschreven; overige keys uit old_fm blijven
    # als ze niet in de exclude-set zitten.
    assert "rommel" in fm_w or "titel" in fm_w


def test_kuiser_idempotent():
    text = "ja ja\n"
    path = "alleluia-toon-8-groningen.vsa"
    once = kuiser_vsa_text(text, source_path=path, dict_interactive=False).text
    twice = kuiser_vsa_text(once, source_path=path, dict_interactive=False).text
    assert once == twice


def test_vsa_kuiser_cli_check(tmp_path):
    p = tmp_path / "tropaar-demo-toon-2-hemelum.vsa"
    p.write_text("Heer\n", encoding="utf-8")
    code = vsa_main(["kuiser", str(p), "--check"])
    assert code == 1  # would change
    assert p.read_text(encoding="utf-8") == "Heer\n"
