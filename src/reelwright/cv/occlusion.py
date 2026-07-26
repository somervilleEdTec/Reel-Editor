from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float

    def intersects(self, other: Box) -> bool:
        return not (
            self.x + self.w <= other.x
            or other.x + other.w <= self.x
            or self.y + self.h <= other.y
            or other.y + other.h <= self.y
        )


def occlusion_warnings(
    text_boxes: list[Box],
    face_boxes: list[Box],
    inset: Box,
    caption: Box,
) -> list[str]:
    warns: list[str] = []
    for b in text_boxes + face_boxes:
        if inset.intersects(b):
            warns.append("Inset intersects detected content region")
        if caption.intersects(b):
            warns.append("Caption intersects detected content region")
    return sorted(set(warns))
