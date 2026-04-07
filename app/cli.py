"""Command-line interface for Datamasker."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from app.config_loader import ConfigLoader
from app.connection_loader import ConnectionLoader
from app.exceptions import DatamaskerError, SecretError, ValidationError
from app.models import FunctionalConfig, ConnectionConfig
from app.secret_store import SecretStore
from app.sqlserver_metadata import SQLServerMetadata
from app.sql_generator import SQLGenerator
from app.validator import Validator


def create_argparser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        A configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="datamasker",
        description="SQL Server Data Masking Script Generator",
        epilog="For more information, see the README.md file.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    encrypt_parser = subparsers.add_parser(
        "encrypt-password",
        help="Encrypt a SQL Server password using DPAPI and store it in a file",
    )
    encrypt_parser.add_argument(
        "--output",
        "-o",
        required=True,
        type=Path,
        help="Output file path for the encrypted password (e.g., secrets/sql-password.dpapi)",
    )

    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a SQL Server data masking script from configuration files",
    )
    generate_parser.add_argument(
        "--config",
        "-c",
        required=True,
        type=Path,
        help="Path to the functional masking configuration JSON file",
    )
    generate_parser.add_argument(
        "--connection",
        "-cn",
        required=True,
        type=Path,
        help="Path to the technical connection configuration JSON file",
    )
    generate_parser.add_argument(
        "--output",
        "-o",
        required=True,
        type=Path,
        help="Output path for the generated SQL masking script",
    )

    test_conn_parser = subparsers.add_parser(
        "test-connection",
        help="Test SQL Server connection using a configuration file",
    )
    test_conn_parser.add_argument(
        "--connection",
        "-cn",
        required=True,
        type=Path,
        help="Path to the technical connection configuration JSON file",
    )

    return parser


def handle_encrypt_password(args: argparse.Namespace) -> int:
    """Handle the encrypt-password command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    secret_store = SecretStore()

    if not secret_store.supports_dpapi:
        print("ERROR: DPAPI is only supported on Windows.", file=sys.stderr)
        return 1

    try:
        password = _read_password_interactive()
    except KeyboardInterrupt:
        print("\nOperation cancelled.", file=sys.stderr)
        return 1

    if not password:
        print("ERROR: Password cannot be empty.", file=sys.stderr)
        return 1

    try:
        secret_store.encrypt_password(password, args.output)
        print("SUCCESS: Password encrypted and saved to '{}'".format(args.output))
        print("NOTE: This file is encrypted with DPAPI and can only be decrypted")
        print("      by the same Windows user account on the same machine.")
        return 0
    except SecretError as e:
        print("ERROR: {}".format(e.message), file=sys.stderr)
        return 1
    except Exception as e:
        print("ERROR: Unexpected error: {}".format(str(e)), file=sys.stderr)
        return 1


def _read_password_interactive() -> str:
    """Read a password from the console without echo.

    Returns:
        The password string entered by the user.
    """
    try:
        import getpass

        return getpass.getpass("Enter SQL Server password: ")
    except getpass.GetPassWarning:
        import warnings

        warnings.filterwarnings("ignore")
        return input("Enter SQL Server password: ")


