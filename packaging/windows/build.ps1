# Build Windows bundle + installer (run on Windows with PyInstaller + Inno Setup)
# Usage: powershell -ExecutionPolicy Bypass -File packaging/windows/build.ps1

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Dist = Join-Path $Root "dist\windows"
$Bundle = Join-Path $Dist "bundle"

Write-Host "Root: $Root"
Remove-Item -Recurse -Force $Dist -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $Bundle | Out-Null

Push-Location $Root
try {
  python -m pip install -e ".[dev]" pyinstaller
  pyinstaller --noconfirm --clean packaging/windows/reelwright-api.spec
  pyinstaller --noconfirm --clean packaging/windows/launcher.spec

  Copy-Item -Recurse "dist\reelwright-api\*" $Bundle
  Copy-Item "dist\Reelwright.exe" (Join-Path $Bundle "Reelwright.exe")

  # UI next to launcher (also inside _internal from PyInstaller datas)
  New-Item -ItemType Directory -Path (Join-Path $Bundle "ui") -Force | Out-Null
  Copy-Item -Recurse "ui\web" (Join-Path $Bundle "ui\web")

  # Vendor placeholders
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
    & $iscc "packaging\windows\Reelwright.iss"
    Write-Host "Installer: dist\windows\installer\ReelwrightSetup.exe"
  } else {
    Write-Warning "Inno Setup not found; bundle ready at dist\windows\bundle"
  }
}
finally {
  Pop-Location
}
