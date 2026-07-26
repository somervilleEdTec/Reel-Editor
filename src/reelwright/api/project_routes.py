from fastapi import APIRouter, HTTPException

from reelwright.api import app as app_module
from reelwright.api.undo import move_history

router = APIRouter(prefix="/project")


@router.post("/undo")
def undo_project():
    app_module._proj()
    project = move_history(app_module._STATE, "undo", "redo")
    if project is None:
        raise HTTPException(409, "Nothing to undo")
    return project.model_dump()


@router.post("/redo")
def redo_project():
    app_module._proj()
    project = move_history(app_module._STATE, "redo", "undo")
    if project is None:
        raise HTTPException(409, "Nothing to redo")
    return project.model_dump()
