# Reelwrite

Transcript-driven compositor and captioning tool for short-form and teaching video (HVL).

## Status

**V3.0.2** — CapCut-style dual-track editing zone (A-roll EDL + B-roll assembly), Explorer-style media picker with Places/path bar, creator toolkit (undo, fillers, VO, music, transitions, titles, rank/reframe), Tauri 2 desktop shell, and uninstall process cleanup. Product renamed from Reelwright to **Reelwrite**.

## Install

**Windows end users:** download `ReelwriteSetup.exe` from [GitHub Releases](https://github.com/somervilleEdTec/Reel-Editor/releases) (built by Actions — not stored in git). See [Install Instructions.txt](Install%20Instructions.txt).

**Developers / from source:**

```bash
pip install -e ".[dev]"
# requires ffmpeg/ffprobe on PATH
python3 -m reelwrite.api.server
# open http://127.0.0.1:8765/
```

**Maintainers:** tag `v*` or run workflow **Release Windows Package** to publish the installer. Details: [docs/packaging-windows.md](docs/packaging-windows.md).

First launch walks through FFmpeg check, optional model consent, and projects folder.

## Phase 0 — captioned master

```bash
reelwrite init video.mp4 -o project.json
reelwrite transcribe project.json
reelwrite export project.json -o master.mp4
# default 9:16; landscape: --aspect 16:9
reelwrite import-vtt project.json meeting.vtt   # optional Zoom text+align
```

## Phase 1b — Mode C

```bash
reelwrite record-vo project.json -o voiceover.wav
reelwrite import-clips project.json clip1.mp4 clip2.mp4
reelwrite auto-distribute project.json
reelwrite export project.json -o master.mp4
```

## Phase 1 — editor UI

```bash
python3 -m reelwrite.api.server
# open http://127.0.0.1:8765/
```

Product UI flows: first-run setup → home (new/recent reels) → editor → export (job queue).

## Phase 2 — jobs

`POST /jobs/export` then poll `GET /jobs/{id}`; cancel with `POST /jobs/{id}/cancel`.

## Phase 3 — computer vision

```bash
reelwrite reframe project.json --mode active_speaker
```

## Phase 4 — research ranking

```bash
reelwrite rank project.json
reelwrite rank project.json --score   # Azure OpenAI opt-in (egress)
reelwrite select project.json c0
reelwrite export project.json -o clip.mp4
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
