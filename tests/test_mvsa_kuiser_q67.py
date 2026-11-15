"""Kuiser Q6 (banners) + Q7 (validate-gate) — docs/formats/kuiser.md."""

from __future__ import annotations

from vsa.mvsa_import import IMPORT_SKETCH_WARNING_BANNER
from vsa.mvsa_kuiser import kuiser_mvsa_text
from vsa.mvsa_kuiser_q67 import apply_q6, assert_q7_valid
from vsa.mvsa_validate import MvsaValidationError, validate_mvsa_text
from vsa.vsa_mvsa import TEMPLATE_DERIVED_WARNING_BANNER, format_emit_warnings


_CORE = """\
@do F4
@mode major
@sectie a
L: ja ja ||
S: fa so ||
A: re re ||
T: la- so- ||
B: re re ||
"""


def test_q6_strips_imported_and_import_banner():
    text = (
        "# Imported: Demo titel\n"
        + IMPORT_SKETCH_WARNING_BANNER
        + "\n"
        + _CORE
    )
    out = apply_q6(text, werkbank=False)
    assert "Imported:" not in out
    assert "WAARSCHUWING:" not in out
    assert "################################################################" not in out
    assert "@do F4" in out
    assert "#maat" not in out  # apply_q6 alleen; Q3 volgt in pipeline


def test_q6_strips_template_banner_and_emit_warnings():
    extra = "\n".join(format_emit_warnings(["stem A ontbreekt"])) + "\n"
    text = TEMPLATE_DERIVED_WARNING_BANNER + "\n" + extra + _CORE
    out = apply_q6(text, werkbank=False)
    assert "AFGELEID UIT VSA" not in out
    assert "specifieke waarschuwingen" not in out
    assert "stem A ontbreekt" not in out
    assert "@do F4" in out


def test_q6_werkbank_keeps_banners():
    text = "# Imported: X\n" + IMPORT_SKETCH_WARNING_BANNER + "\n" + _CORE
    out = apply_q6(text, werkbank=True)
    assert out == text


def test_q6_keeps_maat_comments():
    text = "#maat 3\n" + _CORE
    assert "#maat 3" in apply_q6(text, werkbank=False)


def test_kuiser_pipeline_strips_banners_by_default():
    text = (
        "# Imported: Demo\n"
        + IMPORT_SKETCH_WARNING_BANNER
        + "\n"
        + _CORE
    )
    result = kuiser_mvsa_text(
        text, align=False, dict_interactive=False, werkbank=False
    )
    assert "Imported:" not in result.text
    assert "WAARSCHUWING:" not in result.text
    assert "#maat 1" in result.text
    errs = [d for d in validate_mvsa_text(result.text) if d.severity == "error"]
    assert not errs


def test_kuiser_werkbank_keeps_imported_line():
    text = "# Imported: Demo\n" + _CORE
    result = kuiser_mvsa_text(
        text, align=False, dict_interactive=False, werkbank=True
    )
    assert "# Imported: Demo" in result.text


def test_q7_raises_on_invalid():
    bad = "@do F4\nL: a ||\nS: fa so ||\n"
    try:
        assert_q7_valid(bad)
        raise AssertionError("expected MvsaValidationError")
    except MvsaValidationError:
        pass
