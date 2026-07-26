// Hide the console window on Windows release builds; the API child gets its own
// (suppressed) console, see api_process::hide_console_window.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

//! Reelwrite desktop shell.
//!
//! Boots the local FastAPI server, waits for `/health`, then points the WebView at
//! `http://127.0.0.1:8765/` so the UI in `ui/web/` runs same-origin against the API.

mod api_process;
mod health;
mod pid;
mod single_instance;

use std::time::Duration;

use tauri::{AppHandle, Manager, RunEvent};

const API_ADDR: &str = "127.0.0.1:8765";
const API_URL: &str = "http://127.0.0.1:8765/";
const HEALTH_PATH: &str = "/health";
const STARTUP_TIMEOUT: Duration = Duration::from_secs(60);

fn main() {
    single_instance::acquire();
    pid::write(pid::SHELL, std::process::id());

    tauri::Builder::default()
        .manage(api_process::ApiProcess::default())
        .setup(|app| {
            let handle = app.handle().clone();
            // Health polling blocks; keep it off the UI thread so the splash paints.
            std::thread::spawn(move || boot(&handle));
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("failed to build the Reelwrite shell")
        .run(|app, event| match event {
            RunEvent::ExitRequested { .. } | RunEvent::Exit => {
                api_process::shutdown(app);
                pid::clear(pid::SHELL);
            }
            _ => {}
        });
}

/// Start the API and navigate to it.
///
/// An API already on 8765 is reused only when its `/health` platform matches this
/// shell (so a Linux/cloud forward on the same port cannot reject Windows paths).
fn boot(app: &AppHandle) {
    if let Some(info) = health::health_info(API_ADDR, HEALTH_PATH) {
        if info.ok {
            if platform_compatible(info.platform.as_deref()) {
                navigate(app);
                return;
            }
            let remote = info.platform.as_deref().unwrap_or("unknown");
            report(
                app,
                &format!(
                    "Port 8765 is already serving a Reelwrite API for {remote}, \
                     but this Windows app needs a Windows API. Close the other \
                     process (or stop the port forward), then restart Reelwrite."
                ),
            );
            return;
        }
    }

    if let Err(err) = api_process::start(app) {
        report(app, &format!("Could not start the Reelwrite API: {err}"));
        return;
    }
    if !health::wait_until_healthy(API_ADDR, HEALTH_PATH, STARTUP_TIMEOUT) {
        report(app, "The Reelwrite API did not respond on 127.0.0.1:8765.");
        return;
    }
    navigate(app);
}

fn navigate(app: &AppHandle) {
    let Ok(url) = API_URL.parse() else { return };
    if let Some(window) = app.get_webview_window("main") {
        if let Err(err) = window.navigate(url) {
            report(app, &format!("Could not open the Reelwrite UI: {err}"));
        }
    }
}

fn platform_compatible(remote: Option<&str>) -> bool {
    // Older APIs omit platform — allow reuse for local dev servers.
    let Some(remote) = remote else { return true };
    #[cfg(windows)]
    {
        remote == "win32"
    }
    #[cfg(not(windows))]
    {
        remote != "win32"
    }
}

/// Surface a startup failure on the splash page (and to stderr for logs).
fn report(app: &AppHandle, message: &str) {
    eprintln!("[reelwrite] {message}");
    if let Some(window) = app.get_webview_window("main") {
        let script = format!("window.reelwriteError?.({})", json_string(message));
        let _ = window.eval(&script);
    }
}

fn json_string(value: &str) -> String {
    let escaped = value.replace('\\', r"\\").replace('"', r#"\""#);
    format!("\"{}\"", escaped.replace('\n', " "))
}
