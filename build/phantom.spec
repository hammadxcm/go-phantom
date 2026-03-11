# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Phantom."""

import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH).parent

a = Analysis(
    [str(root / "phantom" / "__main__.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "phantom" / "config" / "defaults.json"), "phantom/config"),
    ],
    hiddenimports=[
        "pynput.keyboard._xorg",
        "pynput.keyboard._darwin",
        "pynput.keyboard._win32",
        "pynput.mouse._xorg",
        "pynput.mouse._darwin",
        "pynput.mouse._win32",
        "pystray._darwin",
        "pystray._win32",
        "pystray._xorg",
        "rich",
        "rich.logging",
        "rich.live",
        "rich.layout",
        "rich.panel",
        "rich.table",
        "rich.text",
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="phantom",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
