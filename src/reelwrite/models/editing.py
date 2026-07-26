from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel, Field


class Marker(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    t_out_s: float
    label: str = ""


class Title(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str
    start_out_s: float
    end_out_s: float
    y: float = 0.5
    style: dict = Field(default_factory=dict)
