from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from reelwrite.api import app as app_module
from reelwrite.api.source_ops import EditableRole, add_sources, primary_word_source

router = APIRouter(prefix="/sources")


class AddSourcesBody(BaseModel):
    paths: list[str] = Field(default_factory=list)
    path: str | None = None
    role: EditableRole = "media"


class RemoveSourcesBody(BaseModel):
    ids: list[str] = Field(default_factory=list)
    id: str | None = None


@router.post("/add")
def add_project_sources(body: AddSourcesBody):
    project = app_module._proj()
    paths = body.paths + ([body.path] if body.path else [])
    add_sources(project, paths, body.role)
    app_module._save(project)
    return project.model_dump()


@router.post("/remove")
def remove_project_sources(body: RemoveSourcesBody):
    project = app_module._proj()
    ids = set(body.ids + ([body.id] if body.id else []))
    before = len(project.sources)
    project.sources = [source for source in project.sources if source.id not in ids]
    if project.assembly:
        project.assembly.clips = [
            clip for clip in project.assembly.clips if clip.source_id not in ids
        ]
        if project.assembly.narration_source_id in ids:
            available = {source.id for source in project.sources}
            narration = primary_word_source(project)
            project.assembly.narration_source_id = (
                narration if narration in available else ""
            )
    removed = before - len(project.sources)
    if removed:
        app_module._save(project)
    return project.model_dump()
