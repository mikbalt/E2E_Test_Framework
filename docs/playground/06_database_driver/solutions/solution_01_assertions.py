"""Solution: Database Assertions."""

import os
import pytest
from ankole.driver.db_driver import DBDriver


@pytest.fixture
def db():
    dsn = os.environ.get("DATABASE_URL", "")
    if not dsn:
        pytest.skip("DATABASE_URL not set")
    driver = DBDriver(dsn=dsn, autorollback=True)
    driver.connect()
    yield driver
    driver.close()


@pytest.mark.api
class TestDatabaseAssertionsSolution:
    def test_admin_exists(self, db):
        db.assert_row_exists("members", {"username": "admin"})

    def test_count(self, db):
        assert db.row_count("members") >= 1

    def test_role(self, db):
        db.assert_column_value("members", "role", "admin", where={"username": "admin"})
