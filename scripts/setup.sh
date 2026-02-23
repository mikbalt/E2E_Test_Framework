#!/usr/bin/env bash
# =====================================================
# HSM Test Framework - First-time Setup (Linux/macOS)
# =====================================================
# Supports side-by-side Python installs.
# Tries: python3.13 down to python3.9, then python3
# =====================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "====================================================="
echo "HSM Test Framework - Setup (Linux/macOS)"
echo "====================================================="
echo

# Find best Python >= 3.9
PYTHON_CMD=""
for ver in python3.13 python3.12 python3.11 python3.10 python3.9; do
    if command -v "$ver" &> /dev/null; then
        PYTHON_CMD="$ver"
        break
    fi
done

# Fallback to python3
if [ -z "$PYTHON_CMD" ]; then
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "[ERROR] Python 3.9+ not found."
    echo
    echo "Install options:"
    echo "  Ubuntu/Debian: sudo apt install python3.11 python3.11-venv"
    echo "  RHEL/CentOS:   sudo dnf install python3.11"
    echo "  macOS:          brew install python@3.11"
    echo
    echo "If Python 3.8 is installed, you need a newer version alongside it."
    echo "Both can coexist without conflicts."
    exit 1
fi

echo "Using: $PYTHON_CMD ($($PYTHON_CMD --version))"

# Verify version
$PYTHON_CMD -c "
import sys
if sys.version_info < (3, 9):
    print(f'[ERROR] Python {sys.version} is too old. Need 3.9+')
    print('Install Python 3.11 alongside your existing version.')
    sys.exit(1)
"

# Create virtual environment
echo
echo "Creating virtual environment..."
$PYTHON_CMD -m venv venv
source venv/bin/activate

echo "venv Python: $(python3 --version)"

# Install dependencies
echo
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create evidence directories
mkdir -p evidence/allure-results evidence/screenshots

echo
echo "====================================================="
echo "Setup complete!"
echo
echo "Quick start:"
echo "  1. Edit config/settings.yaml with your tool paths"
echo "  2. Run: ./scripts/run_tests.sh smoke"
echo
echo "On Linux, only console/PKCS11 tests will run."
echo "UI tests auto-skip (requires Windows)."
echo "====================================================="
