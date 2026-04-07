"""SQL Server metadata queries for validation."""

from typing import Any, Dict, List, Optional, Tuple

import pyodbc

from app.exceptions import MetadataError


class SQLServerMetadata:
    """Queries SQL Server system catalogs for table and column metadata."""

    def __init__(self, connection_string: str) -> None:
        """Initialize with a SQL Server connection string.

        Args:
            connection_string: Full ODBC connection string with credentials.
        """
        self._connection_string = connection_string

    def _connect(self) -> pyodbc.Connection:
        """Establish a connection to SQL Server.

        Returns:
            An open pyodbc connection.

        Raises:
            MetadataError: If connection fails.
        """
        try:
            return pyodbc.connect(self._connection_string, timeout=30)
        except pyodbc.Error as e:
            raise MetadataError("Failed to connect to SQL Server: {}".format(str(e)))

    def schema_exists(
        self, schema: str, cursor: Optional[pyodbc.Cursor] = None
    ) -> bool:
        """Check if a schema exists in the database.

        Args:
            schema: Schema name to check.
            cursor: Optional existing cursor to use.

        Returns:
            True if schema exists, False otherwise.
        """
        query = """
            SELECT 1 FROM sys.schemas WHERE name = ?
        """
        return self._execute_exists(query, (schema,), cursor)

    def table_exists(
        self, schema: str, table: str, cursor: Optional[pyodbc.Cursor] = None
    ) -> bool:
        """Check if a table exists in the database.

        Args:
            schema: Schema name.
            table: Table name.
            cursor: Optional existing cursor to use.

        Returns:
            True if table exists, False otherwise.
        """
        query = """
            SELECT 1 FROM sys.tables t
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE s.name = ? AND t.name = ?
        """
        return self._execute_exists(query, (schema, table), cursor)

    def column_exists(
        self,
        schema: str,
        table: str,
        column: str,
        cursor: Optional[pyodbc.Cursor] = None,
    ) -> bool:
        """Check if a column exists in a table.

        Args:
            schema: Schema name.
            table: Table name.
            column: Column name.
            cursor: Optional existing cursor to use.

        Returns:
            True if column exists, False otherwise.
        """
        query = """
            SELECT 1 FROM sys.columns c
            INNER JOIN sys.tables t ON c.object_id = t.object_id
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE s.name = ? AND t.name = ? AND c.name = ?
        """
        return self._execute_exists(query, (schema, table, column), cursor)

    def is_primary_key(
        self,
        schema: str,
        table: str,
        column: str,
        cursor: Optional[pyodbc.Cursor] = None,
    ) -> bool:
        """Check if a column is part of the primary key.

        Args:
            schema: Schema name.
            table: Table name.
            column: Column name.
            cursor: Optional existing cursor to use.

        Returns:
            True if column is a primary key, False otherwise.
        """
        query = """
            SELECT 1 FROM sys.indexes i
            INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            INNER JOIN sys.tables t ON i.object_id = t.object_id
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE i.is_primary_key = 1
              AND s.name = ? AND t.name = ? AND c.name = ?
        """
        return self._execute_exists(query, (schema, table, column), cursor)

    def is_unique(
        self,
        schema: str,
        table: str,
        column: str,
        cursor: Optional[pyodbc.Cursor] = None,
    ) -> bool:
        """Check if a column has a unique constraint.

        Args:
            schema: Schema name.
            table: Table name.
            column: Column name.
            cursor: Optional existing cursor to use.

        Returns:
            True if column is unique, False otherwise.
        """
        query = """
            SELECT 1 FROM sys.indexes i
            INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            INNER JOIN sys.tables t ON i.object_id = t.object_id
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE i.is_unique = 1 AND i.type_description != 'HEAP'
              AND s.name = ? AND t.name = ? AND c.name = ?
        """
        return self._execute_exists(query, (schema, table, column), cursor)

    def is_computed(
        self,
        schema: str,
        table: str,
        column: str,
        cursor: Optional[pyodbc.Cursor] = None,
    ) -> bool:
        """Check if a column is a computed column.

        Args:
            schema: Schema name.
            table: Table name.
            column: Column name.
            cursor: Optional existing cursor to use.

        Returns:
            True if column is computed, False otherwise.
        """
        query = """
            SELECT 1 FROM sys.columns c
            INNER JOIN sys.tables t ON c.object_id = t.object_id
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE c.is_computed = 1
              AND s.name = ? AND t.name = ? AND c.name = ?
        """
        return self._execute_exists(query, (schema, table, column), cursor)

    def is_foreign_key_source(
        self,
        schema: str,
        table: str,
        column: str,
        cursor: Optional[pyodbc.Cursor] = None,
    ) -> bool:
        """Check if a column is involved in an outgoing foreign key (referenced column).

        Args:
            schema: Schema name.
            table: Table name.
            column: Column name.
            cursor: Optional existing cursor to use.

        Returns:
            True if column is a source of a foreign key, False otherwise.
        """
        query = """
            SELECT 1 FROM sys.foreign_key_columns fkc
            INNER JOIN sys.columns c ON fkc.parent_column_id = c.column_id AND fkc.parent_object_id = c.object_id
            INNER JOIN sys.tables t ON c.object_id = t.object_id
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE s.name = ? AND t.name = ? AND c.name = ?
        """
        return self._execute_exists(query, (schema, table, column), cursor)

    def is_foreign_key_target(
        self,
        schema: str,
        table: str,
        column: str,
        cursor: Optional[pyodbc.Cursor] = None,
    ) -> bool:
        """Check if a column is involved in an incoming foreign key (referencing column).

        Args:
            schema: Schema name.
            table: Table name.
            column: Column name.
            cursor: Optional existing cursor to use.

        Returns:
            True if column is a target of a foreign key, False otherwise.
        """
        query = """
            SELECT 1 FROM sys.foreign_key_columns fkc
            INNER JOIN sys.columns c ON fkc.referenced_column_id = c.column_id AND fkc.referenced_object_id = c.object_id
            INNER JOIN sys.tables t ON c.object_id = t.object_id
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE s.name = ? AND t.name = ? AND c.name = ?
        """
        return self._execute_exists(query, (schema, table, column), cursor)

    def get_table_primary_key_columns(
        self, schema: str, table: str, cursor: Optional[pyodbc.Cursor] = None
    ) -> List[str]:
        """Get all columns that are part of the primary key.

        Args:
            schema: Schema name.
            table: Table name.
            cursor: Optional existing cursor to use.

        Returns:
            List of primary key column names.
        """
        query = """
            SELECT c.name
            FROM sys.indexes i
            INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            INNER JOIN sys.tables t ON i.object_id = t.object_id
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE i.is_primary_key = 1
              AND s.name = ? AND t.name = ?
            ORDER BY ic.key_ordinal
        """
        return self._execute_list(query, (schema, table), cursor)

    def _execute_exists(
        self,
        query: str,
        params: Tuple[Any, ...],
        cursor: Optional[pyodbc.Cursor] = None,
    ) -> bool:
        """Execute a query that returns a single boolean value.

        Args:
            query: SQL query to execute.
            params: Query parameters.
            cursor: Optional existing cursor to use.

        Returns:
            True if a row is returned, False otherwise.
        """
        own_connection = cursor is None
        conn = None
        cur = None
        try:
            if own_connection:
                conn = self._connect()
                cur = conn.cursor()
            else:
                cur = cursor

            cur.execute(query, params)
            row = cur.fetchone()
            return row is not None
        finally:
            if own_connection:
                if cur:
                    cur.close()
                if conn:
                    conn.close()

    def _execute_list(
        self,
        query: str,
        params: Tuple[Any, ...],
        cursor: Optional[pyodbc.Cursor] = None,
    ) -> List[str]:
        """Execute a query that returns a list of strings.

        Args:
            query: SQL query to execute.
            params: Query parameters.
            cursor: Optional existing cursor to use.

        Returns:
            List of string values from the query.
        """
        own_connection = cursor is None
        conn = None
        cur = None
        try:
            if own_connection:
                conn = self._connect()
                cur = conn.cursor()
            else:
                cur = cursor

            cur.execute(query, params)
            return [row[0] for row in cur.fetchall()]
        finally:
            if own_connection:
                if cur:
                    cur.close()
                if conn:
                    conn.close()
