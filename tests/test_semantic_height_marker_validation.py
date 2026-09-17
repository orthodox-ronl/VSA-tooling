"""Tests voor semantische validatie van hoogte-markeringen.

Elke lokale markering ([X:] na de eerste) wordt gecontroleerd tegen de
cumulatieve diatonische laddergraad berekend uit alle tussenliggende EHMs.
Accidens-prefixen bewegen die cursor niet.
"""

from vsa.parser import Parser
from vsa.semantic_validator import SemanticValidator, SemanticValidationOptions
from vsa.height_markers import (
    _degree_of_ehm,
    _degree_of_ehm_list,
    _marker_for_degree,
    _pitch_of_ehm,
    _pitch_of_ehm_list,
    _marker_for_pitch,
)


# ---------------------------------------------------------------------------
# Hulpfunctie
# ---------------------------------------------------------------------------

def _validate(source: str):
    document = Parser(source).parse()
    return SemanticValidator(document, source_text=source).validate()


# ---------------------------------------------------------------------------
# Graad-rekenkundige helpers
# ---------------------------------------------------------------------------

class TestDegreeHelpers:
    def test_empty_ehm_is_zero(self):
        assert _degree_of_ehm("") == 0

    def test_neutral_is_zero(self):
        assert _degree_of_ehm("-") == 0
        assert _degree_of_ehm("~") == 0

    def test_single_rise(self):
        assert _degree_of_ehm("/") == 1

    def test_double_rise(self):
        assert _degree_of_ehm("//") == 2

    def test_single_fall(self):
        assert _degree_of_ehm("\\") == -1

    def test_double_fall(self):
        assert _degree_of_ehm("\\\\") == -2

    def test_accidental_does_not_change_degree(self):
        assert _degree_of_ehm("+/") == 1
        assert _degree_of_ehm("#/") == 1
        assert _degree_of_ehm("♯/") == 1
        assert _degree_of_ehm("b\\") == -1
        assert _degree_of_ehm("♭\\") == -1
        assert _degree_of_ehm("+-") == 0
        assert _degree_of_ehm("#-") == 0
        assert _degree_of_ehm("b-") == 0
        assert _degree_of_ehm("+\\") == -1
        assert _degree_of_ehm("#\\") == -1
        assert _degree_of_ehm("b/") == 1
        assert _degree_of_ehm("+//") == 2

    def test_list_sums_degrees_only(self):
        assert _degree_of_ehm_list(["/", "\\"]) == 0
        assert _degree_of_ehm_list(["//", "/"]) == 3
        # b\ and #\ each move −1 degree; accidentals ignored → −2
        assert _degree_of_ehm_list(["b\\", "#\\"]) == -2

    def test_empty_list_is_zero(self):
        assert _degree_of_ehm_list([]) == 0

    def test_legacy_aliases(self):
        assert _pitch_of_ehm("#\\") == _degree_of_ehm("#\\")
        assert _pitch_of_ehm_list(["b/", "-"]) == _degree_of_ehm_list(["b/", "-"])


class TestMarkerForDegree:
    def test_zero(self):
        assert _marker_for_degree(0) == "[:]"

    def test_positive(self):
        assert _marker_for_degree(1) == "[/:]"
        assert _marker_for_degree(3) == "[///:]"

    def test_negative(self):
        assert _marker_for_degree(-1) == "[\\:]"
        assert _marker_for_degree(-2) == "[\\\\:]"

    def test_legacy_alias(self):
        assert _marker_for_pitch(2) == "[//:]"


# ---------------------------------------------------------------------------
# Validatieregels
# ---------------------------------------------------------------------------

