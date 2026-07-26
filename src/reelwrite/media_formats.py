"""Central registry of supported media input/output formats.

Single source of truth for video extensions, MIME types, and export
containers/codecs. The UI mirrors these lists in ``ui/web/js/formats.js``.
"""

from __future__ import annotations

VIDEO_EXTS = {
    ".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi",
    ".mts", ".m2ts", ".wmv", ".flv", ".3gp", ".ts",
}

MEDIA_TYPES = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".m4v": "video/x-m4v",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
    ".avi": "video/x-msvideo",
    ".mts": "video/mp2t",
    ".m2ts": "video/mp2t",
    ".ts": "video/mp2t",
    ".wmv": "video/x-ms-wmv",
    ".flv": "video/x-flv",
    ".3gp": "video/3gpp",
}

# Export containers. mp4/mov ship H.264/AAC (+faststart); mkv H.264/AAC;
# webm VP9/Opus with VP8/Vorbis fallback (see render.ffmpeg).
OUTPUT_FORMATS: dict[str, dict[str, str]] = {
    "mp4": {"ext": ".mp4", "label": "MP4 · H.264/AAC"},
    "mov": {"ext": ".mov", "label": "MOV · H.264/AAC"},
    "webm": {"ext": ".webm", "label": "WebM · VP9/Opus"},
    "mkv": {"ext": ".mkv", "label": "MKV · H.264/AAC"},
}
DEFAULT_OUTPUT_FORMAT = "mp4"

_EXT_TO_FORMAT = {v["ext"]: k for k, v in OUTPUT_FORMATS.items()}


def format_for_ext(ext: str) -> str | None:
    """Map a filename extension (with dot) to an output format key."""
    return _EXT_TO_FORMAT.get(ext.lower())
