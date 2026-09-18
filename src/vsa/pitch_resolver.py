"""
Resolves VSA EHMs (Enkelvoudige Hoogte-Modifiers) to absolute
:class:`~vsa.music.Pitch` objects.

Two layers are kept strictly separate:

1. **Diatonic cursor** — the current scale degree relative to ``do`` / mode.
   Only base motions (``/``, ``\\``, ``-``, ``~``, and stacked slashes) move it.
   (``-`` / ``~`` move by zero steps.)
2. **Sounding pitch** — what the singer hears / MusicXML exports.

Accidental prefixes (``#`` / ``+`` / ``♯``, ``b`` / ``♭``) apply to the pitch
*after* the base motion of that EHM.  They do **not** change the diatonic
cursor: the next *moving* EHM starts from the unaltered degree.

Same-tone continuation (``~``, ``-``, or unscoped reciting text) keeps the
**previous sounding pitch**, including any accidental — so ``{+\\go}{ri}``
and ``{+\\go}ri`` both sustain the raised tone without writing ``#-``.
A later ladder step (``/``, ``\\``, …) uses the natural degree again unless
that EHM carries its own prefix.

Resolution algorithm:

1. The ``do`` block parameter (e.g. ``"F4"``) defines the tonic.
2. The ``mode`` block parameter (e.g. ``"major"``) defines the scale.
3. The first pitch marker sets the starting scale degree (accidental prefixes
   on the marker do not shift the degree).
4. Each subsequent EHM advances the degree by its ladder-step count; stay
   without a new prefix reuses the last sounding pitch.

Scale degree 0 = do, degree 1 = re, … degree 6 = ti; degree 7 = do an octave
higher, degree -1 = ti an octave lower, etc.
"""

from __future__ import annotations

from .music import Pitch

# ── Step name tables ────────────────────────────────────────────────────────

STEP_NAMES = ["C", "D", "E", "F", "G", "A", "B"]

# Natural semitone within an octave for each step letter (C=0, D=2, …)
_NATURAL_SEMITONES: dict[str, int] = {
    "C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11,
}

# ── Scale definitions ────────────────────────────────────────────────────────

# Semitone offsets from the tonic for each of the 7 scale degrees
_SCALE_INTERVALS: dict[str, list[int]] = {
    "major":  [0, 2, 4, 5, 7, 9, 11],
    "minor":  [0, 2, 3, 5, 7, 8, 10],   # natural minor
}

# Canonieke `mode`-waarden in VSA-frontmatter én template-YAML (geen synoniemen).
ALLOWED_MODES = frozenset(_SCALE_INTERVALS)


class UnknownMode(ValueError):
    pass


# ── Pitch / MIDI helpers ─────────────────────────────────────────────────────

def _pitch_to_midi(p: Pitch) -> int:
    """MIDI note number: C4 = 60."""
    return 12 * (p.octave + 1) + _NATURAL_SEMITONES[p.step] + int(p.alter)


def parse_pitch_string(s: str) -> Pitch:
    """Parse a pitch string such as ``"F4"``, ``"Bb4"``, ``"C#5"`` into a
    :class:`~vsa.music.Pitch`.

    Supported alteration suffixes: ``b`` (flat), ``#`` / ``♯`` (sharp).
    The octave number is the final character.
    """
    s = s.strip()
    if not s:
        raise ValueError("Lege toonhoogte-string.")

    octave_char = s[-1]
    if not octave_char.isdigit():
        raise ValueError(f"Geen octaafgetal gevonden in: '{s}'")
    octave = int(octave_char)
    note = s[:-1]

    if note.endswith("bb") or note.endswith("♭♭"):
        step = note[:-2].upper()
        alter = -2.0
    elif note.endswith("b") and len(note) > 1 and note[-2].isalpha():
        step = note[:-1].upper()
        alter = -1.0
    elif note.endswith("#") or note.endswith("♯"):
        step = note[:-1].upper()
        alter = 1.0
    else:
        step = note.upper()
        alter = 0.0

    if step not in _NATURAL_SEMITONES:
        raise ValueError(
            f"Onbekende toonhoogtenaam '{step}' in '{s}'. "
            f"Verwacht een van {STEP_NAMES}."
        )

    return Pitch(step=step, octave=octave, alter=alter)


