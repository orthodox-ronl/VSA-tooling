from dataclasses import dataclass, field
import re

from .ast import TextNode, ScopeNode, PitchMarkerNode, PitchTransitionNode
from .scope_layout import build_scope_layout, estimate_text_width
from .spacing_policy import whitespace_width


@dataclass
class WhitespaceNode:
    text: str


@dataclass
class HardBreakNode:
    token: str = "\n"


@dataclass
class LayoutItem:
    node: object
    width: float


@dataclass
class LayoutLine:
    items: list[LayoutItem] = field(default_factory=list)
    width: float = 0.0


@dataclass
class LineLayoutSettings:
    font_size: float = 20.0
    text_gap: float = 0.0
    scope_gap: float = 0.0
    pitch_marker_width: float = 20.0
    pitch_marker_gap: float = 2.0
    font_family: str = "DejaVu Sans"


def split_text_node(node: TextNode):
    text = node.text

    if text == "":
        return []

    text = re.sub(r"[ \t]+(\r\n|\r|\n)", r"\1", text)

    tokens = re.findall(r"\r\n|\r|\n|\s+|[^\s\r\n]+", text)

    result = []

    for token in tokens:
        if token in ("\r\n", "\r", "\n"):
            result.append(HardBreakNode(token=token))
        elif token.isspace():
            result.append(WhitespaceNode(text=token))
        else:
            result.append(TextNode(text=token))

    return result


def iter_layout_nodes(document):
    for node in document.nodes:
        if isinstance(node, PitchTransitionNode):
            # Stille toonhoogte-overgang: geen breedte, geen regelbreuk-effect.
            continue
        if isinstance(node, TextNode):
            yield from split_text_node(node)
        else:
            yield node


def measure_node(node, settings: LineLayoutSettings | None = None):
    settings = settings or LineLayoutSettings()

    if isinstance(node, HardBreakNode):
        return 0.0

    if isinstance(node, WhitespaceNode):
        return whitespace_width(node.text, settings.font_size, settings.font_family)

    if isinstance(node, TextNode):
        return estimate_text_width(
            node.text,
            settings.font_size,
            preserve_whitespace=True,
            font_family=settings.font_family,
        ) + settings.text_gap

    if isinstance(node, ScopeNode):
        return build_scope_layout(
            node,
            text_font_size=settings.font_size,
            font_family=settings.font_family,
        ).width + settings.scope_gap

    if isinstance(node, PitchMarkerNode):
        marker_width = max(
            settings.pitch_marker_width,
            max(len(node.height_modifier), 1) * settings.pitch_marker_width,
        )
        return marker_width + settings.pitch_marker_gap

    return 0.0


def build_lines(
    document,
    max_width: float = 800.0,
    settings: LineLayoutSettings | None = None,
):
    settings = settings or LineLayoutSettings()
    lines = []
    current = LayoutLine()

    for node in iter_layout_nodes(document):
        if isinstance(node, HardBreakNode):
            lines.append(_strip_trailing_whitespace(current))
            current = LayoutLine()
            continue

        width = measure_node(node, settings=settings)

        if (
            current.items
            and current.width + width > max_width
            and _may_break_before(current.items[-1].node, node)
        ):
            lines.append(_strip_trailing_whitespace(current))
            current = LayoutLine()

            if isinstance(node, WhitespaceNode):
                continue

        current.items.append(LayoutItem(node=node, width=width))
        current.width += width

    if current.items or not lines:
        lines.append(_strip_trailing_whitespace(current))

    return lines


def _strip_trailing_whitespace(line: LayoutLine):
    while line.items and isinstance(line.items[-1].node, WhitespaceNode):
        item = line.items.pop()
        line.width -= item.width

    return line


def _may_break_before(previous_node, next_node):
    if isinstance(previous_node, PitchMarkerNode):
        return True

    if isinstance(next_node, PitchMarkerNode):
        return True

    if isinstance(previous_node, WhitespaceNode):
        return True

    if isinstance(next_node, WhitespaceNode):
        return True

    if isinstance(previous_node, ScopeNode) and isinstance(next_node, ScopeNode):
        return _scope_is_plain_word(previous_node) and _scope_is_plain_word(next_node)

    return False


def _scope_is_plain_word(node: ScopeNode):
    return not node.height_modifier and not node.length_modifier
