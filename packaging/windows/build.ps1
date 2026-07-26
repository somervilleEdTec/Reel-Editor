# Build Windows bundle + installer (run on Windows with PyInstaller + Inno Setup)
# Usage:
#   powershell -ExecutionPolicy Bypass -File packaging/windows/build.ps1
#   powershell -ExecutionPolicy Bypass -File packaging/windows/build.ps1 -Version 0.1.1
#   powershell -ExecutionPolicy Bypass -File packaging/windows/build.ps1 -FetchFfmpeg
#   powershell -ExecutionPolicy Bypass -File packaging/windows/build.ps1 -SkipTauri
#
# Shipped Reelwrite.exe is the Tauri shell (src-tauri). When Rust is unavailable, or
# with -SkipTauri, the bundle falls back to the legacy PyInstaller browser launcher.

param(
  [string]$Version = "0.1.0",
  [switch]$FetchFfmpeg,
  [switch]$SkipTauri,
  [switch]$RequireTauri
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Dist = Join-Path $Root "dist\windows"
$Bundle = Join-Path $Dist "bundle"
$VendorFfmpeg = Join-Path $Root "vendor\ffmpeg"

Write-Host "Root: $Root"
Write-Host "Version: $Version"
Remove-Item -Recurse -Force $Dist -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $Bundle | Out-Null

if ($FetchFfmpeg) {
  & (Join-Path $PSScriptRoot "fetch_ffmpeg.ps1") -DestDir $VendorFfmpeg
}

Push-Location $Root
try {
  python -m pip install -e ".[dev]" pyinstaller
  pyinstaller --noconfirm --clean packaging/windows/reelwrite-api.spec
  python packaging/windows/verify_frozen_modules.py
  pyinstaller --noconfirm --clean packaging/windows/launcher.spec

  Copy-Item -Recurse "dist\reelwrite-api\*" $Bundle

  # Tauri shell: WebView2 window that starts reelwrite-api.exe and loads 127.0.0.1:8765.
  # Needs the Rust MSVC toolchain (see src-tauri/README.md); optional so Python-only
  # machines can still produce a bundle.
  $TauriExe = Join-Path $Root "src-tauri\target\release\Reelwrite.exe"
  if (-not $SkipTauri) {
    if (Get-Command cargo -ErrorAction SilentlyContinue) {
      Push-Location (Join-Path $Root "src-tauri")
      try {
        cargo build --release --locked
        if ($LASTEXITCODE -ne 0) { throw "cargo build failed ($LASTEXITCODE)" }
      }
      catch {
        if ($RequireTauri) { throw }
        Write-Warning "Tauri build failed: $_"
      }
      finally { Pop-Location }
    }
    elseif ($RequireTauri) {
      throw "cargo not found; install Rust (https://rustup.rs) or pass -SkipTauri"
    }
    else {
      Write-Warning "cargo not found; falling back to the browser launcher"
    }
  }

  if ((-not $SkipTauri) -and (Test-Path $TauriExe)) {
    Copy-Item $TauriExe (Join-Path $Bundle "Reelwrite.exe")
    # Keep the browser launcher alongside for headless/WebView2-less fallback.
    Copy-Item "dist\Reelwrite.exe" (Join-Path $Bundle "Reelwrite-browser.exe")
  }
  else {
    if ($RequireTauri) { throw "Tauri shell missing: $TauriExe" }
    Copy-Item "dist\Reelwrite.exe" (Join-Path $Bundle "Reelwrite.exe")
  }

  Copy-Item "packaging\windows\uninstall_kill.ps1" (Join-Path $Bundle "uninstall_kill.ps1")

  New-Item -ItemType Directory -Path (Join-Path $Bundle "ui") -Force | Out-Null
  Copy-Item -Recurse "ui\web" (Join-Path $Bundle "ui\web")

  New-Item -ItemType Directory -Path (Join-Path $Bundle "vendor\ffmpeg") -Force | Out-Null
  New-Item -ItemType Directory -Path (Join-Path $Bundle "vendor\models") -Force | Out-Null
  if (Test-Path "vendor\ffmpeg") {
    Copy-Item -Recurse "vendor\ffmpeg\*" (Join-Path $Bundle "vendor\ffmpeg") -ErrorAction SilentlyContinue
  }
  Copy-Item "vendor\ffmpeg\README.md" (Join-Path $Bundle "vendor\ffmpeg\README.md") -ErrorAction SilentlyContinue
  Copy-Item "vendor\models\README.md" (Join-Path $Bundle "vendor\models\README.md") -ErrorAction SilentlyContinue
  Copy-Item "LICENCE_NOTES.md" (Join-Path $Bundle "LICENCE_NOTES.md") -ErrorAction SilentlyContinue

  $iscc = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
  ) | Where-Object { Test-Path $_ } | Select-Object -First 1

  if ($iscc) {
    & $iscc "/DMyAppVersion=$Version" "packaging\windows\Reelwrite.iss"
    $setup = Join-Path $Dist "installer\ReelwriteSetup.exe"
    if (-not (Test-Path $setup)) {
      throw "Installer missing after ISCC: $setup"
    }
    Write-Host "Installer: $setup"
  } else {
    if ($env:CI -eq "true") {
      throw "Inno Setup not found (required in CI)"
    }
    Write-Warning "Inno Setup not found; bundle ready at dist\windows\bundle"
  }
}
finally {
  Pop-Location
}
