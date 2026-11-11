"""CLI-foutmeldingen voor beheerders (pad + locatie + herstelhint).

Contract: ``docs/specification/error-handling.md`` (sectie CLI-/omgevingsfouten).

Vorm:
- met bronlocatie: ``pad:regel:kolom: beschrijving`` (kolom weglaten als onbekend);
- alleen pad: ``pad: beschrijving``;
- zonder pad (CLI-gebruik): alleen de beschrijving;
- optioneel tweede regel: ``Hint: …`` (wat de beheerder kan doen).
"""

from __future__ import annotations

import sys
from pathlib import Path


def path_label(path: Path | str | None) -> str:
    """Leesbaar pad t.o.v. cwd wanneer mogelijk (forward slashes)."""
    if path is None:
        return ""
    raw = str(path).strip()
    if not raw:
        return "<onbekend>"
    p = Path(raw)
    try:
        cwd = Path.cwd().resolve()
        resolved = p.resolve() if p.is_absolute() else (cwd / p).resolve()
        try:
            return resolved.relative_to(cwd).as_posix()
        except ValueError:
            pass
        if p.is_absolute():
            return resolved.as_posix()
    except OSError:
        pass
    return raw.replace("\\", "/")


def format_cli_error(
    message: str,
    *,
    path: Path | str | None = None,
    line: int | None = None,
    column: int | None = None,
    hint: str | None = None,
) -> str:
    """Bouw een beheerder-leesbare fouttekst (meerdere regels toegestaan).

    Locatie op de eerste regel; verdere regels van ``message`` blijven
    onder elkaar. Hint-blok daaronder, eveneens regel-per-regel.
    """
    raw = (message or "").strip() or "Onbekende fout."
    msg_lines = raw.splitlines() or [raw]
    first = (msg_lines[0] if msg_lines else raw).strip() or "Onbekende fout."
    rest = [ln.rstrip() for ln in msg_lines[1:]]

    label = path_label(path) if path is not None else ""
    if label:
        if line is not None and column is not None:
            head = f"{label}:{int(line)}:{int(column)}: {first}"
        elif line is not None:
            head = f"{label}:{int(line)}: {first}"
        else:
            head = f"{label}: {first}"
    else:
        head = first

    parts = [head]
    parts.extend(rest)

    hint_text = (hint or "").strip()
    if hint_text:
        hint_lines = hint_text.splitlines()
        first_hint = hint_lines[0].strip()
        if not first_hint.lower().startswith("hint:"):
            first_hint = f"Hint: {first_hint}"
        parts.append("")
        parts.append(first_hint)
        for ln in hint_lines[1:]:
            parts.append(ln.rstrip())
    return "\n".join(parts)


def emit_cli_error(
    message: str,
    *,
    path: Path | str | None = None,
    line: int | None = None,
    column: int | None = None,
    hint: str | None = None,
) -> None:
    """Schrijf :func:`format_cli_error` naar stderr."""
    print(
        format_cli_error(
            message, path=path, line=line, column=column, hint=hint
        ),
        file=sys.stderr,
    )


def emit_cli_exception(
    exc: BaseException,
    *,
    path: Path | str | None = None,
    hint: str | None = None,
    prefix: str | None = None,
) -> None:
    """Print exception met optionele locatie-attributen ``line`` / ``column``."""
    message = getattr(exc, "message_nl", None) or str(exc)
    message = str(message).strip() or exc.__class__.__name__
    if prefix:
        message = f"{prefix}{message}"
    line = getattr(exc, "line", None)
    column = getattr(exc, "column", None)
    if column is None:
        column = getattr(exc, "col", None)
    line_i = int(line) if isinstance(line, int) and int(line) > 0 else None
    col_i = int(column) if isinstance(column, int) and int(column) > 0 else None
    source = path if path is not None else getattr(exc, "source", None) or None
    code = getattr(exc, "code", None)
    if code and not str(message).startswith(str(code)):
        # Code op eigen regel bij meerregelige beschrijving (leesbaarder).
        if "\n" in message:
            message = f"{code}\n{message}"
        else:
            message = f"{code}: {message}"
    emit_cli_error(
        message,
        path=source,
        line=line_i,
        column=col_i,
        hint=hint or getattr(exc, "hint_nl", None) or None,
    )


__all__ = [
    "emit_cli_error",
    "emit_cli_exception",
    "format_cli_error",
    "path_label",
]
