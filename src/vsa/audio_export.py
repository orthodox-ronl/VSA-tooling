"""Export playback MusicXML (or .vsa / .mvsa / .mscz) to audio via MuseScore.

Preview-luisteren: één afspeelbaar artefact (default ``.mp3``). Geen speler,
geen stemkeuze — de consumer-site maakt de knop.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .musescore_cli import (
    MuseScoreConvertError,
    MuseScoreNotFoundError,
    convert_with_musescore,
)

AUDIO_FORMATS = ("mp3", "ogg", "wav")
DEFAULT_AUDIO_FORMAT = "mp3"

_MUSICXML_SUFFIXES = {".mxl", ".musicxml", ".xml"}
_SOURCE_SUFFIXES = _MUSICXML_SUFFIXES | {".vsa", ".mvsa", ".mscz"}


class AudioExportError(RuntimeError):
    """Raised when audio export fails (missing MuseScore, bad input, …)."""


def normalize_audio_format(format_name: str | None) -> str:
    """Return a canonical audio format name (``mp3`` / ``ogg`` / ``wav``)."""
    if format_name is None or str(format_name).strip() == "":
        return DEFAULT_AUDIO_FORMAT
    value = str(format_name).strip().lower().lstrip(".")
    if value not in AUDIO_FORMATS:
        raise AudioExportError(
            f"Onbekend audioformaat: {format_name!r}. "
            f"Gebruik: {', '.join(AUDIO_FORMATS)}."
        )
    return value


def resolve_audio_output_path(
    out: Path,
    *,
    format_name: str | None = None,
) -> Path:
    """Ensure ``out`` has a recognized audio suffix (default ``.mp3``)."""
    out = Path(out)
    fmt = normalize_audio_format(format_name)
    suffix = out.suffix.lower().lstrip(".")
    if suffix in AUDIO_FORMATS:
        return out
    return out.with_suffix(f".{fmt}")


def export_musicxml_to_audio(
    source: Path,
    out: Path,
    *,
    musescore: Path | None = None,
    format_name: str | None = None,
) -> Path:
    """Convert an existing ``.mxl`` / ``.musicxml`` to audio via MuseScore."""
    source = Path(source)
    out = resolve_audio_output_path(out, format_name=format_name)
    if not source.is_file():
        raise AudioExportError(f"Bestand niet gevonden: {source}")
    if source.suffix.lower() not in _MUSICXML_SUFFIXES:
        raise AudioExportError(
            f"Audio-export verwacht .mxl/.musicxml, kreeg: {source.name}"
        )
    try:
        convert_with_musescore(source, out, musescore=musescore)
    except (MuseScoreNotFoundError, MuseScoreConvertError) as exc:
        raise AudioExportError(str(exc)) from exc
    return out


def export_to_audio(
    path: Path,
    out: Path,
    *,
    format_name: str | None = None,
    musescore: Path | None = None,
    section_id: str | None = None,
    keep_mxl: Path | None = None,
) -> Path:
    """Export ``.mxl`` / ``.vsa`` / ``.mvsa`` / ``.mscz`` to audio.

    Non-MusicXML sources are converted to playback ``.mxl`` first (temp, or
    ``keep_mxl`` when set). ``.mscz`` is a fallback via MuseScore → ``.mxl``.
    """
    path = Path(path)
    out = resolve_audio_output_path(out, format_name=format_name)
    if not path.is_file():
        raise AudioExportError(f"Bestand niet gevonden: {path}")

    suffix = path.suffix.lower()
    if suffix not in _SOURCE_SUFFIXES:
        raise AudioExportError(
            f"Audio-export verwacht .mxl/.musicxml/.vsa/.mvsa/.mscz, "
            f"kreeg: {path.name}"
        )

    if suffix in _MUSICXML_SUFFIXES:
        if section_id is not None or keep_mxl is not None:
            raise AudioExportError(
                "Audio-export: --section/--keep-mxl gelden niet bij .mxl/.musicxml"
            )
        return export_musicxml_to_audio(
            path, out, musescore=musescore, format_name=format_name
        )

    tmp_mxl: Path | None = None
    if keep_mxl is not None:
        mxl_path = Path(keep_mxl)
        if mxl_path.suffix.lower() not in _MUSICXML_SUFFIXES:
            mxl_path = mxl_path.with_suffix(".mxl")
        mxl_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        fd, name = tempfile.mkstemp(suffix=".mxl", prefix="vsa-audio-")
        os.close(fd)
        tmp_mxl = Path(name)
        mxl_path = tmp_mxl

    try:
        _write_playback_mxl(
            path,
            mxl_path,
            musescore=musescore,
            section_id=section_id,
        )
        return export_musicxml_to_audio(
            mxl_path, out, musescore=musescore, format_name=format_name
        )
    finally:
        if tmp_mxl is not None:
            tmp_mxl.unlink(missing_ok=True)


def _write_playback_mxl(
    path: Path,
    mxl_path: Path,
    *,
    musescore: Path | None = None,
    section_id: str | None = None,
) -> None:
    suffix = path.suffix.lower()
    if suffix == ".vsa":
        if section_id is not None:
            raise AudioExportError(
                "Audio-export: --section geldt alleen bij .mvsa"
            )
        _export_vsa_to_mxl(path, mxl_path)
        return
    if suffix == ".mvsa":
        from .mvsa_musicxml import MvsaExportError, export_mvsa_path
        from .mvsa_validate import MvsaValidationError

        try:
            export_mvsa_path(
                path, mxl_path, section_id=section_id, layout="playback"
            )
        except (MvsaValidationError, MvsaExportError):
            raise
        return
    if suffix == ".mscz":
        if section_id is not None:
            raise AudioExportError(
                "Audio-export: --section geldt alleen bij .mvsa"
            )
        try:
            convert_with_musescore(path, mxl_path, musescore=musescore)
        except (MuseScoreNotFoundError, MuseScoreConvertError) as exc:
            raise AudioExportError(str(exc)) from exc
        return
    raise AudioExportError(f"Onverwacht bronformaat: {path.name}")


def _export_vsa_to_mxl(path: Path, mxl_path: Path) -> None:
    from .block_parser import DEFAULT_METADATA
    from .include_vsa import IncludeVsaError, prepare_vsa_body
    from .markdown_newline_policy import preserve_vsa_source_newlines
    from .musicxml_package import write_musicxml_output
    from .musicxml_renderer import MusicXMLExportError, MusicXMLRenderer
    from .parser import Parser
    from .yaml_frontmatter import frontmatter_to_block_metadata, parse_vsa_frontmatter

    text = path.read_text(encoding="utf-8")
    frontmatter, _vsa_body = parse_vsa_frontmatter(text)
    try:
        vsa_body, _ = prepare_vsa_body(text, path)
    except IncludeVsaError as exc:
        raise AudioExportError(exc.message_nl) from exc
    fm_meta = frontmatter_to_block_metadata(frontmatter)
    metadata = dict(DEFAULT_METADATA)
    metadata.update(fm_meta)
    explicit_keys = set(fm_meta.keys())
    document = Parser(preserve_vsa_source_newlines(vsa_body)).parse()
    try:
        renderer = MusicXMLRenderer(metadata=metadata, explicit_keys=explicit_keys)
        xml_str = renderer.render(document)
    except MusicXMLExportError as exc:
        raise AudioExportError(f"fout bij MusicXML-export: {exc}") from exc
    write_musicxml_output(mxl_path, xml_str)
