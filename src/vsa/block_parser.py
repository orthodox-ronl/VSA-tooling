from dataclasses import dataclass, field
import re
from typing import Literal

from .parser import Parser


END_MARKER = ":::"

# Canonieke openingsregels (na strip); aliassen normaliseren naar kind.
VSA_FENCE_INFOS = frozenset({"vsa-notatie", "vsa"})
MVSA_FENCE_INFOS = frozenset({"mvsa-notatie", "mvsa"})

# Backwards-compat voor imports die de canonieke VSA-fence verwachten.
START_MARKER = "::: vsa-notatie"

NotationKind = Literal["vsa", "mvsa"]


DEFAULT_METADATA = {
    "do": "F4",
    "mode": "major",
    "tempo": "120",
    "validate-ending": "true",
    "duration-model": "default",
    "reciting-mode": "quarters",
    "musicxml-profile": "playback",
    "part-name": "Vocal",
    "midi-sound": "keyboard.piano.grand",
    "midi-channel": "1",
    "midi-program": "1",
    "typografie.lyric-font": "Source Sans 3",
    "typografie.lyric-size": "13",
    "typografie.word-font": "Source Sans 3",
    "typografie.word-size": "12",
}


@dataclass
class MarkdownBlock:
    start_line: int
    end_line: int
    metadata: dict[str, str] = field(default_factory=dict)
    body: str = ""
    kind: NotationKind = "vsa"
    info_string: str = "vsa-notatie"

    def effective_metadata(self):
        result = dict(DEFAULT_METADATA)
        result.update(self.metadata)
        return result

    def parse_body(self, body: str | None = None):
        return Parser(body if body is not None else self.body).parse()


def notation_fence_kind(stripped: str) -> NotationKind | None:
    """Return ``vsa`` / ``mvsa`` for a fence-open line, else ``None``."""
    info = _fence_info_string(stripped)
    if info is None:
        return None
    if info in VSA_FENCE_INFOS:
        return "vsa"
    if info in MVSA_FENCE_INFOS:
        return "mvsa"
    return None


def parse_markdown_blocks(markdown: str):
    lines = markdown.splitlines()
    blocks = []

    index = 0
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

            index += 1
            continue

        kind = None if in_code_fence else notation_fence_kind(stripped)
        if kind is None:
            index += 1
            continue

        info_string = _fence_info_string(stripped) or kind
        start_line = index + 1
        index += 1

        metadata: dict[str, str] = {}
        body_lines: list[str] = []

        while index < len(lines):
            stripped_inner = lines[index].strip()

            if stripped_inner == END_MARKER:
                break

            if kind == "vsa":
                parsed = _parse_metadata_line(stripped_inner)
                if parsed is not None:
                    key, value = parsed
                    metadata[key] = value
                    index += 1
                    continue
            elif kind == "mvsa":
                # Alleen assignment-metadata; ``# …`` is mvsa-commentaar.
                parsed = _parse_assignment_metadata_line(stripped_inner)
                if parsed is not None:
                    key, value = parsed
                    metadata[key] = value
                    index += 1
                    continue

            body_lines.append(lines[index])
            index += 1

        end_line = index + 1 if index < len(lines) else len(lines)

        blocks.append(
            MarkdownBlock(
                start_line=start_line,
                end_line=end_line,
                metadata=metadata,
                body="\n".join(body_lines).strip(),
                kind=kind,
                info_string=info_string,
            )
        )

        index += 1

    return blocks


def _fence_info_string(stripped: str) -> str | None:
    """``::: vsa-notatie`` → ``vsa-notatie``; anders ``None``."""
    if not stripped.startswith(":::"):
        return None
    rest = stripped[3:].strip()
    if not rest:
        return None
    info = rest.split(None, 1)[0]
    if info in VSA_FENCE_INFOS or info in MVSA_FENCE_INFOS:
        return info
    return None


def _parse_metadata_line(line: str):
    if line == "":
        return None

    hash_match = re.match(
        r"^#\s*([A-Za-z0-9_.-]+)\s*:\s*(.*?)\s*$",
        line,
    )

    if hash_match:
        return hash_match.group(1), hash_match.group(2)

    return _parse_assignment_metadata_line(line)


def _parse_assignment_metadata_line(line: str):
    if line == "":
        return None

    assignment_match = re.match(
        r'^([A-Za-z0-9_-]+)\s*=\s*"([^"]*)"\s*$',
        line,
    )

    if assignment_match:
        return assignment_match.group(1), assignment_match.group(2)

    return None


def _opening_or_closing_fence(stripped: str):
    if stripped.startswith("```"):
        return "```"

    if stripped.startswith("~~~"):
        return "~~~"

    return ""


def _closes_fence(stripped: str, fence_marker: str):
    return stripped.startswith(fence_marker)
