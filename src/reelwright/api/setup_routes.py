"""Setup, projects, filesystem browse, and caption preset routes."""

from __future__ import annotations

import json
import os
from importlib import resources
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from reelwright.api import app as app_module
from reelwright.ffmpeg_check import ffmpeg_status
from reelwright.jobs.queue import QUEUE
from reelwright.paths import app_data_dir, default_projects_dir, normalize_user_path, vendor_dir
from reelwright.setup_state import load_setup, projects_dir_from_state, save_setup
from reelwright.workflows import init_project, transcribe_project

router = APIRouter()

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}


class ConsentBody(BaseModel):
    consented: bool = True


class ProjectsDirBody(BaseModel):
    path: str


class CreateProjectBody(BaseModel):
    video_path: str
    name: str | None = None


def _model_paths() -> list[Path]:
    return [
        vendor_dir() / "models",
        app_data_dir() / "models",
    ]


def _model_downloaded() -> bool:
    for base in _model_paths():
        if not base.is_dir():
            continue
        for _ in base.rglob("*"):
            if _.is_file() and _.stat().st_size > 1_000_000:
                return True
    return False


@router.get("/setup/status")
def setup_status():
    state = load_setup()
    ff = ffmpeg_status()
    projects = Path(state.projects_dir)
    writable = False
    try:
        projects.mkdir(parents=True, exist_ok=True)
        probe = projects / ".reelwright_write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        writable = True
    except Exception:
        writable = False
    downloaded = state.model_downloaded or _model_downloaded()
    complete = bool(ff["found"] and writable and state.completed)
    return {
        "completed": state.completed,
        "complete": complete,
        "ffmpeg": ff,
        "model": {
            "consented": state.model_consented,
            "downloaded": downloaded,
        },
        "projects_dir": str(projects),
        "projects_writable": writable,
    }


@router.post("/setup/consent")
def setup_consent(body: ConsentBody):
    state = load_setup()
    state.model_consented = body.consented
    if body.consented and _model_downloaded():
        state.model_downloaded = True
    save_setup(state)
    return {"ok": True, "model": {"consented": state.model_consented, "downloaded": state.model_downloaded}}


@router.post("/setup/projects-dir")
def setup_projects_dir(body: ProjectsDirBody):
    path = Path(body.path).expanduser().resolve()
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".reelwright_write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except Exception as e:
        raise HTTPException(400, f"Cannot use projects folder: {e}") from e
    state = load_setup()
    state.projects_dir = str(path)
    save_setup(state)
    return {"ok": True, "projects_dir": str(path)}


@router.post("/setup/complete")
def setup_complete():
    state = load_setup()
    ff = ffmpeg_status()
    if not ff["found"]:
        raise HTTPException(400, "FFmpeg is required to finish setup")
    projects = Path(state.projects_dir)
    if not projects.is_dir():
        raise HTTPException(400, "Projects folder missing")
    state.completed = True
    save_setup(state)
    return {"ok": True}


@router.get("/projects")
def list_projects():
    root = projects_dir_from_state()
    items = []
    for path in sorted(root.rglob("project.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        items.append(
            {
                "path": str(path),
                "name": path.parent.name,
                "mtime": path.stat().st_mtime,
            }
        )
    return {"projects": items, "projects_dir": str(root)}


@router.post("/projects/create")
def create_project(body: CreateProjectBody):
    try:
        video = normalize_user_path(body.video_path).resolve()
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    if video.is_dir():
        raise HTTPException(400, "Path is a folder — choose a video file")
    if not video.is_file():
        raise HTTPException(404, f"Video file not found: {video}")
    if video.suffix.lower() not in VIDEO_EXTS:
        raise HTTPException(
            400,
            f"Unsupported video type {video.suffix!r}. Use: "
            + ", ".join(sorted(VIDEO_EXTS)),
        )
    root = projects_dir_from_state()
    name = body.name or video.stem
    dest = root / name
    n = 1
    while dest.exists():
        dest = root / f"{name}-{n}"
        n += 1
    dest.mkdir(parents=True, exist_ok=True)
    project_path = dest / "project.json"

    def work(job):
        job.progress = 0.1
        if job.cancel.is_set():
            return None
        init_project(str(video), str(project_path))
        job.progress = 0.35
        if job.cancel.is_set():
            return None
        project = transcribe_project(str(project_path))
        job.progress = 1.0
        app_module._STATE["path"] = str(project_path)
        app_module._STATE["project"] = project
        return {"path": str(project_path), "words": len(project.words)}

    job = QUEUE.submit("create", work)
    return {"job_id": job.id, "path": str(project_path)}


def _allowed_roots() -> list[Path]:
    roots = [
        Path.home().resolve(),
        projects_dir_from_state().resolve(),
        default_projects_dir().resolve(),
        app_data_dir().resolve(),
    ]
    extra = os.environ.get("REELWRIGHT_FS_ROOTS")
    if extra:
        for part in extra.split(os.pathsep):
            if part.strip():
                roots.append(Path(part).expanduser().resolve())
    # unique
    out: list[Path] = []
    for r in roots:
        if r not in out:
            out.append(r)
    return out


def _is_allowed(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except Exception:
        return False
    for root in _allowed_roots():
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


@router.get("/fs/list")
def fs_list(dir: str | None = None):
    root = Path(dir).expanduser() if dir else projects_dir_from_state()
    try:
        root = root.resolve()
    except Exception as e:
        raise HTTPException(400, f"Invalid path: {e}") from e
    if not _is_allowed(root):
        raise HTTPException(403, "Path outside allowed roots")
    if not root.is_dir():
        raise HTTPException(404, "Directory not found")
    entries = []
    try:
        for child in sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if child.name.startswith("."):
                continue
            if child.is_dir():
                entries.append({"name": child.name, "path": str(child), "type": "dir"})
            elif child.suffix.lower() in VIDEO_EXTS or child.name == "project.json" or child.suffix.lower() == ".json":
                entries.append({"name": child.name, "path": str(child), "type": "file"})
    except PermissionError as e:
        raise HTTPException(403, str(e)) from e
    parent = root.parent if root.parent != root else None
    return {
        "dir": str(root),
        "parent": str(parent) if parent and _is_allowed(parent) else None,
        "entries": entries,
    }


@router.get("/captions/presets")
def caption_presets():
    ref = resources.files("reelwright").joinpath("captions/presets.json")
    return json.loads(ref.read_text(encoding="utf-8"))


@router.get("/aspects")
def aspects():
    ref = resources.files("reelwright").joinpath("config/aspects.json")
    return json.loads(ref.read_text(encoding="utf-8"))
