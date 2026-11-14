"""Canonieke zing-deling: lemma → hyphenvorm (soft ``-`` / hard ``=``).

De org-lijst hoort in de **bibliotheek**-repo (of een andere content-repo).
Pad via CLI ``--syllable-dictionary``, ``vsa.toml`` ``[syllabificatie]``,
omgevingsvariabele ``VSA_SYLLABLE_DICTIONARY``, of auto-detectie naast de
werkmap / sibling ``bibliotheek``. Zonder pad: lege mapping (geen stille
package-lijst meer).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from .syllabify import HARD_HYPHEN, strip_soft_hyphens

# Historische relatieve naam (docs/tests); runtime gebruikt dictionary_file_path().
DICTIONARY_RELATIVE_PATH = "data/syllable_dictionary.nl.txt"
ENV_VAR = "VSA_SYLLABLE_DICTIONARY"

_active_path: Path | None = None


def packaged_dictionary_file_path() -> Path:
    """Optioneel package-bestand (leeg/stub); niet de org-canon."""
    return Path(__file__).resolve().parent / "data" / "syllable_dictionary.nl.txt"


def set_syllable_dictionary_path(path: Path | str | None) -> None:
    """Zet het actieve dictionary-pad (None = opnieuw resolven bij load)."""
    global _active_path
    if path is None:
        _active_path = None
    else:
        _active_path = Path(path).expanduser().resolve()
    clear_syllable_dictionary_cache()


def dictionary_file_path() -> Path:
    """Pad naar het actieve databestand (bestaand of schrijfdoel)."""
    if _active_path is not None:
        return _active_path
    resolved = resolve_syllable_dictionary_path()
    if resolved is not None:
        return resolved
    return packaged_dictionary_file_path()


def dictionary_path_label() -> str:
    """Korte padtekst voor hints/meldingen."""
    path = dictionary_file_path()
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def resolve_syllable_dictionary_path(
    *,
    cli_path: str | Path | None = None,
    config_value: str | None = None,
    config_dir: Path | None = None,
    environ: dict[str, str] | None = None,
) -> Path | None:
    """Bepaal dictionary-pad: CLI → config → env → auto-detect.

    Retourneert ``None`` als niets bruikbaars gevonden is.
    """
    if cli_path is not None and str(cli_path).strip():
        return Path(cli_path).expanduser().resolve()

    if config_value is not None and str(config_value).strip():
        raw = Path(str(config_value).strip()).expanduser()
        if not raw.is_absolute() and config_dir is not None:
            raw = Path(config_dir) / raw
        return raw.resolve()

    env = environ if environ is not None else os.environ
    env_val = env.get(ENV_VAR, "").strip()
    if env_val:
        return Path(env_val).expanduser().resolve()

    return discover_syllable_dictionary_path()


def discover_syllable_dictionary_path() -> Path | None:
    """Zoek ``data/syllable_dictionary.nl.txt`` in cwd of sibling bibliotheek."""
    cwd = Path.cwd()
    package_root = Path(__file__).resolve().parents[2]  # …/VSA-tooling
    candidates = [
        cwd / "data" / "syllable_dictionary.nl.txt",
        cwd / "bibliotheek" / "data" / "syllable_dictionary.nl.txt",
        cwd.parent / "bibliotheek" / "data" / "syllable_dictionary.nl.txt",
        package_root.parent / "bibliotheek" / "data" / "syllable_dictionary.nl.txt",
    ]
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file() and _file_has_entries(resolved):
            return resolved
    return None


def apply_syllable_dictionary_from_config(
    *,
    cli_path: str | Path | None = None,
    config_value: str | None = None,
    config_dir: Path | None = None,
) -> Path | None:
    """Resolve + activeer; retourneer het gekozen pad of ``None``."""
    path = resolve_syllable_dictionary_path(
        cli_path=cli_path,
        config_value=config_value,
        config_dir=config_dir,
    )
    set_syllable_dictionary_path(path)
    return path


def syllable_lemma(word: str) -> str:
    """Lemma voor matching: geen soft ``-``, geen hard ``=``, case-fold."""
    if not word:
        return ""
    core = strip_soft_hyphens(word).replace(HARD_HYPHEN, "")
    return core.casefold()


@lru_cache(maxsize=1)
def load_syllable_dictionary() -> dict[str, str]:
    """Laad lemma → canonieke hyphenvorm.

    Lege regels en ``#``-commentaar worden overgeslagen. Dubbele lemma's
    met verschillende vormen zijn een fout in het databestand.
    """
    path = dictionary_file_path()
    if not path.is_file():
        return {}
    mapping: dict[str, str] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        form = line.casefold()
        key = syllable_lemma(form)
        if not key:
            continue
        existing = mapping.get(key)
        if existing is not None and existing != form:
            raise ValueError(
                f"{path.name}:{lineno}: lemma {key!r} heeft twee vormen: "
                f"{existing!r} en {form!r}"
            )
        mapping[key] = form
    return mapping


def canonical_syllable_form(word: str) -> str | None:
    """Canonieke hyphenvorm voor ``word``, of ``None`` als onbekend."""
    key = syllable_lemma(word)
    if not key:
        return None
    return load_syllable_dictionary().get(key)


def clear_syllable_dictionary_cache() -> None:
    """Voor tests: cache legen."""
    clear = getattr(load_syllable_dictionary, "cache_clear", None)
    if callable(clear):
        clear()


def _file_has_entries(path: Path) -> bool:
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line and not line.startswith("#"):
                return True
    except OSError:
        return False
    return False
