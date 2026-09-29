from dataclasses import dataclass
from pathlib import Path
import re
import shutil

from .content_assets import CORIA_HTML_SOURCE_SUFFIX, NATIVE_MUSICXML_SUFFIXES

from .block_parser import END_MARKER, notation_fence_kind, parse_markdown_blocks
from .config import VSAConfig
from .markdown_coria import (
    emit_coria_shortcode,
    emit_mxl_download_shortcode,
    resolve_coria_directives,
)
from .markdown_directives import process_directives
from .markdown_include import IncludeError, resolve_includes
from .resolve_catalogus import (
    ResolveCatalogusError,
    has_unresolved_zoek_includes,
    resolve_catalogus_markdown,
)
from .include_vsa import prepare_markdown_block_body
from .svg_renderer import SVGRenderer
from .validation_runner import validate_file
from .markdown_processor import ProcessValidationError

try:
    from .catalogus_bridge import discover_bron_root as _discover_bron_root
except ImportError:  # pragma: no cover - catalogus niet geïnstalleerd

    def _discover_bron_root(content_root=None):  # type: ignore[misc]
        return None


CONTENT_ASSET_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".pdf",
}

# Catalogus-sjablonen/sessies: wel valideren/resolve-catalogus, nog geen Hugo-build.
BUILD_EXCLUDE_DIR_NAMES = frozenset({})


def _discover_markdown_files(input_dir: Path) -> list[Path]:
    files = sorted(
        list(input_dir.rglob("*.md")) + list(input_dir.rglob("*.markdown"))
    )
    return [
        path
        for path in files
        if not BUILD_EXCLUDE_DIR_NAMES.intersection(
            path.relative_to(input_dir).parts
        )
    ]


@dataclass
class MarkdownBuildResult:
    markdown_files: list[str]
    svg_files: list[str]
    static_files: list[str]


def build_markdown_site(
    input_dir,
    output_dir,
    assets_dir,
    assets_url_prefix="/vsa",
    max_line_width=800.0,
    output_mode="img",
    config: VSAConfig | None = None,
    coria_assets_dir=None,
    native_mxl_assets_dir=None,
):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    assets_dir = Path(assets_dir)
    if coria_assets_dir is None:
        coria_assets_dir = assets_dir.parent / "coria"
    else:
        coria_assets_dir = Path(coria_assets_dir)
    coria_assets_dir.mkdir(parents=True, exist_ok=True)
    if native_mxl_assets_dir is None:
        native_mxl_assets_dir = assets_dir.parent / "mxl"
    else:
        native_mxl_assets_dir = Path(native_mxl_assets_dir)
    native_mxl_assets_dir.mkdir(parents=True, exist_ok=True)

    markdown_files = _discover_markdown_files(input_dir)

    all_messages = []

    for markdown_file in markdown_files:
        validation = validate_file(markdown_file, config=config)

        if not validation.ok:
            all_messages.extend(validation.messages)

    if all_messages:
        raise ProcessValidationError(all_messages)

    # The output directory is a build artifact. Start from a clean tree so
    # pages removed from the source cannot survive a later build and leave
    # stale navigation links behind.
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    written_markdown = []
    written_svg = []

    for markdown_file in markdown_files:
        relative = markdown_file.relative_to(input_dir)

        target_markdown = output_dir / relative
        target_markdown.parent.mkdir(parents=True, exist_ok=True)

        rewritten, svg_paths = prepare_markdown_document(
            markdown_file,
            content_root=input_dir,
            assets_dir=assets_dir,
            assets_url_prefix=assets_url_prefix,
            max_line_width=max_line_width,
            output_mode=output_mode,
            bron_root=_discover_bron_root(input_dir),
        )

        target_markdown.write_text(rewritten, encoding="utf-8")

        written_markdown.append(str(target_markdown))
        written_svg.extend(str(path) for path in svg_paths)

    written_static = _copy_content_assets(input_dir, output_dir)
    written_coria = _copy_coria_html_assets(input_dir, coria_assets_dir)
    written_native_mxl = _copy_native_musicxml_assets(input_dir, native_mxl_assets_dir)
    written_static.extend(written_coria)
    written_static.extend(written_native_mxl)

    return MarkdownBuildResult(
        markdown_files=written_markdown,
        svg_files=written_svg,
        static_files=written_static,
    )


def _source_relative(markdown_file: Path, content_root: Path) -> Path:
    try:
        return markdown_file.resolve().relative_to(content_root.resolve())
    except ValueError:
        return Path(markdown_file.name)


