//! PID files, matching `reelwright.pid_file` so `uninstall_kill.ps1` can stop us:
//! `%LOCALAPPDATA%\Reelwright\{reelwright,api}.pid` (or `$REELWRIGHT_DATA`).

use std::path::PathBuf;

pub const SHELL: &str = "reelwright";
pub const API: &str = "api";

pub fn write(name: &str, pid: u32) {
    let path = pid_path(name);
    if let Some(dir) = path.parent() {
        let _ = std::fs::create_dir_all(dir);
    }
    let _ = std::fs::write(path, pid.to_string());
}

pub fn clear(name: &str) {
    let _ = std::fs::remove_file(pid_path(name));
}

fn pid_path(name: &str) -> PathBuf {
    data_dir().join(format!("{name}.pid"))
}

/// Mirrors `reelwright.paths.app_data_dir()`.
fn data_dir() -> PathBuf {
    match std::env::var_os("REELWRIGHT_DATA") {
        Some(dir) => PathBuf::from(dir),
        None => default_data_dir(),
    }
}

#[cfg(windows)]
fn default_data_dir() -> PathBuf {
    std::env::var_os("LOCALAPPDATA")
        .map(PathBuf::from)
        .unwrap_or_else(|| home().join("AppData").join("Local"))
        .join("Reelwright")
}

#[cfg(not(windows))]
fn default_data_dir() -> PathBuf {
    match std::env::var_os("XDG_DATA_HOME") {
        Some(xdg) => PathBuf::from(xdg).join("reelwright"),
        None => home().join(".local").join("share").join("reelwright"),
    }
}

fn home() -> PathBuf {
    #[cfg(windows)]
    let key = "USERPROFILE";
    #[cfg(not(windows))]
    let key = "HOME";
    std::env::var_os(key).map(PathBuf::from).unwrap_or_default()
}
