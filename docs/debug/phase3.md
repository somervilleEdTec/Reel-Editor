# Phase 3 debug playbook

## Gate
```bash
pytest tests/test_cv.py -q
```

## Wrong speaker
1. Dump diarisation segments and face track IDs.
2. Fall back to `reframe.mode = fixed`.

## Crop jitter
- Increase `hysteresis_s` (default 1.2) and smoothing alpha.

## Low resolution warning
- `crop_resolution_warning` when crop px < export size.
