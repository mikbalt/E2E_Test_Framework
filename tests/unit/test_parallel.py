"""Unit tests for Parallel Execution module."""

import os
from unittest.mock import patch

from ankole.testing.parallel import (
    get_worker_id,
    is_xdist_worker,
    worker_port_offset,
    worker_safe_evidence_dir,
)


class TestParallel:
    """Tests for parallel execution helpers."""

    def test_get_worker_id_master(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove PYTEST_XDIST_WORKER if present
            os.environ.pop("PYTEST_XDIST_WORKER", None)
            assert get_worker_id() == "master"

    def test_get_worker_id_worker(self):
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw2"}):
            assert get_worker_id() == "gw2"

    def test_is_xdist_worker_false(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("PYTEST_XDIST_WORKER", None)
            assert is_xdist_worker() is False

    def test_is_xdist_worker_true(self):
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw0"}):
            assert is_xdist_worker() is True

    def test_worker_port_offset_master(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("PYTEST_XDIST_WORKER", None)
            assert worker_port_offset() == 0

    def test_worker_port_offset_gw0(self):
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw0"}):
            assert worker_port_offset() == 1

    def test_worker_port_offset_gw3(self):
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw3"}):
            assert worker_port_offset() == 4

    def test_worker_safe_evidence_dir_master(self, tmp_path):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("PYTEST_XDIST_WORKER", None)
            result = worker_safe_evidence_dir(str(tmp_path / "evidence"))
            assert result == str(tmp_path / "evidence")

    def test_worker_safe_evidence_dir_worker(self, tmp_path):
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw1"}):
            result = worker_safe_evidence_dir(str(tmp_path / "evidence"))
            assert "worker_gw1" in result
            assert os.path.isdir(result)
