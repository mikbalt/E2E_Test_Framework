@echo off
REM ===========================================================
REM PKCS#11 Test Suite - Build Script (Windows)
REM ===========================================================
REM
REM Compiles source code for tools that have 'needs_build: true'
REM in config/settings.yaml. Only builds what's needed.
REM
REM Usage:
REM   scripts\build.bat              - Build everything
REM   scripts\build.bat java         - Build Java tests only
REM   scripts\build.bat go           - Build Go tests only
REM   scripts\build.bat gtest        - Build GTest/C++ tests only
REM   scripts\build.bat clean        - Clean all build artifacts
REM
REM ===========================================================

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
cd /d %PROJECT_DIR%

set TARGET=%~1
if "%TARGET%"=="" set TARGET=all

REM Ensure output directories exist
if not exist bin mkdir bin
if not exist logs mkdir logs
if not exist evidence mkdir evidence

echo =====================================================
echo PKCS#11 Test Suite - Build
echo Target  : %TARGET%
echo Platform: Windows
echo =====================================================
echo.

set BUILD_OK=0
set BUILD_FAIL=0

if /I "%TARGET%"=="all" goto :build_all
if /I "%TARGET%"=="java" goto :build_java
if /I "%TARGET%"=="go" goto :build_go
if /I "%TARGET%"=="gtest" goto :build_gtest
if /I "%TARGET%"=="cpp" goto :build_gtest
if /I "%TARGET%"=="clean" goto :clean

echo [ERROR] Unknown target: %TARGET%
echo Usage: scripts\build.bat [all^|java^|go^|gtest^|clean]
exit /b 1

:build_all
call :build_java
call :build_go
call :build_gtest
goto :summary

REM ---------------------------------------------------------
REM Java Builds (Maven)
REM ---------------------------------------------------------
:build_java
echo [BUILD] === Building Java Tests ===

if exist "src\java\signing\pom.xml" (
    echo [BUILD] Building: pkcs11-signing (Maven^)
    call mvn clean package -q -f src\java\signing\pom.xml -DskipTests
    if !ERRORLEVEL! equ 0 (
        copy src\java\signing\target\*.jar bin\ >nul 2>&1
        echo [BUILD]   -^> bin\pkcs11-signing.jar OK
        set /a BUILD_OK+=1
    ) else (
        echo [ERROR]   -^> pkcs11-signing build FAILED
        set /a BUILD_FAIL+=1
    )
) else (
    echo [WARN]  src\java\signing\pom.xml not found - skipping
)

goto :eof

REM ---------------------------------------------------------
REM Go Builds
REM ---------------------------------------------------------
:build_go
echo [BUILD] === Building Go Tests ===

where go >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [WARN]  Go not installed - skipping Go builds
    goto :eof
)

if exist "src\go\slot" (
    echo [BUILD] Building: pkcs11-slot (Go^)
    go build -o bin\pkcs11-slot.exe .\src\go\slot\...
    if !ERRORLEVEL! equ 0 (
        echo [BUILD]   -^> bin\pkcs11-slot.exe OK
        set /a BUILD_OK+=1
    ) else (
        echo [ERROR]   -^> pkcs11-slot build FAILED
        set /a BUILD_FAIL+=1
    )
) else (
    echo [WARN]  src\go\slot\ not found - skipping
)

goto :eof

REM ---------------------------------------------------------
REM Google Test / C++ Builds (via Makefile or CMake)
REM ---------------------------------------------------------
:build_gtest
echo [BUILD] === Building Google Test / C++ Tests ===

if exist "src\cpp\gtest_crypto\Makefile" (
    echo [BUILD] Building: pkcs11_gtest_crypto (Makefile^)

    REM Try mingw32-make first, then nmake
    where mingw32-make >nul 2>nul
    if !ERRORLEVEL! equ 0 (
        mingw32-make -C src\cpp\gtest_crypto all
    ) else (
        where nmake >nul 2>nul
        if !ERRORLEVEL! equ 0 (
            cd src\cpp\gtest_crypto && nmake /f Makefile all && cd ..\..\..
        ) else (
            echo [WARN]  Neither mingw32-make nor nmake found
            set /a BUILD_FAIL+=1
            goto :eof
        )
    )

    if !ERRORLEVEL! equ 0 (
        copy src\cpp\gtest_crypto\pkcs11_gtest_crypto.exe bin\ >nul 2>&1
        echo [BUILD]   -^> bin\pkcs11_gtest_crypto.exe OK
        set /a BUILD_OK+=1
    ) else (
        echo [ERROR]   -^> pkcs11_gtest_crypto build FAILED
        set /a BUILD_FAIL+=1
    )
) else (
    echo [WARN]  src\cpp\gtest_crypto\Makefile not found - skipping
)

goto :eof

REM ---------------------------------------------------------
REM Clean
REM ---------------------------------------------------------
:clean
echo [BUILD] === Cleaning build artifacts ===

REM Java
if exist "src\java" (
    for /d /r src\java %%d in (target) do (
        if exist "%%d" rmdir /s /q "%%d"
    )
    echo [BUILD]   Cleaned Java target directories
)

REM Go
del /q bin\pkcs11-slot.exe 2>nul
echo [BUILD]   Cleaned Go binaries

REM GTest/C++
if exist "src\cpp\gtest_crypto\Makefile" (
    where mingw32-make >nul 2>nul
    if !ERRORLEVEL! equ 0 (
        mingw32-make -C src\cpp\gtest_crypto clean 2>nul
    )
    echo [BUILD]   Cleaned GTest build
)

REM Logs & evidence
if exist logs rmdir /s /q logs & mkdir logs
if exist evidence\allure-results rmdir /s /q evidence\allure-results
echo [BUILD]   Cleaned logs and evidence

echo.
echo [BUILD] Clean complete
exit /b 0

REM ---------------------------------------------------------
REM Summary
REM ---------------------------------------------------------
:summary
echo.
echo =====================================================
echo Build Summary: %BUILD_OK% succeeded, %BUILD_FAIL% failed
echo =====================================================

if %BUILD_FAIL% gtr 0 (
    echo [ERROR] Some builds failed!
    exit /b 1
)

echo [BUILD] All builds completed successfully
exit /b 0
