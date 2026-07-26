"""PID file used by the launcher so uninstall can stop a running API."""

from __future__ import annotations

from pathlib import Path

from reelwrite.paths import app_data_dir

DEFAULT_NAME = "reelwrite"
API_NAME = "api"


def pid_file_path(name: str = DEFAULT_NAME) -> Path:
    return app_data_dir() / f"{name}.pid"


def write_pid_file(pid: int, name: str = DEFAULT_NAME) -> Path:
    path = pid_file_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(int(pid)), encoding="utf-8")
    return path


def read_pid_file(name: str = DEFAULT_NAME) -> int | None:
    try:
        raw = pid_file_path(name).read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        pid = int(raw.strip())
    except ValueError:
        return None
    return pid if pid > 0 else None


def clear_pid_file(name: str = DEFAULT_NAME) -> None:
    try:
        pid_file_path(name).unlink(missing_ok=True)
    except OSError:
        pass
