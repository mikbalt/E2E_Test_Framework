"""
Kiwi TCMS Integration - Report test results to Kiwi Test Case Management System.

Supports both push-only and bidirectional modes:
  - Push-only: Create test run, push results after execution (default).
  - Bidirectional: Pull test cases from an existing TestRun, filter pytest
    collection, execute only matching tests, push results back.

Requires environment variables:
    TCMS_API_URL=https://kiwi.yourcompany.com/xml-rpc/
    TCMS_USERNAME=your_user
    TCMS_PASSWORD=your_pass

Usage (via conftest.py - automatic):
    Results are automatically pushed after test session completes.

Bidirectional usage:
    pytest --kiwi-run-id=123

Manual usage:
    reporter = KiwiReporter(url, username, password)
    reporter.create_test_run("HSM Smoke Test", plan_id=1)
    reporter.report_result("test_login", status="PASSED", comment="All good")
    reporter.finalize()
"""

import base64
import datetime
import logging
import os
import ssl

logger = logging.getLogger(__name__)


# Default status IDs in Kiwi TCMS (default installation).
# Can be overridden via settings.yaml kiwi_tcms.status_ids
DEFAULT_STATUS_IDS = {
    "PASSED": 4,
    "FAILED": 5,
    "BLOCKED": 6,
}


