"""PyInstaller entry for the Reelwrite API server."""

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
        os.environ.setdefault("REELWRITE_UI", str(ui))
    vendor = root / "vendor"
    if vendor.is_dir():
        os.environ.setdefault("REELWRITE_VENDOR", str(vendor))

from reelwrite.paths import ensure_stdio, ensure_vendor_ffmpeg_on_path

ensure_stdio()
ensure_vendor_ffmpeg_on_path()

import uvicorn

# Import the app object (not a string) so PyInstaller traces reelwrite.api.*
from reelwrite.api.app import app


def main():
    # use_colors=False avoids ColourizedFormatter touching None stdio.
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8765,
        reload=False,
        use_colors=False,
    )


if __name__ == "__main__":
    main()
