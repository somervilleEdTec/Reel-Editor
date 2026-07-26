# Build Windows bundle + installer (run on Windows with PyInstaller + Inno Setup)
# Usage:
#   powershell -ExecutionPolicy Bypass -File packaging/windows/build.ps1
#   powershell -ExecutionPolicy Bypass -File packaging/windows/build.ps1 -Version 0.1.1
#   powershell -ExecutionPolicy Bypass -File packaging/windows/build.ps1 -FetchFfmpeg

param(
  [string]$Version = "0.1.0",
  [switch]$FetchFfmpeg
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
  pyinstaller --noconfirm --clean packaging/windows/reelwright-api.spec
  python packaging/windows/verify_frozen_modules.py
  pyinstaller --noconfirm --clean packaging/windows/launcher.spec

  Copy-Item -Recurse "dist\reelwright-api\*" $Bundle
  Copy-Item "dist\Reelwright.exe" (Join-Path $Bundle "Reelwright.exe")

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
    & $iscc "/DMyAppVersion=$Version" "packaging\windows\Reelwright.iss"
    $setup = Join-Path $Dist "installer\ReelwrightSetup.exe"
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
