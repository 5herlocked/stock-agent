@echo off
setlocal enabledelayedexpansion

REM Stock Agent Development Script for Windows
REM Convenient wrapper for starting the development server

echo.
echo 🚀 Stock Agent Development Server
echo =================================
echo.

REM Get the project root directory (go up one level from scripts/)
set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"

REM Check if Python is available
set "PYTHON_CMD="
where python >nul 2>nul
if !errorlevel! equ 0 (
    set "PYTHON_CMD=python"
    goto :check_version
)

where python3 >nul 2>nul
if !errorlevel! equ 0 (
    set "PYTHON_CMD=python3"
    goto :check_version
)

echo ❌ Error: Python not found
echo Please install Python 3.12+ and add it to your PATH
pause
exit /b 1

:check_version
echo ✅ Using Python: !PYTHON_CMD!

REM Check for and activate virtual environment
if exist ".venv" (
    echo 📁 Found virtual environment
    if exist ".venv\Scripts\activate.bat" (
        call .venv\Scripts\activate.bat
        echo ✅ Virtual environment activated
    ) else (
        echo ⚠️  Virtual environment found but activation script missing
    )
) else (
    echo ⚠️  No virtual environment found ^(.venv^)
    echo    Consider running: python -m venv .venv
)

REM Check for environment file
if exist ".dev.env" (
    echo ✅ Development environment file found ^(.dev.env^)
) else (
    echo ❌ Warning: .dev.env file not found
    echo    Create .dev.env with required environment variables
)

REM Check dependencies
where uv >nul 2>nul
if !errorlevel! equ 0 (
    echo 📦 Using UV package manager
    if not exist "uv.lock" (
        echo 🔄 Syncing dependencies with UV...
        uv sync
    ) else (
        for %%i in (pyproject.toml) do set "pyproject_time=%%~ti"
        for %%i in (uv.lock) do set "uvlock_time=%%~ti"
        REM Simple time comparison - sync if pyproject.toml is newer
        if "!pyproject_time!" gtr "!uvlock_time!" (
            echo 🔄 Syncing dependencies with UV...
            uv sync
        )
    )
) else (
    echo 📦 UV not found, checking pip installation...
    !PYTHON_CMD! -c "import robyn" >nul 2>nul
    if !errorlevel! neq 0 (
        echo 🔄 Installing dependencies with pip...
        pip install -e .
    )
)
echo ✅ Dependencies ready

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :start_server
if "%~1"=="--help" goto :show_help
if "%~1"=="-h" goto :show_help
if "%~1"=="--port" (
    set "DEV_PORT=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--host" (
    set "DEV_HOST=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--summary" (
    set "DEV_GENERATE_SUMMARY=true"
    shift
    goto :parse_args
)
if "%~1"=="--no-summary" (
    set "DEV_GENERATE_SUMMARY=false"
    shift
    goto :parse_args
)

echo ❌ Unknown option: %~1
goto :show_help

:show_help
echo Usage: dev.bat [options]
echo.
echo Options:
echo   --help, -h     Show this help message
echo   --port PORT    Use custom port ^(default: 8080^)
echo   --host HOST    Use custom host ^(default: 127.0.0.1^)
echo   --summary      Generate market summary on startup
echo   --no-summary   Skip market summary generation
echo.
echo Environment variables ^(set in .dev.env^):
echo   DEV_HOST       Development host ^(default: 127.0.0.1^)
echo   DEV_PORT       Development port ^(default: 8080^)
echo   DEV_GENERATE_SUMMARY  Generate market summary ^(default: false^)
echo.
echo Examples:
echo   dev.bat                    # Start with default settings
echo   dev.bat --port 3000        # Start on port 3000
echo   dev.bat --summary          # Start with market summary
pause
exit /b 0

:start_server
REM Kill any existing server on port 8080 (Windows equivalent)
set "port=8080"
if defined DEV_PORT set "port=%DEV_PORT%"

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":!port!" ^| findstr "LISTENING"') do (
    echo 🔄 Killing existing server on port !port! ^(PID: %%a^)
    taskkill /PID %%a /F >nul 2>nul
)

echo 🔥 Starting development server...
echo.

REM Start the development server
!PYTHON_CMD! scripts\dev_server.py %*

REM Handle Ctrl+C gracefully
:cleanup
echo.
echo 👋 Shutting down development server...
exit /b 0
