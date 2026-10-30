"""Top-level ``markdown`` CLI (bron: ``.md`` / ``.markdown``).

Producten: pdf (pagina-A4), svg (VSA-blokken), text (platte pagina-tekst).
Geen validate/kuiser/normalize. Geen ``md``-entrypoint: op Windows is ``md``
makedir. Contract: docs/formats/contract-index.md (site-Markdown vs
notatie-product pdf).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from .derived_path import derived_output_path
from .input_paths import InputPathError, collect_cli_sources

_MD_SUFFIXES = (".md", ".markdown")
_VSA_FENCE_RE = re.compile(
    r":::[\t ]*vsa-notatie[^\n]*\n(.*?):::",
    re.IGNORECASE | re.DOTALL,
)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()
    ns = parser.parse_args(args)
    if ns.md_command == "pdf":
        return _cmd_md_pdf(ns)
    if ns.md_command == "svg":
        return _cmd_md_svg(ns)
    if ns.md_command == "text":
        return _cmd_md_text(ns)
    parser.print_help()
    return 1


def run_markdown_pdf_cli(
    *,
    input_path: Path,
    output: Path | None,
    config_path: str | None,
    content_root: str | None,
    bron_root: str | None,
    max_line_width: float | None,
    chrome: str | None,
) -> int:
    """Gedeelde implementatie voor ``markdown pdf`` en verouderd ``vsa pdf``."""
    from .config import load_config
    from .markdown_pdf import PdfError, write_markdown_pdf
    from .markdown_processor import ProcessValidationError

    if input_path.suffix.lower() not in {".md", ".markdown"}:
        print(
            f"markdown pdf weigert {input_path.suffix or '(geen extensie)'}; "
            f"gebruik een .md-bestand: markdown pdf {input_path}",
            file=sys.stderr,
        )
        return 1
    out = (
        Path(output)
        if output is not None
        else derived_output_path(input_path, ".pdf")
    )
    config = load_config(config_path)
    chrome_command = [chrome] if chrome else None
    from .validation_display import format_validation_message

    try:
        result = write_markdown_pdf(
            input_path,
            out,
            content_root=content_root,
            bron_root=bron_root,
            config=config,
            max_line_width=max_line_width,
            chrome_command=chrome_command,
        )
    except ProcessValidationError as exc:
        for message in exc.messages:
            for line in format_validation_message(message):
                print(line)
        return 1
    except PdfError as exc:
        print(f"ERROR: {exc.message_nl}", file=sys.stderr)
        if exc.hint_nl:
            print(exc.hint_nl, file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"PDF geschreven naar: {result}")
    return 0


def _collect(path: str | Path) -> list[Path] | None:
    try:
        return collect_cli_sources(path, suffixes=_MD_SUFFIXES)
    except InputPathError as exc:
        print(str(exc), file=sys.stderr)
        return None


def _reject_multi_output(files: list[Path], output: str | None) -> bool:
    if len(files) > 1 and output:
        print(
            "-o/--output is alleen toegestaan bij precies één bronbestand "
            "(bij een map: sibling-output per bron).",
            file=sys.stderr,
        )
        return True
    return False


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="markdown",
        description=(
            "Producten uit Markdown (.md): pagina-PDF, VSA-SVG’s, platte tekst. "
            "Geen `md`-commando (Windows = makedir). "
            "Zie docs/reference/cli/markdown.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "subcommando's:\n"
            "  pdf PATH [-o OUT] — A4-PDF (Chrome/Edge; default sibling *.md.pdf)\n"
            "  svg PATH [-o DIR] — SVG’s uit :::vsa-notatie-blokken\n"
            "  text PATH [-o OUT] — platte tekst (default sibling *.md.txt)\n"
            "\n"
            "voorbeelden:\n"
            "  markdown pdf index.md\n"
            "  markdown pdf index.md -o index.md.pdf\n"
            "  markdown text liturgie.md\n"
            "  markdown svg liturgie.md -o generated\\svg\n"
        ),
    )
    sub = parser.add_subparsers(
        dest="md_command",
        required=True,
        metavar="{pdf,svg,text}",
    )

    pdf = sub.add_parser(
        "pdf",
        help="Render Markdown (VSA, includes, pagebreaks) naar A4-PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_pdf_args(pdf)

    svg = sub.add_parser(
        "svg",
        help="Schrijf SVG’s voor :::vsa-notatie-blokken in het Markdownbestand.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    svg.add_argument(
        "path",
        help=".md-bestand of map met .md-bestanden (recursief).",
    )
    svg.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoermap voor SVG’s (default: sibling <bronnaam>.assets/). "
            "Alleen bij precies één bronbestand."
        ),
    )
    svg.add_argument("--config", default=None)
    svg.add_argument("--content-root", default=None)
    svg.add_argument("--bron-root", default=None)
    svg.add_argument("--max-line-width", type=float, default=None)

    text = sub.add_parser(
        "text",
        help="Platte tekst uit Markdown (+ VSA-blokken zonder notatie).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    text.add_argument(
        "path",
        help=".md-bestand of map met .md-bestanden (recursief).",
    )
    text.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoer (default: sibling <bronnaam>.txt). "
            "Alleen bij precies één bronbestand."
        ),
    )
    return parser


def _add_pdf_args(pdf: argparse.ArgumentParser) -> None:
    pdf.add_argument(
        "path",
        help=".md-bestand of map met .md-bestanden (recursief).",
    )
    pdf.add_argument(
        "-o",
        "--output",
        default=None,
        help=(
            "Uitvoer-PDF (default: sibling <bronnaam>.pdf, bv. index.md.pdf). "
            "Alleen bij precies één bronbestand."
        ),
    )
    pdf.add_argument("--config", default=None)
    pdf.add_argument(
        "--content-root",
        default=None,
        help="Content-root voor includes (map met lokaal/).",
    )
    pdf.add_argument(
        "--bron-root",
        default=None,
        help="Bron-repo root (default: auto).",
    )
    pdf.add_argument("--max-line-width", type=float, default=None)
    pdf.add_argument(
        "--chrome",
        default=None,
        help="Pad naar Edge/Chrome/Chromium.",
    )


def _cmd_md_pdf(ns: argparse.Namespace) -> int:
    files = _collect(ns.path)
    if files is None:
        return 1
    if _reject_multi_output(files, ns.output):
        return 1
    exit_code = 0
    for path in files:
        out = Path(ns.output) if ns.output else None
        # Bij map: altijd sibling per bron
        if len(files) > 1:
            out = None
        code = run_markdown_pdf_cli(
            input_path=path,
            output=out,
            config_path=ns.config,
            content_root=ns.content_root,
            bron_root=ns.bron_root,
            max_line_width=ns.max_line_width,
            chrome=ns.chrome,
        )
        if code:
            exit_code = code
    return exit_code


def _cmd_md_svg(ns: argparse.Namespace) -> int:
    from .config import load_config
    from .include_vsa import discover_content_root
    from .markdown_builder import prepare_markdown_document
    from .markdown_directives import DirectiveError
    from .markdown_include import IncludeError
    from .markdown_processor import ProcessValidationError
    from .validation_runner import validate_file

    files = _collect(ns.path)
    if files is None:
        return 1
    if _reject_multi_output(files, ns.output):
        return 1
    config = load_config(ns.config)
    width = (
        ns.max_line_width
        if ns.max_line_width is not None
        else config.rendering.max_line_width
    )
    exit_code = 0
    for path in files:
        assets = (
            Path(ns.output)
            if ns.output
            else path.parent / f"{path.name}.assets"
        )
        root = (
            Path(ns.content_root)
            if ns.content_root
            else discover_content_root(path)
        )
        if root is None:
            root = path.parent
        bron = Path(ns.bron_root) if ns.bron_root else None
        from .validation_display import format_validation_message

        validation = validate_file(path, config=config)
        if not validation.ok:
            for message in validation.messages:
                for line in format_validation_message(message):
                    print(line)
            exit_code = 1
            continue
        try:
            _rewritten, svg_paths = prepare_markdown_document(
                path,
                content_root=root,
                assets_dir=assets,
                assets_url_prefix=assets.name,
                max_line_width=width,
                output_mode="img",
                bron_root=bron,
                config=config,
            )
        except (IncludeError, DirectiveError, ProcessValidationError) as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        except Exception as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        if not svg_paths:
            print(f"{path}: geen :::vsa-notatie-blokken (geen SVG).", flush=True)
            continue
        for svg in svg_paths:
            print(f"Geschreven: {svg}")
    return exit_code


def _plain_text_from_markdown(source: str) -> str:
    """Platte tekst: VSA-blokken via text_export; overige regels ontdaan van light markup."""
    from .text_export import plain_text_from_vsa
    from .yaml_frontmatter import parse_vsa_frontmatter

    _fm, body = parse_vsa_frontmatter(source)
    parts: list[str] = []
    pos = 0
    for match in _VSA_FENCE_RE.finditer(body):
        before = body[pos : match.start()]
        if before.strip():
            parts.append(_strip_md_light(before))
        try:
            parts.append(plain_text_from_vsa(match.group(1)))
        except Exception:
            parts.append(_strip_md_light(match.group(1)))
        pos = match.end()
    tail = body[pos:]
    if tail.strip():
        parts.append(_strip_md_light(tail))
    text = "\n\n".join(p.strip() for p in parts if p.strip())
    return text


def _strip_md_light(text: str) -> str:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            lines.append("")
            continue
        if line.startswith(":::"):
            continue
        line = re.sub(r"^#{1,6}\s+", "", line)
        line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
        line = re.sub(r"[`*_]+", "", line)
        lines.append(line)
    # Collapse excess blank lines
    out: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if not blank:
                out.append("")
            blank = True
        else:
            out.append(line)
            blank = False
    return "\n".join(out).strip()


def _cmd_md_text(ns: argparse.Namespace) -> int:
    files = _collect(ns.path)
    if files is None:
        return 1
    if _reject_multi_output(files, ns.output):
        return 1
    exit_code = 0
    for path in files:
        out = (
            Path(ns.output)
            if ns.output
            else derived_output_path(path, ".txt")
        )
        try:
            text = _plain_text_from_markdown(
                path.read_text(encoding="utf-8")
            )
        except Exception as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = text if text.endswith("\n") or text == "" else text + "\n"
        out.write_text(payload, encoding="utf-8", newline="\n")
        print(f"Geschreven: {out}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
