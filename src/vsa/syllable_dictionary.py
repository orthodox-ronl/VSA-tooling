"""Canonieke zing-deling: lemma → hyphenvorm (soft ``-`` / hard ``=``).

De org-lijst hoort in de **bibliotheek**-repo (of een andere content-repo).
Twee talen: ``nl`` (Latijnse lyrics) en ``ksl`` (Cyrillische / kerkslavische
lyrics). Default CLI-modus ``auto``: per bron Cyrillisch in lyrics → ``ksl``,
anders ``nl``. Pad via CLI ``--syllable-dictionary``, ``vsa.toml``
``[syllabificatie]``, omgevingsvariabele, of auto-detectie naast de
werkmap / sibling ``bibliotheek``. Zonder pad: lege mapping (package-stub).
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

from .syllabify import HARD_HYPHEN, strip_soft_hyphens

LYRICS_LANGS = ("nl", "ksl")
LYRICS_LANG_MODES = ("auto", "nl", "ksl")
DEFAULT_LYRICS_LANG_MODE = "auto"
# Concrete fallback wanneer ``auto`` geen Cyrillisch ziet.
DEFAULT_LYRICS_LANG = "nl"

# Historische relatieve naam (docs/tests); runtime gebruikt dictionary_file_path().
DICTIONARY_RELATIVE_PATH = "data/syllable_dictionary.nl.txt"
ENV_VAR = "VSA_SYLLABLE_DICTIONARY"
ENV_VAR_KSL = "VSA_SYLLABLE_DICTIONARY_KSL"

_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")

_active_path: Path | None = None
_active_mode: str = DEFAULT_LYRICS_LANG_MODE
_active_lang: str = DEFAULT_LYRICS_LANG
_resolution_cli_path: str | Path | None = None
_resolution_config_value: str | None = None
_resolution_config_dir: Path | None = None


def dictionary_basename(lang: str | None = None) -> str:
    """Bestandsnaam ``syllable_dictionary.<lang>.txt``."""
    code = normalize_lyrics_lang(lang)
    return f"syllable_dictionary.{code}.txt"


def normalize_lyrics_lang_mode(lang: str | None) -> str:
    """Normalizeer naar ``auto``, ``nl`` of ``ksl``."""
    if lang is None or str(lang).strip() == "":
        return DEFAULT_LYRICS_LANG_MODE
    value = str(lang).strip().lower()
    if value not in LYRICS_LANG_MODES:
        raise ValueError(
            f"Onbekende lyrics-taal-modus: {lang!r}. "
            f"Gebruik: {', '.join(LYRICS_LANG_MODES)}."
        )
    return value


def normalize_lyrics_lang(lang: str | None) -> str:
    """Normalizeer naar concrete taal ``nl`` of ``ksl`` (geen ``auto``)."""
    if lang is None or str(lang).strip() == "":
        return DEFAULT_LYRICS_LANG
    value = str(lang).strip().lower()
    if value == "auto":
        return DEFAULT_LYRICS_LANG
    if value not in LYRICS_LANGS:
        raise ValueError(
            f"Onbekende lyrics-taal: {lang!r}. Gebruik: {', '.join(LYRICS_LANGS)}."
        )
    return value


def get_lyrics_lang_mode() -> str:
    """Actieve modus: ``auto``, ``nl`` of ``ksl``."""
    return _active_mode


def get_lyrics_lang() -> str:
    """Laatst geactiveerde concrete taal (``nl`` / ``ksl``)."""
    return _active_lang


def set_lyrics_lang(lang: str | None) -> None:
    """Zet modus (``auto``/``nl``/``ksl``); concrete talen activeren meteen het pad."""
    set_lyrics_lang_mode(lang)


def set_lyrics_lang_mode(lang: str | None) -> None:
    """Zet lyrics-modus (``auto``/``nl``/``ksl``); wist het pad niet.

    Padresolutie gebeurt in ``apply_syllable_dictionary_from_config``,
    ``activate_concrete_lyrics_lang`` of ``ensure_lyrics_lang_for_cores``.
    """
    global _active_mode, _active_lang
    mode = normalize_lyrics_lang_mode(lang)
    _active_mode = mode
    if mode in LYRICS_LANGS:
        _active_lang = mode
    clear_syllable_dictionary_cache()


def detect_lyrics_lang_from_cores(cores: list[str] | tuple[str, ...]) -> str:
    """``ksl`` als minstens één kern Cyrillisch bevat, anders ``nl``."""
    for core in cores:
        if core and _CYRILLIC_RE.search(core):
            return "ksl"
    return DEFAULT_LYRICS_LANG


def detect_lyrics_lang_from_text(text: str) -> str:
    """``ksl`` bij Cyrillisch in de tekst, anders ``nl``."""
    if text and _CYRILLIC_RE.search(text):
        return "ksl"
    return DEFAULT_LYRICS_LANG


def activate_concrete_lyrics_lang(lang: str | None) -> Path | None:
    """Zet concrete ``nl``/``ksl`` en resolve het dictionary-pad."""
    global _active_lang
    code = normalize_lyrics_lang(lang)
    _active_lang = code
    path = resolve_syllable_dictionary_path(
        cli_path=_resolution_cli_path,
        config_value=_resolution_config_value,
        config_dir=_resolution_config_dir,
        lang=code,
    )
    set_syllable_dictionary_path(path)
    return path


def ensure_lyrics_lang_for_cores(cores: list[str] | tuple[str, ...]) -> str:
    """Activeer concrete taal: bij ``auto`` op basis van de kernen.

    Bij expliciet ``nl``/``ksl`` blijft een al gezet dictionary-pad staan
    (handig voor tests/fixtures); alleen resolven als er nog geen pad is.
    """
    global _active_lang
    mode = _active_mode
    if mode == "auto":
        lang = detect_lyrics_lang_from_cores(cores)
        activate_concrete_lyrics_lang(lang)
        return lang
    _active_lang = mode
    if _active_path is None:
        activate_concrete_lyrics_lang(mode)
    return mode


def prepare_lyrics_lang_for_source(text: str) -> str:
    """Activeer concrete taal vóór syllabify/validate op één brontekst."""
    global _active_lang
    mode = _active_mode
    if mode == "auto":
        lang = detect_lyrics_lang_from_text(text)
        activate_concrete_lyrics_lang(lang)
        return lang
    _active_lang = mode
    if _active_path is None:
        activate_concrete_lyrics_lang(mode)
    return mode


def core_matches_lyrics_lang(core: str, lang: str | None = None) -> bool:
    """Of een lyric-kern bij de gekozen taal hoort (schrift-heuristiek).

    ``ksl``: bevat Cyrillisch. ``nl``: geen Cyrillisch (Latijn e.d.).
    """
    code = normalize_lyrics_lang(lang if lang is not None else _active_lang)
    has_cyr = bool(_CYRILLIC_RE.search(core or ""))
    if code == "ksl":
        return has_cyr
    return not has_cyr


def packaged_dictionary_file_path(lang: str | None = None) -> Path:
    """Optioneel package-bestand (stub); niet de org-canon."""
    return (
        Path(__file__).resolve().parent
        / "data"
        / dictionary_basename(lang)
    )


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
    resolved = resolve_syllable_dictionary_path(lang=_active_lang)
    if resolved is not None:
        return resolved
    return packaged_dictionary_file_path(_active_lang)


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
    lang: str | None = None,
) -> Path | None:
    """Bepaal dictionary-pad: CLI → config → env → auto-detect.

    Retourneert ``None`` als niets bruikbaars gevonden is.
    Expliciet ``cli_path`` wint ongeacht ``lang``.
    """
    code = normalize_lyrics_lang(lang if lang is not None else _active_lang)

    if cli_path is not None and str(cli_path).strip():
        return Path(cli_path).expanduser().resolve()

    if config_value is not None and str(config_value).strip():
        # Config-dictionary is historisch de NL-lijst; bij ksl negeren
        # tenzij het pad al op .ksl.txt eindigt.
        raw = Path(str(config_value).strip()).expanduser()
        if not raw.is_absolute() and config_dir is not None:
            raw = Path(config_dir) / raw
        resolved_cfg = raw.resolve()
        if code == "nl" or resolved_cfg.name.endswith(".ksl.txt"):
            return resolved_cfg

    env = environ if environ is not None else os.environ
    env_key = ENV_VAR_KSL if code == "ksl" else ENV_VAR
    env_val = env.get(env_key, "").strip()
    if env_val:
        return Path(env_val).expanduser().resolve()
    # Fallback: algemene env alleen voor nl.
    if code == "nl":
        env_val = env.get(ENV_VAR, "").strip()
        if env_val:
            return Path(env_val).expanduser().resolve()

    return discover_syllable_dictionary_path(lang=code)


def discover_syllable_dictionary_path(
    lang: str | None = None,
) -> Path | None:
    """Zoek ``data/syllable_dictionary.<lang>.txt`` in cwd of sibling bibliotheek.

    Voor ``nl``: alleen bestanden mét entries (zoals voorheen).
    Voor ``ksl``: ook een leeg bestand (schrijfdoel / initieel leeg).
    """
    code = normalize_lyrics_lang(lang if lang is not None else _active_lang)
    name = dictionary_basename(code)
    cwd = Path.cwd()
    package_root = Path(__file__).resolve().parents[2]  # …/VSA-tooling
    candidates = [
        cwd / "data" / name,
        cwd / "bibliotheek" / "data" / name,
        cwd.parent / "bibliotheek" / "data" / name,
        package_root.parent / "bibliotheek" / "data" / name,
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
        if not resolved.is_file():
            continue
        if code == "ksl" or _file_has_entries(resolved):
            return resolved
    return None


def apply_syllable_dictionary_from_config(
    *,
    cli_path: str | Path | None = None,
    config_value: str | None = None,
    config_dir: Path | None = None,
    lang: str | None = None,
) -> Path | None:
    """Bewaar resolve-context + zet modus; bij ``nl``/``ksl`` meteen pad.

    Bij modus ``auto`` nog geen pad: dat volgt per bron via
    ``ensure_lyrics_lang_for_cores`` / ``prepare_lyrics_lang_for_source``.
    """
    global _resolution_cli_path, _resolution_config_value, _resolution_config_dir
    _resolution_cli_path = cli_path
    _resolution_config_value = config_value
    _resolution_config_dir = config_dir
    mode = normalize_lyrics_lang_mode(lang)
    set_lyrics_lang_mode(mode)
    if mode == "auto":
        set_syllable_dictionary_path(None)
        return None
    return activate_concrete_lyrics_lang(mode)


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
