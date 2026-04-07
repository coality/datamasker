"""Tests for the cli module."""

import sys
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock
import argparse
import pytest

from app.cli import (
    main,
    create_argparser,
    handle_generate,
    handle_encrypt_password,
    _build_connection_string,
    _decrypt_password,
)
from app.exceptions import ConfigurationError, SecretError, ValidationError
from app.models import FunctionalConfig, MaskingRule, ConnectionConfig
from app.secret_store import SecretStore


class TestCreateArgparser:
    """Tests for argument parser creation."""

    def test_parser_creation(self):
        """Test that parser is created successfully."""
        parser = create_argparser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == "datamasker"

    def test_subcommands_exist(self):
        """Test that expected subcommands are available."""
        parser = create_argparser()
        subparsers_action = None
        for action in parser._actions:
            if hasattr(action, "_parser_class"):
                subparsers_action = action
                break
        assert subparsers_action is not None
        subcommand_names = list(subparsers_action.choices.keys())
        assert "encrypt-password" in subcommand_names
        assert "generate" in subcommand_names

    def test_encrypt_password_subcommand_has_output_arg(self):
        """Test encrypt-password subcommand has required --output argument."""
        parser = create_argparser()
        subparsers = parser._subparsers._actions[1]
        encrypt_parser = subparsers.choices["encrypt-password"]

        actions = {action.dest: action for action in encrypt_parser._actions}
        assert "output" in actions
        assert actions["output"].required is True

    def test_generate_subcommand_has_required_args(self):
        """Test generate subcommand has all required arguments."""
        parser = create_argparser()
        subparsers = parser._subparsers._actions[1]
        generate_parser = subparsers.choices["generate"]

        actions = {action.dest: action for action in generate_parser._actions}
        assert "config" in actions
        assert "connection" in actions
        assert "output" in actions
        assert actions["config"].required is True
        assert actions["connection"].required is True
        assert actions["output"].required is True


class TestBuildConnectionString:
    """Tests for connection string building."""

    def test_build_connection_string(self):
        """Test building a connection string."""
        config = ConnectionConfig(
            server="SQL01",
            database="MyDb",
            username="masking_user",
            password_file="secrets/sql-password.dpapi",
        )
        password = "MySecretPassword"

        result = _build_connection_string(config, password)

        assert "DRIVER={ODBC Driver 17 for SQL Server}" in result
        assert "SERVER=SQL01" in result
        assert "DATABASE=MyDb" in result
        assert "UID=masking_user" in result
        assert "PWD=MySecretPassword" in result
        assert ";" in result

    def test_connection_string_password_not_in_logs(self):
        """Test that password in connection string won't appear in error messages by default."""
        config = ConnectionConfig(
            server="SQL01",
            database="MyDb",
            username="masking_user",
            password_file="secrets/sql-password.dpapi",
        )
        password = "SuperSecret123"

        result = _build_connection_string(config, password)

        assert "SuperSecret123" in result
        assert "PWD=SuperSecret123" in result


class TestHandleEncryptPassword:
    """Tests for encrypt-password command handler."""

    def test_handling_when_not_windows(self):
        """Test that non-Windows platform shows error."""
        with patch.object(sys, "platform", "linux"):
            with patch("app.cli._read_password_interactive", return_value="password"):
                args = MagicMock()
                args.output = Path("/tmp/out.dpapi")

                result = handle_encrypt_password(args)

                assert result == 1

    def test_handling_empty_password(self):
        """Test that empty password shows error."""
        with patch.object(sys, "platform", "win32"):
            args = MagicMock()
            args.output = Path("/tmp/out.dpapi")

            with patch("app.cli._read_password_interactive", return_value=""):
                result = handle_encrypt_password(args)
                assert result == 1

    def test_handling_keyboard_interrupt(self):
        """Test that KeyboardInterrupt is handled gracefully."""
        with patch.object(sys, "platform", "win32"):
            args = MagicMock()
            args.output = Path("/tmp/out.dpapi")

            with patch(
                "app.cli._read_password_interactive", side_effect=KeyboardInterrupt
            ):
                result = handle_encrypt_password(args)
                assert result == 1


