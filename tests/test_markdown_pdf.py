import sys
from pathlib import Path

import pytest

from vsa.cli import main
from vsa.markdown_pdf import (
    PdfError,
    expand_print_shortcodes,
    markdown_to_print_html,
    write_markdown_pdf,
)


def _fake_chrome(tmp_path: Path) -> list[str]:
    script = tmp_path / "fake_chrome.py"
    script.write_text(
        "import sys\n"
        "from pathlib import Path\n"
        "for arg in sys.argv[1:]:\n"
        "    if arg.startswith('--print-to-pdf='):\n"
        "        Path(arg.split('=', 1)[1]).write_bytes(b'%PDF-1.4\\n%%EOF\\n')\n",
        encoding="utf-8",
    )
    return [sys.executable, str(script)]


def test_expand_pagebreak_and_vsa_shortcode():
    text = (
        "Voor\n"
        "{{< pagebreak >}}\n"
        '{{< vsa src="assets/demo.svg" alt="Demo" scale="200px" >}}\n'
        "Na\n"
    )
    result = expand_print_shortcodes(text)
    assert 'class="pagebreak"' in result
    assert 'src="assets/demo.svg"' in result
    assert 'style="width: 200px"' in result
    assert "{{<" not in result


def test_expand_drops_web_only_keeps_print_only():
    text = (
        "A\n"
        "{{< web-only >}}\n"
        "alleen web\n"
        "{{< /web-only >}}\n"
        "{{< print-only >}}\n"
        "alleen print\n"
        "{{< /print-only >}}\n"
        "B\n"
    )
    result = expand_print_shortcodes(text)
    assert "alleen web" not in result
    assert "alleen print" in result
    assert 'class="print-only"' in result


def test_expand_keep_together_scale():
    text = '{{< keep-together scale="70%" >}}\ntekst\n{{< /keep-together >}}\n'
    result = expand_print_shortcodes(text)
    assert 'class="keep-together"' in result
    assert 'style="width: 70%"' in result


def test_markdown_to_print_html_has_print_css_and_headings():
    html = markdown_to_print_html("# Titel\n\n{{< pagebreak >}}\n", title="Demo")
    assert "<title>Demo</title>" in html
    assert "210mm 297mm" in html
    assert "papier: A4" in html
    assert "@page { size: 210mm 297mm;" in html
    assert "page-break-before: always" in html
    assert 'class="pagebreak"' in html
    assert "<h1>Titel</h1>" in html


def test_write_markdown_pdf_renders_vsa_and_pagebreak(tmp_path: Path, monkeypatch):
    source = tmp_path / "liturgie.md"
    source.write_text(
        "---\n"
        "title: Testliturgie\n"
        "---\n\n"
        "### Kop\n\n"
        "{{< pagebreak >}}\n\n"
        ":::pagebreak:::\n\n"
        "::: vsa-notatie\n"
        "[:] {/Hei_}{/lig_} is de Heer. [//:]\n"
        ":::\n",
        encoding="utf-8",
    )
    pdf_path = tmp_path / "out" / "liturgie.pdf"
    html_snapshot = {}

    def capturing_html_to_pdf(html_path, pdf_path, *, chrome_command=None):
        html_snapshot["text"] = Path(html_path).read_text(encoding="utf-8")
        Path(pdf_path).write_bytes(b"%PDF-1.4\n%%EOF\n")

    monkeypatch.setattr("vsa.markdown_pdf.html_file_to_pdf", capturing_html_to_pdf)

    write_markdown_pdf(source, pdf_path, chrome_command=_fake_chrome(tmp_path))

    assert pdf_path.is_file()
    assert pdf_path.read_bytes().startswith(b"%PDF")
    html = html_snapshot["text"]
    assert html.count('class="pagebreak"') >= 2
    assert "vsa-notation" in html
    assert "::: vsa-notatie" not in html



