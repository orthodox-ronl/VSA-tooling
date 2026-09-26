from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Pitch:
    """Absolute pitch in MusicXML terms."""
    step: str       # "C", "D", "E", "F", "G", "A", "B"
    octave: int     # e.g. 4
    alter: float    # 0.0 natural, 1.0 sharp, -1.0 flat

    def __str__(self) -> str:
        alter_str = ""
        if self.alter == 1.0:
            alter_str = "#"
        elif self.alter == -1.0:
            alter_str = "b"
        elif self.alter != 0.0:
            alter_str = f"({self.alter:+.1f})"
        return f"{self.step}{alter_str}{self.octave}"


@dataclass(frozen=True)
class Duration:
    """MusicXML note duration derived from an ELM."""
    note_type: str  # "quarter", "half", "whole", "breve", "eighth", "16th"
    dots: int = 0   # 0 = normal, 1 = dotted

    # MusicXML <duration> in divisions (divisions-per-quarter = 4)
    divisions: int = 4

    @property
    def divisions_value(self) -> int:
        """Actual MusicXML <duration> value at 4 divisions per quarter."""
        base = {
            "16th": 1,
            "eighth": 2,
            "quarter": 4,
            "half": 8,
            "whole": 16,
            "breve": 32,
        }[self.note_type]
        if self.dots == 1:
            base = base + base // 2
        return base


@dataclass
class MusicalPosition:
    text: str
    ehm: str
    elm: str
    pitch: Optional[Pitch] = None
    duration: Optional[Duration] = None
    is_melisma_start: bool = False
    is_melisma_middle: bool = False
    is_melisma_end: bool = False
