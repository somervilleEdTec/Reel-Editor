from __future__ import annotations


def apply_music_bed(
    parts: list[str],
    speech_label: str,
    music_input_idx: int,
    duration_s: float,
    gain_db: float,
    duck_under_speech: bool,
) -> str:
    """Loop/trim music to timeline length, apply gain, optionally duck, mix with speech.

    Returns the new audio label (including brackets), e.g. ``[outa]``.
    """
    dur = max(0.05, float(duration_s))
    gain = float(gain_db)
    music = (
        f"[{music_input_idx}:a]aloop=loop=-1:size=2e+09,"
        f"atrim=0:{_fmt(dur)},asetpts=PTS-STARTPTS,"
        f"volume={_fmt(gain)}dB[mbed]"
    )
    parts.append(music)
    if duck_under_speech:
        parts.append(f"{speech_label}asplit=2[spmain][spsc]")
        parts.append(
            "[mbed][spsc]sidechaincompress="
            "threshold=0.02:ratio=6:attack=200:release=800:level_sc=1[mduck]"
        )
        parts.append(
            "[spmain][mduck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[outa]"
        )
    else:
        parts.append(
            f"{speech_label}[mbed]amix=inputs=2:duration=first:"
            "dropout_transition=0:normalize=0[outa]"
        )
    return "[outa]"


def _fmt(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")
