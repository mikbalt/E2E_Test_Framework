#!/usr/bin/env bash
# =====================================================
# HSM Test Framework - Test Runner (Linux/macOS)
# =====================================================
#
# Usage:
#   ./run_tests.sh                   - Run ALL tests (UI auto-skipped on Linux)
#   ./run_tests.sh ui                - Run UI tests only
#   ./run_tests.sh console           - Run console/CLI tests only
#   ./run_tests.sh pkcs11            - Run PKCS11 tests only
#   ./run_tests.sh smoke             - Run smoke tests only
#   ./run_tests.sh regression        - Run full regression
#
# Run in order (UI first, then console):
#   ./run_tests.sh ui && ./run_tests.sh console
#
# Run a specific test file:
#   ./run_tests.sh file tests/console/test_pkcs11_sample.py
#
# =====================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR"

# Activate virtual environment if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

SUITE="${1:-all}"
EXTRA_ARGS=""
PYTEST_ARGS="-v --tb=short --alluredir=evidence/allure-results --junitxml=evidence/junit-results.xml --timeout=120"

# Handle "file" mode: run a specific test file
if [ "$SUITE" = "file" ]; then
    EXTRA_ARGS="$2"
elif [ "$SUITE" != "all" ]; then
    EXTRA_ARGS="-m $SUITE"
fi

echo "====================================================="
echo "HSM Test Framework"
echo ""
if [ "$SUITE" = "file" ]; then
    echo "Mode   : Single file"
    echo "Target : $2"
else
    echo "Suite  : $SUITE"
fi
echo ""
echo "Available suites:"
echo "  ui         Windows UI tests only"
echo "  console    Console/CLI tests only"
echo "  pkcs11     PKCS11 tests only"
echo "  smoke      Quick smoke tests"
echo "  regression Full regression"
echo "  all        Everything"
echo ""
echo "Tip: ./run_tests.sh ui && ./run_tests.sh console"
echo "     (runs UI first, then console)"
echo "Platform: $(uname -s)"
echo "====================================================="

# Clean previous results
rm -rf evidence/allure-results
mkdir -p evidence/allure-results

# Run tests
python3 -m pytest $EXTRA_ARGS $PYTEST_ARGS || TEST_EXIT=$?
TEST_EXIT=${TEST_EXIT:-0}

echo
echo "====================================================="
echo "Test execution complete (exit code: $TEST_EXIT)"
echo "====================================================="

# Generate Allure report if CLI installed
if command -v allure &> /dev/null; then
    echo "Generating Allure report..."
    allure generate evidence/allure-results -o evidence/allure-report --clean
    echo "Report: evidence/allure-report/index.html"
else
    echo "[INFO] Allure CLI not found. Install: brew install allure (macOS) / snap install allure (Linux)"
    echo "[INFO] Raw results in: evidence/allure-results/"
fi

exit $TEST_EXIT
