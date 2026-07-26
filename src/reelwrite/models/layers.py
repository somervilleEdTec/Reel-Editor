from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Inset(BaseModel):
    x: float = 0.06
    y: float = 0.52
    w: float = 0.50
    corner_radius_px: int = 12
    border_px: int = 0


class Layers(BaseModel):
    background: Literal["camera", "media"] = "media"
    inset: Inset = Field(default_factory=Inset)
    # Preview framing pan (0–1 → object-position); export still uses cover unless reframe runs.
    pan_x: float = 0.5
    pan_y: float = 0.5
