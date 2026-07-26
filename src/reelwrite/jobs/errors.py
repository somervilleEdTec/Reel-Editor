from __future__ import annotations

from pathlib import Path


class ReelwriteError(Exception):
    code: str = "E_UNKNOWN"

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class MediaProbeError(ReelwriteError):
    code = "E_MEDIA_PROBE"


class ExportError(ReelwriteError):
    code = "E_EXPORT"


def require_media(path: str) -> Path:
    p = Path(path)
    if not p.exists():
        raise MediaProbeError(f"Missing media: {path}", "E_MEDIA_MISSING")
    if p.stat().st_size == 0:
        raise MediaProbeError(f"Empty media: {path}", "E_MEDIA_EMPTY")
    return p
