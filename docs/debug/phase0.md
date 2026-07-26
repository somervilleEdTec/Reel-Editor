# Phase 0 debug playbook

## Gate
```bash
pytest tests/test_edl.py tests/test_timeline.py tests/test_ass.py \
  tests/test_golden_sync.py tests/test_zoom_vtt.py -q
```

## Captions drift
1. Dump EDL from `derive_edl`.
2. Check `Timeline.source_to_output` for first/last word.
3. Confirm ASS dialogue times match output timeline, not source.

## ffmpeg fails
1. Print full command from `export_master`.
2. Validate media with `ffprobe`.
3. Confirm rotation applied in probe before crop.

## Whisper issues
- CI may skip model download.
- Persist `project.json` after ASR for resume.
