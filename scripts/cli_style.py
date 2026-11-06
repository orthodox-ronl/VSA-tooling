"""Terminal-output voor repo-scripts: rollen/kleur (bron repo-scripts.md)."""

from __future__ import annotations

import os
import sys
from typing import Literal

_VERBOSE = False

_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_MAGENTA = "\033[35m"
_CYAN = "\033[36m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"

Role = Literal[
    "section", "ok", "work", "hard", "refuse", "note", "info", "detail"
]

_ROLE_CODES: dict[str, tuple[str, ...]] = {
    "section": (_BOLD, _CYAN),
    "ok": (_GREEN,),
    "work": (_YELLOW,),
    "hard": (_BOLD, _RED),
    "refuse": (_MAGENTA,),
    "note": (_DIM,),
    "info": (),
    "detail": (),
}


def configure_stdio() -> None:
    """Forceer UTF-8 op stdout/stderr (Windows cp1252)."""
    for stream in (sys.stdout, sys.stderr):
        reconf = getattr(stream, "reconfigure", None)
        if not callable(reconf):
            continue
        try:
            reconf(encoding="utf-8", errors="replace")
        except (OSError, ValueError, AttributeError):
            pass


configure_stdio()


def _use_color(stream) -> bool:
    if os.environ.get("NO_COLOR", "").strip():
        return False
    if os.environ.get("FORCE_COLOR", "").strip():
        return True
    try:
        return bool(stream.isatty())
    except Exception:  # noqa: BLE001
        return False


def paint(msg: str, *codes: str, stream=None) -> str:
    target = sys.stdout if stream is None else stream
    if not codes or not _use_color(target):
        return msg
    return f"{''.join(codes)}{msg}{_RESET}"


def set_verbose(enabled: bool) -> None:
    global _VERBOSE
    _VERBOSE = bool(enabled)


def is_verbose() -> bool:
    if _VERBOSE:
        return True
    return os.environ.get("VSA_VERBOSE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def add_verbose_argument(parser) -> None:
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Uitgebreide logging. Standaard uit.",
    )


def section(msg: str) -> None:
    print(paint(msg, _BOLD, _CYAN), flush=True)


def ok(msg: str) -> None:
    print(paint(msg, _GREEN), flush=True)


def work(msg: str) -> None:
    print(paint(msg, _YELLOW), flush=True)


def hard(msg: str) -> None:
    print(paint(msg, _BOLD, _RED), flush=True)


def refuse(msg: str) -> None:
    print(paint(msg, _MAGENTA), flush=True)


def note(msg: str) -> None:
    print(paint(msg, _DIM), flush=True)


def info(msg: str) -> None:
    print(msg, flush=True)


def detail(msg: str) -> None:
    if is_verbose():
        print(msg, flush=True)


def format_count(n: int, label: str, *, width: int = 3) -> str:
    return f"{int(n):>{max(1, width)}}  {label}"


def count(
    n: int,
    label: str,
    *,
    role: Role | str = "work",
    width: int = 3,
) -> None:
    msg = format_count(n, label, width=width)
    codes = _ROLE_CODES.get(role)
    if codes is None:
        raise ValueError(
            f"onbekende count-rol {role!r}; verwacht: "
            + ", ".join(sorted(_ROLE_CODES))
        )
    if role == "detail" and not is_verbose():
        return
    if not codes:
        print(msg, flush=True)
        return
    print(paint(msg, *codes), flush=True)
