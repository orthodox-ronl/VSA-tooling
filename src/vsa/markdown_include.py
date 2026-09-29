import re
import shutil
from pathlib import Path

from .content_assets import (
    CORIA_MXL_SOURCE_SUFFIXES,
    ContentAssetError,
    DEFAULT_CORIA_HTML_URL_PREFIX,
    DEFAULT_MXL_URL_PREFIX,
    DEFAULT_NATIVE_MXL_URL_PREFIX,
    resolve_asset,
)
from .markdown_coria import (
    DEFAULT_MXL_DOWNLOAD_LABEL,
    CoriaDirectiveError,
    emit_coria_shortcode,
    emit_mxl_download_shortcode,
    parse_coria_label,
    parse_coria_mode,
)
from .yaml_frontmatter import frontmatter_to_block_metadata, parse_vsa_frontmatter

try:
    from .catalogus_bridge import (
        discover_bron_root,
        resolve_logical_vsa_path,
    )
    from catalogus.include_ref import is_logical_reference
except ImportError:  # pragma: no cover - catalogus niet geïnstalleerd
    is_logical_reference = None  # type: ignore[assignment]
    discover_bron_root = None  # type: ignore[assignment]
    resolve_logical_vsa_path = None  # type: ignore[assignment]

EXPORT_TYPES = frozenset({"svg", "coria", "mxl"})

# Optional exporttype, then path (quoted or unquoted), then optional parameters.
INCLUDE_EXPORT_PATTERN = re.compile(
    r'^:::include\s+(svg|coria|mxl)\s+(?:"([^"]+)"|(\S+))(?:\s+(.+?))?:::$'
)
INCLUDE_ZOEK_EXPORT_PATTERN = re.compile(
    r'^:::include\s+(svg|coria|mxl)\s+zoek="([^"]*)"(?:\s+(.+?))?:::$'
)
INCLUDE_PATTERN = re.compile(
    r'^:::include\s+(?:"([^"]+)"|(\S+))(?:\s+(.+?))?:::$'
)
# Detect mistyped exporttype keywords (word + path, not a plain file include).
INCLUDE_UNKNOWN_EXPORT_PATTERN = re.compile(
    r'^:::include\s+(\w+)\s+(?:"([^"]+)"|(\S+))(?:\s+(.+?))?:::$'
)

_ALT_ATTR = re.compile(r'alt="([^"]*)"')
_SCALE_ATTR = re.compile(r'scale="([^"]*)"')

_RASTER_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_DOCUMENT_SUFFIXES = {".pdf"}


class IncludeError(Exception):
    pass


