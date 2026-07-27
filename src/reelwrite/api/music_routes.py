from __future__ import annotations

from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from reelwrite.api import app as app_module
from reelwrite.api.source_ops import add_sources
from reelwrite.models.project import AudioSettings
from reelwrite.music.catalog import load_catalog, public_track, track_by_id
from reelwrite.music.library import download_track, list_library, local_path_for

router = APIRouter(prefix="/music")


class UseTrackBody(BaseModel):
    track_id: str


@router.get("/catalog")
def music_catalog(genre: str | None = None):
    data = load_catalog()
    downloaded = {item["id"] for item in list_library()}
    tracks = []
    for track in data.get("tracks") or []:
        if genre and track.get("genre") != genre:
            continue
        tracks.append(public_track(track, downloaded=track.get("id") in downloaded))
    genres = sorted({t.get("genre") or "other" for t in data.get("tracks") or []})
    return {
        "attribution_note": data.get("attribution_note") or "",
        "genres": genres,
        "tracks": tracks,
    }


@router.get("/library")
def music_library():
    return {"tracks": list_library()}


@router.get("/preview/{track_id}")
def music_preview(track_id: str):
    local = local_path_for(track_id)
    if local:
        return FileResponse(local, media_type="audio/mpeg", filename=local.name)
    track = track_by_id(track_id)
    if not track or not track.get("download_url"):
        raise HTTPException(404, "Track not found")
    try:
        client = httpx.Client(follow_redirects=True, timeout=60.0)
        req = client.build_request("GET", track["download_url"])
        resp = client.send(req, stream=True)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Could not stream preview: {exc}") from exc

    def iter_bytes():
        try:
            for chunk in resp.iter_bytes(65536):
                yield chunk
        finally:
            resp.close()
            client.close()

    return StreamingResponse(iter_bytes(), media_type="audio/mpeg")


@router.post("/download")
def music_download(body: UseTrackBody):
    try:
        item = download_track(body.track_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except (httpx.HTTPError, OSError, RuntimeError) as exc:
        raise HTTPException(502, f"Download failed: {exc}") from exc
    return item


@router.post("/use")
def music_use_in_project(body: UseTrackBody):
    """Download (if needed), add as a music source, and set as project music bed."""
    try:
        item = download_track(body.track_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except (httpx.HTTPError, OSError, RuntimeError) as exc:
        raise HTTPException(502, f"Download failed: {exc}") from exc

    project = app_module._proj()
    path = item["path"]
    existing = next(
        (
            s
            for s in project.sources
            if Path(s.path).resolve() == Path(path).resolve()
        ),
        None,
    )
    if existing:
        source = existing
        if source.role != "music":
            source.role = "music"
    else:
        added = add_sources(project, [path], "music")
        source = added[0]

    audio = project.audio.model_dump()
    audio["music_track_id"] = source.id
    project.audio = AudioSettings.model_validate(audio)
    app_module._save(project)
    return {
        "track": item,
        "source": source.model_dump(),
        "audio": project.audio.model_dump(),
        "sources": [s.model_dump() for s in project.sources],
    }