def handle_generate(args: argparse.Namespace) -> int:
    """Handle the generate command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    config_loader = ConfigLoader()
    connection_loader = ConnectionLoader()
    secret_store = SecretStore()

    try:
        functional_config = config_loader.load(args.config)
    except DatamaskerError as e:
        print(
            "ERROR loading functional configuration: {}".format(e.message),
            file=sys.stderr,
        )
        return 1

    try:
        connection_config = connection_loader.load(args.connection)
    except DatamaskerError as e:
        print(
            "ERROR loading connection configuration: {}".format(e.message),
            file=sys.stderr,
        )
        return 1

    try:
        password = _decrypt_password(secret_store, connection_config.password_file)
    except SecretError as e:
        print("ERROR reading encrypted password: {}".format(e.message), file=sys.stderr)
        return 1

    connection_string = _build_connection_string(connection_config, password)

    try:
        metadata = SQLServerMetadata(connection_string)
        validator = Validator(metadata)

        validation_errors = validator.validate(functional_config)

        if validation_errors:
            print(
                "ERROR: Validation failed. The following rules cannot be processed:",
                file=sys.stderr,
            )
            for error in validation_errors:
                print("  - {}".format(error.message), file=sys.stderr)
            print("\nNo masking.sql file has been generated.", file=sys.stderr)
            return 1

    except DatamaskerError as e:
        print("ERROR during validation: {}".format(e.message), file=sys.stderr)
        return 1
    except Exception as e:
        print(
            "ERROR: Unexpected error during validation: {}".format(str(e)),
            file=sys.stderr,
        )
        return 1

    try:
        generator = SQLGenerator()
        sql_script = generator.generate(functional_config)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(sql_script, encoding="utf-8")

        print("SUCCESS: masking.sql generated at '{}'".format(args.output))
        print("NOTE: Review the generated SQL script before executing it manually.")
        print(
            "      SQL execution is NOT automatic. Use sqlcmd or another tool to run it."
        )
        return 0

    except DatamaskerError as e:
        print("ERROR during SQL generation: {}".format(e.message), file=sys.stderr)
        return 1
    except Exception as e:
        print(
            "ERROR: Unexpected error during SQL generation: {}".format(str(e)),
            file=sys.stderr,
        )
        return 1


def handle_test_connection(args: argparse.Namespace) -> int:
    """Handle the test-connection command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    connection_loader = ConnectionLoader()
    secret_store = SecretStore()

    try:
        connection_config = connection_loader.load(args.connection)
    except DatamaskerError as e:
        print(
            "ERROR loading connection configuration: {}".format(e.message),
            file=sys.stderr,
        )
        return 1

    try:
        password = _decrypt_password(secret_store, connection_config.password_file)
    except SecretError as e:
        print("ERROR reading encrypted password: {}".format(e.message), file=sys.stderr)
        return 1

    connection_string = _build_connection_string(connection_config, password)

    try:
        metadata = SQLServerMetadata(connection_string)
        conn = metadata._connect()
        conn.close()
        print(
            "SUCCESS: Connected to SQL Server '{}' (database: '{}')".format(
                connection_config.server, connection_config.database
            )
        )
        return 0
    except DatamaskerError as e:
        print("ERROR: {}".format(e.message), file=sys.stderr)
        return 1
    except Exception as e:
        print("ERROR: Unexpected error: {}".format(str(e)), file=sys.stderr)
        return 1


def _decrypt_password(secret_store: SecretStore, password_file: str) -> str:
    """Decrypt the password from a DPAPI-encrypted file.

    Args:
        secret_store: The SecretStore instance.
        password_file: Path to the encrypted password file.

    Returns:
        The decrypted password.

    Raises:
        SecretError: If decryption fails.
    """
    password_path = Path(password_file)
    return secret_store.decrypt_password(password_path)


def _build_connection_string(config: ConnectionConfig, password: str) -> str:
    """Build an ODBC connection string from configuration.

    Args:
        config: The connection configuration.
        password: The decrypted SQL Server password.

    Returns:
        A formatted ODBC connection string.
    """
    parts = [
        "DRIVER={ODBC Driver 17 for SQL Server}",
        "SERVER={}".format(config.server),
        "DATABASE={}".format(config.database),
        "UID={}".format(config.username),
        "PWD={}".format(password),
    ]
    return ";".join(parts)


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Optional list of command-line arguments (defaults to sys.argv).

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parser = create_argparser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "encrypt-password":
        return handle_encrypt_password(args)
    elif args.command == "generate":
        return handle_generate(args)
    elif args.command == "test-connection":
        return handle_test_connection(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
