"""
Maps VSA ELM (Enkelvoudige Lengte-Modifier) strings to MusicXML
:class:`~vsa.music.Duration` objects.

The default mapping is specified in VSA-spec §8.2.5::

    ELM  → MusicXML duration
    ~    → kwartnoot  (quarter)
    -    → kwartnoot  (quarter)
    -.   → gepunteerde kwartnoot (dotted quarter)
    ~.   → gepunteerde kwartnoot (dotted quarter)
    ~..  → dubbelgepunteerde kwart (S13-pack)
    _    → halve noot (half)
    _.   → gepunteerde halve noot (dotted half)
    _..  → dubbelgepunteerde halve (S13-pack)
    __   → hele noot  (whole)
    __.  → gepunteerde hele noot (dotted whole; Score-IR/S13-eindvorm)
    __.. → dubbelgepunteerde hele noot (double-dotted whole; S13-pack ≤28)
    .    → achtste noot (eighth)
    ..   → zestiende noot (16th)

Additional ``duration-model`` values may be registered in the future.

``__.`` / ``__..`` / ``~..`` / ``_..`` zijn vooral voor Score-IR ↔ from-ir
(S13 compacte same-pitch); ze horen niet in gewone ``.mvsa``-invoer.
"""

from __future__ import annotations

from .music import Duration


# Default mapping: ELM string → Duration
_DEFAULT_MODEL: dict[str, Duration] = {
    "~":  Duration(note_type="quarter", dots=0),
    "-":  Duration(note_type="quarter", dots=0),
    "-.": Duration(note_type="quarter", dots=1),
    "~.": Duration(note_type="quarter", dots=1),
    "~..": Duration(note_type="quarter", dots=2),
    "_":  Duration(note_type="half",    dots=0),
    "_.": Duration(note_type="half",    dots=1),
    "_..": Duration(note_type="half",   dots=2),
    "__": Duration(note_type="whole",   dots=0),
    "__.": Duration(note_type="whole",  dots=1),
    "__..": Duration(note_type="whole", dots=2),
    ".":  Duration(note_type="eighth",  dots=0),
    "..": Duration(note_type="16th",    dots=0),
}

_MODELS: dict[str, dict[str, Duration]] = {
    "default": _DEFAULT_MODEL,
}


class UnknownDurationModel(ValueError):
    pass


class UnknownELM(ValueError):
    pass


def elm_to_duration(elm: str, model: str = "default") -> Duration:
    """Return the :class:`~vsa.music.Duration` for a given ELM string.

    :param elm: The ELM string, e.g. ``"_"``, ``"-."``, ``"_."``.
    :param model: The duration model name (default: ``"default"``).
    :raises UnknownDurationModel: If the model name is not registered.
    :raises UnknownELM: If the ELM string has no mapping in the model.
    """
    try:
        mapping = _MODELS[model]
    except KeyError:
        raise UnknownDurationModel(
            f"Onbekend duration-model: '{model}'. "
            f"Beschikbare modellen: {sorted(_MODELS)}"
        )

    try:
        return mapping[elm]
    except KeyError:
        raise UnknownELM(
            f"Onbekende ELM '{elm}' in model '{model}'. "
            f"Geldige waarden: {sorted(mapping)}"
        )
