"""Public lifecycle API: PID file plus targeted Reelwrite process shutdown."""

from __future__ import annotations

import os
from pathlib import Path

from reelwrite.paths import install_root
from reelwrite.pid_file import (
    API_NAME,
    clear_pid_file,
    pid_file_path,
    read_pid_file,
    write_pid_file,
)
from reelwrite.process_kill import process_alive, terminate_process_tree
from reelwrite.process_scan import ProcessInfo, list_processes

__all__ = [
    "API_NAME",
    "clear_pid_file",
    "kill_reelwrite_processes",
    "pid_file_path",
    "process_alive",
    "read_pid_file",
    "terminate_process_tree",
    "write_pid_file",
]

APP_NAMES = ("reelwrite.exe", "reelwrite-api.exe", "reelwrite", "reelwrite-api")
MEDIA_NAMES = ("ffmpeg.exe", "ffprobe.exe", "ffmpeg", "ffprobe")


def _owned_by_install(proc: ProcessInfo, install_dir: str) -> bool:
    """True only for media tools shipped in / launched from this install."""
    root = Path(install_dir).resolve()
    if proc.exe:
        try:
            Path(proc.exe).resolve().relative_to(root)
            return True
        except (ValueError, OSError):
            pass
    needle = str(root).lower().replace("\\", "/").rstrip("/") + "/"
    return needle in proc.cmdline.lower().replace("\\", "/")


def _targets(install_dir: str) -> list[int]:
    self_pid = os.getpid()
    pids = []
    for proc in list_processes():
        name = proc.name.lower()
        if proc.pid == self_pid:
            continue
        if name in APP_NAMES or (name in MEDIA_NAMES and _owned_by_install(proc, install_dir)):
            pids.append(proc.pid)
    return pids


def _pid_is_reelwrite(pid: int, install_dir: str | None = None) -> bool:
    """Refuse to kill PIDs that are not Reelwrite / this install's API."""
    for proc in list_processes():
        if proc.pid != pid:
            continue
        name = proc.name.lower()
        if name in APP_NAMES:
            if not install_dir or not proc.exe:
                return True
            try:
                Path(proc.exe).resolve().relative_to(Path(install_dir).resolve())
                return True
            except (ValueError, OSError):
                return False
        return False
    return False


def kill_reelwrite_processes(install_dir: str | None = None) -> list[int]:
    """Stop the recorded API pid, Reelwrite executables, and this install's ffmpeg."""
    root = str(Path(install_dir).resolve()) if install_dir else str(install_root())
    killed = []
    for name in (API_NAME, "reelwrite"):
        pid = read_pid_file(name)
        if pid and _pid_is_reelwrite(pid, root) and terminate_process_tree(pid):
            killed.append(pid)
        clear_pid_file(name)
    for pid in _targets(root):
        if pid not in killed and terminate_process_tree(pid):
            killed.append(pid)
    return killed
