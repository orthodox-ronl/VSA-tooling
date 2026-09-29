from __future__ import annotations

from dataclasses import dataclass
import re

from .markdown_newline_policy import preserve_vsa_source_newlines


@dataclass(frozen=True)
class VSAMarkdownBlock:
    info_string: str
    source: str


VSA_FENCE_RE = re.compile(
    r"(?P<fence>^```+\s*(?P<codeinfo>(?:m?vsa)(?:-notatie)?)\s*$"
    r"|^:::\s*(?P<coloninfo>(?:m?vsa)(?:-notatie)?)\s*$)"
    r"(?P<body>.*?)"
    r"(?P<close>^```+\s*$|^:::\s*$)",
    re.MULTILINE | re.DOTALL,
)


def normalize_newlines_preserving_line_boundaries(text: str) -> str:
    return preserve_vsa_source_newlines(text)


def extract_vsa_blocks_preserving_newlines(markdown: str) -> list[VSAMarkdownBlock]:
    blocks: list[VSAMarkdownBlock] = []

    for match in VSA_FENCE_RE.finditer(markdown):
        info = match.group("codeinfo") or match.group("coloninfo") or "vsa"
        body = match.group("body")

        if body.startswith("\r\n"):
            body = body[2:]
        elif body.startswith("\n") or body.startswith("\r"):
            body = body[1:]

        if body.endswith("\r\n"):
            body = body[:-2]
        elif body.endswith("\n") or body.endswith("\r"):
            body = body[:-1]

        blocks.append(
            VSAMarkdownBlock(
                info_string=info,
                source=preserve_vsa_source_newlines(body),
            )
        )

    return blocks
