"""Unit tests for the Database Driver module."""

from unittest.mock import MagicMock, patch

import pytest


class TestDBDriverUnit:
    """Tests for DBDriver (mocked psycopg2)."""

    def _make_driver(self):
        from ankole.driver.db_driver import DBDriver
        return DBDriver(dsn="postgresql://test:test@localhost/test")

    @patch("ankole.driver.db_driver.psycopg2", create=True)
    def test_connect_and_close(self, mock_psycopg2):
        """Test connect/close lifecycle."""
        import importlib
        import ankole.driver.db_driver as mod
        # Inject mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        with patch.dict("sys.modules", {"psycopg2": MagicMock()}):
            driver = self._make_driver()
            with patch("ankole.driver.db_driver.DBDriver.connect") as mock_connect:
                mock_connect.return_value = driver
                driver._conn = mock_conn
                driver._cursor = mock_cursor
                driver.close()
                mock_conn.close.assert_called_once()

    def test_assert_row_exists_raises_on_zero(self):
        """assert_row_exists raises when count is 0."""
        driver = self._make_driver()
        driver._conn = MagicMock()
        driver._cursor = MagicMock()
        driver._cursor.fetchone.return_value = (0,)

        with pytest.raises(AssertionError, match="Expected row"):
            driver.assert_row_exists("members", {"username": "nobody"})

    def test_assert_row_exists_passes(self):
        """assert_row_exists passes when count > 0."""
        driver = self._make_driver()
        driver._conn = MagicMock()
        driver._cursor = MagicMock()
        driver._cursor.fetchone.return_value = (3,)

        result = driver.assert_row_exists("members", {"role": "admin"})
        assert result is driver  # chainable

    def test_assert_row_count_raises(self):
        """assert_row_count raises on mismatch."""
        driver = self._make_driver()
        driver._conn = MagicMock()
        driver._cursor = MagicMock()
        driver._cursor.fetchone.return_value = (5,)

        with pytest.raises(AssertionError, match="Expected 3 rows"):
            driver.assert_row_count("members", 3)

    def test_assert_column_value_passes(self):
        """assert_column_value passes on match."""
        driver = self._make_driver()
        driver._conn = MagicMock()
        driver._cursor = MagicMock()
        driver._cursor.fetchone.return_value = ("admin",)

        result = driver.assert_column_value(
            "members", "role", "admin", where={"id": 1}
        )
        assert result is driver

    def test_assert_column_value_raises(self):
        """assert_column_value raises on mismatch."""
        driver = self._make_driver()
        driver._conn = MagicMock()
        driver._cursor = MagicMock()
        driver._cursor.fetchone.return_value = ("member",)

        with pytest.raises(AssertionError, match="Expected role='admin'"):
            driver.assert_column_value("members", "role", "admin")

    def test_execute_scalar(self):
        """execute_scalar returns first column of first row."""
        driver = self._make_driver()
        driver._conn = MagicMock()
        driver._cursor = MagicMock()
        driver._cursor.fetchone.return_value = (42,)

        result = driver.execute_scalar("SELECT COUNT(*) FROM t")
        assert result == 42
