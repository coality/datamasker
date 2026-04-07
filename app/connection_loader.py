"""Technical/connection configuration loader."""

import json
from pathlib import Path
from typing import Any, Dict, List

from app.exceptions import ConfigurationError
from app.models import ConnectionConfig, DatabaseConfig, ServerConfig


class ConnectionLoader:
    """Loads and validates the technical/connection configuration."""

    SERVER_FIELDS = frozenset({"server", "username", "passwordFile"})
    REQUIRED_FIELDS = SERVER_FIELDS | {"databases"}

    def load(self, config_path: Path) -> ConnectionConfig:
        """Load and parse a connection configuration file.

        Args:
            config_path: Path to the connection JSON configuration file.

        Returns:
            A validated ConnectionConfig object.

        Raises:
            ConfigurationError: If the file is missing, invalid, or fails validation.
        """
        if not config_path or str(config_path) == "":
            raise ConfigurationError(
                "Connection configuration file path cannot be empty"
            )

        if not config_path.exists():
            raise ConfigurationError(
                "Connection configuration file not found: {}".format(config_path)
            )

        try:
            raw_content = config_path.read_text(encoding="utf-8")
        except IOError as e:
            raise ConfigurationError(
                "Failed to read connection configuration file {}: {}".format(
                    config_path, str(e)
                )
            )

        try:
            data = json.loads(raw_content)
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                "Invalid JSON in connection configuration file {}: {}".format(
                    config_path, str(e)
                )
            )

        if not isinstance(data, dict):
            raise ConfigurationError(
                "Connection configuration file {} must contain a JSON object at root".format(
                    config_path
                )
            )

        return self._parse_and_validate(data, str(config_path))

    def _parse_and_validate(
        self, data: Dict[str, Any], source: str
    ) -> ConnectionConfig:
        """Parse and validate the connection configuration data."""
        missing_fields = self.REQUIRED_FIELDS - set(data.keys())
        if missing_fields:
            raise ConfigurationError(
                "Missing required field(s) in {}: {}".format(
                    source, ", ".join(sorted(missing_fields))
                )
            )

        server = data.get("server")
        if not isinstance(server, str) or not server:
            raise ConfigurationError(
                "server in {} must be a non-empty string".format(source)
            )

        username = data.get("username")
        if not isinstance(username, str) or not username:
            raise ConfigurationError(
                "username in {} must be a non-empty string".format(source)
            )

        password_file = data.get("passwordFile")
        if not isinstance(password_file, str) or not password_file:
            raise ConfigurationError(
                "passwordFile in {} must be a non-empty string".format(source)
            )

        databases = data.get("databases")
        if not isinstance(databases, list) or not databases:
            raise ConfigurationError(
                "databases in {} must be a non-empty list".format(source)
            )

        db_configs: List[DatabaseConfig] = []
        for i, db in enumerate(databases):
            if not isinstance(db, str) or not db:
                raise ConfigurationError(
                    "databases entry at index {} in {} must be a non-empty string".format(
                        i, source
                    )
                )
            db_configs.append(DatabaseConfig(name=db))

        server_config = ServerConfig(
            server=server,
            username=username,
            password_file=password_file,
        )

        return ConnectionConfig(
            server_config=server_config,
            databases=db_configs,
        )
