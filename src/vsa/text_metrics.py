from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


NARROW_CHARS = set("ijlI.,;:!|'`´’‘")
WIDE_CHARS = set("mwMW@#%&")
SPACE_CHARS = set(" \t")
DIGIT_CHARS = set("0123456789")


@dataclass(frozen=True)
class FontMetrics:
    backend: str
    font_family: str
    font_size: float
    ascent: float
    descent: float
    font_path: str | None = None


DEFAULT_FONT_FAMILY = "DejaVu Sans"
DEFAULT_FONT_SIZE = 20.0
PROJECT_FONT_PATH = Path("assets/fonts/DejaVuSans.ttf")


def estimate_text_width(
    text: str,
    font_size: float,
    preserve_whitespace: bool = True,
    font_family: str = DEFAULT_FONT_FAMILY,
) -> float:
    if text == "":
        return 0.0

    visible = text if preserve_whitespace else text.strip()

    if visible == "":
        return 0.0

    measured = _measure_with_pillow(visible, font_family=font_family, font_size=font_size)

    if measured is not None:
        return measured

    return _estimate_text_width_by_letter_classes(visible, font_size)


def estimate_scope_text_width(
    text: str,
    font_size: float,
    font_family: str = DEFAULT_FONT_FAMILY,
    *,
    leading_safety: bool = True,
    trailing_safety: bool = True,
) -> float:
    """Bare syllable width plus optional edge safety pads (C).

    Text is left-aligned in the syllable zone; only ``trailing_safety`` widens
    that zone to the right. ``leading_safety`` is applied in
    :func:`vsa.scope_layout.build_scope_layout` as a left pad (not here), so
    callers that only need the historical “text + margin” width for an
    isolated scope should pass both flags True — this function then adds the
    full margin on the trailing side (same total as before).
    """
    if text == "":
        return round(max(4.0, font_size * 0.25), 2)

    # Import here to avoid circular import at module load time.
    from .spacing_policy import scope_safety_margin

    margin = scope_safety_margin(font_size)
    bare = estimate_text_width(text, font_size, font_family=font_family)
    # Isolated scope: one full margin (legacy). Mid-word: none. Word-end only:
    # trailing margin. Word-start only: bare here; left pad added in layout.
    if leading_safety and trailing_safety:
        extra = margin
    elif trailing_safety:
        extra = margin
    else:
        extra = 0.0

    return round(max(4.0, bare + extra), 2)


def get_font_metrics(
    font_size: float = DEFAULT_FONT_SIZE,
    font_family: str = DEFAULT_FONT_FAMILY,
) -> FontMetrics:
    font_info = _get_pillow_font_info(font_family=font_family, font_size=font_size)

    if font_info is not None:
        font, font_path = font_info
        try:
            ascent, descent = font.getmetrics()
        except Exception:
            ascent = font_size * 0.80
            descent = font_size * 0.20

        return FontMetrics(
            backend="pillow",
            font_family=font_family,
            font_size=font_size,
            ascent=float(ascent),
            descent=float(descent),
            font_path=str(font_path) if font_path else None,
        )

    return FontMetrics(
        backend="fallback",
        font_family=font_family,
        font_size=font_size,
        ascent=round(font_size * 0.80, 2),
        descent=round(font_size * 0.20, 2),
        font_path=None,
    )


def using_real_font_metrics(
    font_size: float = DEFAULT_FONT_SIZE,
    font_family: str = DEFAULT_FONT_FAMILY,
) -> bool:
    return _get_pillow_font_info(font_family=font_family, font_size=font_size) is not None


def _measure_with_pillow(text: str, font_family: str, font_size: float) -> float | None:
    font_info = _get_pillow_font_info(font_family=font_family, font_size=font_size)

    if font_info is None:
        return None

    font, _font_path = font_info

    try:
        from PIL import Image, ImageDraw

        image = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(image)
        return round(float(draw.textlength(text, font=font)), 2)
    except Exception:
        return None


@lru_cache(maxsize=64)
def _get_pillow_font_info(font_family: str, font_size: float):
    try:
        from PIL import ImageFont
    except Exception:
        return None

    font_size_int = max(1, int(round(font_size)))

    for candidate in _font_candidates(font_family):
        try:
            if isinstance(candidate, Path) and candidate.exists():
                return ImageFont.truetype(str(candidate), font_size_int), candidate
        except Exception:
            continue

    for candidate in _font_name_candidates(font_family):
        try:
            return ImageFont.truetype(candidate, font_size_int), candidate
        except Exception:
            continue

    return None


def _font_candidates(font_family: str) -> list[Path]:
    family = font_family.lower().replace(" ", "")

    windows_fonts = Path("C:/Windows/Fonts")

    candidates: list[Path] = []

    if "dejavu" in family:
        candidates.extend([
            PROJECT_FONT_PATH,
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
            Path("/usr/local/share/fonts/DejaVuSans.ttf"),
            windows_fonts / "DejaVuSans.ttf",
        ])

    if "segoe" in family:
        candidates.append(windows_fonts / "segoeui.ttf")

    if "arial" in family:
        candidates.append(windows_fonts / "arial.ttf")

    candidates.extend([
        PROJECT_FONT_PATH,
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        windows_fonts / "DejaVuSans.ttf",
        windows_fonts / "arial.ttf",
        windows_fonts / "segoeui.ttf",
    ])

    return candidates


def _font_name_candidates(font_family: str) -> list[str]:
    candidates = [font_family]

    if font_family != DEFAULT_FONT_FAMILY:
        candidates.append(DEFAULT_FONT_FAMILY)

    candidates.extend([
        "DejaVuSans.ttf",
        "DejaVu Sans",
        "Arial",
        "Segoe UI",
    ])

    return candidates


def _estimate_text_width_by_letter_classes(text: str, font_size: float) -> float:
    units = 0.0

    for char in text:
        units += _char_width_units(char)

    return round(max(0.0, units * font_size), 2)


def _char_width_units(char: str) -> float:
    if char in SPACE_CHARS:
        return 0.36

    if char in NARROW_CHARS:
        return 0.28

    if char in WIDE_CHARS:
        return 0.78

    if char in DIGIT_CHARS:
        return 0.55

    if char.isupper():
        return 0.62

    if char in "-_/\\()[]{}":
        return 0.42

    return 0.52
