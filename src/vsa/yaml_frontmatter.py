"""
Parses optional YAML frontmatter from .vsa files.

A .vsa file may begin with a YAML block delimited by ``---``:

    ---
    do: F4
    mode: major
    tempo: 132
    partituur:
      title: Tropaar van de zondag, toon 1
      composer: Traditioneel
    taal: nl
    bron:
      uitgangspunt: Liturgikon, p.58
    ---
    [:] ...

Playback keys may also appear under ``muziek:`` (legacy) or ``afspelen:``
(future). ``bron.uitgangspunt`` maps to MusicXML ``<source>`` / MuseScore
meta ``source``. Legacy ``identificatie:`` remains readable for older files.

Files without a ``---`` delimiter are returned unchanged.
"""

from __future__ import annotations

_DELIMITER = "---"


def parse_vsa_frontmatter(text: str) -> tuple[dict, str]:
    """Strip and parse optional YAML frontmatter from VSA source text.

    Returns ``(metadata_dict, vsa_body)`` where ``metadata_dict`` is empty
    when no valid frontmatter is present.
    """
    meta, body, _offset = parse_vsa_frontmatter_with_body_offset(text)
    return meta, body


def parse_vsa_frontmatter_with_body_offset(text: str) -> tuple[dict, str, int]:
    """Zoals ``parse_vsa_frontmatter``, plus start-offset van de body in ``text``."""
    if not text.startswith(_DELIMITER):
        return {}, text, 0

    # Find the closing delimiter on its own line
    after_open = text[len(_DELIMITER) :]
    close_idx = after_open.find("\n" + _DELIMITER)
    if close_idx == -1:
        return {}, text, 0

    yaml_text = after_open[:close_idx].strip()
    # ``close_idx`` wijst naar de ``\\n`` vóór de sluitende ``---``.
    close_at = len(_DELIMITER) + close_idx
    body_from = close_at + 1 + len(_DELIMITER)
    rest = text[body_from:]
    body = rest.lstrip("\n")
    body_offset = body_from + (len(rest) - len(body))

    try:
        import yaml  # optional; only needed for .vsa frontmatter

        data = yaml.safe_load(yaml_text) or {}
    except Exception:
        return {}, text, 0

    if not isinstance(data, dict):
        return {}, text, 0

    return data, body, body_offset


def _promote_playback(frontmatter: dict, result: dict[str, str]) -> None:
    """Zet do/mode/tempo in het platte block-metadata dict."""
    for section in ("muziek", "afspelen"):
        block = frontmatter.get(section, {})
        if isinstance(block, dict):
            for k, v in block.items():
                if v is None or v == "":
                    continue
                result[str(k)] = str(v)
    for k in ("do", "mode", "tempo"):
        if k in frontmatter and frontmatter[k] is not None and frontmatter[k] != "":
            result[k] = str(frontmatter[k])


def frontmatter_to_block_metadata(frontmatter: dict) -> dict[str, str]:
    """Flatten YAML frontmatter into the flat ``key=value`` dict format used
    by :class:`~vsa.block_parser.MarkdownBlock`.

    Playback keys (``do`` / ``mode`` / ``tempo``) are promoted from top-level,
    ``muziek:``, or ``afspelen:``.

    Nested sections are stored as ``section.key`` (e.g. ``bron.uitgangspunt``,
    ``partituur.title``, legacy ``identificatie.title``).
    """
    result: dict[str, str] = {}
    _promote_playback(frontmatter, result)

    skip_sections = {"muziek", "afspelen", "do", "mode", "tempo"}
    for section, values in frontmatter.items():
        if section in skip_sections:
            continue
        if isinstance(values, dict):
            for k, v in values.items():
                if v is None or v == "":
                    continue
                result[f"{section}.{k}"] = str(v)
        elif values is None or values == "":
            continue
        else:
            result[str(section)] = str(values)

    return result


def bron_uitgangspunt_from_frontmatter(frontmatter: dict) -> str | None:
    """Return ``bron.uitgangspunt`` if set (non-empty string).

    Falls back to legacy ``identificatie.bron``.
    """
    bron = frontmatter.get("bron")
    if isinstance(bron, dict):
        val = bron.get("uitgangspunt")
        if val is not None and str(val).strip():
            return str(val).strip()
    ident = frontmatter.get("identificatie")
    if isinstance(ident, dict):
        val = ident.get("bron")
        if val is not None and str(val).strip():
            return str(val).strip()
    return None
