"""Read-only playback checklist for Coria/MXL (canonical-checklists M-reeks).

Used by ``mxl validate``. Does not mutate XML.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from .musicxml_coria_timing import CORIA_FORBIDDEN_TAGS, strip_doctype
from .musicxml_satb_layout import local
from .mvsa_import import read_musicxml_file

_PLAYBACK_MIDI_SOUND = "keyboard.piano.grand"
_PLAYBACK_MIDI_PROGRAM = "1"
_PLAYBACK_PART_NAMES = {
    "P1": "Soprano",
    "P2": "Alto",
    "P3": "Tenor",
    "P4": "Bass",
}
# Tags that must be absent for Coria importer (demo check_coria_mxl).
# movement-title is allowed (MVSA @ondertitel); not in VALIDATE_FORBIDDEN.
_VALIDATE_FORBIDDEN = CORIA_FORBIDDEN_TAGS - {"movement-title"}
_LICENSE_IN_SOURCE = re.compile(
    r"(?i)\b(CC\s*BY|creativecommons|colofon|all\s+rights\s+reserved)\b"
)


@dataclass(frozen=True)
class ChecklistFinding:
    """One checklist violation."""

    code: str
    message: str


def _child(el: ET.Element, name: str) -> ET.Element | None:
    for c in el:
        if local(c.tag) == name:
            return c
    return None


def _children(el: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in el if local(c.tag) == name]


def _text(el: ET.Element | None) -> str:
    return (el.text or "").strip() if el is not None else ""


def coria_importer_violations(root: ET.Element) -> list[str]:
    """Return forbidden tag names (and bad version) still present in *root*.

    Port of VSA-demo ``coria_importer_violations``, minus ``movement-title``
    (kept for ``@ondertitel``).
    """
    found: set[str] = set()
    for el in root.iter():
        tag = local(el.tag)
        if tag in _VALIDATE_FORBIDDEN:
            found.add(tag)
    version = root.attrib.get("version")
    if version not in {"3.0", "3.1"}:
        found.add(f"version:{version}")
    return sorted(found)


def validate_playback_musicxml(
    xml: str,
    *,
    profile: str = "satb",
) -> list[ChecklistFinding]:
    """Non-mutating checklist. Empty list = OK for implemented rules."""
    if profile not in {"satb", "mono"}:
        return [
            ChecklistFinding(
                "PROFILE",
                f"onbekend profiel {profile!r} (verwacht satb of mono)",
            )
        ]
    findings: list[ChecklistFinding] = []
    cleaned = strip_doctype(xml)
    if "<!DOCTYPE" in xml.upper():
        findings.append(
            ChecklistFinding("M4", "DOCTYPE aanwezig (Coria DTD-fetch)")
        )
    try:
        root = ET.fromstring(cleaned)
    except ET.ParseError as exc:
        return [ChecklistFinding("PARSE", f"ongeldige MusicXML: {exc}")]

    if _child(root, "defaults") is not None:
        findings.append(
            ChecklistFinding("M9", "defaults/layout aanwezig (engraving-only)")
        )

    for tag in coria_importer_violations(root):
        findings.append(
            ChecklistFinding(
                "M4",
                f"Coria-onveilige markup: {tag}",
            )
        )

    part_list = _child(root, "part-list")
    score_parts = _children(part_list, "score-part") if part_list is not None else []
    body_parts = [el for el in root if local(el.tag) == "part"]
    body_ids = {p.get("id") for p in body_parts}

    if profile == "satb":
        for pid, name in _PLAYBACK_PART_NAMES.items():
            sp = next((s for s in score_parts if s.get("id") == pid), None)
            if sp is None:
                findings.append(
                    ChecklistFinding("M2", f"score-part {pid} ontbreekt")
                )
                continue
            pname = _text(_child(sp, "part-name"))
            if pname != name:
                findings.append(
                    ChecklistFinding(
                        "M2",
                        f"part-name {pid} is {pname!r}, verwacht {name!r}",
                    )
                )
            if pid not in body_ids:
                findings.append(
                    ChecklistFinding(
                        "M2",
                        f"body <part id={pid!r}> ontbreekt "
                        "(part-list/body mismatch)",
                    )
                )
            _check_piano(sp, pid, findings)
        if len(body_parts) != 4:
            findings.append(
                ChecklistFinding(
                    "M2",
                    f"verwacht 4 body-parts, kreeg {len(body_parts)}",
                )
            )
        findings.extend(_check_monophonic_parts(body_parts))
    else:
        if not score_parts:
            findings.append(ChecklistFinding("M2", "geen score-part"))
        else:
            _check_piano(score_parts[0], score_parts[0].get("id") or "P1", findings)
        if not body_parts:
            findings.append(ChecklistFinding("M2", "geen body <part>"))
        else:
            findings.extend(_check_monophonic_parts(body_parts))

    findings.extend(_check_identification(root))
    return findings


def _check_monophonic_parts(body_parts: list[ET.Element]) -> list[ChecklistFinding]:
    """M18: elke part is één oefenlijn (geen partituur-restanten).

    Maximaal één finding per (part, schendingstype) — geen spam per noot.
    """
    findings: list[ChecklistFinding] = []
    for part in body_parts:
        pid = part.get("id") or "?"
        seen: set[str] = set()

        def _once(kind: str, message: str) -> None:
            if kind in seen:
                return
            seen.add(kind)
            findings.append(ChecklistFinding("M18", message))

        for el in part.iter():
            tag = local(el.tag)
            if tag == "staves":
                text = _text(el)
                if text and text != "1":
                    _once(
                        "staves",
                        f"{pid}: <staves>{text}</staves> "
                        "(verwacht één balk per playback-part)",
                    )
            elif tag == "clef" and el.get("number") not in (None, "1"):
                _once(
                    "clef",
                    f"{pid}: clef number={el.get('number')!r} "
                    "(alleen clef zonder number of number=1)",
                )
            elif tag in {"backup", "forward"}:
                _once(
                    tag,
                    f"{pid}: <{tag}> in playback-part "
                    "(meerstemmig restant; Coria = één lijn per part)",
                )
            elif tag != "note":
                continue
            staff = None
            voice = None
            has_chord = False
            for child in el:
                ctag = local(child.tag)
                if ctag == "staff":
                    staff = _text(child)
                elif ctag == "voice":
                    voice = _text(child)
                elif ctag == "chord":
                    has_chord = True
            if has_chord:
                _once(
                    "chord",
                    f"{pid}: <chord/> in playback-part "
                    "(octaaf/divisi → één toon; B2 later apart)",
                )
            if staff and staff != "1":
                _once(
                    "staff",
                    f"{pid}: note staff={staff!r} (verwacht 1)",
                )
            if voice and voice != "1":
                _once(
                    "voice",
                    f"{pid}: note voice={voice!r} (verwacht 1)",
                )
    return findings


def _check_piano(
    score_part: ET.Element,
    part_id: str,
    findings: list[ChecklistFinding],
) -> None:
    sound = None
    for si in _children(score_part, "score-instrument"):
        sound = _text(_child(si, "instrument-sound"))
        if sound:
            break
    if sound != _PLAYBACK_MIDI_SOUND:
        findings.append(
            ChecklistFinding(
                "M8",
                f"{part_id}: instrument-sound is {sound!r}, "
                f"verwacht {_PLAYBACK_MIDI_SOUND!r}",
            )
        )
    midi = _child(score_part, "midi-instrument")
    if midi is None:
        findings.append(
            ChecklistFinding("M8", f"{part_id}: midi-instrument ontbreekt")
        )
        return
    prog = _text(_child(midi, "midi-program"))
    if prog != _PLAYBACK_MIDI_PROGRAM:
        findings.append(
            ChecklistFinding(
                "M8",
                f"{part_id}: midi-program is {prog!r}, "
                f"verwacht {_PLAYBACK_MIDI_PROGRAM!r}",
            )
        )


def _misc_bron(ident: ET.Element) -> str:
    misc = _child(ident, "miscellaneous")
    if misc is None:
        return ""
    for field in _children(misc, "miscellaneous-field"):
        if field.get("name") == "bron":
            return _text(field)
    return ""


def _check_identification(root: ET.Element) -> list[ChecklistFinding]:
    findings: list[ChecklistFinding] = []
    ident = _child(root, "identification")
    if ident is None:
        return findings
    source = _text(_child(ident, "source"))
    rights = _text(_child(ident, "rights"))
    encoding = _child(ident, "encoding")
    bron = _misc_bron(ident)
    # Coria play_from_url: ``<source>`` + ``<encoding>`` → "translation failed".
    if source and encoding is not None:
        findings.append(
            ChecklistFinding(
                "META",
                "identification/source mag niet samen met encoding "
                "(Coria: translation failed); zet bron in "
                "miscellaneous-field name=\"bron\"",
            )
        )
    # Coria: ``miscellaneous`` vóór ``encoding`` → "translation failed".
    child_tags = [local(c.tag) for c in ident]
    if (
        "encoding" in child_tags
        and "miscellaneous" in child_tags
        and child_tags.index("miscellaneous") < child_tags.index("encoding")
    ):
        findings.append(
            ChecklistFinding(
                "META",
                "identification/miscellaneous mag niet vóór encoding "
                "(Coria: translation failed); zet encoding vóór miscellaneous",
            )
        )
    if source and _LICENSE_IN_SOURCE.search(source):
        findings.append(
            ChecklistFinding(
                "META",
                "identification/source lijkt op licentie/copyright "
                "(hoort in rights, niet source)",
            )
        )
    if (
        not source
        and not bron
        and rights
        and _LICENSE_IN_SOURCE.search(rights)
    ):
        findings.append(
            ChecklistFinding(
                "META",
                "miscellaneous-field name=\"bron\" ontbreekt terwijl rights "
                "een licentie bevat (bronvermelding ontbreekt)",
            )
        )
    return findings


def validate_playback_mxl_path(
    path: Path,
    *,
    profile: str = "satb",
) -> list[ChecklistFinding]:
    """Validate an on-disk ``.mxl`` / ``.musicxml`` file."""
    xml = read_musicxml_file(Path(path))
    return validate_playback_musicxml(xml, profile=profile)
