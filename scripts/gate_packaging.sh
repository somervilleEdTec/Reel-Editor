#!/usr/bin/env bash
# Smoke gate for setup/projects API used by product UI
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pytest tests/test_setup_api.py tests/test_api.py tests/test_jobs.py -q
