"""Exercise: Parallel Execution.

TODO: Verify parallel execution helpers work correctly.
"""

import os
from unittest.mock import patch

import pytest

from ankole.testing.parallel import (
    get_worker_id,
    is_xdist_worker,
    worker_port_offset,
    worker_safe_evidence_dir,
)


class TestParallelHelpers:
    """Parallel execution exercises."""

    def test_master_worker_id(self):
        """TODO: Verify master worker returns 'master'."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("PYTEST_XDIST_WORKER", None)
            assert get_worker_id() == "master"
            assert is_xdist_worker() is False

    def test_worker_port_offset_logic(self):
        """TODO: Verify port offsets are calculated correctly."""
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw0"}):
            assert worker_port_offset() == 1

        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw5"}):
            assert worker_port_offset() == 6

    def test_worker_safe_evidence_dir_isolation(self, tmp_path):
        """TODO: Verify workers get isolated evidence directories."""
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw2"}):
            result = worker_safe_evidence_dir(str(tmp_path / "evidence"))
            assert "worker_gw2" in result
            assert os.path.isdir(result)

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("PYTEST_XDIST_WORKER", None)
            result = worker_safe_evidence_dir(str(tmp_path / "evidence"))
            assert "worker_" not in result
