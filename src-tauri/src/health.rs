//! Loopback health probe.
//!
//! A hand-rolled HTTP/1.1 GET keeps the shell dependency-free: an HTTP client crate
//! would drag in TLS machinery we never use when talking to 127.0.0.1.

use std::io::{Read, Write};
use std::net::TcpStream;
use std::time::{Duration, Instant};

const POLL_INTERVAL: Duration = Duration::from_millis(250);
const SOCKET_TIMEOUT: Duration = Duration::from_millis(1500);

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HealthInfo {
    pub ok: bool,
    /// `sys.platform` from the API when present (`win32`, `linux`, …).
    pub platform: Option<String>,
}

/// One probe: true when `addr` answers `path` with HTTP 200 right now.
pub fn is_healthy(addr: &str, path: &str) -> bool {
    probe(addr, path).map(|h| h.ok).unwrap_or(false)
}

/// Probe with platform metadata from the JSON body when available.
pub fn health_info(addr: &str, path: &str) -> Option<HealthInfo> {
    probe(addr, path).ok()
}

/// Poll `addr` until it answers `path` with HTTP 200, or `timeout` elapses.
pub fn wait_until_healthy(addr: &str, path: &str, timeout: Duration) -> bool {
    let deadline = Instant::now() + timeout;
    loop {
        if is_healthy(addr, path) {
            return true;
        }
        if Instant::now() >= deadline {
            return false;
        }
        std::thread::sleep(POLL_INTERVAL);
    }
}

fn probe(addr: &str, path: &str) -> std::io::Result<HealthInfo> {
    let mut stream = TcpStream::connect(addr)?;
    stream.set_read_timeout(Some(SOCKET_TIMEOUT))?;
    stream.set_write_timeout(Some(SOCKET_TIMEOUT))?;

    let request =
        format!("GET {path} HTTP/1.1\r\nHost: {addr}\r\nConnection: close\r\nAccept: */*\r\n\r\n");
    stream.write_all(request.as_bytes())?;

    let mut buf = Vec::new();
    stream.read_to_end(&mut buf)?;
    let text = String::from_utf8_lossy(&buf);
    let status_ok = text
        .lines()
        .next()
        .map(|line| line.starts_with("HTTP/1.") && line.contains(" 200"))
        .unwrap_or(false);
    if !status_ok {
        return Ok(HealthInfo {
            ok: false,
            platform: None,
        });
    }
    let platform = json_string_field(&text, "platform");
    Ok(HealthInfo {
        ok: true,
        platform,
    })
}

/// Tiny extractor for `"platform":"win32"` without a JSON dependency.
fn json_string_field(body: &str, key: &str) -> Option<String> {
    let needle = format!("\"{key}\"");
    let idx = body.find(&needle)?;
    let after = &body[idx + needle.len()..];
    let colon = after.find(':')?;
    let rest = after[colon + 1..].trim_start();
    if !rest.starts_with('"') {
        return None;
    }
    let inner = &rest[1..];
    let end = inner.find('"')?;
    Some(inner[..end].to_string())
}

#[cfg(test)]
mod tests {
    use super::json_string_field;

    #[test]
    fn parses_platform() {
        let body = r#"{"ok":true,"version":"3.0.3","platform":"win32","frozen":true}"#;
        assert_eq!(json_string_field(body, "platform").as_deref(), Some("win32"));
    }
}