def resolve_includes(
    text: str,
    source_path: Path,
    include_stack: list[Path] | None = None,
    svg_assets_dir: Path | None = None,
    svg_assets_url_prefix: str = "/vsa",
    content_root: Path | None = None,
    bron_root: Path | None = None,
    mxl_url_prefix: str = DEFAULT_MXL_URL_PREFIX,
    native_mxl_url_prefix: str = DEFAULT_NATIVE_MXL_URL_PREFIX,
    coria_html_url_prefix: str = DEFAULT_CORIA_HTML_URL_PREFIX,
) -> str:
    """Resolve :::include [exporttype] path [params]::: directives recursively.

    Exporttype ``svg`` refers to a ``.vsa`` source path. Exporttypes ``coria``
    and ``mxl`` accept ``.vsa`` (derived MXL) or native ``.mxl`` / ``.musicxml``.
    Extension-based includes (``.md``, ``.vsa`` / ``.mvsa`` without exporttype,
    ``.svg``, …) behave as before. Plain ``:::include bestand.mxl:::`` is not
    supported.

    Logische referenties ``id:…``, ``lokaal:…`` en ``bron:…`` worden via
    **catalogus** opgelost naar een ``.vsa``-pad (fase 3).

    ``content_root`` is required for exporttypes ``coria`` and ``mxl``.
    """
    if include_stack is None:
        include_stack = [source_path.resolve()]

    lines = text.splitlines()
    result_lines: list[str] = []
    in_code_fence = False
    fence_marker = ""

    for line in lines:
        stripped = line.strip()

        fence = _opening_or_closing_fence(stripped)
        if fence:
            if not in_code_fence:
                in_code_fence = True
                fence_marker = fence
            elif _closes_fence(stripped, fence_marker):
                in_code_fence = False
                fence_marker = ""
            result_lines.append(line)
            continue

        if in_code_fence:
            result_lines.append(line)
            continue

        parsed = _parse_include_directive(stripped)
        if parsed is None:
            result_lines.append(line)
            continue

        export_type, rel_path, params_str = parsed
        included_path = _resolve_include_path(
            rel_path,
            source_path=source_path,
            content_root=content_root,
            bron_root=bron_root,
        )

        if export_type is not None:
            _resolve_export_include(
                export_type,
                rel_path,
                included_path,
                params_str,
                source_path,
                result_lines,
                content_root=content_root,
                mxl_url_prefix=mxl_url_prefix,
                native_mxl_url_prefix=native_mxl_url_prefix,
                coria_html_url_prefix=coria_html_url_prefix,
            )
            continue

        if included_path in include_stack:
            chain = " → ".join(str(p) for p in include_stack) + f" → {included_path}"
            raise IncludeError(f"Kringverwijzing gedetecteerd: {chain}")

        if not included_path.exists():
            raise IncludeError(
                f"Bestand niet gevonden: '{rel_path}' (vanuit {source_path})"
            )

        suffix = included_path.suffix.lower()
        supported = {
            ".md",
            ".markdown",
            ".vsa",
            ".mvsa",
            ".svg",
        } | _RASTER_SUFFIXES | _DOCUMENT_SUFFIXES

        if suffix not in supported:
            raise IncludeError(
                f"Onbekend bestandstype '{suffix}' voor include:"
                f" '{rel_path}' (vanuit {source_path})"
            )

        alt = _parse_alt(params_str)
        scale = _parse_scale(params_str)

        if suffix in (".md", ".markdown"):
            raw = included_path.read_text(encoding="utf-8")
            expanded = resolve_includes(
                raw,
                source_path=included_path,
                include_stack=include_stack + [included_path],
                svg_assets_dir=svg_assets_dir,
                svg_assets_url_prefix=svg_assets_url_prefix,
                content_root=content_root,
                bron_root=bron_root,
                mxl_url_prefix=mxl_url_prefix,
                native_mxl_url_prefix=native_mxl_url_prefix,
                coria_html_url_prefix=coria_html_url_prefix,
            )
            result_lines.extend(expanded.splitlines())

        elif suffix == ".vsa":
            _append_vsa_notation_block(
                result_lines,
                included_path,
                alt=alt,
                scale=scale,
            )

        elif suffix == ".mvsa":
            _append_mvsa_notation_block(
                result_lines,
                included_path,
                alt=alt,
            )

        elif suffix in {".svg"} | _RASTER_SUFFIXES:
            alt_val = alt if alt is not None else ""
            natural_width = (
                _svg_natural_width(included_path.read_text(encoding="utf-8"))
                if suffix == ".svg"
                else None
            )
            if svg_assets_dir is not None:
                asset_name = _svg_asset_name(included_path, content_root)
                dest = svg_assets_dir / asset_name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(included_path, dest)
                url = f"{svg_assets_url_prefix.rstrip('/')}/{asset_name}"
                result_lines.append(
                    _vsa_shortcode(url, alt_val or None, scale, natural_width)
                )
            else:
                style_attr = _scale_style(scale, natural_width)
                alt_attr = f' alt="{alt_val}"' if alt is not None else ' alt=""'
                result_lines.append(
                    f'<img src="{rel_path}" class="vsa-notation"{alt_attr}{style_attr} />'
                )

        elif suffix in _DOCUMENT_SUFFIXES:
            alt_val = alt if alt is not None else included_path.stem.replace("-", " ")
            if svg_assets_dir is not None:
                asset_name = _svg_asset_name(included_path, content_root)
                dest = svg_assets_dir / asset_name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(included_path, dest)
                if content_root is not None:
                    url = _relative_static_vsa_href(
                        source_path, content_root, asset_name
                    )
                else:
                    url = f"{svg_assets_url_prefix.rstrip('/')}/{asset_name}"
                title_attr = f' title="{alt_val}"' if alt_val else ""
                result_lines.append(
                    f'<embed src="{url}" type="application/pdf" class="scan-pdf"{title_attr} />'
                )
            else:
                title_attr = f' title="{alt_val}"' if alt_val else ""
                result_lines.append(
                    f'<a href="{rel_path}" class="scan-pdf"{title_attr}>{alt_val}</a>'
                )

    return "\n".join(result_lines) + "\n"


def _parse_include_directive(stripped: str) -> tuple[str | None, str, str | None] | None:
    if INCLUDE_ZOEK_EXPORT_PATTERN.match(stripped):
        raise IncludeError(
            "Onopgeloste catalogus-zoekactie (zoek=) — draai eerst "
            "'vsa resolve-catalogus' op dit bestand."
        )

    match = INCLUDE_EXPORT_PATTERN.match(stripped)
    if match:
        return (
            match.group(1),
            (match.group(2) or match.group(3)).strip(),
            match.group(4),
        )

    match = INCLUDE_UNKNOWN_EXPORT_PATTERN.match(stripped)
    if match:
        keyword = match.group(1)
        rel_path = (match.group(2) or match.group(3)).strip()
        if (
            keyword not in EXPORT_TYPES
            and "." not in keyword
            and Path(rel_path).suffix.lower() in CORIA_MXL_SOURCE_SUFFIXES
        ):
            raise IncludeError(f"Onbekend exporttype: {keyword!r}")

    match = INCLUDE_PATTERN.match(stripped)
    if match:
        return None, (match.group(1) or match.group(2)).strip(), match.group(3)

    return None


