"""Gedeelde ``--dry-run`` / ``--verbose`` voor same-type schrijfcommando's.

``--dry-run``: noem doelbestanden die anders zouden worden weggeschreven.
``--verbose`` (met dry-run): bounded unified diff per zo'n bestand.
"""

from __future__ import annotations

import difflib
import sys
from dataclasses import dataclass
from pathlib import Path

from .cli_messages import path_label

# Max. diffregels per bestand (inclusief headers) zodat catalogus-runs leesbaar blijven.
DEFAULT_MAX_DIFF_LINES = 80


@dataclass(frozen=True)
class DryRunCounters:
    """Tellers voor een dry-run- of schrijfrun."""

    would_change: int = 0
    unchanged: int = 0
    errors: int = 0

    def plus(
        self,
        *,
        would_change: int = 0,
        unchanged: int = 0,
        errors: int = 0,
    ) -> DryRunCounters:
        return DryRunCounters(
            would_change=self.would_change + would_change,
            unchanged=self.unchanged + unchanged,
            errors=self.errors + errors,
        )


def read_text_if_exists(path: Path) -> str | None:
    """Huidige doelinhoud, of ``None`` als het bestand nog niet bestaat."""
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8-sig")


def content_would_change(old: str | None, new: str) -> bool:
    """True als schrijven de schijfinhoud zou wijzigen (of een nieuw bestand maakt)."""
    if old is None:
        return True
    # Normaliseer newlines voor vergelijking met write_text(..., newline=\"\\n\").
    return old.replace("\r\n", "\n").replace("\r", "\n") != new.replace(
        "\r\n", "\n"
    ).replace("\r", "\n")


def format_bounded_unified_diff(
    old: str | None,
    new: str,
    *,
    from_label: str,
    to_label: str,
    max_lines: int = DEFAULT_MAX_DIFF_LINES,
) -> str:
    """Unified diff; bij te veel regels: afkappen + melding."""
    old_lines = ([] if old is None else old.splitlines(keepends=True))
    new_lines = new.splitlines(keepends=True)
    if old is None:
        from_label = f"{from_label} (nieuw)"
    diff = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=from_label,
            tofile=to_label,
            n=3,
        )
    )
    if not diff:
        return ""
    if len(diff) <= max_lines:
        return "".join(diff)
    head = "".join(diff[:max_lines])
    omitted = len(diff) - max_lines
    return f"{head}… ({omitted} diffregels weggelaten; verhoog niet nodig — bekijk lokaal)\n"


def report_would_write(
    target: Path,
    old: str | None,
    new: str,
    *,
    dry_run: bool,
    verbose: bool = False,
    max_diff_lines: int = DEFAULT_MAX_DIFF_LINES,
    file=None,
) -> bool:
    """Rapporteer één doelbestand. True als inhoud zou wijzigen.

    Bij ``dry_run``: print pad (en optioneel diff); schrijf nooit.
    Zonder ``dry_run``: geen output hier (caller schrijft zelf).
    """
    file = sys.stdout if file is None else file
    changed = content_would_change(old, new)
    if not dry_run:
        return changed
    label = path_label(target)
    if not changed:
        return False
    print(f"would write: {label}", file=file)
    if verbose:
        diff = format_bounded_unified_diff(
            old,
            new,
            from_label=label,
            to_label=label,
            max_lines=max_diff_lines,
        )
        if diff:
            print(diff, end="" if diff.endswith("\n") else "\n", file=file)
    return True


def print_dry_run_summary(
    counters: DryRunCounters,
    *,
    dry_run: bool,
    file=None,
) -> None:
    """Eindsummary voor dry-run (of stille no-op zonder dry-run)."""
    if not dry_run:
        return
    file = sys.stdout if file is None else file
    print(
        f"dry-run: {counters.would_change} zou schrijven, "
        f"{counters.unchanged} ongewijzigd"
        + (
            f", {counters.errors} fout(en)"
            if counters.errors
            else ""
        ),
        file=file,
    )


def write_text_utf8(path: Path, text: str) -> None:
    """Schrijf UTF-8 met LF (zelfde conventie als normalize/transpose)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


__all__ = [
    "DEFAULT_MAX_DIFF_LINES",
    "DryRunCounters",
    "content_would_change",
    "format_bounded_unified_diff",
    "print_dry_run_summary",
    "read_text_if_exists",
    "report_would_write",
    "write_text_utf8",
]
