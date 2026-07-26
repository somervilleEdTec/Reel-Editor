from __future__ import annotations

from reelwright.models.assembly import Assembly, AssemblyClip
from reelwright.models.source import Source
from reelwright.models.word import Word


def auto_distribute(
    narration_source_id: str,
    clips: list[Source],
    words: list[Word],
) -> Assembly:
    """Evenly assign imported clips across narration words (import order)."""
    kept = [w for w in words if not w.deleted and w.source_id == narration_source_id]
    if not kept or not clips:
        return Assembly(narration_source_id=narration_source_id, clips=[])
    n = len(clips)
    bucket = max(1, len(kept) // n)
    out: list[AssemblyClip] = []
    for i, src in enumerate(clips):
        start = i * bucket
        end = (i + 1) * bucket - 1 if i < n - 1 else len(kept) - 1
        start = min(start, len(kept) - 1)
        end = max(start, min(end, len(kept) - 1))
        out.append(
            AssemblyClip(
                id=f"clip_{i+1}",
                source_id=src.id,
                in_s=0.0,
                word_start_id=kept[start].id,
                word_end_id=kept[end].id,
                mute_source_audio=True,
                duration_strategy="hold",
            )
        )
    return Assembly(narration_source_id=narration_source_id, clips=out)


def reorder_clips(assembly: Assembly, order: list[str]) -> Assembly:
    by_id = {c.id: c for c in assembly.clips}
    clips = [by_id[i] for i in order if i in by_id]
    if not clips:
        return assembly
    # Reassign word spans proportionally across existing span range
    if not assembly.clips:
        return Assembly(narration_source_id=assembly.narration_source_id, clips=clips)
    w0 = min(c.word_start_id for c in assembly.clips)
    w1 = max(c.word_end_id for c in assembly.clips)
    total = max(1, w1 - w0 + 1)
    bucket = max(1, total // len(clips))
    new: list[AssemblyClip] = []
    for i, c in enumerate(clips):
        start = w0 + i * bucket
        end = w0 + (i + 1) * bucket - 1 if i < len(clips) - 1 else w1
        new.append(c.model_copy(update={"word_start_id": start, "word_end_id": end}))
    return Assembly(narration_source_id=assembly.narration_source_id, clips=new)
