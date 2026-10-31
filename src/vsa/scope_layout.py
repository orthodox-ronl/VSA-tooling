from dataclasses import dataclass

from .parser import HALFTOON_CANONICAL
from .text_metrics import (
    estimate_scope_text_width as _estimate_scope_text_width,
    estimate_text_width as _estimate_text_width,
)


MIN_GLYPH_CELL_WIDTH = 14.0


@dataclass
class ScopeColumn:
    ehm: str
    elm: str
    width: float


@dataclass
class ScopeLayout:
    text: str
    width: float
    columns: list[ScopeColumn]
    text_width: float = 0.0
    filler_width: float = 0.0
    prefix_extra: float = 0.0
    leading_pad: float = 0.0


def build_scope_layout(
    node,
    minimum_column_width: float = MIN_GLYPH_CELL_WIDTH,
    text_font_size: float = 20.0,
    font_family: str = "Segoe UI",
    *,
    leading_safety: bool = True,
    trailing_safety: bool = True,
):
    from .spacing_policy import scope_safety_margin

    hm = node.height_modifier or []
    lm = node.length_modifier or []

    if not hm and not lm:
        hm = ["~"]
        lm = ["~"]
    elif hm and not lm:
        lm = ["~"] * len(hm)
    elif lm and not hm:
        hm = ["~"] * len(lm)

    count = max(len(hm), len(lm), 1)

    if len(hm) == 1 and count > 1:
        hm = hm * count

    if len(lm) == 1 and count > 1:
        lm = lm * count

    text = node.text
    margin = scope_safety_margin(text_font_size)
    # Left pad only when the word starts here (not mid-word). Isolated scopes
    # keep legacy “one trailing margin” via estimate_scope_text_width.
    if leading_safety and not trailing_safety:
        leading_pad = margin
    else:
        leading_pad = 0.0

    text_width = estimate_scope_text_width(
        text,
        text_font_size,
        font_family=font_family,
        leading_safety=leading_safety,
        trailing_safety=trailing_safety,
    )

    if count <= 1:
        base_grid_width = text_width
    else:
        base_grid_width = max(
            text_width + minimum_column_width,
            count * minimum_column_width,
        )

    # Filler width is based on the syllable zone only (before prefix extra).
    filler_width = max(0.0, base_grid_width - text_width)

    # Reserve extra space to the left of the glyph for halftone prefix symbols.
    # This shifts the column centre rightward so the prefix fits inside the column
    # without overflowing into the adjacent scope.
    prefix_count = sum(
        1 for ehm in hm
        if len(ehm) >= 2 and ehm[0] in HALFTOON_CANONICAL
    )
    prefix_extra = round(prefix_count * text_font_size * 0.8, 2) + leading_pad

    grid_width = base_grid_width + prefix_extra
    column_width = grid_width / count

    columns = [
        ScopeColumn(
            ehm=hm[index],
            elm=lm[index],
            width=column_width,
        )
        for index in range(count)
    ]

    return ScopeLayout(
        text=text,
        width=round(grid_width, 2),
        columns=columns,
        text_width=round(text_width, 2),
        filler_width=round(filler_width, 2),
        prefix_extra=prefix_extra,
        leading_pad=leading_pad,
    )


def estimate_scope_text_width(
    text: str,
    font_size: float,
    font_family: str = "Segoe UI",
    *,
    leading_safety: bool = True,
    trailing_safety: bool = True,
):
    return _estimate_scope_text_width(
        text,
        font_size,
        font_family=font_family,
        leading_safety=leading_safety,
        trailing_safety=trailing_safety,
    )


def estimate_text_width(
    text: str,
    font_size: float,
    preserve_whitespace: bool = True,
    font_family: str = "Segoe UI",
):
    return _estimate_text_width(
        text,
        font_size,
        preserve_whitespace=preserve_whitespace,
        font_family=font_family,
    )