class TestHeightMarkerValidation:
    def test_no_markers_no_error(self):
        result = _validate("{aap}")
        assert result.ok
        assert not any(
            d.code == "VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH"
            for d in result.diagnostics
        )

    def test_single_marker_no_error(self):
        result = _validate("[//:] {/aap}{/noot}")
        assert result.ok

    def test_consistent_rising_sequence(self):
        # start=2, +1+1=4, markering=4 → OK
        result = _validate("[//:] {/aap}{/noot} [////:]")
        assert result.ok

    def test_mismatch_rising(self):
        # start=2, +1+1=4, maar markering declareert 0
        result = _validate("[//:] {/noot}{/mies} [:]")
        codes = [d.code for d in result.diagnostics]
        assert "VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH" in codes

    def test_mismatch_hint_contains_correct_marker(self):
        result = _validate("[//:] {/noot}{/mies} [:]")
        mismatch = next(
            d for d in result.diagnostics
            if d.code == "VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH"
        )
        assert "[////:]" in mismatch.hint_nl

    def test_mismatch_message_contains_computed_delta(self):
        result = _validate("[//:] {/noot}{/mies} [:]")
        mismatch = next(
            d for d in result.diagnostics
            if d.code == "VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH"
        )
        assert mismatch.message_nl == "computed = marker + 4"

    def test_consistent_falling_sequence(self):
        # start=-1, -1-1=-3, markering=-3 → OK
        result = _validate("[\\:] {\\aap}{\\noot} [\\\\\\:]")
        assert result.ok

    def test_mismatch_falling(self):
        # start=-1, -1-1=-3, maar markering declareert 0
        result = _validate("[\\:] {\\aap}{\\noot} [:]")
        codes = [d.code for d in result.diagnostics]
        assert "VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH" in codes

    def test_mixed_rise_and_fall_consistent(self):
        # start=-1, +1=0, markering=0 → OK (niet fout!)
        result = _validate("[\\:] {/aap} [:]")
        assert result.ok

    def test_neutral_scope_contributes_zero(self):
        # start=1, {tekst}=0, markering=1 → OK
        result = _validate("[//:] {aap} [//:]")
        assert result.ok

    def test_multiple_mismatches_all_reported(self):
        # Twee onafhankelijke foute lokale markeringen → beide fouten zichtbaar
        result = _validate("[//:] {/aap} [//:] {/noot} [//:]")
        mismatches = [
            d for d in result.diagnostics
            if d.code == "VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH"
        ]
        assert len(mismatches) == 2

    def test_cascade_mismatches_after_wrong_marker_are_suppressed(self):
        # Eén foute markering; latere [:] zijn alleen fout door die cascade
        result = _validate("[//:] {/aap}{/noot} [:] [:]")
        mismatches = [
            d for d in result.diagnostics
            if d.code == "VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH"
        ]
        assert len(mismatches) == 1

    def test_accidental_sequence_tracks_degree_only(self):
        # [:] {+\aap.}{#\noot_}{b\mies} [\\\:]
        # degrees: 0 + (−1) + (−1) + (−1) = −3 → OK
        result = _validate(r"[:]  {+\aap.}{#\noot_}{b\mies} [\\\:]")
        assert result.ok

    def test_sharp_down_then_up_matches_do_marker(self):
        # Canonical regression: #\\ then / returns to do — not b/-height.
        result = _validate(r"[:] {#\aap}{/noot} [:]")
        assert result.ok

    def test_plus_down_then_up_matches_do_marker(self):
        result = _validate(r"[:] {+\aap}{/noot} [:]")
        assert result.ok

    def test_accidental_mismatch_uses_degree_hint(self):
        # [:] {+\aap} [:]  → degree −1, but marker says 0
        result = _validate(r"[:] {+\aap} [:]")
        codes = [d.code for d in result.diagnostics]
        assert "VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH" in codes
        mismatch = next(
            d for d in result.diagnostics
            if d.code == "VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH"
        )
        assert "[\\:]" in mismatch.hint_nl
        assert "[b-:]" not in mismatch.hint_nl

    def test_flat_up_leaves_cursor_on_re(self):
        result = _validate(r"[:] {b/aap} [/:]")
        assert result.ok

    def test_chromatic_dash_does_not_move_marker(self):
        result = _validate(r"[:] {#-aap}{b-noot} [:]")
        assert result.ok

    def test_line_column_points_to_wrong_marker(self):
        source2 = "[//:] {/aap} [:]"
        result2 = _validate(source2)
        mismatch = next(
            d for d in result2.diagnostics
            if d.code == "VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH"
        )
        assert mismatch.column > 1

    def test_severity_overridable_to_warning(self):
        opts = SemanticValidationOptions(
            severity_overrides={"VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH": "warning"}
        )
        document = Parser("[//:] {/noot} [:]").parse()
        result = SemanticValidator(
            document, opts, source_text="[//:] {/noot} [:]"
        ).validate()
        assert result.ok  # geen fatal error
        assert result.has_warnings()
