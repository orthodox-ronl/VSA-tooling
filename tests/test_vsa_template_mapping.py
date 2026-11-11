"""Tests for VSA text → template-frase mapping."""

from __future__ import annotations

import pytest

from vsa.template_mapping import (
    TemplateMappingError,
    assign_stanzas_to_phrases,
    compile_text_mapping,
    format_plan_label,
    list_mapping_plans,
    select_mapping_plan,
)


def test_cycle_final_compiles_and_assigns() -> None:
    doc = {
        "cycle": ["1", "2"],
        "final": "laatste",
        "phrases": [{"id": "1"}, {"id": "2"}, {"id": "laatste"}],
    }
    plan = list_mapping_plans(doc)[0]
    assert assign_stanzas_to_phrases(plan, 5) == ["1", "2", "1", "2", "laatste"]
    assert assign_stanzas_to_phrases(plan, 6) == ["1", "2", "1", "2", "1", "laatste"]
    assert assign_stanzas_to_phrases(plan, 2) == ["1", "laatste"]
    assert format_plan_label(plan) == "||: 1, 2 :|| laatste"


def test_prefix_then_cycle() -> None:
    doc = {
        "text_mapping": [
            {"phrase": "1"},
            {"repeat": ["2", "3"], "until": "final"},
            {"phrase": "laatste"},
        ],
        "phrases": [{"id": "1"}, {"id": "2"}, {"id": "3"}, {"id": "laatste"}],
    }
    plan = list_mapping_plans(doc)[0]
    assert assign_stanzas_to_phrases(plan, 5) == ["1", "2", "3", "2", "laatste"]


def test_pure_sequence() -> None:
    doc = {
        "sequence": ["1", "3", "1", "2"],
        "phrases": [{"id": x} for x in ["1", "3", "2"]],
    }
    plan = list_mapping_plans(doc)[0]
    assert assign_stanzas_to_phrases(plan, 4) == ["1", "3", "1", "2"]


def test_sequence_ending_laatste_truncates() -> None:
    """Toon-3-speelplan: prefix + altijd «laatste»; max = lengte plan."""
    doc = {
        "sequence": ["1", "3", "1", "2", "3", "1", "4", "laatste"],
        "phrases": [{"id": x} for x in ["1", "3", "2", "4", "laatste"]],
    }
    plan = list_mapping_plans(doc)[0]
    assert assign_stanzas_to_phrases(plan, 8) == [
        "1",
        "3",
        "1",
        "2",
        "3",
        "1",
        "4",
        "laatste",
    ]
    assert assign_stanzas_to_phrases(plan, 6) == [
        "1",
        "3",
        "1",
        "2",
        "3",
        "laatste",
    ]
    assert assign_stanzas_to_phrases(plan, 1) == ["laatste"]


def test_sequence_ending_laatste_rejects_overflow() -> None:
    doc = {
        "sequence": ["1", "3", "1", "2", "3", "1", "4", "laatste"],
        "phrases": [{"id": x} for x in ["1", "3", "2", "4", "laatste"]],
    }
    plan = list_mapping_plans(doc)[0]
    with pytest.raises(TemplateMappingError) as caught:
        assign_stanzas_to_phrases(plan, 9)
    msg = str(caught.value)
    assert "9 frasen" in msg
    assert "8 plaatsen" in msg
    assert "laatste" in msg


def test_prefix_cycle_in_middle() -> None:
    doc = {
        "text_mapping": [
            {"sequence": ["1", "2", "3"]},
            {"repeat": ["4", "5", "3a"], "until": "final"},
            {"phrase": "laatste"},
        ],
        "phrases": [{"id": x} for x in ["1", "2", "3", "4", "5", "3a", "laatste"]],
    }
    plan = list_mapping_plans(doc)[0]
    assert assign_stanzas_to_phrases(plan, 7) == [
        "1",
        "2",
        "3",
        "4",
        "5",
        "3a",
        "laatste",
    ]


def test_tropaar_toon1_extended_tail() -> None:
    doc = {
        "mapping_plans": [
            {
                "id": "standard",
                "label": "||: 1, 2 :|| laatste",
                "steps": [
                    {"repeat": ["1", "2"], "until": "final"},
                    {"phrase": "laatste"},
                ],
            },
            {
                "id": "extended-close",
                "label": "||: 1, 2 :|| 1, 1a, 1a, 2",
                "when": {"stanza_count": 5},
                "steps": [
                    {"repeat": ["1", "2"], "until": {"remaining": 4}},
                    {"sequence": ["1", "1a", "1a", "2"]},
                ],
            },
        ],
        "phrases": [{"id": x} for x in ["1", "1a", "2", "laatste"]],
    }
    std = select_mapping_plan(doc, 6)
    assert std.id == "standard"
    assert assign_stanzas_to_phrases(std, 6) == [
        "1",
        "2",
        "1",
        "2",
        "1",
        "laatste",
    ]
    ext = select_mapping_plan(doc, 5)
    assert ext.id == "extended-close"
    assert assign_stanzas_to_phrases(ext, 5) == ["1", "1", "1a", "1a", "2"]


def test_conditional_mod_plan() -> None:
    doc = {
        "mapping_plans": [
            {
                "id": "triple",
                "when": {"stanza_count_mod": {"mod": 3, "remainder": 0}},
                "steps": [
                    {"phrase": "1"},
                    {"repeat": ["2", "3", "1"], "until": "final"},
                    {"phrase": "2a"},
                    {"phrase": "laatste"},
                ],
            },
            {
                "id": "default",
                "when": {"default": True},
                "steps": [
                    {"repeat": ["1", "2", "3"], "until": "final"},
                    {"phrase": "laatste"},
                ],
            },
        ],
        "phrases": [{"id": x} for x in ["1", "2", "3", "2a", "laatste"]],
    }
    triple = select_mapping_plan(doc, 6)
    assert triple.id == "triple"
    assert assign_stanzas_to_phrases(triple, 6) == [
        "1",
        "2",
        "3",
        "1",
        "2a",
        "laatste",
    ]
    default = select_mapping_plan(doc, 5)
    assert default.id == "default"


def test_cycle_not_multiple_of_k() -> None:
    doc = {
        "cycle": ["1", "2"],
        "final": "laatste",
        "phrases": [{"id": "1"}, {"id": "2"}, {"id": "laatste"}],
    }
    plan = list_mapping_plans(doc)[0]
    assert assign_stanzas_to_phrases(plan, 7) == [
        "1",
        "2",
        "1",
        "2",
        "1",
        "2",
        "laatste",
    ]


def test_too_few_stanzas_raises() -> None:
    doc = {
        "text_mapping": [
            {"repeat": ["1", "2"], "until": "final"},
            {"phrase": "laatste"},
        ],
        "phrases": [{"id": "1"}, {"id": "2"}, {"id": "laatste"}],
    }
    plan = list_mapping_plans(doc)[0]
    with pytest.raises(TemplateMappingError):
        assign_stanzas_to_phrases(plan, 0)
