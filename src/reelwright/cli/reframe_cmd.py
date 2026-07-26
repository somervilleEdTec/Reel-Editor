from __future__ import annotations

from reelwright.cv.diarise import diarise_from_words
from reelwright.cv.project_reframe import attach_reframe
from reelwright.cv.reframe import associate_speakers, build_crop_path
from reelwright.cv.occlusion import Box
from reelwright.models.project import Project


def register(sub):
    p = sub.add_parser("reframe", help="Compute active-speaker crop path (Phase 3)")
    p.add_argument("project")
    p.add_argument(
        "--mode",
        choices=["active_speaker", "split_stacked", "fixed"],
        default="active_speaker",
    )
    p.set_defaults(func=run)


def run(args) -> int:
    project = Project.load(args.project)
    diar = diarise_from_words(project.words)
    # Without video face tracks, use fixed centres for two speakers
    tracks = {
        "f1": [(0.0, Box(0.25, 0.3, 0.2, 0.25))],
        "f2": [(0.0, Box(0.65, 0.3, 0.2, 0.25))],
    }
    mapping = associate_speakers(diar, tracks) if args.mode != "fixed" else {}
    path = build_crop_path(diar, mapping, tracks, mode=args.mode)
    attach_reframe(project, args.mode, path)
    project.save(args.project)
    print(f"reframe_keys={len(path)} mode={args.mode}")
    return 0
