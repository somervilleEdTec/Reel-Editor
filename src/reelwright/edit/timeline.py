from __future__ import annotations

from reelwright.edit.edl import Segment


class Timeline:
    """Maps source time to output time using an EDL."""

    def __init__(self, segments: list[Segment]):
        self.segments = segments
        self._spans: list[tuple[Segment, float, float]] = []
        t = 0.0
        for seg in segments:
            dur = max(0.0, seg.out_s - seg.in_s)
            self._spans.append((seg, t, t + dur))
            t += dur
        self.duration_s = t

    def source_to_output(self, source_id: str, source_t: float) -> float | None:
        for seg, o0, o1 in self._spans:
            if seg.source_id != source_id:
                continue
            if seg.in_s <= source_t <= seg.out_s:
                return o0 + (source_t - seg.in_s)
        return None

    def output_to_source(self, output_t: float) -> tuple[str, float] | None:
        for seg, o0, o1 in self._spans:
            if o0 <= output_t <= o1:
                return seg.source_id, seg.in_s + (output_t - o0)
        return None