class TestHandleGenerate:
    """Tests for generate command handler."""

    def test_handling_config_load_error(self):
        """Test handling of functional config load error."""
        with patch("app.cli.ConfigLoader") as mock_config_loader:
            mock_config_loader.return_value.load.side_effect = ConfigurationError(
                "config error"
            )

            args = MagicMock()
            args.config = Path("/tmp/config.json")
            args.connection = Path("/tmp/connection.json")
            args.output = Path("/tmp/masking.sql")

            result = handle_generate(args)

            assert result == 1

    def test_handling_connection_load_error(self):
        """Test handling of connection config load error."""
        with patch("app.cli.ConfigLoader") as mock_config_loader:
            mock_config_loader.return_value.load.return_value = MagicMock()

            with patch("app.cli.ConnectionLoader") as mock_conn_loader:
                mock_conn_loader.return_value.load.side_effect = ConfigurationError(
                    "connection error"
                )

                args = MagicMock()
                args.config = Path("/tmp/config.json")
                args.connection = Path("/tmp/connection.json")
                args.output = Path("/tmp/masking.sql")

                result = handle_generate(args)

                assert result == 1

    def test_handling_secret_error(self):
        """Test handling of secret decryption error."""
        with (
            patch("app.cli.ConfigLoader") as mock_config_loader,
            patch("app.cli.ConnectionLoader") as mock_conn_loader,
            patch("app.cli.SecretStore") as mock_secret_store,
        ):
            mock_config_loader.return_value.load.return_value = MagicMock()
            mock_conn_loader.return_value.load.return_value = MagicMock()
            mock_secret_store.return_value.decrypt_password.side_effect = SecretError(
                "secret error"
            )

            args = MagicMock()
            args.config = Path("/tmp/config.json")
            args.connection = Path("/tmp/connection.json")
            args.output = Path("/tmp/masking.sql")

            result = handle_generate(args)

            assert result == 1

    def test_handling_validation_errors(self):
        """Test handling of validation errors."""
        with (
            patch("app.cli.ConfigLoader") as mock_config_loader,
            patch("app.cli.ConnectionLoader") as mock_conn_loader,
            patch("app.cli.SecretStore") as mock_secret_store,
            patch("app.cli.SQLServerMetadata") as mock_metadata,
            patch("app.cli.Validator") as mock_validator,
        ):
            functional_config = MagicMock(spec=FunctionalConfig)
            connection_config = MagicMock(spec=ConnectionConfig)
            connection_config.server = "SQL01"
            connection_config.database = "MyDb"
            connection_config.username = "masking_user"
            connection_config.password_file = "secrets/sql-password.dpapi"

            mock_config_loader.return_value.load.return_value = functional_config
            mock_conn_loader.return_value.load.return_value = connection_config
            mock_secret_store.return_value.decrypt_password.return_value = "password"
            mock_validator.return_value.validate.return_value = [
                ValidationError("Schema 'dbo' does not exist")
            ]

            args = MagicMock()
            args.config = Path("/tmp/config.json")
            args.connection = Path("/tmp/connection.json")
            args.output = Path("/tmp/masking.sql")

            result = handle_generate(args)

            assert result == 1


class TestMainFunction:
    """Tests for main function."""

    def test_main_with_no_args(self):
        """Test main() with no arguments shows help and returns 0."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            result = main([])
            assert result == 0

    def test_main_with_help(self):
        """Test main() with --help shows help and exits."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_main_with_encrypt_password_help(self):
        """Test main() with encrypt-password --help shows subcommand help."""
        with pytest.raises(SystemExit) as exc_info:
            main(["encrypt-password", "--help"])
        assert exc_info.value.code == 0

    def test_main_with_generate_help(self):
        """Test main() with generate --help shows subcommand help."""
        with pytest.raises(SystemExit) as exc_info:
            main(["generate", "--help"])
        assert exc_info.value.code == 0

    def test_main_with_unknown_command(self):
        """Test main() with unknown command exits with error."""
        with patch("sys.stdout", new_callable=StringIO):
            with pytest.raises(SystemExit) as exc_info:
                main(["unknown-command"])
            assert exc_info.value.code == 2


