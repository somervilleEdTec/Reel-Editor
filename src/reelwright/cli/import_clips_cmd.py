from __future__ import annotations

from pathlib import Path

from reelwright.assembly.distribute import auto_distribute
from reelwright.ingest.probe import probe
from reelwright.models.project import Project


def register(sub):
    p = sub.add_parser("import-clips", help="Import visual clips for Mode C")
    p.add_argument("project")
    p.add_argument("clips", nargs="+")
    p.set_defaults(func=run)


def run(args) -> int:
    project = Project.load(args.project)
    for i, path in enumerate(args.clips):
        sid = f"src_clip_{i+1}"
        project.sources.append(probe(path, source_id=sid, role="media"))
    project.save(args.project)
    print(f"clips={len(args.clips)}")
    return 0
