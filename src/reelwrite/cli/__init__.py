from __future__ import annotations

import argparse
import sys

from . import (
    auto_distribute_cmd,
    export_cmd,
    import_clips_cmd,
    import_vtt_cmd,
    init_cmd,
    rank_cmd,
    record_vo_cmd,
    reframe_cmd,
    run_cmd,
    select_cmd,
    transcribe_cmd,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reelwrite")
    sub = parser.add_subparsers(dest="cmd", required=True)
    init_cmd.register(sub)
    transcribe_cmd.register(sub)
    import_vtt_cmd.register(sub)
    import_clips_cmd.register(sub)
    record_vo_cmd.register(sub)
    auto_distribute_cmd.register(sub)
    export_cmd.register(sub)
    run_cmd.register(sub)
    rank_cmd.register(sub)
    select_cmd.register(sub)
    reframe_cmd.register(sub)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