class KiwiReporter:
    """Report test results to Kiwi TCMS (push-only and bidirectional)."""

    def __init__(self, url=None, username=None, password=None,
                 product=None, plan_id=None, build_id=None,
                 status_ids=None):
        self.url = url or os.environ.get("TCMS_API_URL", "")
        self.username = username or os.environ.get("TCMS_USERNAME", "")
        self.password = password or os.environ.get("TCMS_PASSWORD", "")
        self.product = product or "HSM Suite"
        self.plan_id = plan_id
        self.build_id = build_id
        self.status_ids = {**DEFAULT_STATUS_IDS, **(status_ids or {})}
        self.rpc = None
        self.test_run_id = None
        self.results = []
        self._category_id = None

    def connect(self):
        """Connect to Kiwi TCMS XML-RPC API."""
        try:
            from tcms_api import TCMS

            # Allow self-signed certificates (common for internal Kiwi instances).
            # Scoped: restore original context factory after connection to avoid
            # global side effects on other HTTPS connections.
            original_ctx_factory = ssl._create_default_https_context
            ssl._create_default_https_context = ssl._create_unverified_context
            try:
                self.rpc = TCMS(self.url, self.username, self.password).exec
            finally:
                ssl._create_default_https_context = original_ctx_factory

            logger.info(f"Connected to Kiwi TCMS: {self.url}")

            # Resolve default category from the plan's product
            self._resolve_category()

            return True
        except Exception as e:
            logger.warning(f"Cannot connect to Kiwi TCMS: {e}")
            return False

    def _resolve_category(self):
        """Lookup default category from the plan's product."""
        try:
            plans = self.rpc.TestPlan.filter({"id": self.plan_id})
            if plans:
                product_id = plans[0].get("product")
                cats = self.rpc.Category.filter({"product": product_id})
                if cats:
                    self._category_id = cats[0]["id"]
                    logger.info(f"Resolved category: {cats[0]['name']} (ID: {self._category_id})")
        except Exception as e:
            logger.warning(f"Could not resolve category: {e}")

    def create_test_run(self, summary=None, plan_id=None):
        """Create a new test run in Kiwi TCMS."""
        if not self.rpc:
            return None

        plan_id = plan_id or self.plan_id
        if not summary:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            summary = f"Automated Run - {now}"

        try:
            create_data = {
                "summary": summary,
                "plan": plan_id,
                "manager": self.username,
            }
            if self.build_id:
                create_data["build"] = self.build_id

            run = self.rpc.TestRun.create(create_data)
            self.test_run_id = run["id"]
            logger.info(f"Created test run #{self.test_run_id}: {summary}")
            return self.test_run_id
        except Exception as e:
            logger.error(f"Failed to create test run: {e}")
            return None

    def find_or_create_case(self, test_name, category="Automation"):
        """Find existing test case or create a new one."""
        if not self.rpc:
            return None

        try:
            cases = self.rpc.TestCase.filter({
                "summary": test_name,
                "plan": self.plan_id,
            })

            if cases:
                return cases[0]["id"]

            # Create new test case
            case = self.rpc.TestCase.create({
                "summary": test_name,
                "category": self._category_id or 1,
                "priority": 2,
                "case_status": 2,  # CONFIRMED
                "plan": self.plan_id,
            })
            logger.info(f"Created test case #{case['id']}: {test_name}")
            return case["id"]
        except Exception as e:
            logger.error(f"Failed to find/create test case: {e}")
            return None

    def report_result(self, test_name, status="PASSED", comment="",
                      duration=0, evidence_dir=None):
        """
        Report a single test result.

        Args:
            test_name: Name of the test case.
            status: "PASSED", "FAILED", or "BLOCKED".
            comment: Additional comment/notes.
            duration: Test duration in seconds.
            evidence_dir: Path to evidence directory with screenshots/logs to attach.
        """
        status_map = {
            "PASSED": self.status_ids["PASSED"],
            "FAILED": self.status_ids["FAILED"],
            "BLOCKED": self.status_ids["BLOCKED"],
            "ERROR": self.status_ids["BLOCKED"],
        }

        result_entry = {
            "test_name": test_name,
            "status": status,
            "comment": comment,
            "duration": duration,
        }
        self.results.append(result_entry)

        if not self.rpc or not self.test_run_id:
            return

        try:
            case_id = self.find_or_create_case(test_name)
            if not case_id:
                return

            # Add case to run if not already there
            self.rpc.TestRun.add_case(self.test_run_id, case_id)

            # Get the execution for this case in this run
            executions = self.rpc.TestExecution.filter({
                "run": self.test_run_id,
                "case": case_id,
            })

            if executions:
                execution_id = executions[0]["id"]
                self.rpc.TestExecution.update(execution_id, {
                    "status": status_map.get(status, self.status_ids["BLOCKED"]),
                })

                if comment:
                    self.rpc.TestExecution.add_comment(execution_id, comment)

                # Attach evidence files (screenshots, logs) if available
                if evidence_dir and os.path.isdir(evidence_dir):
                    self._attach_evidence_files(execution_id, evidence_dir)

            logger.info(f"Reported to TCMS: {test_name} = {status}")
        except Exception as e:
            logger.error(f"Failed to report result: {e}")

    def _attach_evidence_files(self, execution_id, evidence_dir):
        """Attach evidence files (screenshots, logs, summary) to a test execution."""
        if not self.rpc:
            return

        attachments = []

        # Collect text files first (summary, log)
        for filename in ("summary.txt", "test_log.txt"):
            filepath = os.path.join(evidence_dir, filename)
            if os.path.isfile(filepath):
                attachments.append((filename, filepath))

        # Collect all PNG screenshots
        for filename in sorted(os.listdir(evidence_dir)):
            if filename.endswith(".png"):
                filepath = os.path.join(evidence_dir, filename)
                if os.path.isfile(filepath):
                    attachments.append((filename, filepath))

        for filename, filepath in attachments:
            try:
                with open(filepath, "rb") as f:
                    b64content = base64.b64encode(f.read()).decode("ascii")

                self.rpc.TestExecution.add_attachment(
                    execution_id, filename, b64content
                )
                logger.info(f"Attached to execution #{execution_id}: {filename}")
            except Exception as e:
                logger.warning(f"Failed to attach {filename}: {e}")

    # ------------------------------------------------------------------
    # Bidirectional methods (pull from Kiwi → filter → execute → push)
    # ------------------------------------------------------------------

    def use_existing_run(self, run_id):
        """
        Attach to an existing TestRun instead of creating a new one.

        Args:
            run_id: Kiwi TCMS TestRun ID.

        Returns:
            True if the run was found and attached, False otherwise.
        """
        if not self.rpc:
            return False

        try:
            runs = self.rpc.TestRun.filter({"id": run_id})
            if not runs:
                logger.error(f"TestRun #{run_id} not found in Kiwi TCMS")
                return False

            self.test_run_id = run_id
            run_info = runs[0]
            logger.info(
                f"Attached to existing TestRun #{run_id}: "
                f"'{run_info.get('summary', '')}'"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to attach to TestRun #{run_id}: {e}")
            return False

    def get_cases_from_run(self, run_id=None):
        """
        Fetch all TestCase summaries from a TestRun.

        Args:
            run_id: TestRun ID. Defaults to self.test_run_id.

        Returns:
            List of dicts: [{"id": case_id, "summary": "test name",
                             "execution_id": exec_id}, ...]
        """
        run_id = run_id or self.test_run_id
        if not self.rpc or not run_id:
            return []

        try:
            executions = self.rpc.TestExecution.filter({"run": run_id})
            cases = []
            for execution in executions:
                case_id = execution.get("case")
                case_data = self.rpc.TestCase.filter({"id": case_id})
                if case_data:
                    cases.append({
                        "id": case_data[0]["id"],
                        "summary": case_data[0].get("summary", ""),
                        "execution_id": execution["id"],
                    })
            logger.info(f"Fetched {len(cases)} test cases from TestRun #{run_id}")
            return cases
        except Exception as e:
            logger.error(f"Failed to fetch cases from TestRun #{run_id}: {e}")
            return []

    def get_active_runs(self, plan_id=None):
        """
        Fetch active (non-finished) TestRuns from a TestPlan.

        Args:
            plan_id: TestPlan ID. Defaults to self.plan_id.

        Returns:
            List of run dicts from Kiwi TCMS.
        """
        plan_id = plan_id or self.plan_id
        if not self.rpc or not plan_id:
            return []

        try:
            runs = self.rpc.TestRun.filter({
                "plan": plan_id,
                "stop_date__isnull": True,
            })
            logger.info(f"Found {len(runs)} active runs for plan #{plan_id}")
            return runs
        except Exception as e:
            logger.error(f"Failed to fetch runs for plan #{plan_id}: {e}")
            return []

    def report_result_by_case_id(self, case_id, status="PASSED", comment="",
                                  duration=0, evidence_dir=None):
        """
        Report result for a specific case_id (bidirectional mode).

        Unlike report_result(), this uses the case_id directly without
        calling find_or_create_case, assuming the case already exists
        in the TestRun.

        Args:
            case_id: Kiwi TCMS TestCase ID.
            status: "PASSED", "FAILED", or "BLOCKED".
            comment: Additional comment/notes.
            duration: Test duration in seconds.
            evidence_dir: Path to evidence directory.
        """
        status_map = {
            "PASSED": self.status_ids["PASSED"],
            "FAILED": self.status_ids["FAILED"],
            "BLOCKED": self.status_ids["BLOCKED"],
            "ERROR": self.status_ids["BLOCKED"],
        }

        result_entry = {
            "test_name": f"case#{case_id}",
            "status": status,
            "comment": comment,
            "duration": duration,
        }
        self.results.append(result_entry)

        if not self.rpc or not self.test_run_id:
            return

        try:
            executions = self.rpc.TestExecution.filter({
                "run": self.test_run_id,
                "case": case_id,
            })
            if executions:
                execution_id = executions[0]["id"]
                self.rpc.TestExecution.update(execution_id, {
                    "status": status_map.get(status, self.status_ids["BLOCKED"]),
                })
                if comment:
                    self.rpc.TestExecution.add_comment(execution_id, comment)
                if evidence_dir and os.path.isdir(evidence_dir):
                    self._attach_evidence_files(execution_id, evidence_dir)

                logger.info(f"Reported to TCMS: case #{case_id} = {status}")
            else:
                logger.warning(
                    f"No execution found for case #{case_id} "
                    f"in run #{self.test_run_id}"
                )
        except Exception as e:
            logger.error(f"Failed to report result for case #{case_id}: {e}")

    def mark_unmatched_as_blocked(self, unmatched_cases):
        """
        Mark TCMS cases that have no matching automation test as BLOCKED.

        Called during bidirectional mode when some TCMS TestRun cases
        could not be matched to any Python test via @pytest.mark.tcms.

        Args:
            unmatched_cases: List of dicts from get_cases_from_run(),
                each with keys: id, summary, execution_id.
        """
        if not self.rpc or not self.test_run_id:
            return

        blocked_status = self.status_ids["BLOCKED"]

        for case in unmatched_cases:
            execution_id = case.get("execution_id")
            case_id = case.get("id")
            summary = case.get("summary", "")

            if not execution_id:
                logger.warning(
                    f"No execution_id for unmatched case #{case_id}, skipping"
                )
                continue

            try:
                self.rpc.TestExecution.update(execution_id, {
                    "status": blocked_status,
                })
                self.rpc.TestExecution.add_comment(
                    execution_id,
                    f"BLOCKED: No automation test found for this case. "
                    f"Add @pytest.mark.tcms(case_id={case_id}) to a Python "
                    f"test function to link it.",
                )
                logger.info(
                    f"Marked as BLOCKED: case #{case_id} ({summary})"
                )

                self.results.append({
                    "test_name": summary or f"case#{case_id}",
                    "status": "BLOCKED",
                    "comment": "No automation test available",
                    "duration": 0,
                })
            except Exception as e:
                logger.error(
                    f"Failed to mark case #{case_id} as BLOCKED: {e}"
                )

    def finalize(self):
        """Finalize and log summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASSED")
        failed = sum(1 for r in self.results if r["status"] == "FAILED")
        errors = sum(1 for r in self.results if r["status"] in ("BLOCKED", "ERROR"))

        logger.info(
            f"Kiwi TCMS Summary: {total} tests | "
            f"{passed} passed | {failed} failed | {errors} errors"
        )

        if self.test_run_id:
            logger.info(
                f"Test Run URL: {self.url.replace('/xml-rpc/', '')}"
                f"/runs/{self.test_run_id}/"
            )
