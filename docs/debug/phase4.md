# Phase 4 debug playbook

## Gate
```bash
pytest tests/test_rank.py -q
```

## Azure OpenAI missing
- Without keys, `rank --score` attaches a not-configured warning and keeps windows unranked.
- Never send research audio/transcripts without explicit `--score` / UI opt-in.

## Malformed LLM JSON
1. Retry once.
2. Fall back to caveat-only windows (`scores: null`).

## Caveat false negatives
- Extend `config/caveat_markers.json` (data, not code).
