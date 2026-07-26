from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from reelwrite.api import app as app_module
from reelwrite.models.editing import Title

router = APIRouter()


class TitleChange(BaseModel):
    id: str | None = None
    text: str | None = None
    start_out_s: float | None = None
    end_out_s: float | None = None
    y: float | None = None
    style: dict | None = None
    deleted: bool = False
    titles: list[Title] | None = None


@router.post("/titles")
def update_titles(body: list[Title] | TitleChange):
    project = app_module._proj()
    if isinstance(body, list):
        project.titles = body
    elif body.titles is not None:
        project.titles = body.titles
    elif body.id:
        index = next((i for i, item in enumerate(project.titles) if item.id == body.id), None)
        if index is None:
            raise HTTPException(404, "Title not found")
        if body.deleted:
            project.titles.pop(index)
        else:
            changes = body.model_dump(
                exclude_none=True, exclude={"id", "deleted", "titles"}
            )
            project.titles[index] = Title.model_validate(
                {**project.titles[index].model_dump(), **changes}
            )
    elif None not in (body.text, body.start_out_s, body.end_out_s):
        project.titles.append(
            Title(
                text=body.text or "",
                start_out_s=body.start_out_s or 0,
                end_out_s=body.end_out_s or 0,
                y=body.y if body.y is not None else 0.5,
                style=body.style or {},
            )
        )
    else:
        raise HTTPException(400, "Provide titles or title fields")
    app_module._save(project)
    return {"titles": [title.model_dump() for title in project.titles]}
