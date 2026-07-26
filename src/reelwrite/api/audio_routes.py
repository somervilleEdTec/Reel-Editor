from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from reelwrite.api import app as app_module
from reelwrite.models.project import AudioSettings

router = APIRouter()


class AudioBody(BaseModel):
    target_lufs: float | None = None
    music_track_id: str | None = None
    music_gain_db: float | None = None
    duck_under_speech: bool | None = None


@router.post("/audio")
def update_audio(body: AudioBody):
    project = app_module._proj()
    data = project.audio.model_dump()
    changes = body.model_dump(exclude_unset=True)
    changes = {
        key: value
        for key, value in changes.items()
        if value is not None or key == "music_track_id"
    }
    data.update(changes)
    project.audio = AudioSettings.model_validate(data)
    app_module._save(project)
    return project.audio.model_dump()
