"""
Sync Kiwi TCMS test run results to Grafana via Pushgateway.

Reads current execution statuses from a Kiwi test run and pushes
updated metrics to Prometheus Pushgateway. Use this after manual
testing in Kiwi so Grafana reflects the latest results.

Usage:
    python demo/sync_metrics.py                # One-shot sync
    python demo/sync_metrics.py --watch        # Sync every 30s
    python demo/sync_metrics.py --watch --interval 10  # Custom interval
    python demo/sync_metrics.py --run-id 25    # Sync specific run
"""

import argparse
import json
import os
import sys
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

STATE_FILE = os.path.join(os.path.dirname(__file__), ".demo_state.json")

# Kiwi TCMS status IDs (default installation)
STATUS_NAMES = {
    1: "IDLE",
    2: "RUNNING",
    4: "PASSED",
    5: "FAILED",
    6: "BLOCKED",
}


def load_state():
    """Load demo state."""
    if not os.path.exists(STATE_FILE):
        print("ERROR: Demo state not found. Run 'python demo/seed_kiwi.py' first.")
        sys.exit(1)
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def fetch_run_results(reporter, run_id):
    """Fetch all execution statuses from a Kiwi test run."""
    executions = reporter.rpc.TestExecution.filter({"run": run_id})

    results = {"PASSED": 0, "FAILED": 0, "BLOCKED": 0, "OTHER": 0}
    details = []

    for ex in executions:
        status_id = ex.get("status")
        status_name = STATUS_NAMES.get(status_id, "OTHER")

        # Map IDLE/RUNNING to OTHER (not yet tested)
        if status_name in ("IDLE", "RUNNING"):
            results["OTHER"] += 1
            bucket = "OTHER"
        elif status_name in results:
            results[status_name] += 1
            bucket = status_name
        else:
            results["OTHER"] += 1
            bucket = "OTHER"

        # Get case summary
        case_id = ex.get("case")
        case_data = reporter.rpc.TestCase.filter({"id": case_id})
        summary = case_data[0].get("summary", f"Case #{case_id}") if case_data else f"Case #{case_id}"

        details.append({
            "case_id": case_id,
            "summary": summary,
            "status": bucket,
        })

    return results, details


def push_metrics(results, duration=0):
    """Push results to Pushgateway."""
    from hsm_test_framework.plugin import load_config

    cfg = load_config()
    metrics_config = cfg.get("metrics", {})
    if not metrics_config.get("enabled"):
        print("WARNING: Metrics disabled in settings.yaml")
        return False

    from hsm_test_framework.grafana_push import MetricsPusher

    pusher = MetricsPusher(
        pushgateway_url=metrics_config.get("pushgateway_url"),
        job_name=metrics_config.get("job_name", "hsm_tests"),
        labels=metrics_config.get("labels", {}),
    )

    total_executed = results["PASSED"] + results["FAILED"]
    blocked = results["BLOCKED"] + results["OTHER"]
    total = total_executed + blocked

    pusher.record_suite(
        "hsm",
        total=total_executed,
        passed=results["PASSED"],
        duration=duration,
        blocked=blocked,
    )
    pusher.push()
    return True


def sync_once(reporter, run_id):
    """Perform a single sync: Kiwi → Grafana."""
    timestamp = time.strftime("%H:%M:%S")

    results, details = fetch_run_results(reporter, run_id)

    total = sum(results.values())
    print(f"[{timestamp}] Run #{run_id}: "
          f"{results['PASSED']} passed, "
          f"{results['FAILED']} failed, "
          f"{results['BLOCKED']} blocked, "
          f"{results['OTHER']} idle "
          f"(total: {total})")

    for d in details:
        icon = {"PASSED": "+", "FAILED": "x", "BLOCKED": "!", "OTHER": "?"}
        print(f"  [{icon.get(d['status'], '?')}] {d['summary']}")

    if push_metrics(results):
        print(f"[{timestamp}] Metrics pushed to Pushgateway")
    else:
        print(f"[{timestamp}] Metrics push skipped")

    return results


def main():
    parser = argparse.ArgumentParser(description="Sync Kiwi TCMS → Grafana metrics")
    parser.add_argument(
        "--run-id", type=int, default=None,
        help="Kiwi test run ID to sync (default: latest from state)",
    )
    parser.add_argument(
        "--watch", action="store_true",
        help="Continuously sync at regular intervals",
    )
    parser.add_argument(
        "--interval", type=int, default=30,
        help="Sync interval in seconds (default: 30, used with --watch)",
    )
    args = parser.parse_args()

    # Load state for default run_id
    state = load_state()
    run_id = args.run_id or state.get("test_run_id")

    if not run_id:
        print("ERROR: No run ID. Use --run-id or run seed_kiwi.py first.")
        sys.exit(1)

    # Connect to Kiwi
    from hsm_test_framework.plugin import load_config

    cfg = load_config()
    tcms_config = cfg.get("kiwi_tcms", {})

    from hsm_test_framework.kiwi_tcms import KiwiReporter

    reporter = KiwiReporter(
        url=tcms_config.get("url"),
        plan_id=state.get("plan_id"),
        build_id=tcms_config.get("build_id"),
    )

    print(f"Connecting to Kiwi TCMS at {reporter.url} ...")
    if not reporter.connect():
        print("ERROR: Cannot connect to Kiwi TCMS.")
        sys.exit(1)

    print(f"Syncing Test Run #{run_id} → Grafana")
    print("=" * 50)

    if args.watch:
        print(f"Watch mode: syncing every {args.interval}s (Ctrl+C to stop)\n")
        try:
            while True:
                sync_once(reporter, run_id)
                print()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        sync_once(reporter, run_id)

    reporter.finalize()


if __name__ == "__main__":
    main()
