@echo off
REM ============================================================
REM Cortex — Windows Build Script (PyInstaller)
REM Compiles Python source into a single standalone .exe
REM Requirements: Python 3.12, pyinstaller (pip install pyinstaller)
REM ============================================================

cd /d "%~dp0"

echo ==================================================
echo   Cortex Windows Build  (PyInstaller)
echo ==================================================

REM ── 0. Check PyInstaller is installed ────────────────────
echo [Step 0] Checking PyInstaller...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed.
    echo Run: pip install pyinstaller
    exit /b 1
)
echo    PyInstaller found.

REM ── 1. Read version ──────────────────────────────────────
set /p VERSION=<version.txt
echo Version: %VERSION%

REM ── 2. Clean previous build output ──────────────────────
echo.
echo [Step 1] Cleaning previous build output...
if exist dist     rmdir /s /q dist
if exist build    rmdir /s /q build
if exist Cortex.spec del /f /q Cortex.spec
echo    Done.

REM ── 3. Compile with PyInstaller ─────────────────────────
echo.
echo [Step 2] Compiling with PyInstaller...
echo    This may take 5-15 minutes. Please wait.
"%~dp0venv\Scripts\python.exe" -m PyInstaller ^
  --clean ^
  --onefile ^
  --noconsole ^
  --icon="%~dp0icon.ico" ^
  --name=Cortex ^
  --add-data="%~dp0data;data" ^
  --add-data="%~dp0piper_engine;piper_engine" ^
  --add-data="%~dp0icon.png;." ^
  --add-data="%~dp0icon.ico;." ^
  --add-data="%~dp0version.txt;." ^
  --hidden-import=sklearn ^
  --hidden-import=sklearn.utils._cython_blas ^
  --hidden-import=sklearn.neighbors.typedefs ^
  --hidden-import=sklearn.neighbors._partition_nodes ^
  --hidden-import=faster_whisper ^
  --hidden-import=pyttsx3 ^
  --hidden-import=pyttsx3.drivers ^
  --hidden-import=pyttsx3.drivers.sapi5 ^
  --hidden-import=winshell ^
  --hidden-import=win32com ^
  --hidden-import=win32com.client ^
  --collect-all faster_whisper ^
  --collect-all sklearn ^
  --collect-all ctranslate2 ^
  --collect-all tokenizers ^
  --collect-submodules=components ^
  --collect-submodules=core ^
  --add-binary="%~dp0venv\Lib\site-packages\ctranslate2\ctranslate2.dll;ctranslate2" ^
  --add-binary="%~dp0venv\Lib\site-packages\ctranslate2\libiomp5md.dll;ctranslate2" ^
  --add-binary="%~dp0venv\Lib\site-packages\ctranslate2\_ext.cp312-win_amd64.pyd;ctranslate2" ^
  --runtime-hook="%~dp0pyi_rthook_ctranslate2.py" ^
  "%~dp0main.py"

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller compilation failed. Check messages above.
    exit /b 1
)

REM ── 4. Report ────────────────────────────────────────────
echo.
echo [Step 3] Finalizing output...
if exist "%~dp0dist\Cortex.exe" (
    echo    SUCCESS! Executable is ready at: dist\Cortex.exe
    for %%A in ("%~dp0dist\Cortex.exe") do echo    File size: %%~zA bytes
) else (
    echo    WARNING: Expected dist\Cortex.exe not found. Check build log.
)

echo.
echo ==================================================
echo   Build complete!
echo   Single file executable: dist\Cortex.exe
echo ==================================================
