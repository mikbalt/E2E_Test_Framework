#!/usr/bin/env bash
# =====================================================
# HSM Test Framework - Quick Run Script (Linux/macOS)
# =====================================================
# Usage:
#   ./run_tests.sh              - Run all tests (UI auto-skipped on Linux)
#   ./run_tests.sh smoke        - Run smoke tests only
#   ./run_tests.sh console      - Run console tests only
#   ./run_tests.sh pkcs11       - Run PKCS11 tests only
# =====================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR"

# Activate virtual environment if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Determine test marker
MARKER=""
SUITE="${1:-all}"
if [ "$SUITE" != "all" ]; then
    MARKER="-m $SUITE"
fi

echo "====================================================="
echo "HSM Test Framework"
echo "Suite: $SUITE"
echo "Platform: $(uname -s)"
echo "Timestamp: $(date)"
echo "====================================================="

# Clean previous results
rm -rf evidence/allure-results
mkdir -p evidence/allure-results

# Run tests
python3 -m pytest $MARKER \
    -v \
    --tb=short \
    --alluredir=evidence/allure-results \
    --junitxml=evidence/junit-results.xml \
    --timeout=120 \
    || TEST_EXIT=$?

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
