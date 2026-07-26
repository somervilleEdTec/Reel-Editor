from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Role = Literal["camera", "media", "voiceover", "participant"]


class Source(BaseModel):
    id: str
    path: str
    role: Role = "camera"
    duration_s: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 30.0
    has_audio: bool = False
    sample_rate: int | None = None
    rotation: int = 0
