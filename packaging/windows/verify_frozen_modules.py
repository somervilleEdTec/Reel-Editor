"""Fail the Windows package build if critical modules were not frozen."""

from __future__ import annotations

import sys
from pathlib import Path

REQUIRED = (
    "reelwright.api",
    "reelwright.api.app",
    "reelwright.api.jobs_routes",
    "reelwright.api.setup_routes",
    "reelwright.api.media_routes",
)


def main() -> int:
    # Default workpath from build.ps1 / local pyinstaller at repo root
    root = Path(__file__).resolve().parents[2]
    candidates = [
        root / "build" / "reelwright-api" / "Analysis-00.toc",
        Path(sys.argv[1]) if len(sys.argv) > 1 else None,
    ]
    toc = next((p for p in candidates if p and p.is_file()), None)
    if not toc:
        print("ERROR: Analysis-00.toc not found", file=sys.stderr)
        return 2
    text = toc.read_text(encoding="utf-8", errors="ignore")
    missing = [m for m in REQUIRED if f"'{m}'" not in text and f'"{m}"' not in text]
    if missing:
        print("ERROR: PyInstaller omitted required modules:", ", ".join(missing), file=sys.stderr)
        print(f"(checked {toc})", file=sys.stderr)
        return 1
    print(f"OK: required modules present in {toc.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
