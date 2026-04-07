"""Tests for the sqlserver_metadata module."""

from unittest.mock import MagicMock, patch
import pytest

from app.sqlserver_metadata import SQLServerMetadata
from app.exceptions import MetadataError


class TestSQLServerMetadataInit:
    """Tests for SQLServerMetadata initialization."""

    def test_init_stores_connection_string(self):
        """Test that connection string is stored."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)
        assert metadata._connection_string == conn_str


class TestSQLServerMetadataSchemaExists:
    """Tests for schema_exists method."""

    def test_schema_exists_returns_true(self):
        """Test schema_exists returns True when schema exists."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.schema_exists("dbo")

            assert result is True
            mock_cursor.execute.assert_called_once()

    def test_schema_exists_returns_false(self):
        """Test schema_exists returns False when schema does not exist."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.schema_exists("nonexistent")

            assert result is False


class TestSQLServerMetadataTableExists:
    """Tests for table_exists method."""

    def test_table_exists_returns_true(self):
        """Test table_exists returns True when table exists."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.table_exists("dbo", "Personnel")

            assert result is True

    def test_table_exists_returns_false(self):
        """Test table_exists returns False when table does not exist."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.table_exists("dbo", "NonExistent")

            assert result is False


class TestSQLServerMetadataColumnExists:
    """Tests for column_exists method."""

    def test_column_exists_returns_true(self):
        """Test column_exists returns True when column exists."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.column_exists("dbo", "Personnel", "LastName")

            assert result is True

    def test_column_exists_returns_false(self):
        """Test column_exists returns False when column does not exist."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.column_exists("dbo", "Personnel", "NonExistent")

            assert result is False


class TestSQLServerMetadataPrimaryKey:
    """Tests for is_primary_key method."""

    def test_is_primary_key_returns_true(self):
        """Test is_primary_key returns True for PK column."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.is_primary_key("dbo", "Personnel", "PersonID")

            assert result is True

    def test_is_primary_key_returns_false(self):
        """Test is_primary_key returns False for non-PK column."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.is_primary_key("dbo", "Personnel", "LastName")

            assert result is False


class TestSQLServerMetadataUnique:
    """Tests for is_unique method."""

    def test_is_unique_returns_true(self):
        """Test is_unique returns True for unique column."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.is_unique("dbo", "Personnel", "SSN")

            assert result is True

    def test_is_unique_returns_false(self):
        """Test is_unique returns False for non-unique column."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.is_unique("dbo", "Personnel", "LastName")

            assert result is False


class TestSQLServerMetadataComputed:
    """Tests for is_computed method."""

    def test_is_computed_returns_true(self):
        """Test is_computed returns True for computed column."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.is_computed("dbo", "Order", "Total")

            assert result is True

    def test_is_computed_returns_false(self):
        """Test is_computed returns False for non-computed column."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.is_computed("dbo", "Personnel", "LastName")

            assert result is False


class TestSQLServerMetadataForeignKey:
    """Tests for foreign key methods."""

    def test_is_foreign_key_source_returns_true(self):
        """Test is_foreign_key_source returns True for FK source column."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.is_foreign_key_source("dbo", "Order", "CustomerID")

            assert result is True

    def test_is_foreign_key_source_returns_false(self):
        """Test is_foreign_key_source returns False for non-FK column."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.is_foreign_key_source("dbo", "Personnel", "LastName")

            assert result is False

    def test_is_foreign_key_target_returns_true(self):
        """Test is_foreign_key_target returns True for FK target column."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.is_foreign_key_target("dbo", "OrderItem", "OrderID")

            assert result is True

    def test_is_foreign_key_target_returns_false(self):
        """Test is_foreign_key_target returns False for non-FK column."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.is_foreign_key_target("dbo", "Personnel", "LastName")

            assert result is False


class TestSQLServerMetadataConnectionError:
    """Tests for connection error handling."""

    def test_connection_failure_raises_metadata_error(self):
        """Test that connection failure raises MetadataError."""
        import pyodbc

        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        with patch("pyodbc.connect", side_effect=pyodbc.Error("Connection failed")):
            with pytest.raises(MetadataError) as exc_info:
                metadata.schema_exists("dbo")
            assert "Failed to connect" in str(exc_info.value.message)


class TestSQLServerMetadataWithCursor:
    """Tests using existing cursor."""

    def test_schema_exists_with_cursor(self):
        """Test schema_exists uses provided cursor."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)

        result = metadata.schema_exists("dbo", cursor=mock_cursor)

        assert result is True

    def test_table_exists_with_cursor(self):
        """Test table_exists uses provided cursor."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)

        result = metadata.table_exists("dbo", "Personnel", cursor=mock_cursor)

        assert result is True

    def test_column_exists_with_cursor(self):
        """Test column_exists uses provided cursor."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)

        result = metadata.column_exists(
            "dbo", "Personnel", "LastName", cursor=mock_cursor
        )

        assert result is True


class TestSQLServerMetadataGetTablePrimaryKeyColumns:
    """Tests for get_table_primary_key_columns method."""

    def test_get_table_primary_key_columns(self):
        """Test getting primary key columns for a table."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("PersonID",), ("RowID",)]
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.get_table_primary_key_columns("dbo", "Personnel")

            assert result == ["PersonID", "RowID"]

    def test_get_table_primary_key_columns_empty(self):
        """Test getting primary key columns when table has no PK."""
        conn_str = (
            "DRIVER={ODBC Driver 17};SERVER=SQL01;DATABASE=MyDb;UID=user;PWD=pass"
        )
        metadata = SQLServerMetadata(conn_str)

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        with patch.object(metadata, "_connect", return_value=mock_connection):
            result = metadata.get_table_primary_key_columns("dbo", "LogTable")

            assert result == []
