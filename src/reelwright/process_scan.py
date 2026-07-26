"""Enumerate running processes without third-party dependencies."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass

_TIMEOUT = 20
_WIN_PS = (
    "Get-CimInstance Win32_Process | "
    "Select-Object ProcessId,Name,ExecutablePath,CommandLine | ConvertTo-Json -Compress"
)


@dataclass(frozen=True)
class ProcessInfo:
    pid: int
    name: str
    exe: str
    cmdline: str


def _run(cmd: list[str]) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout or ""


def _windows_processes() -> list[ProcessInfo]:
    raw = _run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", _WIN_PS])
    try:
        data = json.loads(raw) if raw.strip() else []
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = [data]
    procs = []
    for item in data:
        pid = item.get("ProcessId")
        if not isinstance(pid, int):
            continue
        procs.append(
            ProcessInfo(
                pid=pid,
                name=(item.get("Name") or ""),
                exe=(item.get("ExecutablePath") or ""),
                cmdline=(item.get("CommandLine") or ""),
            )
        )
    return procs


def _posix_processes() -> list[ProcessInfo]:
    procs = []
    for line in _run(["ps", "-eo", "pid=,comm=,args="]).splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) < 2 or not parts[0].isdigit():
            continue
        cmdline = parts[2] if len(parts) > 2 else parts[1]
        procs.append(
            ProcessInfo(
                pid=int(parts[0]),
                name=parts[1].rsplit("/", 1)[-1],
                exe=parts[1],
                cmdline=cmdline,
            )
        )
    return procs


def list_processes() -> list[ProcessInfo]:
    return _windows_processes() if sys.platform == "win32" else _posix_processes()
