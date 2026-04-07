"""Tests for the validator module."""

from unittest.mock import MagicMock, patch
import pytest

from app.models import FunctionalConfig, MaskingRule
from app.validator import Validator
from app.exceptions import ValidationError


class MockMetadata:
    """Mock SQLServerMetadata for testing Validator without real database."""

    def __init__(self, exists_data=None, column_data=None):
        self._exists_data = exists_data or {}
        self._column_data = column_data or {}
        self._calls = []

    def schema_exists(self, schema, cursor=None):
        self._calls.append(("schema_exists", schema))
        return self._exists_data.get("schema", {}).get(schema, False)

    def table_exists(self, schema, table, cursor=None):
        self._calls.append(("table_exists", schema, table))
        return self._exists_data.get("table", {}).get((schema, table), False)

    def column_exists(self, schema, table, column, cursor=None):
        self._calls.append(("column_exists", schema, table, column))
        return self._exists_data.get("column", {}).get((schema, table, column), False)

    def is_primary_key(self, schema, table, column, cursor=None):
        self._calls.append(("is_primary_key", schema, table, column))
        return self._exists_data.get("pk", {}).get((schema, table, column), False)

    def is_unique(self, schema, table, column, cursor=None):
        self._calls.append(("is_unique", schema, table, column))
        return self._exists_data.get("unique", {}).get((schema, table, column), False)

    def is_computed(self, schema, table, column, cursor=None):
        self._calls.append(("is_computed", schema, table, column))
        return self._exists_data.get("computed", {}).get((schema, table, column), False)

    def is_foreign_key_source(self, schema, table, column, cursor=None):
        self._calls.append(("is_foreign_key_source", schema, table, column))
        return self._exists_data.get("fk_source", {}).get(
            (schema, table, column), False
        )

    def is_foreign_key_target(self, schema, table, column, cursor=None):
        self._calls.append(("is_foreign_key_target", schema, table, column))
        return self._exists_data.get("fk_target", {}).get(
            (schema, table, column), False
        )

    def get_column_max_length(self, schema, table, column, cursor=None):
        self._calls.append(("get_column_max_length", schema, table, column))
        key = (schema, table, column)
        if key in self._column_data:
            return self._column_data[key].get("max_length", 50)
        return 50

    def get_column_type(self, schema, table, column, cursor=None):
        self._calls.append(("get_column_type", schema, table, column))
        key = (schema, table, column)
        if key in self._column_data:
            return self._column_data[key].get("type", "varchar")
        return "varchar"


class TestValidatorValid:
    """Tests for valid masking rule validation."""

    def test_valid_single_rule(self):
        """Test validation passes for a valid single rule."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "Personnel"): True},
                "column": {
                    ("dbo", "Personnel", "LastName"): True,
                    ("dbo", "Personnel", "PersonID"): True,
                },
            }
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 0

    def test_valid_multiple_rules(self):
        """Test validation passes for multiple valid rules."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "Personnel"): True, ("dbo", "Salary"): True},
                "column": {
                    ("dbo", "Personnel", "LastName"): True,
                    ("dbo", "Personnel", "FirstName"): True,
                    ("dbo", "Personnel", "PersonID"): True,
                    ("dbo", "Salary", "Amount"): True,
                    ("dbo", "Salary", "EmployeeID"): True,
                },
            }
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
            ),
            MaskingRule(
                schema="dbo", table="Personnel", column="FirstName", order_by="PersonID"
            ),
            MaskingRule(
                schema="dbo", table="Salary", column="Amount", order_by="EmployeeID"
            ),
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 0


