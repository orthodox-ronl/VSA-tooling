"""In-memory expand van ``@include-vsa`` in VSA-notatie."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .yaml_frontmatter import parse_vsa_frontmatter


class IncludeVsaError(Exception):
    """Fout bij expand van ``@include-vsa``."""

    def __init__(self, message_nl: str, *, line: int = 1) -> None:
        super().__init__(message_nl)
        self.message_nl = message_nl
        self.line = line


@dataclass(frozen=True)
class IncludeVsaWarning:
    code: str
    message_nl: str
    line: int


try:
    from catalogus.errors import CatalogusError

    from .catalogus_bridge import discover_bron_root, resolve_logical_vsa_path
except ImportError:  # pragma: no cover - catalogus niet geïnstalleerd

    def discover_bron_root(content_root=None):  # type: ignore[misc]
        return None

    def resolve_logical_vsa_path(*args, **kwargs):  # type: ignore[misc]
        raise IncludeVsaError(
            "catalogus-package niet beschikbaar; installeer catalogus uit bron-repo.",
            line=1,
        )

    class CatalogusError(Exception):  # type: ignore[no-redef]
        pass


INCLUDE_VSA_PATTERN = re.compile(
    r"@include-vsa\s+(?:"
    r'zoek="([^"]*)"|'
    r"id=([^\s]+)|"
    r"lokaal=([^\s]+)"
    r")"
)


def discover_content_root(source_path: Path) -> Path | None:
    """Zoek parochie content-source (map met ``lokaal/``) omhoog vanaf ``source_path``.

    ``source_path`` mag relatief zijn (bijv. alleen de bestandsnaam in de cwd);
    zonder ``resolve()`` stopt de walk bij ``.`` en wordt ``lokaal/`` in een
    bovenliggende map gemist.
    """
    for parent in Path(source_path).resolve().parents:
        if (parent / "lokaal").is_dir():
            return parent
    return None


def parse_session_frontmatter(text: str) -> tuple[dict, str]:
    """YAML-frontmatter uit markdown of ``.vsa`` (``---`` … ``---``)."""
    return parse_vsa_frontmatter(text)


def expand_include_vsa(
    text: str,
    *,
    source_path: Path,
    content_root: Path | None = None,
    bron_root: Path | None = None,
    include_stack: list[Path] | None = None,
) -> tuple[str, list[IncludeVsaWarning]]:
    """Vervang ``@include-vsa`` door ingesloten VSA-body (brondocument ongewijzigd)."""
    if include_stack is None:
        include_stack = []

    match = INCLUDE_VSA_PATTERN.search(text)
    if not match:
        return text, []

    line_no = text[: match.start()].count("\n") + 1
    kind, value = _parse_directive(match)
    if not value.strip():
        raise IncludeVsaError(f"Lege waarde voor @include-vsa {kind}=", line=line_no)

    resolved_root = content_root.resolve() if content_root else discover_content_root(source_path)
    resolved_bron = bron_root
    if resolved_bron is None and resolved_root is not None:
        resolved_bron = discover_bron_root(resolved_root)

    target_path, warnings = _resolve_target(
        kind,
        value.strip(),
        line_no=line_no,
        content_root=resolved_root,
        bron_root=resolved_bron,
    )

    target_resolved = target_path.resolve()
    if target_resolved in include_stack:
        chain = " → ".join(str(p) for p in include_stack) + f" → {target_resolved}"
        raise IncludeVsaError(f"Cyclische @include-vsa: {chain}", line=line_no)

    included_raw = target_resolved.read_text(encoding="utf-8")
    included_fm, included_body = parse_vsa_frontmatter(included_raw)
    included_body = _trim_vsa_body(included_body)

    included_expanded, nested_warnings = expand_include_vsa(
        included_body,
        source_path=target_resolved,
        content_root=resolved_root,
        bron_root=resolved_bron,
        include_stack=include_stack + [target_resolved],
    )

    replacement = included_expanded
    new_text = text[: match.start()] + replacement + text[match.end() :]

    rest, rest_warnings = expand_include_vsa(
        new_text,
        source_path=source_path,
        content_root=resolved_root,
        bron_root=resolved_bron,
        include_stack=include_stack,
    )
    return rest, [*warnings, *nested_warnings, *rest_warnings]


def prepare_vsa_body(
    text: str,
    source_path: Path,
    *,
    content_root: Path | None = None,
    bron_root: Path | None = None,
    session_frontmatter: dict | None = None,
) -> tuple[str, list[IncludeVsaWarning]]:
    """Expand ``@include-vsa`` in VSA-body (na optionele frontmatter-strip)."""
    _, body = parse_vsa_frontmatter(text)
    return expand_include_vsa(
        body,
        source_path=source_path,
        content_root=content_root,
        bron_root=bron_root,
    )


def prepare_markdown_block_body(
    block_body: str,
    *,
    markdown_path: Path,
    markdown_text: str,
    content_root: Path | None = None,
    bron_root: Path | None = None,
) -> tuple[str, list[IncludeVsaWarning]]:
    """Expand ``@include-vsa`` in een ``::: vsa-notatie`` blok."""
    root = content_root or discover_content_root(markdown_path)
    bron = bron_root
    if bron is None and root is not None:
        bron = discover_bron_root(root)
    return expand_include_vsa(
        block_body,
        source_path=markdown_path,
        content_root=root,
        bron_root=bron,
    )


def _parse_directive(match: re.Match[str]) -> tuple[str, str]:
    if match.group(1) is not None:
        return "zoek", match.group(1)
    if match.group(2) is not None:
        return "id", match.group(2)
    return "lokaal", match.group(3)


def _resolve_target(
    kind: str,
    value: str,
    *,
    line_no: int,
    content_root: Path | None,
    bron_root: Path | None,
) -> tuple[Path, list[IncludeVsaWarning]]:
    warnings: list[IncludeVsaWarning] = []

    if kind in ("id", "lokaal"):
        if content_root is None:
            raise IncludeVsaError(
                "Geen content-root (parochie content-source met lokaal/) gevonden "
                f"voor @include-vsa {kind}={value!r}.",
                line=line_no,
            )
        reference = f"{kind}:{value}"
        try:
            path = resolve_logical_vsa_path(
                reference,
                content_root=content_root,
                bron_root=bron_root,
            )
        except (ValueError, CatalogusError) as exc:
            raise IncludeVsaError(str(exc), line=line_no) from exc
        return path, warnings

    raise IncludeVsaError(
        "@include-vsa zoek= wordt niet meer ondersteund. "
        "Gebruik id=<catalogus-id> of lokaal=<pad>.",
        line=line_no,
    )


def _trim_vsa_body(body: str) -> str:
    lines = body.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)
