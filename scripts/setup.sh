#!/usr/bin/env bash
# =====================================================
# HSM Test Framework - First-time Setup (Linux/macOS)
# =====================================================
# Supports side-by-side Python installs.
# Tries: python3.13 down to python3.11, then python3
# Requires Python 3.11+
# =====================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "====================================================="
echo "HSM Test Framework - Setup (Linux/macOS)"
echo "====================================================="
echo

# ── Step 1: Find Python 3.11+ ──
PYTHON_CMD=""
for ver in python3.13 python3.12 python3.11; do
    if command -v "$ver" &> /dev/null; then
        PYTHON_CMD="$ver"
        break
    fi
done

# Fallback to python3 (check version later)
if [ -z "$PYTHON_CMD" ]; then
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "[ERROR] Python 3.11+ not found."
    echo
    echo "── Troubleshooting ──"
    echo
    echo "Install options:"
    echo "  Ubuntu/Debian: sudo apt install python3.11 python3.11-venv"
    echo "  RHEL/CentOS:   sudo dnf install python3.11"
    echo "  macOS:          brew install python@3.11"
    echo
    echo "If Python IS installed but not detected:"
    echo "  - Open a NEW terminal (current terminal may have old PATH)"
    echo "  - Run: python3 --version"
    echo "  - Run: which python3"
    echo
    echo "If you have Python 3.8/3.9/3.10, upgrade to 3.11+"
    echo "Both versions can coexist side-by-side."
    exit 1
fi

echo "Using: $PYTHON_CMD ($($PYTHON_CMD --version 2>&1))"

# ── Step 2: Verify version >= 3.11 ──
$PYTHON_CMD -c "
import sys
if sys.version_info < (3, 11):
    v = f'{sys.version_info.major}.{sys.version_info.minor}'
    print(f'[ERROR] Python {v} is too old. Need 3.11+')
    print()
    print('Install options:')
    print('  Ubuntu/Debian: sudo apt install python3.11 python3.11-venv')
    print('  RHEL/CentOS:   sudo dnf install python3.11')
    print('  macOS:          brew install python@3.11')
    print()
    print('Both versions can coexist side-by-side.')
    sys.exit(1)
"

# ── Step 3: Create virtual environment ──
echo
if [ -d "venv" ]; then
    echo "[INFO] venv/ already exists. Reusing it."
    echo "[INFO] To recreate, delete venv/ and re-run this script."
else
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi
source venv/bin/activate

echo "venv Python: $(python3 --version 2>&1)"

# ── Step 4: Install dependencies ──
echo
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# ── Step 5: Create evidence directories ──
mkdir -p evidence/allure-results evidence/screenshots

# ── Step 6: Copy .env if missing ──
if [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
    echo
    echo "[INFO] Created .env from .env.example"
    echo "[INFO] Edit .env with your HSM_IP, E_ADMIN_PATH, etc."
fi

echo
echo "====================================================="
echo "Setup complete!"
echo
echo "Next steps:"
echo "  1. Edit .env with your HSM_IP, E_ADMIN_PATH, etc."
echo "  2. Activate venv:  source venv/bin/activate"
echo "  3. Verify:         pytest tests/ui/e_admin/ --co -v"
echo "  4. Run tests:      pytest -m smoke -v"
echo
echo "On Linux, only console/PKCS11 tests will run."
echo "UI tests auto-skip (requires Windows)."
echo "====================================================="
