# -*- mode: python ; coding: utf-8 -*-

import platform
import os

# Determine the target architecture
arch = platform.machine()

# Define the path to chromedriver based on architecture
chromedriver = 'chromedriver_mac_arm' if arch == 'arm64' else 'chromedriver_mac_x'

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[(chromedriver, '.')],  # Include the chromedriver binary
    datas=[('templates', 'templates'), ('static', 'static')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=False,  # Include all binaries
    name=f'run_{arch}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
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
    name=f'run_{arch}',
)
