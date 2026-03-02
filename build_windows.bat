@echo off
REM ============================================================
REM Cortex — Windows Local Build Script
REM Run this on a Windows machine to produce the .exe installer
REM Requirements: Python 3.12, Inno Setup 6
REM ============================================================

echo ==================================================
echo   Cortex Windows Build
echo ==================================================

REM ── 1. Read version ──────────────────────────────────────
set /p VERSION=<version.txt
echo Version: %VERSION%

REM ── 2. Install PyInstaller ────────────────────────────────
echo.
echo [Step 1] Installing PyInstaller...
pip install pyinstaller --quiet
if errorlevel 1 ( echo ERROR: pip failed & exit /b 1 )

REM ── 3. Build with PyInstaller ────────────────────────────
echo.
echo [Step 2] Building executable...
pyinstaller ^
  --onedir ^
  --windowed ^
  --name Cortex ^
  --icon=icon.ico ^
  --add-data "icon.png;." ^
  --add-data "icon.ico;." ^
  --add-data "version.txt;." ^
  --add-data "components;components" ^
  --add-data "core;core" ^
  --add-data "data;data" ^
  --add-data "scripts;scripts" ^
  --exclude-module piper_engine ^
  main.py

if errorlevel 1 ( echo ERROR: PyInstaller failed & exit /b 1 )
echo ✅ PyInstaller done

REM ── 4. Copy launcher and icon into dist ───────────────────
echo.
echo [Step 3] Copying launcher files...
copy launcher.py dist\Cortex\launcher.py
copy version.txt dist\Cortex\version.txt
copy icon.png    dist\Cortex\icon.png
copy icon.ico    dist\Cortex\icon.ico

REM ── 5. Run Inno Setup ────────────────────────────────────
echo.
echo [Step 4] Creating installer with Inno Setup...
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
    set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
)
%ISCC% installer\windows\cortex_setup.iss
if errorlevel 1 ( echo ERROR: Inno Setup failed & exit /b 1 )

echo.
echo ==================================================
echo   ✅  Windows build complete!
echo   File: installer\windows\Output\Cortex-Setup-%VERSION%-Windows.exe
echo ==================================================
