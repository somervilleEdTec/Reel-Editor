from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from reelwright.media_formats import (
    DEFAULT_OUTPUT_FORMAT,
    OUTPUT_FORMATS,
    VIDEO_EXTS,
    format_for_ext,
)
from reelwright.models.project import Project
from reelwright.paths import ensure_vendor_ffmpeg_on_path, ui_web_dir
from reelwright.render.ffmpeg import export_master
from reelwright.security.paths import PathDenied, resolve_workspace_path

ensure_vendor_ffmpeg_on_path()

app = FastAPI(title="Reelwright", version="2.0.0")
# Same-origin UI + optional Tauri/local shells only — never "*".
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=(
        r"https?://(localhost|127\.0\.0\.1|tauri\.localhost)(:\d+)?|"
        r"tauri://localhost|https://tauri\.localhost"
    ),
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)

from reelwright.api.assembly_routes import router as assembly_router
from reelwright.api.audio_routes import router as audio_router
from reelwright.api.edit_routes import router as edit_router
from reelwright.api.fs_routes import router as fs_router
from reelwright.api.jobs_routes import router as jobs_router
from reelwright.api.marker_routes import router as marker_router
from reelwright.api.media_routes import router as media_router
from reelwright.api.project_routes import router as project_router
from reelwright.api.rank_routes import router as rank_router
from reelwright.api.setup_routes import router as setup_router
from reelwright.api.snapshot_routes import router as snapshot_router
from reelwright.api.source_routes import router as source_router
from reelwright.api.title_routes import router as title_router

app.include_router(assembly_router)
app.include_router(audio_router)
app.include_router(edit_router)
app.include_router(fs_router)
app.include_router(jobs_router)
app.include_router(marker_router)
app.include_router(media_router)
app.include_router(project_router)
app.include_router(rank_router)
app.include_router(setup_router)
app.include_router(snapshot_router)
app.include_router(source_router)
app.include_router(title_router)

_STATE: dict = {"path": "project.json", "project": None, "undo": [], "redo": []}


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
    from reelwright.api.undo import save_with_undo

    save_with_undo(_STATE, p)


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


class ExportSettingsBody(BaseModel):
    transition: Literal["cut", "crossfade"] | None = None
    transition_s: float | None = None


class ExportBody(BaseModel):
    out: str = "master.mp4"
    aspect: str | None = None
    format: str | None = None


def resolve_export_out(out: str, fmt: str | None) -> tuple[str, str]:
    """Return (safe absolute out path, format key).

    Bare filenames land next to the loaded project.json (not the server cwd).
    The extension is forced to match the chosen format.
    """
    name = (out or "").strip() or "master"
    key = fmt or format_for_ext(Path(name).suffix) or DEFAULT_OUTPUT_FORMAT
    if key not in OUTPUT_FORMATS:
        raise HTTPException(400, f"Unsupported export format: {key}")
    ext = OUTPUT_FORMATS[key]["ext"]
    p = Path(name)
    replaceable = VIDEO_EXTS | {v["ext"] for v in OUTPUT_FORMATS.values()}
    if p.suffix.lower() in replaceable:
        if p.suffix.lower() != ext:
            p = p.with_suffix(ext)
    else:
        p = Path(str(p) + ext)
    if "/" not in str(p) and "\\" not in str(p):
        p = Path(_STATE["path"]).expanduser().resolve().parent / p
    return _safe_path(str(p), for_write=True), key


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/project/open")
def open_project(body: OpenBody):
    from reelwright.api.undo import reset_history

    path = _safe_path(body.path, must_exist=True)
    try:
        project = Project.load(path)
    except (ValidationError, ValueError, OSError) as e:
        raise HTTPException(400, f"Invalid project file: {e}") from e
    _STATE["path"] = path
    _STATE["project"] = project
    reset_history(_STATE)
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


@app.post("/export-settings")
def update_export_settings(body: ExportSettingsBody):
    p = _proj()
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if "transition_s" in data and data["transition_s"] < 0:
        raise HTTPException(400, "transition_s must be non-negative")
    p.export = p.export.model_copy(update=data)
    _save(p)
    return p.export.model_dump()


@app.get("/safezones")
def safezones():
    from importlib import resources
    import json

    ref = resources.files("reelwright").joinpath("config/safezones.json")
    return json.loads(ref.read_text(encoding="utf-8"))


@app.get("/formats")
def formats():
    return {
        "input_exts": sorted(VIDEO_EXTS),
        "output": [
            {"key": k, "ext": v["ext"], "label": v["label"]}
            for k, v in OUTPUT_FORMATS.items()
        ],
        "default": DEFAULT_OUTPUT_FORMAT,
    }


@app.post("/export")
def do_export(body: ExportBody):
    p = _proj()
    out, fmt = resolve_export_out(body.out, body.format)
    path = export_master(p, out, aspect=body.aspect, fmt=fmt)
    return {"out": path, "format": fmt}


ui_dir = ui_web_dir()
if ui_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(ui_dir), html=True), name="ui")
