# Phase 2 debug playbook

## Gate
```bash
pytest tests/test_jobs.py -q
```

## Job cancel
- Cancel sets event; worker must check `job.cancel.is_set()`.

## Malformed media
- `require_media` before probe; map ffprobe failures to `E_MEDIA_PROBE`.

## Export idempotency
- Compare EDL JSON + ASS text across two exports with same project.
