@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

echo.
echo  ==============================================================
echo  ^|                                                            ^|
echo  ^|   ███╗   ███╗██╗   ██╗███████╗██╗   ██╗██████╗ ██╗ ██████╗ ^|
echo  ^|   ████╗ ████║██║   ██║██╔════╝╚██╗ ██╔╝██╔══██╗██║██╔════╝ ^|
echo  ^|   ██╔████╔██║██║   ██║███████╗ ╚████╔╝ ██████╔╝██║██║      ^|
echo  ^|   ██║╚██╔╝██║██║   ██║╚════██║  ╚██╔╝  ██╔══██╗██║██║      ^|
echo  ^|   ██║ ╚═╝ ██║╚██████╔╝███████║   ██║   ██║  ██║██║╚██████╗ ^|
echo  ^|   ╚═╝     ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝ ╚═════╝ ^|
echo  ^|                                                            ^|
echo  ==============================================================
echo.
echo 🎶 Welcome to the Mu(syr)ic One-Click Installer! 🎶
echo.

:: 1. Check Python
echo 🔍 Checking for Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ Python is not installed or not in PATH.
    echo 📦 Attempting to install Python via winget...
    winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Failed to install Python via winget. 
        echo Please download and install it manually from https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation.
        goto :error
    )
    echo ✅ Python installed successfully! Please restart the installer.
    pause
    exit /b 0
) else (
    echo ✅ Python is installed.
)

:: 2. Check FFmpeg
echo.
echo 🔍 Checking for FFmpeg...
ffmpeg -version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ FFmpeg is not installed or not in PATH.
    echo 📦 Attempting to install FFmpeg via winget...
    winget install ffmpeg --silent --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Failed to install FFmpeg via winget.
        echo Please install it manually or check your winget configuration.
        echo Download from: https://ffmpeg.org/download.html
        goto :error
    )
    echo ✅ FFmpeg installed successfully!
) else (
    echo ✅ FFmpeg is installed.
)

:: 3. Create virtual environment
echo.
echo 🐍 Creating Python virtual environment...
if not exist ".venv" (
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Failed to create virtual environment.
        goto :error
    )
    echo ✅ Virtual environment created in .venv directory.
) else (
    echo ♻️ Virtual environment already exists.
)

:: 4. Install dependencies
echo.
echo 📦 Installing dependencies...
call .venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to activate virtual environment.
    goto :error
)

python -m pip install --upgrade pip >nul
if exist "requirements.txt" (
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Failed to install dependencies from requirements.txt.
        goto :error
    )
    echo ✅ Dependencies installed successfully.
) else (
    echo ⚠️ requirements.txt not found. Skipping dependency installation.
)

:: 5. Create launcher script
echo.
echo 🛠️ Creating musyric.bat launcher...
(
echo @echo off
echo chcp 65001 ^^^>nul
echo setlocal
echo.
echo if "%%~1"=="" ^(
echo     echo 🎵 Mu^^(syr^^)ic CLI 🎵
echo     echo.
echo     echo Usage: musyric ^<command^> [options]
echo     echo Example: musyric download "Coldplay"
echo     echo.
echo     echo Activating virtual environment and showing help...
echo     call "%%~dp0.venv\Scripts\activate.bat"
echo     python -m musyric.cli --help
echo     exit /b
echo ^)
echo.
echo call "%%~dp0.venv\Scripts\activate.bat"
echo python -m musyric.cli %%*
) > musyric.bat

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to create musyric.bat launcher.
    goto :error
)
echo ✅ Launcher musyric.bat created.

:: 6. Completion
echo.
echo ==============================================================
echo 🎉 Setup Complete! 🎉
echo.
echo You can now use the tool by double-clicking 'musyric.bat' 
echo or running it from the terminal!
echo.
echo Examples:
echo   musyric.bat
echo   musyric.bat download "Rick Astley"
echo ==============================================================
echo.
pause
exit /b 0

:error
echo.
echo 🛑 An error occurred during installation. Please check the messages above.
pause
exit /b 1
