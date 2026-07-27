"""Curated free music catalog and local library."""

from reelwrite.music.catalog import load_catalog, track_by_id
from reelwrite.music.library import (
    download_track,
    library_dir,
    list_library,
    local_path_for,
)

__all__ = [
    "download_track",
    "library_dir",
    "list_library",
    "load_catalog",
    "local_path_for",
    "track_by_id",
]
