from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AssemblyClip(BaseModel):
    id: str
    source_id: str
    in_s: float = 0.0
    word_start_id: int = 0
    word_end_id: int = 0
    fit: Literal["cover", "contain"] = "cover"
    speed: float = 1.0
    mute_source_audio: bool = True
    duration_strategy: Literal["hold", "loop", "slow"] = "hold"


class Assembly(BaseModel):
    narration_source_id: str = ""
    clips: list[AssemblyClip] = Field(default_factory=list)
