from __future__ import annotations

from reelwrite.models.word import Word


def apply_candidate(
    words: list[Word], word_start_id: int, word_end_id: int
) -> list[Word]:
    """Keep only words in [start, end]; delete the rest."""
    out: list[Word] = []
    for w in words:
        keep = word_start_id <= w.id <= word_end_id
        out.append(w.model_copy(update={"deleted": not keep}))
    return out
