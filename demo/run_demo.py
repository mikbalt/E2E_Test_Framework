"""
Run the HSM E2E demo — all 3 integrations in one shot.

Creates a fresh Kiwi test run, executes the E-Admin smoke test with
Allure reporting + Kiwi bidirectional mode + Grafana metrics push,
then prints a summary with all dashboard URLs.

Usage:
    python demo/run_demo.py           # Run demo
    python demo/run_demo.py --open    # Run + auto-open reports in browser
    python demo/run_demo.py --skip-health-check  # Skip HSM connectivity check
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import webbrowser

# Ensure project root is importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

STATE_FILE = os.path.join(os.path.dirname(__file__), ".demo_state.json")
ALLURE_RESULTS = os.path.join(PROJECT_ROOT, "evidence", "allure-results")
ALLURE_REPORT = os.path.join(PROJECT_ROOT, "evidence", "allure-report")


def load_state():
    """Load demo state from seed step."""
    if not os.path.exists(STATE_FILE):
        print("ERROR: Demo state not found.")
        print("Run 'python demo/seed_kiwi.py' first to create test cases.")
        sys.exit(1)

    with open(STATE_FILE, "r") as f:
        return json.load(f)


def create_fresh_run(state):
    """Create a new Kiwi test run with the seeded cases."""
    from hsm_test_framework.plugin import load_config

    cfg = load_config()
    tcms_config = cfg.get("kiwi_tcms", {})
    plan_id = state["plan_id"]

    from hsm_test_framework.kiwi_tcms import KiwiReporter

    reporter = KiwiReporter(
        url=tcms_config.get("url"),
        plan_id=plan_id,
        build_id=tcms_config.get("build_id"),
        status_ids=tcms_config.get("status_ids"),
    )

    print(f"Connecting to Kiwi TCMS at {reporter.url} ...")
    if not reporter.connect():
        print("ERROR: Cannot connect to Kiwi TCMS. Check .env credentials.")
        sys.exit(1)

    run_id = reporter.create_test_run(
        summary="[Demo] E-Admin Live Demo Run",
        plan_id=plan_id,
    )
    if not run_id:
        print("ERROR: Failed to create test run.")
        sys.exit(1)

    # Add all seeded cases to the new run
    for case in state["all_cases"]:
        try:
            reporter.rpc.TestRun.add_case(run_id, case["id"])
        except Exception as e:
            print(f"  Warning: could not add case #{case['id']} to run: {e}")

    print(f"Created fresh Test Run #{run_id} with {len(state['all_cases'])} cases.")
    return run_id, reporter.url


def clean_allure_results():
    """Remove previous allure results for a clean report."""
    if os.path.isdir(ALLURE_RESULTS):
        shutil.rmtree(ALLURE_RESULTS)
    os.makedirs(ALLURE_RESULTS, exist_ok=True)


def run_tests(run_id, skip_health_check=False):
    """Execute pytest as a subprocess with all integrations enabled.

    Runs in a separate process to avoid COM threading conflicts —
    pywinauto needs CoInitializeEx() in a clean thread, which is
    impossible when pytest.main() runs in-process alongside libraries
    that already initialized COM.
    """
    demo_dir = os.path.dirname(os.path.abspath(__file__))

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/ui/e_admin/test_connect.py",
        "-v",
        "--tb=short",
        f"--alluredir={ALLURE_RESULTS}",
        f"--kiwi-run-id={run_id}",
        "-p", "conftest_demo",  # loaded via PYTHONPATH below
    ]

    if skip_health_check:
        cmd.append("--skip-health-check")

    print("\n" + "=" * 60)
    print("RUNNING TESTS")
    print("=" * 60)
    print(f"  {' '.join(cmd[2:])}")  # skip "python -m"
    print(f"  + plugin: conftest_demo (TCMS marker injection)")
    print()

    # Add demo/ to PYTHONPATH so pytest can import conftest_demo as a plugin
    env = os.environ.copy()
    env["PYTHONPATH"] = demo_dir + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT, env=env)
    return result.returncode


def generate_allure_report():
    """Generate Allure HTML report from results."""
    print("\nGenerating Allure report ...")

    try:
        subprocess.run(
            ["allure", "generate", ALLURE_RESULTS,
             "-o", ALLURE_REPORT, "--clean"],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"  Report generated at: {ALLURE_REPORT}")
        return True
    except FileNotFoundError:
        print("  WARNING: 'allure' CLI not found. Install from https://allurereport.org/")
        print(f"  Raw results available at: {ALLURE_RESULTS}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"  WARNING: Allure generation failed: {e.stderr}")
        return False


def print_summary(run_id, kiwi_url, allure_ok):
    """Print demo summary with all URLs."""
    kiwi_base = kiwi_url.replace("/xml-rpc/", "")
    kiwi_run_url = f"{kiwi_base}/runs/{run_id}/"

    from hsm_test_framework.plugin import load_config
    cfg = load_config()
    grafana_url = cfg.get("metrics", {}).get("pushgateway_url", "N/A")

    print("\n" + "=" * 60)
    print("DEMO COMPLETE — All 3 Integrations Active")
    print("=" * 60)

    print("\n  1. ALLURE REPORT (Screenshots + Evidence)")
    if allure_ok:
        allure_index = os.path.join(ALLURE_REPORT, "index.html")
        print(f"     file://{allure_index.replace(os.sep, '/')}")
    else:
        print(f"     Raw results: {ALLURE_RESULTS}")

    print(f"\n  2. KIWI TCMS (Bidirectional Test Results)")
    print(f"     {kiwi_run_url}")
    print(f"     Expected: 1 PASSED + 4 BLOCKED (coverage gap detection)")

    print(f"\n  3. GRAFANA (Metrics Dashboard)")
    print(f"     Pushgateway: {grafana_url}")
    print(f"     Import config/grafana-dashboard.json into Grafana")

    print("\n" + "=" * 60)

    return {
        "allure": os.path.join(ALLURE_REPORT, "index.html") if allure_ok else None,
        "kiwi": kiwi_run_url,
        "grafana": grafana_url,
    }


def open_reports(urls):
    """Open all report URLs in the default browser."""
    print("\nOpening reports in browser ...")

    if urls.get("allure") and os.path.exists(urls["allure"]):
        allure_uri = "file:///" + urls["allure"].replace(os.sep, "/")
        webbrowser.open(allure_uri)
        print(f"  Opened Allure report")

    if urls.get("kiwi"):
        webbrowser.open(urls["kiwi"])
        print(f"  Opened Kiwi TCMS")

    if urls.get("grafana") and urls["grafana"] != "N/A":
        webbrowser.open(urls["grafana"])
        print(f"  Opened Grafana/Pushgateway")


def main():
    parser = argparse.ArgumentParser(description="Run HSM E2E demo")
    parser.add_argument(
        "--open", action="store_true",
        help="Auto-open Allure, Kiwi, and Grafana in browser after demo",
    )
    parser.add_argument(
        "--skip-health-check", action="store_true",
        help="Skip pre-execution HSM connectivity checks",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("HSM E2E TEST FRAMEWORK — DEMO")
    print("=" * 60)

    # 1. Load seed state
    state = load_state()
    print(f"Loaded state: {len(state['all_cases'])} cases, "
          f"{len(state['tcms_marker_map'])} automated")

    # 2. Create fresh Kiwi run
    run_id, kiwi_url = create_fresh_run(state)

    # 3. Clean allure results
    clean_allure_results()

    # 4. Run tests
    exit_code = run_tests(run_id, skip_health_check=args.skip_health_check)

    # 5. Generate Allure report
    allure_ok = generate_allure_report()

    # 6. Print summary
    urls = print_summary(run_id, kiwi_url, allure_ok)

    # 7. Optionally open browsers
    if args.open:
        open_reports(urls)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
