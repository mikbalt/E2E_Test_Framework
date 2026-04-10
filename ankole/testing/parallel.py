"""Parallel execution helpers for pytest-xdist compatibility.

Provides worker-aware utilities for safe parallel test execution::

    from ankole.testing.parallel import get_worker_id, worker_port_offset

    worker = get_worker_id()
    port = 5000 + worker_port_offset()
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def get_worker_id() -> str:
    """Get the current pytest-xdist worker ID.

    Returns:
        Worker ID string (e.g., "gw0", "gw1") or "master" if not running
        under xdist.
    """
    return os.environ.get("PYTEST_XDIST_WORKER", "master")


def is_xdist_worker() -> bool:
    """Check if running as a pytest-xdist worker."""
    return get_worker_id() != "master"


def worker_port_offset() -> int:
    """Get a numeric port offset based on worker ID.

    Returns:
        0 for master, 1 for gw0, 2 for gw1, etc.
    """
    worker_id = get_worker_id()
    if worker_id == "master":
        return 0
    try:
        return int(worker_id.replace("gw", "")) + 1
    except (ValueError, AttributeError):
        return 0


def worker_safe_evidence_dir(base_dir: str = "evidence") -> str:
    """Get a worker-specific evidence directory.

    Args:
        base_dir: Base evidence directory path.

    Returns:
        Worker-isolated evidence directory path.
    """
    worker_id = get_worker_id()
    if worker_id == "master":
        return base_dir
    safe_dir = os.path.join(base_dir, f"worker_{worker_id}")
    os.makedirs(safe_dir, exist_ok=True)
    return safe_dir
