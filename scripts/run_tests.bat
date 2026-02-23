@echo off
REM =====================================================
REM HSM Test Framework - Quick Run Script (Windows)
REM =====================================================
REM Usage:
REM   run_tests.bat              - Run all tests
REM   run_tests.bat smoke        - Run smoke tests only
REM   run_tests.bat ui           - Run UI tests only
REM   run_tests.bat console      - Run console tests only
REM   run_tests.bat pkcs11       - Run PKCS11 tests only
REM =====================================================

setlocal

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
set PYTHONPATH=%PROJECT_DIR%

cd /d %PROJECT_DIR%

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Determine test marker
set MARKER=
if not "%~1"=="" (
    if /I "%~1"=="all" (
        set MARKER=
    ) else (
        set MARKER=-m %~1
    )
)

echo =====================================================
echo HSM Test Framework
echo Suite: %~1 (default: all)
echo Timestamp: %date% %time%
echo =====================================================

REM Clean previous results
if exist evidence\allure-results rmdir /s /q evidence\allure-results
mkdir evidence\allure-results 2>nul

REM Run tests
python -m pytest %MARKER% ^
    -v ^
    --tb=short ^
    --alluredir=evidence\allure-results ^
    --junitxml=evidence\junit-results.xml ^
    --timeout=120

set TEST_EXIT=%ERRORLEVEL%

echo.
echo =====================================================
echo Test execution complete (exit code: %TEST_EXIT%)
echo =====================================================

REM Generate Allure report (if allure CLI is installed)
where allure >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Generating Allure report...
    allure generate evidence\allure-results -o evidence\allure-report --clean
    echo Report: evidence\allure-report\index.html
) else (
    echo [INFO] Allure CLI not found. Install with: scoop install allure
    echo [INFO] Raw results in: evidence\allure-results\
)

exit /b %TEST_EXIT%
