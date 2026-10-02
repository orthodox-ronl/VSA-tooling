"""Fase 3: sticky @taal stuurt hulptekst-richting per passage."""

from __future__ import annotations

from pathlib import Path

from vsa.mvsa_musicxml import export_mvsa_to_musicxml
from vsa.mvsa_parse import parse_mvsa
from vsa.mvsa_validate import validate_mvsa_text

ROOT = Path(__file__).resolve().parents[1]
GEMENGD = (
    ROOT / "examples" / "mvsa" / "hulptekst-gemengd-taal-mini.mvsa"
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
    xml = export_mvsa_to_musicxml(GEMENGD, layout="playback", hulptekst=True)
    # NL-passage → Cyrillisch
    assert "<text>Хер</text>" in xml
    assert "<text>онт</text>" in xml
    assert "<text>Heer</text>" in xml
    # KSL-passage → Latijn
    assert "<text>Гос</text>" in xml
    assert "<text>Gos</text>" in xml
    assert "<text>loej</text>" in xml
