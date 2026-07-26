"""Run local API: python -m reelwrite.api.server"""

from __future__ import annotations

import uvicorn

from reelwrite.paths import ensure_stdio, ensure_vendor_ffmpeg_on_path


def main():
    ensure_stdio()
    ensure_vendor_ffmpeg_on_path()
    # Loopback only — never bind 0.0.0.0; API has no auth by design.
    uvicorn.run(
        "reelwrite.api.app:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
        use_colors=False,
    )


if __name__ == "__main__":
    main()
