# -*- mode: python ; coding: utf-8 -*-
# Build on Windows: pyinstaller packaging/windows/reelwright-api.spec

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).resolve().parents[1]
SRC = ROOT / "src"
UI = ROOT / "ui" / "web"

block_cipher = None

# uvicorn.run("reelwright.api.app:app") is a dynamic string import — PyInstaller
# will not follow it. Collect the whole package and import the app in api_entry.
hiddenimports = collect_submodules("reelwright") + [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
]

a = Analysis(
    [str(ROOT / "packaging" / "windows" / "api_entry.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=[
        (str(UI), "ui/web"),
        (str(ROOT / "src" / "reelwright" / "config"), "reelwright/config"),
        (str(ROOT / "src" / "reelwright" / "captions"), "reelwright/captions"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="reelwright-api",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="reelwright-api",
)
