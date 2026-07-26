# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

ROOT = Path(SPECPATH).resolve().parents[1]

a = Analysis(
    [str(ROOT / "packaging" / "windows" / "launcher.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[],
    hiddenimports=["reelwrite.process_lifecycle"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Reelwrite",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
