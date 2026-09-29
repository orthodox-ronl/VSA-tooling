from dataclasses import dataclass
from pathlib import Path

from .block_parser import parse_markdown_blocks
from .config import VSAConfig
from .include_vsa import prepare_markdown_block_body
from .parser import Parser
from .svg_renderer import SVGRenderer
from .validation_runner import validate_file


class ProcessValidationError(Exception):
    def __init__(self, messages):
        super().__init__("VSA-validatie mislukt.")
        self.messages = messages


@dataclass
class ProcessedBlock:
    source_file: str
    block_index: int
    output_file: str


@dataclass
class ProcessResult:
    blocks: list[ProcessedBlock]


def process_markdown_file(
    input_path: str | Path,
    output_dir: str | Path,
    base_dir: str | Path | None = None,
    validate: bool = True,
    max_line_width: float = 800.0,
    config: VSAConfig | None = None,
) -> ProcessResult:
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    if validate:
        validation = validate_file(input_path, config=config)

        if not validation.ok:
            raise ProcessValidationError(validation.messages)

    text = input_path.read_text(encoding="utf-8")
    blocks = parse_markdown_blocks(text)

    output_dir.mkdir(parents=True, exist_ok=True)

    if base_dir is None:
        relative_stem = input_path.stem
    else:
        relative_path = input_path.relative_to(base_dir).with_suffix("")
        relative_stem = "-".join(relative_path.parts)

    processed = []

    for index, block in enumerate(blocks, start=1):
        if block.kind == "mvsa":
            from .mvsa_musicxml import export_mvsa_to_musicxml
            from .musicxml_package import write_musicxml_output

            output_file = output_dir / f"{relative_stem}-block-{index}.mxl"
            xml = export_mvsa_to_musicxml(
                block.body,
                title=output_file.stem,
                layout="playback",
            )
            write_musicxml_output(output_file, xml)
            processed.append(
                ProcessedBlock(
                    source_file=str(input_path),
                    block_index=index,
                    output_file=str(output_file),
                )
            )
            continue

        expanded_body, _ = prepare_markdown_block_body(
            block.body,
            markdown_path=input_path,
            markdown_text=text,
        )
        output_file = output_dir / f"{relative_stem}-block-{index}.svg"

        renderer = SVGRenderer()
        renderer.max_line_width = max_line_width

        svg = renderer.render_document(block.parse_body(expanded_body))
        output_file.write_text(svg, encoding="utf-8")

        processed.append(
            ProcessedBlock(
                source_file=str(input_path),
                block_index=index,
                output_file=str(output_file),
            )
        )

    return ProcessResult(blocks=processed)


def process_path(
    input_path: str | Path,
    output_dir: str | Path,
    validate: bool = True,
    max_line_width: float = 800.0,
    config: VSAConfig | None = None,
) -> ProcessResult:
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    if input_path.is_file():
        return process_markdown_file(
            input_path,
            output_dir,
            validate=validate,
            max_line_width=max_line_width,
            config=config,
        )

    if not input_path.is_dir():
        raise FileNotFoundError(input_path)

    markdown_files = sorted(
        list(input_path.rglob("*.md")) +
        list(input_path.rglob("*.markdown"))
    )

    if validate:
        all_messages = []

        for markdown_file in markdown_files:
            validation = validate_file(markdown_file, config=config)

            if not validation.ok:
                all_messages.extend(validation.messages)

        if all_messages:
            raise ProcessValidationError(all_messages)

    output_dir.mkdir(parents=True, exist_ok=True)

    all_blocks = []

    for markdown_file in markdown_files:
        result = process_markdown_file(
            markdown_file,
            output_dir,
            base_dir=input_path,
            validate=False,
            max_line_width=max_line_width,
            config=config,
        )

        all_blocks.extend(result.blocks)

    return ProcessResult(blocks=all_blocks)
