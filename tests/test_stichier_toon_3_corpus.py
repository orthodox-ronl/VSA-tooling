"""Corpus-steekproef stichier-toon-3-groningen (T7): speelplan + vsa mvsa."""

from __future__ import annotations

from pathlib import Path

from vsa.template_library import load_resolved_template
from vsa.template_mapping import assign_stanzas_to_phrases, select_mapping_plan
from vsa.vsa_mvsa import convert_vsa_to_mvsa

CORPUS = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "specification-vsa-templates"
    / "library"
    / "stichier-toon-3-groningen"
    / "examples"
    / "corpus"
)


def test_corpus_phrase_plans() -> None:
    doc = load_resolved_template("stichier-toon-3-groningen").doc
    cases = {
        "heer-ik-roep-toon-3-deel1.vsa": (
            "triple-close",
            ["1", "2", "1", "2", "voorlaatste", "laatste"],
        ),
        "heer-ik-roep-toon-3-deel2.vsa": (
            "standard",
            ["1", "2", "1", "2", "laatste"],
        ),
    }
    for name, (plan_id, expected) in cases.items():
        out = convert_vsa_to_mvsa(CORPUS / name)
        assert out.resolved.formula_id == "stichier-toon-3-groningen"
        assert out.phrase_ids == expected
        plan = select_mapping_plan(doc, len(expected))
        assert plan.id == plan_id
        assert assign_stanzas_to_phrases(plan, len(expected)) == expected
        assert out.phrase_ids[-1] == "laatste"


def test_two_couplets_plan_11() -> None:
    doc = load_resolved_template("stichier-toon-3-groningen").doc
    expected = [
        "1",
        "2",
        "1",
        "2",
        "voorlaatste",
        "laatste",
        "1",
        "2",
        "1",
        "2",
        "laatste",
    ]
    plan = select_mapping_plan(doc, 11)
    assert plan.id == "two-couplets"
    assert assign_stanzas_to_phrases(plan, 11) == expected
