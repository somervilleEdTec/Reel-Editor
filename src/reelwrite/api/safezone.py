from __future__ import annotations

import json
from importlib import resources

from reelwrite.models.layers import Inset
from reelwrite.models.project import Project


def safezone_hits(project: Project) -> list[dict]:
    """Return advisory collisions between inset/captions and platform safe zones."""
    raw = resources.files("reelwrite").joinpath("config/safezones.json")
    zones = json.loads(raw.read_text(encoding="utf-8"))
    hits: list[dict] = []
    inset = project.layers.inset
    cap_y = project.captions.y
    for platform, z in zones.items():
        if platform not in project.export.check_platforms:
            continue
        # Caption near bottom reserved area
        if cap_y > 1.0 - z.get("bottom", 0):
            hits.append(
                {
                    "platform": platform,
                    "target": "captions",
                    "reason": "caption y intersects bottom safe zone",
                }
            )
        # Inset intersects right reserved strip
        if inset.x + inset.w > 1.0 - z.get("right", 0):
            hits.append(
                {
                    "platform": platform,
                    "target": "inset",
                    "reason": "inset intersects right safe zone",
                }
            )
        if inset.y < z.get("top", 0):
            hits.append(
                {
                    "platform": platform,
                    "target": "inset",
                    "reason": "inset intersects top safe zone",
                }
            )
    return hits
