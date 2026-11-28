"""Welke transliteraties een bron nodig heeft, en welke talen er geen krijgen."""

from __future__ import annotations

import pytest

from vsa.mvsa_musicxml import export_mvsa_to_musicxml
from vsa.transliterate import render_syllable, translit_modi_for_source

_HEAD = '@title "t"\n@do F4\n@mode major\n'


def _system(lyric: str) -> str:
    return f"L: {lyric} ||\nS: a - ||\nA: f - ||\nT: c - ||\nB: f - ||\n"


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (_system("Гос-по_-ди_"), ("nls",)),
        (_system("Va-der_"), ("ksl",)),
        ("@taal ro\n" + _system("Doam-ne_"), ()),
        (
            _system("Гос-по_-ди_") + "@taal ro\n" + _system("Doam-ne_"),
            ("nls",),
        ),
    ],
)
def test_mvsa_modi_uit_gezongen_tekst(tmp_path, body, expected):
    """Stemregels (S/A/T/B) en andere talen tellen niet mee."""
    path = tmp_path / "lied.mvsa"
    path.write_text(_HEAD + body, encoding="utf-8")
    assert translit_modi_for_source(path) == expected


def test_vsa_commentaar_telt_niet_mee(tmp_path):
    path = tmp_path / "lied.vsa"
    path.write_text(
        "---\ntaal: ksl\n---\n\n<!-- Wij verheerlijken U -->\n[:] {Гос_}{по_} [:]\n",
        encoding="utf-8",
    )
    assert translit_modi_for_source(path) == ("nls",)


def test_roemeens_krijgt_geen_transliteratie():
    xml = export_mvsa_to_musicxml(
        _HEAD + "@taal ro\n" + _system("Doam-ne_"), translit=True
    )
    assert 'lyric number="2"' not in xml


def test_vrij_label_houdt_transliteratie():
    xml = export_mvsa_to_musicxml(
        _HEAD + "@taal Lap=aap\nLap: Va-der_ ||\nS: a - ||\nA: f - ||\n"
        "T: c - ||\nB: f - ||\n",
        translit=True,
    )
    assert 'lyric number="2"' in xml


@pytest.mark.parametrize(
    ("bron", "doel"), [("Ky", "Ки"), ("Kyrie", "Кирие"), ("ri", "ри")]
)
def test_kyrie(bron, doel):
    assert render_syllable(bron) == doel
