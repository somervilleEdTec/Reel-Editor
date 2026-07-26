from __future__ import annotations

from reelwright.models.word import Word
from reelwright.rank.caveats import caveat_warnings


def enumerate_windows(
    words: list[Word], min_s: float = 25.0, max_s: float = 60.0
) -> list[dict]:
    kept = [w for w in words if not w.deleted]
    if not kept:
        return []
    candidates: list[dict] = []
    i = 0
    cid = 0
    while i < len(kept):
        j = i
        while j < len(kept) and (kept[j].end_s - kept[i].start_s) < min_s:
            j += 1
        while j < len(kept) and (kept[j].end_s - kept[i].start_s) <= max_s:
            # Prefer sentence-ish end
            if kept[j].text.endswith((".", "?", "!")) or j == len(kept) - 1:
                break
            j += 1
        if j >= len(kept):
            j = len(kept) - 1
        span = kept[i : j + 1]
        if not span:
            break
        dur = span[-1].end_s - span[0].start_s
        if dur >= min_s * 0.5:
            ws, we = span[0].id, span[-1].id
            candidates.append(
                {
                    "id": f"c{cid}",
                    "word_start_id": ws,
                    "word_end_id": we,
                    "duration_s": dur,
                    "warnings": caveat_warnings(words, ws, we),
                    "scores": None,
                }
            )
            cid += 1
        i = j + 1
    return candidates
