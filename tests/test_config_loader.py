"""Tests for the config_loader module."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest

from app.config_loader import ConfigLoader
from app.exceptions import ConfigurationError


class TestConfigLoaderValid:
    """Tests for valid configuration loading."""

    def test_valid_minimal_config(self):
        """Test loading a valid minimal configuration."""
        config_data = {
            "global": {"maskingFormat": "<{column}_{counter}>", "padLength": 4},
            "maskingRules": [
                {
                    "schema": "dbo",
                    "table": "Personnel",
                    "column": "LastName",
                    "orderBy": "PersonID",
                }
            ],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            config = loader.load(config_path)

            assert config.masking_format == "<{column}_{counter}>"
            assert config.pad_length == 4
            assert len(config.masking_rules) == 1
            assert config.masking_rules[0].schema == "dbo"
            assert config.masking_rules[0].table == "Personnel"
            assert config.masking_rules[0].column == "LastName"
            assert config.masking_rules[0].order_by == "PersonID"

    def test_valid_multiple_rules(self):
        """Test loading configuration with multiple rules."""
        config_data = {
            "global": {"maskingFormat": "<{column}_{counter}>", "padLength": 6},
            "maskingRules": [
                {
                    "schema": "dbo",
                    "table": "Personnel",
                    "column": "LastName",
                    "orderBy": "PersonID",
                },
                {
                    "schema": "dbo",
                    "table": "Personnel",
                    "column": "FirstName",
                    "orderBy": "PersonID",
                },
                {
                    "schema": "dbo",
                    "table": "Salary",
                    "column": "Amount",
                    "orderBy": "EmployeeID",
                },
            ],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            config = loader.load(config_path)

            assert len(config.masking_rules) == 3
            assert config.pad_length == 6


class TestConfigLoaderInvalid:
    """Tests for invalid configuration handling."""

    def test_missing_file(self):
        """Test that missing file raises ConfigurationError."""
        loader = ConfigLoader()
        with pytest.raises(ConfigurationError) as exc_info:
            loader.load(Path("/nonexistent/path/config.json"))
        assert "not found" in str(exc_info.value.message)

    def test_empty_path(self):
        """Test that empty path raises ConfigurationError."""
        loader = ConfigLoader()
        with pytest.raises(ConfigurationError) as exc_info:
            loader.load(Path(""))
        assert "Failed to read" in str(
            exc_info.value.message
        ) or "cannot be empty" in str(exc_info.value.message)

    def test_invalid_json(self):
        """Test that invalid JSON raises ConfigurationError."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("{ invalid json }", encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "Invalid JSON" in str(exc_info.value.message)

    def test_root_not_object(self):
        """Test that non-object root raises ConfigurationError."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(
                '["array", "instead", "of", "object"]', encoding="utf-8"
            )

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "JSON object" in str(exc_info.value.message)

    def test_missing_global_section(self):
        """Test that missing global section raises ConfigurationError."""
        config_data = {
            "maskingRules": [
                {
                    "schema": "dbo",
                    "table": "Personnel",
                    "column": "LastName",
                    "orderBy": "PersonID",
                }
            ]
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "maskingFormat" in str(exc_info.value.message)
            assert "padLength" in str(exc_info.value.message)

    def test_missing_masking_format(self):
        """Test that missing maskingFormat raises ConfigurationError."""
        config_data = {"global": {"padLength": 4}, "maskingRules": []}

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "maskingFormat" in str(exc_info.value.message)

    def test_missing_pad_length(self):
        """Test that missing padLength raises ConfigurationError."""
        config_data = {
            "global": {"maskingFormat": "<{column}_{counter}>"},
            "maskingRules": [],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "padLength" in str(exc_info.value.message)

    def test_invalid_pad_length_zero(self):
        """Test that zero padLength raises ConfigurationError."""
        config_data = {
            "global": {"maskingFormat": "<{column}_{counter}>", "padLength": 0},
            "maskingRules": [],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "padLength" in str(exc_info.value.message)
            assert "strictly positive" in str(exc_info.value.message)

    def test_invalid_pad_length_negative(self):
        """Test that negative padLength raises ConfigurationError."""
        config_data = {
            "global": {"maskingFormat": "<{column}_{counter}>", "padLength": -1},
            "maskingRules": [],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "padLength" in str(exc_info.value.message)

    def test_invalid_pad_length_string(self):
        """Test that string padLength raises ConfigurationError."""
        config_data = {
            "global": {"maskingFormat": "<{column}_{counter}>", "padLength": "four"},
            "maskingRules": [],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "padLength" in str(exc_info.value.message)
            assert "integer" in str(exc_info.value.message)

    def test_invalid_masking_format_empty_string(self):
        """Test that empty masking format raises error."""
        config_data = {
            "global": {"maskingFormat": "", "padLength": 4},
            "maskingRules": [
                {"schema": "dbo", "table": "T", "column": "C", "orderBy": "ID"}
            ],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "maskingFormat" in str(exc_info.value.message)
            assert "non-empty" in str(exc_info.value.message)

    def test_empty_masking_rules(self):
        """Test that empty maskingRules array raises ConfigurationError."""
        config_data = {
            "global": {"maskingFormat": "<{column}_{counter}>", "padLength": 4},
            "maskingRules": [],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "maskingRules" in str(exc_info.value.message)
            assert "empty" in str(exc_info.value.message)

    def test_masking_rules_not_array(self):
        """Test that non-array maskingRules raises ConfigurationError."""
        config_data = {
            "global": {"maskingFormat": "<{column}_{counter}>", "padLength": 4},
            "maskingRules": {"schema": "dbo"},
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "maskingRules" in str(exc_info.value.message)
            assert "array" in str(exc_info.value.message)

    def test_incomplete_rule_missing_schema(self):
        """Test that rule missing schema raises ConfigurationError."""
        config_data = {
            "global": {"maskingFormat": "<{column}_{counter}>", "padLength": 4},
            "maskingRules": [
                {"table": "Personnel", "column": "LastName", "orderBy": "PersonID"}
            ],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "schema" in str(exc_info.value.message)

    def test_incomplete_rule_missing_table(self):
        """Test that rule missing table raises ConfigurationError."""
        config_data = {
            "global": {"maskingFormat": "<{column}_{counter}>", "padLength": 4},
            "maskingRules": [
                {"schema": "dbo", "column": "LastName", "orderBy": "PersonID"}
            ],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "table" in str(exc_info.value.message)

    def test_incomplete_rule_missing_column(self):
        """Test that rule missing column raises ConfigurationError."""
        config_data = {
            "global": {"maskingFormat": "<{column}_{counter}>", "padLength": 4},
            "maskingRules": [
                {"schema": "dbo", "table": "Personnel", "orderBy": "PersonID"}
            ],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "column" in str(exc_info.value.message)

    def test_incomplete_rule_missing_order_by(self):
        """Test that rule missing orderBy raises ConfigurationError."""
        config_data = {
            "global": {"maskingFormat": "<{column}_{counter}>", "padLength": 4},
            "maskingRules": [
                {"schema": "dbo", "table": "Personnel", "column": "LastName"}
            ],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "orderBy" in str(exc_info.value.message)

    def test_rule_field_not_string(self):
        """Test that non-string rule field raises ConfigurationError."""
        config_data = {
            "global": {"maskingFormat": "<{column}_{counter}>", "padLength": 4},
            "maskingRules": [
                {
                    "schema": "dbo",
                    "table": "Personnel",
                    "column": 123,
                    "orderBy": "PersonID",
                }
            ],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "non-empty string" in str(exc_info.value.message)

    def test_rule_field_empty_string(self):
        """Test that empty string rule field raises ConfigurationError."""
        config_data = {
            "global": {"maskingFormat": "<{column}_{counter}>", "padLength": 4},
            "maskingRules": [
                {
                    "schema": "",
                    "table": "Personnel",
                    "column": "LastName",
                    "orderBy": "PersonID",
                }
            ],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "non-empty string" in str(exc_info.value.message)

    def test_global_not_object(self):
        """Test that non-object global raises ConfigurationError."""
        config_data = {
            "global": ["array"],
            "maskingRules": [
                {
                    "schema": "dbo",
                    "table": "Personnel",
                    "column": "LastName",
                    "orderBy": "PersonID",
                }
            ],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "'global'" in str(exc_info.value.message)
            assert "object" in str(exc_info.value.message)

    def test_masking_format_not_string(self):
        """Test that non-string maskingFormat raises ConfigurationError."""
        config_data = {
            "global": {"maskingFormat": 12345, "padLength": 4},
            "maskingRules": [
                {
                    "schema": "dbo",
                    "table": "Personnel",
                    "column": "LastName",
                    "orderBy": "PersonID",
                }
            ],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConfigLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "maskingFormat" in str(exc_info.value.message)
            assert "non-empty string" in str(exc_info.value.message)
