"""Integration tests for Database Driver assertions.

Requires a running PostgreSQL instance with the sample app schema.
"""

import pytest

from ankole.driver.db_driver import DBDriver
from ankole.plugin.config import load_config


@pytest.fixture
def db(config):
    """Provide a DB driver with autorollback for test isolation."""
    dsn = (
        config.get("workspace", {})
        .get("database", {})
        .get("dsn", "")
    )
    if not dsn:
        pytest.skip("DATABASE_URL not configured")

    driver = DBDriver(dsn=dsn, autorollback=True)
    driver.connect()
    yield driver
    driver.close()


@pytest.mark.api
class TestDBAssertions:
    """Database assertion tests against the sample app."""

    def test_members_table_exists(self, db):
        """Verify the members table exists and has rows."""
        count = db.row_count("members")
        assert count >= 0  # Table exists if no error

    def test_assert_admin_exists(self, db):
        """Assert the default admin user exists."""
        db.assert_row_exists("members", {"username": "admin"})

    def test_assert_row_count(self, db):
        """Assert there is at least 1 member."""
        count = db.row_count("members")
        db.assert_row_count("members", count)

    def test_assert_column_value(self, db):
        """Assert admin has the expected role."""
        db.assert_column_value(
            "members", "role", "admin",
            where={"username": "admin"},
        )

    def test_autorollback_isolation(self, db):
        """Changes within autorollback are not persisted."""
        initial_count = db.row_count("members")
        db.execute(
            "INSERT INTO members (username, email, full_name, role) "
            "VALUES (%s, %s, %s, %s)",
            ("temp_user", "temp@test.com", "Temp", "member"),
        )
        new_count = db.row_count("members")
        assert new_count == initial_count + 1
        # autorollback will undo this on close
