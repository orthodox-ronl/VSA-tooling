"""``.vsa`` → Coria/playback MusicXML (optioneel syllabify + finalize)."""

from __future__ import annotations

from pathlib import Path

from .block_parser import DEFAULT_METADATA
from .include_vsa import IncludeVsaError, prepare_vsa_body
from .markdown_newline_policy import preserve_vsa_source_newlines
from .musicxml_coria_timing import finalize_coria_musicxml
from .musicxml_package import write_musicxml_output
from .musicxml_renderer import (
    MUSICXML_PROFILE_PLAYBACK,
    MusicXMLExportError,
    MusicXMLRenderer,
)
from .parser import Parser
from .syllabify import syllabify_vsa_source
from .yaml_frontmatter import frontmatter_to_block_metadata, parse_vsa_frontmatter


def export_vsa_to_musicxml(
    path: Path,
    output_path: Path,
    *,
    cli_overrides: dict[str, str] | None = None,
    syllabify: bool = False,
) -> None:
    """Schrijf MusicXML/MXL uit *path*.

    Bij *syllabify*: tijdelijke lettergreepstreepjes voor Coria; canonieke
    bron blijft ongewijzigd. Bij playback-profiel: ``finalize_coria_musicxml``
    (sanitize + accidentals, geen DOCTYPE).
    """
    path = Path(path)
    output_path = Path(output_path)
    overrides = dict(cli_overrides or {})

    text = path.read_text(encoding="utf-8")
    if syllabify:
        text = syllabify_vsa_source(text).text

    frontmatter, _ = parse_vsa_frontmatter(text)
    try:
        body, _ = prepare_vsa_body(text, path)
    except IncludeVsaError:
        raise

    fm_meta = frontmatter_to_block_metadata(frontmatter)
    metadata = dict(DEFAULT_METADATA)
    metadata.update(fm_meta)
    metadata.update(overrides)
    explicit_keys = set(fm_meta.keys()) | set(overrides.keys())

    document = Parser(preserve_vsa_source_newlines(body)).parse()
    renderer = MusicXMLRenderer(metadata=metadata, explicit_keys=explicit_keys)
    xml_str = renderer.render(document)

    profile = metadata.get("musicxml-profile", MUSICXML_PROFILE_PLAYBACK)
    if profile == MUSICXML_PROFILE_PLAYBACK:
        # Zelfde nabewerking als bibliotheek ``process_existing_mxl``:
        # sanitize + accidentals; timing niet (VSA-renderer heeft geen MVSA-[PAUZE]).
        xml_str = finalize_coria_musicxml(xml_str, apply_timing=False)

    write_musicxml_output(output_path, xml_str)


__all__ = ["export_vsa_to_musicxml", "IncludeVsaError", "MusicXMLExportError"]
