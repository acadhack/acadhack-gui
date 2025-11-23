@echo off
cd /d "%~dp0"

set VENV_DIR=.venv

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in your PATH.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if virtual environment exists
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    
    echo Installing dependencies...
    call "%VENV_DIR%\Scripts\activate.bat"
    python -m pip install --upgrade pip
    
    :: Install requirements (unified file)
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo [WARNING] Some dependencies failed to install. 
        echo Attempting to proceed...
    )
) else (
    call "%VENV_DIR%\Scripts\activate.bat"
)

:: Run the application
echo Starting AcadHack...
python app_webview.py
pause
