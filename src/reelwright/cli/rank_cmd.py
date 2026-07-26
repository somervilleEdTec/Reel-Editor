from __future__ import annotations

from reelwright.models.project import Project
from reelwright.rank.windows import enumerate_windows


def register(sub):
    p = sub.add_parser("rank", help="Enumerate candidate windows + caveat warnings")
    p.add_argument("project")
    p.add_argument("--score", action="store_true", help="Use Azure OpenAI (opt-in)")
    p.set_defaults(func=run)


def run(args) -> int:
    project = Project.load(args.project)
    cands = enumerate_windows(project.words)
    if args.score:
        from reelwright.rank.azure_ranker import AzureOpenAIRanker

        ranker = AzureOpenAIRanker()
        for c in cands:
            try:
                c["scores"] = ranker.score_window(
                    project.words, c["word_start_id"], c["word_end_id"]
                )
            except RuntimeError as e:
                c["scores"] = None
                c["warnings"] = list(c.get("warnings") or []) + [str(e)]
    project.candidates = cands
    project.save(args.project)
    print(f"candidates={len(cands)}")
    return 0
