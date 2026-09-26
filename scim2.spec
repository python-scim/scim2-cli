# -*- mode: python ; coding: utf-8 -*-

import os

a = Analysis(
    ["scim2_cli/__init__.py"],
    pathex=[],
    binaries=[],
    data=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

# Use PYINSTALLER_ONEDIR=1 for faster builds
onedir_mode = os.environ.get("PYINSTALLER_ONEDIR", "0") == "1"

if onedir_mode:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="scim2",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
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
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="scim2",
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="scim2",
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
