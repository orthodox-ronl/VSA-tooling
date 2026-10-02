"""Integratietests: hulptekst lyric number 2 en Coria-dubbelparts."""

from __future__ import annotations

from pathlib import Path

import pytest

from vsa.mvsa_musicxml import MvsaExportError, export_mvsa_to_musicxml
from vsa.mvsa_parse import parse_mvsa
from vsa.mvsa_validate import validate_mvsa_text

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "mvsa"

KSL_MINI = (EXAMPLES / "hulptekst-ksl-mini.mvsa").read_text(encoding="utf-8")
NL_MINI = (EXAMPLES / "hulptekst-nl-mini.mvsa").read_text(encoding="utf-8")
PARALLEL = (EXAMPLES / "hulptekst-parallel-l1-mini.mvsa").read_text(
    encoding="utf-8"
)


def test_ksl_partituur_lyric_number_2() -> None:
    xml = export_mvsa_to_musicxml(
        KSL_MINI, layout="partituur", hulptekst=True
    )
    assert 'lyric number="1"' in xml
    assert 'lyric number="2"' in xml
    assert "<text>Свя</text>" in xml or "<text>Свя" in xml
    assert "<text>Svja</text>" in xml
    assert "<text>Bo</text>" in xml
    assert "<text>zje</text>" in xml


def test_nl_playback_lyric_number_2() -> None:
    xml = export_mvsa_to_musicxml(NL_MINI, layout="playback", hulptekst=True)
    assert 'lyric number="2"' in xml
    assert "<text>Хер</text>" in xml
    assert "<text>онт</text>" in xml
    assert "<text>ферм</text>" in xml
    assert "<text>У</text>" in xml


def test_hulptekst_as_parts_playback() -> None:
    xml = export_mvsa_to_musicxml(
        KSL_MINI, layout="playback", hulptekst_as_parts=True
    )
    assert 'id="P5"' in xml
    assert "Soprano (ksl)" in xml
    assert "Soprano (nl)" in xml
    assert "Soprano (hulptekst)" not in xml
    assert "<volume>0</volume>" in xml
    # Bronparts behouden lyric 1 + 2; hulptekst-parts hebben Svja als number 1.
    assert xml.count("Svja") >= 2


def test_hulptekst_as_parts_nl_labels() -> None:
    xml = export_mvsa_to_musicxml(
        NL_MINI, layout="playback", hulptekst_as_parts=True
    )
    assert "Soprano (nl)" in xml
    assert "Bass (ksl)" in xml


def test_hulptekst_as_parts_custom_ids() -> None:
    text = (
        ROOT / "examples" / "mvsa" / "hulptekst-coria-custom-ids-mini.mvsa"
    ).read_text(encoding="utf-8")
    doc = parse_mvsa(text)
    systems = [sys for sec in doc.sections for sys in sec.systems]
    assert systems[0].context.oct_for("Sop") == 0
    assert systems[0].context.oct_for("Zeep") == -1
    assert systems[0].context.oct_for("sop") == 0  # case-insensitive
    assert systems[0].context.taal_for("Lap") == "aap"
    assert systems[0].context.taal_for("Lus") == "noot"
    xml = export_mvsa_to_musicxml(
        text, layout="playback", hulptekst_as_parts=True
    )
    assert "Sop (aap)" in xml
    assert "Sop (noot)" in xml
    assert "Zeep (aap)" in xml
    assert "Zeep (noot)" in xml
    assert 'id="P4"' in xml


def test_hulptekst_as_parts_parallel_l_prime() -> None:
    doc = parse_mvsa(PARALLEL)
    systems = [sys for sec in doc.sections for sys in sec.systems]
    assert systems[0].context.taal_for("L") == "ksl"
    assert systems[0].context.taal_for("L1") == "nl"
    assert systems[0].context.taal_for("L'") == "nl"
    xml = export_mvsa_to_musicxml(
        PARALLEL, layout="playback", hulptekst_as_parts=True
    )
    assert "Alto (ksl)" in xml
    assert "Alto (nl)" in xml


def test_taal_assign_invalid_stem() -> None:
    text = "@taal S=nl\nL: a_ |\nS: do |\n"
    diags = validate_mvsa_text(text)
    assert any(d.code == "MVSA-TAAL" for d in diags)


def test_hulptekst_as_parts_rejects_partituur() -> None:
    with pytest.raises(MvsaExportError, match="playback"):
        export_mvsa_to_musicxml(
            KSL_MINI, layout="partituur", hulptekst_as_parts=True
        )


def test_without_flag_no_lyric_2() -> None:
    xml = export_mvsa_to_musicxml(KSL_MINI, layout="playback")
    assert 'lyric number="2"' not in xml
