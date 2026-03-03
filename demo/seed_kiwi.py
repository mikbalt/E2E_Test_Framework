"""
Seed Kiwi TCMS with demo test cases and an initial test run.

One-time setup: creates 5 test cases under plan_id 347 and a test run
containing all of them. Saves state to .demo_state.json for run_demo.py.

Usage:
    python demo/seed_kiwi.py          # Interactive (asks before overwrite)
    python demo/seed_kiwi.py --force  # Skip confirmation if state exists
"""

import argparse
import json
import os
import sys

# Ensure project root is importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

STATE_FILE = os.path.join(os.path.dirname(__file__), ".demo_state.json")

# The single automated test function in tests/ui/e_admin/test_connect.py
AUTOMATED_TEST = "test_connect_and_load_dashboard"

# Demo test cases to create in Kiwi TCMS.
# Only case #1 maps to an automated test; the rest are manual placeholders
# that will show up as BLOCKED in bidirectional mode (coverage gap demo).
DEMO_CASES = [
    {
        "summary": "[E2E][eAdmin][Connect] Connect to HSM and load dashboard",
        "has_automation": True,
        "maps_to": AUTOMATED_TEST,
    },
    {
        "summary": "[E2E][eAdmin][Settings] Navigate to settings panel",
        "has_automation": False,
        "maps_to": None,
    }
]


def seed(force=False):
    """Create demo cases and run in Kiwi TCMS."""
    # Guard: check existing state
    if os.path.exists(STATE_FILE) and not force:
        print(f"State file already exists: {STATE_FILE}")
        print("Use --force to overwrite, or delete the file manually.")
        answer = input("Overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return

    # Load settings (with env var overrides)
    from hsm_test_framework.plugin import load_config

    cfg = load_config()

    tcms_config = cfg.get("kiwi_tcms", {})
    plan_id = tcms_config.get("plan_id", 347)
    build_id = tcms_config.get("build_id")

    from hsm_test_framework.kiwi_tcms import KiwiReporter

    reporter = KiwiReporter(
        url=tcms_config.get("url"),
        plan_id=plan_id,
        build_id=build_id,
        status_ids=tcms_config.get("status_ids"),
    )

    print(f"Connecting to Kiwi TCMS at {reporter.url} ...")
    if not reporter.connect():
        print("ERROR: Cannot connect to Kiwi TCMS. Check .env credentials.")
        sys.exit(1)
    print("Connected.")

    # --- Create test cases ---
    print(f"\nCreating {len(DEMO_CASES)} test cases under plan #{plan_id} ...")
    created_cases = []
    tcms_marker_map = {}

    for case_def in DEMO_CASES:
        case_id = reporter.find_or_create_case(case_def["summary"])
        if not case_id:
            print(f"  FAILED: {case_def['summary']}")
            sys.exit(1)

        entry = {
            "id": case_id,
            "summary": case_def["summary"],
            "has_automation": case_def["has_automation"],
        }
        created_cases.append(entry)
        print(f"  Case #{case_id}: {case_def['summary']}")

        if case_def["maps_to"]:
            tcms_marker_map[case_def["maps_to"]] = case_id

    # --- Create test run with all cases ---
    print("\nCreating initial test run ...")
    run_id = reporter.create_test_run(
        summary="[Demo] E-Admin Integration Showcase",
        plan_id=plan_id,
    )
    if not run_id:
        print("ERROR: Failed to create test run.")
        sys.exit(1)

    # Add all cases to the run
    for case in created_cases:
        try:
            reporter.rpc.TestRun.add_case(run_id, case["id"])
        except Exception as e:
            print(f"  Warning: could not add case #{case['id']} to run: {e}")

    print(f"  Test Run #{run_id} created with {len(created_cases)} cases.")

    # --- Save state ---
    state = {
        "plan_id": plan_id,
        "test_run_id": run_id,
        "tcms_marker_map": tcms_marker_map,
        "all_cases": created_cases,
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    print(f"\nState saved to {STATE_FILE}")

    # --- Summary ---
    kiwi_base = reporter.url.replace("/xml-rpc/", "")
    print("\n" + "=" * 60)
    print("SEED COMPLETE")
    print("=" * 60)
    print(f"  Plan:       {kiwi_base}/plan/{plan_id}/")
    print(f"  Test Run:   {kiwi_base}/runs/{run_id}/")
    print(f"  Cases:      {len(created_cases)}")
    print(f"  Automated:  {sum(1 for c in created_cases if c['has_automation'])}")
    print(f"  Manual:     {sum(1 for c in created_cases if not c['has_automation'])}")
    print()
    print("Next step: python demo/run_demo.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Kiwi TCMS for demo")
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite existing state without confirmation",
    )
    args = parser.parse_args()
    seed(force=args.force)
