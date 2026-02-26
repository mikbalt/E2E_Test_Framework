"""
Kiwi TCMS Integration - Report test results to Kiwi Test Case Management System.

Syncs pytest results with Kiwi TCMS test runs/cases.

Requires environment variables:
    TCMS_API_URL=https://kiwi.yourcompany.com/xml-rpc/
    TCMS_USERNAME=your_user
    TCMS_PASSWORD=your_pass

Usage (via conftest.py - automatic):
    Results are automatically pushed after test session completes.

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


# Status IDs in Kiwi TCMS (default installation)
STATUS_POSITIVE = 4  # PASSED
STATUS_NEGATIVE = 5  # FAILED
STATUS_BLOCKED = 6   # BLOCKED/ERROR


class KiwiReporter:
    """Report test results to Kiwi TCMS."""

    def __init__(self, url=None, username=None, password=None,
                 product=None, plan_id=None, build_id=None):
        self.url = url or os.environ.get("TCMS_API_URL", "")
        self.username = username or os.environ.get("TCMS_USERNAME", "")
        self.password = password or os.environ.get("TCMS_PASSWORD", "")
        self.product = product or "HSM Suite"
        self.plan_id = plan_id
        self.build_id = build_id
        self.rpc = None
        self.test_run_id = None
        self.results = []
        self._category_id = None

    def connect(self):
        """Connect to Kiwi TCMS XML-RPC API."""
        try:
            from tcms_api import TCMS

            # Allow self-signed certificates (common for internal Kiwi instances)
            ssl._create_default_https_context = ssl._create_unverified_context

            self.rpc = TCMS(self.url, self.username, self.password).exec
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
            "PASSED": STATUS_POSITIVE,
            "FAILED": STATUS_NEGATIVE,
            "BLOCKED": STATUS_BLOCKED,
            "ERROR": STATUS_BLOCKED,
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
                    "status": status_map.get(status, STATUS_BLOCKED),
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