def _resolve_include_path(
    rel_path: str,
    *,
    source_path: Path,
    content_root: Path | None,
    bron_root: Path | None,
) -> Path:
    if is_logical_reference is not None and is_logical_reference(rel_path):
        if content_root is None:
            raise IncludeError(
                f"content_root is verplicht voor logische referentie {rel_path!r}"
                f" (vanuit {source_path})"
            )
        if resolve_logical_vsa_path is None:
            raise IncludeError(
                "catalogus is niet geïnstalleerd; installeer bron-repo pakket "
                "(pip install -e vendor/bron of ../bron)"
            )
        effective_bron_root = bron_root
        if effective_bron_root is None and discover_bron_root is not None:
            effective_bron_root = discover_bron_root(content_root)
        try:
            return resolve_logical_vsa_path(
                rel_path,
                content_root=content_root,
                bron_root=effective_bron_root,
            )
        except Exception as exc:
            raise IncludeError(
                f"Catalogus-referentie {rel_path!r} (vanuit {source_path}): {exc}"
            ) from exc
    return (source_path.parent / rel_path).resolve()


def _resolve_export_include(
    export_type: str,
    rel_path: str,
    included_path: Path,
    params_str: str | None,
    source_path: Path,
    result_lines: list[str],
    *,
    content_root: Path | None,
    mxl_url_prefix: str,
    native_mxl_url_prefix: str,
    coria_html_url_prefix: str,
) -> None:
    suffix = included_path.suffix.lower()
    if export_type == "svg":
        if suffix != ".vsa":
            raise IncludeError(
                f"Exporttype 'svg' verwacht een .vsa-bron, kreeg: '{rel_path}'"
                f" (vanuit {source_path})"
            )
    elif export_type in {"coria", "mxl"}:
        if suffix not in CORIA_MXL_SOURCE_SUFFIXES:
            raise IncludeError(
                f"Exporttype '{export_type}' verwacht een .vsa-, .mxl- of "
                f".musicxml-bron, kreeg: '{rel_path}' (vanuit {source_path})"
            )
    else:
        raise IncludeError(f"Onbekend exporttype: {export_type!r}")

    if not included_path.exists():
        raise IncludeError(
            f"Bestand niet gevonden: '{rel_path}' (vanuit {source_path})"
        )

    if export_type == "svg":
        _append_vsa_notation_block(
            result_lines,
            included_path,
            alt=_parse_alt(params_str),
            scale=_parse_scale(params_str),
        )
        return

    if content_root is None:
        raise IncludeError(
            f"content_root is verplicht voor exporttype '{export_type}'"
            f" (directive: {rel_path!r})"
        )

    try:
        if export_type == "coria":
            try:
                coria_mode = parse_coria_mode(params_str)
            except CoriaDirectiveError as exc:
                raise IncludeError(str(exc)) from exc
            asset = resolve_asset(
                included_path,
                content_root,
                "coria",
                mxl_url_prefix=mxl_url_prefix,
                native_mxl_url_prefix=native_mxl_url_prefix,
                coria_html_url_prefix=coria_html_url_prefix,
                coria_mode=coria_mode,
            )
            label = parse_coria_label(params_str) or "Oefenen in Coria"
            result_lines.append(emit_coria_shortcode(asset.public_url_path, label))
            return

        if export_type == "mxl":
            asset = resolve_asset(
                included_path,
                content_root,
                "mxl",
                mxl_url_prefix=mxl_url_prefix,
                native_mxl_url_prefix=native_mxl_url_prefix,
                coria_html_url_prefix=coria_html_url_prefix,
            )
            label = parse_coria_label(params_str) or DEFAULT_MXL_DOWNLOAD_LABEL
            result_lines.append(emit_mxl_download_shortcode(asset.public_url_path, label))
            return
    except ContentAssetError as exc:
        raise IncludeError(f"{source_path}: {exc}") from exc

    raise IncludeError(f"Onbekend exporttype: {export_type!r}")


