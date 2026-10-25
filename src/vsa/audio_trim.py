"""Trim trailing silence from MuseScore preview-audio renders.

MuseScore often appends multiple seconds of silence after the last note
(seen as ~8–9 quarter notes at typical tempi). Preview-audio should end
shortly after the last audible sample.
"""

from __future__ import annotations

import shutil
import struct
import subprocess
from array import array
from pathlib import Path

# Keep a short pad so players/encoders do not clip the release hard.
DEFAULT_TRAILING_PAD_MS = 10
# Absolute peak on float32 (−1..1) / scaled PCM. ~−40 dBFS; piano release
# below this counts as silence for preview trim.
DEFAULT_SILENCE_THRESHOLD = 0.01

_FFMPEG_CANDIDATES = (
    Path(r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"),
    Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
)


class AudioTrimError(RuntimeError):
    """Raised when trailing-silence trim or re-encode fails."""


def find_ffmpeg() -> Path | None:
    """Return ``ffmpeg`` on PATH (or a few common Windows locations)."""
    which = shutil.which("ffmpeg")
    if which:
        return Path(which)
    for path in _FFMPEG_CANDIDATES:
        if path.is_file():
            return path
    return None


def require_ffmpeg(*, override: Path | None = None) -> Path:
    """Return ffmpeg path or raise :class:`AudioTrimError`."""
    if override is not None:
        path = Path(override)
        if not path.is_file():
            raise AudioTrimError(f"ffmpeg niet gevonden: {path}")
        return path
    found = find_ffmpeg()
    if found is None:
        raise AudioTrimError(
            "ffmpeg niet gevonden (nodig om preview-audio in te korten na "
            "MuseScore). Installeer ffmpeg en zet het op PATH."
        )
    return found


def last_audible_end_seconds(
    wav_path: Path,
    *,
    threshold: float = DEFAULT_SILENCE_THRESHOLD,
) -> float:
    """Return seconds through the first sample *after* the last audible frame.

    Supports PCM16 (format 1) and IEEE-float32 (format 3, MuseScore default).
    """
    channels, rate, peaks = _frame_peak_envelope(Path(wav_path))
    if rate <= 0 or not peaks:
        raise AudioTrimError(f"Ongeldige WAV: {wav_path}")
    last = -1
    for i in range(len(peaks) - 1, -1, -1):
        if peaks[i] > threshold:
            last = i
            break
    if last < 0:
        return 0.0
    # End of that frame (exclusive next sample index).
    return (last + 1) / float(rate)


def wav_duration_seconds(wav_path: Path) -> float:
    """Return WAV duration in seconds (PCM16 or float32)."""
    _channels, rate, peaks = _frame_peak_envelope(Path(wav_path))
    if rate <= 0:
        raise AudioTrimError(f"Ongeldige WAV: {wav_path}")
    return len(peaks) / float(rate)


def encode_trimmed_audio(
    wav_path: Path,
    out: Path,
    *,
    pad_ms: int = DEFAULT_TRAILING_PAD_MS,
    threshold: float = DEFAULT_SILENCE_THRESHOLD,
    ffmpeg: Path | None = None,
) -> Path:
    """Write ``out`` from ``wav_path``, cutting after last sound + ``pad_ms``."""
    wav_path = Path(wav_path)
    out = Path(out)
    if not wav_path.is_file():
        raise AudioTrimError(f"WAV niet gevonden: {wav_path}")
    end = last_audible_end_seconds(wav_path, threshold=threshold)
    duration = end + max(0, pad_ms) / 1000.0
    if duration <= 0:
        duration = max_audible_fallback(wav_path)
    exe = require_ffmpeg(override=ffmpeg)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    codec_args = _ffmpeg_codec_args(out)
    cmd = [
        str(exe),
        "-y",
        "-i",
        str(wav_path),
        "-t",
        f"{duration:.6f}",
        *codec_args,
        str(out),
    ]
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise AudioTrimError(f"ffmpeg starten mislukt: {exc}") from exc
    if proc.returncode != 0 or not out.is_file():
        detail = (proc.stderr or proc.stdout or "").strip()
        msg = f"ffmpeg schreef geen {out.name} (exit {proc.returncode})"
        if detail:
            msg = f"{msg}: {detail[-500:]}"
        raise AudioTrimError(msg)
    return out


def max_audible_fallback(wav_path: Path) -> float:
    """Whole-file duration when nothing exceeds the silence threshold."""
    return max(0.01, wav_duration_seconds(wav_path))


# LAME VBR: 0 = groot/hoog, 9 = klein/laag. Preview-piano: 5 ≈ 80–100 kbps,
# merkbaar kleiner dan 2, nog helder genoeg om even mee te beluisteren.
_MP3_LAME_Q = "5"
# Vorbis q 4 ≈ vergelijkbare preview-kwaliteit/grootte als mp3 q5.
_OGG_VORBIS_Q = "4"


def _ffmpeg_codec_args(out: Path) -> list[str]:
    suffix = out.suffix.lower()
    if suffix == ".mp3":
        return ["-codec:a", "libmp3lame", "-q:a", _MP3_LAME_Q]
    if suffix == ".ogg":
        return ["-codec:a", "libvorbis", "-q:a", _OGG_VORBIS_Q]
    if suffix == ".wav":
        return ["-codec:a", "pcm_s16le"]
    raise AudioTrimError(f"Onbekend audioformaat voor trim: {out.name}")


def _frame_peak_envelope(wav_path: Path) -> tuple[int, int, list[float]]:
    """Return ``(channels, sample_rate, per-frame peak abs amplitude 0..1)``."""
    data = wav_path.read_bytes()
    if len(data) < 44 or data[0:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise AudioTrimError(f"Geen RIFF/WAVE-bestand: {wav_path}")
    pos = 12
    fmt_tag = channels = rate = bits = 0
    pcm = b""
    while pos + 8 <= len(data):
        chunk_id = data[pos : pos + 4]
        size = struct.unpack_from("<I", data, pos + 4)[0]
        payload_start = pos + 8
        payload_end = payload_start + size
        if payload_end > len(data):
            break
        payload = data[payload_start:payload_end]
        if chunk_id == b"fmt " and size >= 16:
            fmt_tag, channels, rate, _br, _ba, bits = struct.unpack_from(
                "<HHIIHH", payload, 0
            )
        elif chunk_id == b"data":
            pcm = payload
            break
        pos = payload_end + (size % 2)
    if channels < 1 or rate < 1 or not pcm:
        raise AudioTrimError(f"WAV zonder bruikbare audio: {wav_path}")
    if fmt_tag == 3 and bits == 32:
        samples = array("f")
        samples.frombytes(pcm[: len(pcm) - (len(pcm) % 4)])
        return channels, rate, _peaks_from_interleaved(samples, channels)
    if fmt_tag == 1 and bits == 16:
        samples = array("h")
        samples.frombytes(pcm[: len(pcm) - (len(pcm) % 2)])
        peaks: list[float] = []
        n = len(samples) // channels
        scale = 1.0 / 32768.0
        for i in range(n):
            base = i * channels
            peak = 0.0
            for c in range(channels):
                peak = max(peak, abs(samples[base + c]) * scale)
            peaks.append(peak)
        return channels, rate, peaks
    raise AudioTrimError(
        f"Niet-ondersteunde WAV (format={fmt_tag}, bits={bits}): {wav_path}"
    )


def _peaks_from_interleaved(samples: array, channels: int) -> list[float]:
    n = len(samples) // channels
    peaks: list[float] = []
    for i in range(n):
        base = i * channels
        peak = 0.0
        for c in range(channels):
            peak = max(peak, abs(float(samples[base + c])))
        peaks.append(peak)
    return peaks


def write_silent_padded_pcm16_fixture(
    path: Path,
    *,
    rate: int = 44100,
    channels: int = 1,
    tone_ms: int = 100,
    silence_ms: int = 500,
    frequency_hz: float = 440.0,
) -> Path:
    """Write a PCM16 WAV (tone then silence) for unit tests."""
    import math
    import wave

    path = Path(path)
    n_tone = int(rate * tone_ms / 1000)
    n_sil = int(rate * silence_ms / 1000)
    frames = array("h")
    for i in range(n_tone):
        t = i / rate
        sample = int(0.5 * 32767 * math.sin(2 * math.pi * frequency_hz * t))
        for _ in range(channels):
            frames.append(sample)
    for _ in range(n_sil * channels):
        frames.append(0)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(frames.tobytes())
    return path

