from xml.sax.saxutils import escape

from .ast import TextNode, ScopeNode, PitchMarkerNode
from .config import SVGRenderingConfig
from .svg_glyphs import SVGGlyphRenderer, _split_ehm_token
from .scope_layout import build_scope_layout, estimate_text_width
from .spacing_policy import filler_line_geometry, whitespace_width
from .svg_line_layout import (
    LineLayoutSettings,
    WhitespaceNode,
    build_lines,
)
from .syllabify import display_lyric_text
# Optical gap is decided in line layout (collision-based); renderer applies item.pre_gap.


class SVGRenderer:
    def __init__(
        self,
        svg_config: SVGRenderingConfig | None = None,
        *,
        translit: bool = False,
        translit_modus: str = "both",
    ):
        self.svg_config = svg_config or SVGRenderingConfig()
        self.translit = bool(translit)
        from .transliterate import normalize_translit_modus

        self.translit_modus = normalize_translit_modus(translit_modus)

        self.font_family = self.svg_config.font_family
        self.font_size = self.svg_config.font_size

        self.glyphs = SVGGlyphRenderer(
            unit=max(6.0, self.font_size * 0.40),
            upper_width_factor=self.svg_config.upper.width_factor,
            lower_width_factor=self.svg_config.lower.width_factor,
            upper_stroke_width_factor=self.svg_config.upper.stroke_width_factor,
            lower_stroke_width_factor=self.svg_config.lower.stroke_width_factor,
            upper_color=self.svg_config.upper.color,
            lower_color=self.svg_config.lower.color,
        )

        self.left_margin = self.svg_config.margin_x
        self.top_margin = self.svg_config.margin_y
        self.line_height = self.svg_config.line_height
        self.max_line_width = 800.0

        self.text_gap = self.svg_config.text_gap
        self.scope_gap = self.svg_config.scope_gap
        self.optical_scope_gap = self.svg_config.optical_scope_gap
        self.pitch_marker_gap = self.svg_config.pitch_marker_gap
        # Vorm A: tweede tekstregel onder de bron (§5a).
        self._translit_row_dy = self.font_size * 1.05 if self.translit else 0.0

    def _translit_line(self, shown: str) -> str | None:
        """Tweede regel of ``None`` als modus/schrift geen omzetting geeft."""
        if not self.translit or not shown:
            return None
        from .transliterate import (
            detect_direction,
            modus_allows_direction,
            render_syllable,
        )

        det = detect_direction(shown)
        if not modus_allows_direction(self.translit_modus, det):
            return None
        out = render_syllable(shown, direction=det)
        if not out or out == shown:
            return None
        return out

    def render_document(self, document):
        line_settings = LineLayoutSettings(
            font_size=self.font_size,
            text_gap=self.text_gap,
            scope_gap=self.scope_gap,
            pitch_marker_width=self.svg_config.pitch_marker.width,
            pitch_marker_gap=self.pitch_marker_gap,
            font_family=self.font_family,
            optical_scope_gap=self.optical_scope_gap,
            glyphs=self.glyphs,
            translit=self.translit,
            translit_modus=self.translit_modus,
        )
        lines = build_lines(document, self.max_line_width, settings=line_settings)

        width = self.left_margin * 2 + max((line.width for line in lines), default=0)
        width = max(width, 60.0)

        extra_top = self._compute_extra_top(lines)
        row_h = self.line_height + self._translit_row_dy
        height = self.top_margin * 2 + len(lines) * row_h + extra_top
        height = max(height, 55.0)

        parts = [
            f'<svg class="vsa-svg" xmlns="http://www.w3.org/2000/svg" '
            f'width="{width:.0f}" height="{height:.0f}" '
            f'viewBox="0 0 {width:.0f} {height:.0f}">',
            '<rect width="100%" height="100%" fill="white"/>',
            '<g class="vsa-score">',
        ]

        for line_index, line in enumerate(lines):
            x = self.left_margin
            baseline_y = self.top_margin + extra_top + 28 + (line_index * row_h)

            parts.append(f'<g class="vsa-line" data-vsa-line="{line_index + 1}">')

            for item_index, item in enumerate(line.items, start=1):
                node = item.node
                x += item.pre_gap

                if isinstance(node, WhitespaceNode):
                    x = self._render_whitespace(node, x)

                elif isinstance(node, TextNode):
                    x = self._render_text(parts, node.text, x, baseline_y, item_index)

                elif isinstance(node, ScopeNode):
                    x = self._render_scope(
                        parts,
                        node,
                        x,
                        baseline_y,
                        item_index,
                        leading_safety=item.leading_safety,
                        trailing_safety=item.trailing_safety,
                    )

                elif isinstance(node, PitchMarkerNode):
                    x = self._render_pitch_marker(parts, node, x, baseline_y, item_index)

            parts.append("</g>")

        parts.append("</g>")
        parts.append("</svg>")
        return "\n".join(parts)

    def _compute_extra_top(self, lines) -> float:
        """Extra top padding so the highest stacked glyph tip stays above y=0."""
        max_stack = 1
        for line in lines:
            for item in line.items:
                node = item.node
                if isinstance(node, ScopeNode):
                    ehm_values = node.height_modifier
                elif isinstance(node, PitchMarkerNode):
                    ehm_values = node.height_modifier
                else:
                    continue
                for value in ehm_values:
                    if not value:
                        continue
                    _, base = _split_ehm_token(value)
                    if base and len(set(base)) == 1 and set(base) <= {"/", "\\"}:
                        max_stack = max(max_stack, len(base))

        if max_stack <= 1:
            return 0.0

        unit = self.glyphs.unit
        stack_gap = max(3.0, unit * 0.46)
        # Worst-case half-height matching the cap in _render_base_ehm
        max_half_height = (unit * 1.35 / 2) * 0.45
        # Y of the lowest-indexed (bottom) slash for line 0
        upper_y_line0 = self.top_margin + 28 + self.svg_config.upper.offset_y
        # Top endpoint of the highest slash
        highest_point = upper_y_line0 - (max_stack - 1) * stack_gap - max_half_height
        # Push it to y=2 to leave room for the stroke half-width
        return max(0.0, 2.0 - highest_point)

    def render(self, positions):
        from .ast import Document, ScopeNode

        nodes = [
            ScopeNode(
                height_modifier=[position.ehm],
                text=position.text,
                length_modifier=[position.elm],
            )
            for position in positions
        ]

        return self.render_document(Document(nodes=nodes))

    def _render_whitespace(self, node, x):
        return x + whitespace_width(node.text, self.font_size, self.font_family)

    def _render_text(self, parts, text, x, baseline_y, item_index):
        if text == "":
            return x

        shown = display_lyric_text(text)
        second = self._translit_line(shown)
        parts.append(f'<g class="vsa-unit vsa-unit-text" data-vsa-unit="{item_index}">')
        parts.append(
            f'<text class="vsa-text vsa-free-text" x="{x:.2f}" y="{baseline_y:.2f}" '
            f'xml:space="preserve" '
            f'font-family="{escape(self.font_family)}" font-size="{self.font_size:.2f}">'
            f'{escape(shown)}</text>'
        )
        w = estimate_text_width(
            shown,
            self.font_size,
            preserve_whitespace=True,
            font_family=self.font_family,
        )
        if second is not None:
            parts.append(
                f'<text class="vsa-text vsa-free-text vsa-translit-text" '
                f'x="{x:.2f}" y="{baseline_y + self._translit_row_dy:.2f}" '
                f'xml:space="preserve" '
                f'font-family="{escape(self.font_family)}" '
                f'font-size="{self.font_size:.2f}">'
                f'{escape(second)}</text>'
            )
            w = max(
                w,
                estimate_text_width(
                    second,
                    self.font_size,
                    preserve_whitespace=True,
                    font_family=self.font_family,
                ),
            )
        parts.append("</g>")

        return x + w + self.text_gap

    def _render_scope(
        self,
        parts,
        node,
        x,
        baseline_y,
        item_index,
        *,
        leading_safety: bool = True,
        trailing_safety: bool = True,
    ):
        layout = build_scope_layout(
            node,
            text_font_size=self.font_size,
            font_family=self.font_family,
            leading_safety=leading_safety,
            trailing_safety=trailing_safety,
        )
        shown = display_lyric_text(layout.text)
        second = self._translit_line(shown)
        translit_dy = self._translit_row_dy if second is not None else 0.0
        upper_y = baseline_y + self.svg_config.upper.offset_y
        lower_y = baseline_y + self.svg_config.lower.offset_y + translit_dy
        filler_y = baseline_y + self.svg_config.filler_offset_y

        # x_syllable is where the syllable text (and ELM) begins.
        # When a halftone prefix is present, x_syllable is shifted right
        # so the ELM stays centered under the syllable text while the
        # prefix symbol occupies the reserved space to the left.
        x_syllable = x + layout.prefix_extra

        second_w = 0.0
        if second is not None:
            second_w = estimate_text_width(
                second,
                self.font_size,
                preserve_whitespace=True,
                font_family=self.font_family,
            )
        width_extra = max(0.0, second_w - layout.text_width)
        total_width = layout.width + width_extra

        parts.append(f'<g class="vsa-unit vsa-unit-scope" data-vsa-unit="{item_index}">')

        # Vorm A-kolom: EHM → bron → translit → ELM.
        parts.append(
            f'<text class="vsa-text vsa-sung-text" x="{x_syllable:.2f}" y="{baseline_y:.2f}" '
            f'xml:space="preserve" '
            f'font-family="{escape(self.font_family)}" font-size="{self.font_size:.2f}">'
            f'{escape(shown)}</text>'
        )
        if second is not None:
            parts.append(
                f'<text class="vsa-text vsa-sung-text vsa-translit-text" '
                f'x="{x_syllable:.2f}" y="{baseline_y + translit_dy:.2f}" '
                f'xml:space="preserve" '
                f'font-family="{escape(self.font_family)}" '
                f'font-size="{self.font_size:.2f}">'
                f'{escape(second)}</text>'
            )

        if layout.filler_width > 2.0:
            start = x_syllable + layout.text_width + 1.0
            end = x + layout.width - 3.0
            draw_start, draw_end = filler_line_geometry(start, end, layout.filler_width, self.font_size)
            if draw_end > draw_start:
                parts.append(
                    f'<line class="vsa-filler-line" '
                    f'x1="{draw_start:.2f}" y1="{filler_y:.2f}" '
                    f'x2="{draw_end:.2f}" y2="{filler_y:.2f}" '
                    f'stroke="black" stroke-width="0.75" stroke-linecap="round"/>'
                )

        # EHM: runs from x (full column width includes the prefix zone).
        parts.append('<g class="vsa-glyph-group vsa-upper-glyphs">')
        running_x = x
        col_scale = total_width / layout.width if layout.width else 1.0
        for column in layout.columns:
            col_w = column.width * col_scale
            parts.extend(
                self.glyphs.render_height_modifier(
                    [column.ehm], running_x, upper_y, col_w
                )
            )
            running_x += col_w
        parts.append("</g>")

        # ELM: under translit-regel (of bron als geen tweede regel).
        parts.append('<g class="vsa-glyph-group vsa-lower-glyphs">')
        elm_zone = total_width - layout.prefix_extra
        elm_col_width = elm_zone / len(layout.columns)
        running_x = x_syllable
        for column in layout.columns:
            parts.extend(
                self.glyphs.render_length_modifier(
                    [column.elm], running_x, lower_y, elm_col_width
                )
            )
            running_x += elm_col_width
        parts.append("</g>")

        parts.append("</g>")
        return x + total_width + self.scope_gap

    def _render_pitch_marker(self, parts, node, x, baseline_y, item_index):
        width = max(
            self.svg_config.pitch_marker.width,
            max(len(node.height_modifier), 1) * self.svg_config.pitch_marker.width,
        )

        parts.append(f'<g class="vsa-unit vsa-pitch-marker" data-vsa-unit="{item_index}">')

        if node.height_modifier:
            column_width = width / len(node.height_modifier)
            parts.append('<g class="vsa-pitch-marker-upper-glyph vsa-upper-glyphs">')
            for index, ehm in enumerate(node.height_modifier):
                parts.extend(
                    self.glyphs.render_height_modifier(
                        [ehm],
                        x + index * column_width,
                        baseline_y + self.svg_config.pitch_marker.ehm_offset_y,
                        column_width,
                    )
                )
            parts.append("</g>")

        dash_width = width * self.svg_config.pitch_marker.dash_width_factor
        dash_start = x + (width - dash_width) / 2
        dash_end = dash_start + dash_width
        dash_y = baseline_y + self.svg_config.pitch_marker.offset_y

        parts.append(
            f'<line class="vsa-pitch-marker-dash" '
            f'x1="{dash_start:.2f}" y1="{dash_y:.2f}" '
            f'x2="{dash_end:.2f}" y2="{dash_y:.2f}" '
            f'stroke="black" stroke-width="1.50" stroke-linecap="round"/>'
        )
        parts.append("</g>")

        return x + width + self.pitch_marker_gap

