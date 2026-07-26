from __future__ import annotations

from reelwright.ingest.zoom_vtt import VttCue, parse_webvtt
from reelwright.models.word import Word


def align_vtt_cues(
    cues: list[VttCue], source_id: str
) -> list[Word]:
    """Distribute phrase text into word timings within each cue span.

    Lightweight force-align approximation (even split). Replace with
    MFA/torchaudio when higher accuracy is required.
    """
    words: list[Word] = []
    wid = 0
    for cue in cues:
        tokens = [t for t in cue.text.split() if t]
        if not tokens:
            continue
        dur = max(0.01, cue.end_s - cue.start_s)
        step = dur / len(tokens)
        for i, tok in enumerate(tokens):
            start = cue.start_s + i * step
            end = start + step
            words.append(
                Word(
                    id=wid,
                    text=tok,
                    start_s=start,
                    end_s=end,
                    speaker=cue.speaker,
                    source_id=source_id,
                )
            )
            wid += 1
    return words


def import_vtt(path: str, source_id: str) -> list[Word]:
    return align_vtt_cues(parse_webvtt(path), source_id)
