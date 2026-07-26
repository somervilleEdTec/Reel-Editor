"""Run local API: python -m reelwright.api.server"""

from __future__ import annotations

import uvicorn

from reelwright.paths import ensure_vendor_ffmpeg_on_path


def main():
    ensure_vendor_ffmpeg_on_path()
    uvicorn.run("reelwright.api.app:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()
