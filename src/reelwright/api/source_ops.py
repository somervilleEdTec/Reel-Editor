from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import HTTPException

from reelwright.api import app as app_module
from reelwright.ingest.probe import probe
from reelwright.models.project import Project
from reelwright.models.source import Source
from reelwright.paths import normalize_user_path

EditableRole = Literal["media", "camera", "voiceover"]


def primary_word_source(project: Project) -> str:
    active = next((w.source_id for w in project.words if not w.deleted), None)
    return active or next((w.source_id for w in project.words), "")


def add_sources(project: Project, paths: list[str], role: EditableRole) -> list[Source]:
    if not paths:
        raise HTTPException(400, "At least one path is required")
    added = []
    for raw in paths:
        try:
            normalized = str(normalize_user_path(raw))
            path = app_module._safe_path(normalized, must_exist=True)
            if not Path(path).is_file():
                raise HTTPException(400, f"Source is not a file: {path}")
            added.append(probe(path, source_id=f"src_{uuid4().hex[:12]}", role=role))
        except HTTPException:
            raise
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            raise HTTPException(400, f"Could not probe source: {raw}") from exc
    project.sources.extend(added)
    return added
