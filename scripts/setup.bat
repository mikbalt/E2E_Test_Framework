@echo off
REM =====================================================
REM HSM Test Framework - First-time Setup (Windows)
REM =====================================================
REM Supports side-by-side Python installs.
REM Tries: py -3.11, py -3.10, py -3.9, python, python
REM =====================================================

setlocal

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
set MIN_VERSION=3.9

cd /d %PROJECT_DIR%

echo =====================================================
echo HSM Test Framework - Setup
echo =====================================================
echo.

REM Find best Python >= 3.9 using the Windows Python Launcher (py)
set PYTHON_CMD=

REM Try py launcher first (recommended for side-by-side installs)
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    for %%V in (3.13 3.12 3.11 3.10 3.9) do (
        if not defined PYTHON_CMD (
            py -%%V --version >nul 2>nul
            if !ERRORLEVEL! equ 0 (
                set PYTHON_CMD=py -%%V
            )
        )
    )
)

REM Fallback: try python then python
if not defined PYTHON_CMD (
    python --version >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        set PYTHON_CMD=python
    ) else (
        python --version >nul 2>nul
        if %ERRORLEVEL% equ 0 (
            set PYTHON_CMD=python
        )
    )
)

if not defined PYTHON_CMD (
    echo [ERROR] Python %MIN_VERSION%+ not found.
    echo.
    echo Install Python from https://python.org/downloads
    echo   - Check "Add Python to PATH"
    echo   - Or install side-by-side: the 'py' launcher will find it
    echo.
    echo If Python 3.8 is installed, you need a newer version alongside it.
    echo Download Python 3.11 from python.org. Both can coexist.
    exit /b 1
)

echo Using: %PYTHON_CMD%
%PYTHON_CMD% --version

REM Verify version is >= 3.9
%PYTHON_CMD% -c "import sys; assert sys.version_info >= (3,9), f'Python {sys.version} is too old. Need 3.9+'" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python version is too old. Need %MIN_VERSION%+
    echo Current Python 3.8 is end-of-life since October 2024.
    echo Install Python 3.11 from https://python.org/downloads
    echo It can be installed alongside your existing Python 3.8.
    exit /b 1
)

REM Create virtual environment
echo.
echo Creating virtual environment...
%PYTHON_CMD% -m venv venv
call venv\Scripts\activate.bat

REM Show venv Python version
echo venv Python:
python --version

REM Install dependencies
echo.
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Create evidence directories
mkdir evidence 2>nul
mkdir evidence\allure-results 2>nul
mkdir evidence\screenshots 2>nul

echo.
echo =====================================================
echo Setup complete!
echo.
echo Quick start:
echo   1. Edit config\settings.yaml with your app paths
echo   2. Run: scripts\run_tests.bat smoke
echo.
echo Optional:
echo   - Install Allure CLI: scoop install allure
echo   - Configure Kiwi TCMS in config\settings.yaml
echo   - Configure Grafana/Prometheus in config\settings.yaml
echo =====================================================
