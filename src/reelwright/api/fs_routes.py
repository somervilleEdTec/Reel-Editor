from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from reelwright.api.setup_routes import _is_allowed
from reelwright.paths import app_data_dir
from reelwright.security.paths import _BLOCKED

router = APIRouter(prefix="/fs")


class RevealBody(BaseModel):
    path: str


def _allowed_file(raw: str) -> Path:
    try:
        path = Path(raw).expanduser().resolve()
    except (OSError, ValueError) as exc:
        raise HTTPException(400, "Invalid path") from exc
    text = str(path)
    if any(pat.search(text) for pat in _BLOCKED):
        raise HTTPException(403, "Blocked system path")
    if not _is_allowed(path):
        raise HTTPException(403, "Path outside allowed roots")
    if not path.exists():
        raise HTTPException(404, "Path not found")
    return path


def _midpoint(path: Path) -> float:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            check=True, capture_output=True, text=True, timeout=15,
        )
        return max(0.0, float(result.stdout.strip()) / 2)
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0.0


@router.get("/thumb")
def thumbnail(path: str):
    source = _allowed_file(path)
    if not source.is_file():
        raise HTTPException(400, "Thumbnail source must be a file")
    key = hashlib.sha256(f"{source}:{source.stat().st_mtime_ns}".encode()).hexdigest()
    directory = app_data_dir() / "thumbs"
    directory.mkdir(parents=True, exist_ok=True)
    thumb = directory / f"{key}.jpg"
    if not thumb.is_file():
        temp = directory / f"{key}.tmp.jpg"
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-ss", str(_midpoint(source)), "-i", str(source),
                 "-frames:v", "1", "-vf", "scale=480:-2", str(temp)],
                check=True, capture_output=True, timeout=30,
            )
            temp.replace(thumb)
        except (OSError, subprocess.SubprocessError) as exc:
            temp.unlink(missing_ok=True)
            raise HTTPException(400, "Could not generate thumbnail") from exc
    return FileResponse(thumb, media_type="image/jpeg")


@router.post("/reveal")
def reveal(body: RevealBody):
    path = _allowed_file(body.path)
    if sys.platform != "win32":
        return {"ok": False, "reason": "Reveal is only supported on Windows"}
    command = ["explorer", str(path)] if path.is_dir() else ["explorer", f"/select,{path}"]
    try:
        subprocess.Popen(command)
    except OSError as exc:
        raise HTTPException(500, "Could not reveal path") from exc
    return {"ok": True}
