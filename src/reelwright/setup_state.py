"""Persisted first-run / setup state."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from reelwright.paths import default_projects_dir, setup_state_path


class SetupState(BaseModel):
    completed: bool = False
    model_consented: bool = False
    model_downloaded: bool = False
    projects_dir: str = Field(default_factory=lambda: str(default_projects_dir()))


def load_setup() -> SetupState:
    path = setup_state_path()
    if path.exists():
        try:
            return SetupState.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    state = SetupState()
    save_setup(state)
    return state


def save_setup(state: SetupState) -> None:
    path = setup_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")


def projects_dir_from_state() -> Path:
    state = load_setup()
    p = Path(state.projects_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p
