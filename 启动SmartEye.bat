@echo off
cd /d "%~dp0"
title SmartEye Launcher

echo ================================================
echo   SmartEye - AI Visual Inspection System
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
    echo [ERROR] Python not found. Please install Python 3.12
    echo         https://python.org
    pause
    exit /b 1
)
echo [OK] Python found

REM --- Create venv ---
if not exist "venv\Scripts\python.exe" (
    echo [1/2] Creating virtual environment...
    %PYTHON% -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv
        pause
        exit /b 1
    )
    echo [OK] venv created
) else (
    echo [OK] venv exists
)

REM --- Run ---
echo [2/2] Installing deps and starting services...
echo        First run may take 10-15 minutes. Please be patient.
echo.
call venv\Scripts\python.exe run.py

echo.
echo ================================================
if errorlevel 1 (
    echo [ERROR] Startup failed (code: %errorlevel%)
    echo Please screenshot the above and send for help
) else (
    echo SmartEye closed. Double-click this file to restart.
)
echo ================================================
pause
