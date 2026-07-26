from __future__ import annotations

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


@router.post("/export")
def enqueue_export(body: ExportJobBody):
    project = app_module._proj()

    def work(job):
        job.progress = 0.1
        if job.cancel.is_set():
            return None
        path = export_master(project, body.out, aspect=body.aspect)
        job.progress = 1.0
        return {"out": path}

    job = QUEUE.submit("export", work)
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
