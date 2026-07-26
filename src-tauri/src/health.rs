//! Loopback health probe.
//!
//! A hand-rolled HTTP/1.1 GET keeps the shell dependency-free: an HTTP client crate
//! would drag in TLS machinery we never use when talking to 127.0.0.1.

use std::io::{Read, Write};
use std::net::TcpStream;
use std::time::{Duration, Instant};

const POLL_INTERVAL: Duration = Duration::from_millis(250);
const SOCKET_TIMEOUT: Duration = Duration::from_millis(1500);

/// One probe: true when `addr` answers `path` with HTTP 200 right now.
pub fn is_healthy(addr: &str, path: &str) -> bool {
    probe(addr, path).unwrap_or(false)
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

fn probe(addr: &str, path: &str) -> std::io::Result<bool> {
    let mut stream = TcpStream::connect(addr)?;
    stream.set_read_timeout(Some(SOCKET_TIMEOUT))?;
    stream.set_write_timeout(Some(SOCKET_TIMEOUT))?;

    let request =
        format!("GET {path} HTTP/1.1\r\nHost: {addr}\r\nConnection: close\r\nAccept: */*\r\n\r\n");
    stream.write_all(request.as_bytes())?;

    // Exactly the status line prefix: "HTTP/1.1 200 ".
    let mut status = [0u8; 13];
    stream.read_exact(&mut status)?;
    Ok(status.starts_with(b"HTTP/1.") && status.ends_with(b" 200 "))
}
