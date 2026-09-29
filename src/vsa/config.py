from dataclasses import dataclass, field
from pathlib import Path
import tomllib


@dataclass
class UpperGlyphConfig:
    width_factor: float = 0.48
    offset_y: float = -20.0 # was -22.0
    stroke_width_factor: float = 0.075
    color: str = "black"


@dataclass
class LowerGlyphConfig:
    width_factor: float = 0.55
    offset_y: float = 5.0 # was 7.0
    stroke_width_factor: float = 0.075
    color: str = "red"


@dataclass
class PitchMarkerConfig:
    width: float = 20.0
    dash_width_factor: float = 0.45
    offset_y: float = -5.0
    ehm_offset_y: float = -12.0

@dataclass
class SVGRenderingConfig:
    font_family: str = "DejaVu Sans"
    font_size: float = 20.0
    line_height: float = 34.0 # was 38.0
    text_gap: float = 0.0
    scope_gap: float = 0.0
    optical_scope_gap: float = 4.0
    pitch_marker_gap: float = 4.0
    margin_x: float = 8.0
    margin_y: float = 8.0
    filler_offset_y: float = -6.0
    upper: UpperGlyphConfig = field(default_factory=UpperGlyphConfig)
    lower: LowerGlyphConfig = field(default_factory=LowerGlyphConfig)
    pitch_marker: PitchMarkerConfig = field(default_factory=PitchMarkerConfig)


@dataclass
class RenderingConfig:
    max_line_width: float = 800.0
    svg: SVGRenderingConfig = field(default_factory=SVGRenderingConfig)


@dataclass
class HugoConfig:
    assets_url_prefix: str = "/vsa"
    output_mode: str = "img"


@dataclass
class ValidationConfig:
    severity: dict[str, str] = field(default_factory=dict)


@dataclass
class AudioConfig:
    """Defaults for ``vsa audio`` / ``mvsa audio`` (preview-luisteren)."""

    format: str = "mp3"


@dataclass
class VSAConfig:
    rendering: RenderingConfig = field(default_factory=RenderingConfig)
    hugo: HugoConfig = field(default_factory=HugoConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)


def load_config(path: str | Path | None = None) -> VSAConfig:
    config = VSAConfig()

    if path is None:
        return config

    path = Path(path)

    if not path.exists():
        return config

    data = tomllib.loads(path.read_text(encoding="utf-8"))

    rendering = data.get("rendering", {})
    hugo = data.get("hugo", {})
    validation = data.get("validation", {})
    audio = data.get("audio", {})

    if "max-line-width" in rendering:
        config.rendering.max_line_width = _positive_float(
            rendering["max-line-width"],
            "rendering.max-line-width",
        )

    _load_svg_rendering_config(config.rendering.svg, rendering.get("svg", {}))

    if "assets-url-prefix" in hugo:
        config.hugo.assets_url_prefix = str(hugo["assets-url-prefix"])

    if "output-mode" in hugo:
        config.hugo.output_mode = _normalize_output_mode(hugo["output-mode"])

    severity = validation.get("severity", {})

    if isinstance(severity, dict):
        config.validation.severity = {
            str(code): _normalize_severity(value)
            for code, value in severity.items()
        }

    if isinstance(audio, dict) and "format" in audio:
        config.audio.format = _normalize_audio_format(audio["format"])

    return config


def _normalize_audio_format(value):
    from .audio_export import AUDIO_FORMATS, AudioExportError, normalize_audio_format

    try:
        return normalize_audio_format(value)
    except AudioExportError as exc:
        raise ValueError(
            f"Onbekend audio.format: {value!r}. "
            f"Gebruik: {', '.join(AUDIO_FORMATS)}."
        ) from exc


