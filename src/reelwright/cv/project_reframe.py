from __future__ import annotations

from reelwright.cv.occlusion import Box
from reelwright.cv.reframe import CropKeyframe, build_crop_path
from reelwright.models.project import Project


def attach_reframe(
    project: Project,
    mode: str,
    crop_path: list[CropKeyframe],
    warnings: list[str] | None = None,
) -> Project:
    project.schema_version = max(project.schema_version, 2)
    project.reframe = {
        "mode": mode,
        "crop_path": [
            {"t": k.t, "cx": k.cx, "cy": k.cy, "mode": k.mode} for k in crop_path
        ],
        "warnings": warnings or [],
    }
    return project


def crop_resolution_warning(
    source_w: int, source_h: int, crop: Box, export_w: int, export_h: int
) -> str | None:
    cw, ch = crop.w * source_w, crop.h * source_h
    if cw < export_w or ch < export_h:
        return (
            f"Crop region {cw:.0f}x{ch:.0f} is below export {export_w}x{export_h}; "
            "upscaling will be required."
        )
    return None
