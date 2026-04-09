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
import contextlib
import datetime
import html as html_mod
import io
import json
import logging
import os
import zipfile
import ssl

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def _unverified_ssl():
    """Temporarily disable SSL certificate verification (process-global).

    Restores the original factory on exit, even if an exception occurs.
    """
    original = ssl._create_default_https_context
    ssl._create_default_https_context = ssl._create_unverified_context
    try:
        yield
    finally:
        ssl._create_default_https_context = original


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
                 plan_id=None, build_id=None, status_ids=None):
        self.url = url or os.environ.get("TCMS_API_URL", "")
        self.username = username or os.environ.get("TCMS_USERNAME", "")
        self.password = password or os.environ.get("TCMS_PASSWORD", "")
        self.plan_id = plan_id
        self.build_id = build_id
        self.status_ids = {**DEFAULT_STATUS_IDS, **(status_ids or {})}
        self.rpc = None
        self.test_run_id = None
        self.results = []
        self._category_id = None
        self._ssl_cm = None

    def connect(self):
        """Connect to Kiwi TCMS XML-RPC API."""
        try:
            from tcms_api import TCMS

            # WARNING: process-global SSL override.
            # Internal Kiwi instances commonly use self-signed certs.
            # The context manager restores the original factory in finalize()
            # or on crash.
            self._ssl_cm = _unverified_ssl()
            self._ssl_cm.__enter__()
            self.rpc = TCMS(self.url, self.username, self.password).exec

            logger.info(f"Connected to Kiwi TCMS: {self.url}")

            # Resolve default category from the plan's product
            self._resolve_category()

            return True
        except Exception as e:
            # Restore SSL on connect failure
            if self._ssl_cm:
                self._ssl_cm.__exit__(None, None, None)
                self._ssl_cm = None
            logger.warning(f"Cannot connect to Kiwi TCMS: {e}")
            return False

    def _resolve_category(self):
        """Lookup default category from the plan's product.

        Only needed for push-only mode (create_test_run / find_or_create_case).
        Silently skipped when plan_id is not set (e.g. bidirectional mode).
        """
        if not self.plan_id:
            return
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
                      duration=0, nodeid=None, evidence_dir=None):
        """
        Report a single test result.

        Args:
            test_name: Name of the test case.
            status: "PASSED", "FAILED", or "BLOCKED".
            comment: Additional comment/notes.
            duration: Test duration in seconds.
            nodeid: pytest nodeid used to find allure results for attachment.
            evidence_dir: Path to the test's evidence directory (for zip attachments).
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

                # Attach evidence HTML from allure results
                self._attach_evidence_files(
                    execution_id, nodeid=nodeid, case_id=case_id,
                    evidence_dir=evidence_dir,
                )

            logger.info(f"Reported to TCMS: {test_name} = {status}")
        except Exception as e:
            logger.error(f"Failed to report result: {e}")

    def _attach_evidence_files(self, execution_id, nodeid=None, case_id=None,
                               evidence_dir=None):
        """Build evidence ZIP with HTML report + allure results and attach it.

        ZIP contents:
          - evidence_report.html  (self-contained HTML with embedded screenshots)
          - allure-results/       (raw allure JSON + attachment files for full report)

        Naming convention:
          TC-{case_id}_{short_name}_{STATUS}_{YYYYMMDD_HHmmss}.zip
        """
        if not self.rpc:
            return

        allure_dir = os.path.join("evidence", "allure-results")
        if not os.path.isdir(allure_dir):
            logger.warning("No allure-results directory found, skipping attachment")
            return

        allure_data = self._find_allure_result(allure_dir, nodeid)
        if not allure_data:
            logger.warning(f"No allure result found for {nodeid}, skipping attachment")
            return

        try:
            # --- Build standardized ZIP filename ---
            status = allure_data.get("status", "unknown").upper()
            test_name = allure_data.get("name", "test")
            # Shorten to safe filename: lowercase, underscores, max 40 chars
            short_name = (
                test_name.lower()
                .replace(" ", "_")
                .replace("-", "_")
            )
            # Keep only alphanumeric + underscore
            short_name = "".join(
                c for c in short_name if c.isalnum() or c == "_"
            )[:40]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            case_tag = f"TC-{case_id}" if case_id else "TC-unknown"
            zip_filename = f"{case_tag}_{short_name}_{status}_{timestamp}.zip"

            # --- Build HTML report ---
            report_html = _build_allure_html(allure_data, allure_dir)

            # --- Collect allure result files for this test ---
            # Find the source JSON filename
            allure_files = {}  # {arcname: filepath}
            for filename in os.listdir(allure_dir):
                if not filename.endswith("-result.json"):
                    continue
                filepath = os.path.join(allure_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data.get("fullName") == allure_data.get("fullName"):
                        allure_files[f"allure-results/{filename}"] = filepath
                        # Collect all referenced attachment files
                        self._collect_allure_attachments(
                            data, allure_dir, allure_files
                        )
                        break
                except (json.JSONDecodeError, OSError):
                    continue

            # --- Collect evidence directory zips (AppLogs, RemoteLogs) ---
            evidence_zips = {}  # {arcname: filepath}
            if evidence_dir and os.path.isdir(evidence_dir):
                for fname in os.listdir(evidence_dir):
                    if fname.endswith(".zip"):
                        evidence_zips[f"evidence/{fname}"] = os.path.join(
                            evidence_dir, fname
                        )

            # --- Build ZIP ---
            # Kiwi TCMS blocks raw HTML uploads (forbidden <body> tag).
            # Wrap in a ZIP that includes the HTML + raw allure data +
            # evidence zips (AppLogs, RemoteLogs).
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("evidence_report.html", report_html.encode("utf-8"))
                for arcname, filepath in allure_files.items():
                    zf.write(filepath, arcname)
                for arcname, filepath in evidence_zips.items():
                    zf.write(filepath, arcname)
            b64content = base64.b64encode(zip_buffer.getvalue()).decode("ascii")

            self.rpc.TestExecution.add_attachment(
                execution_id, zip_filename, b64content
            )
            logger.info(
                f"Attached {zip_filename} to execution #{execution_id} "
                f"({len(allure_files)} allure files, "
                f"{len(evidence_zips)} evidence zips included)"
            )
        except Exception as e:
            logger.warning(f"Failed to attach evidence report: {e}")

    @staticmethod
    def _collect_allure_attachments(allure_data, allure_dir, allure_files):
        """Recursively collect attachment files referenced in allure result data."""
        # Top-level attachments
        for att in allure_data.get("attachments", []):
            source = att.get("source", "")
            if source:
                att_path = os.path.join(allure_dir, source)
                if os.path.isfile(att_path):
                    allure_files[f"allure-results/{source}"] = att_path

        # Step-level attachments (recursive for nested steps)
        for step in allure_data.get("steps", []):
            for att in step.get("attachments", []):
                source = att.get("source", "")
                if source:
                    att_path = os.path.join(allure_dir, source)
                    if os.path.isfile(att_path):
                        allure_files[f"allure-results/{source}"] = att_path
            # Recurse into nested steps
            KiwiReporter._collect_allure_attachments(
                step, allure_dir, allure_files
            )

    @staticmethod
    def _find_allure_result(allure_dir, nodeid):
        """Find the allure result JSON that matches the given pytest nodeid."""
        if not nodeid:
            return None

        # Convert nodeid to allure fullName format:
        #   "tests/ui/e_admin/test_connect.py::TestEAdminConnection::test_connect_and_load_dashboard"
        #   -> "tests.ui.e_admin.test_connect.TestEAdminConnection#test_connect_and_load_dashboard"
        parts = nodeid.replace("/", ".").replace("\\", ".")
        parts = parts.replace(".py::", ".").replace("::", "#", 1)

        for filename in os.listdir(allure_dir):
            if not filename.endswith("-result.json"):
                continue
            filepath = os.path.join(allure_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("fullName") == parts:
                    return data
            except (json.JSONDecodeError, OSError):
                continue

        return None

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
                                  duration=0, nodeid=None, evidence_dir=None):
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
            nodeid: pytest nodeid used to find allure results for attachment.
            evidence_dir: Path to the test's evidence directory (for zip attachments).
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
                # Attach evidence HTML + evidence zips from allure results
                self._attach_evidence_files(
                    execution_id, nodeid=nodeid, case_id=case_id,
                    evidence_dir=evidence_dir,
                )

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
        """Finalize and log summary. Restores original SSL context."""
        # Restore SSL verification disabled during connect()
        if self._ssl_cm is not None:
            self._ssl_cm.__exit__(None, None, None)
            self._ssl_cm = None

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


# ======================================================================
# HTML Evidence Report Builder (module-level helper)
# ======================================================================

def _esc(text):
    """HTML-escape a string."""
    return html_mod.escape(str(text)) if text else ""


def _format_duration_ms(start_ms, stop_ms):
    """Format millisecond timestamps to human-readable duration."""
    if not start_ms or not stop_ms:
        return ""
    delta_s = (stop_ms - start_ms) / 1000.0
    if delta_s < 1:
        return f"{delta_s * 1000:.0f}ms"
    return f"{delta_s:.2f}s"


def _build_allure_html(allure_data, allure_dir):
    """Build a self-contained HTML report from an allure result JSON.

    Embeds all screenshots as base64 data URIs so the HTML is fully
    standalone — viewable in any browser without external dependencies.
    """
    esc = _esc
    test_name = allure_data.get("name", "Unknown Test")
    full_name = allure_data.get("fullName", "")
    status = allure_data.get("status", "unknown")
    description = allure_data.get("description", "")
    duration = _format_duration_ms(
        allure_data.get("start"), allure_data.get("stop")
    )

    # Status badge color
    status_colors = {
        "passed": ("#c8e6c9", "#2e7d32"),
        "failed": ("#ffcdd2", "#c62828"),
        "broken": ("#ffe0b2", "#e65100"),
        "skipped": ("#e0e0e0", "#616161"),
    }
    bg, fg = status_colors.get(status, ("#e0e0e0", "#333"))

    # --- Build steps HTML ---
    steps_html = ""
    for i, step in enumerate(allure_data.get("steps", []), 1):
        s_status = step.get("status", "unknown")
        s_bg, s_fg = status_colors.get(s_status, ("#e0e0e0", "#333"))
        s_dur = _format_duration_ms(step.get("start"), step.get("stop"))

        attachments_html = ""
        for att in step.get("attachments", []):
            source = att.get("source", "")
            att_type = att.get("type", "")
            att_path = os.path.join(allure_dir, source)
            if att_type.startswith("image/") and os.path.isfile(att_path):
                with open(att_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("ascii")
                attachments_html += (
                    f'<img src="data:{att_type};base64,{b64}" '
                    f'alt="{esc(att.get("name", ""))}">'
                )
            elif att_type.startswith("text/") and os.path.isfile(att_path):
                with open(att_path, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()
                attachments_html += f'<pre class="att-text">{esc(text)}</pre>'

        steps_html += (
            '<div class="step">'
            f'<div class="step-header">'
            f'<span class="badge" style="background:{s_bg};color:{s_fg}">'
            f'{s_status.upper()}</span>'
            f'<strong>Step {i}: {esc(step.get("name", ""))}</strong>'
            f'<span class="dur">{s_dur}</span>'
            f'</div>'
            f'{attachments_html}'
            '</div>'
        )

    # --- Build top-level attachments (log, stdout) ---
    top_attachments_html = ""
    for att in allure_data.get("attachments", []):
        source = att.get("source", "")
        att_type = att.get("type", "")
        att_name = att.get("name", source)
        att_path = os.path.join(allure_dir, source)
        if att_type.startswith("text/") and os.path.isfile(att_path):
            with open(att_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            top_attachments_html += (
                f'<div class="log-block">'
                f'<h3>{esc(att_name)}</h3>'
                f'<pre>{esc(text)}</pre>'
                f'</div>'
            )

    # --- Labels ---
    labels = allure_data.get("labels", [])
    tags = [lb["value"] for lb in labels if lb.get("name") == "tag"]
    severity = next(
        (lb["value"] for lb in labels if lb.get("name") == "severity"), ""
    )
    suite = next(
        (lb["value"] for lb in labels if lb.get("name") == "suite"), ""
    )
    feature = next(
        (lb["value"] for lb in labels if lb.get("name") == "feature"), ""
    )

    meta_parts = []
    if suite:
        meta_parts.append(suite)
    if feature:
        meta_parts.append(feature)
    meta_parts.append(full_name)
    meta_line = " / ".join(meta_parts)

    tags_html = ""
    if tags:
        tags_html = " ".join(
            f'<span class="tag">{esc(t)}</span>' for t in tags
        )

    return (
        '<!DOCTYPE html>'
        '<html lang="en"><head><meta charset="UTF-8">'
        f'<title>{esc(test_name)}</title>'
        '<style>'
        '*{margin:0;padding:0;box-sizing:border-box}'
        'body{font-family:"Segoe UI",Tahoma,sans-serif;background:#f5f5f5;'
        'color:#333;padding:20px}'
        '.container{background:#fff;border-radius:8px;'
        'box-shadow:0 2px 8px rgba(0,0,0,.1);overflow:hidden;'
        'max-width:1000px;margin:0 auto}'
        '.header{background:#1a237e;color:#fff;padding:20px 24px}'
        '.header h1{font-size:18px;font-weight:600;margin-bottom:6px}'
        '.header .meta{font-size:12px;opacity:.8}'
        '.info{padding:16px 24px;display:flex;gap:16px;align-items:center;'
        'border-bottom:1px solid #eee;flex-wrap:wrap}'
        '.badge{display:inline-block;padding:4px 12px;border-radius:4px;'
        'font-size:12px;font-weight:700;text-transform:uppercase}'
        '.dur{font-size:12px;color:#888;margin-left:auto}'
        '.tag{display:inline-block;background:#e8eaf6;color:#3949ab;'
        'padding:2px 8px;border-radius:3px;font-size:11px;margin:2px}'
        '.section{padding:20px 24px;border-bottom:1px solid #eee}'
        '.section:last-child{border-bottom:none}'
        '.section h2{font-size:14px;color:#1a237e;margin-bottom:12px;'
        'text-transform:uppercase;letter-spacing:.5px}'
        'pre{background:#f8f9fa;border:1px solid #e0e0e0;border-radius:4px;'
        'padding:12px;font-size:11px;line-height:1.5;overflow-x:auto;'
        'white-space:pre-wrap;word-wrap:break-word}'
        '.step{margin-bottom:16px;border:1px solid #eee;border-radius:6px;'
        'overflow:hidden}'
        '.step-header{padding:10px 14px;background:#fafafa;display:flex;'
        'align-items:center;gap:10px}'
        '.step-header strong{font-size:13px}'
        '.step img{max-width:100%;display:block;padding:8px}'
        '.att-text{margin:0;border-radius:0;border:none;border-top:1px solid #eee}'
        '.log-block{margin-bottom:12px}'
        '.log-block h3{font-size:13px;color:#555;margin-bottom:6px}'
        '.desc{padding:16px 24px;border-bottom:1px solid #eee;'
        'font-size:13px;color:#555;line-height:1.6;white-space:pre-wrap}'
        '</style></head><body>'
        '<div class="container">'
        # -- Header --
        '<div class="header">'
        f'<h1>{esc(test_name)}</h1>'
        f'<div class="meta">{esc(meta_line)}</div>'
        '</div>'
        # -- Info bar --
        '<div class="info">'
        f'<span class="badge" style="background:{bg};color:{fg}">'
        f'{status.upper()}</span>'
        f'{f"<span class=badge style=background:#e8eaf6;color:#3949ab>{esc(severity)}</span>" if severity else ""}'
        f'<span class="dur">{duration}</span>'
        f'{tags_html}'
        '</div>'
        # -- Description --
        + (f'<div class="desc">{esc(description)}</div>' if description else '')
        +
        # -- Steps --
        '<div class="section">'
        f'<h2>Steps ({len(allure_data.get("steps", []))})</h2>'
        f'{steps_html if steps_html else "<p>No steps recorded</p>"}'
        '</div>'
        # -- Logs --
        + (
            '<div class="section"><h2>Logs</h2>'
            f'{top_attachments_html}</div>'
            if top_attachments_html else ''
        )
        +
        '</div></body></html>'
    )
