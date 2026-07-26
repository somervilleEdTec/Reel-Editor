from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from reelwright.api import app as app_module
from reelwright.jobs.queue import QUEUE
from reelwright.models.project import Project
from reelwright.render.ffmpeg import export_master

router = APIRouter(prefix="/jobs")


class ExportJobBody(BaseModel):
    out: str = "master.mp4"
    aspect: str | None = None
    format: str | None = None


class TranscribeJobBody(BaseModel):
    backend: str = "local"


class ReframeJobBody(BaseModel):
    mode: Literal["active_speaker", "split_stacked", "fixed"] = "active_speaker"


@router.post("/export")
def enqueue_export(body: ExportJobBody):
    project = app_module._proj()
    # Capture path at enqueue time so job uses saved project file
    project_path = app_module._STATE["path"]
    out, fmt = app_module.resolve_export_out(body.out, body.format)
    if any(j.meta.get("out") == out for j in QUEUE.active("export")):
        raise HTTPException(409, "An export to this file is already running")

    def work(job):
        job.progress = 0.1
        if job.cancel.is_set():
            return None
        p = Project.load(project_path) if project_path else project
        path = export_master(p, out, aspect=body.aspect, fmt=fmt)
        job.progress = 1.0
        return {"out": path, "format": fmt}

    try:
        job = QUEUE.submit("export", work, meta={"out": out})
    except RuntimeError as e:
        raise HTTPException(429, str(e)) from e
    return {"job_id": job.id, "out": out, "format": fmt}


@router.post("/transcribe")
def enqueue_transcribe(body: TranscribeJobBody):
    from reelwright.workflows import transcribe_project

    path = app_module._STATE["path"]
    app_module._proj()

    def work(job):
        job.progress = 0.1
        if job.cancel.is_set():
            return None
        updated = transcribe_project(path, backend=body.backend)
        app_module._STATE["project"] = updated
        job.progress = 1.0
        return {"words": len(updated.words)}

    try:
        job = QUEUE.submit("transcribe", work)
    except RuntimeError as e:
        raise HTTPException(429, str(e)) from e
    return {"job_id": job.id}


@router.post("/reframe")
def enqueue_reframe(body: ReframeJobBody):
    from reelwright.cv.project_reframe import project_reframe

    mode = body.mode

    def work(job):
        job.progress = 0.1
        if job.cancel.is_set():
            return None
        # Reload live project so concurrent edits are not overwritten.
        current = app_module._proj().model_copy(deep=True)
        updated = project_reframe(current, mode)
        live = app_module._proj()
        live.reframe = updated.reframe
        app_module._save(live)
        return {"mode": mode, "keyframes": len(updated.reframe["crop_path"])}

    try:
        job = QUEUE.submit("reframe", work)
    except RuntimeError as e:
        raise HTTPException(429, str(e)) from e
    return {"job_id": job.id}


@router.get("/{job_id}")
def job_status(job_id: str):
    job = QUEUE.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return {
        "id": job.id,
        "kind": job.kind,
        "status": job.status,
        "progress": job.progress,
        "error": job.error,
        "result": job.result,
    }


@router.post("/{job_id}/cancel")
def cancel_job(job_id: str):
    if not QUEUE.cancel(job_id):
        raise HTTPException(404, "job not found")
    return {"ok": True}
