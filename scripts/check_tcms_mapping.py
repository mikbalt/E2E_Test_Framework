"""
Check mapping between Kiwi TCMS TestRun and pytest test functions.

Collects @pytest.mark.tcms(case_id=X) markers from the repo,
fetches cases from a Kiwi TestRun, and shows:

  - Matched:   TCMS case has a corresponding pytest test
  - No Auto:   TCMS case exists but no pytest test is linked
  - Orphan:    pytest test has @tcms marker but case_id not in the TestRun
  - Suggest:   Tag-based suggestions for unmatched TCMS cases

Usage:
    python scripts/check_tcms_mapping.py --run-id 28
    python scripts/check_tcms_mapping.py --run-id 28 --test-dir tests/
    python scripts/check_tcms_mapping.py --run-id 28 --verbose
"""

import argparse
import ast
import os
import re
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


# ── 1. Collect @pytest.mark.tcms markers from source files ─────────────

def collect_tcms_markers(test_dir):
    """
    Parse Python test files and extract @pytest.mark.tcms(case_id=X).

    Returns dict: {case_id: {"file": path, "function": name, "class": name|None}}
    """
    markers = {}

    for root, _dirs, files in os.walk(test_dir):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            filepath = os.path.join(root, fname)
            _parse_file_for_tcms(filepath, markers)

    return markers


def _parse_file_for_tcms(filepath, markers):
    """Parse a single file for @pytest.mark.tcms decorators."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except (SyntaxError, UnicodeDecodeError):
        return

    rel_path = os.path.relpath(filepath, PROJECT_ROOT)

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_"):
            continue

        # Find parent class if any
        class_name = _find_parent_class(tree, node)

        for decorator in node.decorator_list:
            case_id = _extract_tcms_case_id(decorator)
            if case_id is not None:
                markers[case_id] = {
                    "file": rel_path,
                    "function": node.name,
                    "class": class_name,
                    "line": node.lineno,
                }


def _find_parent_class(tree, func_node):
    """Find the class that contains a function node."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for child in ast.walk(node):
                if child is func_node:
                    return node.name
    return None


def _extract_tcms_case_id(decorator):
    """Extract case_id from @pytest.mark.tcms(case_id=X)."""
    # Handle: @pytest.mark.tcms(case_id=37509)
    if isinstance(decorator, ast.Call):
        # Get the function being called
        func = decorator.func

        # Check if it's pytest.mark.tcms or just tcms
        is_tcms = False
        if isinstance(func, ast.Attribute) and func.attr == "tcms":
            is_tcms = True
        elif isinstance(func, ast.Name) and func.id == "tcms":
            is_tcms = True

        if is_tcms:
            for kw in decorator.keywords:
                if kw.arg == "case_id" and isinstance(kw.value, ast.Constant):
                    return kw.value.value
    return None


# ── 2. Fetch TCMS cases from a TestRun ─────────────────────────────────

def fetch_tcms_cases(run_id):
    """
    Fetch all test cases from a Kiwi TCMS TestRun.

    Returns list of dicts: [{"id": int, "summary": str, "status_id": int}]
    """
    from hsm_test_framework.plugin import load_config
    from hsm_test_framework.kiwi_tcms import KiwiReporter

    cfg = load_config()
    tcms_config = cfg.get("kiwi_tcms", {})

    reporter = KiwiReporter(
        url=tcms_config.get("url"),
        plan_id=tcms_config.get("plan_id"),
        build_id=tcms_config.get("build_id"),
    )

    if not reporter.connect():
        print("ERROR: Cannot connect to Kiwi TCMS")
        sys.exit(1)

    executions = reporter.rpc.TestExecution.filter({"run": run_id})
    cases = []
    for ex in executions:
        case_id = ex.get("case")
        case_data = reporter.rpc.TestCase.filter({"id": case_id})
        summary = case_data[0].get("summary", f"Case #{case_id}") if case_data else f"Case #{case_id}"
        cases.append({
            "id": case_id,
            "summary": summary,
            "status_id": ex.get("status"),
        })

    return cases


# ── 3. Tag-based matching suggestions ──────────────────────────────────

def extract_tags(summary):
    """Extract bracket tags from TCMS summary.

    "[E2E][e-admin][Key Ceremony] ..." → ["e2e", "e-admin", "key ceremony"]
    """
    return [tag.lower() for tag in re.findall(r"\[([^\]]+)\]", summary)]


