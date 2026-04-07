"""Tests for the connection_loader module."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest

from app.connection_loader import ConnectionLoader
from app.exceptions import ConfigurationError


class TestConnectionLoaderValid:
    """Tests for valid connection configuration loading."""

    def test_valid_minimal_config(self):
        """Test loading a valid minimal connection configuration."""
        config_data = {
            "server": "SQL01",
            "username": "masking_user",
            "passwordFile": "secrets/sql-password.dpapi",
            "databases": ["MyDb"],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            config = loader.load(config_path)

            assert config.server_config.server == "SQL01"
            assert config.databases[0].name == "MyDb"
            assert config.server_config.username == "masking_user"
            assert config.server_config.password_file == "secrets/sql-password.dpapi"

    def test_valid_full_config(self):
        """Test loading a complete connection configuration."""
        config_data = {
            "server": "SQL01.example.com",
            "username": "service_account",
            "passwordFile": "secrets/prod-sql.dpapi",
            "databases": ["ProductionDb", "TestDb"],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            config = loader.load(config_path)

            assert config.server_config.server == "SQL01.example.com"
            assert config.databases[0].name == "ProductionDb"
            assert config.databases[1].name == "TestDb"
            assert config.server_config.username == "service_account"
            assert config.server_config.password_file == "secrets/prod-sql.dpapi"


class TestConnectionLoaderInvalid:
    """Tests for invalid connection configuration handling."""

    def test_missing_file(self):
        """Test that missing file raises ConfigurationError."""
        loader = ConnectionLoader()
        with pytest.raises(ConfigurationError) as exc_info:
            loader.load(Path("/nonexistent/path/connection.json"))
        assert "not found" in str(exc_info.value.message)

    def test_empty_path(self):
        """Test that empty path raises ConfigurationError."""
        loader = ConnectionLoader()
        with pytest.raises(ConfigurationError) as exc_info:
            loader.load(Path(""))
        assert "Failed to read" in str(
            exc_info.value.message
        ) or "cannot be empty" in str(exc_info.value.message)

    def test_invalid_json(self):
        """Test that invalid JSON raises ConfigurationError."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text("{ invalid }", encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "Invalid JSON" in str(exc_info.value.message)

    def test_root_not_object(self):
        """Test that non-object root raises ConfigurationError."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text('["array"]', encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "JSON object" in str(exc_info.value.message)

    def test_missing_server(self):
        """Test that missing server raises ConfigurationError."""
        config_data = {
            "database": "MyDb",
            "username": "masking_user",
            "passwordFile": "secrets/sql-password.dpapi",
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "server" in str(exc_info.value.message)

    def test_missing_database(self):
        """Test that missing databases raises ConfigurationError."""
        config_data = {
            "server": "SQL01",
            "username": "masking_user",
            "passwordFile": "secrets/sql-password.dpapi",
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "databases" in str(exc_info.value.message)

    def test_missing_username(self):
        """Test that missing username raises ConfigurationError."""
        config_data = {
            "server": "SQL01",
            "database": "MyDb",
            "passwordFile": "secrets/sql-password.dpapi",
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "username" in str(exc_info.value.message)

    def test_missing_password_file(self):
        """Test that missing passwordFile raises ConfigurationError."""
        config_data = {
            "server": "SQL01",
            "database": "MyDb",
            "username": "masking_user",
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "passwordFile" in str(exc_info.value.message)

    def test_empty_server(self):
        """Test that empty server raises ConfigurationError."""
        config_data = {
            "server": "",
            "username": "masking_user",
            "passwordFile": "secrets/sql-password.dpapi",
            "databases": ["MyDb"],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "server" in str(exc_info.value.message)
            assert "non-empty string" in str(exc_info.value.message)

    def test_empty_username(self):
        """Test that empty username raises ConfigurationError."""
        config_data = {
            "server": "SQL01",
            "username": "",
            "passwordFile": "secrets/sql-password.dpapi",
            "databases": ["MyDb"],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "username" in str(exc_info.value.message)

    def test_empty_password_file(self):
        """Test that empty passwordFile raises ConfigurationError."""
        config_data = {
            "server": "SQL01",
            "username": "masking_user",
            "passwordFile": "",
            "databases": ["MyDb"],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "passwordFile" in str(exc_info.value.message)

    def test_server_not_string(self):
        """Test that non-string server raises ConfigurationError."""
        config_data = {
            "server": 123,
            "username": "masking_user",
            "passwordFile": "secrets/sql-password.dpapi",
            "databases": ["MyDb"],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "server" in str(exc_info.value.message)
            assert "non-empty string" in str(exc_info.value.message)

    def test_username_not_string(self):
        """Test that non-string username raises ConfigurationError."""
        config_data = {
            "server": "SQL01",
            "username": {},
            "passwordFile": "secrets/sql-password.dpapi",
            "databases": ["MyDb"],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "username" in str(exc_info.value.message)

    def test_password_file_not_string(self):
        """Test that non-string passwordFile raises ConfigurationError."""
        config_data = {
            "server": "SQL01",
            "username": "masking_user",
            "passwordFile": 999,
            "databases": ["MyDb"],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "passwordFile" in str(exc_info.value.message)

    def test_server_not_string(self):
        """Test that non-string server raises ConfigurationError."""
        config_data = {
            "server": 123,
            "username": "masking_user",
            "passwordFile": "secrets/sql-password.dpapi",
            "databases": ["MyDb"],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "server" in str(exc_info.value.message)
            assert "non-empty string" in str(exc_info.value.message)

    def test_database_not_string(self):
        """Test that non-string database in list raises ConfigurationError."""
        config_data = {
            "server": "SQL01",
            "username": "masking_user",
            "passwordFile": "secrets/sql-password.dpapi",
            "databases": [["array"]],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "databases" in str(exc_info.value.message)

    def test_username_not_string(self):
        """Test that non-string username raises ConfigurationError."""
        config_data = {
            "server": "SQL01",
            "username": {},
            "passwordFile": "secrets/sql-password.dpapi",
            "databases": ["MyDb"],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "username" in str(exc_info.value.message)

    def test_password_file_not_string(self):
        """Test that non-string passwordFile raises ConfigurationError."""
        config_data = {
            "server": "SQL01",
            "username": "masking_user",
            "passwordFile": 999,
            "databases": ["MyDb"],
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load(config_path)
            assert "passwordFile" in str(exc_info.value.message)

    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored without error."""
        config_data = {
            "server": "SQL01",
            "username": "masking_user",
            "passwordFile": "secrets/sql-password.dpapi",
            "databases": ["MyDb"],
            "extraField": "should be ignored",
            "anotherField": 123,
        }

        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connection.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")

            loader = ConnectionLoader()
            config = loader.load(config_path)

            assert config.server_config.server == "SQL01"
            assert config.databases[0].name == "MyDb"
