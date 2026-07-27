from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import httpx

from reelwrite.music.catalog import load_catalog, public_track, track_by_id
from reelwrite.paths import app_data_dir

_SAFE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,80}$")


def library_dir() -> Path:
    path = app_data_dir() / "music_library"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _index_path() -> Path:
    return library_dir() / "index.json"


def _load_index() -> dict[str, Any]:
    path = _index_path()
    if not path.is_file():
        return {"tracks": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"tracks": {}}
    if not isinstance(data.get("tracks"), dict):
        data["tracks"] = {}
    return data


def _save_index(data: dict[str, Any]) -> None:
    _index_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def local_path_for(track_id: str) -> Path | None:
    if not _SAFE_ID.match(track_id):
        return None
    entry = _load_index().get("tracks", {}).get(track_id)
    if entry and entry.get("path"):
        path = Path(entry["path"])
        if path.is_file():
            return path
    candidate = library_dir() / f"{track_id}.mp3"
    return candidate if candidate.is_file() else None


def list_library() -> list[dict[str, Any]]:
    catalog = {t["id"]: t for t in load_catalog().get("tracks") or [] if t.get("id")}
    index = _load_index().get("tracks") or {}
    items: list[dict[str, Any]] = []
    for track_id, entry in index.items():
        path = Path(entry.get("path") or "")
        if not path.is_file():
            continue
        base = catalog.get(track_id) or {
            "id": track_id,
            "title": entry.get("title") or track_id,
            "artist": entry.get("artist") or "",
            "genre": entry.get("genre") or "other",
            "duration_s": entry.get("duration_s") or 0,
            "license": entry.get("license") or "",
            "license_url": entry.get("license_url") or "",
            "attribution": entry.get("attribution") or "",
            "page_url": entry.get("page_url") or "",
        }
        item = public_track(base, downloaded=True)
        item["path"] = str(path)
        items.append(item)
    items.sort(key=lambda t: (t.get("artist") or "", t.get("title") or ""))
    return items


def download_track(track_id: str, *, client: httpx.Client | None = None) -> dict[str, Any]:
    if not _SAFE_ID.match(track_id):
        raise ValueError("Invalid track id")
    track = track_by_id(track_id)
    if not track:
        raise KeyError(f"Unknown catalog track: {track_id}")
    existing = local_path_for(track_id)
    if existing:
        return {**public_track(track, downloaded=True), "path": str(existing)}

    url = track.get("download_url")
    if not url:
        raise ValueError("Track has no download URL")

    dest = library_dir() / f"{track_id}.mp3"
    owns_client = client is None
    client = client or httpx.Client(follow_redirects=True, timeout=120.0)
    try:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            tmp = dest.with_suffix(".part")
            with tmp.open("wb") as fh:
                for chunk in resp.iter_bytes(65536):
                    fh.write(chunk)
            tmp.replace(dest)
    finally:
        if owns_client:
            client.close()

    if dest.stat().st_size < 1024:
        dest.unlink(missing_ok=True)
        raise RuntimeError("Downloaded file is empty or invalid")

    index = _load_index()
    index["tracks"][track_id] = {
        "path": str(dest),
        "title": track.get("title"),
        "artist": track.get("artist"),
        "genre": track.get("genre"),
        "duration_s": track.get("duration_s"),
        "license": track.get("license"),
        "license_url": track.get("license_url"),
        "attribution": track.get("attribution"),
        "page_url": track.get("page_url"),
    }
    _save_index(index)
    return {**public_track(track, downloaded=True), "path": str(dest)}
