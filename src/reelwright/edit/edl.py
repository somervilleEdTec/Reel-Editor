from __future__ import annotations

from dataclasses import dataclass

from reelwright.models.word import Word


@dataclass
class Segment:
    source_id: str
    in_s: float
    out_s: float


def derive_edl(
    words: list[Word],
    source_duration_s: float | None = None,
    lead_pad: float = 0.06,
    tail_pad: float = 0.12,
    min_gap: float = 0.08,
) -> list[Segment]:
    kept = [w for w in words if not w.deleted]
    if not kept:
        return []
    runs: list[list[Word]] = [[kept[0]]]
    for w in kept[1:]:
        prev = runs[-1][-1]
        if w.source_id == prev.source_id and w.id == prev.id + 1:
            runs[-1].append(w)
        else:
            runs.append([w])
    segs: list[Segment] = []
    for run in runs:
        in_s = max(0.0, run[0].start_s - lead_pad)
        out_s = run[-1].end_s + tail_pad
        if source_duration_s is not None:
            out_s = min(out_s, source_duration_s)
        segs.append(Segment(run[0].source_id, in_s, out_s))
    return _merge(segs, min_gap)


def _merge(segs: list[Segment], min_gap: float) -> list[Segment]:
    if not segs:
        return []
    out = [segs[0]]
    for s in segs[1:]:
        prev = out[-1]
        if s.source_id == prev.source_id and s.in_s - prev.out_s < min_gap:
            out[-1] = Segment(prev.source_id, prev.in_s, max(prev.out_s, s.out_s))
        else:
            out.append(s)
    return out
