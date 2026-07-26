"""Filesystem browse allowlist, quick places, and path resolution."""

from __future__ import annotations

import os
import string
import sys
from pathlib import Path

from reelwrite.paths import app_data_dir, default_projects_dir, normalize_user_path
from reelwrite.security.paths import _BLOCKED
from reelwrite.setup_state import projects_dir_from_state


def allowed_roots() -> list[Path]:
    roots: list[Path] = [
        Path.home().resolve(),
        projects_dir_from_state().resolve(),
        default_projects_dir().resolve(),
        app_data_dir().resolve(),
    ]
    for folder in _known_user_folders():
        roots.append(folder)
    roots.extend(_volume_roots())
    extra = os.environ.get("REELWRITE_FS_ROOTS")
    if extra:
        for part in extra.split(os.pathsep):
            if part.strip():
                try:
                    roots.append(Path(part).expanduser().resolve())
                except OSError:
                    continue
    out: list[Path] = []
    for root in roots:
        if root not in out:
            out.append(root)
    # One level up from each root so "Up" works from Projects without trapping
    # the picker when the projects folder sits outside $HOME.
    for root in list(out):
        parent = root.parent
        if parent != root and not is_blocked(parent) and parent not in out:
            out.append(parent)
    return out


def is_blocked(path: Path) -> bool:
    text = str(path)
    return any(pat.search(text) for pat in _BLOCKED)


def is_allowed(path: Path) -> bool:
    if is_blocked(path):
        return False
    try:
        resolved = path.resolve()
    except OSError:
        return False
    for root in allowed_roots():
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def list_places() -> list[dict]:
    """Quick-access folders for the media picker sidebar."""
    home = Path.home()
    projects = projects_dir_from_state()
    candidates: list[tuple[str, str, Path]] = [
        ("home", "Home", home),
        ("desktop", "Desktop", home / "Desktop"),
        ("documents", "Documents", home / "Documents"),
        ("downloads", "Downloads", home / "Downloads"),
        ("videos", "Videos", _videos_dir()),
        ("pictures", "Pictures", home / "Pictures"),
        ("projects", "Projects", projects),
    ]
    if sys.platform == "darwin":
        candidates.insert(4, ("movies", "Movies", home / "Movies"))
    places: list[dict] = []
    seen: set[str] = set()
    for pid, label, path in candidates:
        try:
            resolved = path.expanduser().resolve()
        except OSError:
            continue
        if not resolved.is_dir() or not is_allowed(resolved):
            continue
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        places.append({"id": pid, "label": label, "path": key})
    for drive in _volume_roots():
        key = str(drive)
        if key in seen or not drive.is_dir():
            continue
        seen.add(key)
        label = drive.drive.upper() if getattr(drive, "drive", "") else drive.name or key
        if not label:
            label = key
        places.append({"id": f"vol-{label}", "label": label, "path": key})
    return places


def resolve_fs_path(raw: str) -> dict:
    """Normalize a pasted/typed path for browse or pick."""
    try:
        path = normalize_user_path(raw).expanduser()
    except ValueError as exc:
        return {"ok": False, "error": str(exc), "path": None, "kind": "invalid"}
    try:
        resolved = path.resolve(strict=False)
    except OSError as exc:
        return {"ok": False, "error": str(exc), "path": str(path), "kind": "invalid"}
    if is_blocked(resolved) or not is_allowed(resolved):
        return {
            "ok": False,
            "error": "Path outside allowed folders",
            "path": str(resolved),
            "kind": "denied",
        }
    if resolved.is_dir():
        return {"ok": True, "path": str(resolved), "kind": "dir"}
    if resolved.is_file():
        return {"ok": True, "path": str(resolved), "kind": "file"}
    return {
        "ok": False,
        "error": f"Path not found: {resolved}",
        "path": str(resolved),
        "kind": "missing",
    }


def _videos_dir() -> Path:
    home = Path.home()
    for name in ("Videos", "Movies", "Video"):
        candidate = home / name
        if candidate.is_dir():
            return candidate
    return home / "Videos"


def _known_user_folders() -> list[Path]:
    home = Path.home()
    names = ("Desktop", "Documents", "Downloads", "Videos", "Movies", "Pictures", "Video")
    out: list[Path] = []
    for name in names:
        p = home / name
        try:
            if p.is_dir():
                out.append(p.resolve())
        except OSError:
            continue
    return out


def _volume_roots() -> list[Path]:
    roots: list[Path] = []
    if sys.platform == "win32":
        for letter in string.ascii_uppercase:
            drive = Path(f"{letter}:/")
            try:
                if drive.exists():
                    roots.append(drive.resolve())
            except OSError:
                continue
        return roots
    for base in (Path("/media"), Path("/mnt"), Path("/Volumes")):
        try:
            if not base.is_dir():
                continue
            roots.append(base.resolve())
            for child in base.iterdir():
                if child.is_dir():
                    roots.append(child.resolve())
        except OSError:
            continue
    return roots