class TestValidatorInvalidSchema:
    """Tests for schema validation errors."""

    def test_missing_schema(self):
        """Test validation fails when schema does not exist."""
        metadata = MockMetadata(
            {
                "schema": {"other_schema": True},
            }
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 1
        assert "Schema" in errors[0].message
        assert "dbo" in errors[0].message
        assert "does not exist" in errors[0].message


class TestValidatorInvalidTable:
    """Tests for table validation errors."""

    def test_missing_table(self):
        """Test validation fails when table does not exist."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
            }
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 1
        assert "Table" in errors[0].message
        assert "Personnel" in errors[0].message
        assert "does not exist" in errors[0].message


class TestValidatorInvalidColumn:
    """Tests for column validation errors."""

    def test_missing_column_to_mask(self):
        """Test validation fails when column to mask does not exist."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "Personnel"): True},
            }
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 1
        assert "Column" in errors[0].message
        assert "LastName" in errors[0].message
        assert "does not exist" in errors[0].message

    def test_missing_order_by_column(self):
        """Test validation fails when orderBy column does not exist."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "Personnel"): True},
                "column": {("dbo", "Personnel", "LastName"): True},
            }
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 1
        assert "orderBy" in errors[0].message
        assert "PersonID" in errors[0].message
        assert "does not exist" in errors[0].message


class TestValidatorPrimaryKey:
    """Tests for primary key validation."""

    def test_primary_key_column_rejected(self):
        """Test validation fails when column is a primary key."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "Personnel"): True},
                "column": {
                    ("dbo", "Personnel", "PersonID"): True,
                    ("dbo", "Personnel", "LastName"): True,
                },
                "pk": {("dbo", "Personnel", "PersonID"): True},
            }
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="PersonID", order_by="PersonID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 1
        assert "PRIMARY KEY" in errors[0].message
        assert "cannot be masked" in errors[0].message


class TestValidatorUnique:
    """Tests for unique constraint validation."""

    def test_unique_column_rejected(self):
        """Test validation fails when column has a unique constraint."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "Personnel"): True},
                "column": {
                    ("dbo", "Personnel", "SSN"): True,
                    ("dbo", "Personnel", "PersonID"): True,
                },
                "unique": {("dbo", "Personnel", "SSN"): True},
            }
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="SSN", order_by="PersonID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 1
        assert "UNIQUE" in errors[0].message
        assert "cannot be masked" in errors[0].message


class TestValidatorComputed:
    """Tests for computed column validation."""

    def test_computed_column_rejected(self):
        """Test validation fails when column is computed."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "Order"): True},
                "column": {
                    ("dbo", "Order", "Total"): True,
                    ("dbo", "Order", "OrderID"): True,
                },
                "computed": {("dbo", "Order", "Total"): True},
            }
        )

        rules = [
            MaskingRule(schema="dbo", table="Order", column="Total", order_by="OrderID")
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 1
        assert "COMPUTED" in errors[0].message
        assert "cannot be masked" in errors[0].message


class TestValidatorForeignKey:
    """Tests for foreign key validation."""

    def test_foreign_key_source_rejected(self):
        """Test validation fails when column is source of foreign key."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "Department"): True},
                "column": {
                    ("dbo", "Department", "DeptID"): True,
                    ("dbo", "Department", "Name"): True,
                },
                "fk_source": {("dbo", "Department", "DeptID"): True},
            }
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Department", column="DeptID", order_by="DeptID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 1
        assert "outgoing FOREIGN KEY" in errors[0].message
        assert "cannot be masked" in errors[0].message

    def test_foreign_key_target_rejected(self):
        """Test validation fails when column is target of foreign key."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "Employee"): True},
                "column": {
                    ("dbo", "Employee", "DeptID"): True,
                    ("dbo", "Employee", "Name"): True,
                    ("dbo", "Employee", "EmployeeID"): True,
                },
                "fk_target": {("dbo", "Employee", "DeptID"): True},
            }
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Employee", column="DeptID", order_by="EmployeeID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 1
        assert "incoming FOREIGN KEY" in errors[0].message
        assert "cannot be masked" in errors[0].message


