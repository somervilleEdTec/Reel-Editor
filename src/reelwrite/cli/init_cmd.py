from __future__ import annotations

from reelwrite.workflows import init_project


def register(sub):
    p = sub.add_parser("init", help="Create project from a video file")
    p.add_argument("video")
    p.add_argument("-o", "--out", default="project.json")
    p.add_argument("--role", default="camera")
    p.set_defaults(func=run)


def run(args) -> int:
    init_project(args.video, args.out, role=args.role)
    print(args.out)
    return 0