def prepare_markdown_document(
    markdown_file: Path,
    *,
    content_root: Path,
    assets_dir: Path,
    assets_url_prefix: str = "/vsa",
    max_line_width: float = 800.0,
    output_mode: str = "img",
    bron_root: Path | None = None,
) -> tuple[str, list[Path]]:
    """Resolve includes/directives and replace VSA-blokken with SVG references.

    Same pipeline as one file in ``build_markdown_site``, without writing
    the rewritten Markdown. Caller is responsible for validation.
    """
    markdown_file = Path(markdown_file)
    content_root = Path(content_root)
    assets_dir = Path(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)

    source = markdown_file.read_text(encoding="utf-8")
    if bron_root is None:
        bron_root = _discover_bron_root(content_root)
    if has_unresolved_zoek_includes(source):
        try:
            source = resolve_catalogus_markdown(
                source,
                source_path=markdown_file,
                content_root=content_root,
                bron_root=bron_root,
            ).text
        except ResolveCatalogusError as exc:
            raise IncludeError(exc.message_nl) from exc
    source = resolve_includes(
        source,
        source_path=markdown_file,
        svg_assets_dir=assets_dir,
        svg_assets_url_prefix=assets_url_prefix,
        content_root=content_root,
        bron_root=bron_root,
    )
    source = resolve_coria_directives(
        source,
        markdown_file,
        content_root=content_root,
    )
    source = process_directives(source)

    rewritten, svg_paths = _rewrite_markdown_file(
        source=source,
        source_path=markdown_file,
        source_relative=_source_relative(markdown_file, content_root),
        assets_dir=assets_dir,
        assets_url_prefix=assets_url_prefix,
        max_line_width=max_line_width,
        output_mode=output_mode,
    )
    return rewritten, svg_paths


def _copy_content_assets(input_dir: Path, output_dir: Path) -> list[str]:
    written_static: list[str] = []

    for source in sorted(input_dir.rglob("*")):
        if not source.is_file():
            continue

        suffix = source.suffix.lower()
        if suffix in {".md", ".markdown"}:
            continue
        if suffix not in CONTENT_ASSET_SUFFIXES:
            continue

        relative = source.relative_to(input_dir)
        target = output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        written_static.append(str(target))

    return written_static


def _copy_coria_html_assets(input_dir: Path, coria_assets_dir: Path) -> list[str]:
    """Copy ``*.coria.html`` siblings from content-source to ``static/coria/``."""
    written: list[str] = []

    for source in sorted(input_dir.rglob(f"*{CORIA_HTML_SOURCE_SUFFIX}")):
        if not source.is_file():
            continue

        relative = source.relative_to(input_dir)
        published = relative.with_name(
            relative.name[: -len(CORIA_HTML_SOURCE_SUFFIX)] + ".html"
        )
        target = coria_assets_dir / published
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        written.append(str(target))

    return written


def _copy_native_musicxml_assets(input_dir: Path, mxl_assets_dir: Path) -> list[str]:
    """Copy native ``.mxl`` / ``.musicxml`` from content-source to ``static/mxl/``."""
    written: list[str] = []

    for source in sorted(input_dir.rglob("*")):
        if not source.is_file():
            continue
        if source.suffix.lower() not in NATIVE_MUSICXML_SUFFIXES:
            continue

        relative = source.relative_to(input_dir)
        target = mxl_assets_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        written.append(str(target))

    return written


def _rewrite_markdown_file(
    source,
    source_path,
    source_relative,
    assets_dir,
    assets_url_prefix,
    max_line_width,
    output_mode,
):
    blocks = parse_markdown_blocks(source)
    lines = source.splitlines()

    result_lines = []
    svg_paths = []

    index = 0
    block_index = 0
    in_code_fence = False
    fence_marker = ""

    while index < len(lines):
        stripped = lines[index].strip()
        fence = _opening_or_closing_fence(stripped)

        if fence:
            if not in_code_fence:
                in_code_fence = True
                fence_marker = fence
            elif _closes_fence(stripped, fence_marker):
                in_code_fence = False
                fence_marker = ""

            result_lines.append(lines[index])
            index += 1
            continue

        kind = None if in_code_fence else notation_fence_kind(stripped)
        if kind is None:
            result_lines.append(lines[index])
            index += 1
            continue

        block_index += 1
        index += 1

        while index < len(lines) and lines[index].strip() != END_MARKER:
            index += 1

        if index >= len(lines):
            break

        end_index = index
        block = blocks[block_index - 1]

        if block.kind == "mvsa":
            replacements, asset_paths = _rewrite_mvsa_block(
                block,
                source_relative=source_relative,
                block_index=block_index,
                assets_dir=assets_dir,
                assets_url_prefix=assets_url_prefix,
            )
            result_lines.extend(replacements)
            svg_paths.extend(asset_paths)
        else:
            replacement, svg_path = _rewrite_vsa_block(
                block,
                source=source,
                source_path=source_path,
                source_relative=source_relative,
                block_index=block_index,
                assets_dir=assets_dir,
                assets_url_prefix=assets_url_prefix,
                max_line_width=max_line_width,
                output_mode=output_mode,
            )
            result_lines.append(replacement)
            svg_paths.append(svg_path)

        index = end_index + 1

    return "\n".join(result_lines) + "\n", svg_paths