def _load_svg_rendering_config(config: SVGRenderingConfig, data: dict):
    if not isinstance(data, dict):
        return

    if "font-family" in data:
        config.font_family = _non_empty_string(data["font-family"], "rendering.svg.font-family")
    if "font-size" in data:
        config.font_size = _positive_float(data["font-size"], "rendering.svg.font-size")
    if "line-height" in data:
        config.line_height = _positive_float(data["line-height"], "rendering.svg.line-height")
    if "text-gap" in data:
        config.text_gap = _non_negative_float(data["text-gap"], "rendering.svg.text-gap")
    if "scope-gap" in data:
        config.scope_gap = _non_negative_float(data["scope-gap"], "rendering.svg.scope-gap")
    if "optical-scope-gap" in data:
        config.optical_scope_gap = _non_negative_float(data["optical-scope-gap"], "rendering.svg.optical-scope-gap")
    if "pitch-marker-gap" in data:
        config.pitch_marker_gap = _non_negative_float(data["pitch-marker-gap"], "rendering.svg.pitch-marker-gap")
    if "margin-x" in data:
        config.margin_x = _non_negative_float(data["margin-x"], "rendering.svg.margin-x")
    if "margin-y" in data:
        config.margin_y = _non_negative_float(data["margin-y"], "rendering.svg.margin-y")
    if "filler-offset-y" in data:
        config.filler_offset_y = float(data["filler-offset-y"])

    glyphs = data.get("glyphs", {})
    if isinstance(glyphs, dict):
        _load_upper_glyph_config(config.upper, glyphs.get("upper", {}))
        _load_lower_glyph_config(config.lower, glyphs.get("lower", {}))

    pitch_marker = data.get("pitch-marker", {})
    if isinstance(pitch_marker, dict):
        _load_pitch_marker_config(config.pitch_marker, pitch_marker)


def _load_upper_glyph_config(config: UpperGlyphConfig, data: dict):
    if not isinstance(data, dict):
        return
    if "width-factor" in data:
        config.width_factor = _positive_float(data["width-factor"], "rendering.svg.glyphs.upper.width-factor")
    if "offset-y" in data:
        config.offset_y = float(data["offset-y"])
    if "stroke-width-factor" in data:
        config.stroke_width_factor = _positive_float(data["stroke-width-factor"], "rendering.svg.glyphs.upper.stroke-width-factor")
    if "color" in data:
        config.color = _non_empty_string(data["color"], "rendering.svg.glyphs.upper.color")


def _load_lower_glyph_config(config: LowerGlyphConfig, data: dict):
    if not isinstance(data, dict):
        return
    if "width-factor" in data:
        config.width_factor = _positive_float(data["width-factor"], "rendering.svg.glyphs.lower.width-factor")
    if "offset-y" in data:
        config.offset_y = float(data["offset-y"])
    if "stroke-width-factor" in data:
        config.stroke_width_factor = _positive_float(data["stroke-width-factor"], "rendering.svg.glyphs.lower.stroke-width-factor")
    if "color" in data:
        config.color = _non_empty_string(data["color"], "rendering.svg.glyphs.lower.color")


def _load_pitch_marker_config(config: PitchMarkerConfig, data: dict):
    if not isinstance(data, dict):
        return
    if "width" in data:
        config.width = _positive_float(data["width"], "rendering.svg.pitch-marker.width")
    if "dash-width-factor" in data:
        config.dash_width_factor = _positive_float(data["dash-width-factor"], "rendering.svg.pitch-marker.dash-width-factor")
    if "offset-y" in data:
        config.offset_y = float(data["offset-y"])


def _normalize_output_mode(value):
    value = str(value).strip().lower()
    if value not in {"img", "shortcode"}:
        raise ValueError(f"Onbekende output-mode: {value}. Gebruik 'img' of 'shortcode'.")
    return value


def _normalize_severity(value):
    value = str(value).strip().lower()
    if value not in {"error", "warning"}:
        raise ValueError(f"Onbekende severity: {value}. Gebruik 'error' of 'warning'.")
    return value


def _positive_float(value, name):
    value = float(value)
    if value <= 0:
        raise ValueError(f"{name} moet groter zijn dan 0.")
    return value


def _non_negative_float(value, name):
    value = float(value)
    if value < 0:
        raise ValueError(f"{name} mag niet negatief zijn.")
    return value


def _non_empty_string(value, name):
    value = str(value).strip()
    if value == "":
        raise ValueError(f"{name} mag niet leeg zijn.")
    return value
