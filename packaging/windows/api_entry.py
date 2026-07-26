"""PyInstaller entry for the Reelwright API server."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure package imports work when frozen
if getattr(sys, "frozen", False):
    root = Path(sys.executable).resolve().parent
    meipass = Path(getattr(sys, "_MEIPASS", root))
    ui = meipass / "ui" / "web"
    if ui.is_dir():
        os.environ.setdefault("REELWRIGHT_UI", str(ui))
    vendor = root / "vendor"
    if vendor.is_dir():
        os.environ.setdefault("REELWRIGHT_VENDOR", str(vendor))

from reelwright.paths import ensure_vendor_ffmpeg_on_path

ensure_vendor_ffmpeg_on_path()

import uvicorn


def main():
    uvicorn.run("reelwright.api.app:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()
