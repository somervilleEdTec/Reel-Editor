# Reelwrite desktop shell (Tauri 2)

Native window that owns the local API and renders the existing UI. It is **not** a
rewrite of `ui/web/` — the shell boots `reelwrite-api.exe`, waits for
`http://127.0.0.1:8765/health`, then navigates the WebView to `http://127.0.0.1:8765/`
so the vanilla-JS UI keeps running same-origin against FastAPI.

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Rust (stable, 1.88+) | [rustup.rs](https://rustup.rs). Windows: the `x86_64-pc-windows-msvc` toolchain |
| Visual Studio Build Tools | "Desktop development with C++" — supplies the MSVC linker and `rc.exe` |
| WebView2 runtime | Preinstalled on Windows 10 21H2+/11; otherwise install the [evergreen bootstrapper](https://developer.microsoft.com/microsoft-edge/webview2/) |
| Python 3.11+ | Only for the dev fallback (`python -m reelwrite.api.server`) |

No Node toolchain and no `@tauri-apps/cli` are required: the shell serves a static
splash page from `splash/` and everything else comes from the API.

## Build

```powershell
cd src-tauri
cargo build --release        # -> target/release/Reelwrite.exe
```

`packaging/windows/build.ps1` runs the same command and copies the result into
`dist/windows/bundle/Reelwrite.exe`, which Inno Setup installs. Pass `-SkipTauri` to
build the Python-only bundle instead.

## Run in development

```bash
cargo run    # from src-tauri/
```

With no sibling `reelwrite-api.exe`, the shell falls back to
`python -m reelwrite.api.server` from the repo root, so run `pip install -e ".[dev]"`
first. If an API is already listening on 8765 it is reused and left running on exit.

## Layout

| Path | Purpose |
|------|---------|
| `src/main.rs` | Window setup, startup sequence, exit handling |
| `src/api_process.rs` | Spawn/kill the API child (Windows process-tree kill) |
| `src/health.rs` | Dependency-free loopback `/health` poll |
| `src/pid.rs` | Records the API PID under the app data dir |
| `splash/index.html` | Static "starting…" page shown until the API answers |
| `capabilities/default.json` | Core window permissions only; no plugin APIs exposed |
| `icons/make_icon.py` | Regenerates the placeholder `icons/icon.ico` |

## Process lifecycle

The shell only kills an API it started itself. On Windows it uses
`taskkill /PID <pid> /T /F` so PyInstaller's child processes go down with the parent;
elsewhere it sends a plain kill. The child PID is written to `api.pid` in the app data
dir (`%APPDATA%\uk.co.somervilleedtec.reelwrite`) and removed on clean exit.
