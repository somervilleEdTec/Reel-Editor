from __future__ import annotations

from reelwrite.edit.edl import Segment
from reelwrite.models.source import Source


def build_edl_av_filters(
    edl: list[Segment],
    source_inputs: dict[str, int],
    sources: dict[str, Source],
    width: int,
    height: int,
    transition: str,
    transition_s: float,
) -> tuple[list[str], str, str, float]:
    if not edl:
        raise ValueError("EDL must not be empty")
    parts: list[str] = []
    durations = [_dur(seg) for seg in edl]
    for i, seg in enumerate(edl):
        idx = source_inputs[seg.source_id]
        start = _fmt(seg.in_s)
        end = _fmt(seg.out_s)
        parts.append(
            f"[{idx}:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,"
            f"{_cover_filter(width, height)}[v{i}]"
        )
        if sources.get(seg.source_id) and sources[seg.source_id].has_audio:
            parts.append(
                f"[{idx}:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]"
            )
        else:
            parts.append(
                f"anullsrc=r=48000:cl=stereo,atrim=duration={_fmt(durations[i])}[a{i}]"
            )
    fade = _fade_duration(transition, transition_s, durations)
    video_label = _video_timeline(parts, durations, fade)
    audio_label = _audio_timeline(parts, len(edl), fade)
    return parts, video_label, audio_label, _timeline_duration(durations, fade)


def _video_timeline(parts: list[str], durations: list[float], fade: float) -> str:
    if len(durations) == 1:
        return "[v0]"
    if fade <= 0:
        labels = "".join(f"[v{i}]" for i in range(len(durations)))
        parts.append(f"{labels}concat=n={len(durations)}:v=1:a=0[basev]")
        return "[basev]"
    total = durations[0]
    current = "v0"
    for i in range(1, len(durations)):
        offset = max(0.0, total - fade)
        out = f"vx{i}"
        parts.append(
            f"[{current}][v{i}]xfade=transition=fade:duration={_fmt(fade)}:"
            f"offset={_fmt(offset)}[{out}]"
        )
        current = out
        total += durations[i] - fade
    return f"[{current}]"


def _audio_timeline(parts: list[str], n: int, fade: float) -> str:
    if n == 1:
        return "[a0]"
    if fade <= 0:
        labels = "".join(f"[a{i}]" for i in range(n))
        parts.append(f"{labels}concat=n={n}:v=0:a=1[basea]")
        return "[basea]"
    current = "a0"
    for i in range(1, n):
        out = f"ax{i}"
        parts.append(
            f"[{current}][a{i}]acrossfade=d={_fmt(fade)}:c1=tri:c2=tri[{out}]"
        )
        current = out
    return f"[{current}]"


def _fade_duration(transition: str, transition_s: float, durations: list[float]) -> float:
    if transition != "crossfade" or transition_s <= 0 or len(durations) < 2:
        return 0.0
    shortest = min(durations)
    fade = min(max(0.0, transition_s), max(0.0, shortest * 0.45))
    return fade if fade >= 0.01 else 0.0


def _timeline_duration(durations: list[float], fade: float) -> float:
    total = sum(durations)
    if len(durations) < 2 or fade <= 0:
        return total
    return max(0.0, total - fade * (len(durations) - 1))


def _cover_filter(width: int, height: int) -> str:
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},setsar=1,format=yuv420p"
    )


def _dur(seg: Segment) -> float:
    return max(0.0, seg.out_s - seg.in_s)


def _fmt(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") or "0"
