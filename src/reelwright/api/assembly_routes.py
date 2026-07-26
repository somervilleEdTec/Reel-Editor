from __future__ import annotations

from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError

from reelwright.api import app as app_module
from reelwright.api.source_ops import add_sources, primary_word_source
from reelwright.assembly.capture import capture_voiceover
from reelwright.assembly.distribute import auto_distribute, reorder_clips
from reelwright.ingest.probe import probe
from reelwright.models.assembly import Assembly, AssemblyClip

router = APIRouter(prefix="/assembly")


class ImportBody(BaseModel):
    paths: list[str]


class ReorderBody(BaseModel):
    order: list[str]


class ClipPatch(BaseModel):
    id: str
    source_id: str | None = None
    in_s: float | None = None
    word_start_id: int | None = None
    word_end_id: int | None = None
    fit: Literal["cover", "contain"] | None = None
    speed: float | None = None
    mute_source_audio: bool | None = None
    duration_strategy: Literal["hold", "loop", "slow"] | None = None


class RecordVoiceoverBody(BaseModel):
    duration_s: float = 3.0


def _assembly(project) -> Assembly:
    if project.assembly is None:
        project.assembly = Assembly(narration_source_id=primary_word_source(project))
    return project.assembly


@router.post("/import")
def import_clips(body: ImportBody):
    project = app_module._proj()
    added = add_sources(project, body.paths, "media")
    assembly = _assembly(project)
    narration = primary_word_source(project)
    if narration:
        assembly.narration_source_id = narration
    app_module._save(project)
    return {"sources": [s.model_dump() for s in added], "assembly": assembly.model_dump()}


@router.post("/distribute")
def distribute_clips():
    project = app_module._proj()
    narration = _assembly(project).narration_source_id or primary_word_source(project)
    clips = [source for source in project.sources if source.role == "media"]
    project.assembly = auto_distribute(narration, clips, project.words)
    app_module._save(project)
    return project.assembly.model_dump()


@router.post("/reorder")
def reorder_assembly(body: ReorderBody):
    project = app_module._proj()
    assembly = _assembly(project)
    known = [clip.id for clip in assembly.clips]
    if len(body.order) != len(set(body.order)) or any(i not in known for i in body.order):
        raise HTTPException(400, "Order contains duplicate or unknown clip ids")
    order = body.order + [clip_id for clip_id in known if clip_id not in body.order]
    project.assembly = reorder_clips(assembly, order)
    app_module._save(project)
    return project.assembly.model_dump()


@router.post("/clip")
def patch_clip(body: ClipPatch):
    project = app_module._proj()
    if project.assembly is None:
        raise HTTPException(404, "Clip not found")
    assembly = project.assembly
    index = next((i for i, clip in enumerate(assembly.clips) if clip.id == body.id), None)
    if index is None:
        raise HTTPException(404, "Clip not found")
    changes = body.model_dump(exclude_none=True, exclude={"id"})
    if "source_id" in changes and not any(s.id == changes["source_id"] for s in project.sources):
        raise HTTPException(400, "Unknown source_id")
    try:
        assembly.clips[index] = AssemblyClip.model_validate(
            {**assembly.clips[index].model_dump(), **changes}
        )
    except ValidationError as exc:
        raise HTTPException(422, str(exc)) from exc
    app_module._save(project)
    return assembly.clips[index].model_dump()


@router.delete("/clip/{clip_id}")
def delete_clip(clip_id: str):
    project = app_module._proj()
    if project.assembly is None:
        raise HTTPException(404, "Clip not found")
    assembly = project.assembly
    clips = [clip for clip in assembly.clips if clip.id != clip_id]
    if len(clips) == len(assembly.clips):
        raise HTTPException(404, "Clip not found")
    assembly.clips = clips
    app_module._save(project)
    return {"ok": True}


@router.post("/record-vo")
def record_voiceover(body: RecordVoiceoverBody):
    if body.duration_s <= 0:
        raise HTTPException(400, "duration_s must be positive")
    project = app_module._proj()
    out = Path(app_module._STATE["path"]).resolve().parent / f"voiceover-{uuid4().hex[:8]}.wav"
    capture_voiceover(str(out), duration_s=body.duration_s)
    source = probe(str(out), source_id=f"src_vo_{uuid4().hex[:8]}", role="voiceover")
    project.sources.append(source)
    app_module._save(project)
    return {"source": source.model_dump()}
