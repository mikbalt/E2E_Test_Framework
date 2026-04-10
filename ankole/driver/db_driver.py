"""Database driver for direct DB assertions in E2E tests.

Wraps psycopg2 with assertion helpers for verifying database state::

    with DBDriver(dsn="postgresql://user:pass@localhost/db") as db:
        db.assert_row_exists("members", {"username": "admin"})
        db.assert_row_count("projects", 5, where={"status": "active"})
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class DBDriver:
    """PostgreSQL database driver with assertion helpers.

    Supports per-test autorollback: when enabled, wraps the session in a
    transaction that is rolled back on close, leaving the DB unchanged.
    """

    def __init__(
        self,
        dsn: str = "postgresql://localhost/test",
        autorollback: bool = False,
    ):
        self.dsn = dsn
        self.autorollback = autorollback
        self._conn = None
        self._cursor = None

    def connect(self) -> "DBDriver":
        """Open database connection."""
        import psycopg2

        self._conn = psycopg2.connect(self.dsn)
        if self.autorollback:
            self._conn.autocommit = False
        else:
            self._conn.autocommit = True
        self._cursor = self._conn.cursor()
        logger.info(f"DBDriver connected (autorollback={self.autorollback})")
        return self

    def close(self) -> None:
        """Close database connection, rolling back if autorollback is enabled."""
        if self._conn:
            if self.autorollback:
                self._conn.rollback()
                logger.info("DBDriver: transaction rolled back (autorollback)")
            if self._cursor:
                self._cursor.close()
            self._conn.close()
            logger.info("DBDriver closed")
        self._conn = None
        self._cursor = None

    def __enter__(self) -> "DBDriver":
        return self.connect()

    def __exit__(self, *args) -> None:
        self.close()

    # -- Query methods --------------------------------------------------------

    def execute(self, query: str, params: tuple | None = None) -> "DBDriver":
        """Execute a SQL query."""
        self._cursor.execute(query, params)
        logger.debug(f"Executed: {query[:100]}")
        return self

    def fetchone(self) -> tuple | None:
        """Fetch one row from the last query."""
        return self._cursor.fetchone()

    def fetchall(self) -> list[tuple]:
        """Fetch all rows from the last query."""
        return self._cursor.fetchall()

    def execute_scalar(self, query: str, params: tuple | None = None) -> Any:
        """Execute a query and return the first column of the first row."""
        self.execute(query, params)
        row = self.fetchone()
        return row[0] if row else None

    def row_count(self, table: str, where: dict[str, Any] | None = None) -> int:
        """Count rows in a table, optionally filtered by WHERE conditions."""
        if where:
            conditions = " AND ".join(f"{k} = %s" for k in where)
            query = f"SELECT COUNT(*) FROM {table} WHERE {conditions}"
            params = tuple(where.values())
        else:
            query = f"SELECT COUNT(*) FROM {table}"
            params = None
        return self.execute_scalar(query, params)

    # -- Assertion methods ----------------------------------------------------

    def assert_row_exists(
        self, table: str, where: dict[str, Any], msg: str | None = None,
    ) -> "DBDriver":
        """Assert that at least one row matches the conditions."""
        count = self.row_count(table, where)
        if count == 0:
            error = msg or f"Expected row in '{table}' matching {where}, found none"
            raise AssertionError(error)
        logger.debug(f"assert_row_exists: {table} {where} -> {count} rows")
        return self

    def assert_row_not_exists(
        self, table: str, where: dict[str, Any], msg: str | None = None,
    ) -> "DBDriver":
        """Assert that no rows match the conditions."""
        count = self.row_count(table, where)
        if count > 0:
            error = msg or f"Expected no rows in '{table}' matching {where}, found {count}"
            raise AssertionError(error)
        return self

    def assert_row_count(
        self, table: str, expected: int, where: dict[str, Any] | None = None,
        msg: str | None = None,
    ) -> "DBDriver":
        """Assert exact row count in a table."""
        actual = self.row_count(table, where)
        if actual != expected:
            error = msg or (
                f"Expected {expected} rows in '{table}'"
                f"{' matching ' + str(where) if where else ''}, got {actual}"
            )
            raise AssertionError(error)
        return self

    def assert_column_value(
        self, table: str, column: str, expected: Any,
        where: dict[str, Any] | None = None, msg: str | None = None,
    ) -> "DBDriver":
        """Assert that a column has the expected value for matching rows."""
        if where:
            conditions = " AND ".join(f"{k} = %s" for k in where)
            query = f"SELECT {column} FROM {table} WHERE {conditions} LIMIT 1"
            params = tuple(where.values())
        else:
            query = f"SELECT {column} FROM {table} LIMIT 1"
            params = None

        self.execute(query, params)
        row = self.fetchone()
        if row is None:
            raise AssertionError(
                msg or f"No rows found in '{table}'"
                f"{' matching ' + str(where) if where else ''}"
            )
        actual = row[0]
        if actual != expected:
            raise AssertionError(
                msg or f"Expected {column}={expected!r} in '{table}', got {actual!r}"
            )
        return self
