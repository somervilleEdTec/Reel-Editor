# Reelwright

Transcript-driven compositor and captioning tool for short-form and teaching video (HVL).

## Phase status

| Phase | Status |
| --- | --- |
| 0 CLI pipeline | In progress |
| 1b Mode C assembly | Planned |
| 1 Editor (Tauri + FastAPI) | Planned |
| 2 Hardening / jobs | Planned |
| 3 Computer vision | Planned |
| 4 Research ranking | Planned |

## Quick start (Phase 0)

```bash
pip install -e ".[dev]"
reelwright init video.mp4 -o project.json
reelwright transcribe project.json          # local Whisper (default)
reelwright export project.json -o master.mp4
# or: reelwright run video.mp4 -o master.mp4
```

Optional Zoom VTT (does **not** replace ASR as the default path):

```bash
reelwright import-vtt project.json meeting.vtt
reelwright export project.json -o master.mp4
```

Aspect profiles: default `portrait_9_16` (1080×1920). Use `--aspect landscape_16_9` or `16:9` for landscape.

## Cloud opt-in (university / Azure EU)

Offline by default. To enable cloud backends:

- `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`
- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`

```bash
reelwright transcribe project.json --backend azure
reelwright rank project.json --score
```

## Gates

```bash
./scripts/gate_phase0.sh
```

Debug playbooks: `docs/debug/`.
