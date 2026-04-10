"""Prometheus/Grafana metrics push for pytest plugin."""

import logging

logger = logging.getLogger(__name__)


def _push_metrics(results, session_duration, cfg, config=None):
    """Push metrics to Prometheus/Grafana if enabled."""
    metrics_config = cfg.get("metrics", {})
    if not metrics_config.get("enabled"):
        return

    try:
        from ankole.driver.grafana_push import MetricsPusher

        run_id = getattr(config, "_run_id", None) if config else None
        pusher = MetricsPusher(
            pushgateway_url=metrics_config.get("pushgateway_url"),
            job_name=metrics_config.get("job_name", "e2e_tests"),
            labels=metrics_config.get("labels", {}),
            run_id=run_id,
            metric_prefix=metrics_config.get("metric_prefix", "e2e"),
        )

        total = len(results)
        passed = sum(1 for r in results if r["status"] == "PASSED")

        # Count blocked cases from Kiwi bidirectional mode
        blocked = 0
        if config:
            unmatched = getattr(config, "_kiwi_unmatched_cases", [])
            blocked = len(unmatched)

        suite_name = metrics_config.get("suite_name", "default")

        for result in results:
            pusher.record_test(
                test_name=result["name"],
                passed=(result["status"] == "PASSED"),
                duration=result.get("duration", 0),
                suite=suite_name,
            )

        pusher.record_suite(suite_name, total, passed, session_duration,
                            blocked=blocked)
        pusher.push()
    except Exception as e:
        logger.warning(f"Metrics push failed: {e}")
