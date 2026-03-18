"""
Flow Orchestration Layer — composable, reusable test flows.

Provides a thin layer above page objects:
- FlowContext: shared state (driver, evidence, test data) passed between steps
- Step: single named action, auto-wrapped in tracked_step for Allure + screenshot
- Flow: ordered sequence of steps with composition via ``+``
- FlowResult: summary of a flow execution (steps run, failures, etc.)

Usage::

    from sphere_e2e_test_framework.flows.base import FlowContext, Step, Flow

    ctx = FlowContext(driver, evidence, td)
    flow = Flow("My Flow", [
        Step("Connect", lambda ctx: ...),
        Step("Login", lambda ctx: ..., retries=2, retry_delay=0.5),
    ])
    flow.run(ctx)
"""

import logging
import time
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@contextmanager
def _allure_step(label):
    """Allure step grouping only — no screenshots, no COM calls."""
    try:
        import allure
        with allure.step(label):
            yield
    except ImportError:
        yield


@dataclass
class FlowContext:
    """Shared state passed between steps.

    Attributes:
        driver: UIDriver instance.
        evidence: Evidence instance for screenshots/logging.
        td: Test data dataclass (e.g. DeleteOperationUserData).
        state: Arbitrary dict for inter-step communication.
    """

    driver: Any
    evidence: Any
    td: Any
    state: dict = field(default_factory=dict)

    @property
    def page(self):
        """Shortcut for the current page object stored in state."""
        return self.state.get("page")

    @page.setter
    def page(self, value):
        self.state["page"] = value

    def get(self, key, default=None):
        """Read a value from state."""
        return self.state.get(key, default)

    def set(self, key, value):
        """Store a value in state."""
        self.state[key] = value


@dataclass
class Step:
    """Single named action that wraps in tracked_step for Allure + screenshot.

    Args:
        name: Human-readable step description (appears in Allure).
        action: Callable(FlowContext) that performs the step.
        when: Optional predicate Callable(FlowContext) -> bool.
            If provided and returns False, the step is skipped.
        retries: Number of retry attempts (0 = no retry, backward compat).
        retry_delay: Base delay in seconds between retries (exponential backoff).
        on_failure: Optional callback(ctx, exception) called on final failure.
            Does NOT suppress the exception — cleanup/logging only.
    """

    name: str
    action: Callable
    when: Optional[Callable] = None
    retries: int = 0
    retry_delay: float = 1.0
    on_failure: Optional[Callable] = None

    def execute(self, ctx: FlowContext):
        """Run the step action, wrapped in an Allure step group.

        Uses ``allure.step()`` for report grouping only — no extra
        screenshots or COM calls. The inner page-object methods and
        ``tracked_step`` calls inside the action provide evidence.

        Retries up to ``self.retries`` additional times on failure with
        exponential backoff. Each attempt is individually tracked in Allure.
        On final failure, calls ``on_failure(ctx, error)`` if provided,
        then re-raises.
        """
        if self.when is not None and not self.when(ctx):
            logger.info(f"Step skipped (condition not met): {self.name}")
            return

        max_attempts = 1 + self.retries
        last_error = None

        for attempt in range(max_attempts):
            try:
                step_label = self.name
                if attempt > 0:
                    step_label = f"{self.name} (retry {attempt}/{self.retries})"

                logger.info(f"Step: {step_label}")
                with _allure_step(step_label):
                    self.action(ctx)
                return  # success
            except Exception as e:
                last_error = e
                if attempt < max_attempts - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Step '{self.name}' failed (attempt {attempt + 1}/{max_attempts}), "
                        f"retrying in {delay:.1f}s: {e}"
                    )
                    time.sleep(delay)

        # All attempts exhausted
        if self.on_failure is not None:
            try:
                self.on_failure(ctx, last_error)
            except Exception as cb_err:
                logger.warning(f"on_failure callback error for '{self.name}': {cb_err}")

        raise last_error


@dataclass
class FlowResult:
    """Summary of a flow execution."""

    flow_name: str
    steps_run: int = 0
    steps_passed: int = 0
    steps_failed: int = 0
    failures: list = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.steps_failed == 0


class Flow:
    """Ordered sequence of Steps with error handling and composition.

    Usage::

        flow_a = Flow("Login", [step1, step2])
        flow_b = Flow("Create User", [step3, step4])
        combined = flow_a + flow_b  # new Flow with all steps
        combined.run(ctx)

    Args:
        name: Human-readable flow name.
        steps: Ordered list of Step instances.
        cleanup_steps: Steps that always run (finally block), regardless of failures.
        continue_on_failure: If True, continue executing remaining steps after a failure.
    """

    def __init__(
        self,
        name: str,
        steps: list[Step],
        cleanup_steps: list[Step] | None = None,
        continue_on_failure: bool = False,
    ):
        self.name = name
        self.steps = list(steps)
        self.cleanup_steps = list(cleanup_steps or [])
        self.continue_on_failure = continue_on_failure

    def run(self, ctx: FlowContext) -> FlowContext:
        """Execute all steps in order. Returns the context.

        If ``continue_on_failure`` is True, step failures are recorded but
        do not abort the flow. ``cleanup_steps`` always execute in a finally
        block. The FlowResult is stored in ``ctx.state["_flow_result"]``.
        """
        result = FlowResult(flow_name=self.name)
        first_error = None

        logger.info(f"Flow started: {self.name}")
        try:
            for step in self.steps:
                result.steps_run += 1
                try:
                    step.execute(ctx)
                    result.steps_passed += 1
                except Exception as e:
                    result.steps_failed += 1
                    result.failures.append({"step": step.name, "error": str(e)})
                    if first_error is None:
                        first_error = e
                    if not self.continue_on_failure:
                        raise
        finally:
            # Always run cleanup steps
            for step in self.cleanup_steps:
                try:
                    step.execute(ctx)
                except Exception as e:
                    logger.warning(f"Cleanup step '{step.name}' failed: {e}")

            ctx.state["_flow_result"] = result

        if self.continue_on_failure and first_error is not None:
            logger.warning(
                f"Flow '{self.name}' completed with {result.steps_failed} failure(s)"
            )
        else:
            logger.info(f"Flow completed: {self.name}")

        return ctx

    def __add__(self, other: "Flow") -> "Flow":
        """Compose two flows into a new Flow."""
        return Flow(
            f"{self.name} + {other.name}",
            self.steps + other.steps,
            cleanup_steps=self.cleanup_steps + other.cleanup_steps,
        )

    def __repr__(self):
        return f"Flow({self.name!r}, {len(self.steps)} steps)"