# ── Scale-degree arithmetic ──────────────────────────────────────────────────

def degree_to_pitch(do: Pitch, degree: int, intervals: list[int]) -> Pitch:
    """Return the :class:`~vsa.music.Pitch` at ``degree`` steps from ``do``
    in the scale defined by ``intervals``.

    Degree 0 = do, degree 7 = do one octave higher, degree -1 = ti one
    octave lower, etc.
    """
    n = len(intervals)  # 7
    # Python's floor-division handles negative degrees correctly
    octave_offset = degree // n
    degree_in_scale = degree % n

    do_midi = _pitch_to_midi(do)
    target_midi = do_midi + intervals[degree_in_scale] + octave_offset * 12

    do_step_idx = STEP_NAMES.index(do.step)
    step_idx = (do_step_idx + degree_in_scale) % 7
    step = STEP_NAMES[step_idx]

    # Derive the alter from the difference between the MIDI semitone and the
    # natural semitone of the step letter
    target_semitone_in_octave = target_midi % 12
    natural_semi = _NATURAL_SEMITONES[step]
    alter = float(target_semitone_in_octave - natural_semi)

    # Correct for wrap-around (e.g. Cb, B#)
    if alter > 6:
        alter -= 12.0
    elif alter < -6:
        alter += 12.0

    actual_octave = target_midi // 12 - 1
    return Pitch(step=step, octave=actual_octave, alter=alter)


# ── EHM decomposition ────────────────────────────────────────────────────────

_SHARP_CHARS = frozenset("+#♯")
_FLAT_CHARS = frozenset("b♭")


def ehm_to_motion(ehm: str) -> tuple[int, float]:
    """Decompose an EHM string into ``(ladder_steps, chromatic_alter)``.

    ``ladder_steps`` is the integer number of scale-degree steps (positive =
    up, negative = down, 0 = stay).  Only this component advances the
    diatonic cursor.

    ``chromatic_alter`` is ``+1.0`` for a sharp prefix (``#`` / ``+`` / ``♯``),
    ``-1.0`` for a flat prefix (``b`` / ``♭``), ``0.0`` otherwise.  It affects
    only the sounding pitch of *this* EHM (MusicXML ``alter``), never the
    cursor for the next EHM.  ``+`` is a spelling alias of ``#``.

    Examples::

        ehm_to_motion("/")   → (1, 0.0)
        ehm_to_motion("//")  → (2, 0.0)
        ehm_to_motion("\\\\") → (-2, 0.0)
        ehm_to_motion("#/")  → (1, 1.0)
        ehm_to_motion("+/")  → (1, 1.0)   # alias of #
        ehm_to_motion("b\\\\") → (-2, -1.0)
        ehm_to_motion("#-")  → (0, 1.0)
        ehm_to_motion("-")   → (0, 0.0)
        ehm_to_motion("~")   → (0, 0.0)
    """
    if not ehm:
        return 0, 0.0

    chromatic = 0.0
    base = ehm
    if ehm[0] in _SHARP_CHARS:
        chromatic, base = 1.0, ehm[1:]
    elif ehm[0] in _FLAT_CHARS:
        chromatic, base = -1.0, ehm[1:]

    steps = base.count("/") - base.count("\\")
    return steps, chromatic


# ── PitchMarker helpers ──────────────────────────────────────────────────────

def pitch_marker_degree(ehm_list: list[str]) -> int:
    """Return the scale-degree offset indicated by a pitch-marker's EHM list.

    ``[:]`` → ``[]`` or ``["~"]`` → degree 0 (do).
    ``[//:]`` → ``["//"]`` → degree 2.
    ``[\\\\:]`` → ``["\\\\"]`` → degree -2.
    """
    total = 0
    for ehm in ehm_list:
        steps, _chrom = ehm_to_motion(ehm)
        total += steps
    return total