def _append_vsa_notation_block(
    result_lines: list[str],
    included_path: Path,
    *,
    alt: str | None,
    scale: str | None,
) -> None:
    raw = included_path.read_text(encoding="utf-8")
    frontmatter, vsa_body = parse_vsa_frontmatter(raw)
    fm_meta = frontmatter_to_block_metadata(frontmatter)
    result_lines.append("::: vsa-notatie")
    for key, value in sorted(fm_meta.items()):
        result_lines.append(f"# {key}: {value}")
    if alt:
        result_lines.append(f"# alt: {alt}")
    if scale:
        result_lines.append(f"# scale: {scale}")
    if vsa_body:
        result_lines.extend(vsa_body.splitlines())
    result_lines.append(":::")


def _append_mvsa_notation_block(
    result_lines: list[str],
    included_path: Path,
    *,
    alt: str | None,
) -> None:
    """Wrap a ``.mvsa`` file as ``::: mvsa-notatie`` (geen YAML-frontmatter)."""
    body = included_path.read_text(encoding="utf-8-sig")
    result_lines.append("::: mvsa-notatie")
    if alt:
        result_lines.append(f'alt="{alt}"')
    if body:
        result_lines.extend(body.splitlines())
    result_lines.append(":::")


def _parse_alt(params_str: str | None) -> str | None:
    if not params_str:
        return None
    m = _ALT_ATTR.search(params_str)
    return m.group(1) if m else None


def _parse_scale(params_str: str | None) -> str | None:
    if not params_str:
        return None
    m = _SCALE_ATTR.search(params_str)
    return m.group(1) if m else None


def _svg_asset_name(asset_path: Path, content_root: Path | None) -> str:
    """Derive a flat, collision-free filename for a copied asset."""
    if content_root is not None:
        try:
            relative = asset_path.resolve().relative_to(content_root.resolve())
            stem = "-".join(relative.with_suffix("").parts)
            return _safe_name(stem) + asset_path.suffix.lower()
        except ValueError:
            pass
    return _safe_name(asset_path.stem) + asset_path.suffix.lower()


def _relative_static_vsa_href(
    source_path: Path,
    content_root: Path,
    asset_name: str,
    *,
    static_segment: str = "vsa",
) -> str:
    """Site-root-relative href to static/vsa (Hugo serves static/ at site root).

    Hugo leaf pages become ``…/slug/index.html``; depth = padsegmenten onder
    content-root tot en met de pagina-slug (niet alleen de map van het .md-bestand).
    """
    rel_page = source_path.resolve().relative_to(content_root.resolve())
    if rel_page.name.startswith("_index."):
        ups = len(rel_page.parent.parts)
    else:
        ups = len(rel_page.with_suffix("").parts)
    prefix = "../" * ups if ups else ""
    return f"{prefix}{static_segment}/{asset_name.replace(chr(92), '/')}"


def _safe_name(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    value = value.strip("-")
    return value or "asset"


def _opening_or_closing_fence(stripped: str) -> str:
    if stripped.startswith("```"):
        return "```"
    if stripped.startswith("~~~"):
        return "~~~"
    return ""


def _closes_fence(stripped: str, fence_marker: str) -> bool:
    return stripped.startswith(fence_marker)


_SVG_WIDTH_RE = re.compile(r"<svg\b[^>]*\bwidth=\"(\d+(?:\.\d+)?)\"")


def _svg_natural_width(svg_text: str) -> float | None:
    """Extract the natural pixel width from an SVG string."""
    m = _SVG_WIDTH_RE.search(svg_text)
    return float(m.group(1)) if m else None


def _scale_style(scale: str | None, natural_width: float | None) -> str:
    """Return an inline style attribute for the given scale, or empty string.

    Uses absolute pixels (natural_width × scale%) so that the visual font size
    stays consistent regardless of SVG content width. Falls back to percentage
    when natural_width is unavailable.
    """
    if not scale:
        return ""
    if natural_width is not None:
        try:
            pct = float(scale.rstrip("%"))
            px = round(natural_width * pct / 100)
            return f' style="width: {px}px"'
        except ValueError:
            pass
    return f' style="width: {scale}"'


def _scale_px(scale: str | None, natural_width: float | None) -> str | None:
    if not scale:
        return None
    if natural_width is not None:
        try:
            pct = float(scale.rstrip("%"))
            return f"{round(natural_width * pct / 100)}px"
        except ValueError:
            pass
    return scale


def _vsa_shortcode(
    src: str,
    alt: str | None,
    scale: str | None,
    natural_width: float | None = None,
) -> str:
    """Emit Hugo vsa shortcode; relURL in the shortcode adds the site baseURL."""
    alt_val = alt if alt is not None else "VSA notatie"
    scale_param = ""
    px = _scale_px(scale, natural_width)
    if px:
        scale_param = f' scale="{px}"'
    return f'{{{{< vsa src="{src}" alt="{alt_val}"{scale_param} >}}}}'
