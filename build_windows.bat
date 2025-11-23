@echo off
echo ==========================================
echo Building AcadHack for Windows...
echo ==========================================

:: Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found! Please run run_windows.bat first.
    pause
    exit /b 1
)

:: Install PyInstaller if not present
pip install pyinstaller
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)

:: Run PyInstaller
echo Running PyInstaller...
pyinstaller --clean --noconfirm app_webview.spec

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo BUILD SUCCESSFUL!
    echo Executable located at: dist\AcadHack.exe
    echo ==========================================
) else (
    echo.
    echo [ERROR] Build failed. Check the logs above.
)

pause
