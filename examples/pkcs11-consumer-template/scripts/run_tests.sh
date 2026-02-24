#!/usr/bin/env bash
# ===========================================================
# PKCS#11 Test Suite - Test Runner (Linux/macOS)
# ===========================================================
#
# Usage:
#   ./scripts/run_tests.sh                - Run ALL tests
#   ./scripts/run_tests.sh java           - Run Java tests only
#   ./scripts/run_tests.sh cpp            - Run C++ tests only
#   ./scripts/run_tests.sh go_test        - Run Go tests only
#   ./scripts/run_tests.sh gtest          - Run GTest tests only
#   ./scripts/run_tests.sh smoke          - Run smoke tests
#   ./scripts/run_tests.sh build_and_test - Build first, then run all
#
# ===========================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR"

# Activate virtual environment if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

SUITE="${1:-all}"
PYTEST_ARGS="-v --tb=short --alluredir=evidence/allure-results --junitxml=evidence/junit-results.xml --timeout=120"

echo "====================================================="
echo "PKCS#11 Test Suite"
echo ""
echo "Suite    : $SUITE"
echo "Platform : $(uname -s)"
echo ""
echo "Available suites:"
echo "  java         Java PKCS#11 tests only"
echo "  cpp          C++ native tests only"
echo "  go_test      Go tests only"
echo "  gtest        Google Test (C++) only"
echo "  smoke        Quick smoke tests"
echo "  regression   Full regression"
echo "  all          Everything"
echo "  build_and_test  Build + run all"
echo "====================================================="

# Handle build_and_test mode
if [ "$SUITE" = "build_and_test" ]; then
    echo ""
    echo ">>> Phase 1: Build"
    chmod +x scripts/build.sh
    ./scripts/build.sh || exit $?
    echo ""
    echo ">>> Phase 2: Test"
    SUITE="all"
fi

# Clean previous results
rm -rf evidence/allure-results
mkdir -p evidence/allure-results logs

# Determine pytest marker
EXTRA_ARGS=""
if [ "$SUITE" != "all" ]; then
    EXTRA_ARGS="-m $SUITE"
fi

# Run tests
python3 -m pytest $EXTRA_ARGS $PYTEST_ARGS || TEST_EXIT=$?
TEST_EXIT=${TEST_EXIT:-0}

echo
echo "====================================================="
echo "Test execution complete (exit code: $TEST_EXIT)"
echo "====================================================="

# Generate Allure report
if command -v allure &> /dev/null; then
    echo "Generating Allure report..."
    allure generate evidence/allure-results -o evidence/allure-report --clean
    echo "Report: evidence/allure-report/index.html"
else
    echo "[INFO] Allure CLI not found. Raw results in: evidence/allure-results/"
fi

exit $TEST_EXIT
