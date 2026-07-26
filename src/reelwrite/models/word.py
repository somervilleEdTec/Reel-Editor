from __future__ import annotations

from pydantic import BaseModel


class Word(BaseModel):
    id: int
    text: str
    start_s: float
    end_s: float
    speaker: str | None = None
    source_id: str
    deleted: bool = False
