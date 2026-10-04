@echo off
chcp 65001 >nul
setlocal

:: Get script directory (works even from shortcuts or "Run as")
set "SCRIPT_DIR=%~dp0"

:: Check venv exists
if not exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    echo.
    echo  ╔══════════════════════════════════════════════════════╗
    echo  ║  Mu(syr)ic hasn't been installed yet!               ║
    echo  ║  Please run install.bat first, then try again.      ║
    echo  ╚══════════════════════════════════════════════════════╝
    echo.
    pause
    exit /b 1
)

:: Set window title
title Mu(syr)ic - Music Album Downloader

:: Activate venv and launch interactive app
call "%SCRIPT_DIR%.venv\Scripts\activate.bat"
python -m musyric.app

:: Keep window open if app crashed
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Something went wrong. Press any key to close...
    pause >nul
)
