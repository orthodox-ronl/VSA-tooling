"""Tests for EHM motion, PitchResolver, and chromatic-accidental semantics.

Canonical model: diatonic cursor + temporary accidental on the arrival pitch.
The accidental must not poison the cursor for the next EHM.
"""

from __future__ import annotations

from vsa.music import Pitch
from vsa.pitch_resolver import (
    PitchResolver,
    ehm_to_motion,
    pitch_marker_degree,
)


# ---------------------------------------------------------------------------
# ehm_to_motion
# ---------------------------------------------------------------------------


class TestEhmToMotion:
    def test_base_motions(self):
        assert ehm_to_motion("/") == (1, 0.0)
        assert ehm_to_motion("//") == (2, 0.0)
        assert ehm_to_motion("\\") == (-1, 0.0)
        assert ehm_to_motion("\\\\") == (-2, 0.0)
        assert ehm_to_motion("-") == (0, 0.0)
        assert ehm_to_motion("~") == (0, 0.0)

    def test_sharp_aliases(self):
        assert ehm_to_motion("#/") == (1, 1.0)
        assert ehm_to_motion("+/") == (1, 1.0)
        assert ehm_to_motion("♯/") == (1, 1.0)
        assert ehm_to_motion("#\\") == (-1, 1.0)
        assert ehm_to_motion("+\\") == (-1, 1.0)

    def test_flat_aliases(self):
        assert ehm_to_motion("b/") == (1, -1.0)
        assert ehm_to_motion("♭/") == (1, -1.0)
        assert ehm_to_motion("b\\") == (-1, -1.0)

    def test_chromatic_on_current_degree(self):
        assert ehm_to_motion("#-") == (0, 1.0)
        assert ehm_to_motion("+-") == (0, 1.0)
        assert ehm_to_motion("b-") == (0, -1.0)
        assert ehm_to_motion("#~") == (0, 1.0)

    def test_empty(self):
        assert ehm_to_motion("") == (0, 0.0)


class TestPitchMarkerDegree:
    def test_empty_is_do(self):
        assert pitch_marker_degree([]) == 0
        assert pitch_marker_degree(["~"]) == 0
        assert pitch_marker_degree(["-"]) == 0

    def test_ladder_only(self):
        assert pitch_marker_degree(["//"]) == 2
        assert pitch_marker_degree(["\\\\"]) == -2

    def test_accidental_ignored_for_degree(self):
        assert pitch_marker_degree(["+-"]) == 0
        assert pitch_marker_degree(["b\\\\"]) == -2
        assert pitch_marker_degree(["#/"]) == 1


# ---------------------------------------------------------------------------
# PitchResolver — acceptance tables from semantics.md
# ---------------------------------------------------------------------------


def _resolver(do: str = "C4", mode: str = "major") -> PitchResolver:
    r = PitchResolver.from_metadata({"do": do, "mode": mode})
    r.apply_start_marker([])  # [:]
    return r


class TestPitchResolverChromaticSemantics:
    def test_sharp_down_then_up_returns_to_do_c4(self):
        """Start do. #\\ then / → end degree do; end sound = start sound."""
        r = _resolver("C4")
        p1 = r.resolve_ehm("#\\")
        assert r.current_degree == -1
        assert p1 == Pitch(step="B", octave=3, alter=1.0)

        p2 = r.resolve_ehm("/")
        assert r.current_degree == 0
        assert p2 == Pitch(step="C", octave=4, alter=0.0)
        assert p2 == r.current_pitch

    def test_plus_alias_same_as_hash(self):
        """+\\ then / must not leave a lingering half-step (≠ b/ effect)."""
        r = _resolver("C4")
        r.resolve_ehm("+\\")
        p = r.resolve_ehm("/")
        assert r.current_degree == 0
        assert p == Pitch(step="C", octave=4, alter=0.0)

        # Contrast: single b/ lands on re-flat and leaves cursor on re.
        r2 = _resolver("C4")
        p_flat = r2.resolve_ehm("b/")
        assert r2.current_degree == 1
        assert p_flat == Pitch(step="D", octave=4, alter=-1.0)
        assert p != p_flat

    def test_flat_up_then_same_tone_keeps_accidental(self):
        """Stay (~ / -) inherits sounding, including flat — readable for singers."""
        r = _resolver("C4")
        p1 = r.resolve_ehm("b/")
        assert r.current_degree == 1
        assert p1 == Pitch(step="D", octave=4, alter=-1.0)

        p2 = r.resolve_ehm("-")
        assert r.current_degree == 1
        assert p2 == p1

        p3 = r.resolve_ehm("~")
        assert r.current_degree == 1
        assert p3 == p1
        assert r.current_pitch == p1

    def test_moving_ehm_releases_inherited_accidental(self):
        r = _resolver("C4")
        r.resolve_ehm("b/")
        r.resolve_ehm("-")
        p = r.resolve_ehm("/")
        assert r.current_degree == 2
        assert p == Pitch(step="E", octave=4, alter=0.0)

    def test_sharp_dash_then_stay_keeps_sharp(self):
        r = _resolver("C4")
        p_sharp = r.resolve_ehm("#-")
        assert r.current_degree == 0
        assert p_sharp == Pitch(step="C", octave=4, alter=1.0)

        p_hold = r.resolve_ehm("-")
        assert r.current_degree == 0
        assert p_hold == p_sharp

        p_flat = r.resolve_ehm("b-")
        assert r.current_degree == 0
        assert p_flat == Pitch(step="C", octave=4, alter=-1.0)

    def test_gregos_same_tone_then_up_readable_form(self):
        """[/:] {+\\go}{ri}{/os} [/:] → D Cis Cis D with do=C (no #- needed)."""
        r = PitchResolver.from_metadata({"do": "C4", "mode": "major"})
        r.apply_start_marker(["/"])  # [/:] = D
        assert r.current_pitch == Pitch(step="D", octave=4, alter=0.0)

        go = r.resolve_ehm("+\\")
        assert go == Pitch(step="C", octave=4, alter=1.0)

        ri = r.resolve_ehm("~")
        assert ri == go
        assert r.current_pitch == go  # unscoped "ri" would recite this

        os_ = r.resolve_ehm("/")
        assert os_ == Pitch(step="D", octave=4, alter=0.0)
        assert r.current_degree == 1

    def test_non_c_do_enharmonic_spelling(self):
        """do=F4: #\\ then / → E# then F; end = start."""
        r = _resolver("F4")
        p1 = r.resolve_ehm("#\\")
        assert r.current_degree == -1
        assert p1 == Pitch(step="E", octave=4, alter=1.0)

        p2 = r.resolve_ehm("/")
        assert r.current_degree == 0
        assert p2 == Pitch(step="F", octave=4, alter=0.0)

        r2 = _resolver("F4")
        p_flat = r2.resolve_ehm("b/")
        assert r2.current_degree == 1
        assert p_flat == Pitch(step="G", octave=4, alter=-1.0)
