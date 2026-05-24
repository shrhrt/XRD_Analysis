# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [('assets/XRD_ANALYSIS_ICON.ico', 'assets')]
binaries = []
hiddenimports = ['tkinterdnd2']

for pkg in ('sv_ttk', 'scipy', 'matplotlib'):
    tmp = collect_all(pkg)
    datas     += tmp[0]
    binaries  += tmp[1]
    hiddenimports += tmp[2]

hiddenimports += collect_submodules('scipy')
hiddenimports += collect_submodules('matplotlib')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    exclude_binaries=True,
    name='XRD解析プログラム',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    icon='assets/XRD_ANALYSIS_ICON.ico',
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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='XRD解析プログラム',
)
