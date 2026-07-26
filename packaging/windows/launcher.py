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


def main() -> int:
    root = _root()
    os.chdir(root)
    vendor = root / "vendor"
    if vendor.is_dir():
        os.environ.setdefault("REELWRIGHT_VENDOR", str(vendor))
    ui = root / "ui" / "web"
    if ui.is_dir():
        os.environ.setdefault("REELWRIGHT_UI", str(ui))

    proc = None
    if not _healthy():
        api = root / "reelwright-api.exe"
        if api.exists():
            proc = subprocess.Popen([str(api)], cwd=str(root))
        else:
            proc = subprocess.Popen(
                [sys.executable, "-m", "reelwright.api.server"],
                cwd=str(root),
            )
        for _ in range(60):
            if _healthy():
                break
            time.sleep(0.25)
        else:
            print("Reelwright API failed to start", file=sys.stderr)
            if proc:
                proc.terminate()
            return 1

    webbrowser.open(URL)
    if proc is None:
        return 0
    try:
        return proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
