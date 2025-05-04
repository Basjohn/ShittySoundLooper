@echo off
echo Building ShittySoundLooper executable...
echo.

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Build the executable
pyinstaller --clean build_exe.spec

echo.
if %errorlevel% equ 0 (
    echo Build successful! Executable is in dist\ShittySoundLooper folder.
) else (
    echo Build failed. Please check the error messages.
)

pause
