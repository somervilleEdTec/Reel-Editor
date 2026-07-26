"""Heuristic diarisation from word speakers / silence gaps."""

from __future__ import annotations

from reelwright.cv.reframe import DiarSegment
from reelwright.models.word import Word


def diarise_from_words(words: list[Word], gap_s: float = 0.8) -> list[DiarSegment]:
    if not words:
        return []
    segs: list[DiarSegment] = []
    cur_spk = words[0].speaker or "S1"
    start = words[0].start_s
    prev_end = words[0].end_s
    for w in words[1:]:
        spk = w.speaker or cur_spk
        if spk != cur_spk or (w.start_s - prev_end) >= gap_s:
            segs.append(DiarSegment(cur_spk, start, prev_end))
            cur_spk = spk
            start = w.start_s
        prev_end = w.end_s
    segs.append(DiarSegment(cur_spk, start, prev_end))
    return segs
