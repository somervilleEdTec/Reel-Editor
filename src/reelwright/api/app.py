from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from reelwright.models.project import Project
from reelwright.paths import ensure_vendor_ffmpeg_on_path, ui_web_dir
from reelwright.render.ffmpeg import export_master
from reelwright.security.paths import PathDenied, resolve_workspace_path

ensure_vendor_ffmpeg_on_path()

app = FastAPI(title="Reelwright", version="0.1.0")
# Same-origin UI + optional Tauri/local shells only — never "*".
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=(
        r"https?://(localhost|127\.0\.0\.1|tauri\.localhost)(:\d+)?|"
        r"tauri://localhost|https://tauri\.localhost"
    ),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

from reelwright.api.jobs_routes import router as jobs_router
from reelwright.api.setup_routes import router as setup_router

app.include_router(jobs_router)
app.include_router(setup_router)

_STATE: dict = {"path": "project.json", "project": None}


def _proj() -> Project:
    if _STATE["project"] is None:
        path = _STATE["path"]
        try:
            resolved = resolve_workspace_path(path, must_exist=True)
        except PathDenied as e:
            raise HTTPException(403, str(e)) from e
        except FileNotFoundError:
            raise HTTPException(404, "No project loaded") from None
        _STATE["project"] = Project.load(str(resolved))
    return _STATE["project"]


def _save(p: Project) -> None:
    p.save(_STATE["path"])
    _STATE["project"] = p


def _safe_path(path: str, *, must_exist: bool = False, for_write: bool = False) -> str:
    try:
        return str(
            resolve_workspace_path(path, must_exist=must_exist, for_write=for_write)
        )
    except PathDenied as e:
        raise HTTPException(403, str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(404, "File not found") from e


class OpenBody(BaseModel):
    path: str


class DeleteWordBody(BaseModel):
    word_id: int
    deleted: bool = True


class LayersBody(BaseModel):
    background: Literal["camera", "media"] | None = None
    inset: dict | None = None


class CaptionsBody(BaseModel):
    preset: str | None = None
    y: float | None = None
    max_words_visible: int | None = None
    uppercase: bool | None = None


class ExportBody(BaseModel):
    out: str = "master.mp4"
    aspect: str | None = None


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/project/open")
def open_project(body: OpenBody):
    path = _safe_path(body.path, must_exist=True)
    try:
        project = Project.load(path)
    except (ValidationError, ValueError, OSError) as e:
        raise HTTPException(400, f"Invalid project file: {e}") from e
    _STATE["path"] = path
    _STATE["project"] = project
    return project.model_dump()


@app.get("/project")
def get_project():
    return _proj().model_dump()


@app.post("/words/delete")
def delete_word(body: DeleteWordBody):
    p = _proj()
    found = False
    new_words = []
    for w in p.words:
        if w.id == body.word_id:
            new_words.append(w.model_copy(update={"deleted": body.deleted}))
            found = True
        else:
            new_words.append(w)
    if not found:
        raise HTTPException(404, "word not found")
    p.words = new_words
    _save(p)
    return {"ok": True}


@app.post("/layers")
def update_layers(body: LayersBody):
    p = _proj()
    if body.background:
        p.layers.background = body.background
    if body.inset:
        p.layers.inset = p.layers.inset.model_copy(update=body.inset)
    _save(p)
    return p.layers.model_dump()


@app.post("/captions")
def update_captions(body: CaptionsBody):
    p = _proj()
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    p.captions = p.captions.model_copy(update=data)
    _save(p)
    return p.captions.model_dump()


@app.get("/safezones")
def safezones():
    from importlib import resources
    import json

    ref = resources.files("reelwright").joinpath("config/safezones.json")
    return json.loads(ref.read_text(encoding="utf-8"))


@app.post("/export")
def do_export(body: ExportBody):
    p = _proj()
    out = _safe_path(body.out, for_write=True)
    path = export_master(p, out, aspect=body.aspect)
    return {"out": path}


ui_dir = ui_web_dir()
if ui_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(ui_dir), html=True), name="ui")