# ── PitchResolver ────────────────────────────────────────────────────────────

class PitchResolver:
    """Stateful resolver that tracks the current scale degree and returns
    absolute :class:`~vsa.music.Pitch` objects for each EHM it processes.

    Usage::

        resolver = PitchResolver.from_metadata({"do": "F4", "mode": "major"})
        resolver.apply_start_marker([])      # [:]  → start at do
        pitch = resolver.resolve_ehm("/")    # → G4
        pitch = resolver.resolve_ehm("\\\\")  # → F4 again
    """

    def __init__(self, do: Pitch, intervals: list[int]):
        self._do = do
        self._intervals = intervals
        self._degree: int = 0
        self._last_sounding: Pitch | None = None

    @classmethod
    def from_metadata(cls, metadata: dict) -> "PitchResolver":
        """Create a resolver from block metadata (``do``, ``mode`` keys)."""
        do_str = metadata.get("do", "F4")
        mode = metadata.get("mode", "major")

        if mode not in _SCALE_INTERVALS:
            raise UnknownMode(
                f"Onbekende modus: '{mode}'. "
                f"Ondersteunde modi: {sorted(_SCALE_INTERVALS)}."
            )

        do = parse_pitch_string(do_str)
        intervals = _SCALE_INTERVALS[mode]
        return cls(do=do, intervals=intervals)

    def apply_start_marker(self, ehm_list: list[str]) -> None:
        """Set the starting scale degree from the first pitch marker's EHMs."""
        self._degree = pitch_marker_degree(ehm_list)
        self._last_sounding = degree_to_pitch(
            self._do, self._degree, self._intervals
        )

    @property
    def current_degree(self) -> int:
        return self._degree

    @property
    def current_pitch(self) -> Pitch:
        """Pitch for reciting / same-tone continuation (includes last alter)."""
        if self._last_sounding is not None:
            return self._last_sounding
        return degree_to_pitch(self._do, self._degree, self._intervals)

    def resolve_ehm(self, ehm: str) -> Pitch:
        """Apply ``ehm`` to the current degree and return the resulting
        :class:`~vsa.music.Pitch`.

        The internal degree counter is advanced only by the ladder-step count.
        A chromatic prefix adds ±1.0 to the natural scale note's ``alter``.
        Stay (``~`` / ``-``) without a new prefix reuses the previous sounding
        pitch so accidentals persist across same-tone syllables and melisma
        holds — without poisoning the diatonic cursor for the next step.
        """
        steps, chromatic = ehm_to_motion(ehm)
        self._degree += steps

        if steps == 0 and chromatic == 0.0 and self._last_sounding is not None:
            return self._last_sounding

        natural = degree_to_pitch(self._do, self._degree, self._intervals)
        if chromatic != 0.0:
            pitched = Pitch(
                step=natural.step,
                octave=natural.octave,
                alter=natural.alter + chromatic,
            )
        else:
            pitched = natural
        self._last_sounding = pitched
        return pitched



def key_fifths(do: Pitch, mode: str) -> int:
    """Return the MusicXML ``<fifths>`` value for the key signature.

    For major: fifths is derived from the do tonic.
    For minor: the relative major is used (tonic + 3 semitones).
    """
    _MAJOR_SEMITONE_TO_FIFTHS = {
        0: 0,    # C
        7: 1,    # G
        2: 2,    # D
        9: 3,    # A
        4: 4,    # E
        11: 5,   # B
        6: 6,    # F#/Gb (use +6; enharmonic with -6)
        1: -5,   # Db
        8: -4,   # Ab
        3: -3,   # Eb
        10: -2,  # Bb
        5: -1,   # F
    }
    semitone = (_pitch_to_midi(do) - 12) % 12
    if mode == "minor":
        semitone = (semitone + 3) % 12
    return _MAJOR_SEMITONE_TO_FIFTHS.get(semitone, 0)
