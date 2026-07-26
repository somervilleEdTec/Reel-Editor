#!/usr/bin/env bash
# Run all phase gates in order. On failure, see docs/debug/phaseN.md
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p artifacts/debug
for n in 0 1b 1 2 3 4; do
  echo "=== gate_phase${n} ==="
  ./scripts/gate_phase${n}.sh 2>&1 | tee "artifacts/debug/gate_phase${n}.log"
done
echo "All gates passed."