def test_write_markdown_pdf_resolves_markdown_include(tmp_path: Path, monkeypatch):
    (tmp_path / "deel.md").write_text("Ingevoegd stuk.\n", encoding="utf-8")
    source = tmp_path / "hoofd.md"
    source.write_text(':::include "deel.md":::\n', encoding="utf-8")
    html_snapshot = {}

    def capturing_html_to_pdf(html_path, pdf_path, *, chrome_command=None):
        html_snapshot["text"] = Path(html_path).read_text(encoding="utf-8")
        Path(pdf_path).write_bytes(b"%PDF-1.4\n%%EOF\n")

    monkeypatch.setattr("vsa.markdown_pdf.html_file_to_pdf", capturing_html_to_pdf)
    write_markdown_pdf(source, tmp_path / "hoofd.pdf")
    assert "Ingevoegd stuk" in html_snapshot["text"]

    source = tmp_path / "fout.md"
    source.write_text(
        "# Demo\n\n"
        "::: vsa-notatie\n"
        "[:] goede regel\n"
        "{fout/}\n"
        ":::\n",
        encoding="utf-8",
    )
    with pytest.raises(Exception) as caught:
        write_markdown_pdf(
            source,
            tmp_path / "fout.pdf",
            chrome_command=_fake_chrome(tmp_path),
        )
    from vsa.markdown_processor import ProcessValidationError

    assert isinstance(caught.value, ProcessValidationError)
    message = caught.value.messages[0]
    assert message.line == 5
    assert message.column > 1
    assert "fout.md" in Path(message.source).name


def test_cli_pdf_writes_output(tmp_path: Path, monkeypatch, capsys):
    source = tmp_path / "demo.md"
    source.write_text("# Demo\n\nTekst.\n", encoding="utf-8")
    pdf_path = tmp_path / "demo.pdf"

    def fake_html_to_pdf(html_path, pdf_path, *, chrome_command=None):
        Path(pdf_path).write_bytes(b"%PDF-1.4\n%%EOF\n")

    monkeypatch.setattr("vsa.markdown_pdf.html_file_to_pdf", fake_html_to_pdf)

    exit_code = main(["pdf", str(source), "-o", str(pdf_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert pdf_path.is_file()
    assert "PDF geschreven naar:" in captured.out


def test_pdf_resolves_catalogus_id_from_nested_cwd(tmp_path: Path, monkeypatch):
    from test_include_vsa import _write_lokaal_tree

    content = tmp_path / "content-source"
    nested = content / "praktijk" / "samenstellingen"
    nested.mkdir(parents=True)
    _write_lokaal_tree(content)
    source = nested / "liturgie.md"
    source.write_text(
        ':::include svg id:antifoon-1-weekdagen/liturgikon-weekdagen/hemelum '
        'alt="antifoon":::\n',
        encoding="utf-8",
    )
    html_snapshot = {}

    def capturing_html_to_pdf(html_path, pdf_path, *, chrome_command=None):
        html_snapshot["text"] = Path(html_path).read_text(encoding="utf-8")
        Path(pdf_path).write_bytes(b"%PDF-1.4\n%%EOF\n")

    monkeypatch.setattr("vsa.markdown_pdf.html_file_to_pdf", capturing_html_to_pdf)
    monkeypatch.chdir(nested)
    write_markdown_pdf(Path("liturgie.md"), tmp_path / "out.pdf")
    assert "vsa-notation" in html_snapshot["text"]
    assert ":::include" not in html_snapshot["text"]


def test_cli_pdf_validation_error_shows_file_line(tmp_path: Path, capsys):
    source = tmp_path / "fout.md"
    source.write_text(
        "::: vsa-notatie\n"
        "[:] {fout/}\n"
        ":::\n",
        encoding="utf-8",
    )
    exit_code = main(["pdf", str(source), "-o", str(tmp_path / "x.pdf")])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fout.md:" in captured.out or "fout.md:" in captured.err
    assert "VSA-SYNTAX" in captured.out or "VSA-SYNTAX" in captured.err


def test_expand_unclosed_keep_together_raises():
    with pytest.raises(PdfError, match="Niet-gesloten"):
        expand_print_shortcodes("{{< keep-together >}}\ntekst\n")
