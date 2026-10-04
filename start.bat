@echo off
setlocal
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"

if not exist "%SCRIPT_DIR%.venv\Scripts\python.exe" goto :not_installed

title Mu(syr)ic - Music Album Downloader
call "%SCRIPT_DIR%.venv\Scripts\activate.bat"
python -m musyric.app
goto :end

:not_installed
echo.
echo ========================================================
echo   Mu(syr)ic is not installed yet!
echo   Please run install.bat first, then try again.
echo ========================================================
echo.
pause
exit /b 1

:end
if errorlevel 1 (
    echo.
    echo Press any key to close...
    pause >nul
)
