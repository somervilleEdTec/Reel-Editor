"""Locate and probe ffmpeg/ffprobe."""

from __future__ import annotations

import shutil
import subprocess

from reelwright.paths import ensure_vendor_ffmpeg_on_path, ffmpeg_bin_dir


def ffmpeg_status() -> dict:
    ensure_vendor_ffmpeg_on_path()
    exe = shutil.which("ffmpeg")
    vendored = ffmpeg_bin_dir() is not None
    if not exe:
        return {"found": False, "version": None, "path": None, "vendored": vendored}
    version = None
    try:
        out = subprocess.run(
            [exe, "-version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        line = (out.stdout or "").splitlines()[:1]
        version = line[0] if line else None
    except Exception as e:
        return {"found": False, "version": None, "path": exe, "vendored": vendored, "error": str(e)}
    return {"found": True, "version": version, "path": exe, "vendored": vendored}
