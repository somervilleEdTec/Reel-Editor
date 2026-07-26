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
   with `ReelwrightSetup.exe` attached. The runner image ships Rust, so the Tauri
   shell is built too; if `cargo` is missing or the build fails, the script warns and
   ships the browser launcher instead of failing the release.
3. End users install from the Releases page.

## End-user install

1. Download `ReelwrightSetup.exe` from the latest Release
2. Installer writes to `%LOCALAPPDATA%\Reelwright` (per-user, no admin)
3. Start Menu **Reelwright** opens the desktop shell: it starts the local API on
   `127.0.0.1:8765` and renders the UI in its own window

## App shell

`Reelwright.exe` is a [Tauri 2](https://tauri.app) WebView2 window (`src-tauri/`). On
launch it spawns `reelwright-api.exe`, waits for `/health`, then navigates to
`http://127.0.0.1:8765/` — same-origin, so `ui/web/` is unchanged. Closing the window
kills the API process tree.

The browser launcher (`packaging/windows/launcher.py`) is now **legacy/fallback**: it
ships as `Reelwright-browser.exe` and is used as `Reelwright.exe` only when the bundle
is built without Rust (see `-SkipTauri` below). WebView2 is evergreen on Windows 10
21H2+/11; older images need the Microsoft bootstrapper.

## Local build (optional)

```powershell
powershell -ExecutionPolicy Bypass -File packaging/windows/build.ps1 -Version 0.1.0 -FetchFfmpeg
```

Output: `dist/windows/installer/ReelwrightSetup.exe` (do not commit).

Flags: `-SkipTauri` builds the Python-only bundle (browser launcher as
`Reelwright.exe`); `-RequireTauri` fails the build instead of falling back when the
Rust toolchain or the shell binary is missing.

## Bundle contents

| Path | Purpose |
|------|---------|
| `Reelwright.exe` | Tauri shell (starts API, health-check, WebView2 window) |
| `Reelwright-browser.exe` | Legacy launcher: starts API, opens the system browser |
| `reelwright-api.exe` + `_internal/` | PyInstaller onedir FastAPI server |
| `ui/web/` | Product UI (also embedded in API datas) |
| `vendor/ffmpeg/` | Optional `ffmpeg` / `ffprobe` (fetched in CI with `-FetchFfmpeg`) |
| `vendor/models/` | Optional Whisper weights (or download on first-run consent) |
| `uninstall_kill.ps1` | Stops running Reelwright processes during uninstall |
| `LICENCE_NOTES.md` | Licence summary |

## Uninstall

Files under `{app}` cannot be deleted while they are running, so uninstall stops
Reelwright first:

- `AppMutex=ReelwrightSingleInstance` makes the uninstaller prompt when the app is
  still open. The Tauri shell and the browser launcher both hold that mutex, and both
  record `reelwright.pid` / `api.pid`.
- An `[UninstallRun]` entry runs `uninstall_kill.ps1 -InstallDir "{app}"` before
  files are removed. It kills the pid recorded in
  `%LOCALAPPDATA%\Reelwright\reelwright.pid` (and `api.pid`), then any
  `Reelwright.exe` / `reelwright-api.exe`, then only the `ffmpeg.exe` /
  `ffprobe.exe` whose path lives under the install dir — a system-wide FFmpeg is
  never touched. It exits 0 when nothing is running.

The same logic is available to Python callers via
`reelwright.process_lifecycle.kill_reelwright_processes(install_dir)`.
User projects under `%LOCALAPPDATA%\Reelwright\projects` are kept.

## Build prerequisites (Windows)

- Python 3.11+
- `pip install -e ".[dev]" pyinstaller`
- [Inno Setup 6](https://jrsoftware.org/isinfo.php) for `ReelwrightSetup.exe`
- Rust stable 1.88+ (MSVC) + VS Build Tools for the Tauri shell — see
  [`src-tauri/README.md`](../src-tauri/README.md); skip with `-SkipTauri`
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

Or run the desktop shell, which starts that server for you:

```bash
cd src-tauri && cargo run
```

Env overrides: `REELWRIGHT_DATA`, `REELWRIGHT_VENDOR`, `REELWRIGHT_UI`, `REELWRIGHT_FS_ROOTS`, `REELWRIGHT_ROOT`.

## Follow-ups

- Code signing and auto-updater
- Real shell artwork: `src-tauri/icons/` currently holds a generated placeholder
- Bundle the WebView2 bootstrapper for pre-21H2 Windows 10 images
- Do not bundle AGPL aligners in the default installer
