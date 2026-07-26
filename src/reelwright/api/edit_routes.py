from __future__ import annotations

import re
from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from reelwright.api import app as app_module
from reelwright.edit.edl import derive_edl
from reelwright.edit.timeline import Timeline

router = APIRouter()
FILLERS = {"um", "uh", "umm", "uhh", "erm", "er", "ah", "hmm", "like", "you know"}


class WordRangeBody(BaseModel):
    start_s: float
    end_s: float
    source_id: str | None = None
    deleted: bool


class CleanupBody(BaseModel):
    phrase_gap_s: float = 0.35


def _token(text: str) -> str:
    return re.sub(r"(^[^\w]+|[^\w]+$)", "", text.lower()).strip()


@router.get("/edl")
def get_edl():
    project = app_module._proj()
    active_sources = {w.source_id for w in project.words if not w.deleted}
    duration = None
    if len(active_sources) == 1:
        source = next((s for s in project.sources if s.id in active_sources), None)
        duration = source.duration_s if source else None
    segments = derive_edl(project.words, source_duration_s=duration)
    timeline = Timeline(segments)
    spans = []
    for seg, o0, o1 in timeline._spans:
        row = asdict(seg)
        row.update(
            {
                "source_start": seg.in_s,
                "source_end": seg.out_s,
                "output_start": o0,
                "output_end": o1,
            }
        )
        spans.append(row)
    return {
        "segments": spans,
        "output_duration_s": timeline.duration_s,
        "total_duration": timeline.duration_s,
    }


@router.post("/words/range")
def update_word_range(body: WordRangeBody):
    if body.end_s <= body.start_s:
        raise HTTPException(400, "end_s must be greater than start_s")
    project = app_module._proj()
    changed = 0
    for word in project.words:
        overlaps = word.start_s < body.end_s and word.end_s > body.start_s
        if overlaps and (body.source_id is None or word.source_id == body.source_id):
            if word.deleted != body.deleted:
                word.deleted = body.deleted
                changed += 1
    if changed:
        app_module._save(project)
    return {"ok": True, "changed": changed}


@router.post("/words/cleanup")
def cleanup_words(body: CleanupBody | None = None):
    gap = (body or CleanupBody()).phrase_gap_s
    project = app_module._proj()
    active = [w for w in project.words if not w.deleted]
    filler_ids = {
        (w.source_id, w.id) for w in active if _token(w.text) in FILLERS
    }
    for first, second in zip(active, active[1:]):
        if (
            first.source_id == second.source_id
            and 0 <= second.start_s - first.end_s <= gap
            and f"{_token(first.text)} {_token(second.text)}" in FILLERS
        ):
            filler_ids.update(
                ((first.source_id, first.id), (second.source_id, second.id))
            )
    changed = sum(
        1 for w in project.words if (w.source_id, w.id) in filler_ids and not w.deleted
    )
    if changed:
        project.words = [
            w.model_copy(update={"deleted": True})
            if (w.source_id, w.id) in filler_ids
            else w
            for w in project.words
        ]
        app_module._save(project)
    return {"ok": True, "deleted": changed}
