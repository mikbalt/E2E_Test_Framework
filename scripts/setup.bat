@echo off
REM =====================================================
REM HSM Test Framework - First-time Setup (Windows)
REM =====================================================
REM Supports side-by-side Python installs.
REM Tries: py -3.13 down to py -3.11, then python, python3
REM Requires Python 3.11+
REM =====================================================

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
set MIN_VERSION=3.11

cd /d %PROJECT_DIR%

echo =====================================================
echo HSM Test Framework - Setup
echo =====================================================
echo.

REM ── Step 1: Find Python 3.11+ ──
set PYTHON_CMD=

REM Try py launcher first (recommended for side-by-side installs)
where py >nul 2>nul
if !ERRORLEVEL! equ 0 (
    echo [INFO] Found py launcher. Scanning installed versions...
    py --list 2>nul
    echo.
    for %%V in (3.13 3.12 3.11) do (
        if not defined PYTHON_CMD (
            py -%%V --version >nul 2>nul
            if !ERRORLEVEL! equ 0 (
                set "PYTHON_CMD=py -%%V"
                echo [INFO] Selected: py -%%V
            )
        )
    )
) else (
    echo [INFO] py launcher not found, trying PATH...
)

REM Fallback: try python then python3
if not defined PYTHON_CMD (
    python --version >nul 2>nul
    if !ERRORLEVEL! equ 0 (
        set PYTHON_CMD=python
    )
)
if not defined PYTHON_CMD (
    python3 --version >nul 2>nul
    if !ERRORLEVEL! equ 0 (
        set PYTHON_CMD=python3
    )
)

if not defined PYTHON_CMD (
    echo [ERROR] Python %MIN_VERSION%+ not found.
    echo.
    echo ── Troubleshooting ──
    echo.
    echo 1. Install Python 3.11+ from https://python.org/downloads
    echo    IMPORTANT: Check "Add Python to PATH" during installation
    echo.
    echo 2. If Python IS installed but not detected:
    echo    - Open a NEW terminal ^(current terminal may have old PATH^)
    echo    - Run: py --list          ^(check py launcher^)
    echo    - Run: python --version   ^(check PATH^)
    echo    - Run: where python       ^(find Python location^)
    echo.
    echo 3. If you have Python 3.8/3.9/3.10, upgrade to 3.11+
    echo    Both versions can coexist side-by-side.
    echo.
    exit /b 1
)

echo.
echo Using: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM ── Step 2: Verify version >= 3.11 ──
%PYTHON_CMD% -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" 2>nul
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Python version is too old. Need %MIN_VERSION%+
    echo.
    for /f "delims=" %%I in ('%PYTHON_CMD% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do (
        echo Detected: Python %%I
    )
    echo Required: Python %MIN_VERSION%+
    echo.
    echo Install Python 3.11+ from https://python.org/downloads
    echo It can be installed alongside your existing Python version.
    exit /b 1
)

REM ── Step 3: Create virtual environment ──
echo Creating virtual environment...
if exist venv (
    echo [INFO] venv/ already exists. Reusing it.
    echo [INFO] To recreate, delete venv/ and re-run this script.
) else (
    %PYTHON_CMD% -m venv venv
)
call venv\Scripts\activate.bat

echo.
echo venv Python:
python --version
echo.

REM ── Step 4: Install dependencies ──
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM ── Step 5: Create evidence directories ──
mkdir evidence 2>nul
mkdir evidence\allure-results 2>nul
mkdir evidence\screenshots 2>nul

REM ── Step 6: Copy .env if missing ──
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo.
        echo [INFO] Created .env from .env.example
        echo [INFO] Edit .env with your HSM_IP, E_ADMIN_PATH, etc.
    )
)

echo.
echo =====================================================
echo Setup complete!
echo.
echo Next steps:
echo   1. Edit .env with your HSM_IP, E_ADMIN_PATH, etc.
echo   2. Activate venv:  venv\Scripts\activate.bat
echo   3. Verify:         pytest tests/ui/e_admin/ --co -v
echo   4. Run tests:      pytest -m smoke -v
echo.
echo See README.md for more commands.
echo =====================================================
