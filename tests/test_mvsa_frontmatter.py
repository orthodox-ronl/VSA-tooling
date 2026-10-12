"""YAML-frontmatter (o.a. zoektekst) vóór .mvsa-body."""

from __future__ import annotations

from vsa.mvsa_parse import parse_mvsa
from vsa.mvsa_validate import validate_mvsa_text
from vsa.text_export import plain_text_from_mvsa

_MINIMAL_BODY = """\
@do F4
@mode major

L: Hei_ li_ ge_ ||
S: do   re   mi ||
A: la-  ti-  do ||
T: fa-  so-  la- ||
B: do-  re-  mi- ||
"""


def test_parse_mvsa_strips_yaml_frontmatter_and_keeps_zoektekst() -> None:
    text = (
        "---\n"
        "identificatie:\n"
        "  title: Test\n"
        "zoektekst: >-\n"
        "  Heilige\n"
        "---\n"
        "\n"
        f"{_MINIMAL_BODY}"
    )
    doc = parse_mvsa(text)
    assert doc.frontmatter.get("zoektekst") == "Heilige"
    assert doc.frontmatter.get("identificatie", {}).get("title") == "Test"
    assert not [
        d for d in doc.diagnostics if d.severity == "error"
    ], [d.message for d in doc.diagnostics if d.severity == "error"]
    assert doc.sections
    assert doc.sections[0].systems


def test_parse_mvsa_line_numbers_skip_frontmatter() -> None:
    text = (
        "---\n"
        "zoektekst: x\n"
        "---\n"
        "\n"
        "@do F4\n"
        "@mode major\n"
        "\n"
        "L: Hei_ ||\n"
        "S: do   ||\n"
        "A: la-  ||\n"
        "T: fa-  ||\n"
        "B: do-  ||\n"
        "L/: fout ||\n"  # lyrics + EHM → error op deze regel
        "S: do   ||\n"
        "A: la-  ||\n"
        "T: fa-  ||\n"
        "B: do-  ||\n"
    )
    doc = parse_mvsa(text)
    ehm_errs = [d for d in doc.diagnostics if d.code == "MVSA-EHM-L"]
    assert ehm_errs
    # --- / zoektekst / --- / lege / @do / @mode / lege / L…B / L/:
    # L/: is regel 13 in het bestand
    assert ehm_errs[0].line == 13


def test_validate_and_text_ignore_zoektekst_field() -> None:
    text = (
        "---\n"
        "zoektekst: Helemaal andere tekst die niet in L staat\n"
        "---\n"
        "\n"
        f"{_MINIMAL_BODY}"
    )
    diags = validate_mvsa_text(text)
    assert not [d for d in diags if d.severity == "error"], [
        d.message for d in diags if d.severity == "error"
    ]
    plain = plain_text_from_mvsa(text)
    assert "Hei" in plain
    assert "Helemaal andere" not in plain


def test_parse_mvsa_without_frontmatter_unchanged() -> None:
    doc = parse_mvsa(_MINIMAL_BODY)
    assert doc.frontmatter == {}
    assert doc.sections
