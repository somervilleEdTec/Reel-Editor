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
    env = os.environ.get("REELWRITE_VENDOR")
    if env:
        return Path(env)
    return install_root() / "vendor"


def ui_web_dir() -> Path:
    env = os.environ.get("REELWRITE_UI")
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
    env = os.environ.get("REELWRITE_DATA")
    if env:
        p = Path(env)
    elif sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        p = Path(base) / "Reelwrite"
    else:
        xdg = os.environ.get("XDG_DATA_HOME")
        p = Path(xdg) / "reelwrite" if xdg else Path.home() / ".local" / "share" / "reelwrite"
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


def ensure_stdio() -> Path | None:
    """Restore stdout/stderr when a windowed freeze sets them to None.

    PyInstaller ``console=False`` builds leave ``sys.stdout`` / ``sys.stderr``
    as ``None``, which crashes uvicorn's colourised logging (``.isatty()``).
    """
    if sys.stdout is not None and sys.stderr is not None:
        return None
    log_dir = app_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "api.log"
    stream = open(log_path, "a", encoding="utf-8", buffering=1)
    if sys.stdout is None:
        sys.stdout = stream  # type: ignore[assignment]
    if sys.stderr is None:
        sys.stderr = stream  # type: ignore[assignment]
    return log_path


def normalize_user_path(raw: str) -> Path:
    """Normalize Explorer "Copy as path", file:// URLs, and stray whitespace."""
    from urllib.parse import unquote, urlparse

    s = (raw or "").strip().lstrip("\ufeff").strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1].strip()
    if s.lower().startswith("file:"):
        parsed = urlparse(s)
        s = unquote(parsed.path or "")
        # file:///C:/Users/... → /C:/Users/... on urlparse; drop leading slash.
        if sys.platform == "win32" and len(s) >= 3 and s[0] == "/" and s[2] == ":":
            s = s[1:]
    if not s:
        raise ValueError("Empty path")
    return Path(s).expanduser()
