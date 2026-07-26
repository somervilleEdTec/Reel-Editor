from __future__ import annotations

from pydantic import BaseModel


class Captions(BaseModel):
    preset: str = "sticker"
    y: float = 0.60
    max_words_visible: int = 3
    uppercase: bool = True
