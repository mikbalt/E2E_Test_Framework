"""Kiwi TCMS integration helpers for pytest plugin."""

import logging

logger = logging.getLogger(__name__)


def _filter_by_kiwi_run(config, items, kiwi_cases):
    """
    Filter test items to only those matching Kiwi TestRun cases.

    Matching strategy:
        Only @pytest.mark.tcms(case_id=X) is used for matching.
        Name-based matching is intentionally not supported because TCMS
        summaries use bracket-tag format (e.g. "[E2E][PKCS11][Sign] ...")
        which never matches Python function names.

    After matching, two types of gaps are detected and reported:
        - Unmatched TCMS cases: cases in the TestRun with no automation test
        - Unmatched Python tests: tests with @pytest.mark.tcms pointing to
          case IDs not present in the TestRun (deselected)
    """
    case_ids = {c["id"]: c for c in kiwi_cases}
    matched_case_ids = set()

    selected = []
    deselected = []

    for item in items:
        matched = False

        tcms_marker = item.get_closest_marker("tcms")
        if tcms_marker:
            marker_case_id = tcms_marker.kwargs.get("case_id")
            if marker_case_id and marker_case_id in case_ids:
                item._kiwi_case = case_ids[marker_case_id]
                matched_case_ids.add(marker_case_id)
                matched = True

        if matched:
            selected.append(item)
        else:
            deselected.append(item)

    # --- Detect unmatched TCMS cases (no automation test exists) ---
    unmatched_cases = [c for c in kiwi_cases if c["id"] not in matched_case_ids]
    config._kiwi_unmatched_cases = unmatched_cases

    if unmatched_cases:
        logger.warning("=" * 60)
        logger.warning(
            f"TCMS COVERAGE GAP: {len(unmatched_cases)} test case(s) in "
            f"TestRun have no matching automation test"
        )
        for case in unmatched_cases:
            logger.warning(f"  - Case #{case['id']}: {case['summary']}")
        logger.warning(
            "Add @pytest.mark.tcms(case_id=X) to a Python test to link it."
        )
        logger.warning("=" * 60)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected

    logger.info(
        f"Kiwi filter: {len(selected)} matched, "
        f"{len(deselected)} deselected, "
        f"{len(unmatched_cases)} TCMS cases without automation"
    )


def _push_to_kiwi(results, cfg, config=None):
    """Push results to Kiwi TCMS if enabled."""
    # Bidirectional mode: use the reporter initialized during configure
    bidir_reporter = getattr(config, "_kiwi_reporter", None) if config else None

    if bidir_reporter:
        _push_to_kiwi_bidirectional(results, bidir_reporter, config=config)
        return

    # Standard push-only mode
    tcms_config = cfg.get("kiwi_tcms", {})
    if not tcms_config.get("enabled"):
        return

    try:
        from sphere_e2e_test_framework.driver.kiwi_tcms import KiwiReporter

        reporter = KiwiReporter(
            url=tcms_config.get("url"),
            plan_id=tcms_config.get("plan_id"),
            build_id=tcms_config.get("build_id"),
            status_ids=tcms_config.get("status_ids"),
        )

        if not reporter.connect():
            return

        if tcms_config.get("auto_create_run"):
            reporter.create_test_run()

        for result in results:
            reporter.report_result(
                test_name=result["name"],
                status=result["status"],
                comment=result.get("error", ""),
                duration=result.get("duration", 0),
                evidence_dir=result.get("evidence_dir"),
            )

        reporter.finalize()
    except Exception as e:
        logger.warning(f"Kiwi TCMS reporting failed: {e}")


def _push_to_kiwi_bidirectional(results, reporter, config=None):
    """Push results to an existing Kiwi TestRun (bidirectional mode).

    Three actions:
    1. Push PASSED/FAILED for matched (executed) tests.
    2. Mark unmatched TCMS cases as BLOCKED with explanation.
    3. Log a summary of matched vs unmatched.
    """
    try:
        # 1. Report executed test results
        for result in results:
            case_id = result.get("_kiwi_case_id")
            if case_id:
                reporter.report_result_by_case_id(
                    case_id=case_id,
                    status=result["status"],
                    comment=result.get("error", ""),
                    duration=result.get("duration", 0),
                    nodeid=result.get("nodeid"),
                    evidence_dir=result.get("evidence_dir"),
                )

        # 2. Mark unmatched TCMS cases as BLOCKED
        unmatched = getattr(config, "_kiwi_unmatched_cases", []) if config else []
        if unmatched:
            reporter.mark_unmatched_as_blocked(unmatched)

        # 3. Summary
        executed = sum(1 for r in results if r.get("_kiwi_case_id"))
        reporter.finalize()

        logger.info("=" * 60)
        logger.info("Kiwi TCMS Bidirectional Summary")
        logger.info(f"  Executed (matched):  {executed}")
        logger.info(f"  No automation test:  {len(unmatched)}")
        if unmatched:
            for case in unmatched:
                logger.info(f"    BLOCKED  Case #{case['id']}: {case['summary']}")
        logger.info("=" * 60)

    except Exception as e:
        logger.warning(f"Kiwi TCMS bidirectional reporting failed: {e}")
