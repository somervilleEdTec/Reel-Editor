from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from reelwright.api import app as app_module
from reelwright.edit.apply_candidate import apply_candidate
from reelwright.rank.caveats import caveat_warnings
from reelwright.rank.windows import enumerate_windows

router = APIRouter()


class RankBody(BaseModel):
    score: bool = False


class SelectBody(BaseModel):
    candidate_id: str


@router.post("/rank")
def rank_project(body: RankBody | None = None):
    project = app_module._proj()
    candidates = enumerate_windows(project.words)
    if body and body.score:
        from reelwright.rank.azure_ranker import AzureOpenAIRanker

        ranker = AzureOpenAIRanker()
        for candidate in candidates:
            try:
                candidate["scores"] = ranker.score_window(
                    project.words,
                    candidate["word_start_id"],
                    candidate["word_end_id"],
                )
            except RuntimeError as exc:
                candidate["warnings"] = list(candidate.get("warnings") or []) + [str(exc)]
    project.candidates = candidates
    app_module._save(project)
    return {"candidates": candidates}


@router.post("/select")
def select_candidate(body: SelectBody):
    project = app_module._proj()
    candidate = next(
        (item for item in project.candidates if item.get("id") == body.candidate_id),
        None,
    )
    if not candidate:
        raise HTTPException(404, "Candidate not found")
    start, end = candidate["word_start_id"], candidate["word_end_id"]
    warnings = caveat_warnings(project.words, start, end)
    project.words = apply_candidate(project.words, start, end)
    app_module._save(project)
    return {"candidate_id": body.candidate_id, "warnings": warnings}
