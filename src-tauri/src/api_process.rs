//! Lifecycle of the local Reelwrite API.
//!
//! Packaged: `reelwrite-api.exe` sits next to `Reelwrite.exe` (see
//! `packaging/windows/build.ps1`). Dev: `python -m reelwrite.api.server` from the repo root.

use std::io;
use std::path::{Path, PathBuf};
use std::process::{Child, Command};
use std::sync::Mutex;

use tauri::{AppHandle, Manager};

use crate::pid;

#[cfg(windows)]
const API_EXE: &str = "reelwrite-api.exe";
#[cfg(not(windows))]
const API_EXE: &str = "reelwrite-api";

#[cfg(windows)]
const PYTHON: &str = "python";
#[cfg(not(windows))]
const PYTHON: &str = "python3";

/// The API child, if this shell started one. Managed state so the run-loop can reach it.
#[derive(Default)]
pub struct ApiProcess(Mutex<Option<Child>>);

/// Start the API unless we already own a child process.
pub fn start(app: &AppHandle) -> io::Result<()> {
    let state = app.state::<ApiProcess>();
    let mut slot = state.0.lock().expect("api process mutex poisoned");
    if slot.is_some() {
        return Ok(());
    }
    let child = spawn()?;
    pid::write(pid::API, child.id());
    *slot = Some(child);
    Ok(())
}

/// Kill the API process tree. Idempotent: safe to call for both close and exit events.
pub fn shutdown(app: &AppHandle) {
    let taken = app
        .state::<ApiProcess>()
        .0
        .lock()
        .ok()
        .and_then(|mut slot| slot.take());
    if let Some(mut child) = taken {
        kill_tree(&mut child);
        let _ = child.wait();
        pid::clear(pid::API);
    }
}

fn spawn() -> io::Result<Child> {
    let bundle = exe_dir();
    let packaged = bundle.join(API_EXE);
    let (root, mut command) = if packaged.is_file() {
        (bundle, Command::new(&packaged))
    } else {
        let mut dev = Command::new(PYTHON);
        dev.args(["-m", "reelwrite.api.server"]);
        (repo_root(), dev)
    };

    // Mirror launcher.py: run from the bundle root and point the API at sibling assets.
    command.current_dir(&root);
    for (key, dir) in [
        ("REELWRITE_UI", root.join("ui").join("web")),
        ("REELWRITE_VENDOR", root.join("vendor")),
    ] {
        if dir.is_dir() {
            command.env(key, dir);
        }
    }
    hide_console_window(&mut command);
    command.spawn()
}

fn exe_dir() -> PathBuf {
    std::env::current_exe()
        .ok()
        .as_deref()
        .and_then(Path::parent)
        .map(Path::to_path_buf)
        .unwrap_or_else(|| PathBuf::from("."))
}

/// Dev-only fallback: the checkout this binary was compiled from.
fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .map(Path::to_path_buf)
        .unwrap_or_else(|| PathBuf::from("."))
}

/// Uvicorn spawns no children today, but PyInstaller onedir builds and multiprocessing
/// workers can, so kill the whole tree rather than just the direct child.
#[cfg(windows)]
fn kill_tree(child: &mut Child) {
    let mut taskkill = Command::new("taskkill");
    taskkill.args(["/PID", &child.id().to_string(), "/T", "/F"]);
    hide_console_window(&mut taskkill);
    let killed = taskkill.status().map(|s| s.success()).unwrap_or(false);
    if !killed {
        let _ = child.kill();
    }
}

#[cfg(not(windows))]
fn kill_tree(child: &mut Child) {
    let _ = child.kill();
}

/// CREATE_NO_WINDOW: without it every spawn flashes a console window on Windows.
#[cfg(windows)]
fn hide_console_window(command: &mut Command) {
    use std::os::windows::process::CommandExt;
    const CREATE_NO_WINDOW: u32 = 0x0800_0000;
    command.creation_flags(CREATE_NO_WINDOW);
}

#[cfg(not(windows))]
fn hide_console_window(_command: &mut Command) {}
