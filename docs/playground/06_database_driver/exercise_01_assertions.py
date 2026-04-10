"""Exercise: Database Assertions.

TODO: Use DBDriver to verify database state directly.
Requires DATABASE_URL env var to be set.
"""

import os
import pytest

from ankole.driver.db_driver import DBDriver


@pytest.fixture
def db():
    """Provide a DB driver with autorollback."""
    dsn = os.environ.get("DATABASE_URL", "")
    if not dsn:
        pytest.skip("DATABASE_URL not set")
    driver = DBDriver(dsn=dsn, autorollback=True)
    driver.connect()
    yield driver
    driver.close()


@pytest.mark.api
class TestDatabaseAssertions:
    """Database assertion exercises."""

    def test_admin_user_exists(self, db):
        """TODO: Assert the admin user exists in the members table."""
        db.assert_row_exists("members", {"username": "admin"})

    def test_member_count(self, db):
        """TODO: Count members and assert there is at least one."""
        count = db.row_count("members")
        assert count >= 1

    def test_admin_role_value(self, db):
        """TODO: Assert the admin user has role 'admin'."""
        db.assert_column_value(
            "members", "role", "admin",
            where={"username": "admin"},
        )

    def test_insert_with_autorollback(self, db):
        """TODO: Insert a row, verify it exists, and trust autorollback."""
        initial = db.row_count("members")
        db.execute(
            "INSERT INTO members (username, email, full_name, role) "
            "VALUES (%s, %s, %s, %s)",
            ("temp_pg_user", "temp@pg.com", "Temp PG", "member"),
        )
        assert db.row_count("members") == initial + 1
        # autorollback undoes this when db.close() is called
