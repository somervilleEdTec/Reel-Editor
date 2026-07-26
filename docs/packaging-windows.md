# Windows packaging path (Phase 2 sketch)

## Bundle
- ffmpeg + ffprobe LGPL builds under `vendor/ffmpeg/`
- Python runtime via PyInstaller or embedded venv
- Whisper English distilled weights under `vendor/models/`
- Do not bundle AGPL aligners in the default installer

## Installer
- Prefer WiX or Inno Setup generating `ReelwrightSetup.exe`
- Install to `%LOCALAPPDATA%\\Reelwright`
- Start menu shortcut launching Tauri shell or `reelwright-api` + browser

## First-run checks
1. `ffmpeg -version`
2. Write test to user projects folder
3. Optional: download model if missing (user consent)
