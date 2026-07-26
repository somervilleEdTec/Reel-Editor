from __future__ import annotations

from reelwrite.edit.timeline import Timeline
from reelwrite.models.assembly import AssemblyClip
from reelwrite.models.source import Source
from reelwrite.models.word import Word


def clip_output_duration(
    clip: AssemblyClip, words: list[Word], timeline: Timeline
) -> float:
    start_w = next((w for w in words if w.id == clip.word_start_id), None)
    end_w = next((w for w in words if w.id == clip.word_end_id), None)
    if not start_w or not end_w:
        return 0.0
    o0 = timeline.source_to_output(start_w.source_id, start_w.start_s)
    o1 = timeline.source_to_output(end_w.source_id, end_w.end_s)
    if o0 is None or o1 is None:
        return max(0.0, end_w.end_s - start_w.start_s)
    return max(0.0, o1 - o0)


def reconcile(
    clip: AssemblyClip, source: Source, needed_s: float
) -> tuple[AssemblyClip, list[str]]:
    """Return updated clip + warnings for short sources."""
    warnings: list[str] = []
    avail = max(0.01, source.duration_s - clip.in_s)
    if needed_s <= avail:
        return clip, warnings
    strategy = clip.duration_strategy
    if strategy == "slow":
        speed = avail / needed_s
        if speed < 0.5:
            warnings.append(
                f"Clip {clip.id} requires speed {speed:.2f}x (<0.5). Consider hold/loop."
            )
        return clip.model_copy(update={"speed": speed}), warnings
    # hold / loop: keep speed 1.0; ffmpeg holds last frame or loops
    return clip, warnings
