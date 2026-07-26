from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from reelwright.models.project import Project
from reelwright.render.ffmpeg import export_master

app = FastAPI(title="Reelwright", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from reelwright.api.jobs_routes import router as jobs_router

app.include_router(jobs_router)

_STATE: dict = {"path": "project.json", "project": None}


def _proj() -> Project:
    if _STATE["project"] is None:
        path = _STATE["path"]
        if not Path(path).exists():
            raise HTTPException(404, "No project loaded")
        _STATE["project"] = Project.load(path)
    return _STATE["project"]


def _save(p: Project) -> None:
    p.save(_STATE["path"])
    _STATE["project"] = p


class OpenBody(BaseModel):
    path: str


class DeleteWordBody(BaseModel):
    word_id: int
    deleted: bool = True


class LayersBody(BaseModel):
    background: str | None = None
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
    if not Path(body.path).exists():
        raise HTTPException(404, "File not found")
    _STATE["path"] = body.path
    _STATE["project"] = Project.load(body.path)
    return _STATE["project"].model_dump()


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
        p.layers.background = body.background  # type: ignore
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
    path = export_master(p, body.out, aspect=body.aspect)
    return {"out": path}


ui_dir = Path(__file__).resolve().parents[3] / "ui" / "web"
if ui_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(ui_dir), html=True), name="ui")
