# PKCS#11 Test Suite — Consumer Repo Template

This is a **ready-to-use template** for wrapping existing PKCS#11 tests
(Java, C++, Go, Google Test) with the HSM Test Framework.

## Quick Start

```bash
# 1. Copy this template to a new repo
cp -r examples/pkcs11-consumer-template/ /path/to/pkcs11-tests/
cd /path/to/pkcs11-tests/

# 2. Install framework
python3 -m venv venv
source venv/bin/activate      # Linux
# or: venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 3. Place your binaries in bin/ and update config/settings.yaml

# 4. Run tests
./scripts/run_tests.sh smoke         # Linux
scripts\run_tests.bat smoke          # Windows
```

## Structure

```
pkcs11-tests/
├── bin/                          # Pre-compiled binaries go here
│   ├── pkcs11-keygen.jar         # Java (ready)
│   ├── pkcs11_encrypt            # C++ (ready)
│   └── ...
├── src/                          # Source code (if building needed)
│   ├── java/signing/pom.xml      # Java Maven project
│   ├── go/slot/main.go           # Go source
│   └── cpp/gtest_crypto/         # GTest + Makefile
├── config/
│   └── settings.yaml             # Paths, log locations, build flags
├── tests/
│   └── console/
│       ├── test_pkcs11_java.py   # Java wrappers
│       ├── test_pkcs11_cpp.py    # C++ wrappers
│       ├── test_pkcs11_go.py     # Go wrappers
│       └── test_pkcs11_gtest.py  # GTest wrappers
├── scripts/
│   ├── build.sh / build.bat      # Compile source code
│   └── run_tests.sh / .bat       # Run tests
├── logs/                         # Tool log files (auto-collected)
├── evidence/                     # Test evidence (auto-generated)
├── conftest.py                   # Auto-build + fixtures
├── Jenkinsfile                   # CI/CD pipeline
└── requirements.txt              # One line: hsm-test-framework
```

## Test Types

| Type | Marker | Source | Build |
|------|--------|--------|-------|
| Java JAR (ready) | `-m java` | `bin/*.jar` | No |
| Java JAR (source) | `-m java` | `src/java/` | Maven |
| C++ executable | `-m cpp` | `bin/pkcs11_*` | No |
| Go binary | `-m go_test` | `src/go/` | go build |
| Google Test | `-m gtest` | `src/cpp/gtest*/` | Makefile |

## Running Tests

```bash
# By type
./scripts/run_tests.sh java       # Java tests only
./scripts/run_tests.sh cpp        # C++ tests only
./scripts/run_tests.sh go_test    # Go tests only
./scripts/run_tests.sh gtest      # Google Test only

# By priority
./scripts/run_tests.sh smoke      # Quick verification
./scripts/run_tests.sh regression # Full suite

# Build + test in one command
./scripts/run_tests.sh build_and_test
```

## Log Collection

Each tool can have its own log path in `settings.yaml`:

```yaml
pkcs11_java_keygen:
  command_linux: "bin/pkcs11-keygen.jar"
  log_path_linux: "logs/java_keygen.log"      # Single file
  log_dir_linux: "logs/java/"                  # Or a directory
  log_pattern: "*.log"                         # File pattern
  gtest_xml_linux: "evidence/results.xml"      # GTest XML
```

The `log_collector` fixture auto-collects these and attaches to Allure.
