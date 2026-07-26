"""Cross-platform process termination used by the launcher and uninstaller."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

_TASKKILL_NOT_FOUND = 128


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return str(pid) in (out.stdout or "")
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return not _posix_zombie(pid)


def _posix_zombie(pid: int) -> bool:
    """An unreaped child still answers signal 0, so read its state instead."""
    try:
        with open(f"/proc/{pid}/stat", "rb") as fh:
            return fh.read().rpartition(b")")[2].split()[0] == b"Z"
    except (OSError, IndexError):
        pass
    try:
        out = subprocess.run(
            ["ps", "-o", "state=", "-p", str(pid)], capture_output=True, text=True
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return (out.stdout or "").strip().startswith("Z")


def _kill_windows(pid: int) -> bool:
    try:
        out = subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, text=True
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return out.returncode in (0, _TASKKILL_NOT_FOUND)


def _signal_posix(pid: int, sig: int) -> bool:
    """Signal the process group when the pid leads one, else the pid alone."""
    try:
        if os.getpgid(pid) == pid:
            os.killpg(pid, sig)
        else:
            os.kill(pid, sig)
    except (ProcessLookupError, PermissionError, OSError):
        return False
    return True


def _wait_gone(pid: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not process_alive(pid):
            return True
        time.sleep(0.05)
    return not process_alive(pid)


def _kill_posix(pid: int, timeout: float) -> bool:
    if not _signal_posix(pid, signal.SIGTERM):
        return not process_alive(pid)
    if _wait_gone(pid, timeout):
        return True
    _signal_posix(pid, signal.SIGKILL)
    return _wait_gone(pid, 1.0)


def terminate_process_tree(pid: int, timeout: float = 5.0) -> bool:
    """Kill ``pid`` and its children. Returns True when nothing is left running."""
    if pid <= 0 or pid == os.getpid():
        return False
    if sys.platform == "win32":
        return _kill_windows(pid)
    return _kill_posix(pid, timeout)