def _rewrite_vsa_block(
    block,
    *,
    source,
    source_path,
    source_relative,
    block_index,
    assets_dir,
    assets_url_prefix,
    max_line_width,
    output_mode,
) -> tuple[str, Path]:
    expanded_body, _ = prepare_markdown_block_body(
        block.body,
        markdown_path=source_path,
        markdown_text=source,
    )

    svg_name = _svg_name(source_relative, block_index)
    svg_path = assets_dir / svg_name
    svg_path.parent.mkdir(parents=True, exist_ok=True)

    renderer = SVGRenderer()
    renderer.max_line_width = max_line_width
    svg = renderer.render_document(block.parse_body(expanded_body))
    svg_path.write_text(svg, encoding="utf-8")

    img_src = f"{assets_url_prefix.rstrip('/')}/{svg_name.replace(chr(92), '/')}"
    alt = block.metadata.get("alt", "VSA notatie")
    scale = block.metadata.get("scale")
    natural_width = _svg_natural_width(svg)
    style_attr = _scale_style(scale, natural_width)

    if output_mode == "shortcode":
        px = _scale_px(scale, natural_width)
        scale_param = f' scale="{px}"' if px else ""
        replacement = f'{{{{< vsa src="{img_src}" alt="{alt}"{scale_param} >}}}}'
    else:
        replacement = (
            f'<img class="vsa-notation" '
            f'src="{img_src}" alt="{alt}"{style_attr}>'
        )
    return replacement, svg_path


def _rewrite_mvsa_block(
    block,
    *,
    source_relative,
    block_index,
    assets_dir,
    assets_url_prefix,
) -> tuple[list[str], list[Path]]:
    """Playback-MXL + Coria-/download-shortcodes (mvsa heeft geen SVG-renderer)."""
    from .mvsa_musicxml import export_mvsa_to_musicxml
    from .musicxml_package import write_musicxml_output

    mxl_name = _mxl_name(source_relative, block_index)
    mxl_path = assets_dir / mxl_name
    mxl_path.parent.mkdir(parents=True, exist_ok=True)

    title = block.metadata.get("alt") or Path(mxl_name).stem
    xml = export_mvsa_to_musicxml(
        block.body,
        title=title,
        layout="playback",
    )
    write_musicxml_output(mxl_path, xml)

    public = f"{assets_url_prefix.rstrip('/')}/{mxl_name.replace(chr(92), '/')}"
    label = block.metadata.get("label") or "Oefenen in Coria"
    download_label = block.metadata.get("mxl-label") or "Download MusicXML"
    return [
        emit_coria_shortcode(public, label),
        emit_mxl_download_shortcode(public, download_label),
    ], [mxl_path]


def _svg_name(source_relative, block_index):
    without_suffix = source_relative.with_suffix("")
    stem = "-".join(without_suffix.parts)
    stem = _safe_name(stem)

    return f"{stem}-block-{block_index}.svg"


def _mxl_name(source_relative, block_index):
    without_suffix = source_relative.with_suffix("")
    stem = "-".join(without_suffix.parts)
    stem = _safe_name(stem)
    return f"{stem}-block-{block_index}.mxl"


def _safe_name(value):
    value = value.lower()
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    value = value.strip("-")

    return value or "vsa"


def _opening_or_closing_fence(stripped: str):
    if stripped.startswith("```"):
        return "```"

    if stripped.startswith("~~~"):
        return "~~~"

    return ""


def _closes_fence(stripped: str, fence_marker: str):
    return stripped.startswith(fence_marker)


_SVG_WIDTH_RE = re.compile(r"<svg\b[^>]*\bwidth=\"(\d+(?:\.\d+)?)\"")


def _svg_natural_width(svg_text: str) -> float | None:
    """Extract the natural pixel width from a rendered SVG string."""
    m = _SVG_WIDTH_RE.search(svg_text)
    return float(m.group(1)) if m else None


def _scale_px(scale: str | None, natural_width: float | None) -> str | None:
    """Convert a percentage scale to an absolute pixel width string (e.g. '680px').

    Returns None when scale is absent, and falls back to the original value
    (e.g. '85%') when natural_width is unavailable.
    """
    if not scale:
        return None
    if natural_width is not None:
        try:
            pct = float(scale.rstrip("%"))
            return f"{round(natural_width * pct / 100)}px"
        except ValueError:
            pass
    return scale


def _scale_style(scale: str | None, natural_width: float | None) -> str:
    """Return an inline style attribute string, or empty string when no scale."""
    value = _scale_px(scale, natural_width)
    return f' style="width: {value}"' if value else ""
