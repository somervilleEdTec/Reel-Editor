from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import HTTPException

from reelwrite.api.fs_access import resolve_fs_path
from reelwrite.ingest.probe import probe
from reelwrite.models.project import Project
from reelwrite.models.source import Source

EditableRole = Literal["media", "camera", "voiceover", "music"]


def primary_word_source(project: Project) -> str:
    active = next((w.source_id for w in project.words if not w.deleted), None)
    return active or next((w.source_id for w in project.words), "")


def add_sources(project: Project, paths: list[str], role: EditableRole) -> list[Source]:
    if not paths:
        raise HTTPException(400, "At least one path is required")
    added = []
    for raw in paths:
        try:
            resolved = resolve_fs_path(raw)
            if not resolved["ok"] or resolved["kind"] != "file":
                raise HTTPException(
                    404 if resolved["kind"] == "missing" else 400,
                    resolved.get("error") or f"Source file not found: {raw}",
                )
            path = resolved["path"]
            if not Path(path).is_file():
                raise HTTPException(400, f"Source is not a file: {path}")
            added.append(probe(path, source_id=f"src_{uuid4().hex[:12]}", role=role))
        except HTTPException:
            raise
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            raise HTTPException(400, f"Could not probe source: {raw}") from exc
    project.sources.extend(added)
    return added
