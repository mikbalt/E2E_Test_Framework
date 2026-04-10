"""Solution: Parallel Execution."""

import os
from unittest.mock import patch

from ankole.testing.parallel import (
    get_worker_id,
    is_xdist_worker,
    worker_port_offset,
    worker_safe_evidence_dir,
)


class TestParallelSolution:
    def test_master(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("PYTEST_XDIST_WORKER", None)
            assert get_worker_id() == "master"

    def test_port_offset(self):
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw3"}):
            assert worker_port_offset() == 4

    def test_evidence_isolation(self, tmp_path):
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw1"}):
            assert "worker_gw1" in worker_safe_evidence_dir(str(tmp_path))
