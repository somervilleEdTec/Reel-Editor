from __future__ import annotations

from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from reelwright.models.assembly import Assembly
from reelwright.models.captions import Captions
from reelwright.models.editing import Marker, Title
from reelwright.models.layers import Layers
from reelwright.models.source import Source
from reelwright.models.word import Word


class AudioSettings(BaseModel):
    target_lufs: float = -14.0
    music_track_id: str | None = None
    music_gain_db: float = -18.0
    duck_under_speech: bool = True


class ExportSettings(BaseModel):
    profile: Literal["portrait_9_16", "landscape_16_9"] = "portrait_9_16"
    width: int = 1080
    height: int = 1920
    fps: int = 30
    transition: Literal["cut", "crossfade"] = "cut"
    transition_s: float = 0.25
    check_platforms: list[str] = Field(
        default_factory=lambda: ["instagram", "tiktok", "youtube"]
    )


class TranscriptImport(BaseModel):
    path: str
    format: Literal["webvtt"] = "webvtt"
    aligned: bool = False


class Project(BaseModel):
    project_id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: int = 1
    sources: list[Source] = Field(default_factory=list)
    words: list[Word] = Field(default_factory=list)
    layers: Layers = Field(default_factory=Layers)
    captions: Captions = Field(default_factory=Captions)
    audio: AudioSettings = Field(default_factory=AudioSettings)
    export: ExportSettings = Field(default_factory=ExportSettings)
    assembly: Assembly | None = None
    transcript_import: TranscriptImport | None = None
    candidates: list[dict] = Field(default_factory=list)
    reframe: dict | None = None
    markers: list[Marker] = Field(default_factory=list)
    titles: list[Title] = Field(default_factory=list)

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, path: str) -> Project:
        with open(path, encoding="utf-8") as f:
            return cls.model_validate_json(f.read())
