"""Uitzonderingslijst: bewust eenlettergrepig ondanks Pyphen."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

EXCEPTIONS_RELATIVE_PATH = "src/vsa/data/monosyllable_exceptions.nl.txt"


def exceptions_file_path() -> Path:
    """Pad naar het databestand naast deze module."""
    return Path(__file__).resolve().parent / "data" / "monosyllable_exceptions.nl.txt"


@lru_cache(maxsize=1)
def load_monosyllable_exceptions() -> frozenset[str]:
    """Laad de uitzonderingslijst (case-fold keys)."""
    path = exceptions_file_path()
    if not path.is_file():
        return frozenset()
    words: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        words.add(line.casefold())
    return frozenset(words)


def is_monosyllable_exception(word: str) -> bool:
    """True als ``word`` (zonder leestekens) op de uitzonderingslijst staat."""
    core = "".join(ch for ch in word if ch.isalpha() or ch in "'’")
    if not core:
        return False
    return core.casefold() in load_monosyllable_exceptions()


def clear_monosyllable_exceptions_cache() -> None:
    """Voor tests: cache legen na tijdelijke lijstwijziging."""
    load_monosyllable_exceptions.cache_clear()
