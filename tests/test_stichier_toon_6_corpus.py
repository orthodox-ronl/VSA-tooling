"""Corpus-steekproef stichier-toon-6-groningen (T7): speelplan + vsa mvsa."""

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
    / "stichier-toon-6-groningen"
    / "examples"
    / "corpus"
)


def test_corpus_phrase_plans() -> None:
    doc = load_resolved_template("stichier-toon-6-groningen").doc
    cases = {
        "kondak-moeder-gods-toon-6-groningen.vsa": (
            "standard",
            ["1", "2", "3", "1", "2", "3", "1", "laatste"],
        ),
        "heer-ik-roep-toon-6-deel1.vsa": (
            "triple-close",
            ["1", "2", "3", "1", "voorlaatste", "laatste"],
        ),
        "heer-ik-roep-toon-6-deel2.vsa": (
            "standard",
            ["1", "2", "3", "1", "laatste"],
        ),
    }
    for name, (plan_id, expected) in cases.items():
        out = convert_vsa_to_mvsa(CORPUS / name)
        assert out.resolved.formula_id == "stichier-toon-6-groningen"
        assert out.phrase_ids == expected
        plan = select_mapping_plan(doc, len(expected))
        assert plan.id == plan_id
        assert assign_stanzas_to_phrases(plan, len(expected)) == expected
        assert "@sectie laatste" in out.text
