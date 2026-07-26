//! Holds the named mutex declared as `AppMutex` in `Reelwright.iss`, so the uninstaller
//! notices a running app. The handle is intentionally leaked: Windows releases it when
//! the process ends, which is exactly the lifetime we want.

#[cfg(windows)]
pub fn acquire() {
    use std::ffi::OsStr;
    use std::iter::once;
    use std::os::windows::ffi::OsStrExt;
    use windows_sys::Win32::System::Threading::CreateMutexW;

    let name: Vec<u16> = OsStr::new("ReelwrightSingleInstance")
        .encode_wide()
        .chain(once(0))
        .collect();
    // SAFETY: `name` is a valid NUL-terminated wide string alive for the call.
    unsafe { CreateMutexW(std::ptr::null(), 0, name.as_ptr()) };
}

#[cfg(not(windows))]
pub fn acquire() {}
