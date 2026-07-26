"""Resolve app data, vendor, and UI paths for dev and packaged installs."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def install_root() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def vendor_dir() -> Path:
    env = os.environ.get("REELWRIGHT_VENDOR")
    if env:
        return Path(env)
    return install_root() / "vendor"


def ui_web_dir() -> Path:
    env = os.environ.get("REELWRIGHT_UI")
    if env:
        return Path(env)
    root = install_root()
    candidates = [
        root / "ui" / "web",
        root / "_internal" / "ui" / "web",
        Path(__file__).resolve().parents[2] / "ui" / "web",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]


def app_data_dir() -> Path:
    env = os.environ.get("REELWRIGHT_DATA")
    if env:
        p = Path(env)
    elif sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        p = Path(base) / "Reelwright"
    else:
        xdg = os.environ.get("XDG_DATA_HOME")
        p = Path(xdg) / "reelwright" if xdg else Path.home() / ".local" / "share" / "reelwright"
    p.mkdir(parents=True, exist_ok=True)
    return p


def setup_state_path() -> Path:
    return app_data_dir() / "setup.json"


def default_projects_dir() -> Path:
    p = app_data_dir() / "projects"
    p.mkdir(parents=True, exist_ok=True)
    return p


def ffmpeg_bin_dir() -> Path | None:
    d = vendor_dir() / "ffmpeg"
    if (d / "ffmpeg.exe").exists() or (d / "ffmpeg").exists():
        return d
    bin_d = d / "bin"
    if (bin_d / "ffmpeg.exe").exists() or (bin_d / "ffmpeg").exists():
        return bin_d
    return None


def ensure_vendor_ffmpeg_on_path() -> None:
    d = ffmpeg_bin_dir()
    if not d:
        return
    path = os.environ.get("PATH", "")
    prefix = str(d)
    if prefix not in path.split(os.pathsep):
        os.environ["PATH"] = prefix + os.pathsep + path
