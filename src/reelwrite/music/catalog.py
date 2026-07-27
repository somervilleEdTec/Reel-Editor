from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    try:
        ref = resources.files("reelwrite").joinpath("config/music_catalog.json")
        raw = ref.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, TypeError):
        path = Path(__file__).resolve().parents[1] / "config" / "music_catalog.json"
        raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    tracks = data.get("tracks") or []
    if not isinstance(tracks, list):
        raise ValueError("music catalog tracks must be a list")
    return data


def track_by_id(track_id: str) -> dict[str, Any] | None:
    for track in load_catalog().get("tracks") or []:
        if track.get("id") == track_id:
            return track
    return None


def public_track(track: dict[str, Any], *, downloaded: bool = False) -> dict[str, Any]:
    """Strip download_url from API responses; clients preview via /music/preview."""
    return {
        "id": track["id"],
        "title": track.get("title") or track["id"],
        "artist": track.get("artist") or "",
        "genre": track.get("genre") or "other",
        "duration_s": float(track.get("duration_s") or 0),
        "license": track.get("license") or "",
        "license_url": track.get("license_url") or "",
        "attribution": track.get("attribution") or "",
        "page_url": track.get("page_url") or "",
        "downloaded": downloaded,
    }
