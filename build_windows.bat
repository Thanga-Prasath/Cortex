@echo off
echo ============================================================
echo   Cortex Desktop App — Windows Build
echo ============================================================
echo.

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found. Run setup.py first.
    pause
    exit /b 1
)

REM Install PyInstaller if not present
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Convert icons
echo.
echo Converting icons...
python convert_icon.py

REM Build with PyInstaller
echo.
echo Building Cortex with PyInstaller...
pyinstaller cortex.spec --noconfirm

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Build Complete!
echo   Output: dist\Cortex\Cortex.exe
echo ============================================================
echo.
echo Next steps:
echo   1. Test: dist\Cortex\Cortex.exe
echo   2. Create installer: Compile installer\windows\cortex_setup.iss with Inno Setup
echo.
pause
