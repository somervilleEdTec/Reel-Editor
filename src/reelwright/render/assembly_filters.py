from __future__ import annotations

from reelwright.assembly.reconcile import clip_output_duration, reconcile
from reelwright.edit.timeline import Timeline
from reelwright.models.assembly import Assembly
from reelwright.models.source import Source
from reelwright.models.word import Word


def build_assembly_filters(
    assembly: Assembly,
    words: list[Word],
    timeline: Timeline,
    source_inputs: dict[str, int],
    sources: dict[str, Source],
    width: int,
    height: int,
    base_video_label: str,
    base_audio_label: str,
) -> tuple[list[str], str, str]:
    parts: list[str] = []
    video_label = base_video_label
    audio_layers = [base_audio_label]
    word_by_id = {w.id: w for w in words}
    for i, clip in enumerate(assembly.clips):
        source = sources.get(clip.source_id)
        input_idx = source_inputs.get(clip.source_id)
        if not source or input_idx is None:
            continue
        needed_s = clip_output_duration(clip, words, timeline)
        if needed_s <= 0:
            continue
        start_s = _clip_start(clip.word_start_id, word_by_id, timeline)
        if start_s is None:
            continue
        reconciled, _ = reconcile(clip, source, needed_s)
        speed = max(0.01, reconciled.speed)
        avail_s = max(0.01, source.duration_s - reconciled.in_s)
        src_slice_s = min(avail_s, max(0.01, needed_s * speed))
        playback_s = src_slice_s / speed
        pad_s = max(0.0, needed_s - playback_s)
        vlabel = _clip_video(
            parts,
            i,
            input_idx,
            source,
            reconciled.in_s,
            src_slice_s,
            needed_s,
            speed,
            pad_s,
            reconciled.duration_strategy,
            reconciled.fit,
            width,
            height,
        )
        outv = f"ov{i}"
        parts.append(
            f"{video_label}{vlabel}overlay=shortest=1:enable='between(t,{_fmt(start_s)},"
            f"{_fmt(start_s + needed_s)})'[{outv}]"
        )
        video_label = f"[{outv}]"
        if reconciled.mute_source_audio or not source.has_audio:
            continue
        alabel = _clip_audio(
            parts, i, input_idx, reconciled.in_s, src_slice_s, needed_s, speed, pad_s
        )
        delayed = f"mixa{i}"
        delay_ms = int(round(start_s * 1000))
        parts.append(f"{alabel}adelay={delay_ms}:all=1[{delayed}]")
        audio_layers.append(f"[{delayed}]")
    audio_label = base_audio_label
    if len(audio_layers) > 1:
        parts.append(
            "".join(audio_layers)
            + f"amix=inputs={len(audio_layers)}:duration=first:dropout_transition=0[asma]"
        )
        audio_label = "[asma]"
    return parts, video_label, audio_label


def _clip_video(
    parts: list[str],
    clip_index: int,
    input_idx: int,
    source: Source,
    in_s: float,
    src_slice_s: float,
    needed_s: float,
    speed: float,
    pad_s: float,
    duration_strategy: str,
    fit: str,
    width: int,
    height: int,
) -> str:
    end_s = in_s + src_slice_s
    chain = [
        f"[{input_idx}:v]trim=start={_fmt(in_s)}:end={_fmt(end_s)}",
        "setpts=PTS-STARTPTS",
    ]
    if abs(speed - 1.0) > 1e-3:
        chain.append(f"setpts=PTS/{_fmt(speed)}")
    if duration_strategy == "loop" and pad_s > 0.01:
        frames = max(1, int(round(src_slice_s * (source.fps or 30))))
        chain.append(f"loop=loop=-1:size={frames}:start=0")
    elif duration_strategy == "hold" and pad_s > 0.01:
        chain.append(f"tpad=stop_mode=clone:stop_duration={_fmt(pad_s)}")
    chain.append(f"trim=duration={_fmt(needed_s)}")
    chain.append(_fit_filter(fit, width, height))
    label = f"bv{clip_index}"
    parts.append(",".join(chain) + f"[{label}]")
    return f"[{label}]"


def _clip_audio(
    parts: list[str],
    clip_index: int,
    input_idx: int,
    in_s: float,
    src_slice_s: float,
    needed_s: float,
    speed: float,
    pad_s: float,
) -> str:
    end_s = in_s + src_slice_s
    chain = [
        f"[{input_idx}:a]atrim=start={_fmt(in_s)}:end={_fmt(end_s)}",
        "asetpts=PTS-STARTPTS",
        *_atempo(speed),
    ]
    if pad_s > 0.01:
        chain.append(f"apad=pad_dur={_fmt(pad_s)}")
    chain.append(f"atrim=duration={_fmt(needed_s)}")
    label = f"ba{clip_index}"
    parts.append(",".join(chain) + f"[{label}]")
    return f"[{label}]"


def _atempo(speed: float) -> list[str]:
    if abs(speed - 1.0) <= 1e-3:
        return []
    remaining = speed
    filters: list[str] = []
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    filters.append(f"atempo={_fmt(remaining)}")
    return filters


def _clip_start(word_id: int, words: dict[int, Word], timeline: Timeline) -> float | None:
    word = words.get(word_id)
    if not word:
        return None
    return timeline.source_to_output(word.source_id, word.start_s)


def _fit_filter(fit: str, width: int, height: int) -> str:
    if fit == "contain":
        return (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,format=yuv420p"
        )
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},setsar=1,format=yuv420p"
    )


def _fmt(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") or "0"
