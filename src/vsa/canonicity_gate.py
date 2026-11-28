"""C3/C4 canoniciteitsgates.

- C3: canonieke bron vóór conversie (validate).
- C4: steekproef op geschreven Coria-``.mxl`` (playback-checklist).

Contract: docs/formats/contract-index.md §Canoniciteit ·
docs/formats/cli-canoniciteit-audit.md.
"""

from __future__ import annotations

import argparse
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .config import VSAConfig, load_config
from .cli_messages import emit_cli_error, format_cli_error


@dataclass(frozen=True)
class CanonicityIssue:
    """Eén fout die C3 blokkeert (alleen severity error)."""

    code: str
    message_nl: str
    line: int = 1
    column: int = 1


class NonCanonicalSourceError(Exception):
    """Bron faalt C3 (validate-errors)."""

    def __init__(self, path: Path, issues: list[CanonicityIssue]) -> None:
        self.path = Path(path)
        self.issues = list(issues)
        n = len(self.issues)
        super().__init__(f"{self.path}: {n} canoniciteitsfout(en) (C3)")


class NonCanonicalTargetError(Exception):
    """Doel faalt C4 (geschreven ``.mxl``, Score-IR of PDF)."""

    def __init__(self, path: Path, issues: list[CanonicityIssue]) -> None:
        self.path = Path(path)
        self.issues = list(issues)
        n = len(self.issues)
        super().__init__(f"{self.path}: {n} doelfout(en) (C4)")


def add_allow_noncanonical_arg(parser: argparse.ArgumentParser) -> None:
    """CLI-uitzondering: conversie ondanks niet-canonieke bron/doel."""
    parser.add_argument(
        "--allow-noncanonical",
        action="store_true",
        help=(
            "C3/C4-uitzondering: ga door ondanks validate-fouten in de bron "
            "of C4-fouten op geschreven .mxl / Score-IR / .pdf / audio "
            "(niet voor catalogus; zie contract-index §C*)."
        ),
    )


@contextmanager
def _noninteractive_validate() -> Iterator[None]:
    """C3 mag nooit TTY-prompts openen (dictionary-fix).

    Zet ``syllable_dict_check._force_noninteractive`` — dat wint binnen
    :func:`is_interactive_stdin` zelf, ook bij ``from X import``-bindings.
    """
    from . import syllable_dict_check

    previous = syllable_dict_check._force_noninteractive
    syllable_dict_check._force_noninteractive = True
    try:
        yield
    finally:
        syllable_dict_check._force_noninteractive = previous


def check_canonical_source(
    path: Path | str,
    *,
    config: VSAConfig | None = None,
) -> list[CanonicityIssue]:
    """Geef error-level issues terug; lege lijst = bron OK voor C3.

    - ``.vsa``: ``validate_file`` (incl. syllabificatie/dictionary).
    - ``.mvsa``: ``validate_mvsa_path`` errors.
    - ``.mscz``: structureel (geldige zip + leesbare ``.mscx``); geen S*.

    Altijd non-interactief (geen dictionary-TTY-prompts).
    """
    path = Path(path)
    suffix = path.suffix.lower()
    with _noninteractive_validate():
        if suffix == ".vsa":
            return _check_vsa(path, config=config)
        if suffix == ".mvsa":
            return _check_mvsa(path)
        if suffix == ".mscz":
            return _check_mscz(path)
    return []


def require_canonical_source(
    path: Path | str,
    *,
    config: VSAConfig | None = None,
    allow_noncanonical: bool = False,
) -> None:
    """Raise :exc:`NonCanonicalSourceError` als C3 faalt."""
    if allow_noncanonical:
        return
    issues = check_canonical_source(path, config=config)
    if issues:
        raise NonCanonicalSourceError(Path(path), issues)


def cli_gate_source(
    path: Path | str,
    args: object | None = None,
    *,
    config: VSAConfig | None = None,
) -> bool:
    """C3 voor één bron in een CLI-loop.

    Returns ``True`` als de conversie moet stoppen (fout geprint).
    """
    allow = bool(getattr(args, "allow_noncanonical", False)) if args else False
    try:
        require_canonical_source(
            path, config=config, allow_noncanonical=allow
        )
    except NonCanonicalSourceError as exc:
        emit_noncanonical_error(exc)
        return True
    return False


