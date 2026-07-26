# Windows packaging path

End users download **ReelwrightSetup.exe** from
[GitHub Releases](https://github.com/somervilleEdTec/Reel-Editor/releases).
The `.exe` is a build artifact (gitignored under `dist/`) — it is **not** committed to git.

## Publish via GitHub Actions (recommended)

Workflow: `.github/workflows/release-windows.yml` (**Release Windows Package**).

1. Push a version tag, or run the workflow manually:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
   Or: **Actions → Release Windows Package → Run workflow** (enter `v0.1.0`).
2. The Windows runner installs Python + Inno Setup, fetches FFmpeg essentials,
   runs `packaging/windows/build.ps1 -FetchFfmpeg`, and creates a GitHub Release
   with `ReelwrightSetup.exe` attached.
3. End users install from the Releases page.

## End-user install

1. Download `ReelwrightSetup.exe` from the latest Release
2. Installer writes to `%LOCALAPPDATA%\Reelwright` (per-user, no admin)
3. Start Menu **Reelwright** runs the launcher: local API on `127.0.0.1:8765`, opens the browser

## Local build (optional)

```powershell
powershell -ExecutionPolicy Bypass -File packaging/windows/build.ps1 -Version 0.1.0 -FetchFfmpeg
```

Output: `dist/windows/installer/ReelwrightSetup.exe` (do not commit).

## Bundle contents

| Path | Purpose |
|------|---------|
| `Reelwright.exe` | Launcher (health-check, start API, open browser) |
| `reelwright-api.exe` + `_internal/` | PyInstaller onedir FastAPI server |
| `ui/web/` | Product UI (also embedded in API datas) |
| `vendor/ffmpeg/` | Optional `ffmpeg` / `ffprobe` (fetched in CI with `-FetchFfmpeg`) |
| `vendor/models/` | Optional Whisper weights (or download on first-run consent) |
| `LICENCE_NOTES.md` | Licence summary |

## Build prerequisites (Windows)

- Python 3.11+
- `pip install -e ".[dev]" pyinstaller`
- [Inno Setup 6](https://jrsoftware.org/isinfo.php) for `ReelwrightSetup.exe`
- Optional: `-FetchFfmpeg` or drop builds into `vendor/ffmpeg/` (see README there)

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

Env overrides: `REELWRIGHT_DATA`, `REELWRIGHT_VENDOR`, `REELWRIGHT_UI`, `REELWRIGHT_FS_ROOTS`, `REELWRIGHT_ROOT`.

## Follow-ups

- Code signing and auto-updater
- Optional Tauri shell (out of scope for this installer path)
- Do not bundle AGPL aligners in the default installer
