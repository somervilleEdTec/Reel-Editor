// Hide the console window on Windows release builds; the API child gets its own
// (suppressed) console, see api_process::hide_console_window.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

//! Reelwright desktop shell.
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
        .expect("failed to build the Reelwright shell")
        .run(|app, event| match event {
            RunEvent::ExitRequested { .. } | RunEvent::Exit => {
                api_process::shutdown(app);
                pid::clear(pid::SHELL);
            }
            _ => {}
        });
}

/// Start the API and navigate to it. An API already on 8765 (a dev server, say) is
/// reused as-is, and left running when the shell exits.
fn boot(app: &AppHandle) {
    if !health::is_healthy(API_ADDR, HEALTH_PATH) {
        if let Err(err) = api_process::start(app) {
            report(app, &format!("Could not start the Reelwright API: {err}"));
            return;
        }
        if !health::wait_until_healthy(API_ADDR, HEALTH_PATH, STARTUP_TIMEOUT) {
            report(app, "The Reelwright API did not respond on 127.0.0.1:8765.");
            return;
        }
    }

    let Ok(url) = API_URL.parse() else { return };
    if let Some(window) = app.get_webview_window("main") {
        if let Err(err) = window.navigate(url) {
            report(app, &format!("Could not open the Reelwright UI: {err}"));
        }
    }
}

/// Surface a startup failure on the splash page (and to stderr for logs).
fn report(app: &AppHandle, message: &str) {
    eprintln!("[reelwright] {message}");
    if let Some(window) = app.get_webview_window("main") {
        let script = format!("window.reelwrightError?.({})", json_string(message));
        let _ = window.eval(&script);
    }
}

fn json_string(value: &str) -> String {
    let escaped = value.replace('\\', r"\\").replace('"', r#"\""#);
    format!("\"{}\"", escaped.replace('\n', " "))
}
