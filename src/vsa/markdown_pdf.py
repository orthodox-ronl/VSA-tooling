"""Render one Markdown file (VSA-blokken, includes, pagebreaks) to a print PDF."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from html import escape
from pathlib import Path

from .config import VSAConfig, load_config
from .include_vsa import discover_content_root
from .markdown_builder import prepare_markdown_document
from .markdown_directives import DirectiveError
from .markdown_include import IncludeError
from .markdown_processor import ProcessValidationError
from .validation_runner import validate_file
from .yaml_frontmatter import parse_vsa_frontmatter

_SHORTCODE_RE = re.compile(
    r"\{\{<\s*(/?)\s*([a-z0-9-]+)([^>]*?)>\}\}",
    re.IGNORECASE,
)
_ATTR_RE = re.compile(r'([a-z0-9-]+)="([^"]*)"', re.IGNORECASE)

_DROP_SINGLE = frozenset(
    {"coria", "coria-html", "mxl-download", "navbuttons"}
)
_PAIRED_KEEP = frozenset({"print-only", "keep-together"})
_PAIRED_DROP = frozenset({"web-only"})

# Chrome/Edge headless ``--print-to-pdf`` zet preferCSSPageSize=true.
# Zonder geldige @page-size valt CDP terug op US Letter (8.5×11 in).
# Expliciete A4-maten (mm) i.p.v. alleen het keyword — stabieler over browsers.
_A4_PAGE_CSS = (
    "/* papier: A4 staand — niet US Letter */\n"
    "@page { size: 210mm 297mm; margin: 1cm 2cm; }"
)

_PRINT_CSS = f"""
{_A4_PAGE_CSS}
html {{ font-size: 18px; }}
body {{
  font-family: Arial, sans-serif;
  line-height: 1.55;
  color: #111;
  margin: 0;
}}
h1, h2, h3, h4 {{ page-break-after: avoid; }}
.pagebreak {{ break-before: page; page-break-before: always; }}
.web-only {{ display: none; }}
.keep-together {{
  break-inside: avoid;
  page-break-inside: avoid;
}}
.keep-together > p:empty,
.print-only > p:empty {{
  display: none;
  margin: 0;
  padding: 0;
}}
img, .vsa-notation {{ max-width: 100%; height: auto; }}
.vsa-container {{ margin: 1.25rem 0; max-width: 100%; }}
.vsa-notation {{
  border: 1px solid #d0d0d0;
  padding: 0;
  background: #fff;
}}
.keep-together .vsa-notation {{ width: var(--vsa-scale, auto); }}
"""


class PdfError(Exception):
    def __init__(self, message_nl: str, *, hint_nl: str = "") -> None:
        super().__init__(message_nl)
        self.message_nl = message_nl
        self.hint_nl = hint_nl


def write_markdown_pdf(
    input_path: str | Path,
    output_path: str | Path,
    *,
    content_root: str | Path | None = None,
    bron_root: str | Path | None = None,
    config: VSAConfig | None = None,
    max_line_width: float | None = None,
    chrome_command: list[str] | None = None,
) -> Path:
    input_path = Path(input_path)
    output_path = Path(output_path)
    if not input_path.is_file():
        raise PdfError(
            f"Bestand niet gevonden: {input_path}",
            hint_nl="Geef een bestaand Markdownbestand (.md) op.",
        )
    input_path = input_path.resolve()
    if input_path.suffix.lower() not in {".md", ".markdown"}:
        raise PdfError(
            f"PDF-export verwacht Markdown, kreeg: {input_path.name}",
            hint_nl="Gebruik een .md-bestand met VSA-blokken en/of includes.",
        )

    if config is None:
        config = load_config()
    width = (
        max_line_width
        if max_line_width is not None
        else config.rendering.max_line_width
    )
    root = Path(content_root) if content_root else discover_content_root(input_path)
    if root is None:
        root = input_path.parent
    bron = Path(bron_root) if bron_root else None

    validation = validate_file(input_path, config=config)
    if not validation.ok:
        raise ProcessValidationError(validation.messages)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="vsa-pdf-") as tmp:
        tmp_dir = Path(tmp)
        assets_dir = tmp_dir / "assets"
        try:
            rewritten, _svg_paths = prepare_markdown_document(
                input_path,
                content_root=root,
                assets_dir=assets_dir,
                assets_url_prefix="assets",
                max_line_width=width,
                output_mode="img",
                bron_root=bron,
            )
        except IncludeError as exc:
            raise PdfError(
                f"{input_path}: {exc}",
                hint_nl=(
                    "Controleer :::include-paden en catalogus-ids. "
                    "De content-root is de map met lokaal/ (meestal content-source); "
                    "geef die zonodig met --content-root."
                ),
            ) from exc
        except DirectiveError as exc:
            raise PdfError(
                f"{input_path}: {exc}",
                hint_nl=(
                    "Controleer :::pagebreak::: / :::keep-together::: / "
                    ":::web-only::: / :::print-only:::."
                ),
            ) from exc
        html_path = tmp_dir / "page.html"
        html_path.write_text(
            markdown_to_print_html(rewritten, title=_document_title(rewritten, input_path)),
            encoding="utf-8",
        )
        html_file_to_pdf(html_path, output_path, chrome_command=chrome_command)

    return output_path


def markdown_to_print_html(source: str, *, title: str) -> str:
    meta, body = parse_vsa_frontmatter(source)
    if not title:
        title = str(meta.get("title") or "VSA")
    expanded = expand_print_shortcodes(body)
    body_html = _markdown_to_html(expanded)
    return (
        "<!DOCTYPE html>\n<html lang=\"nl\">\n<head>\n"
        f"<meta charset=\"utf-8\">\n<title>{escape(title)}</title>\n"
        f"<style>{_PRINT_CSS}</style>\n</head>\n<body>\n"
        f"{body_html}\n</body>\n</html>\n"
    )


def expand_print_shortcodes(text: str) -> str:
    """Turn Hugo print/web shortcodes into HTML (or drop web-only material)."""
    parts: list[str] = []
    last = 0
    skip_depth = 0
    keep_stack: list[str] = []

    for match in _SHORTCODE_RE.finditer(text):
        closing = match.group(1) == "/"
        name = match.group(2).lower()
        raw_attrs = match.group(3) or ""

        if skip_depth:
            if closing and name in _PAIRED_DROP:
                skip_depth -= 1
            elif not closing and name in _PAIRED_DROP:
                skip_depth += 1
            last = match.end()
            continue

        parts.append(text[last:match.start()])
        last = match.end()

        if not closing and name in _PAIRED_DROP:
            skip_depth = 1
            continue

        if closing and name in _PAIRED_DROP:
            continue

        if not closing and name == "pagebreak":
            parts.append('\n<div class="pagebreak"></div>\n')
            continue

        if not closing and name == "vsa":
            parts.append(_vsa_img_html(_parse_attrs(raw_attrs)))
            continue

        if not closing and name in _DROP_SINGLE:
            continue

        if not closing and name in _PAIRED_KEEP:
            keep_stack.append(name)
            if name == "keep-together":
                attrs = _parse_attrs(raw_attrs)
                scale = attrs.get("scale")
                style = f' style="width: {escape(scale, quote=True)}"' if scale else ""
                parts.append(f'\n<div class="keep-together"{style}>\n')
            else:
                parts.append('\n<div class="print-only">\n')
            continue

        if closing and name in _PAIRED_KEEP:
            if keep_stack and keep_stack[-1] == name:
                keep_stack.pop()
            class_name = "keep-together" if name == "keep-together" else "print-only"
            parts.append(f"\n</div><!-- {class_name} -->\n")
            continue

        parts.append(match.group(0))

    parts.append(text[last:])
    if skip_depth or keep_stack:
        open_name = keep_stack[-1] if keep_stack else "web-only"
        raise PdfError(
            f"Niet-gesloten Hugo-shortcode: {open_name}",
            hint_nl=f"Sluit het blok met {{{{< /{open_name} >}}}}.",
        )
    return "".join(parts)


def find_chrome() -> Path:
    env = os.environ.get("CHROME_PATH") or os.environ.get("EDGE_PATH")
    candidates: list[Path] = []
    if env:
        candidates.append(Path(env))

    program_files = [
        os.environ.get("PROGRAMFILES", r"C:\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", ""),
    ]
    relative = [
        r"Microsoft\Edge\Application\msedge.exe",
        r"Google\Chrome\Application\chrome.exe",
    ]
    for root in program_files:
        if not root:
            continue
        for rel in relative:
            candidates.append(Path(root) / rel)

    for name in ("msedge", "chrome", "chromium", "chromium-browser", "google-chrome"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))

    for path in candidates:
        if path.is_file():
            return path

    raise PdfError(
        "geen Chromium-browser gevonden voor PDF-export",
        hint_nl=(
            "Installeer Microsoft Edge of Google Chrome, of zet CHROME_PATH "
            "naar het .exe-bestand."
        ),
    )


def html_file_to_pdf(
    html_path: Path,
    pdf_path: Path,
    *,
    chrome_command: list[str] | None = None,
) -> None:
    """Print HTML to PDF via Chrome/Edge headless.

    Papierformaat komt uit de HTML (``@page`` A4 / 210×297 mm), niet uit een
    Chrome-CLI-flag. Headless zet ``preferCSSPageSize``; zonder CSS is de
    CDP-default US Letter.
    """
    command = list(chrome_command) if chrome_command else [str(find_chrome())]
    html_uri = html_path.resolve().as_uri()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    args = command + [
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--allow-file-access-from-files",
        "--virtual-time-budget=10000",
        f"--print-to-pdf={pdf_path.resolve()}",
        html_uri,
    ]
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not pdf_path.is_file():
        retry = command + [
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--allow-file-access-from-files",
            f"--print-to-pdf={pdf_path.resolve()}",
            html_uri,
        ]
        proc = subprocess.run(retry, capture_output=True, text=True, check=False)
    if not pdf_path.is_file():
        detail = (proc.stderr or proc.stdout or "").strip()
        extra = f" {detail}" if detail else ""
        raise PdfError(
            f"PDF-export mislukt (exitcode {proc.returncode}).{extra}",
            hint_nl=(
                "Controleer CHROME_PATH, of open de tussentijdse HTML in Edge "
                "en druk af naar PDF."
            ),
        )


def _document_title(source: str, input_path: Path) -> str:
    meta, _body = parse_vsa_frontmatter(source)
    title = meta.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return input_path.stem


def _parse_attrs(raw: str) -> dict[str, str]:
    return {match.group(1).lower(): match.group(2) for match in _ATTR_RE.finditer(raw)}


def _vsa_img_html(attrs: dict[str, str]) -> str:
    src = attrs.get("src") or ""
    alt = attrs.get("alt") or "VSA notatie"
    scale = attrs.get("scale")
    style = f' style="width: {escape(scale, quote=True)}"' if scale else ""
    return (
        '\n<div class="vsa-container">'
        f'<img class="vsa-notation" src="{escape(src, quote=True)}" '
        f'alt="{escape(alt, quote=True)}"{style}>'
        "</div>\n"
    )


def _markdown_to_html(text: str) -> str:
    try:
        import markdown
    except ImportError as exc:
        raise PdfError(
            "Python-pakket 'markdown' ontbreekt.",
            hint_nl="Installeer het in dezelfde Python als vsa-tool (pip install markdown).",
        ) from exc
    return markdown.markdown(text, extensions=["extra"])
