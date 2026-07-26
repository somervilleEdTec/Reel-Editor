from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from reelwright.api import app as app_module
from reelwright.models.editing import Marker

router = APIRouter()


class MarkerChange(BaseModel):
    id: str | None = None
    t_out_s: float | None = None
    label: str | None = None
    deleted: bool = False
    markers: list[Marker] | None = None


@router.post("/markers")
def update_markers(body: list[Marker] | MarkerChange):
    project = app_module._proj()
    if isinstance(body, list):
        project.markers = body
    elif body.markers is not None:
        project.markers = body.markers
    elif body.id:
        index = next((i for i, item in enumerate(project.markers) if item.id == body.id), None)
        if index is None:
            raise HTTPException(404, "Marker not found")
        if body.deleted:
            project.markers.pop(index)
        else:
            changes = body.model_dump(
                exclude_none=True, exclude={"id", "deleted", "markers"}
            )
            project.markers[index] = Marker.model_validate(
                {**project.markers[index].model_dump(), **changes}
            )
    elif body.t_out_s is not None:
        project.markers.append(Marker(t_out_s=body.t_out_s, label=body.label or ""))
    else:
        raise HTTPException(400, "Provide markers or marker fields")
    app_module._save(project)
    return {"markers": [marker.model_dump() for marker in project.markers]}
