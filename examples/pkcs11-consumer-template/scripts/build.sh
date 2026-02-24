#!/usr/bin/env bash
# ===========================================================
# PKCS#11 Test Suite - Build Script (Linux/macOS)
# ===========================================================
#
# Compiles source code for tools that have 'needs_build: true'
# in config/settings.yaml. Only builds what's needed.
#
# Usage:
#   ./scripts/build.sh              - Build everything
#   ./scripts/build.sh java         - Build Java tests only
#   ./scripts/build.sh go           - Build Go tests only
#   ./scripts/build.sh gtest        - Build GTest/C++ tests only
#   ./scripts/build.sh clean        - Clean all build artifacts
#
# ===========================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

TARGET="${1:-all}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[BUILD]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Ensure output directories exist
mkdir -p bin logs evidence

echo "====================================================="
echo "PKCS#11 Test Suite - Build"
echo "Target  : $TARGET"
echo "Platform: $(uname -s)"
echo "====================================================="
echo

BUILD_OK=0
BUILD_FAIL=0

# ---------------------------------------------------------
# Java Builds (Maven)
# ---------------------------------------------------------
build_java() {
    log_info "=== Building Java Tests ==="

    # pkcs11-signing (needs build)
    if [ -f "src/java/signing/pom.xml" ]; then
        log_info "Building: pkcs11-signing (Maven)"
        if mvn clean package -q -f src/java/signing/pom.xml -DskipTests; then
            cp src/java/signing/target/*.jar bin/ 2>/dev/null || true
            log_info "  -> bin/pkcs11-signing.jar OK"
            BUILD_OK=$((BUILD_OK + 1))
        else
            log_error "  -> pkcs11-signing build FAILED"
            BUILD_FAIL=$((BUILD_FAIL + 1))
        fi
    else
        log_warn "  src/java/signing/pom.xml not found — skipping"
    fi

    # Add more Java builds here as needed:
    # if [ -f "src/java/keygen/pom.xml" ]; then
    #     ...
    # fi
}

# ---------------------------------------------------------
# Go Builds
# ---------------------------------------------------------
build_go() {
    log_info "=== Building Go Tests ==="

    if command -v go &> /dev/null; then
        # pkcs11-slot
        if [ -d "src/go/slot" ]; then
            log_info "Building: pkcs11-slot (Go)"
            if go build -o bin/pkcs11-slot ./src/go/slot/...; then
                log_info "  -> bin/pkcs11-slot OK"
                BUILD_OK=$((BUILD_OK + 1))
            else
                log_error "  -> pkcs11-slot build FAILED"
                BUILD_FAIL=$((BUILD_FAIL + 1))
            fi
        else
            log_warn "  src/go/slot/ not found — skipping"
        fi

        # Add more Go builds here:
        # if [ -d "src/go/other_tool" ]; then
        #     go build -o bin/other_tool ./src/go/other_tool/...
        # fi
    else
        log_warn "Go not installed — skipping Go builds"
    fi
}

# ---------------------------------------------------------
# Google Test / C++ Builds (via Makefile)
# ---------------------------------------------------------
build_gtest() {
    log_info "=== Building Google Test / C++ Tests ==="

    # pkcs11_gtest_crypto
    if [ -f "src/cpp/gtest_crypto/Makefile" ]; then
        log_info "Building: pkcs11_gtest_crypto (Makefile)"
        if make -C src/cpp/gtest_crypto all; then
            # Copy output binary to bin/
            cp src/cpp/gtest_crypto/pkcs11_gtest_crypto bin/ 2>/dev/null || true
            log_info "  -> bin/pkcs11_gtest_crypto OK"
            BUILD_OK=$((BUILD_OK + 1))
        else
            log_error "  -> pkcs11_gtest_crypto build FAILED"
            BUILD_FAIL=$((BUILD_FAIL + 1))
        fi
    else
        log_warn "  src/cpp/gtest_crypto/Makefile not found — skipping"
    fi

    # Add more Makefile-based builds here:
    # if [ -f "src/cpp/other_test/Makefile" ]; then
    #     make -C src/cpp/other_test all
    # fi
}

# ---------------------------------------------------------
# Clean
# ---------------------------------------------------------
clean() {
    log_info "=== Cleaning build artifacts ==="

    # Java
    if [ -d "src/java" ]; then
        find src/java -name "target" -type d -exec rm -rf {} + 2>/dev/null || true
        log_info "  Cleaned Java target directories"
    fi

    # Go
    rm -f bin/pkcs11-slot bin/pkcs11-slot.exe 2>/dev/null || true
    log_info "  Cleaned Go binaries"

    # GTest/C++
    if [ -f "src/cpp/gtest_crypto/Makefile" ]; then
        make -C src/cpp/gtest_crypto clean 2>/dev/null || true
        log_info "  Cleaned GTest build"
    fi

    # Logs & evidence from previous runs
    rm -rf logs/* evidence/allure-results/* 2>/dev/null || true
    log_info "  Cleaned logs and evidence"

    echo
    log_info "Clean complete"
}

# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
case "$TARGET" in
    all)
        build_java
        build_go
        build_gtest
        ;;
    java)
        build_java
        ;;
    go)
        build_go
        ;;
    gtest|cpp)
        build_gtest
        ;;
    clean)
        clean
        exit 0
        ;;
    *)
        log_error "Unknown target: $TARGET"
        echo "Usage: $0 [all|java|go|gtest|clean]"
        exit 1
        ;;
esac

echo
echo "====================================================="
echo "Build Summary: $BUILD_OK succeeded, $BUILD_FAIL failed"
echo "====================================================="

if [ $BUILD_FAIL -gt 0 ]; then
    log_error "Some builds failed!"
    exit 1
fi

log_info "All builds completed successfully"