def suggest_matches(tcms_cases, test_dir):
    """
    For unmatched TCMS cases, suggest possible test matches based on tags.

    Looks at test file paths and function names for tag overlap.
    """
    suggestions = {}

    # Collect all test functions (not just tcms-marked ones)
    test_funcs = []
    for root, _dirs, files in os.walk(test_dir):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            filepath = os.path.join(root, fname)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source, filename=filepath)
            except (SyntaxError, UnicodeDecodeError):
                continue

            rel_path = os.path.relpath(filepath, PROJECT_ROOT)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("test_"):
                        # Build searchable text from path + function name
                        searchable = f"{rel_path} {node.name}".lower().replace("_", " ").replace("-", " ")
                        test_funcs.append({
                            "file": rel_path,
                            "function": node.name,
                            "line": node.lineno,
                            "searchable": searchable,
                        })

    for case in tcms_cases:
        tags = extract_tags(case["summary"])
        # Also use words from the non-tag portion
        non_tag = re.sub(r"\[[^\]]+\]", "", case["summary"]).strip().lower()
        keywords = tags + non_tag.split()

        matches = []
        for tf in test_funcs:
            score = sum(1 for kw in keywords if kw in tf["searchable"])
            if score > 0:
                matches.append((score, tf))

        matches.sort(key=lambda x: -x[0])
        if matches:
            suggestions[case["id"]] = matches[:3]  # top 3

    return suggestions


# ── 4. Report ──────────────────────────────────────────────────────────

STATUS_NAMES = {1: "IDLE", 2: "RUNNING", 4: "PASSED", 5: "FAILED", 6: "BLOCKED"}


def print_report(tcms_cases, repo_markers, suggestions, verbose=False):
    """Print the comparison report."""
    tcms_ids = {c["id"] for c in tcms_cases}
    repo_ids = set(repo_markers.keys())

    matched_ids = tcms_ids & repo_ids
    no_auto_ids = tcms_ids - repo_ids
    orphan_ids = repo_ids - tcms_ids

    tcms_by_id = {c["id"]: c for c in tcms_cases}

    print("=" * 70)
    print("TCMS <-> REPO MAPPING REPORT")
    print("=" * 70)

    # -- Matched --
    print(f"\n[OK] MATCHED ({len(matched_ids)})")
    if matched_ids:
        for cid in sorted(matched_ids):
            tc = tcms_by_id[cid]
            rm = repo_markers[cid]
            status = STATUS_NAMES.get(tc["status_id"], "?")
            print(f"  Case #{cid} [{status}]")
            print(f"    TCMS:  {tc['summary']}")
            print(f"    Repo:  {rm['file']}:{rm['line']}  {rm['function']}()")
    else:
        print("  (none)")

    # -- No Automation --
    print(f"\n[!!] NO AUTOMATION ({len(no_auto_ids)}) -- TCMS cases without @pytest.mark.tcms")
    if no_auto_ids:
        for cid in sorted(no_auto_ids):
            tc = tcms_by_id[cid]
            status = STATUS_NAMES.get(tc["status_id"], "?")
            print(f"  Case #{cid} [{status}]: {tc['summary']}")

            # Show suggestions
            if cid in suggestions:
                print(f"    Suggested matches:")
                for score, tf in suggestions[cid]:
                    print(f"      score={score}  {tf['file']}:{tf['line']}  {tf['function']}()")
    else:
        print("  (none)")

    # -- Orphan markers --
    print(f"\n[??] ORPHAN MARKERS ({len(orphan_ids)}) -- @pytest.mark.tcms not in this TestRun")
    if orphan_ids:
        for cid in sorted(orphan_ids):
            rm = repo_markers[cid]
            print(f"  Case #{cid}: {rm['file']}:{rm['line']}  {rm['function']}()")
    else:
        print("  (none)")

    # -- Summary --
    total_tcms = len(tcms_cases)
    coverage = (len(matched_ids) / total_tcms * 100) if total_tcms else 0
    print(f"\n{'-' * 70}")
    print(f"TCMS cases: {total_tcms}  |  Matched: {len(matched_ids)}  |  "
          f"No auto: {len(no_auto_ids)}  |  Orphan: {len(orphan_ids)}")
    print(f"Automation coverage: {coverage:.0f}%")
    print("=" * 70)

    return len(no_auto_ids) == 0 and len(orphan_ids) == 0


def main():
    parser = argparse.ArgumentParser(
        description="Check TCMS <-> repo test mapping"
    )
    parser.add_argument(
        "--run-id", type=int, required=True,
        help="Kiwi TCMS TestRun ID to check",
    )
    parser.add_argument(
        "--test-dir", default="tests",
        help="Directory to scan for pytest tests (default: tests/)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show extra detail",
    )
    args = parser.parse_args()

    test_dir = os.path.join(PROJECT_ROOT, args.test_dir)
    if not os.path.isdir(test_dir):
        print(f"ERROR: Test directory not found: {test_dir}")
        sys.exit(1)

    print(f"Scanning repo tests in: {args.test_dir}/")
    repo_markers = collect_tcms_markers(test_dir)
    print(f"  Found {len(repo_markers)} @pytest.mark.tcms marker(s)")

    print(f"\nFetching TCMS TestRun #{args.run_id} ...")
    tcms_cases = fetch_tcms_cases(args.run_id)
    print(f"  Found {len(tcms_cases)} test case(s)")

    # Compute suggestions for unmatched
    tcms_ids = {c["id"] for c in tcms_cases}
    unmatched_cases = [c for c in tcms_cases if c["id"] not in repo_markers]
    suggestions = suggest_matches(unmatched_cases, test_dir) if unmatched_cases else {}

    print()
    all_ok = print_report(tcms_cases, repo_markers, suggestions, verbose=args.verbose)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
