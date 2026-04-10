"""Exercise 01: Your First Ankole Test.

TODO: Complete the test functions below.
Run: pytest docs/playground/01_getting_started/exercise_01_first_test.py -v
"""

import os
import pytest


class TestFirstSteps:
    """Your first Ankole Framework tests."""

    def test_config_is_loaded(self, config):
        """TODO: Assert that `config` is a dict and is not empty."""
        # Hint: config is injected by the Ankole plugin fixture
        assert isinstance(config, dict)
        # TODO: Add an assertion that config has at least one key
        assert len(config) > 0

    def test_evidence_directory_created(self, evidence):
        """TODO: Assert that the evidence directory was created."""
        # Hint: evidence.evidence_dir is the path to the test's evidence folder
        assert os.path.isdir(evidence.evidence_dir)

    def test_evidence_step_tracking(self, evidence):
        """TODO: Add two steps and verify the step count."""
        evidence.step("First step")
        evidence.step("Second step")
        assert evidence.step_count == 2