class TestValidatorMultipleErrors:
    """Tests for multiple validation errors."""

    def test_multiple_errors_for_single_rule(self):
        """Test multiple errors are returned for a single rule."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "Personnel"): True},
                "column": {
                    ("dbo", "Personnel", "PersonID"): True,
                },
                "pk": {("dbo", "Personnel", "PersonID"): True},
            }
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="PersonID", order_by="PersonID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 1
        assert "PRIMARY KEY" in errors[0].message

    def test_multiple_errors_for_multiple_rules(self):
        """Test errors from multiple rules are all returned."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True, "other": True},
                "table": {
                    ("dbo", "Personnel"): True,
                    ("other", "Table"): True,
                },
                "column": {
                    ("dbo", "Personnel", "LastName"): True,
                    ("other", "Table", "Col"): True,
                },
            }
        )

        rules = [
            MaskingRule(
                schema="other_schema",
                table="Personnel",
                column="LastName",
                order_by="PersonID",
            ),
            MaskingRule(
                schema="other", table="NonExistent", column="Col", order_by="ID"
            ),
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 2
        error_messages = [e.message for e in errors]
        assert any("other_schema" in m for m in error_messages)
        assert any("NonExistent" in m for m in error_messages)


class TestValidatorReturnsListNotRaises:
    """Test that validate returns list of errors, does not raise."""

    def test_validate_returns_list(self):
        """Test that validate() returns a list, even when errors exist."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "Personnel"): True},
                "column": {
                    ("dbo", "Personnel", "PersonID"): True,
                },
                "pk": {("dbo", "Personnel", "PersonID"): True},
            }
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="PersonID", order_by="PersonID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        result = validator.validate(config)

        assert isinstance(result, list)
        assert len(result) == 1


class TestValidatorMaskedValueLength:
    """Tests for masked value length validation."""

    def test_masked_value_fits_in_column(self):
        """Test validation passes when masked value fits in column."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "Personnel"): True},
                "column": {
                    ("dbo", "Personnel", "LastName"): True,
                    ("dbo", "Personnel", "PersonID"): True,
                },
            },
            {
                ("dbo", "Personnel", "LastName"): {
                    "max_length": 50,
                    "type": "varchar",
                },
            },
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 0

    def test_masked_value_exceeds_varchar_column(self):
        """Test validation fails when masked value exceeds varchar column length."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "Personnel"): True},
                "column": {
                    ("dbo", "Personnel", "LastName"): True,
                    ("dbo", "Personnel", "PersonID"): True,
                },
            },
            {
                ("dbo", "Personnel", "LastName"): {
                    "max_length": 10,
                    "type": "varchar",
                },
            },
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 1
        assert "exceeds" in errors[0].message
        assert "max length" in errors[0].message

    def test_masked_value_exceeds_nvarchar_column(self):
        """Test validation fails when masked value exceeds nvarchar column length."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "Personnel"): True},
                "column": {
                    ("dbo", "Personnel", "LastName"): True,
                    ("dbo", "Personnel", "PersonID"): True,
                },
            },
            {
                ("dbo", "Personnel", "LastName"): {
                    "max_length": 20,
                    "type": "nvarchar",
                },
            },
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="LastName", order_by="PersonID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 1
        assert "exceeds" in errors[0].message
        assert "nvarchar" in errors[0].message

    def test_length_calculation_with_long_column_name(self):
        """Test validation fails when column name makes masked value too long."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "VeryLongTableName"): True},
                "column": {
                    ("dbo", "VeryLongTableName", "VeryLongColumnName"): True,
                    ("dbo", "VeryLongTableName", "ID"): True,
                },
            },
            {
                ("dbo", "VeryLongTableName", "VeryLongColumnName"): {
                    "max_length": 20,
                    "type": "varchar",
                },
            },
        )

        rules = [
            MaskingRule(
                schema="dbo",
                table="VeryLongTableName",
                column="VeryLongColumnName",
                order_by="ID",
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 1
        assert "exceeds" in errors[0].message

    def test_nvarchaR_correct_length_handling(self):
        """Test that nvarchar columns correctly divide max_length by 2."""
        metadata = MockMetadata(
            {
                "schema": {"dbo": True},
                "table": {("dbo", "Personnel"): True},
                "column": {
                    ("dbo", "Personnel", "Name"): True,
                    ("dbo", "Personnel", "PersonID"): True,
                },
            },
            {
                ("dbo", "Personnel", "Name"): {
                    "max_length": 40,
                    "type": "nvarchar",
                },
            },
        )

        rules = [
            MaskingRule(
                schema="dbo", table="Personnel", column="Name", order_by="PersonID"
            )
        ]
        config = FunctionalConfig(
            masking_format="<{column}_{counter}>", pad_length=4, masking_rules=rules
        )

        validator = Validator(metadata)
        errors = validator.validate(config)

        assert len(errors) == 0
