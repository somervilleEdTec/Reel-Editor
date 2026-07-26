"""Generate src-tauri/icons/icon.{ico,png} (placeholder brand mark).

Tauri needs an .ico to build for Windows and a .png as the default window icon
elsewhere. Regenerate after editing the shapes below:

    python3 src-tauri/icons/make_icon.py

Replace with real artwork via the `tauri icon` CLI when branding lands.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

SIZES = (16, 24, 32, 48, 64, 128, 256)
BACKGROUND = (17, 20, 24)
ACCENT = (255, 214, 102)
SAMPLES = 3  # supersampling per axis


def _in_rounded_square(x: float, y: float, inset: float = 0.04, radius: float = 0.2) -> bool:
    lo, hi = inset, 1.0 - inset
    if not (lo <= x <= hi and lo <= y <= hi):
        return False
    cx = min(max(x, lo + radius), hi - radius)
    cy = min(max(y, lo + radius), hi - radius)
    return (x - cx) ** 2 + (y - cy) ** 2 <= radius**2


def _in_play_triangle(x: float, y: float) -> bool:
    # Right-pointing play head: (0.37,0.27) (0.37,0.73) (0.74,0.5)
    if not 0.37 <= x <= 0.74:
        return False
    span = 0.23 * (1.0 - (x - 0.37) / 0.37)
    return abs(y - 0.5) <= span


def _pixel(x: float, y: float, unit: float) -> tuple[int, int, int, int]:
    hits = [
        (_in_rounded_square(sx, sy), _in_play_triangle(sx, sy)) for sx, sy in _samples(x, y, unit)
    ]
    coverage = sum(1 for square, _ in hits if square) / len(hits)
    mark = sum(1 for square, tri in hits if square and tri) / len(hits)
    if coverage == 0:
        return (0, 0, 0, 0)
    colour = tuple(
        round(bg + (fg - bg) * (mark / coverage)) for bg, fg in zip(BACKGROUND, ACCENT)
    )
    return (*colour, round(255 * coverage))


def _samples(x: float, y: float, unit: float):
    step = unit / SAMPLES
    for i in range(SAMPLES):
        for j in range(SAMPLES):
            yield x + (i + 0.5) * step, y + (j + 0.5) * step


def _png(size: int) -> bytes:
    unit = 1.0 / size
    raw = bytearray()
    for row in range(size):
        raw.append(0)  # PNG filter type 0
        for col in range(size):
            raw.extend(bytes(_pixel(col * unit, row * unit, unit)))

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def main() -> None:
    images = [(size, _png(size)) for size in SIZES]
    png = Path(__file__).with_name("icon.png")
    png.write_bytes(dict(images)[256])
    print(f"wrote {png} ({png.stat().st_size} bytes)")

    offset = 6 + 16 * len(images)
    directory = bytearray(struct.pack("<HHH", 0, 1, len(images)))
    for size, data in images:
        directory.extend(
            struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset)
        )
        offset += len(data)
    out = Path(__file__).with_name("icon.ico")
    out.write_bytes(bytes(directory) + b"".join(data for _, data in images))
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
