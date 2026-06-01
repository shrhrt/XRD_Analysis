# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules
import os

datas = [('assets/XRD_ANALYSIS_ICON.ico', 'assets')]
if os.path.exists('assets/splash.png'):
    datas += [('assets/splash.png', 'assets')]
binaries = []
hiddenimports = ['tkinterdnd2']

for pkg in ('sv_ttk', 'scipy', 'matplotlib'):
    tmp = collect_all(pkg)
    datas     += tmp[0]
    binaries  += tmp[1]
    hiddenimports += tmp[2]

hiddenimports += collect_submodules('scipy')
hiddenimports += collect_submodules('matplotlib')

# 未使用のモジュールを除外してインポート時間を短縮
EXCLUDES = [
    'matplotlib.tests',
    'matplotlib.testing',
    'matplotlib.sphinxext',
    'scipy.io.matlab.tests',
    'scipy.spatial.ckdtree',
    'tkinter.test',
    'unittest',
    'xmlrpc',
    'http.server',
    'email',
    'html',
    'docutils',
    'pydoc',
    'difflib',
    'setuptools',
    'distutils',
    'pkg_resources',
    'IPython',
    'jupyter',
    'notebook',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=1,          # 0→1: .pycの最適化レベルをアップ（assert文削除）
)
pyz = PYZ(a.pure)

# スプラッシュスクリーン（assets/splash.png が存在する場合のみ有効）
_splash_image = 'assets/splash.png'
if os.path.exists(_splash_image):
    splash = Splash(
        _splash_image,
        binaries=a.binaries,
        datas=a.datas,
        text_pos=(0, 250),
        text_size=10,
        text_color='#8ab4d4',
        minify_script=True,
        always_on_top=True,
    )
    _splash_args = [splash]
    _splash_binaries = splash.binaries
else:
    _splash_args = []
    _splash_binaries = []

exe = EXE(
    pyz,
    a.scripts,
    *_splash_args,
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
    _splash_binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='XRD解析プログラム',
)
