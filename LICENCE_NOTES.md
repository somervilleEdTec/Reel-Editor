# Licence notes

## Core
- Application code: project licence (see repo root if present).
- `ffmpeg` / `ffprobe`: LGPL/GPL depending on build — ship a documented LGPL build when packaging.
- `faster-whisper` / CTranslate2: MIT-compatible stack preferred for distribution.
- `pydantic`, `fastapi`: MIT.

## Avoid / isolate
- WhisperX and some pyannote components are **AGPL-3.0**. Do not bundle in the default Windows installer without legal review. Phase 0 uses even-split VTT alignment; upgrade to MFA/torchaudio (non-AGPL) before enabling WhisperX.

## Fonts
- Caption presets ship with **Arial** as a safe system fallback for Phase 0.
- For branded presets (Anton / Inter), embed only fonts with OFL or equivalent redistribution rights and document paths under `assets/fonts/`.

## Cloud opt-in
- Azure Speech / Azure OpenAI: customer subscription; no keys in repo. Data egress only when user selects cloud backends.