def emit_noncanonical_error(
    exc: NonCanonicalSourceError | NonCanonicalTargetError,
) -> None:
    """Schrijf C3/C4-fouten naar stderr (beheerder-leesbaar)."""
    first = exc.issues[0]
    more = len(exc.issues) - 1
    extra = f" (+{more} andere)" if more > 0 else ""
    if isinstance(exc, NonCanonicalTargetError):
        if first.code.startswith("SCORE-IR-"):
            hint = (
                "Geschreven Score-IR faalt structurele C4 (JSON/format/"
                "from-ir-emit). Herstel de bron of gebruik "
                "--allow-noncanonical. Zie contract-index §C* · score-ir.md."
            )
        elif first.code.startswith("PDF-"):
            hint = (
                "Geschreven .pdf faalt structurele C4 (geen geldige "
                "PDF-header). Herhaal de export of gebruik "
                "--allow-noncanonical. Zie contract-index §C* · checklist P*."
            )
        elif first.code.startswith("AUDIO-"):
            hint = (
                "Geschreven audio faalt structurele C4 (geen herkenbare "
                "mp3/ogg/wav-header). Herhaal de export of gebruik "
                "--allow-noncanonical. Zie contract-index §C* · audio.md."
            )
        else:
            hint = (
                "Geschreven .mxl faalt de Coria/playback-checklist (C4). "
                "Controleer met `mxl validate`; normaliseer of herstel de bron. "
                "Nood: --allow-noncanonical. Zie contract-index §C*."
            )
        prefix = f"{first.code}: " if first.code else ""
    elif first.code.startswith("MSCZ-"):
        hint = (
            "Bron-.mscz faalt structurele C3 (geldige zip + leesbare "
            ".mscx). Herstel het MuseScore-bestand of gebruik "
            "--allow-noncanonical. Zie contract-index §C*."
        )
        prefix = f"{first.code}: "
    else:
        hint = (
            "Maak de bron canoniek (`vsa validate` / `mvsa validate`, "
            "eventueel `syllabify`) of gebruik --allow-noncanonical "
            "(C3-uitzondering). Zie docs/formats/contract-index.md §C*."
        )
        prefix = ""
    emit_cli_error(
        f"{prefix}{first.message_nl}{extra}",
        path=exc.path,
        line=first.line,
        column=first.column if first.column else None,
        hint=hint,
    )
    for issue in exc.issues[1:6]:
        msg = issue.message_nl
        if isinstance(exc, NonCanonicalTargetError) and issue.code:
            msg = f"{issue.code}: {msg}"
        print(
            format_cli_error(
                msg,
                path=exc.path,
                line=issue.line,
                column=issue.column if issue.column else None,
            ),
            file=sys.stderr,
        )
    if len(exc.issues) > 6:
        print(
            f"… en {len(exc.issues) - 6} andere fout(en).",
            file=sys.stderr,
        )


def playback_profile_for_bron(bron: Path | str | None) -> str:
    """``mono`` voor `.vsa`; anders ``satb`` (mvsa/mscz)."""
    if bron is None:
        return "satb"
    return "mono" if Path(bron).suffix.lower() == ".vsa" else "satb"


def check_canonical_mxl_target(
    path: Path | str,
    *,
    profile: str | None = None,
    bron: Path | str | None = None,
) -> list[CanonicityIssue]:
    """C4: playback-checklist op geschreven ``.mxl`` / ``.musicxml``."""
    from .musicxml_playback_checklist import validate_playback_mxl_path

    path = Path(path)
    prof = profile or playback_profile_for_bron(bron)
    findings = validate_playback_mxl_path(path, profile=prof)
    return [
        CanonicityIssue(code=f.code, message_nl=f.message)
        for f in findings
    ]


def require_canonical_mxl_target(
    path: Path | str,
    *,
    profile: str | None = None,
    bron: Path | str | None = None,
    allow_noncanonical: bool = False,
) -> None:
    """Raise :exc:`NonCanonicalTargetError` als C4 faalt."""
    if allow_noncanonical:
        return
    issues = check_canonical_mxl_target(
        path, profile=profile, bron=bron
    )
    if issues:
        raise NonCanonicalTargetError(Path(path), issues)


