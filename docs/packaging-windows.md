# Windows packaging path

End users install with **ReelwrightSetup.exe** (Inno Setup) **after it is built**.
That `.exe` is a build artifact under `dist/` (gitignored) — it is not committed to the repository.

## End-user install

1. Build on a Windows machine (or CI Windows runner): `powershell -ExecutionPolicy Bypass -File packaging/windows/build.ps1`
2. Distribute `dist/windows/installer/ReelwrightSetup.exe` (release download / shared drive — do not commit)
3. Installer writes to `%LOCALAPPDATA%\Reelwright` (per-user, no admin)
4. Start Menu **Reelwright** runs the launcher: starts local API on `127.0.0.1:8765`, opens the default browser

## Bundle contents

| Path | Purpose |
|------|---------|
| `Reelwright.exe` | Launcher (health-check, start API, open browser) |
| `reelwright-api.exe` + `_internal/` | PyInstaller onedir FastAPI server |
| `ui/web/` | Product UI (also embedded in API datas) |
| `vendor/ffmpeg/` | Optional LGPL `ffmpeg` / `ffprobe` (see README there) |
| `vendor/models/` | Optional Whisper weights (or download on first-run consent) |
| `LICENCE_NOTES.md` | Licence summary |

## Build prerequisites (Windows)

- Python 3.11+
- `pip install -e ".[dev]" pyinstaller`
- [Inno Setup 6](https://jrsoftware.org/isinfo.php) for `ReelwrightSetup.exe`
- Optional: drop LGPL ffmpeg builds into `vendor/ffmpeg/` before `build.ps1`

## First-run (in UI)

1. FFmpeg check (PATH or vendored)
2. Transcription model consent (skip allowed)
3. Projects folder (writable) — default `%LOCALAPPDATA%\Reelwright\projects`

## Developer run

```bash
pip install -e ".[dev]"
python3 -m reelwright.api.server
# open http://127.0.0.1:8765/
```

Env overrides: `REELWRIGHT_DATA`, `REELWRIGHT_VENDOR`, `REELWRIGHT_UI`, `REELWRIGHT_FS_ROOTS`.

## Follow-ups

- Code signing and auto-updater
- Optional Tauri shell (out of scope for this installer path)
- Do not bundle AGPL aligners in the default installer
