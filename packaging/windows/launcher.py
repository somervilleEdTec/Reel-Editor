"""Windows launcher: start API if needed, open browser, keep alive."""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}/"
HEALTH = f"http://{HOST}:{PORT}/health"


def _root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _healthy() -> bool:
    try:
        with urllib.request.urlopen(HEALTH, timeout=1) as r:
            return r.status == 200
    except Exception:
        return False


def _lifecycle():
    """Import the lifecycle helpers, tolerating an uninstalled source checkout."""
    try:
        from reelwright import process_lifecycle
    except ModuleNotFoundError:
        src = Path(__file__).resolve().parents[2] / "src"
        if src.is_dir():
            sys.path.insert(0, str(src))
        try:
            from reelwright import process_lifecycle
        except ModuleNotFoundError:
            return None
    return process_lifecycle


def _single_instance_mutex():
    """Hold the mutex named by AppMutex so the uninstaller detects a running app."""
    if sys.platform != "win32":
        return None
    import ctypes

    return ctypes.windll.kernel32.CreateMutexW(None, False, "ReelwrightSingleInstance")


def _spawn(cmd: list[str], root: Path) -> subprocess.Popen:
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    kwargs = {"creationflags": flags} if flags else {"start_new_session": True}
    return subprocess.Popen(cmd, cwd=str(root), **kwargs)


def _shutdown(proc: subprocess.Popen | None, lifecycle) -> None:
    if proc is not None:
        if lifecycle is not None:
            lifecycle.terminate_process_tree(proc.pid)
        if proc.poll() is None:
            proc.terminate()
    if lifecycle is not None:
        lifecycle.clear_pid_file(lifecycle.API_NAME)
        lifecycle.clear_pid_file()


def main() -> int:
    root = _root()
    os.chdir(root)
    vendor = root / "vendor"
    if vendor.is_dir():
        os.environ.setdefault("REELWRIGHT_VENDOR", str(vendor))
    ui = root / "ui" / "web"
    if ui.is_dir():
        os.environ.setdefault("REELWRIGHT_UI", str(ui))

    mutex = _single_instance_mutex()  # noqa: F841 — kept alive for the process lifetime
    lifecycle = _lifecycle()
    if lifecycle is not None:
        lifecycle.write_pid_file(os.getpid())
    proc = None
    if not _healthy():
        api = root / "reelwright-api.exe"
        cmd = [str(api)] if api.exists() else [sys.executable, "-m", "reelwright.api.server"]
        proc = _spawn(cmd, root)
        if lifecycle is not None:
            lifecycle.write_pid_file(proc.pid, lifecycle.API_NAME)
        for _ in range(60):
            if _healthy():
                break
            time.sleep(0.25)
        else:
            print("Reelwright API failed to start", file=sys.stderr)
            _shutdown(proc, lifecycle)
            return 1

    webbrowser.open(URL)
    try:
        return proc.wait() if proc is not None else 0
    except KeyboardInterrupt:
        return 0
    finally:
        _shutdown(proc, lifecycle)


if __name__ == "__main__":
    raise SystemExit(main())
