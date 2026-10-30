from pathlib import Path

from .atomic_io import write_text
from .parser import Parser
from .svg_renderer import SVGRenderer


def export_svg(input_path: str, output_path: str, max_line_width: float = 800.0):
    text = Path(input_path).read_text(encoding="utf-8")

    document = Parser(text).parse()

    renderer = SVGRenderer()
    renderer.max_line_width = max_line_width

    svg = renderer.render_document(document)

    write_text(Path(output_path), svg, encoding="utf-8")
