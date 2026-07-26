from __future__ import annotations

from reelwright.models.project import Project
from reelwright.render.ffmpeg import export_master


def register(sub):
    p = sub.add_parser("export", help="Export captioned master")
    p.add_argument("project")
    p.add_argument("-o", "--out", default="master.mp4")
    p.add_argument("--aspect", choices=["portrait_9_16", "landscape_16_9", "9:16", "16:9"])
    p.set_defaults(func=run)


def run(args) -> int:
    project = Project.load(args.project)
    aspect = _norm(args.aspect) if args.aspect else None
    export_master(project, args.out, aspect=aspect)
    print(args.out)
    return 0


def _norm(a: str) -> str:
    return {"9:16": "portrait_9_16", "16:9": "landscape_16_9"}.get(a, a)
