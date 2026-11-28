"""Beginnoten van een stuk, voor de inzet: notennaam en laddergraad.

Vierstemmig uit ``*.from-ir.musicxml`` (S, A, T, B), of de eerste noot van de
melodie uit een ``.vsa``. De laddergraad (do-re-mi) is relatief aan do: bij
MusicXML de majeurtoon van de voortekens, bij ``.vsa`` de ``do`` uit de
frontmatter. Contract: docs/formats/from-ir.md §Beginnoten.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from .pitch_resolver import parse_pitch_string
from .vsa_stanzas import extract_stanza_notes
from .yaml_frontmatter import parse_vsa_frontmatter_with_body_offset

_LETTERS = "CDEFGAB"
_HALVE_TONEN = (0, 2, 4, 5, 7, 9, 11)
_GRADEN = ("do", "re", "mi", "fa", "so", "la", "ti")
# Majeurtonica bij -7 t/m 7 voortekens: (stam, alteratie).
_TONICA = (
    ("C", -1), ("G", -1), ("D", -1), ("A", -1), ("E", -1), ("B", -1), ("F", 0),
    ("C", 0),
    ("G", 0), ("D", 0), ("A", 0), ("E", 0), ("B", 0), ("F", 1), ("C", 1),
)
# Stemmen in from-ir: (deel, voice).
_STEMMEN = (("S", 0, "1"), ("A", 0, "2"), ("T", 1, "1"), ("B", 1, "2"))


@dataclass(frozen=True)
class Beginnoot:
    stem: str  # S, A, T of B; leeg bij alleen een melodie
    naam: str  # Nederlandse notennaam, bijv. "A", "Es", "Fis"
    graad: str  # laddergraad t.o.v. do, bijv. "mi", "bti", "#fa"


def notennaam(step: str, alter: int) -> str:
    """Nederlandse notennaam; B zonder voorteken heet B, met mol Bes."""
    if alter >= 0:
        return step + "is" * alter
    eerste = step + ("s" if step in "AE" else "es")
    return eerste + ("as" if step == "A" else "es") * (-alter - 1)


def laddergraad(step: str, alter: int, do_step: str, do_alter: int) -> str:
    trap = (_LETTERS.index(step) - _LETTERS.index(do_step)) % 7
    noot = _HALVE_TONEN[_LETTERS.index(step)] + alter
    do = _HALVE_TONEN[_LETTERS.index(do_step)] + do_alter
    verschil = (noot - do - _HALVE_TONEN[trap] + 6) % 12 - 6
    voor = "#" * verschil if verschil > 0 else "b" * -verschil
    return voor + _GRADEN[trap]


def _noot(stem: str, step: str, alter: int, do: tuple[str, int]) -> Beginnoot:
    return Beginnoot(stem, notennaam(step, alter), laddergraad(step, alter, *do))


def beginnoten_uit_musicxml(path: Path) -> list[Beginnoot] | None:
    """S, A, T en B; ``None`` als het bestand niet zo is opgebouwd."""
    root = ET.parse(path).getroot()
    delen = root.findall("part")
    fifths = root.findtext("part/measure/attributes/key/fifths")
    if len(delen) != 2 or fifths is None or not -7 <= int(fifths) <= 7:
        return None
    do = _TONICA[int(fifths) + 7]
    uit: list[Beginnoot] = []
    for stem, deel, voice in _STEMMEN:
        pitch = next(
            (
                note.find("pitch")
                for note in delen[deel].iter("note")
                if (note.findtext("voice") or "1") == voice
                and note.find("pitch") is not None
            ),
            None,
        )
        if pitch is None:
            return None
        alter = int(float(pitch.findtext("alter") or 0))
        uit.append(_noot(stem, pitch.findtext("step") or "", alter, do))
    return uit


def beginnoot_uit_vsa(path: Path) -> list[Beginnoot] | None:
    """Eerste noot van de melodie (stem leeg); ``None`` zonder noten."""
    tekst = path.read_text(encoding="utf-8-sig")
    meta, _body, _offset = parse_vsa_frontmatter_with_body_offset(tekst)
    noot = next((n for regel in extract_stanza_notes(tekst) for n in regel), None)
    if noot is None:
        return None
    # Zelfde standaard-do als PitchResolver.from_metadata.
    do = parse_pitch_string(str(meta.get("do", "F4")))
    return [_noot("", noot.pitch.step, int(noot.pitch.alter), (do.step, int(do.alter)))]
