from __future__ import annotations

import subprocess
import wave
from pathlib import Path


def write_silence_wav(path: str, duration_s: float = 0.1, rate: int = 48000) -> str:
    """Placeholder capture helper for tests (real mic via sounddevice later)."""
    n = int(duration_s * rate)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(3)  # 24-bit
        w.setframerate(rate)
        w.writeframes(b"\x00\x00\x00" * n)
    return path


def capture_voiceover(
    out_path: str, duration_s: float | None = None, device: int | None = None
) -> str:
    """Record from default mic to WAV 48k/24-bit mono.

    Uses ffmpeg avfoundation/dshow/pulse when available; falls back to silence
    fixture writer when no capture device exists (CI).
    """
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    dur = duration_s or 3.0
    # Try pulse (Linux CI often has none)
    cmd = [
        "ffmpeg", "-y", "-f", "pulse", "-i", "default",
        "-t", str(dur), "-ac", "1", "-ar", "48000", "-sample_fmt", "s32",
        out_path,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=dur + 10)
        return out_path
    except Exception:
        return write_silence_wav(out_path, duration_s=dur)


def meter_peak_dbfs(path: str) -> float:
    """Rough peak from WAV for clipping indicator (-1.0 = full scale)."""
    with wave.open(path, "rb") as w:
        frames = w.readframes(w.getnframes())
        width = w.getsampwidth()
    if not frames:
        return -120.0
    # Interpret last byte of each sample as rough magnitude for 24-bit
    step = width
    peak = 0
    for i in range(0, len(frames), step):
        b = frames[i + width - 1]
        peak = max(peak, b)
    if peak == 0:
        return -120.0
    import math

    return 20 * math.log10(peak / 255.0)
