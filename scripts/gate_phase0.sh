#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pytest tests/test_edl.py tests/test_timeline.py tests/test_ass.py \
  tests/test_golden_sync.py tests/test_zoom_vtt.py -q
