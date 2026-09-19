from __future__ import annotations

from pathlib import Path

from .validation_runner import ValidationMessage

_SHORT_MESSAGES_NL: dict[str, str] = {
    "VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH": "Hoogte-markering klopt niet.",
    "VSA-SEMANTIC-MODIFIER-COUNT-MISMATCH": (
        "Hoogte- en lengtemodifiers komen niet overeen."
    ),
    "VSA-SYNTAX-UNEXPECTED-CLOSE-BRACE": "Losse sluitaccolade.",
    "VSA-SYNTAX-UNCLOSED-SCOPE": "Scope zonder afsluitende accolade.",
    "VSA-SYNTAX-EMPTY-SCOPE": "Leeg zangelement.",
    "VSA-SYNTAX-WHITESPACE-IN-SCOPE": "Whitespace binnen zangelement.",
    "VSA-SYNTAX-UNCLOSED-PITCH-MARKER": "Toonhoogte-markering zonder ']'.",
    "VSA-SYNTAX-PITCH-MARKER-MISSING-COLON": "Toonhoogte-markering mist ':'.",
    "VSA-SYNTAX-INVALID-SCOPE": "Zangelement heeft geen herkenbare opbouw.",
    "VSA-SYNTAX-EMPTY-SUNG-TEXT": "Zangelement zonder gezongen tekst.",
    "VSA-SYNTAX-MODIFIER-IN-SUNG-TEXT": "Modifierteken in gezongen tekst.",
    "VSA-SYNTAX-HALFTOON-PREFIX-AFTER-BASE": (
        "Halftoon-prefix moet vóór de basisbeweging staan."
    ),
    "VSA-SYNTAX-INVALID-ALIGNMENT-MARKER": "Ongeldige '&'-markering.",
    "VSA-PARSE-ERROR": "VSA-syntaxfout.",
    "VSA-BLOCK-PARSE-ERROR": "Markdown VSA-blokfout.",
    "VSA-PATH-NOT-FOUND": "Pad niet gevonden.",
    "VSA-INCLUDE-VSA-ERROR": "Include-vsa-fout.",
}


def validation_location_label(message: ValidationMessage) -> str:
    """Return ``pad:regel:kolom`` with a navigable path when possible."""
    path_label = _source_path_label(message.source)
    return f"{path_label}:{message.line}:{message.column}"


def _source_path_label(source: str) -> str:
    raw = (source or "").strip()
    if not raw:
        return "<onbekend>"

    path = Path(raw)
    try:
        cwd = Path.cwd().resolve()
        resolved = path.resolve() if path.is_absolute() else (cwd / path).resolve()
        try:
            relative = resolved.relative_to(cwd)
            return relative.as_posix()
        except ValueError:
            pass
        if path.is_absolute():
            return resolved.as_posix()
    except OSError:
        pass

    return raw.replace("\\", "/")


def validation_short_message(message: ValidationMessage) -> str:
    short = _SHORT_MESSAGES_NL.get(message.code)
    if short is not None:
        return short

    text = message.message_nl.strip()
    if not text:
        return message.code

    for separator in (". ", "? ", "! "):
        index = text.find(separator)
        if index >= 0:
            return text[: index + 1]

    return text


def validation_detail_headline(message: ValidationMessage) -> str:
    severity = getattr(message, "severity", "error").upper()
    if message.code == "VSA-SEMANTIC-HEIGHT-MARKER-MISMATCH":
        detail = message.message_nl
    else:
        detail = validation_short_message(message)
    return f"{severity}: {message.code}: {detail}"


def format_validation_message(
    message: ValidationMessage,
    *,
    summary: bool = False,
    source_line: str | None = None,
) -> list[str]:
    location = validation_location_label(message)

    if summary:
        return [f"{location}: {message.code}"]

    lines = [
        location,
        validation_detail_headline(message),
    ]

    if source_line is not None:
        lines.append(source_line)
        lines.append(" " * max(0, message.column - 1) + "^")

    hint = (getattr(message, "hint_nl", "") or "").strip()
    if hint:
        lines.append(f"Hint: {hint}")

    doc_url = (getattr(message, "doc_url", "") or "").strip()
    if doc_url:
        lines.append(f"Zie: {doc_url}")

    return lines
