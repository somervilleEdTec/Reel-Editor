"""Lightweight face region heuristics for CPU-only gallery reframes."""

from __future__ import annotations

from reelwright.cv.occlusion import Box


def detect_faces_bgr(frame_bgr) -> list[Box]:
    try:
        import cv2
    except ImportError:
        return []
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    h, w = gray.shape[:2]
    faces = cascade.detectMultiScale(gray, 1.1, 4)
    out: list[Box] = []
    for x, y, fw, fh in faces:
        out.append(Box(x / w, y / h, fw / w, fh / h))
    return out


def detect_text_regions_stub(frame_bgr) -> list[Box]:
    """Placeholder — wire ONNX EAST/DBNet when packaging CV models."""
    return []
