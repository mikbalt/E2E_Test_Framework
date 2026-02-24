@echo off
REM ===========================================================
REM PKCS#11 Test Suite - Test Runner (Windows)
REM ===========================================================
REM
REM Usage:
REM   scripts\run_tests.bat                - Run ALL tests
REM   scripts\run_tests.bat java           - Run Java tests only
REM   scripts\run_tests.bat cpp            - Run C++ tests only
REM   scripts\run_tests.bat go_test        - Run Go tests only
REM   scripts\run_tests.bat gtest          - Run GTest tests only
REM   scripts\run_tests.bat smoke          - Run smoke tests
REM   scripts\run_tests.bat build_and_test - Build first, then run all
REM
REM ===========================================================

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
set PYTHONPATH=%PROJECT_DIR%
cd /d %PROJECT_DIR%

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" call venv\Scripts\activate.bat

set SUITE=%~1
if "%SUITE%"=="" set SUITE=all

set PYTEST_ARGS=-v --tb=short --alluredir=evidence\allure-results --junitxml=evidence\junit-results.xml --timeout=120

echo =====================================================
echo PKCS#11 Test Suite
echo.
echo Suite    : %SUITE%
echo Platform : Windows
echo.
echo Available suites:
echo   java         Java PKCS#11 tests only
echo   cpp          C++ native tests only
echo   go_test      Go tests only
echo   gtest        Google Test (C++) only
echo   smoke        Quick smoke tests
echo   regression   Full regression
echo   all          Everything
echo   build_and_test  Build + run all
echo =====================================================

REM Handle build_and_test mode
if /I "%SUITE%"=="build_and_test" (
    echo.
    echo ^>^>^> Phase 1: Build
    call scripts\build.bat
    if !ERRORLEVEL! neq 0 exit /b !ERRORLEVEL!
    echo.
    echo ^>^>^> Phase 2: Test
    set SUITE=all
)

REM Clean previous results
if exist evidence\allure-results rmdir /s /q evidence\allure-results
mkdir evidence\allure-results 2>nul
mkdir logs 2>nul

REM Determine pytest marker
set EXTRA_ARGS=
if /I not "%SUITE%"=="all" set EXTRA_ARGS=-m %SUITE%

REM Run tests
python -m pytest %EXTRA_ARGS% %PYTEST_ARGS%
set TEST_EXIT=%ERRORLEVEL%

echo.
echo =====================================================
echo Test execution complete (exit code: %TEST_EXIT%)
echo =====================================================

REM Generate Allure report
where allure >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Generating Allure report...
    allure generate evidence\allure-results -o evidence\allure-report --clean
    echo Report: evidence\allure-report\index.html
) else (
    echo [INFO] Allure CLI not found. Raw results in: evidence\allure-results\
)

exit /b %TEST_EXIT%
