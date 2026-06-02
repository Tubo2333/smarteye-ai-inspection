@echo off
cd /d "%~dp0"
title SmartEye Desktop

echo ================================================
echo   SmartEye - Desktop Edition
echo   Starting up, please wait...
echo ================================================
echo.

REM --- Find Python ---
set PYTHON=
if exist "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" set PYTHON=C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe
if not defined PYTHON (
    py --version >nul 2>&1 && set PYTHON=py
)
if not defined PYTHON (
    python --version >nul 2>&1 && set PYTHON=python
)
if not defined PYTHON (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

REM --- Create venv if needed ---
if not exist "venv\Scripts\python.exe" (
    echo [1/2] Creating virtual environment...
    %PYTHON% -m venv venv
    echo [OK] venv created
) else (
    echo [OK] venv exists
)

REM --- Install pywebview if needed ---
echo [2/2] Checking pywebview...
venv\Scripts\python.exe -c "import webview" 2>nul
if errorlevel 1 (
    echo        Installing pywebview...
    venv\Scripts\pip.exe install pywebview -i https://pypi.tuna.tsinghua.edu.cn/simple
)

REM --- Launch desktop app ---
echo.
echo Launching SmartEye Desktop...
echo Console will hide automatically after window opens.
echo Close the SmartEye window to exit completely.
start "" venv\Scripts\python.exe desktop_app.py

echo.
echo ================================================
echo SmartEye Desktop closed.
echo ================================================
pause
