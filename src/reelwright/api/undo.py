from __future__ import annotations

from pathlib import Path

from reelwright.models.project import Project

MAX_UNDO = 30


def reset_history(state: dict) -> None:
    state["undo"] = []
    state["redo"] = []


def _snapshot(project: Project) -> str:
    return project.model_dump_json()


def push_undo(state: dict, snapshot: str) -> None:
    ring = state.setdefault("undo", [])
    if not ring or ring[-1] != snapshot:
        ring.append(snapshot)
        del ring[:-MAX_UNDO]
    state.setdefault("redo", []).clear()


def save_with_undo(state: dict, project: Project) -> None:
    path = Path(state["path"])
    if path.is_file():
        previous = _snapshot(Project.load(str(path)))
        if previous != _snapshot(project):
            push_undo(state, previous)
    project.save(str(path))
    state["project"] = project


def move_history(state: dict, source: str, target: str) -> Project | None:
    ring = state.setdefault(source, [])
    if not ring:
        return None
    current = _snapshot(state["project"])
    other = state.setdefault(target, [])
    other.append(current)
    del other[:-MAX_UNDO]
    project = Project.model_validate_json(ring.pop())
    project.save(state["path"])
    state["project"] = project
    return project