def check_canonical_score_ir_target(
    path: Path | str,
) -> list[CanonicityIssue]:
    """C4: Score-IR JSON leesbaar + format/profile + from-ir-emitbaar."""
    import json

    from .score_ir import SCORE_IR_FORMAT, SCORE_IR_PROFILE
    from .score_ir_musicxml import ScoreIrMusicxmlError, score_ir_to_musicxml

    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [
            CanonicityIssue(
                code="SCORE-IR-READ",
                message_nl=f"{path.name}: kan Score-IR niet lezen ({exc})",
            )
        ]
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        return [
            CanonicityIssue(
                code="SCORE-IR-JSON",
                message_nl=f"{path.name}: ongeldige JSON ({exc.msg})",
            )
        ]
    if not isinstance(doc, dict):
        return [
            CanonicityIssue(
                code="SCORE-IR-JSON",
                message_nl=f"{path.name}: Score-IR-root moet een object zijn",
            )
        ]
    if doc.get("format") != SCORE_IR_FORMAT:
        return [
            CanonicityIssue(
                code="SCORE-IR-FORMAT",
                message_nl=(
                    f"{path.name}: verwacht format {SCORE_IR_FORMAT!r}, "
                    f"kreeg {doc.get('format')!r}"
                ),
            )
        ]
    if doc.get("profile") != SCORE_IR_PROFILE:
        return [
            CanonicityIssue(
                code="SCORE-IR-PROFILE",
                message_nl=(
                    f"{path.name}: verwacht profile {SCORE_IR_PROFILE!r}, "
                    f"kreeg {doc.get('profile')!r}"
                ),
            )
        ]
    measures = doc.get("measures")
    if not isinstance(measures, list):
        return [
            CanonicityIssue(
                code="SCORE-IR-MEASURES",
                message_nl=f"{path.name}: measures moet een lijst zijn",
            )
        ]
    try:
        score_ir_to_musicxml(doc)
    except ScoreIrMusicxmlError as exc:
        return [
            CanonicityIssue(
                code="SCORE-IR-EMIT",
                message_nl=f"{path.name}: from-ir-emit faalt ({exc})",
            )
        ]
    return []


def require_canonical_score_ir_target(
    path: Path | str,
    *,
    allow_noncanonical: bool = False,
) -> None:
    """Raise :exc:`NonCanonicalTargetError` als Score-IR-C4 faalt."""
    if allow_noncanonical:
        return
    issues = check_canonical_score_ir_target(path)
    if issues:
        raise NonCanonicalTargetError(Path(path), issues)


def check_canonical_pdf_target(path: Path | str) -> list[CanonicityIssue]:
    """C4 structureel: bestand bestaat, niet leeg, header ``%PDF``."""
    path = Path(path)
    if not path.is_file():
        return [
            CanonicityIssue(
                code="PDF-MISS",
                message_nl=f"{path.name}: PDF-bestand ontbreekt na export",
            )
        ]
    try:
        size = path.stat().st_size
    except OSError as exc:
        return [
            CanonicityIssue(
                code="PDF-READ",
                message_nl=f"{path.name}: kan PDF niet lezen ({exc})",
            )
        ]
    if size < 5:
        return [
            CanonicityIssue(
                code="PDF-EMPTY",
                message_nl=f"{path.name}: PDF is leeg of te klein ({size} bytes)",
            )
        ]
    try:
        with path.open("rb") as handle:
            head = handle.read(8)
    except OSError as exc:
        return [
            CanonicityIssue(
                code="PDF-READ",
                message_nl=f"{path.name}: kan PDF-header niet lezen ({exc})",
            )
        ]
    if not head.startswith(b"%PDF"):
        return [
            CanonicityIssue(
                code="PDF-HEADER",
                message_nl=(
                    f"{path.name}: geen PDF-header (verwacht %PDF…, "
                    f"kreeg {head[:8]!r})"
                ),
            )
        ]
    return []


def require_canonical_pdf_target(
    path: Path | str,
    *,
    allow_noncanonical: bool = False,
) -> None:
    """Raise :exc:`NonCanonicalTargetError` als PDF-C4 faalt."""
    if allow_noncanonical:
        return
    issues = check_canonical_pdf_target(path)
    if issues:
        raise NonCanonicalTargetError(Path(path), issues)


