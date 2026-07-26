from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from reelwright.api import app as app_module
from reelwright.models.project import Project

router = APIRouter(prefix="/project/snapshots")


class SnapshotBody(BaseModel):
    name: str


def _name(raw: str) -> str:
    name = raw.strip()
    if not name or len(name) > 100:
        raise HTTPException(400, "Snapshot name must be 1-100 characters")
    return name


def _directory() -> Path:
    path = Path(app_module._STATE["path"]).resolve().parent / ".reelwright-snapshots"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _path(name: str) -> Path:
    digest = hashlib.sha256(name.encode()).hexdigest()
    return _directory() / f"{digest}.json"


@router.post("")
def create_snapshot(body: SnapshotBody):
    name = _name(body.name)
    record = {
        "name": name,
        "created_at": datetime.now(UTC).isoformat(),
        "project": app_module._proj().model_dump(mode="json"),
    }
    _path(name).write_text(json.dumps(record, indent=2), encoding="utf-8")
    return {"name": name, "created_at": record["created_at"]}


@router.get("")
def list_snapshots():
    app_module._proj()
    snapshots = []
    for path in _directory().glob("*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            snapshots.append({k: record[k] for k in ("name", "created_at")})
        except (OSError, ValueError, KeyError):
            continue
    snapshots.sort(key=lambda item: item["created_at"], reverse=True)
    return {"snapshots": snapshots}


@router.post("/restore")
def restore_snapshot(body: SnapshotBody):
    name = _name(body.name)
    path = _path(name)
    if not path.is_file():
        raise HTTPException(404, "Snapshot not found")
    try:
        project = Project.model_validate(
            json.loads(path.read_text(encoding="utf-8"))["project"]
        )
    except (OSError, ValueError, KeyError) as exc:
        raise HTTPException(400, "Invalid snapshot") from exc
    app_module._save(project)
    return project.model_dump()
