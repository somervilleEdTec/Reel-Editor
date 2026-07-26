from __future__ import annotations

from reelwright.asr.local_whisper import LocalWhisper
from reelwright.models.word import Word


def punch_in(
    words: list[Word],
    start_id: int,
    end_id: int,
    new_audio_path: str,
    source_id: str,
) -> list[Word]:
    """Replace words in [start_id, end_id] with fresh transcription of new audio."""
    fresh = LocalWhisper().transcribe(new_audio_path, source_id)
    # Re-time relative to original start
    anchor = next((w for w in words if w.id == start_id), None)
    base = anchor.start_s if anchor else 0.0
    offset = fresh[0].start_s if fresh else 0.0
    retimed = []
    for i, w in enumerate(fresh):
        retimed.append(
            w.model_copy(
                update={
                    "id": start_id + i,
                    "start_s": base + (w.start_s - offset),
                    "end_s": base + (w.end_s - offset),
                    "source_id": source_id,
                }
            )
        )
    before = [w for w in words if w.id < start_id]
    after = [w for w in words if w.id > end_id]
    # Reindex after
    merged = before + retimed
    next_id = (merged[-1].id + 1) if merged else 0
    for w in after:
        merged.append(w.model_copy(update={"id": next_id}))
        next_id += 1
    return merged