class TestDecryptPassword:
    """Tests for _decrypt_password helper."""

    def test_decrypt_password_calls_secret_store(self):
        """Test that _decrypt_password properly calls SecretStore."""
        secret_store = MagicMock(spec=SecretStore)
        secret_store.decrypt_password.return_value = "decrypted_password"

        result = _decrypt_password(secret_store, "secrets/password.dpapi")

        secret_store.decrypt_password.assert_called_once_with(
            Path("secrets/password.dpapi")
        )
        assert result == "decrypted_password"

    def test_decrypt_password_raises_on_error(self):
        """Test that _decrypt_password propagates SecretError."""
        secret_store = MagicMock(spec=SecretStore)
        secret_store.decrypt_password.side_effect = SecretError("file not found")

        with pytest.raises(SecretError):
            _decrypt_password(secret_store, "secrets/password.dpapi")


class TestCLIExitCodes:
    """Tests for CLI exit codes."""

    def test_encrypt_password_returns_0_on_success(self):
        """Test encrypt-password returns 0 on success (mocked)."""
        with patch.object(sys, "platform", "win32"):
            with patch("app.cli._read_password_interactive", return_value="password"):
                with patch.object(SecretStore, "supports_dpapi", True):
                    with patch.object(SecretStore, "encrypt_password"):
                        args = MagicMock()
                        args.output = Path("/tmp/out.dpapi")

                        result = handle_encrypt_password(args)

                        assert result == 0

    def test_encrypt_password_returns_1_on_secret_error(self):
        """Test encrypt-password returns 1 on SecretError (mocked)."""
        with patch.object(sys, "platform", "win32"):
            with patch("app.cli._read_password_interactive", return_value="password"):
                with patch.object(SecretStore, "supports_dpapi", True):
                    with patch.object(
                        SecretStore,
                        "encrypt_password",
                        side_effect=SecretError("error"),
                    ):
                        args = MagicMock()
                        args.output = Path("/tmp/out.dpapi")

                        result = handle_encrypt_password(args)

                        assert result == 1

    def test_generate_returns_0_on_success(self):
        """Test generate returns 0 on success (mocked)."""
        with (
            patch("app.cli.ConfigLoader") as mock_config_loader,
            patch("app.cli.ConnectionLoader") as mock_conn_loader,
            patch("app.cli.SecretStore") as mock_secret_store,
            patch("app.cli.SQLServerMetadata") as mock_metadata,
            patch("app.cli.Validator") as mock_validator,
            patch("app.cli.SQLGenerator") as mock_generator,
            patch("pathlib.Path.mkdir") as mock_mkdir,
            patch("pathlib.Path.write_text") as mock_write_text,
        ):
            functional_config = MagicMock(spec=FunctionalConfig)
            connection_config = MagicMock(spec=ConnectionConfig)
            connection_config.server = "SQL01"
            connection_config.database = "MyDb"
            connection_config.username = "masking_user"
            connection_config.password_file = "secrets/sql-password.dpapi"

            mock_config_loader.return_value.load.return_value = functional_config
            mock_conn_loader.return_value.load.return_value = connection_config
            mock_secret_store.return_value.decrypt_password.return_value = "password"
            mock_validator.return_value.validate.return_value = []
            mock_generator.return_value.generate.return_value = "SELECT 1;"

            args = MagicMock()
            args.config = Path("/tmp/config.json")
            args.connection = Path("/tmp/connection.json")
            args.output = Path("/tmp/masking.sql")

            result = handle_generate(args)

            assert result == 0


class TestCLINoSecretLeakage:
    """Tests ensuring no secret leakage in CLI output."""

    def test_password_not_in_error_messages(self):
        """Test that password never appears in error messages."""
        with (
            patch("app.cli.ConfigLoader") as mock_config_loader,
            patch("app.cli.ConnectionLoader") as mock_conn_loader,
            patch("app.cli.SecretStore") as mock_secret_store,
        ):
            mock_config_loader.return_value.load.return_value = MagicMock()
            mock_conn_loader.return_value.load.return_value = MagicMock()
            mock_secret_store.return_value.decrypt_password.return_value = (
                "SUPERSECRETPASSWORD"
            )

            args = MagicMock()
            args.config = Path("/tmp/config.json")
            args.connection = Path("/tmp/connection.json")
            args.output = Path("/tmp/masking.sql")

            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                handle_generate(args)

                stderr_output = mock_stderr.getvalue()
                assert "SUPERSECRETPASSWORD" not in stderr_output
                assert "PWD=" not in stderr_output
