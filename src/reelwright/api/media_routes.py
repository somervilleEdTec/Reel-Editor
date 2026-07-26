"""Serve project source media for the editor preview."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from reelwright.api import app as app_module

router = APIRouter()

_MEDIA_TYPES = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".m4v": "video/x-m4v",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
    ".avi": "video/x-msvideo",
}


def _primary_source(project):
    if project.words:
        sid = next((w.source_id for w in project.words if not w.deleted), None)
        for s in project.sources:
            if s.id == sid:
                return s
    return project.sources[0] if project.sources else None


@router.get("/media/source")
def media_source():
    project = app_module._proj()
    src = _primary_source(project)
    if not src:
        raise HTTPException(404, "No source media in project")
    path = Path(src.path).expanduser().resolve()
    if not path.is_file():
        raise HTTPException(404, f"Media file missing: {path}")
    media = _MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(path, media_type=media, filename=path.name)
