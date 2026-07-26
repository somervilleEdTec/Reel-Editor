# Reelwright

Transcript-driven compositor and captioning tool for short-form and teaching video (HVL).

## Status

Phases **0–4** implemented in-repo (CLI + local FastAPI/web UI). Desktop Tauri wrapper is optional; run the web UI via the API server.

## Install

```bash
pip install -e ".[dev]"
# requires ffmpeg/ffprobe on PATH
```

## Phase 0 — captioned master

```bash
reelwright init video.mp4 -o project.json
reelwright transcribe project.json
reelwright export project.json -o master.mp4
# default 9:16; landscape: --aspect 16:9
reelwright import-vtt project.json meeting.vtt   # optional Zoom text+align
```

## Phase 1b — Mode C

```bash
reelwright record-vo project.json -o voiceover.wav
reelwright import-clips project.json clip1.mp4 clip2.mp4
reelwright auto-distribute project.json
reelwright export project.json -o master.mp4
```

## Phase 1 — editor UI

```bash
python3 -m reelwright.api.server
# open http://127.0.0.1:8765/
```

## Phase 2 — jobs

`POST /jobs/export` then poll `GET /jobs/{id}`; cancel with `POST /jobs/{id}/cancel`.

## Phase 3 — computer vision

```bash
reelwright reframe project.json --mode active_speaker
```

## Phase 4 — research ranking

```bash
reelwright rank project.json
reelwright rank project.json --score   # Azure OpenAI opt-in (egress)
reelwright select project.json c0
reelwright export project.json -o clip.mp4
```

## Cloud opt-in (Azure EU)

Offline by default. Env vars:

- `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`
- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`

## Gates / debugging

```bash
chmod +x scripts/gate_*.sh
./scripts/gate_all.sh
```

Playbooks: `docs/debug/phase0.md` … `phase4.md`. Packaging: `docs/packaging-windows.md`. Licences: `LICENCE_NOTES.md`.
