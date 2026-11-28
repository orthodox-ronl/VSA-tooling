"""Corpus: stanza-telling en uitgewerkte zangstukken (VSA → MSCZ/MXL)."""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import render_vsa_template_musicxml as render  # noqa: E402

from vsa.corpus_vsa import CORPUS_ENTRIES, load_corpus_from_vsa_dir  # noqa: E402
from vsa.template_mapping import assign_stanzas_to_phrases, select_mapping_plan  # noqa: E402

LIBRARY = ROOT / "docs" / "specification-vsa-templates" / "library"
TEMPLATE_YAML = LIBRARY / "tropaar-toon-4-hemelum" / "template.yaml"
CORPUS_DIR = TEMPLATE_YAML.parent / "examples" / "corpus"

EXPECTED_STANZAS: dict[str, int] = {
    "T4-01": 6,
    "T4-02": 7,
    "T4-03": 6,
    "T4-04": 9,
    "T4-05": 7,
    "T4-06": 7,
    "T4-07": 7,
    "T4-07a": 7,
    "T4-08": 7,
    "T4-09": 7,
    "T4-10": 5,
    "T4-11": 7,
    "T4-12": 7,
}

ELIA_PHRASES = ["1", "2", "1", "2", "1", "2", "laatste"]


@pytest.mark.parametrize("piece_id,expected", EXPECTED_STANZAS.items())
def test_corpus_stanza_counts(piece_id: str, expected: int) -> None:
    piece = next(p for p in load_corpus_from_vsa_dir(CORPUS_DIR) if p.piece_id == piece_id)
    assert piece.stanza_count == expected


def test_corpus_has_thirteen_pieces() -> None:
    assert len(CORPUS_ENTRIES) == 13
    assert len(list(CORPUS_DIR.glob("T4-*.vsa"))) == 13


def test_elia_phrase_assignment() -> None:
    doc = render.load_resolved(TEMPLATE_YAML, LIBRARY)
    plan = select_mapping_plan(doc, 7)
    assert assign_stanzas_to_phrases(plan, 7) == ELIA_PHRASES


def _staff1_block(mscx: str) -> str:
    match = re.search(r'<Staff id="1">(.*?)</Staff>', mscx, re.DOTALL)
    assert match, "staff 1 not found"
    return match.group(1)


def _measure_count_staff1(mscx: str) -> int:
    return _staff1_block(mscx).count("<Measure len=")


def test_expanded_elia_has_seven_measures_no_repeats() -> None:
    doc = render.load_resolved(TEMPLATE_YAML, LIBRARY)
    mscx = render.render_expanded_mscx(
        doc,
        ELIA_PHRASES,
        title="Profeet Elia",
    )
    assert _measure_count_staff1(mscx) == 7
    assert "<startRepeat/>" not in mscx
    assert "<endRepeat>" not in mscx
    assert "Profeet Elia" in mscx


def test_instance_title_uses_frontmatter_not_corpus_id() -> None:
    """MSCZ/PDF-titel = frontmatter title; geen T4-XX-prefix."""
    import render_tropaar_toon4_corpus as corpus  # noqa: E402

    vsa = CORPUS_DIR / "T4-06-profeet-elia.vsa"
    text = vsa.read_text(encoding="utf-8")
    assert corpus.instance_title(vsa, text) == "Profeet Elia"
    bare = "Gij waart een {En_}gel.\n"
    assert corpus.instance_title(Path("T4-06-profeet-elia.vsa"), bare) == (
        "T4-06-profeet-elia"
    )


def test_andreas_five_phrase_assignment() -> None:
    doc = render.load_resolved(TEMPLATE_YAML, LIBRARY)
    plan = select_mapping_plan(doc, 5)
    phrase_ids = assign_stanzas_to_phrases(plan, 5)
    assert phrase_ids == ["1", "2", "1", "2", "laatste"]


def test_corpus_instances_vsa_mscz_mxl() -> None:
    """Uitgewerkte zangstukken: .vsa + .mscz + .mxl (geen legacy `*.pad-b.*`-suffix)."""
    expected_stem = {f"{pid}-{slug}" for pid, slug, _ in CORPUS_ENTRIES}
    for stem in expected_stem:
        vsa = CORPUS_DIR / f"{stem}.vsa"
        mscz = CORPUS_DIR / f"{stem}.mscz"
        mxl = CORPUS_DIR / f"{stem}.mxl"
        assert vsa.is_file(), stem
        assert mscz.is_file(), stem
        assert mxl.is_file(), stem
        text = vsa.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert "template: tropaar-toon-4-hemelum" in text
        assert "corpus_id:" in text
        assert mscz.stat().st_size > 500
        assert mxl.stat().st_size > 500
        assert zipfile.is_zipfile(mxl)
        with zipfile.ZipFile(mscz) as archive:
            mscx = archive.read("score.mscx").decode("utf-8")
        assert "<Lyrics>" in mscx
        assert "<startRepeat/>" not in mscx
        assert "<genCourtesyTimesig>0</genCourtesyTimesig>" in mscx
        pid = stem.split("-")[0] + "-" + stem.split("-")[1]  # T4-07a-... → T4-07a
        if stem.startswith("T4-07a"):
            pid = "T4-07a"
        else:
            pid = stem[:5]
        body = _staff1_block(mscx)
        # Één maat per strofe; geen verborgen binnen-strofe-maatstrepen.
        assert body.count("<Measure len=") == EXPECTED_STANZAS[pid]
        assert "<subtype>normal</subtype><visible>0</visible>" not in body
    # Geen oude `*.pad-b.*`-namen meer.
    leftovers = list(CORPUS_DIR.glob("*.pad-b.*"))
    assert not leftovers, leftovers


def test_template_mscz_and_mxl_exist() -> None:
    base = TEMPLATE_YAML.parent
    assert (base / "template.mscz").is_file()
    assert (base / "template.mxl").is_file()
    assert not (base / "template-from-yaml.mscx").exists()
    assert not (base / "template-from-yaml.mscz").exists()
    with zipfile.ZipFile(base / "template.mscz") as archive:
        mscx = archive.read("score.mscx").decode("utf-8")
    assert "<enableVerticalSpread>0</enableVerticalSpread>" in mscx
    assert "<maxPageFillSpread>0</maxPageFillSpread>" in mscx
    _staff, _sys, _frame = render._vertical_layout_gaps(layout="template")
    assert f"<minSystemDistance>{_sys}</minSystemDistance>" in mscx
    assert f"<maxSystemDistance>{_sys}</maxSystemDistance>" in mscx
    assert f"<staffDistance>{_staff}</staffDistance>" in mscx
    assert f"<frameSystemDistance>{_frame}</frameSystemDistance>" in mscx
    assert "<enableIndentationOnFirstSystem>0</enableIndentationOnFirstSystem>" in mscx
