# Phase 1 debug playbook

## Gate
```bash
pytest tests/test_api.py -q
```

## UI blocks
- Long work must go through jobs (Phase 2). Export endpoint is sync for now — use job queue after Phase 2.

## Safe-zone false positives
- Only use fractions from `config/safezones.json`.
- Warn; never auto-reposition.

## Tauri missing
- Run API: `python3 -m reelwrite.api.server`
- Open `http://127.0.0.1:8765/` for web UI.