def check_canonical_audio_target(path: Path | str) -> list[CanonicityIssue]:
    """C4 structureel: bestand + container-header (mp3 / ogg / wav)."""
    path = Path(path)
    if not path.is_file():
        return [
            CanonicityIssue(
                code="AUDIO-MISS",
                message_nl=f"{path.name}: audiobestand ontbreekt na export",
            )
        ]
    try:
        size = path.stat().st_size
    except OSError as exc:
        return [
            CanonicityIssue(
                code="AUDIO-READ",
                message_nl=f"{path.name}: kan audio niet lezen ({exc})",
            )
        ]
    if size < 4:
        return [
            CanonicityIssue(
                code="AUDIO-EMPTY",
                message_nl=(
                    f"{path.name}: audiobestand is leeg of te klein ({size} bytes)"
                ),
            )
        ]
    try:
        with path.open("rb") as handle:
            head = handle.read(12)
    except OSError as exc:
        return [
            CanonicityIssue(
                code="AUDIO-READ",
                message_nl=f"{path.name}: kan audio-header niet lezen ({exc})",
            )
        ]

    suffix = path.suffix.lower()
    ok = False
    if suffix == ".mp3":
        # ID3-tag of MPEG-frame sync (11 bits 1).
        ok = head.startswith(b"ID3") or (
            len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0
        )
    elif suffix == ".ogg":
        ok = head.startswith(b"OggS")
    elif suffix == ".wav":
        ok = head.startswith(b"RIFF") and len(head) >= 12 and head[8:12] == b"WAVE"
    else:
        # Onbekende extensie: accepteer bekende headers.
        ok = (
            head.startswith(b"ID3")
            or head.startswith(b"OggS")
            or (head.startswith(b"RIFF") and head[8:12] == b"WAVE")
            or (
                len(head) >= 2
                and head[0] == 0xFF
                and (head[1] & 0xE0) == 0xE0
            )
        )
    if not ok:
        return [
            CanonicityIssue(
                code="AUDIO-HEADER",
                message_nl=(
                    f"{path.name}: geen herkenbare audio-header voor "
                    f"{suffix or 'onbekend formaat'} (kreeg {head[:8]!r})"
                ),
            )
        ]
    return []


def require_canonical_audio_target(
    path: Path | str,
    *,
    allow_noncanonical: bool = False,
) -> None:
    """Raise :exc:`NonCanonicalTargetError` als audio-C4 faalt."""
    if allow_noncanonical:
        return
    issues = check_canonical_audio_target(path)
    if issues:
        raise NonCanonicalTargetError(Path(path), issues)


def _check_vsa(
    path: Path, *, config: VSAConfig | None
) -> list[CanonicityIssue]:
    from .validation_runner import validate_file

    cfg = config if config is not None else load_config(None)
    result = validate_file(path, config=cfg)
    out: list[CanonicityIssue] = []
    for msg in result.messages:
        if msg.severity != "error":
            continue
        out.append(
            CanonicityIssue(
                code=msg.code,
                message_nl=msg.message_nl,
                line=msg.line,
                column=msg.column,
            )
        )
    return out


def _check_mvsa(path: Path) -> list[CanonicityIssue]:
    from .mvsa_validate import validate_mvsa_path

    diagnostics = validate_mvsa_path(path)
    out: list[CanonicityIssue] = []
    for d in diagnostics:
        if getattr(d, "severity", "error") != "error":
            continue
        msg = getattr(d, "message_nl", None) or getattr(d, "message", "")
        out.append(
            CanonicityIssue(
                code=d.code,
                message_nl=str(msg),
                line=getattr(d, "line", 1) or 1,
                column=getattr(d, "column", 1) or 1,
            )
        )
    return out


def _check_mscz(path: Path) -> list[CanonicityIssue]:
    """Structurele C3: zip + één leesbare ``.mscx`` (geen S*/leesbaarheid)."""
    import zipfile

    if not path.is_file():
        return [
            CanonicityIssue(
                code="MSCZ-ZIP",
                message_nl=f"bestand ontbreekt of is geen bestand: {path.name}",
            )
        ]
    try:
        with zipfile.ZipFile(path) as archive:
            mscx_name = next(
                (
                    name
                    for name in archive.namelist()
                    if name.lower().endswith(".mscx")
                ),
                None,
            )
            if mscx_name is None:
                return [
                    CanonicityIssue(
                        code="MSCZ-MSCX",
                        message_nl=(
                            f"{path.name}: geen .mscx in het MuseScore-archief"
                        ),
                    )
                ]
            raw = archive.read(mscx_name)
    except zipfile.BadZipFile:
        return [
            CanonicityIssue(
                code="MSCZ-ZIP",
                message_nl=(
                    f"{path.name}: geen geldige zip (verwacht .mscz-archief)"
                ),
            )
        ]
    except OSError as exc:
        return [
            CanonicityIssue(
                code="MSCZ-ZIP",
                message_nl=f"{path.name}: kan archief niet lezen ({exc})",
            )
        ]

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            return [
                CanonicityIssue(
                    code="MSCZ-MSCX-READ",
                    message_nl=(
                        f"{path.name}: .mscx is niet als UTF-8 te lezen"
                    ),
                )
            ]

    head = text.lstrip()[:2000].lower()
    if "<musescore" not in head and "musescore" not in head:
        return [
            CanonicityIssue(
                code="MSCZ-MSCX-XML",
                message_nl=(
                    f"{path.name}: .mscx lijkt geen MuseScore-score (geen "
                    "museScore-wortel)"
                ),
            )
        ]
    return []
