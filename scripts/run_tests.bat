@echo off
REM =====================================================
REM HSM Test Framework - Test Runner (Windows)
REM =====================================================
REM
REM Usage:
REM   run_tests.bat                   - Run ALL tests
REM   run_tests.bat ui                - Run UI tests only
REM   run_tests.bat console           - Run console/CLI tests only
REM   run_tests.bat pkcs11            - Run PKCS11 tests only
REM   run_tests.bat smoke             - Run smoke tests only
REM   run_tests.bat regression        - Run full regression
REM
REM Run in order (UI first, then console):
REM   run_tests.bat ui && run_tests.bat console
REM
REM Run a specific test file:
REM   run_tests.bat file tests\ui\test_sample_app.py
REM
REM =====================================================

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
set PYTHONPATH=%PROJECT_DIR%

cd /d %PROJECT_DIR%

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Parse arguments
set SUITE=%~1
set EXTRA_ARGS=
set PYTEST_ARGS=-v --tb=short --alluredir=evidence\allure-results --junitxml=evidence\junit-results.xml --timeout=120

if "%SUITE%"=="" set SUITE=all

REM Handle "file" mode: run a specific test file
if /I "%SUITE%"=="file" (
    set EXTRA_ARGS=%~2
    set SUITE=file
    goto :run
)

REM Handle marker-based selection
if /I "%SUITE%"=="all" (
    set EXTRA_ARGS=
) else (
    set EXTRA_ARGS=-m %SUITE%
)

:run
echo =====================================================
echo HSM Test Framework
echo.
if /I "%SUITE%"=="file" (
    echo Mode   : Single file
    echo Target : %~2
) else (
    echo Suite  : %SUITE%
)
echo.
echo Available suites:
echo   ui         Windows UI tests only
echo   console    Console/CLI tests only
echo   pkcs11     PKCS11 tests only
echo   smoke      Quick smoke tests
echo   regression Full regression
echo   all        Everything
echo.
echo Tip: run_tests.bat ui ^&^& run_tests.bat console
echo      (runs UI first, then console)
echo =====================================================

REM Clean previous results
if exist evidence\allure-results rmdir /s /q evidence\allure-results
mkdir evidence\allure-results 2>nul

REM Run tests
python -m pytest %EXTRA_ARGS% %PYTEST_ARGS%

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
