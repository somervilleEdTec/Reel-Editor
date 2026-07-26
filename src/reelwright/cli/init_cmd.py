from __future__ import annotations

from pathlib import Path

from reelwright.ingest.probe import probe
from reelwright.models.project import Project


def register(sub):
    p = sub.add_parser("init", help="Create project from a video file")
    p.add_argument("video")
    p.add_argument("-o", "--out", default="project.json")
    p.add_argument("--role", default="camera")
    p.set_defaults(func=run)


def run(args) -> int:
    src = probe(args.video, source_id="src_1", role=args.role)
    project = Project(sources=[src])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    project.save(args.out)
    print(args.out)
    return 0
