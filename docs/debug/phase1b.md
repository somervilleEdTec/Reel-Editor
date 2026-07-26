# Phase 1b debug playbook

## Gate
```bash
pytest tests/test_assembly.py -q
```

## A/V desync
1. Clip output duration must equal timeline span of covered narration words.
2. Do not store clip duration in seconds as source of truth.

## Capture silent / clipping
1. Check `meter_peak_dbfs`.
2. Reject empty WAV (0 frames).
3. CI without mic uses silence placeholder — expect deferred Whisper.

## Auto-distribute empty
- Ensure narration `source_id` matches voiceover words.
