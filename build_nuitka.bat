@echo off
REM ============================================================
REM  XRD Analysis - Nuitka ビルドスクリプト
REM
REM  【狙い】
REM   PyInstaller は実行時に .pyc を都度ロードするが、
REM   Nuitka は Python を C にコンパイルするため起動が 2〜3 倍速くなる。
REM
REM  【前提】
REM   pip install nuitka zstandard ordered-set
REM
REM  【出力】
REM   dist_nuitka\XRD解析プログラム.dist\ フォルダ内に実行ファイル一式
REM ============================================================

setlocal

REM ---- Python インタープリタを venv から参照 ----
set PYTHON=venv\Scripts\python.exe
if not exist %PYTHON% (
    set PYTHON=python
)

REM ---- 出力先 ----
set OUT_DIR=dist_nuitka

echo [1/2] splash.png を生成します...
%PYTHON% create_splash.py

echo [2/2] Nuitka でビルドします（初回は数分かかります）...
%PYTHON% -m nuitka ^
    --standalone ^
    --windows-disable-console ^
    --windows-icon-from-ico=assets\XRD_ANALYSIS_ICON.ico ^
    --output-dir=%OUT_DIR% ^
    --output-filename=XRD解析プログラム.exe ^
    --enable-plugin=tk-inter ^
    --include-data-dir=assets=assets ^
    --include-package=sv_ttk ^
    --include-package=tkinterdnd2 ^
    --include-package-data=sv_ttk ^
    --include-package-data=tkinterdnd2 ^
    --include-package-data=matplotlib ^
    --include-package-data=scipy ^
    --nofollow-import-to=matplotlib.tests ^
    --nofollow-import-to=matplotlib.testing ^
    --nofollow-import-to=matplotlib.sphinxext ^
    --nofollow-import-to=scipy.io.matlab.tests ^
    --nofollow-import-to=tkinter.test ^
    --nofollow-import-to=unittest ^
    --nofollow-import-to=setuptools ^
    --nofollow-import-to=pkg_resources ^
    --nofollow-import-to=IPython ^
    --windows-product-name="XRD Analysis" ^
    --windows-file-version=1.0.0.0 ^
    --windows-company-name="XRD Analysis" ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] ビルドに失敗しました。上記のエラーメッセージを確認してください。
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  ビルド完了！
echo  実行ファイル: %OUT_DIR%\main.dist\XRD解析プログラム.exe
echo ============================================================
pause
