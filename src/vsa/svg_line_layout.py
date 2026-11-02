from dataclasses import dataclass, field
import re

from .ast import TextNode, ScopeNode, PitchMarkerNode, PitchTransitionNode
from .scope_layout import build_scope_layout, estimate_text_width
from .scope_spacing import (
    collision_optical_gap,
    leading_safety_for,
    trailing_safety_for,
)
from .spacing_policy import whitespace_width
from .svg_glyphs import SVGGlyphRenderer


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
    pre_gap: float = 0.0
    leading_safety: bool = True
    trailing_safety: bool = True


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
    optical_scope_gap: float = 4.0
    glyphs: SVGGlyphRenderer | None = None
    # Vorm A: meet max(bron, translit) voor wrap + viewBox (§5a / afkap-fix).
    translit: bool = False
    translit_modus: str = "both"


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


def _default_glyphs(settings: LineLayoutSettings) -> SVGGlyphRenderer:
    if settings.glyphs is not None:
        return settings.glyphs
    return SVGGlyphRenderer(unit=max(6.0, settings.font_size * 0.40))


def _translit_second_width(shown: str, settings: LineLayoutSettings) -> float | None:
    """Breedte van de vorm-A-tweede regel, of ``None`` als die niet getoond wordt."""
    if not settings.translit or not shown:
        return None
    from .transliterate import (
        detect_direction,
        modus_allows_direction,
        render_syllable,
    )

    det = detect_direction(shown)
    if not modus_allows_direction(settings.translit_modus, det):
        return None
    out = render_syllable(shown, direction=det)
    if not out or out == shown:
        return None
    return estimate_text_width(
        out,
        settings.font_size,
        preserve_whitespace=True,
        font_family=settings.font_family,
    )


def measure_node(
    node,
    settings: LineLayoutSettings | None = None,
    *,
    previous=None,
    nxt=None,
    previous_previous=None,
):
    settings = settings or LineLayoutSettings()

    if isinstance(node, HardBreakNode):
        return 0.0, 0.0, True, True

    if isinstance(node, WhitespaceNode):
        return (
            whitespace_width(node.text, settings.font_size, settings.font_family),
            0.0,
            True,
            True,
        )

    if isinstance(node, TextNode):
        from .syllabify import display_lyric_text

        shown = display_lyric_text(node.text)
        base = estimate_text_width(
            shown,
            settings.font_size,
            preserve_whitespace=True,
            font_family=settings.font_family,
        )
        second_w = _translit_second_width(shown, settings)
        if second_w is not None:
            base = max(base, second_w)
        return base + settings.text_gap, 0.0, True, True

    if isinstance(node, ScopeNode):
        from .syllabify import display_lyric_text

        lead = leading_safety_for(previous)
        trail = trailing_safety_for(nxt)
        layout = build_scope_layout(
            node,
            text_font_size=settings.font_size,
            font_family=settings.font_family,
            leading_safety=lead,
            trailing_safety=trail,
        )
        body = layout.width + settings.scope_gap
        shown = display_lyric_text(layout.text)
        second_w = _translit_second_width(shown, settings)
        if second_w is not None:
            # Zelfde width_extra als svg_renderer._render_scope (vorm A-kolom).
            body += max(0.0, second_w - layout.text_width)
        pre_gap = 0.0
        if isinstance(previous, ScopeNode):
            # Pair layouts must match how each scope was (or will be) measured:
            # previous's trailing edge abuts this scope → no trailing safety;
            # this scope's leading edge abuts previous → no leading safety.
            pre_gap = collision_optical_gap(
                previous,
                node,
                glyphs=_default_glyphs(settings),
                font_size=settings.font_size,
                font_family=settings.font_family,
                configured_gap=settings.optical_scope_gap,
                left_leading_safety=leading_safety_for(previous_previous),
                left_trailing_safety=False,
                right_leading_safety=False,
                right_trailing_safety=trail,
            )
        return body, pre_gap, lead, trail

    if isinstance(node, PitchMarkerNode):
        marker_width = max(
            settings.pitch_marker_width,
            max(len(node.height_modifier), 1) * settings.pitch_marker_width,
        )
        return marker_width + settings.pitch_marker_gap, 0.0, True, True

    return 0.0, 0.0, True, True


def build_lines(
    document,
    max_width: float = 800.0,
    settings: LineLayoutSettings | None = None,
):
    settings = settings or LineLayoutSettings()
    nodes = list(iter_layout_nodes(document))
    lines = []
    current = LayoutLine()

    for index, node in enumerate(nodes):
        if isinstance(node, HardBreakNode):
            lines.append(_strip_trailing_whitespace(current))
            current = LayoutLine()
            continue

        previous = nodes[index - 1] if index > 0 else None
        if isinstance(previous, HardBreakNode):
            previous = None
        previous_previous = nodes[index - 2] if index > 1 else None
        if isinstance(previous_previous, HardBreakNode):
            previous_previous = None
        nxt = nodes[index + 1] if index + 1 < len(nodes) else None
        if isinstance(nxt, HardBreakNode):
            nxt = None

        width, pre_gap, lead, trail = measure_node(
            node,
            settings=settings,
            previous=previous,
            nxt=nxt,
            previous_previous=previous_previous,
        )
        advance = width + pre_gap

        if (
            current.items
            and current.width + advance > max_width
            and _may_break_before(current.items[-1].node, node)
        ):
            lines.append(_strip_trailing_whitespace(current))
            current = LayoutLine()

            if isinstance(node, WhitespaceNode):
                continue

            # Recalculate pre_gap: previous scope may now be on the previous line.
            # Optical gap still applies at render across lines? No — new line start.
            # Word-internal wrap between scopes is rare; drop pre_gap at line start.
            pre_gap = 0.0
            advance = width

        current.items.append(
            LayoutItem(
                node=node,
                width=width,
                pre_gap=pre_gap,
                leading_safety=lead,
                trailing_safety=trail,
            )
        )
        current.width += advance

    if current.items or not lines:
        lines.append(_strip_trailing_whitespace(current))

    return lines


def _strip_trailing_whitespace(line: LayoutLine):
    while line.items and isinstance(line.items[-1].node, WhitespaceNode):
        item = line.items.pop()
        line.width -= item.width + item.pre_gap

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
