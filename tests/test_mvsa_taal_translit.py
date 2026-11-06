"""Fase 3: sticky @taal stuurt hulptekst-richting per passage."""

from __future__ import annotations

from pathlib import Path

from vsa.mvsa_musicxml import export_mvsa_to_musicxml
from vsa.mvsa_parse import parse_mvsa
from vsa.mvsa_validate import validate_mvsa_text

ROOT = Path(__file__).resolve().parents[1]
GEMENGD = (
    ROOT / "examples" / "mvsa" / "translit-gemengd-taal-mini.mvsa"
).read_text(encoding="utf-8")


def test_taal_sticky_parsed() -> None:
    doc = parse_mvsa(GEMENGD)
    assert len(doc.diagnostics) == 0 or all(
        d.severity != "error" for d in doc.diagnostics
    )
    systems = [sys for sec in doc.sections for sys in sec.systems]
    assert systems[0].context.taal == "nl"
    assert systems[1].context.taal == "ksl"


def test_taal_invalid_value() -> None:
    text = "@taal fr\nL: a_ |\nS: do |\n"
    diags = validate_mvsa_text(text)
    assert any(d.code == "MVSA-TAAL" for d in diags)


def test_gemengd_hulptekst_respects_taal() -> None:
    xml = export_mvsa_to_musicxml(GEMENGD, layout="playback", translit=True)
    # NL-passage → Cyrillisch
    assert "<text>Хиир</text>" in xml
    assert "<text>онт</text>" in xml
    assert "<text>Heer</text>" in xml
    # KSL-passage → Latijn
    assert "<text>Гос</text>" in xml
    assert "<text>Gos</text>" in xml
    assert "<text>loej</text>" in xml


def test_gemengd_translit_modus_nls_only_ksl_to_latin() -> None:
    """Ксл→Nls: Latijn onder Ksl; Nederlandse passage zonder hulpregel."""
    xml = export_mvsa_to_musicxml(
        GEMENGD, layout="playback", translit=True, translit_modus="nls"
    )
    assert "<text>Heer</text>" in xml
    assert "<text>Хиир</text>" not in xml
    assert "<text>онт</text>" not in xml
    assert "<text>Гос</text>" in xml
    assert "<text>Gos</text>" in xml
    assert "<text>loej</text>" in xml


def test_gemengd_translit_modus_ksl_only_nl_to_cyrillic() -> None:
    """Nls→Ксл: Cyrillisch onder NL; kerkslavische passage zonder hulpregel."""
    xml = export_mvsa_to_musicxml(
        GEMENGD, layout="playback", translit=True, translit_modus="ksl"
    )
    assert "<text>Heer</text>" in xml
    assert "<text>Хиир</text>" in xml
    assert "<text>онт</text>" in xml
    assert "<text>Гос</text>" in xml
    assert "<text>Gos</text>" not in xml
    assert "<text>loej</text>" not in xml


def test_hybrid_auto_script_respects_translit_modus() -> None:
    """Zonder @taal: auto per schrift + modusfilter (hybride bron)."""
    text = """\
@do F4
@mode major
@oct S=0 A=0 T=-1 B=-1

L: Heer_ |
S: a4    |
A: f4    |
T: c4    |
B: f3    |

L: Гос_ |
S: a4   |
A: f4   |
T: c4   |
B: f3   |
"""
    nls = export_mvsa_to_musicxml(
        text, layout="playback", translit=True, translit_modus="nls"
    )
    assert "<text>Heer</text>" in nls
    assert "<text>Хиир</text>" not in nls
    assert "<text>Гос</text>" in nls
    assert "<text>Gos</text>" in nls

    ksl = export_mvsa_to_musicxml(
        text, layout="playback", translit=True, translit_modus="ksl"
    )
    assert "<text>Heer</text>" in ksl
    assert "<text>Хиир</text>" in ksl
    assert "<text>Гос</text>" in ksl
    assert "<text>Gos</text>" not in ksl
