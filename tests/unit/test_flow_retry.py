"""Phase 3 verification: Flow retry mechanism.

Tests Step retry, on_failure callback, Flow cleanup_steps,
continue_on_failure, FlowResult, and backward compatibility.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from ankole.flows.base import (
    FlowContext,
    Step,
    Flow,
    FlowResult,
)


def _make_ctx():
    """Create a minimal FlowContext with mocked driver/evidence."""
    ctx = FlowContext(
        driver=MagicMock(),
        evidence=MagicMock(),
        td=None,
    )
    ctx.evidence.step_count = 0
    return ctx


# =========================================================================
# Step Retry Tests
# =========================================================================


class TestStepRetry:
    """Verify Step retry mechanism."""

    def test_no_retry_default(self):
        """Default retries=0: step runs once, no retry."""
        calls = []
        step = Step("test", lambda ctx: calls.append(1))
        step.execute(_make_ctx())
        assert len(calls) == 1

    def test_success_no_retry_needed(self):
        """Step succeeds on first try — no retries triggered."""
        calls = []
        step = Step("test", lambda ctx: calls.append(1), retries=3)
        step.execute(_make_ctx())
        assert len(calls) == 1

    def test_retry_succeeds_on_third_attempt(self):
        """Step fails twice, succeeds on third — should not raise."""
        attempts = []

        def flaky(ctx):
            attempts.append(1)
            if len(attempts) < 3:
                raise RuntimeError("transient")

        step = Step("flaky", flaky, retries=3, retry_delay=0.01)
        step.execute(_make_ctx())
        assert len(attempts) == 3

    def test_retry_all_exhausted_raises(self):
        """All retry attempts fail — should raise the last error."""
        attempts = []

        def always_fail(ctx):
            attempts.append(1)
            raise RuntimeError(f"fail #{len(attempts)}")

        step = Step("fail", always_fail, retries=2, retry_delay=0.01)
        with pytest.raises(RuntimeError, match="fail #3"):
            step.execute(_make_ctx())
        assert len(attempts) == 3  # 1 initial + 2 retries

    def test_exponential_backoff_timing(self):
        """Verify delays increase exponentially between retries."""
        timestamps = []

        def record_time(ctx):
            timestamps.append(time.monotonic())
            if len(timestamps) < 3:
                raise RuntimeError("retry me")

        step = Step("timed", record_time, retries=2, retry_delay=0.1)
        step.execute(_make_ctx())

        # gap between attempt 1→2 should be ~0.1s (0.1 * 2^0)
        # gap between attempt 2→3 should be ~0.2s (0.1 * 2^1)
        gap1 = timestamps[1] - timestamps[0]
        gap2 = timestamps[2] - timestamps[1]
        assert gap1 >= 0.08, f"First gap too short: {gap1:.3f}s"
        assert gap2 >= 0.15, f"Second gap too short: {gap2:.3f}s"
        assert gap2 > gap1, "Backoff should be exponential"

    def test_when_condition_skips_step(self):
        """Step with when=False should not execute or retry."""
        calls = []
        step = Step(
            "skip me",
            lambda ctx: calls.append(1),
            when=lambda ctx: False,
            retries=3,
        )
        step.execute(_make_ctx())
        assert len(calls) == 0


# =========================================================================
# on_failure Callback Tests
# =========================================================================


class TestStepOnFailure:
    """Verify on_failure callback behavior."""

    def test_on_failure_called_after_exhaustion(self):
        """on_failure is called when all retries are exhausted."""
        callback_args = []

        def my_callback(ctx, err):
            callback_args.append(str(err))

        def always_fail(ctx):
            raise RuntimeError("permanent")

        step = Step(
            "fail", always_fail,
            retries=1, retry_delay=0.01,
            on_failure=my_callback,
        )

        with pytest.raises(RuntimeError):
            step.execute(_make_ctx())

        assert len(callback_args) == 1
        assert "permanent" in callback_args[0]

    def test_on_failure_not_called_on_success(self):
        """on_failure should NOT be called when step succeeds."""
        callback_args = []

        step = Step(
            "ok", lambda ctx: None,
            on_failure=lambda ctx, err: callback_args.append(1),
        )
        step.execute(_make_ctx())
        assert len(callback_args) == 0

    def test_on_failure_does_not_suppress_exception(self):
        """on_failure is for cleanup only — the original exception still raises."""
        step = Step(
            "fail", lambda ctx: (_ for _ in ()).throw(ValueError("original")),
            retries=0,
            on_failure=lambda ctx, err: None,
        )
        with pytest.raises(ValueError, match="original"):
            step.execute(_make_ctx())

    def test_on_failure_callback_error_does_not_mask(self):
        """If on_failure itself raises, the original error should still propagate."""

        def bad_callback(ctx, err):
            raise RuntimeError("callback crashed")

        step = Step(
            "fail", lambda ctx: (_ for _ in ()).throw(ValueError("original")),
            retries=0,
            on_failure=bad_callback,
        )
        with pytest.raises(ValueError, match="original"):
            step.execute(_make_ctx())


# =========================================================================
# FlowResult Tests
# =========================================================================


class TestFlowResult:
    """Verify FlowResult dataclass."""

    def test_success_when_no_failures(self):
        r = FlowResult(flow_name="test", steps_run=5, steps_passed=5)
        assert r.success is True

    def test_failure_when_has_failures(self):
        r = FlowResult(flow_name="test", steps_run=5, steps_passed=3, steps_failed=2)
        assert r.success is False

    def test_default_values(self):
        r = FlowResult(flow_name="test")
        assert r.steps_run == 0
        assert r.steps_passed == 0
        assert r.steps_failed == 0
        assert r.failures == []
        assert r.success is True


# =========================================================================
# Flow Cleanup & Continue-on-failure Tests
# =========================================================================


class TestFlowCleanup:
    """Verify Flow cleanup_steps behavior."""

    def test_cleanup_runs_on_success(self):
        """Cleanup steps run even when all steps succeed."""
        cleanup_called = []

        flow = Flow(
            "test",
            [Step("ok", lambda ctx: None)],
            cleanup_steps=[Step("cleanup", lambda ctx: cleanup_called.append(1))],
        )
        flow.run(_make_ctx())
        assert len(cleanup_called) == 1

    def test_cleanup_runs_on_failure(self):
        """Cleanup steps run even when a step fails."""
        cleanup_called = []

        flow = Flow(
            "test",
            [Step("fail", lambda ctx: (_ for _ in ()).throw(RuntimeError("boom")))],
            cleanup_steps=[Step("cleanup", lambda ctx: cleanup_called.append(1))],
        )

        with pytest.raises(RuntimeError, match="boom"):
            flow.run(_make_ctx())

        assert len(cleanup_called) == 1

    def test_cleanup_failure_does_not_mask_step_failure(self):
        """If cleanup itself fails, the original step error still propagates."""
        flow = Flow(
            "test",
            [Step("fail", lambda ctx: (_ for _ in ()).throw(RuntimeError("step error")))],
            cleanup_steps=[
                Step("bad cleanup", lambda ctx: (_ for _ in ()).throw(RuntimeError("cleanup error")))
            ],
        )

        with pytest.raises(RuntimeError, match="step error"):
            flow.run(_make_ctx())


class TestFlowContinueOnFailure:
    """Verify continue_on_failure behavior."""

    def test_continue_on_failure_runs_all_steps(self):
        """When continue_on_failure=True, all steps run despite failures."""
        execution_order = []

        flow = Flow(
            "test",
            [
                Step("step1", lambda ctx: execution_order.append(1)),
                Step("step2", lambda ctx: (_ for _ in ()).throw(RuntimeError("fail"))),
                Step("step3", lambda ctx: execution_order.append(3)),
            ],
            continue_on_failure=True,
        )
        flow.run(_make_ctx())
        assert execution_order == [1, 3]

    def test_continue_on_failure_records_result(self):
        """FlowResult should record failures when continuing."""
        ctx = _make_ctx()

        flow = Flow(
            "test",
            [
                Step("ok1", lambda ctx: None),
                Step("fail1", lambda ctx: (_ for _ in ()).throw(RuntimeError("err1"))),
                Step("ok2", lambda ctx: None),
            ],
            continue_on_failure=True,
        )
        flow.run(ctx)

        result = ctx.state["_flow_result"]
        assert isinstance(result, FlowResult)
        assert result.steps_run == 3
        assert result.steps_passed == 2
        assert result.steps_failed == 1
        assert len(result.failures) == 1
        assert result.failures[0]["step"] == "fail1"

    def test_default_stops_on_first_failure(self):
        """Default behavior (continue_on_failure=False): stop on first failure."""
        execution_order = []

        flow = Flow(
            "test",
            [
                Step("step1", lambda ctx: execution_order.append(1)),
                Step("step2", lambda ctx: (_ for _ in ()).throw(RuntimeError("fail"))),
                Step("step3", lambda ctx: execution_order.append(3)),
            ],
        )

        with pytest.raises(RuntimeError):
            flow.run(_make_ctx())

        assert execution_order == [1]  # step3 never ran


class TestFlowComposition:
    """Verify Flow.__add__ merges cleanup_steps."""

    def test_add_merges_cleanup(self):
        flow_a = Flow(
            "A", [Step("a1", lambda ctx: None)],
            cleanup_steps=[Step("cleanup_a", lambda ctx: None)],
        )
        flow_b = Flow(
            "B", [Step("b1", lambda ctx: None)],
            cleanup_steps=[Step("cleanup_b", lambda ctx: None)],
        )

        combined = flow_a + flow_b
        assert len(combined.steps) == 2
        assert len(combined.cleanup_steps) == 2
        assert combined.steps[0].name == "a1"
        assert combined.steps[1].name == "b1"
        assert combined.cleanup_steps[0].name == "cleanup_a"
        assert combined.cleanup_steps[1].name == "cleanup_b"

    def test_flow_result_stored_in_context(self):
        """FlowResult should be accessible via ctx.state after run()."""
        ctx = _make_ctx()
        flow = Flow("test", [Step("ok", lambda ctx: None)])
        flow.run(ctx)

        result = ctx.state["_flow_result"]
        assert result.flow_name == "test"
        assert result.success is True


# =========================================================================
# Backward Compatibility
# =========================================================================


class TestBackwardCompat:
    """Ensure default parameters preserve existing behavior."""

    def test_step_defaults_no_retry(self):
        step = Step("test", lambda ctx: None)
        assert step.retries == 0
        assert step.retry_delay == 1.0
        assert step.on_failure is None

    def test_flow_defaults_no_cleanup_no_continue(self):
        flow = Flow("test", [])
        assert flow.cleanup_steps == []
        assert flow.continue_on_failure is False

    def test_flow_run_returns_context(self):
        ctx = _make_ctx()
        result = Flow("test", [Step("ok", lambda ctx: None)]).run(ctx)
        assert result is ctx
